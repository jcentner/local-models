---
title: Ollama
tags: [stack, runner, gguf]
updated: 2026-06-14
status: installed
---

# Ollama — the daily driver

Easiest way to pull and run GGUF models locally. **Already installed (0.20.2)**
and working on this machine. OpenAI-compatible API on `:11434`.

## Why it's the default here

- Zero-fuss model management (`pull`/`run`/`list`), bundles its own CUDA runtime
  so the [Blackwell CUDA 12.8 gotcha](../hardware/blackwell-rtx5070.md) doesn't
  apply.
- OpenAI-compatible endpoint — easy to point tools/scripts at.
- GGUF + automatic GPU/CPU split based on what fits in the 8 GB GPU.

## Installed models (verified 2026-06-14)

| Model | Size | Fits 8 GB? |
|---|---|---|
| `qwen3.5:9b-q4_K_M` | 6.6 GB | yes, with KV headroom |
| `qwen3.5:4b` | 3.4 GB | comfortably |

## Commands

```bash
ollama list                       # installed models
ollama run qwen3.5:4b "..."       # chat
ollama ps                         # loaded models + VRAM use
ollama pull <model>               # download
# OpenAI-compatible API:
curl http://localhost:11434/v1/chat/completions \
  -d '{"model":"qwen3.5:4b","messages":[{"role":"user","content":"hi"}]}'
```

## Notes / limits

- Great for chat and quick evals; not for high-throughput batched serving (that's
  [vLLM](vllm.md)).
- Does **not** run [DiffusionGemma](../models/diffusiongemma.md) — that needs a
  diffusion sampler stock llama.cpp/Ollama lack.
- For tok/s + VRAM baselines, file results in
  [../../lab/benchmarks/](../../lab/benchmarks/).

## First tasks
- [ ] Baseline `qwen3.5:4b` and `qwen3.5:9b-q4_K_M` tok/s (prompt + gen) and VRAM.
- [ ] Confirm the `/v1` endpoint works for a small script.
