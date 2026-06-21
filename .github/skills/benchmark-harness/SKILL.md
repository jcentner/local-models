---
name: benchmark-harness
description: Drive this repo's local benchmark harness (lab/benchmarks/harness) to run a benchmark against a model under test and record results. Use when running a benchmark, choosing a provider (local Ollama vs OpenAI-compatible API like Z.AI GLM), wiring up cost tracking, picking a scorer (equivalence / code_tests / llm_judge / agentic tool-use rollout), handling thinking-model truncation, or reading/writing results.csv. Complements the /benchmark prompt; defers judge invocation to the copilot-cli skill.
user-invocable: false
---

# Benchmark harness — how to run it

The runner lives at [lab/benchmarks/harness](../../../lab/benchmarks/harness/README.md).
It samples prompts against a model under test (local **or** API), scores them, and
appends one row to `lab/benchmarks/results.csv` (raw output to git-ignored `runs/`).
Run everything from `lab/benchmarks/`.

## Always verify first (no model / network)

```bash
cd lab/benchmarks && python3 -m harness.selftest   # must end "ALL PASS"
```

## Providers (local vs API)

- `--provider ollama` (default) — native [`/api/chat`](https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-chat-completion)
  (docs moving to [docs.ollama.com/api](https://docs.ollama.com/api)). Full `options`
  control (`--num-ctx`, `--no-think` → the `think` param) + native tok/s from
  `eval_count`/`eval_duration`. Model = an `ollama list` tag.
- `--provider openai-compatible` — `{--base-url}/chat/completions`, the
  [OpenAI Chat Completions](https://platform.openai.com/docs/api-reference/chat)
  wire format (base_url ends in `/v1`). Targets a hosted API **or** a local model
  via Ollama's OpenAI-compatible endpoint on `:11434/v1` (see
  [Ollama docs](https://docs.ollama.com/api)). tok/s is wall-based (no
  `eval_duration` over `/v1`).
  - Auth: key comes from the env var named by `--api-key-env`. **Never** put a key
    on the CLI or let it reach `results.csv`. localhost needs no key.
- Cost: `--price-in` / `--price-out` (USD per 1M tokens) → `cost_usd` in the row
  (local default 0). Running the same benchmark local vs API and comparing
  capability + `cost_usd` is the point — it's the home-agent model decision.

```bash
# local (default)
python3 -m harness.run --benchmark ../../benchmarks/<name> --model qwen3.5:4b \
  --temperature 0.0 --num-ctx 8192 --seed 0
# API (records cost). base-url + prices are ILLUSTRATIVE - check the provider's
# current API + pricing docs (e.g. Z.AI GLM) before trusting them.
python3 -m harness.run --benchmark ../../benchmarks/<name> --model glm-4.6 \
  --provider openai-compatible --base-url https://api.z.ai/api/paas/v4 \
  --api-key-env ZAI_API_KEY --price-in 0.6 --price-out 2.2 --temperature 0.0
```

## Scorers (declared in the benchmark's bench.json)

- `equivalence` — math/numeric answer matching. Deterministic; use `--temperature 0`.
- `code_tests` — **GATED**: must pass `--code-sandbox podman` (recommended,
  locked-down container) or `local-unsafe` (host exec, opt-in). The runner refuses
  to run model-written code without a sandbox. Podman setup:
  [jcentner/podman-wsl-setup](https://github.com/jcentner/podman-wsl-setup). For
  public coding suites prefer wrapping [evalplus](https://github.com/evalplus/evalplus)
  (HumanEval+/MBPP+) per [wiki/benchmarks/humaneval-plus.md](../../../wiki/benchmarks/humaneval-plus.md).
- `llm_judge` — rubric judged by a **frontier model via the Copilot CLI**
  (`--judge-model`, default `claude-opus-4.8`; never a local small model). For the
  judge invocation details see the **copilot-cli** skill.
- `agentic` — model-agnostic tau-bench-style tool-use **rollout**: the agent under
  test talks to a **Copilot-CLI user-simulator** (`--user-model`, a frontier model
  with a hidden goal) over mocked tools; scored deterministically on terminal action
  (reply vs escalate) + required/forbidden tools. Use `--no-think`. Two tool
  protocols via `--tool-protocol`:
  - `prompt` (default) — one JSON action per step; works with **any** model.
  - `native` — provider function-calling (Ollama `/api/chat` `tools` or OpenAI
    `tools`, parsing `message.tool_calls`); a fair footing for thinking/XML-tool
    models. Needs a **tool-capable** model (`ollama show <m>` must list `tools`);
    MiniCPM5's native XML needs SGLang `--tool-call-parser minicpm5` over the
    `openai-compatible` provider (its stock Ollama template is tool-blind).
    Measured: qwen3.5:4b 3/5 (prompt) → 4/5 (native) on email-triage.
  Two **tool sets** (`bench.json` `toolset`): **support** (act/ask/escalate over a KB,
  [email-triage](../../../benchmarks/email-triage/README.md)) and **home_automation**
  (act/confirm/refuse over a device world, [home-automation](../../../benchmarks/home-automation/README.md) -
  the lighthouse set; scores device end-state + confirm-before-sensitive + don't-over-actuate).
  The flexible alternative to registered-model benchmarks like BFCL.

## Thinking-model gotcha (bites every time)

Thinking models (qwen3.5, vibethinker) spend the token budget on CoT and can emit
**empty** output on trivial tasks → scored as a fail.
- ollama provider: add `--no-think` for deterministic code/equivalence runs.
- openai-compatible (incl. Ollama `/v1`): `--no-think` does **not** apply — give a
  generous `--num-predict`, or run via the `ollama` provider instead.
- For long-CoT reasoning, set `--num-ctx` high (e.g. 32768) to avoid mid-thought
  truncation.

## Stochastic models → reliability (observed pass@k AND pass^k)

Reasoning models run hot (e.g. VibeThinker temp 1.0) and small/quantized models
flake. One sample is noise. `--k` defaults to **3**; read **both** metrics:
`observed_pass_at_k` (best-of-k, ≥1 correct — a ceiling that rises with k; NOT the
unbiased leaderboard pass@k, don't compare) and **`pass_hat_k`** (tau-bench pass^k,
ALL k correct — reliability, weight this for the home agent), plus `flaky_items` and
`sem`. Run reliability passes at the recommended temp, not temp=0. `--slice-by
<meta>` breaks it down per group. Rationale: wiki/concepts/eval-reliability.md.

## After a run

The row is written automatically (schema: date, machine, model, provider, runner,
runner_version, endpoint, benchmark, scoring, num_ctx, num_predict, sampling, think, seed,
k, n_items, observed_pass_at_k, pass_hat_k, avg_correct, flaky_items, sem,
mean_gen_tok_s, token totals,
wall_s_total, cost_usd, judge, code_sandbox, raw_file, platform). `think` is the
run-time CoT control (`on|off|default`; `default` = no flag, template/provider
default governs - interpret alongside provider + model). Results are
**per-environment** (per-machine for local; per-provider + per-date for API).
Add what the harness can't know (quant, VRAM) by hand, then log it: an experiment
folder + a `## [date] bench | …` line in `wiki/log.md`. The full recommend → run →
record workflow is the `/benchmark` prompt.

## Don'ts

- Don't run `code_tests` without `--code-sandbox`.
- Don't use a local small model as the judge.
- Don't put API keys on the CLI or in committed files.
- Don't pull a model without the user's go-ahead.

## References (grounding)

- Ollama native API (`/api/chat`, `options`, `think`, `eval_count`/`eval_duration`):
  https://github.com/ollama/ollama/blob/main/docs/api.md · https://docs.ollama.com/api
- OpenAI Chat Completions wire format (the `openai-compatible` path):
  https://platform.openai.com/docs/api-reference/chat
- Podman rootless on WSL2 (the `code_tests` sandbox): https://github.com/jcentner/podman-wsl-setup
- Coding-suite wrap target — evalplus: https://github.com/evalplus/evalplus
- Tool-use/agentic wrap target — BFCL (install `bfcl-eval`, **not** `bfcl`):
  https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard
- Repo-internal: [harness README](../../../lab/benchmarks/harness/README.md),
  [benchmark system](../../../wiki/benchmarks/README.md), the `/benchmark` +
  `/new-benchmark` prompts, and the **copilot-cli** skill (judge invocation).
