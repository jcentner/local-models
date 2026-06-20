# lab/benchmarks

Numbers, captured consistently so they're comparable over time.

## Always record

| Field | Example |
|---|---|
| date | 2026-06-14 |
| machine | proart-p16 |
| model | qwen3.5:9b-q4_K_M |
| provider | ollama / openai-compatible |
| quant | Q4_K_M |
| runner + version | ollama-harness 0.20.2 / openai-compatible-harness |
| endpoint | http://localhost:11434 / https://api.z.ai/.../v1 |
| context length | 4096 |
| GPU layers (-ngl) | 99 (full) / 20 (partial) |
| sampling | temp 1.0, top_p 0.95, top_k 0 |
| seed | 0 (or none) |
| n-samples / k | k=3 (default; k=1 = quick smoke) |
| benchmark + version | humaneval-plus v0.2 |
| score | observed_pass@k 0.78, **pass^k 0.50** (reliability), avg_correct 0.71, flaky 3 |
| cost (API) | cost_usd 0.0042 (from --price-in/--price-out) |
| judge (if LLM-judged) | opus-4.8 @ 2026-06-18, rubric v1 |
| prompt tok/s | |
| generation tok/s | |
| VRAM used | from `nvidia-smi` / `ollama ps` |
| RAM used | from `free -h` |
| notes | thermal, throttling, fit |

**The harness writes most of this automatically** (`harness/run.py` -> `results.csv`):
date, machine, model, **provider**, runner, **runner_version**, **endpoint**,
benchmark+version, scoring, num_ctx, num_predict, sampling, seed, k, n_items,
observed_pass_at_k, **pass_hat_k**, avg_correct, **flaky_items**, **sem**,
mean_gen_tok_s, prompt/gen token totals, wall_s_total, **cost_usd**, judge,
code_sandbox, raw_file, platform. Add the few it can't know (quant, VRAM/RAM, -ngl,
notes) by hand. Results are **per-environment**: per-machine for local, per-provider
+ per-date for API (prices drift).
**Two capability metrics, always reported together** (see
[eval-reliability](../../wiki/concepts/eval-reliability.md)): `observed_pass_at_k` =
fraction of items with >=1 correct in k (best-of-k *ceiling* - **not** the unbiased
public-leaderboard pass@k, don't compare); **`pass_hat_k`** = fraction correct on
ALL k (tau-bench pass^k = **reliability**). `flaky_items` counts items inconsistent
across k; `sem` is the standard error of the per-item mean.

## Where results live

- `results.csv` — one row per run, written by the harness (created on first run).
- `runs/` — raw per-sample output (git-ignored; keep only distilled numbers in csv).
- Short writeups can become `wiki/` pages (e.g. a quant comparison) so they
  compound.

## Tools

- **Ollama**: `ollama run --verbose ...` reports eval rate; `ollama ps` shows VRAM.
- **llama.cpp**: `llama-bench` is the standard prompt-vs-gen throughput tool.
  See [../../wiki/stacks/llama-cpp.md](../../wiki/stacks/llama-cpp.md).

## First baseline (TODO)
Baseline both installed models so later changes have a reference point:
`qwen3.5:4b` and `qwen3.5:9b-q4_K_M`, full GPU offload, 4k context.
