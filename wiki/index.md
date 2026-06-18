---
title: Wiki Index
updated: 2026-06-14
---

# Index

The catalog of this wiki. Read this first to find a page, then drill in. Updated
on every ingest. Timeline lives in [log.md](log.md).

## Hardware
- [hardware/proart-p16.md](hardware/proart-p16.md) — this machine (ASUS ProArt P16): verified specs, WSL2 setup, what fits.
- [hardware/blackwell-rtx5070.md](hardware/blackwell-rtx5070.md) — RTX 5070 Laptop (Blackwell, 8 GB): specs + the CUDA 12.8 / sm_120 gotcha.
- [hardware/xdna2-npu.md](hardware/xdna2-npu.md) — Ryzen AI 9 HX 370 NPU (XDNA 2): what it can do and why it's a Windows-side experiment.

## Stacks
- [stacks/ollama.md](stacks/ollama.md) — daily driver. GGUF, OpenAI-compatible API. Already installed.
- [stacks/llama-cpp.md](stacks/llama-cpp.md) — engine-level control, llama-bench, the DiffusionGemma diffusion branch.
- [stacks/vllm.md](stacks/vllm.md) — high-throughput serving; Linux-only; stretch goal on 8 GB.
- [stacks/lemonade.md](stacks/lemonade.md) — AMD's local server; the NPU/iGPU on-ramp.
- [stacks/unsloth.md](stacks/unsloth.md) — fine-tuning + Unsloth Studio; easiest path to DiffusionGemma.

## Models
- [models/diffusiongemma.md](models/diffusiongemma.md) — diffusion/block-AR MoE (26B-A4B); first model to try.
- [models/vibethinker-3b.md](models/vibethinker-3b.md) — WeiboAI 3B dense reasoning specialist (Qwen2.5-based, MIT); frontier-ish math/code scores, runs full-GPU here.

## Benchmarks
- [benchmarks/README.md](benchmarks/README.md) — how the benchmark system works: definitions vs results, the harness, scoring per domain, the four workflow verbs.
- [benchmarks/humaneval-plus.md](benchmarks/humaneval-plus.md) — HumanEval+/MBPP+ coding (wraps evalplus); high contamination risk, pair with LiveCodeBench.
- [benchmarks/example-arithmetic.md](benchmarks/example-arithmetic.md) — tiny authored arithmetic set; format reference + harness smoke test.

## Concepts
- [concepts/llm-wiki-method.md](concepts/llm-wiki-method.md) — the Karpathy LLM-wiki pattern this repo runs on.
- [concepts/quantization.md](concepts/quantization.md) — GGUF K-quants, AWQ/GPTQ, FP8/NVFP4, and the 8 GB VRAM math.
- [concepts/wsl2-memory.md](concepts/wsl2-memory.md) — why WSL only sees ~15 GB and how to fix it.

## Lab (not part of the wiki, but linked for navigation)
- [../lab/journal/](../lab/journal/) — dated narrative entries.
- [../lab/experiments/](../lab/experiments/) — reproducible runs.
- [../lab/benchmarks/](../lab/benchmarks/) — numbers.
