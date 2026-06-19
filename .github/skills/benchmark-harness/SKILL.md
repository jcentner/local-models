---
name: benchmark-harness
description: Drive this repo's local benchmark harness (lab/benchmarks/harness) to run a benchmark against a model under test and record results. Use when running a benchmark, choosing a provider (local Ollama vs OpenAI-compatible API like Z.AI GLM), wiring up cost tracking, picking a scorer (equivalence / code_tests / llm_judge), handling thinking-model truncation, or reading/writing results.csv. Complements the /benchmark prompt; defers judge invocation to the copilot-cli skill.
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

- `--provider ollama` (default) — native `/api/chat`. Full `options` control
  (`--num-ctx`, `--no-think`) + native tok/s. Model = an `ollama list` tag.
- `--provider openai-compatible` — `{--base-url}/chat/completions` (base_url ends
  in `/v1`). Targets a hosted API **or** a local model via Ollama's `:11434/v1`
  shim. tok/s is wall-based.
  - Auth: key comes from the env var named by `--api-key-env`. **Never** put a key
    on the CLI or let it reach `results.csv`. localhost needs no key.
- Cost: `--price-in` / `--price-out` (USD per 1M tokens) → `cost_usd` in the row
  (local default 0). Running the same benchmark local vs API and comparing
  capability + `cost_usd` is the point — it's the home-agent model decision.

```bash
# local (default)
python3 -m harness.run --benchmark ../../benchmarks/<name> --model qwen3.5:4b \
  --temperature 0.0 --num-ctx 8192 --seed 0
# API (records cost)
python3 -m harness.run --benchmark ../../benchmarks/<name> --model glm-4.6 \
  --provider openai-compatible --base-url https://api.z.ai/api/paas/v4 \
  --api-key-env ZAI_API_KEY --price-in 0.6 --price-out 2.2 --temperature 0.0
```

## Scorers (declared in the benchmark's bench.json)

- `equivalence` — math/numeric answer matching. Deterministic; use `--temperature 0`.
- `code_tests` — **GATED**: must pass `--code-sandbox podman` (recommended,
  locked-down container) or `local-unsafe` (host exec, opt-in). The runner refuses
  to run model-written code without a sandbox.
- `llm_judge` — rubric judged by a **frontier model via the Copilot CLI**
  (`--judge-model`, default `claude-opus-4.8`; never a local small model). For the
  judge invocation details see the **copilot-cli** skill.

## Thinking-model gotcha (bites every time)

Thinking models (qwen3.5, vibethinker) spend the token budget on CoT and can emit
**empty** output on trivial tasks → scored as a fail.
- ollama provider: add `--no-think` for deterministic code/equivalence runs.
- openai-compatible (incl. Ollama `/v1`): `--no-think` does **not** apply — give a
  generous `--num-predict`, or run via the `ollama` provider instead.
- For long-CoT reasoning, set `--num-ctx` high (e.g. 32768) to avoid mid-thought
  truncation.

## Stochastic models → observed pass@k

Reasoning models run hot (e.g. VibeThinker temp 1.0). One sample is noise: use
`--k 8` and read `observed_pass_at_k` (= fraction of items with ≥1 correct in k;
NOT the formal unbiased pass@k — don't compare to leaderboard pass@k).

## After a run

The row is written automatically (schema: date, machine, model, provider, runner,
runner_version, endpoint, benchmark, scoring, num_ctx, num_predict, sampling, seed,
k, n_items, observed_pass_at_k, avg_correct, mean_gen_tok_s, token totals,
wall_s_total, cost_usd, judge, code_sandbox, raw_file, platform). Results are
**per-environment** (per-machine for local; per-provider + per-date for API).
Add what the harness can't know (quant, VRAM) by hand, then log it: an experiment
folder + a `## [date] bench | …` line in `wiki/log.md`. The full recommend → run →
record workflow is the `/benchmark` prompt.

## Don'ts

- Don't run `code_tests` without `--code-sandbox`.
- Don't use a local small model as the judge.
- Don't put API keys on the CLI or in committed files.
- Don't pull a model without the user's go-ahead.
