---
title: Quantization (and the VRAM math)
tags: [concept, quantization, optimization]
updated: 2026-06-14
status: seed
---

# Quantization

Lowering the numeric precision of weights (and sometimes activations / KV cache)
to shrink memory and speed up inference, trading a little quality. It is the
single most important lever for **fitting a model in a given VRAM budget** — and
on a small GPU it is often the difference between fits-fully and doesn't-run. This
page is a seed — deepen it with experiments under `lab/`.

## Quick VRAM math

Rough rule: **bits-per-weight ÷ 8 × params = bytes for weights**, then add KV
cache + overhead.

| Precision | Bits/weight | A 7B model ≈ | A 13B model ≈ |
|---|---|---|---|
| FP16 / BF16 | 16 | ~14 GB | ~26 GB |
| INT8 / Q8 | 8 | ~7 GB | ~13 GB |
| Q4 (K-quants) | ~4.5 | ~4–4.5 GB | ~7.5–8 GB |
| FP4 / NVFP4 | 4 | ~3.5–4 GB | ~7 GB |

KV cache grows with context length and competes with weights for VRAM, so the
usable model size is always a bit below the raw weight size.

> **Worked example — an 8 GB GPU:** **~7–9B at Q4 fits fully**; 13B at Q4 is
> borderline (needs partial CPU offload + the [WSL RAM bump](wsl2-memory.md)).
> Per-host budgets live under [hardware/](../hardware/).

## Families to know

- **GGUF K-quants** (llama.cpp / Ollama): `Q4_K_M`, `Q5_K_M`, `Q6_K`, `Q8_0`.
  `Q4_K_M` is the usual sweet spot for quality-per-byte. **imatrix** (importance
  matrix) quants improve low-bit quality. This is the daily-driver format here.
- **bitsandbytes** (`nf4`, `int8`): on-the-fly quantization in HF Transformers;
  used by Unsloth for 4-bit training/inference.
- **AWQ / GPTQ**: 4-bit post-training quant popular with [vLLM](../stacks/vllm.md)
  for fast batched serving.
- **FP8 (W8A8) / NVFP4 (W4A4)**: hardware-accelerated on Blackwell's 5th-gen
  tensor cores — a genuinely relevant angle on Blackwell GPUs. See
  [hardware/blackwell-rtx5070.md](../hardware/blackwell-rtx5070.md).
- **KV-cache quantization**: quantize the cache (e.g. to 8-bit) to fit longer
  contexts in limited VRAM.

## What to actually measure (turn into benchmarks)

For a given model, compare quants on: tokens/s (prompt + generation), VRAM used,
and quality on a small task set. File results in
[../../lab/benchmarks/](../../lab/benchmarks/). A good first experiment: same
model at `Q4_K_M` vs `Q5_K_M` vs `Q8_0`, tok/s and VRAM, fully-offloaded vs
partial.

## Open questions
- How much does imatrix actually help at Q4 on these models?
- Where's the quality cliff for small-GPU practical models (7–9B)?
- Does NVFP4 give usable speed/space wins via a stack that supports it?
