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
| n-samples / k | pass@1 (1) / pass@16 (16) |
| benchmark + version | humaneval-plus v0.2 |
| score | 0.78 (pass@1) |
| judge (if LLM-judged) | opus-4.8 @ 2026-06-18, rubric v1 |
| prompt tok/s | |
| generation tok/s | |
| VRAM used | from `nvidia-smi` / `ollama ps` |
| RAM used | from `free -h` |
| notes | thermal, throttling, fit |

**Why the extra fields vs a plain tok/s log:** benchmark numbers are only
comparable if sampling, seed, sample count, and (for open-ended evals) the judge
are pinned. Reasoning models at temp 1.0 are stochastic — report pass@k / avg@k,
not a single pass. `machine` is required because results are per-machine.

## Where results live

- `results.csv` — one row per run (create when the first benchmark lands).
- `runs/` — raw tool output (git-ignored; keep only distilled numbers in csv).
- Short writeups can become `wiki/` pages (e.g. a quant comparison) so they
  compound.

## Tools

- **Ollama**: `ollama run --verbose ...` reports eval rate; `ollama ps` shows VRAM.
- **llama.cpp**: `llama-bench` is the standard prompt-vs-gen throughput tool.
  See [../../wiki/stacks/llama-cpp.md](../../wiki/stacks/llama-cpp.md).

## First baseline (TODO)
Baseline both installed models so later changes have a reference point:
`qwen3.5:4b` and `qwen3.5:9b-q4_K_M`, full GPU offload, 4k context.
