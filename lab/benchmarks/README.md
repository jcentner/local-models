# lab/benchmarks

Numbers, captured consistently so they're comparable over time.

## Always record

| Field | Example |
|---|---|
| date | 2026-06-14 |
| model | qwen3.5:9b-q4_K_M |
| quant | Q4_K_M |
| runner + version | ollama 0.20.2 / llama.cpp <sha> |
| context length | 4096 |
| GPU layers (-ngl) | 99 (full) / 20 (partial) |
| prompt tok/s | |
| generation tok/s | |
| VRAM used | from `nvidia-smi` / `ollama ps` |
| RAM used | from `free -h` |
| notes | thermal, throttling, fit |

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
