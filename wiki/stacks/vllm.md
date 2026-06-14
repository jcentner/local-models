---
title: vLLM
tags: [stack, serving, throughput]
updated: 2026-06-14
status: stretch-goal
---

# vLLM — high-throughput serving (stretch goal)

Production-grade batched inference with PagedAttention. Powerful, but a stretch
on **8 GB VRAM** — bookmark it for after a hardware upgrade, or for batched
benchmarking experiments.

## Fit on this machine

- **Linux-only** — fine, we're in WSL2 Ubuntu (vLLM even notes WSL works; it caps
  guest RAM at 50% by default, which is our [WSL memory issue](../concepts/wsl2-memory.md)).
- **Blackwell needs CUDA >= 12.8.** vLLM ships wheels built for CUDA 12.8/12.9/13.0;
  install the matching one. Min GPU compute capability 7.5 (sm_120 is fine).
- **VRAM-hungry.** vLLM pre-allocates a large KV-cache pool and is happiest with
  more than 8 GB. Usable for small models (e.g. a 4B AWQ) but you lose the
  throughput edge that justifies it at tiny scale.

## When it pays off

- Serving many concurrent requests / batched eval jobs.
- AWQ / GPTQ / FP8 quantized models with fast kernels.
- After upgrading past ~16 GB VRAM.

## Install sketch (in a venv, not system python)

```bash
python3 -m venv .venv && source .venv/bin/activate
uv pip install vllm --torch-backend=auto    # picks CUDA wheel from driver
vllm serve Qwen/Qwen3-0.6B                   # OpenAI-compatible on :8000
```

Source: [vLLM GPU install docs](https://docs.vllm.ai/en/latest/getting_started/installation/gpu.html).

## Verdict for now

Not the daily driver here. Revisit for (a) a batched-throughput benchmark vs
Ollama/llama.cpp, or (b) post-upgrade. Daily work stays on [Ollama](ollama.md).
