---
title: Wiki Index
updated: 2026-06-20
---

# Index

The catalog of this wiki. Read this first to find a page, then drill in. Updated
on every ingest. Timeline lives in [log.md](log.md). **Forward queue / "what's
next" lives in [backlog.md](backlog.md).** North-star
[vision](../README.md#vision): evaluate models (local **and** API) toward a
local-agent **suite** (home automation, email triage, a website/product support bot).

## Hardware
- [hardware/proart-p16.md](hardware/proart-p16.md) — this machine (ASUS ProArt P16): verified specs, WSL2 setup, what fits.
- [hardware/blackwell-rtx5070.md](hardware/blackwell-rtx5070.md) — RTX 5070 Laptop (Blackwell, 8 GB): specs + the CUDA 12.8 / sm_120 gotcha.
- [hardware/xdna2-npu.md](hardware/xdna2-npu.md) — Ryzen AI 9 HX 370 NPU (XDNA 2): what it can do and why it's a Windows-side experiment.

## Stacks
- [stacks/podman-gpu.md](stacks/podman-gpu.md) — **shared foundation**: run GPU LLM servers (SGLang, llama.cpp) as official CUDA images under rootless Podman + NVIDIA CDI; no host toolkit. The page to reproduce the setup on a new box.
- [stacks/ollama.md](stacks/ollama.md) — daily driver. GGUF, OpenAI-compatible API. Already installed.
- [stacks/llama-cpp.md](stacks/llama-cpp.md) — engine-level control, llama-bench, the DiffusionGemma diffusion branch.
- [stacks/vllm.md](stacks/vllm.md) — high-throughput serving; Linux-only; stretch goal on 8 GB.
- [stacks/sglang.md](stacks/sglang.md) — second runner for **thinking/tool models**: `enable_thinking` + reasoning/tool parsers (incl. `minicpm5`) Ollama lacks; OpenAI-compatible, reached via the harness `--provider openai-compatible`.
- [stacks/lemonade.md](stacks/lemonade.md) — AMD's local server; the NPU/iGPU on-ramp.
- [stacks/unsloth.md](stacks/unsloth.md) — fine-tuning + Unsloth Studio; easiest path to DiffusionGemma.

## Models
- [models/diffusiongemma.md](models/diffusiongemma.md) — diffusion/block-AR MoE (26B-A4B); first model to try.
- [models/vibethinker-3b.md](models/vibethinker-3b.md) — WeiboAI 3B dense reasoning specialist (Qwen2.5-based, MIT); frontier-ish math/code scores, runs full-GPU here.
- [models/minicpm5-1b.md](models/minicpm5-1b.md) — OpenBMB 1B dense on-device model (Llama-arch, Apache-2.0); via SGLang: weak abstract reasoner (decision-reasoning 0/6) but a decent home-automation **tool-executor** (7/12) — a home-agent executor, not the deliberation brain.
- [models/gemma-4-12b-agentic-fable5.md](models/gemma-4-12b-agentic-fable5.md) — yuxinlu1 community **coding + agentic** finetune of Gemma 4 12B v2 (dense, `gemma4_unified`, Apache-2.0, 256K ctx, native tool-use + thinking); **local-verified strongest local agent: HA v0.4 obs@3 0.947 / pass^3 0.632, ET v0.3 1.000 / 0.667, 4/4 code-basics (Q3_K_M)**; needs llama.cpp `--jinja`; runs full-GPU on 8 GB.

### Aide models (STT / TTS / embeddings / retrieval)
The non-generative support models for the home agent — see [concepts/aide-models.md](concepts/aide-models.md) for the track; ingest with [`/new-aide`](../.github/prompts/new-aide.prompt.md).
- [models/lfm2.5-colbert-350m.md](models/lfm2.5-colbert-350m.md) — Liquid AI 353M **late-interaction retriever** (ColBERT/MaxSim, 11 languages, LFM Open License); the **router** aide for tool selection (N tools → top-k) + RAG reranking. PyLate or GGUF/llama.cpp, not Ollama.

## Benchmarks
- [benchmarks/README.md](benchmarks/README.md) — how the benchmark system works: definitions vs results, local/API providers + cost, scoring per domain, external-first strategy, the four workflow verbs.
- [benchmarks/bfcl.md](benchmarks/bfcl.md) — Berkeley Function-Calling Leaderboard (tool-use; wraps bfcl-eval); **reference only** (registered-models-only, lags new models). Agentic eval lives in a model-agnostic custom scorer instead.
- [benchmarks/humaneval-plus.md](benchmarks/humaneval-plus.md) — HumanEval+/MBPP+ coding (wraps evalplus); high contamination risk, pair with LiveCodeBench.
- [benchmarks/decision-reasoning.md](benchmarks/decision-reasoning.md) — authored decision-making/reasoning scenarios (**v0.2, 21 items** across 7 categories × 3 difficulty tiers + traps), opus-4.8-judged; v0.1 6-item runs: VibeThinker 1/6, MiniCPM5-1B 0/6 (re-run on v0.2 for `pass^k`).
- [../benchmarks/code-basics/](../benchmarks/code-basics/README.md) — authored coding smoke test (`code_tests`, Podman sandbox); qwen3.5:4b 3/4.
- [benchmarks/email-triage.md](benchmarks/email-triage.md) — authored **agentic** support set (**v0.3, 12 scenarios**: answer-from-KB vs ask vs escalate, ambiguity→ask, prompt-injection, judged fabrication; `support` toolset); model-agnostic rollout + Copilot user-sim. v0.3 `--k 3` baselines: gemma 1.000/0.667, qwen3.5:4b 0.917/0.833, MiniCPM5 0.833/0.333.
- [benchmarks/home-automation.md](benchmarks/home-automation.md) — authored **agentic** lighthouse set (**v0.4, 19 scenarios**): smart-home act/confirm/refuse with device-aware `ask.device` confirm, a dependency precondition, negation/conditional, injection-via-status, **grounding** (`h5`: decline a nonexistent device), a **compound double-confirm** (`h19`), and judged refuse/confirm/grounding over a device world (`home_automation` toolset). v0.4 `--k 3` baselines: gemma 0.947/0.632, qwen3.5:4b 0.789/0.684, MiniCPM5 0.632/0.210 (v0.3 `h5` numbers superseded).

## Concepts
- [concepts/llm-wiki-method.md](concepts/llm-wiki-method.md) — the Karpathy LLM-wiki pattern this repo runs on.
- [concepts/quantization.md](concepts/quantization.md) — GGUF K-quants, AWQ/GPTQ, FP8/NVFP4, and the 8 GB VRAM math.
- [concepts/wsl2-memory.md](concepts/wsl2-memory.md) — why WSL only sees ~15 GB and how to fix it.
- [concepts/aide-models.md](concepts/aide-models.md) — the aide-model track: STT/TTS/embeddings/retrieval, their eval contract (WER/NDCG@k/Recall@k/MOS, external-first), and why they need a separate `/new-aide` flow.
- [concepts/eval-reliability.md](concepts/eval-reliability.md) — multi-pass eval methodology: `observed_pass@k` (best-of-k ceiling) vs `pass^k` (all-k reliability), flaky items, SEM/error bars; why k=3 + recommended-temp is the honest default.

## Lab (not part of the wiki, but linked for navigation)
- [../lab/journal/](../lab/journal/) — dated narrative entries.
- [../lab/experiments/](../lab/experiments/) — reproducible runs.
- [../lab/benchmarks/](../lab/benchmarks/) — numbers.

## Tools
- [../tools/run-viewer/](../tools/run-viewer/README.md) — local read-only web app to browse benchmark **run content** (`results.csv` index + lazy-loaded `runs/*.jsonl`) with schema-adaptive cards for `code_tests`/`llm_judge`/`agentic`, plus a read-only `wiki/` markdown tab. Stdlib Python server + Preact (no build); Vercel/Geist aesthetic ([DESIGN.md](../tools/run-viewer/DESIGN.md)). Run: `python3 tools/run-viewer/server.py`.
