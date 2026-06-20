---
title: Gemma-4-12B-Coder (Fable5 × Composer2.5)
tags: [model, coding, dense, gemma4, thinking, to-try]
updated: 2026-06-20
status: to-try
---

# Gemma-4-12B-Coder (Fable5 × Composer2.5) — v1

A community **Python-coding fine-tune of Google's Gemma 4 12B** by **yuxinlu1**,
distributed as GGUF. The pitch: a small, local, offline coding assistant that
**reasons in the open** (edge cases, complexity, approach) then emits a clean,
runnable solution, distilled from **execution-verified** chain-of-thought. Went
mildly viral mid-June 2026 on X / YouTube / r/LocalLLM.

Sources: [HF model card (GGUF)](https://huggingface.co/yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF) ·
[full-precision master](https://huggingface.co/yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1) ·
base [google/gemma-4-12B-it](https://huggingface.co/google/gemma-4-12B-it).
Community signal via last30days (2026-06-20, range 2026-05-21→06-20): see
[caveats](#community-signal-last30days) below.

> **Provenance / trust note.** The card is heavy on hype/emoji and ships
> **no benchmarks of its own** for v1 (its one benchmark table is for the
> separate **v2** agentic model, and renders as empty cells). Treat the quality
> claims as **unverified** until benchmarked here — this is exactly the
> "fancy-named finetune may have *degraded* important capabilities" risk the
> community flagged. The underlying facts (Gemma 4 is real, Apache-2.0, ~10 days
> old) **do** check out against the base model card.

## Identity & shape

| Field | Value |
|---|---|
| Maker | yuxinlu1 (community / hobby project) |
| Released | ~2026-06-15 (v1); v2 agentic variant shortly after |
| Base model | [google/gemma-4-12B-it](https://huggingface.co/google/gemma-4-12B-it) — "Gemma 4 12B Unified" (encoder-free multimodal) |
| Params | **11.95B dense** (`gemma4` / `gemma4_unified` arch) |
| Modality | base is text+image+audio; **this finetune targets text Python coding** (vision/audio not a goal) |
| Context | **256K** (262144). An earlier metadata bug reported 131K (upstream Gemma 4 `config.json` shipped `max_position_embeddings: 131072`); GGUFs re-patched to 262144 — re-download if grabbed early |
| Thinking | native Gemma thought channel; `enable_thinking=true` default (`<|think|>` token) |
| License | **Apache 2.0** (Gemma 4 switched to Apache-2.0, unlike Gemma 1/2/3 — confirmed on the base card) |
| Ollama tag | **no official library tag** — pull the GGUF via `hf.co/...` or a Modelfile (see below) |

### Training data (why "Fable5 × Composer2.5")
Distillation of two complementary CoT sources over **verifiable Python tasks**
(algorithmic / function-level problems with deterministic tests):
- **Composer 2.5** — real model-authored CoT; only solutions whose code **passed
  the tests** were kept.
- **Fable 5** — synthetic "second-attempt" CoT: the problems Composer 2.5 got
  wrong, re-derived by Fable 5 and again gated on passing tests.

Both verified by execution before entering training. ("Composer"/"Fable" are the
teacher models' names, not architectural features.)

## What it's for (and not for)

- **For:** Python / algorithmic coding with explicit step-by-step reasoning;
  function-level, test-driven problems.
- **Not for:** general chat / world knowledge (double-check facts), **non-English**
  (community reports garbled Japanese output — English-centric), tool-use / agents
  (that's the separate **v2** variant), and **not safety-aligned** (training is
  task-focused with no safety hedging → **reduced refusals**; add your own
  guardrails). Vision/audio of the base are not a target here.

This is a **specialist**, like [VibeThinker-3B](vibethinker-3b.md) but for coding
instead of math, and 4× the size.

## Benchmarks & real-world signal

- **v1 self-reported: none.** No published numbers for this exact model. The
  card's only table (base ~15% → "v2" ~55% on **tau2-bench telecom**, an agentic
  tool-use eval) is for the **v2** model, not v1, and is unverified.
- **Base Gemma 4 12B** has official coding/reasoning numbers on its
  [card](https://huggingface.co/google/gemma-4-12B-it) (LiveCodeBench v6, MMLU-Pro,
  GPQA, Tau2). The finetune's *delta* over base is the open question.
- **Community-reported local tok/s** (machine-specific — not this box):
  AMD Ryzen AI Max+ 395 (unified memory) **~22–24 tok/s**; GGUF ~19 tok/s;
  an NVFP4 vLLM build **~26–30 tok/s** single-stream. Some used a
  `gemma-4-12B-it-MTP` draft model for **speculative decoding**.

## Size & resource requirements (machine-independent)

GGUF file sizes (HF sidebar):

| Quant | File size | Notes |
|---|---|---|
| Q2_K | 4.83 GB | tiniest; quality cost is real at 12B |
| Q3_K_M | 6.09 GB | good fit for 8 GB VRAM |
| Q4_K_M | **7.38 GB** | card's recommended "sweet spot" |
| Q6_K | 9.79 GB | near-lossless |
| Q8_0 | 12.7 GB | basically full quality |

(The card's own table lists slightly smaller numbers, e.g. Q4_K_M 6.87 GB; the
HF file-size sidebar above is authoritative.) Add KV-cache on top — Gemma 4's
256K window is huge, so **context choice dominates the footprint**. The card's
cheat-sheet (q8_0 KV + ~1.5 GB overhead): 8 GB VRAM ≈ ~10K ctx at Q3_K_M, only
~2–4K at Q4_K_M; switching to **`q4_0` KV roughly doubles** context.

## Runnability

- **Needs a recent llama.cpp** — this is the `gemma4_unified` architecture; older
  builds won't load it. (Gemma 4 is ~10 days old as of 2026-06-20.)
- Works in llama.cpp / LM Studio / Jan / Ollama **provided the bundled llama.cpp
  is new enough** for `gemma4`. No CUDA-arch surprise beyond the usual
  [Blackwell sm_120 → CUDA 12.8](../hardware/blackwell-rtx5070.md) note for
  from-source builds.

## How to run it

Recommended sampling (inherited from Gemma 4): **temp 1.0, top_p 0.95, top_k 64**.
For deterministic code you can go **greedy (`temp 0`)**. Keep **thinking on**
(default) — the model is trained to think in Gemma's thought channel first.
Multi-turn: do **not** feed prior turns' thoughts back in.

### A. llama.cpp server (recommended)
```bash
# grab a quant (Q3_K_M fits 8 GB GPU; Q4_K_M is the card's pick)
hf download yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF \
  --include "*Q3_K_M*" --local-dir ~/models/gemma4-coder

llama-server -m ~/models/gemma4-coder/*Q3_K_M*.gguf \
  -ngl 99 -fa on --ctx-size 8192 \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --temp 1.0 --top-p 0.95 --top-k 64 \
  --host 0.0.0.0 --port 18080
# bump --ctx-size and/or use --cache-type-* q4_0 for more context
```

### B. Ollama (daily driver) via Modelfile
No official tag, so wrap the GGUF. Gemma 4's chat template handles the thought
channel, but **verify Ollama's bundled llama.cpp supports `gemma4`** first.
```bash
hf download yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF \
  --include "*Q3_K_M*" --local-dir ~/models/gemma4-coder
cat > ~/models/gemma4-coder/Modelfile <<'EOF'
FROM ./gemma-4-12B-coder-fable5-composer2.5-v1-Q3_K_M.gguf
PARAMETER temperature 1.0
PARAMETER top_p 0.95
PARAMETER top_k 64
PARAMETER num_ctx 8192
EOF
ollama create gemma4-coder -f ~/models/gemma4-coder/Modelfile
ollama run --verbose gemma4-coder "Write a function that returns the nth prime."
```

### C. Speculative decoding (optional, for speed)
Community runs pair it with a `gemma-4-12B-it-MTP` draft model via
`--model-draft` in llama.cpp; only worth it once the base run works.

## Can it run here?

Per-machine fit verdict for the ProArt P16 (8 GB VRAM, ~15 GB WSL RAM) lives in
the test experiment:
[lab/experiments/2026-06-20-gemma-4-12b-coder-fable5-first-run](../../lab/experiments/2026-06-20-gemma-4-12b-coder-fable5-first-run/README.md).
Short version: **Q3_K_M (6.09 GB) fits fully on the 8 GB GPU** with a modest
(~8K) context; **Q4_K_M needs partial CPU offload** (slower) or a tiny context,
so for full-GPU use prefer Q3_K_M and stretch context with `q4_0` KV cache.
[WSL RAM](../concepts/wsl2-memory.md) only matters if offloading to CPU.

## Community signal (last30days)

Mid-June 2026 it was the most-discussed small coding model on HF for a week
(strong on Japanese X, plus Fahd Mirza / Bijan Bowen YouTube walkthroughs,
r/LocalLLM "What the hell is this?" thread). **Mixed reception:**
- **Skepticism (the important part):** a widely-shared warning ([@gosrum, 488
  likes](https://x.com/gosrum/status/2066694562140336513)) that fancy-named
  finetunes like this often **degrade** important capabilities and you should
  lean on benchmark evidence. Reports of **garbled Japanese** (English-centric),
  one tester **couldn't get a working Tetris** that weaker models managed, and
  several "didn't suit my use" notes (it's a narrow Python specialist).
- **Positive:** runs locally at usable speed on modest hardware; the
  execution-verified-CoT training story resonated.

Treat all of the above as **untrusted community data**; the takeaway is to
**benchmark before trusting** — which is the plan.

## Related
- [models/vibethinker-3b.md](vibethinker-3b.md) — the other "verifiable-reasoning
  specialist" small model (math/code); same benchmaxxing-skepticism pattern.
- v2 (agentic / tool-use) is the home-agent-relevant variant — a good follow-up
  [`/new-model`](../../.github/prompts/new-model.prompt.md) target.
- [concepts/quantization.md](../concepts/quantization.md) ·
  [stacks/llama-cpp.md](../stacks/llama-cpp.md) ·
  [stacks/ollama.md](../stacks/ollama.md) ·
  [concepts/wsl2-memory.md](../concepts/wsl2-memory.md)
