---
title: Lemonade (AMD local server)
tags: [stack, amd, npu, server]
updated: 2026-06-14
status: researched
---

# Lemonade — AMD's local AI server (NPU on-ramp)

An Apache-2.0 local server by AMD that exposes OpenAI / Anthropic / Ollama-
compatible APIs and can route to CPU, GPU, **and the XDNA2 NPU**. The most likely
path to actually using this machine's [NPU](../hardware/xdna2-npu.md).

## Why it's interesting here

- One server, multiple backends: `llamacpp` (Vulkan/ROCm/CUDA/CPU), ONNX-GenAI,
  and NPU backends (`flm`, `ryzenai-llm`) for XDNA2.
- Drop-in OpenAI-compatible endpoint (`:13305/api/v1`), works with many apps.
- Built on llama.cpp + OnnxRuntime-GenAI + whisper.cpp + stable-diffusion.cpp.

## The catch: NPU path is Windows-leaning

The XDNA2 NPU backends target **Windows** (and WSL2 can't see the NPU anyway —
see [xdna2-npu.md](../hardware/xdna2-npu.md)). On Linux/WSL, Lemonade is mostly a
CPU/GPU server, which [Ollama](ollama.md) already covers for us.

## How I'd use it

As a **Windows-side experiment**, not part of the WSL daily flow:

1. Install Lemonade Server on Windows.
2. `lemonade run Gemma-4-E2B-it-GGUF` (or pull an NPU/ONNX model).
3. Benchmark the NPU path vs this machine's GPU/CPU paths; write it up under
   `lab/experiments/`.

```bash
lemonade backends      # what this PC actually supports
lemonade list          # available models
lemonade run <model>   # chat
```

Source: [github.com/lemonade-sdk/lemonade](https://github.com/lemonade-sdk/lemonade).

## Verdict

Bookmark for the NPU experiment. For everyday Linux/WSL inference, Ollama wins.
