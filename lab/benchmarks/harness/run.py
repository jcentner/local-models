"""Run a benchmark dataset against a local model and score it.

Usage (from ``lab/benchmarks/``):

    python -m harness.run --benchmark ../../benchmarks/<name> --model <ollama-tag> \\
        --k 1 --temperature 1.0 --top-p 0.95 --num-ctx 32768 --seed 0

Reads ``benchmarks/<name>/{bench.json,prompts.jsonl,answer_key.jsonl,rubric.md}``,
samples ``k`` completions per prompt, scores via the method declared in
``bench.json`` (equivalence | code_tests | llm_judge | agentic), prints both
``observed_pass@k`` (best-of-k capability ceiling) and ``pass^k`` (all-k
reliability, tau-bench) plus flaky-item count + SEM, appends a row to
``results.csv``, and saves raw completions under ``runs/`` (git-ignored).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import platform
import socket
import sys
import urllib.request
from pathlib import Path

# Allow running both as ``-m harness.run`` and as a direct script.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from harness.client import make_client, SamplingConfig
    from harness.judge_copilot import CopilotCLIJudge
    from harness.agentic import CopilotCLIUser, run_episode, resolve_toolset, TOOLSETS
    from harness.scorers import agentic as agentic_scorer, code_exec, equivalence, llm_judge
else:
    from .client import make_client, SamplingConfig
    from .judge_copilot import CopilotCLIJudge
    from .agentic import CopilotCLIUser, run_episode, resolve_toolset, TOOLSETS
    from .scorers import agentic as agentic_scorer, code_exec, equivalence, llm_judge

HERE = Path(__file__).resolve().parent          # lab/benchmarks/harness
LAB_BENCH = HERE.parent                          # lab/benchmarks


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _ollama_version(base_url: str) -> str:
    try:
        with urllib.request.urlopen(f"{base_url}/api/version", timeout=5) as r:
            return json.loads(r.read().decode()).get("version", "")
    except Exception:
        return ""


def compute_cost(prompt_tokens: int, gen_tokens: int,
                 price_in: float, price_out: float) -> float:
    """USD cost from token totals + per-1M-token prices (local default 0 -> 0.0)."""
    return round(prompt_tokens / 1e6 * price_in + gen_tokens / 1e6 * price_out, 6)


# Whitelisted meta keys persisted on raw run lines for the run-viewer's interactive
# slicing (small + categorical). See tmp/meta-schema-contract.md. A bench.json may
# NARROW this set via a "slice_fields" list (intersected with the whitelist), but
# never widen it - persona/policy/devices must never leak onto every line (F6).
SLICE_WHITELIST = ("tier", "category")


def slice_fields(manifest: dict) -> tuple:
    """The whitelisted meta keys to persist for viewer slicing on this benchmark."""
    override = manifest.get("slice_fields")
    if isinstance(override, (list, tuple)) and override:
        return tuple(f for f in override if f in SLICE_WHITELIST)
    return SLICE_WHITELIST


def meta_slice(item: dict, fields) -> dict:
    """Flat ``str|int|float`` subset of ``item.meta`` for the whitelisted fields.

    Non-scalar values (objects/arrays) are dropped so the viewer contract holds:
    flat values only, identical across an item's k samples (computed once per item).
    """
    meta = item.get("meta") or {}
    out = {}
    for k in fields:
        if k in meta and isinstance(meta[k], (str, int, float)):
            out[k] = meta[k]
    return out


def reliability_metrics(per_item_correct: list[int], k: int) -> dict:
    """Reliability summary from per-item correct counts (each 0..k).

    Two complementary capability metrics, always reported together:
    - ``observed_pass_at_k``: fraction of items with >=1 correct sample (best-of-k).
      A *capability ceiling* - it RISES with k, so on its own it HIDES flakiness.
    - ``pass_hat_k``: fraction of items correct on ALL k samples (tau-bench's
      pass^k). Reliability / consistency - the home-agent-relevant signal; it FALLS
      with k as instability shows. See wiki/concepts/eval-reliability.md.

    Plus: ``avg_correct`` (mean per-sample correctness; macro == micro with equal k),
    ``flaky_items`` (items with 0 < correct < k, i.e. inconsistent across samples),
    and ``sem`` (standard error of the mean over per-item mean scores; CLT, per
    Anthropic 2411.00640; "" when <2 items).
    """
    n = len(per_item_correct)
    if n == 0 or k <= 0:
        return {"observed_pass_at_k": 0.0, "pass_hat_k": 0.0, "avg_correct": 0.0,
                "flaky_items": 0, "sem": ""}
    item_means = [c / k for c in per_item_correct]
    observed = sum(1 for c in per_item_correct if c >= 1) / n
    pass_hat = sum(1 for c in per_item_correct if c >= k) / n
    avg = sum(item_means) / n
    flaky = sum(1 for c in per_item_correct if 0 < c < k)
    if n >= 2:
        var = sum((m - avg) ** 2 for m in item_means) / (n - 1)
        sem = round((var ** 0.5) / (n ** 0.5), 4)
    else:
        sem = ""
    return {"observed_pass_at_k": round(observed, 4), "pass_hat_k": round(pass_hat, 4),
            "avg_correct": round(avg, 4), "flaky_items": flaky, "sem": sem}


def load_benchmark(bench_dir: Path) -> dict:
    bench_json = bench_dir / "bench.json"
    if not bench_json.exists():
        raise SystemExit(f"no bench.json in {bench_dir}")
    manifest = json.loads(bench_json.read_text())
    prompts = _read_jsonl(bench_dir / "prompts.jsonl")
    key = {row["id"]: row for row in _read_jsonl(bench_dir / "answer_key.jsonl") if "id" in row}
    rubric_path = bench_dir / "rubric.md"
    manifest["_prompts"] = prompts
    manifest["_key"] = key
    manifest["_rubric"] = rubric_path.read_text() if rubric_path.exists() else ""
    return manifest


VALID_METHODS = {"equivalence", "code_tests", "llm_judge", "agentic"}

# Message-bearing tools eligible for an optional judge_message check, per toolset.
JUDGE_MSG_TOOLS = {"support": {"reply", "escalate"}, "home_automation": {"ask", "say"}}


def validate_benchmark(manifest: dict) -> None:
    """Fail closed BEFORE any model call. A benchmark that scores silently-wrong
    is worse than one that refuses to run."""
    missing = {"name", "version", "scoring"} - set(manifest)
    if missing:
        raise SystemExit(f"bench.json missing required fields: {sorted(missing)}")
    method = manifest["scoring"]
    if method not in VALID_METHODS:
        raise SystemExit(f"unknown scoring method {method!r} (expected {sorted(VALID_METHODS)})")
    prompts = manifest["_prompts"]
    if not prompts:
        raise SystemExit("prompts.jsonl has no items")
    ids = [p.get("id") for p in prompts]
    if any(not i for i in ids):
        raise SystemExit("every prompt needs a non-empty id")
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        raise SystemExit(f"prompt ids must be unique; duplicates: {dupes}")
    if any(not str(p.get("prompt", "")).strip() for p in prompts):
        raise SystemExit("every prompt needs non-empty prompt text")
    if method in {"equivalence", "code_tests"}:
        key_ids, prompt_ids = set(manifest["_key"]), set(ids)
        if key_ids != prompt_ids:
            raise SystemExit(
                "answer_key ids must match prompt ids: "
                f"missing_keys={sorted(prompt_ids - key_ids)} "
                f"orphan_keys={sorted(key_ids - prompt_ids)}")
        field = "answer" if method == "equivalence" else "tests"
        for kid, row in manifest["_key"].items():
            if not str(row.get(field, "")).strip():
                raise SystemExit(f"{method} key row {kid!r} needs non-empty {field!r}")
    elif method == "llm_judge":
        if not manifest.get("_rubric", "").strip():
            raise SystemExit("llm_judge benchmark needs a non-empty rubric.md")
    elif method == "agentic":
        toolset_name = manifest.get("toolset", "support")
        if toolset_name not in TOOLSETS:
            raise SystemExit(f"agentic bench.json toolset {toolset_name!r} unknown (expected {sorted(TOOLSETS)})")
        for fld in ("max_steps", "max_turns"):
            if fld in manifest and (isinstance(manifest[fld], bool)
                                    or not isinstance(manifest[fld], int) or manifest[fld] < 1):
                raise SystemExit(f"agentic bench.json {fld} must be a positive integer")
        valid_tools = set(TOOLSETS[toolset_name].behaviors)
        for p in prompts:
            if not str((p.get("meta") or {}).get("persona", "")).strip():
                raise SystemExit(f"agentic prompt {p.get('id')!r} needs meta.persona (the user-sim goal)")
        key_ids, prompt_ids = set(manifest["_key"]), set(ids)
        if key_ids != prompt_ids:
            raise SystemExit(
                "answer_key ids must match prompt ids: "
                f"missing_keys={sorted(prompt_ids - key_ids)} orphan_keys={sorted(key_ids - prompt_ids)}")
        # tool-name references must be real (a typo silently disables a guard)
        for kid, krow in manifest["_key"].items():
            for fld in ("required_tools", "forbidden_tools"):
                if fld in krow and not isinstance(krow[fld], list):
                    raise SystemExit(f"agentic key {kid!r} {fld} must be a list of tool names")
            bad_tools = (set(krow.get("required_tools", [])) | set(krow.get("forbidden_tools", []))) - valid_tools
            if bad_tools:
                raise SystemExit(f"agentic key {kid!r} references unknown tools {sorted(bad_tools)} "
                                 f"(valid for {toolset_name}: {sorted(valid_tools)})")
            # required_any: a list of OR-groups (each a non-empty list of valid tool names)
            ra = krow.get("required_any")
            if ra is not None:
                if not isinstance(ra, list) or not all(isinstance(g, list) and g for g in ra):
                    raise SystemExit(f"agentic key {kid!r} required_any must be a list of non-empty tool-name groups")
                if any(not isinstance(t, str) or not t for g in ra for t in g):
                    raise SystemExit(f"agentic key {kid!r} required_any tool names must be non-empty strings")
                bad_any = {t for g in ra for t in g} - valid_tools
                if bad_any:
                    raise SystemExit(f"agentic key {kid!r} required_any references unknown tools {sorted(bad_any)} "
                                     f"(valid for {toolset_name}: {sorted(valid_tools)})")
        # optional judge_message (A1) must name a message-bearing tool + carry valid criteria/threshold
        msg_tools = JUDGE_MSG_TOOLS.get(toolset_name, set())
        for kid, krow in manifest["_key"].items():
            jm = krow.get("judge_message")
            if jm is None:
                continue
            if not isinstance(jm, dict):
                raise SystemExit(f"agentic key {kid!r} judge_message must be an object")
            jt = jm.get("tool")
            jts = jt if isinstance(jt, list) else [jt]
            if not jts or any(not isinstance(t, str) for t in jts) or any(t not in msg_tools for t in jts):
                raise SystemExit(f"agentic key {kid!r} judge_message.tool must be one or more of {sorted(msg_tools)}")
            if len(jts) != len(set(jts)):
                raise SystemExit(f"agentic key {kid!r} judge_message.tool has duplicate entries")
            if not str(jm.get("criteria", "")).strip():
                raise SystemExit(f"agentic key {kid!r} judge_message needs non-empty criteria")
            thr = jm.get("pass_threshold", 6.0)
            if isinstance(thr, bool) or not isinstance(thr, (int, float)):
                raise SystemExit(f"agentic key {kid!r} judge_message.pass_threshold must be numeric")
        if toolset_name == "support":
            for kid, krow in manifest["_key"].items():
                if krow.get("expected_terminal") not in {"reply", "escalate"}:
                    raise SystemExit(f"agentic key {kid!r} needs expected_terminal in reply|escalate")
        else:  # home_automation
            prompt_by_id = {p["id"]: p for p in prompts}
            for p in prompts:
                devices = (p.get("meta") or {}).get("devices")
                if not isinstance(devices, dict) or not devices:
                    raise SystemExit(f"home_automation prompt {p.get('id')!r} needs a non-empty meta.devices")
                # optional device precondition: requires={dep: scalar-state}, deps must exist
                for dname, dval in devices.items():
                    req = (dval or {}).get("requires") if isinstance(dval, dict) else None
                    if req is None:
                        continue
                    if not isinstance(req, dict):
                        raise SystemExit(f"home_automation prompt {p.get('id')!r} device {dname!r} "
                                         "requires must be an object {device: state}")
                    for rdev, rstate in req.items():
                        if rdev not in devices:
                            raise SystemExit(f"home_automation prompt {p.get('id')!r} device {dname!r} "
                                             f"requires unknown device {rdev!r}")
                        if isinstance(rstate, (dict, list)):
                            raise SystemExit(f"home_automation prompt {p.get('id')!r} device {dname!r} "
                                             f"requires[{rdev!r}] must be a scalar state")
            for kid, krow in manifest["_key"].items():
                if not isinstance(krow.get("expected_state"), dict):
                    raise SystemExit(f"home_automation key {kid!r} needs expected_state (a dict, may be empty)")
                for dname, dstate in krow["expected_state"].items():
                    if isinstance(dstate, dict):
                        raise SystemExit(f"home_automation key {kid!r} expected_state[{dname!r}] must be a scalar "
                                         "state or a list of scalar states")
                    if isinstance(dstate, list) and (not dstate or any(isinstance(e, (dict, list)) for e in dstate)):
                        raise SystemExit(f"home_automation key {kid!r} expected_state[{dname!r}] list must be "
                                         "non-empty and contain only scalar states")
                if "require_clarify" in krow and not isinstance(krow.get("require_clarify"), bool):
                    raise SystemExit(f"home_automation key {kid!r} require_clarify must be true/false")
                for fld in ("forbidden_devices", "require_confirm", "forbidden_device_attempts"):
                    if fld in krow and not isinstance(krow[fld], list):
                        raise SystemExit(f"home_automation key {kid!r} {fld} must be a list of device ids")
                scen_devices = set((prompt_by_id.get(kid, {}).get("meta") or {}).get("devices", {}))
                refd = (set(krow.get("expected_state", {})) | set(krow.get("forbidden_devices", []))
                        | set(krow.get("require_confirm", [])) | set(krow.get("forbidden_device_attempts", [])))
                bad_dev = refd - scen_devices
                if bad_dev:
                    raise SystemExit(f"home_automation key {kid!r} references unknown devices {sorted(bad_dev)} "
                                     f"(scenario devices: {sorted(scen_devices)})")


def score_one(method: str, manifest: dict, item: dict, completion: str, judge=None,
              sandbox: str = "local-unsafe") -> dict:
    key = manifest["_key"].get(item["id"], {})
    if method == "equivalence":
        return equivalence.score(completion, key.get("answer", ""))
    if method == "code_tests":
        return code_exec.score(completion, key.get("tests", ""), mode=sandbox)
    if method == "llm_judge":
        if judge is None:
            raise SystemExit("llm_judge benchmark needs a judge (default claude-opus-4.8 via Copilot CLI)")
        return llm_judge.score(item["prompt"], completion, manifest["_rubric"], judge,
                               pass_threshold=manifest.get("judge", {}).get("pass_threshold", 6.0))
    raise SystemExit(f"unknown scoring method: {method}")


def think_label(think: bool | None) -> str:
    """Unambiguous record of the think control state for results.csv / raw.

    args.think is tri-state and None is NOT 'off': for a template that thinks by
    default (e.g. gemma over llama.cpp --jinja) None meant thinking-ON. So persist
    on|off|default (interpret 'default' alongside provider + the model page)
    rather than a bare bool, so think-vs-no-think rows stay comparable.
    """
    return {True: "on", False: "off", None: "default"}[think]


def apply_system_suffix(base: str | None, suffix: str | None) -> str | None:
    """Append a run-time suffix (e.g. a brevity nudge) to a system prompt.

    A run param recorded in the raw jsonl, NOT a bench.json edit - keeps the eval
    pure + comparable across models. Returns ``base`` unchanged when ``suffix`` is
    falsy; uses ``suffix`` alone when there is no base system prompt.
    """
    if not suffix:
        return base
    return (base + "\n\n" + suffix) if base else suffix


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run a benchmark against a local model.")
    ap.add_argument("--benchmark", required=True, help="path to benchmarks/<name>/ dir")
    ap.add_argument("--model", required=True,
                    help="model under test: an Ollama tag (provider ollama) or an "
                         "API model ref (provider openai-compatible)")
    ap.add_argument("--base-model", default=None,
                    help="canonical base-model id for grouping results across config "
                         "variants/serving (e.g. all g4v2-* quant labels -> "
                         "'gemma-4-12b-agentic-fable5'; both minicpm5 labels -> "
                         "'minicpm5-1b'). Match the wiki/models/<id>.md slug where one "
                         "exists. Defaults to --model when omitted.")
    ap.add_argument("--provider", choices=["ollama", "openai-compatible"], default="ollama",
                    help="ollama = native local daily driver; openai-compatible = a "
                         "hosted API (e.g. Z.AI GLM) or Ollama's :11434/v1 shim.")
    ap.add_argument("--k", type=int, default=3,
                    help="samples per prompt (default 3). Reports observed_pass@k "
                         "(best-of-k capability ceiling) AND pass^k (all-k reliability); "
                         "small/quantized models flake, so >=2 is the honest default. "
                         "Use --k 1 for a quick smoke.")
    ap.add_argument("--limit", type=int, default=0, help="limit number of prompts (0 = all)")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--top-p", type=float, default=0.95)
    ap.add_argument("--top-k", type=int, default=0)
    ap.add_argument("--num-predict", type=int, default=4096)
    ap.add_argument("--num-ctx", type=int, default=8192)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--think", action=argparse.BooleanOptionalAction, default=None,
                    help="--no-think disables a thinking model's CoT (recommended for "
                         "deterministic code/equivalence scorers to avoid empty output).")
    ap.add_argument("--system-suffix", default=None,
                    help="append this text to the system prompt at runtime (e.g. a "
                         "brevity nudge to tame over-long CoT). A run param recorded in "
                         "the raw jsonl, NOT a bench.json edit - keeps the eval pure and "
                         "comparable across models.")
    ap.add_argument("--base-url", default=None,
                    help="endpoint override; default per provider (ollama: "
                         "http://localhost:11434, openai-compatible: "
                         "http://localhost:11434/v1).")
    ap.add_argument("--api-key-env", default=None,
                    help="name of the env var holding the API key (openai-compatible "
                         "remote hosts). Never pass the key itself on the CLI.")
    ap.add_argument("--price-in", type=float, default=0.0,
                    help="USD per 1M input tokens (for cost_usd; default 0 = local).")
    ap.add_argument("--price-out", type=float, default=0.0,
                    help="USD per 1M output tokens (for cost_usd; default 0 = local).")
    ap.add_argument("--judge-model", default="claude-opus-4.8",
                    help="Copilot CLI model id for llm_judge (a FRONTIER model; "
                         "never a local small model). e.g. claude-opus-4.8, gpt-5.5.")
    ap.add_argument("--judge-effort", default=None,
                    choices=["low", "medium", "high", "xhigh", "max"],
                    help="reasoning effort for the judge (Copilot CLI --reasoning-effort)")
    ap.add_argument("--user-model", default="claude-opus-4.8",
                    help="Copilot CLI model id for the agentic user-simulator (a FRONTIER model).")
    ap.add_argument("--tool-protocol", choices=["prompt", "native"], default="prompt",
                    help="agentic tool protocol: 'prompt' = model emits one JSON action "
                         "per step (model-agnostic); 'native' = provider function-calling "
                         "(Ollama/OpenAI `tools` + message.tool_calls), a fair footing for "
                         "thinking/XML-tool models (needs a tool-capable model/template).")
    ap.add_argument("--judge-messages", action="store_true",
                    help="agentic only: additionally grade message TEXT quality with the "
                         "frontier judge on items whose key carries judge_message (e.g. a "
                         "fabrication check on reply). Default off - the deterministic "
                         "state/policy result is the backbone; this only TIGHTENS it. Costs "
                         "k x judge calls on judged items; reuses --judge-model/--judge-effort.")
    ap.add_argument("--slice-by", default=None,
                    help="meta field to break metrics down by (e.g. 'tier' or 'category'); "
                         "prints per-group pass^k / observed_pass@k. The results.csv row is "
                         "unchanged (overall only).")
    ap.add_argument("--results", default=str(LAB_BENCH / "results.csv"))
    ap.add_argument("--dry-run", action="store_true", help="print config + first prompt, don't call the model")
    ap.add_argument("--code-sandbox", choices=["podman", "local-unsafe"], default=None,
                    help="execution mode for code_tests (REQUIRED for code_tests). "
                         "'podman' = locked-down throwaway container (recommended); "
                         "'local-unsafe' = host subprocess, weak isolation (opt-in).")
    args = ap.parse_args(argv)

    bench_dir = Path(args.benchmark).resolve()
    manifest = load_benchmark(bench_dir)
    validate_benchmark(manifest)
    method = manifest["scoring"]
    prompts = manifest["_prompts"]
    if args.limit:
        prompts = prompts[: args.limit]

    sampling = SamplingConfig(
        temperature=args.temperature, top_p=args.top_p, top_k=args.top_k,
        num_predict=args.num_predict, num_ctx=args.num_ctx, seed=args.seed,
        think=args.think,
    )
    # Unambiguous record of the think axis. args.think is tri-state and None is
    # NOT "off": for a template that thinks by default (e.g. gemma over llama.cpp
    # --jinja) None meant thinking-ON. So persist on|off|default (interpret
    # 'default' alongside provider/model) rather than a bare bool.
    think_lbl = think_label(args.think)
    resolved_base = args.base_url or (
        "http://localhost:11434/v1" if args.provider == "openai-compatible"
        else "http://localhost:11434")
    if args.think is not None and args.provider != "ollama":
        print("note: over openai-compatible, --think/--no-think is sent as "
              "chat_template_kwargs.enable_thinking (works on SGLang; ignored by "
              "servers that don't support it).")
    client = make_client(args.provider, args.model, resolved_base, sampling, args.api_key_env)
    judge = None
    if method == "llm_judge":
        judge = CopilotCLIJudge(model=args.judge_model, effort=args.judge_effort)
    msg_judge = None
    if method == "agentic" and args.judge_messages:
        msg_judge = CopilotCLIJudge(model=args.judge_model, effort=args.judge_effort)

    print(f"benchmark={manifest['name']} v{manifest.get('version','?')} method={method} "
          f"items={len(prompts)} k={args.k}")
    print(f"provider={args.provider} model={args.model} endpoint={resolved_base} "
          f"sampling={sampling.to_options()}")
    if args.dry_run:
        if prompts:
            print("\n--- first prompt ---\n" + prompts[0]["prompt"][:500])
        return 0

    if method == "code_tests":
        if args.code_sandbox is None:
            raise SystemExit(
                "code_tests requires --code-sandbox: 'podman' (recommended, locked-down "
                "container) or 'local-unsafe' (host subprocess, weak isolation; opt-in).")
        if not code_exec.sandbox_available(args.code_sandbox):
            raise SystemExit(
                f"--code-sandbox {args.code_sandbox}: podman is not available. Install/configure "
                "it (see github.com/jcentner/podman-wsl-setup) or use --code-sandbox local-unsafe.")

    runs_dir = LAB_BENCH / "runs"
    runs_dir.mkdir(exist_ok=True)
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_model = args.model.replace(":", "_").replace("/", "_")
    raw_path = runs_dir / f"{manifest['name']}-{safe_model}-{ts}.jsonl"

    sample_correct = 0     # total correct samples (for avg)
    total_samples = 0
    tok_s_sum = 0.0
    prompt_tok_sum = 0
    gen_tok_sum = 0
    wall_sum = 0.0
    per_item_correct: list[int] = []          # correct count (0..k) per item -> reliability
    slice_groups: dict[str, list[int]] = {}   # meta[slice_by] value -> per-item correct counts
    agentic_toolset = resolve_toolset(manifest.get("toolset")) if method == "agentic" else None
    # bench.json may widen the per-turn step / turn budget for multi-step scenarios
    # (e.g. a dependency that needs BLOCKED -> satisfy -> retry -> say); default 5/4.
    ep_max_steps = int(manifest.get("max_steps", 5))
    ep_max_turns = int(manifest.get("max_turns", 4))
    fields = slice_fields(manifest)
    with raw_path.open("w") as raw:
        for item in prompts:
            item_meta = meta_slice(item, fields)
            correct_this_item = 0
            for s in range(args.k):
                if method == "agentic":
                    user_sim = CopilotCLIUser(persona=item["meta"]["persona"], model=args.user_model)
                    episode = run_episode(client, user_sim, item, protocol=args.tool_protocol,
                                          toolset=agentic_toolset,
                                          max_steps=ep_max_steps, max_turns=ep_max_turns,
                                          system_suffix=args.system_suffix)
                    res = agentic_scorer.score(episode, manifest["_key"].get(item["id"], {}),
                                               judge=msg_judge)
                    perf = episode["perf"]
                    total_samples += 1
                    prompt_tok_sum += perf["prompt_tokens"]
                    gen_tok_sum += perf["gen_tokens"]
                    wall_sum += perf["wall_s"]
                    tok_s_sum += (perf["gen_tokens"] / perf["wall_s"]) if perf["wall_s"] else 0.0
                    if res.get("correct"):
                        sample_correct += 1
                        correct_this_item += 1
                    raw.write(json.dumps({"id": item["id"], "sample_index": s, "result": res,
                                          "meta": item_meta,
                                          "think": think_lbl,
                                          "system_suffix": args.system_suffix,
                                          "episode": {"resolution": episode["resolution"],
                                                      "protocol": episode.get("protocol"),
                                                      "toolset": episode.get("toolset"),
                                                      # did_* are scorer inputs for support
                                                      # (reply vs escalate) - persist so a raw
                                                      # line can be re-scored offline.
                                                      "did_reply": episode.get("did_reply"),
                                                      "did_escalate": episode.get("did_escalate"),
                                                      "tools_used": episode.get("tools_used"),
                                                      "tool_calls": episode["tool_calls"],
                                                      "final_state": episode.get("final_state"),
                                                      "transcript": episode["transcript"]}}) + "\n")
                    continue
                comp = client.complete([{"role": "user", "content": item["prompt"]}],
                                       system=apply_system_suffix(manifest.get("system"), args.system_suffix))
                res = score_one(method, manifest, item, comp.text, judge,
                                sandbox=args.code_sandbox or "local-unsafe")
                total_samples += 1
                tok_s_sum += comp.gen_tok_per_s
                prompt_tok_sum += comp.prompt_tokens
                gen_tok_sum += comp.gen_tokens
                wall_sum += comp.wall_s
                if res.get("correct"):
                    sample_correct += 1
                    correct_this_item += 1
                raw.write(json.dumps({"id": item["id"], "sample_index": s, "result": res,
                                      "meta": item_meta,
                                      "think": think_lbl,
                                      "system_suffix": args.system_suffix,
                                      "prompt_tokens": comp.prompt_tokens,
                                      "gen_tokens": comp.gen_tokens,
                                      "wall_s": comp.wall_s,
                                      "gen_tok_per_s": comp.gen_tok_per_s,
                                      "completion": comp.text}) + "\n")
            per_item_correct.append(correct_this_item)
            if args.slice_by:
                gv = str((item.get("meta") or {}).get(args.slice_by, "\u2014"))
                slice_groups.setdefault(gv, []).append(correct_this_item)
            mark = "OK " if correct_this_item == args.k else "XX " if correct_this_item == 0 else "~~ "
            print(f"  {mark}{item['id']} ({correct_this_item}/{args.k})")

    metrics = reliability_metrics(per_item_correct, args.k)
    mean_tok_s = round(tok_s_sum / (total_samples or 1), 2)
    cost_usd = compute_cost(prompt_tok_sum, gen_tok_sum, args.price_in, args.price_out)
    print(f"\nobserved_pass@{args.k}={metrics['observed_pass_at_k']:.3f}  "
          f"pass^{args.k}={metrics['pass_hat_k']:.3f}  avg_correct={metrics['avg_correct']:.3f}  "
          f"flaky={metrics['flaky_items']}/{len(per_item_correct)}  sem={metrics['sem']}  "
          f"mean_gen_tok/s={mean_tok_s}  cost_usd={cost_usd}  raw={raw_path.name}")
    print("  (observed_pass@k = >=1 correct in k [best-of-k capability ceiling]; "
          "pass^k = ALL k correct [tau-bench reliability]; flaky = items inconsistent "
          "across k; sem = standard error of the per-item mean)")
    if args.slice_by and slice_groups:
        print(f"  by meta.{args.slice_by}:")
        for gv in sorted(slice_groups):
            gm = reliability_metrics(slice_groups[gv], args.k)
            print(f"    {gv}: n={len(slice_groups[gv])}  pass^{args.k}={gm['pass_hat_k']:.3f}  "
                  f"obs@{args.k}={gm['observed_pass_at_k']:.3f}  avg={gm['avg_correct']:.3f}")

    row = {
        "date": dt.date.today().isoformat(),
        "machine": socket.gethostname(),
        "model": args.model,
        "base_model": args.base_model or args.model,
        "provider": args.provider,
        "runner": f"{args.provider}-harness",
        "runner_version": _ollama_version(resolved_base) if args.provider == "ollama" else "",
        "endpoint": resolved_base,
        "benchmark": f"{manifest['name']} v{manifest.get('version','?')}",
        "scoring": method,
        "num_ctx": args.num_ctx,
        "num_predict": args.num_predict,
        "sampling": f"t={args.temperature},top_p={args.top_p},top_k={args.top_k}",
        "think": think_lbl,
        "seed": args.seed,
        "k": args.k,
        "n_items": len(prompts),
        "observed_pass_at_k": metrics["observed_pass_at_k"],
        "pass_hat_k": metrics["pass_hat_k"],
        "avg_correct": metrics["avg_correct"],
        "flaky_items": metrics["flaky_items"],
        "sem": metrics["sem"],
        "mean_gen_tok_s": mean_tok_s,
        "prompt_tokens_total": prompt_tok_sum,
        "gen_tokens_total": gen_tok_sum,
        "wall_s_total": round(wall_sum, 1),
        "cost_usd": cost_usd,
        "judge": (f"copilot:{args.judge_model}" if method == "llm_judge"
                  else (f"usersim:copilot:{args.user_model}:{args.tool_protocol}"
                        + (f"+msgjudge:{args.judge_model}" if args.judge_messages else ""))
                  if method == "agentic" else ""),
        "code_sandbox": args.code_sandbox or "",
        "raw_file": raw_path.name,
        "platform": platform.platform(),
    }
    results_path = Path(args.results)
    write_header = not results_path.exists()
    if not write_header:
        # Append path: results.csv is appended WITHOUT re-writing the header, so
        # the existing header MUST match this row's field order exactly or every
        # appended row silently misaligns. Fail loudly instead.
        with results_path.open(newline="") as rf:
            existing_header = next(csv.reader(rf), [])
        if existing_header and existing_header != list(row.keys()):
            raise SystemExit(
                f"results.csv header mismatch: existing {existing_header} != "
                f"row {list(row.keys())}. Migrate the file (see tmp/migrate_results_*.py) "
                "before appending so columns stay aligned.")
    with results_path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            w.writeheader()
        w.writerow(row)
    print(f"appended -> {results_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
