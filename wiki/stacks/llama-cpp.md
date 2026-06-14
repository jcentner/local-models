---
title: llama.cpp
tags: [stack, runner, engine, benchmarks]
updated: 2026-06-14
status: not-installed
---

# llama.cpp — engine-level control

The engine under Ollama, used directly when you want cutting-edge models/quants,
fine-grained flags, the `llama-bench` tool, or special branches (like the
[DiffusionGemma](../models/diffusiongemma.md) diffusion sampler).

## Building for this GPU (Blackwell)

Requires the **CUDA toolkit >= 12.8** (sm_120). This machine has **no toolkit**
(`nvcc` absent), so either install it (NVIDIA WSL-Ubuntu repo) or build in an
NVIDIA CUDA container. See [the Blackwell gotcha](../hardware/blackwell-rtx5070.md).

```bash
git clone https://github.com/ggml-org/llama.cpp && cd llama.cpp
cmake -B build -DGGML_CUDA=ON          # -DGGML_CUDA=OFF for CPU-only
cmake --build build -j --config Release
```

## Why use it directly

- **`llama-bench`** — the standard local throughput benchmark (prompt vs gen
  tok/s across quants / offload settings). Primary tool for
  [../../lab/benchmarks/](../../lab/benchmarks/).
- Per-run flags: `-ngl` (GPU layers to offload), `-c` (context), KV-cache type,
  flash-attention, etc. — exactly the knobs for 8 GB tuning.
- Access to brand-new models/quants and PR branches before Ollama packages them.

## DiffusionGemma branch

DiffusionGemma needs a diffusion runtime via a specific PR branch that builds
`llama-diffusion-cli` (with a live `--diffusion-visual` denoising view). Details
and exact commands: [models/diffusiongemma.md](../models/diffusiongemma.md).

## Relationship to Ollama

Ollama wraps llama.cpp. Use Ollama for convenience; drop to llama.cpp when you
need control, benchmarking, or unreleased features.

## First tasks
- [ ] Decide: install CUDA toolkit in WSL vs use a CUDA container.
- [ ] Build with CUDA, run `llama-bench` on a GGUF already pulled by Ollama.
