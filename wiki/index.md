---
title: Wiki Index
updated: 2026-06-19
---

# Index

The catalog of this wiki. Read this first to find a page, then drill in. Updated
on every ingest. Timeline lives in [log.md](log.md). North-star
[vision](../README.md#vision): evaluate models (local **and** API) toward a
local-agent home-automation system.

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
- [models/minicpm5-1b.md](models/minicpm5-1b.md) — OpenBMB 1B dense on-device model (Llama-arch, Apache-2.0); hybrid reasoning + tool-use tilt, runs trivially here; home-agent brain candidate.

## Benchmarks
- [benchmarks/README.md](benchmarks/README.md) — how the benchmark system works: definitions vs results, local/API providers + cost, scoring per domain, external-first strategy, the four workflow verbs.
- [benchmarks/bfcl.md](benchmarks/bfcl.md) — Berkeley Function-Calling Leaderboard (tool-use; wraps bfcl-eval); **reference only** (registered-models-only, lags new models). Agentic eval lives in a model-agnostic custom scorer instead.
- [benchmarks/humaneval-plus.md](benchmarks/humaneval-plus.md) — HumanEval+/MBPP+ coding (wraps evalplus); high contamination risk, pair with LiveCodeBench.
- [benchmarks/decision-reasoning.md](benchmarks/decision-reasoning.md) — authored decision-making/reasoning scenarios, opus-4.8-judged; runs: VibeThinker 1/6, MiniCPM5-1B 0/6 (confounded by uncontrollable Ollama `<think>`).
- [../benchmarks/code-basics/](../benchmarks/code-basics/README.md) — authored coding smoke test (`code_tests`, Podman sandbox); qwen3.5:4b 3/4.
- [../benchmarks/email-triage/](../benchmarks/email-triage/README.md) — authored **agentic** tool-use set (answer-from-KB vs escalate; `support` toolset); model-agnostic `agentic` rollout + Copilot user-sim; the flexible alternative to BFCL.
- [../benchmarks/home-automation/](../benchmarks/home-automation/README.md) — authored **agentic** lighthouse set: smart-home act/confirm/refuse over a device world (`home_automation` toolset); deterministic device-state + confirm-before-sensitive scoring.

## Concepts
- [concepts/llm-wiki-method.md](concepts/llm-wiki-method.md) — the Karpathy LLM-wiki pattern this repo runs on.
- [concepts/quantization.md](concepts/quantization.md) — GGUF K-quants, AWQ/GPTQ, FP8/NVFP4, and the 8 GB VRAM math.
- [concepts/wsl2-memory.md](concepts/wsl2-memory.md) — why WSL only sees ~15 GB and how to fix it.

## Lab (not part of the wiki, but linked for navigation)
- [../lab/journal/](../lab/journal/) — dated narrative entries.
- [../lab/experiments/](../lab/experiments/) — reproducible runs.
- [../lab/benchmarks/](../lab/benchmarks/) — numbers.
