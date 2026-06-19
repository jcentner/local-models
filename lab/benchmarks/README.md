# lab/benchmarks

Numbers, captured consistently so they're comparable over time.

## Always record

| Field | Example |
|---|---|
| date | 2026-06-14 |
| machine | proart-p16 |
| model | qwen3.5:9b-q4_K_M |
| quant | Q4_K_M |
| runner + version | ollama 0.20.2 / llama.cpp <sha> |
| context length | 4096 |
| GPU layers (-ngl) | 99 (full) / 20 (partial) |
| sampling | temp 1.0, top_p 0.95, top_k 0 |
| seed | 0 (or none) |
| n-samples / k | observed_pass@1 (1) / observed_pass@16 (16) |
| benchmark + version | humaneval-plus v0.2 |
| score | observed_pass_at_k 0.78, avg_correct 0.71 |
| judge (if LLM-judged) | opus-4.8 @ 2026-06-18, rubric v1 |
| prompt tok/s | |
| generation tok/s | |
| VRAM used | from `nvidia-smi` / `ollama ps` |
| RAM used | from `free -h` |
| notes | thermal, throttling, fit |

**The harness writes most of this automatically** (`harness/run.py` -> `results.csv`):
date, machine, model, runner, ollama_version, benchmark+version, scoring, num_ctx,
num_predict, sampling, seed, k, n_items, observed_pass_at_k, avg_correct,
mean_gen_tok_s, prompt/gen token totals, wall_s_total, judge, code_sandbox,
raw_file, platform. Add the few it can't know (quant, VRAM/RAM, -ngl, notes) by
hand. `observed_pass_at_k` = fraction of items with >=1 correct in k - **not** the
formal unbiased pass@k estimator; don't compare it to public-leaderboard pass@k.

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
