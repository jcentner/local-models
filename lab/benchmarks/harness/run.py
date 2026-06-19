"""Run a benchmark dataset against a local model and score it.

Usage (from ``lab/benchmarks/``):

    python -m harness.run --benchmark ../../benchmarks/<name> --model <ollama-tag> \\
        --k 1 --temperature 1.0 --top-p 0.95 --num-ctx 32768 --seed 0

Reads ``benchmarks/<name>/{bench.json,prompts.jsonl,answer_key.jsonl,rubric.md}``,
samples ``k`` completions per prompt, scores via the method declared in
``bench.json`` (equivalence | code_tests | llm_judge), prints pass@k / avg, appends
a row to ``results.csv``, and saves raw completions under ``runs/`` (git-ignored).
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
    from harness.client import ChatClient, SamplingConfig
    from harness.judge_copilot import CopilotCLIJudge
    from harness.scorers import code_exec, equivalence, llm_judge
else:
    from .client import ChatClient, SamplingConfig
    from .judge_copilot import CopilotCLIJudge
    from .scorers import code_exec, equivalence, llm_judge

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


VALID_METHODS = {"equivalence", "code_tests", "llm_judge"}


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


def score_one(method: str, manifest: dict, item: dict, completion: str, judge=None) -> dict:
    key = manifest["_key"].get(item["id"], {})
    if method == "equivalence":
        return equivalence.score(completion, key.get("answer", ""))
    if method == "code_tests":
        return code_exec.score(completion, key.get("tests", ""))
    if method == "llm_judge":
        if judge is None:
            raise SystemExit("llm_judge benchmark needs a judge (default claude-opus-4.8 via Copilot CLI)")
        return llm_judge.score(item["prompt"], completion, manifest["_rubric"], judge,
                               pass_threshold=manifest.get("judge", {}).get("pass_threshold", 6.0))
    raise SystemExit(f"unknown scoring method: {method}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run a benchmark against a local model.")
    ap.add_argument("--benchmark", required=True, help="path to benchmarks/<name>/ dir")
    ap.add_argument("--model", required=True, help="Ollama model tag under test")
    ap.add_argument("--k", type=int, default=1, help="samples per prompt (pass@k)")
    ap.add_argument("--limit", type=int, default=0, help="limit number of prompts (0 = all)")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--top-p", type=float, default=0.95)
    ap.add_argument("--top-k", type=int, default=0)
    ap.add_argument("--num-predict", type=int, default=4096)
    ap.add_argument("--num-ctx", type=int, default=8192)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--base-url", default="http://localhost:11434")
    ap.add_argument("--judge-model", default="claude-opus-4.8",
                    help="Copilot CLI model id for llm_judge (a FRONTIER model; "
                         "never a local small model). e.g. claude-opus-4.8, gpt-5.5.")
    ap.add_argument("--judge-effort", default=None,
                    choices=["low", "medium", "high", "xhigh", "max"],
                    help="reasoning effort for the judge (Copilot CLI --reasoning-effort)")
    ap.add_argument("--results", default=str(LAB_BENCH / "results.csv"))
    ap.add_argument("--dry-run", action="store_true", help="print config + first prompt, don't call the model")
    ap.add_argument("--code-sandbox", choices=["local-unsafe"], default=None,
                    help="execution mode for code_tests. Only 'local-unsafe' (host "
                         "subprocess, weak isolation) exists today and is REQUIRED to run "
                         "code_tests. A locked-down Podman mode lands in Batch B.")
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
    )
    client = ChatClient(model=args.model, base_url=args.base_url, sampling=sampling)
    judge = None
    if method == "llm_judge":
        judge = CopilotCLIJudge(model=args.judge_model, effort=args.judge_effort)

    print(f"benchmark={manifest['name']} v{manifest.get('version','?')} method={method} "
          f"items={len(prompts)} k={args.k}")
    print(f"model={args.model} sampling={sampling.to_options()}")
    if args.dry_run:
        if prompts:
            print("\n--- first prompt ---\n" + prompts[0]["prompt"][:500])
        return 0

    if method == "code_tests" and args.code_sandbox != "local-unsafe":
        raise SystemExit(
            "code_tests is gated: it executes model-written code on the host with only "
            "best-effort isolation (timeout + rlimits; no filesystem/network sandbox). "
            "Re-run with --code-sandbox=local-unsafe to accept that risk, or use an "
            "upstream runner (evalplus). A locked-down Podman mode is coming in Batch B.")

    runs_dir = LAB_BENCH / "runs"
    runs_dir.mkdir(exist_ok=True)
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    raw_path = runs_dir / f"{manifest['name']}-{args.model.replace(':', '_')}-{ts}.jsonl"

    item_pass = 0          # items with >=1 correct sample (observed pass@k)
    sample_correct = 0     # total correct samples (for avg)
    total_samples = 0
    tok_s_sum = 0.0
    prompt_tok_sum = 0
    gen_tok_sum = 0
    wall_sum = 0.0
    with raw_path.open("w") as raw:
        for item in prompts:
            any_correct = False
            for s in range(args.k):
                comp = client.complete([{"role": "user", "content": item["prompt"]}],
                                       system=manifest.get("system"))
                res = score_one(method, manifest, item, comp.text, judge)
                total_samples += 1
                tok_s_sum += comp.gen_tok_per_s
                prompt_tok_sum += comp.prompt_tokens
                gen_tok_sum += comp.gen_tokens
                wall_sum += comp.wall_s
                if res.get("correct"):
                    sample_correct += 1
                    any_correct = True
                raw.write(json.dumps({"id": item["id"], "sample_index": s, "result": res,
                                      "prompt_tokens": comp.prompt_tokens,
                                      "gen_tokens": comp.gen_tokens,
                                      "wall_s": comp.wall_s,
                                      "gen_tok_per_s": comp.gen_tok_per_s,
                                      "completion": comp.text}) + "\n")
            if any_correct:
                item_pass += 1
            mark = "OK " if any_correct else "XX "
            print(f"  {mark}{item['id']}")

    n = len(prompts) or 1
    observed_pass_at_k = item_pass / n
    avg_correct = sample_correct / (total_samples or 1)
    mean_tok_s = round(tok_s_sum / (total_samples or 1), 2)
    print(f"\nobserved_pass@{args.k}={observed_pass_at_k:.3f}  avg_correct={avg_correct:.3f}  "
          f"mean_gen_tok/s={mean_tok_s}  raw={raw_path.name}")
    print("  (observed_pass@k = fraction of items with >=1 correct in k samples; "
          "not the formal unbiased pass@k estimator)")

    row = {
        "date": dt.date.today().isoformat(),
        "machine": socket.gethostname(),
        "model": args.model,
        "runner": "ollama-harness",
        "ollama_version": _ollama_version(args.base_url),
        "benchmark": f"{manifest['name']} v{manifest.get('version','?')}",
        "scoring": method,
        "num_ctx": args.num_ctx,
        "num_predict": args.num_predict,
        "sampling": f"t={args.temperature},top_p={args.top_p},top_k={args.top_k}",
        "seed": args.seed,
        "k": args.k,
        "n_items": len(prompts),
        "observed_pass_at_k": round(observed_pass_at_k, 4),
        "avg_correct": round(avg_correct, 4),
        "mean_gen_tok_s": mean_tok_s,
        "prompt_tokens_total": prompt_tok_sum,
        "gen_tokens_total": gen_tok_sum,
        "wall_s_total": round(wall_sum, 1),
        "judge": f"copilot:{args.judge_model}" if method == "llm_judge" else "",
        "code_sandbox": args.code_sandbox or "",
        "raw_file": raw_path.name,
        "platform": platform.platform(),
    }
    results_path = Path(args.results)
    write_header = not results_path.exists()
    with results_path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            w.writeheader()
        w.writerow(row)
    print(f"appended -> {results_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
