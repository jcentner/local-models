---
title: RTX 5070 Laptop (Blackwell, 8 GB)
tags: [hardware, gpu, blackwell, cuda]
updated: 2026-06-14
status: verified-specs
---

# RTX 5070 Laptop GPU (Blackwell)

The GPU in this machine. Blackwell architecture, **8 GB GDDR7**. The dominant
constraint for local inference here.

## Specs (Laptop / mobile SKU)

| Spec | Value |
|---|---|
| Architecture | Blackwell (GB206), compute capability **sm_120** |
| VRAM | **8 GB** GDDR7 (8151 MiB visible) |
| Memory bus / bandwidth | 128-bit / ~384 GB/s |
| Driver (verified) | 595.97, exposes **CUDA 13.2** runtime in WSL2 |
| Tensor cores | 5th-gen (adds **FP4 / NVFP4** support) |
| TGP | ~50–100 W (laptop, Max-Q) |

Sources: NVIDIA Blackwell whitepaper; [Wikipedia: GeForce RTX 50 series](https://en.wikipedia.org/wiki/GeForce_RTX_50_series).

## The one gotcha that actually bites: CUDA >= 12.8

Blackwell's `sm_120` kernels only exist in recent toolkits and wheels.

- **Ollama**: bundles its own CUDA runtime — just works (verified; models load).
- **From-source builds (llama.cpp, vLLM) and PyTorch wheels**: need **CUDA
  >= 12.8** and matching `cu128`/`cu129`/`cu130` torch wheels. Old prebuilt wheels
  fail with "no kernel image is available for execution on the device".
- This machine has **no CUDA toolkit** installed (`nvcc` absent). To build from
  source: install the CUDA toolkit (>=12.8) via NVIDIA's WSL-Ubuntu repo, or
  build inside an NVIDIA CUDA container.

The 595.97 driver supporting CUDA 13.2 means the driver is never the blocker —
it's about picking toolkit/wheel versions >= 12.8.

## Practical implications

- **FP4/NVFP4** is a genuinely relevant optimization angle here — Blackwell's
  tensor cores accelerate it, and it stretches the 8 GB further. See
  [concepts/quantization.md](../concepts/quantization.md).
- ~384 GB/s bandwidth is the real throughput ceiling for token generation; a
  4-bit ~8B model is decode-bandwidth-bound, not compute-bound.
- 8 GB means KV-cache and context length compete with weights for room; long
  contexts may force smaller quant or partial offload.

## Related
- [hardware/proart-p16.md](proart-p16.md) — the whole machine.
- [stacks/llama-cpp.md](../stacks/llama-cpp.md) — building for this GPU.
