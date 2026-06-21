# lab/benchmarks/harness

A thin benchmark runner. Samples prompts against a model under test — **local
(Ollama) or API (OpenAI-compatible, e.g. Z.AI GLM)** — and scores them. It is the
engine for our **authored** datasets under
[`benchmarks/<name>/`](../../../benchmarks/README.md); for standard public suites
we wrap the upstream framework instead (see the per-benchmark wiki pages).

## Layout

```
harness/
  client.py            OllamaClient (native /api/chat) + OpenAICompatibleClient (/v1)
                       + make_client factory; sampling + num_ctx + tok/s
  run.py               CLI: load dataset -> sample k -> score -> results.csv + runs/
  agentic.py           tau-bench-style episode runner + Copilot-CLI user-simulator
  selftest.py          offline test of the scoring core (no model needed)
  scorers/
    equivalence.py     math/numeric answer matching (sympy optional)
    code_exec.py       sandboxed code execution against tests
    llm_judge.py       rubric LLM-judge (pinned judge model)
    agentic.py         state/policy scoring for the agentic rollout
```

## Dataset format (`benchmarks/<name>/`)

```
bench.json       {"name","version","scoring":equivalence|code_tests|llm_judge|agentic,"toolset"?,"system"?,"judge"?,"max_steps"?,"max_turns"?,"slice_fields"?}
prompts.jsonl    {"id","prompt","meta"?}   (agentic support: meta={"persona","policy","kb"}; home: meta={"persona","policy","devices"} where a device may carry "requires":{dep:state}; meta.category/tier are sliceable)
answer_key.jsonl equivalence:{"id","answer"} code_tests:{"id","tests"} agentic-support:{"id","expected_terminal","required_tools","forbidden_tools"} agentic-home:{"id","expected_state","forbidden_devices","require_confirm","require_clarify"?,"forbidden_device_attempts"?,"required_any"?} (either toolset: +"judge_message":{tool,criteria,pass_threshold}; tool may be a name OR a list) llm_judge:(rubric.md)
rubric.md        for llm_judge benchmarks
```

The answer key is loaded separately and **never sent to the model under test**.

## Run

```bash
cd lab/benchmarks
# verify the scoring core (no model/network):
python3 -m harness.selftest

# dry run (prints config + first prompt, no model call):
python3 -m harness.run --benchmark ../../benchmarks/<name> --model qwen3.5:4b --dry-run

# real run against a pulled Ollama model (local, the default provider):
# (k defaults to 3 -> reports observed_pass@k AND pass^k reliability; --k 1 = smoke.
#  run reliability at the model's recommended temp, NOT temp=0 - see eval-reliability)
python3 -m harness.run --benchmark ../../benchmarks/<name> \
  --model qwen3.5:4b --k 3 --num-ctx 8192 --seed 0

# real run against an API model (OpenAI-compatible; records cost_usd):
python3 -m harness.run --benchmark ../../benchmarks/<name> \
  --model glm-4.6 --provider openai-compatible --base-url https://api.z.ai/api/paas/v4 \
  --api-key-env ZAI_API_KEY --price-in 0.6 --price-out 2.2 --temperature 0.0

# same harness can target a LOCAL model over Ollama's OpenAI shim (no key):
python3 -m harness.run --benchmark ../../benchmarks/<name> \
  --model qwen3.5:4b --provider openai-compatible --base-url http://localhost:11434/v1

# reliability run for a stochastic reasoning model (higher k sharpens pass^k):
python3 -m harness.run --benchmark ../../benchmarks/<name> \
  --model vibethinker-3b --k 8 --temperature 1.0 --top-p 0.95 --num-ctx 32768

# code_tests is GATED - it must be opted into a sandbox mode:
python3 -m harness.run --benchmark ../../benchmarks/<code-bench> \
  --model qwen3.5:4b --code-sandbox podman --no-think

# llm-judged (open-ended) benchmark - judge is opus-4.8 via Copilot CLI (default):
python3 -m harness.run --benchmark ../../benchmarks/<name> \
  --model <under-test> --judge-model claude-opus-4.8

# agentic rollout (tool-use) - agent under test + Copilot user-simulator:
python3 -m harness.run --benchmark ../../benchmarks/email-triage \
  --model qwen3.5:4b --no-think --temperature 0 --user-model claude-opus-4.8

# same, but native function-calling (Ollama/OpenAI `tools`) for a tool-capable model:
python3 -m harness.run --benchmark ../../benchmarks/email-triage \
  --model qwen3.5:4b --tool-protocol native --no-think --temperature 0
```

Datasets live under [`benchmarks/<name>/`](../../../benchmarks/README.md) and are
created with `/author-benchmark`. Output: a row appended to
[`../results.csv`](../README.md) and raw completions under `../runs/` (git-ignored).

## Providers & cost

- `--provider ollama` (default) — native `/api/chat`; full `options` control
  (`num_ctx`, `think`) + native `eval_count`/`eval_duration` tok/s.
- `--provider openai-compatible` — `{--base-url}/chat/completions` (base_url ends
  in `/v1`). Targets hosted APIs **or** Ollama's `:11434/v1` shim **or** a local
  **[SGLang](../../../wiki/stacks/sglang.md)** server. tok/s is wall-based. The API
  key is read from the env var named by `--api-key-env` (**never** put a key on the
  CLI or in `results.csv`); localhost needs none.
- **Thinking control over `openai-compatible`:** `--think/--no-think` is sent as
  `chat_template_kwargs.enable_thinking` (works on SGLang; ignored by servers that
  don't support it) — the analogue of Ollama's `think`.
- **`--system-suffix "<text>"`** appends text to the system prompt at run time (e.g.
  a brevity nudge to tame an over-thinking model's CoT). A **run param** recorded in
  the raw jsonl, NOT a `bench.json` edit — the eval stays pure and comparable across
  models. Applies to both the generative (e.g. decision-reasoning) and agentic paths.
- **XML tool-call fallback:** when a provider returns no native `tool_calls` but the
  content holds MiniCPM-style `<function name=...><param ...>` XML,
  `parse_xml_tool_calls()` recovers it into native calls. Run SGLang **without**
  `--tool-call-parser` (its `minicpm5` parser is broken in 0.5.13 — swallows the XML).
- `--price-in` / `--price-out` (USD per 1M tokens) — compute `cost_usd` from token
  totals (local default 0 -> `cost_usd=0.0`). Running the same benchmark local vs
  API and comparing capability + `cost_usd` is a first-class goal.

## Scoring methods

- **equivalence** — extracts `\boxed{}` / "answer is" / last number, compares
  numerically (sympy if installed). Deterministic.
- **code_tests** — strips code fences, appends the test snippet, runs the program,
  and checks the exit code. **Gated**: the runner refuses `code_tests` unless you
  pass `--code-sandbox`:
  - `podman` (recommended) — throwaway locked-down container (`--network none`,
    read-only rootfs, tmpfs workdir, memory/pid/cpu caps, non-root, caps dropped).
    Needs Podman ([WSL2 setup](https://github.com/jcentner/podman-wsl-setup)) and a
    Python image (`podman pull docker.io/library/python:3.12-slim`; override via
    `HARNESS_PODMAN_IMAGE`).
  - `local-unsafe` — host subprocess + rlimits; weak isolation, explicit opt-in.
  For public suites prefer an upstream runner (evalplus). **Thinking-model gotcha:**
  pass `--no-think` for code tasks - a model that over-thinks can exhaust
  `--num-predict` before emitting code, yielding empty output (scored as a fail).
  `--no-think`/`--think` works on **ollama** (the `think` flag) AND on
  `openai-compatible` via `chat_template_kwargs.enable_thinking` (works on SGLang -
  verified: MiniCPM5-1B ran `--no-think` over SGLang; ignored by Ollama's `/v1`
  shim and servers that don't support it). Give a generous `--num-predict`
  regardless so CoT can't truncate the answer.
- **reliability metrics (multi-pass)** - over `--k` samples per item the runner
  reports `observed_pass_at_k` (best-of-k, >=1 correct - a capability ceiling that
  *rises* with k), **`pass_hat_k`** (tau-bench's pass^k, ALL k correct - reliability,
  the home-agent signal), `avg_correct`, **`flaky_items`** (0<correct<k), and
  **`sem`** (standard error of the per-item mean). `--k` defaults to **3**;
  `--slice-by <meta field>` prints per-group reliability. `observed_pass_at_k` is
  **not** the formal unbiased pass@k estimator used on public leaderboards - don't
  compare the two. Rationale + house rules:
  [eval-reliability](../../../wiki/concepts/eval-reliability.md).
- **llm_judge** — a **frontier** judge scores the response against `rubric.md` and
  returns JSON. The default backend is `judge_copilot.CopilotCLIJudge`
  (`claude-opus-4.8` via the Copilot CLI; use `gpt-5.5` for a second opinion).
  **Never a local small model.** The judge config (model+version+rubric) is
  recorded with the result; LLM-judged scores only compare within the same config.
- **agentic** — a model-agnostic tau-bench-style **rollout**: the agent under test
  (any Ollama tag / API model) talks to a **Copilot-CLI user-simulator**
  (`--user-model`, a frontier model playing a persona with a hidden goal) over
  mocked tools. Scored **deterministically** on the terminal action (reply vs
  escalate) + required/forbidden tool use - no model registration needed (the
  flexible alternative to BFCL). Two tool protocols via `--tool-protocol`:
  - `prompt` (default) — the model emits one JSON action per step. Works with
    **any** tag/API, no native function-calling needed.
  - `native` — tools are passed via the provider's function-calling API (Ollama
    `/api/chat` `tools` or OpenAI `tools`) and we read `message.tool_calls`. A
    **fair footing for thinking / XML-tool models** whose native format isn't bare
    JSON. Needs a **tool-capable** model/template (Ollama: `ollama show <m>` lists
    `tools`; MiniCPM5's native XML path needs SGLang `--tool-call-parser minicpm5`
    over the `openai-compatible` provider — its stock Ollama template is tool-blind).
    Measured: qwen3.5:4b on email-triage went 3/5 (prompt) -> 4/5 (native).
  Two **tool sets** (`bench.json` `toolset`): **support** (act/ask/escalate over a
  KB - [email-triage](../../../benchmarks/email-triage/README.md)) and
  **home_automation** (act/confirm/refuse over a device world, with
  confirm-before-sensitive + don't-over-actuate checks -
  [home-automation](../../../benchmarks/home-automation/README.md), the lighthouse
  set). Adding a domain = a tool schema + an apply-fn + a scorer branch.
  - **support** `ask` is **respond-and-continue** (clarify, the user answers, the
    agent resolves); for an ambiguity item an applied `ask` must precede the final
    reply/escalate and a stalled episode fails.
  - **home** `ask` takes an optional `device`: a **device-aware** `require_confirm`
    checks an `ask.device == dev` before the first `set_device` on `dev` (vs a
    device-agnostic `require_clarify` for ambiguity). A device may declare
    `requires:{dep:state}` - `set_device` returns BLOCKED and does not mutate until
    the precondition holds (raise the per-turn budget with `bench.json` `max_steps`).
    `forbidden_device_attempts` fails an *attempted* change to a forbidden device
    even when a BLOCKED/no-op/skipped-native-sibling left state unchanged (safety /
    prompt-injection items; scans all emitted `set_device` calls, not just applied).
    `expected_state` values may be a scalar OR a list of acceptable scalars (synonym
    states, e.g. an alarm `["disarmed","off","disabled"]`).
    `required_any` (a list of OR-groups, e.g. `[["say","ask"]]`) requires >=1 applied
    tool from each group - so a *grounding* decline can arrive via `say` OR `ask`
    without a hard `say` rule false-failing it, while a silent no-op still fails.
  - **`--judge-messages`** (default off) adds an optional frontier-judge check of one
    message's text (key `judge_message:{tool,criteria,pass_threshold}`; `tool` may be a
    single name or a list, e.g. `["say","ask"]`, grading the LAST applied of them) as an
    AND gate over the deterministic result - e.g. a fabrication or injection-resistance
    check. Fail-closed; reuses `--judge-model`/`--judge-effort`.
  - Each raw run line carries a whitelisted flat `meta` ({tier,category}) so the
    [run-viewer](../../../tools/run-viewer/README.md) can slice reliability per
    category (no `results.csv` change; absent meta = a no-op). `bench.json` may
    *narrow* the whitelist via `slice_fields`, never widen it.

## Wrapping upstream frameworks

For HumanEval+/MBPP+ use [evalplus](https://github.com/evalplus/evalplus); for
broad task coverage use [lm-eval-harness](https://github.com/EleutherAI/lm-evaluation-harness)
(both can target Ollama's OpenAI-compatible endpoint on `:11434`). Document the
exact command on the benchmark's wiki page and record results in the same
`results.csv` schema. Don't reimplement these.

## Dependencies

stdlib only for the core. `sympy` optionally improves math equivalence
(`pip install sympy` in a venv). Upstream frameworks (evalplus, lm-eval) install
into a venv per their docs.
