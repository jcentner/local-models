# Gemma-4-12B v2 — quant × KV × offload sweep (8 GB VRAM)

- Date: staged 2026-06-20 (not yet run)
- Machine: ASUS ProArt P16 (RTX 5070 Laptop, **8 GB** VRAM, WSL2, ~15 GB WSL RAM) — see [proart-p16](../../../wiki/hardware/proart-p16.md)
- Model: [gemma-4-12b-agentic-fable5](../../../wiki/models/gemma-4-12b-agentic-fable5.md) (yuxinlu1 v2 GGUF)
- Runner: **llama.cpp `llama-server` / `llama-bench`** (needs `gemma4_unified` + `--jinja` for tools — Ollama can't do this)

## Question / hypothesis

On an 8 GB card, Q4_K_M (7.38 GB) won't fully fit with usable context, while
Q3_K_M (6.09 GB) will. Two ways to make the higher-quality Q4 usable: shrink the
KV cache (`q4_0`) to keep everything on GPU, or offload a few layers to CPU.
**Which wins on the throughput ↔ quality trade-off?** Concretely:

- **A — Q3_K_M, full GPU:** fast, lower-precision weights. Baseline.
- **B — Q4_K_M + `q4_0` KV, full GPU:** better weights, degraded KV, stays on GPU.
- **C — Q4_K_M + partial CPU offload, `f16`/`q8_0` KV:** better weights + full KV, but offload tax.

Hypotheses: throughput **A ≳ B ≫ C** (C is bandwidth-bound on CPU); quality
**Q4 (B,C) ≥ Q3 (A)**, with **B possibly < C** if `q4_0` KV hurts long-context
fidelity. Net question: is Q4 worth it over Q3 at this VRAM, and which fitting
trick pays off?

> **Confound (be honest):** B vs A changes **both** weight quant *and* KV type;
> C vs B changes KV type *and* offload. So this answers the *practical* "best
> 8 GB config," not a clean one-variable quant-quality isolation. Optional clean
> add-on cell: **A′ — Q3_K_M + `q4_0` KV** (isolates KV effect) and/or
> **Q4_K_M full-GPU @ ~4K ctx** (isolates offload). Add if results are ambiguous.

Fixed across cells: `--ctx-size 16384`, `-fa on`, `--jinja`, temp/top_p/top_k =
1.0 / 0.95 / 64 (greedy for code_tests), same prompts, same seed.

## Prerequisite — build llama.cpp (not installed here)

No host CUDA toolkit (`nvcc` absent). Build/run in a CUDA container via the
**verified rootless-podman GPU** path ([Blackwell sm_120 → CUDA 12.8](../../../wiki/hardware/blackwell-rtx5070.md)),
or install the toolkit. See [stacks/llama-cpp.md](../../../wiki/stacks/llama-cpp.md).
For the optional MTP speculative-decoding run, pin build **`b9553`** (newer builds
crash on the draft).

## Method (planned — do NOT download/run until confirmed)

```bash
# 0. Get the quants (Q3_K_M + Q4_K_M ≈ 13.5 GB)
hf download yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF \
  --include "*Q3_K_M*" "*Q4_K_M*" --local-dir ~/models/gemma4-v2

# --- THROUGHPUT (llama-bench: clean prompt-eval + gen tok/s, sweeps offload) ---
# A: Q3_K_M full GPU
llama-bench -m ~/models/gemma4-v2/*Q3_K_M*.gguf -ngl 99 -fa 1 -p 512 -n 128
# B: Q4_K_M + q4_0 KV, full GPU
llama-bench -m ~/models/gemma4-v2/*Q4_K_M*.gguf -ngl 99 -fa 1 \
  -ctk q4_0 -ctv q4_0 -p 512 -n 128
# C: Q4_K_M + partial offload (tune NGL down until it fits; e.g. 32)
llama-bench -m ~/models/gemma4-v2/*Q4_K_M*.gguf -ngl 32 -fa 1 -p 512 -n 128
# record prompt tok/s, gen tok/s, and `nvidia-smi`/`free -g` VRAM+RAM per cell.

# --- QUALITY (llama-server + harness; one server per cell, same flags) ---
# Cell A example (swap -m / -ctk / -ngl per cell):
llama-server -m ~/models/gemma4-v2/*Q3_K_M*.gguf -ngl 99 -fa on --jinja \
  --ctx-size 16384 --temp 1.0 --top-p 0.95 --top-k 64 \
  --host 127.0.0.1 --port 18080

# then, per cell, run both a deterministic-coding and an agentic benchmark:
cd /home/jakce/utils/local-models/lab/benchmarks
# deterministic coding (clean quality signal, Podman sandbox):
python3 -m harness.run --benchmark ../../benchmarks/code-basics \
  --model gemma4-v2-Q3_K_M --provider openai-compatible \
  --base-url http://127.0.0.1:18080/v1 --temperature 0 \
  --num-ctx 16384 --num-predict 2048 --code-sandbox podman
# agentic tool-use (the capability that matters; native Gemma 4 tool format):
python3 -m harness.run --benchmark ../../benchmarks/home-automation \
  --model gemma4-v2-Q3_K_M --provider openai-compatible \
  --base-url http://127.0.0.1:18080/v1 --tool-protocol native \
  --num-ctx 16384 --num-predict 2048 --user-model claude-opus-4.8
```

Repeat the QUALITY block for B (`Q4_K_M`, `q4_0` KV) and C (`Q4_K_M`, `-ngl 32`),
relabeling `--model` so [results.csv](../../benchmarks/results.csv) keeps the
cells distinct.

## Result (matrix to fill)

| Cell | Quant | KV | -ngl | prompt tok/s | gen tok/s | VRAM | RAM | code-basics | home-automation |
|---|---|---|---|---|---|---|---|---|---|
| A | Q3_K_M | f16 | 99 | | | | | | |
| B | Q4_K_M | q4_0 | 99 | | | | | | |
| C | Q4_K_M | f16/q8_0 | ~32 | | | | | | |

Record per the harness: model, quant, runner+version (llama.cpp build), context,
`-ngl`, tok/s (prompt+gen), VRAM/RAM, **machine = ProArt P16**, date.

## Learnings

(blank — after the run, update
[wiki/models/gemma-4-12b-agentic-fable5.md](../../../wiki/models/gemma-4-12b-agentic-fable5.md)
"Can it run here?" with the winning 8 GB config, append a `bench` line to
[wiki/log.md](../../../wiki/log.md), and note whether v2 beat base on our own
agentic set — the unverified-self-eval question.)

Capture specifically:
- Best **8 GB config** (throughput vs quality Pareto): is Q4's quality bump worth
  the speed cost vs Q3 full-GPU?
- Does `q4_0` KV measurably hurt agentic/long-context quality vs full KV?
- v2 **vs base** gemma-4-12B-it on our agentic set (validates the ~3.5× claim under
  our harness, not the author's self-eval).
