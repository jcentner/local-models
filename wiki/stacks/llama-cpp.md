---
title: llama.cpp
tags: [stack, runner, engine, benchmarks]
updated: 2026-06-20
status: container-verified
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

## Verified here: the CUDA container (rootless Podman) — 2026-06-20

No host CUDA toolkit, so we run the **official prebuilt image** instead of building
(same pattern as the [SGLang container](sglang.md)). One-time GPU/CDI setup is
shared — see **[GPU containers](podman-gpu.md)**. Verified working on this box:

```bash
podman pull ghcr.io/ggml-org/llama.cpp:server-cuda     # CUDA 12.8.1, supports sm_120
# GPU visible via CDI (same flags as SGLang):
podman run --rm --device nvidia.com/gpu=all --security-opt=label=disable \
  ghcr.io/ggml-org/llama.cpp:server-cuda --list-devices
#  -> CUDA0: NVIDIA GeForce RTX 5070 Laptop GPU (8150 MiB, 6999 MiB free)
```

- Image entrypoint **is `llama-server`** (the `:server-*` images); pass server
  flags directly. `:server-cuda13` is the CUDA-13 alternative.
- Build verified: **9737** (`67e9fd3b7`). Recent enough for the `gemma4_unified`
  arch. (The Gemma 4 **MTP draft** for speculative decoding is verified only on
  **b9553**; newer builds were reported to crash on the draft loader — pin separately.)
- **Only ~6999 MiB of 8150 MiB is free** (desktop/WSL overhead) — the real VRAM
  budget is **~6.8 GB**, not 8. Plan quant + KV + `-ngl` against that.
- Serve a GGUF straight from HF with `-hf <user>/<repo>:<QUANT>` (downloads into
  the mounted `~/.cache/huggingface`). Mount it like SGLang:
  `-v ~/.cache/huggingface:/root/.cache/huggingface -p 18080:18080`.
- Key 8 GB knobs: `-ngl` (layers on GPU; lower = CPU offload), `-ctk/-ctv q4_0`
  (shrink KV), `-c` (context), `-fa on`, `-fit off` (disable auto-fit for
  deterministic experiments), `--jinja` (native tool-calls), `--metrics` +
  response `timings` for tok/s. First real use: the
  [gemma-4-12B v2 quant sweep](../../lab/experiments/2026-06-20-gemma-4-12b-v2-quant-config-sweep/README.md).

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
- [x] Decide: install CUDA toolkit in WSL vs use a CUDA container. **→ container**
  (`ghcr.io/ggml-org/llama.cpp:server-cuda`, verified 2026-06-20).
- [x] Run the [gemma-4-12B v2 quant × KV × offload sweep](../../lab/experiments/2026-06-20-gemma-4-12b-v2-quant-config-sweep/README.md) — **done 2026-06-20** (Q3_K_M f16 full-GPU wins; 11/12 home-automation, 4/4 code-basics).
