---
title: Ryzen AI 9 HX 370 NPU (XDNA 2)
tags: [hardware, npu, amd, xdna2]
updated: 2026-06-14
status: researched
---

# Ryzen AI 9 HX 370 — NPU (XDNA 2)

The CPU includes an XDNA 2 NPU (~50 TOPS). Tempting for low-power inference, but
for this setup it's an **experiment, not a daily driver** — mainly because of WSL.

## The blockers

1. **WSL2 can't see the NPU.** GPU passthrough to WSL is solid (NVIDIA CUDA on
   WSL), but the AMD Ryzen AI NPU driver stack is **Windows-native** and is not
   exposed to the Linux guest. NPU work would have to run on the **Windows side**,
   outside this Ubuntu environment.
2. **The LLM tooling is Windows-leaning.** AMD's Ryzen AI Software (ONNX Runtime
   + Vitis AI EP, Quark quantizer) and the [Lemonade](../stacks/lemonade.md)
   server's NPU backends (`flm`, `ryzenai-llm` on XDNA2) target Windows for the
   NPU path; Linux support centers on CPU/iGPU.

## What it's actually good at

- Low-power, small-batch inference of **quantized** CNN/transformer models via
  ONNX Runtime — power efficiency, not peak throughput.
- AMD's flow: quantize with **Quark** (INT8 / bf16), deploy through ONNX Runtime
  with the Vitis AI Execution Provider, which partitions work onto the NPU.

Source: [AMD Ryzen AI Software docs](https://ryzenai.docs.amd.com/en/latest/);
[Lemonade](https://github.com/lemonade-sdk/lemonade).

## Recommendation

Park the NPU as a **later, Windows-side track**: install Lemonade or Ryzen AI on
Windows, run a small ONNX LLM on the NPU, and benchmark it against the GPU/CPU
paths here. Document findings as an experiment under `lab/experiments/`. Don't
block the main (GPU-on-WSL) workflow on it.

## Related
- [stacks/lemonade.md](../stacks/lemonade.md) — the most likely NPU on-ramp.
- [hardware/proart-p16.md](proart-p16.md) — the whole machine.
