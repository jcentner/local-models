---
title: VibeThinker-3B
tags: [model, reasoning, dense, small, qwen2.5, math, code, tested]
updated: 2026-06-19
status: tried
---

# VibeThinker-3B

A **3B dense reasoning model** from **WeiboAI** (Weibo's AI team), released
**2026-06-16**. Built on **Qwen2.5-(Coder-)3B** and post-trained with the
**Spectrum-to-Signal Principle (SSP)** pipeline (curriculum SFT -> multi-domain
verifiable-reward RL -> offline self-distillation -> Instruct RL). The pitch: a
tiny model that reaches **frontier-level scores on *verifiable* reasoning**
(math, competitive coding, STEM), rivaling models 100-300x larger.

Sources: [GitHub WeiboAI/VibeThinker](https://github.com/WeiboAI/VibeThinker) ·
[HF WeiboAI/VibeThinker-3B](https://huggingface.co/WeiboAI/VibeThinker-3B) ·
[arXiv 2606.16140](https://arxiv.org/abs/2606.16140). Community signal via
last30days (2026-06-18): [r/LocalLLaMA scaling thread](https://www.reddit.com/r/LocalLLaMA/comments/1u7dzdr/scaling_former_vibethinker15b_to_3b_now_it/) (78 cmt),
[Fahd Mirza local test](https://www.youtube.com/watch?v=5zSpzIPmpGs) (5.5K views).

## Identity & shape

| Field | Value |
|---|---|
| Maker | WeiboAI (Weibo) |
| Released | 2026-06-16 (1.5B predecessor: 2025-11) |
| Base model | [Qwen2.5-3B](https://huggingface.co/Qwen/Qwen2.5-3B) / [Qwen2.5-Coder-3B](https://huggingface.co/Qwen/Qwen2.5-Coder-3B) |
| Params | 3B, **dense** (qwen2 arch) |
| Modality | text only; long chain-of-thought reasoning |
| Context | trained on a **64K** long-context window (base Qwen2.5 = 32K native); generates very long traces (their example sets `max_new_tokens` 40960-102400) |
| Native precision | BF16 |
| License | **MIT** (code *and* weights) |
| Ollama tag | **none official** — use a community GGUF + a Modelfile (see below) |

## What it's for (and not for)

- **For:** competition-style **math**, **competitive programming** (LeetCode-style),
  **STEM** reasoning, instruction-following with explicit, checkable constraints.
- **Not for:** broad open-domain knowledge / general chat (the makers say larger
  general models are still better), and explicitly **not** tool-calling, function
  calling, API orchestration, or autonomous coding agents - the model was **not
  trained on agent/tool-use data** (official warning on the HF card).

This is a **specialist**, not a general assistant. Treat it as a math/STEM solver.

## Benchmarks (official, from the technical report)

| Benchmark | VibeThinker-3B | + CLR (test-time scaling) |
|---|---|---|
| AIME 2026 | 94.3 | 97.1 |
| HMMT 2025 | 89.3 | 95.4 |
| IMO-AnswerBench (400 IMO-level) | 76.4 | 80.6 |
| BruMO 2025 | - | 99.2 |
| LiveCodeBench v6 | 80.2 Pass@1 | - |
| LeetCode weekly/biweekly (Apr 25-May 31 2026, unseen) | 96.1% acceptance (123/128) | - |

The makers claim this reaches the *range* of GLM-5 (744B), Kimi K2.5 (~1T),
Gemini 3 Pro, Qwen3.6 Plus, and DeepSeek V3.2 (671B) **on these verifiable
benchmarks** - framed by their "Parametric Compression-Coverage Hypothesis"
(verifiable reasoning is parameter-dense and compressible; world knowledge is not).

**CLR** = Claim-Level Reliability Assessment, a test-time scaling trick that
samples/verifies multiple claims; it costs extra compute per query.

### Community caveats (last30days, last 30 days)
- Heavy **"benchmaxxing" skepticism** on [r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA/comments/1u7dzdr/scaling_former_vibethinker15b_to_3b_now_it/) and
  [r/AIToolsPerformance](https://www.reddit.com/r/AIToolsPerformance/comments/1u7jj64/a_3b_model_scores_943_on_aime26_vibethinker/):
  "too good to be true," questions about whether narrow benchmark scores
  generalize. Verify on your *own* problems, not the headline numbers.
- The 3B is a **scale-up of the earlier 1.5B**; same method, more parameters.

## Size & resource requirements (machine-independent)

3B params, so footprints are small - the binding constraint here is **context/KV
cache and wall-clock time for long reasoning traces**, not weight size.

| Quant | Approx file size | Approx weights in VRAM | Notes |
|---|---|---|---|
| BF16 (original) | ~6 GB | ~6 GB | full precision |
| Q8_0 GGUF | ~3.4 GB | ~3.4 GB | community favorite; safest for a precision-sensitive reasoner |
| Q5_K_M GGUF | ~2.2 GB | ~2.2 GB | |
| Q4_K_M GGUF | ~1.9 GB | ~1.9 GB | smallest sane; watch for reasoning-quality loss |

Add KV-cache on top: a long-CoT model wants a **large context (>=32K)**, and KV
at 32-64K adds roughly 1-3 GB depending on quant. Community GGUFs (33+ on HF,
e.g. [JohnRoger/VibeThinker-3B-Q8_0-GGUF](https://huggingface.co/JohnRoger/VibeThinker-3B-Q8_0-GGUF))
work with [llama.cpp](../stacks/llama-cpp.md), LM Studio, and Jan. See
[concepts/quantization.md](../concepts/quantization.md) for the VRAM math.

## How to run it

> **Critical gotcha:** it's a long-reasoning model. Several testers hit
> **"context limit exceeded"** because LM Studio defaulted to ~4K context. Set a
> **large `num_ctx` / context window (>=32K)** or it will truncate mid-thought.
> Also apply the **correct chat template** so the reasoning block is parsed -
> a community template is posted in the
> [Q8 GGUF discussion](https://huggingface.co/JohnRoger/VibeThinker-3B-Q8_0-GGUF/discussions/1).

Recommended sampling (from the report): **temperature 1.0** (or 0.6),
**top_p 0.95**, **top_k -1**, large max tokens (40960+).

### A. Ollama (daily driver) via community GGUF + Modelfile
No official library tag, so pull a GGUF and wrap it in a Modelfile that sets the
template, params, and a big context:

```bash
# 1. grab a quant (Q8_0 recommended for a reasoning model)
hf download JohnRoger/VibeThinker-3B-Q8_0-GGUF --include "*Q8_0*" \
  --local-dir ~/models/vibethinker-3b

# 2. Modelfile (paste the community chat TEMPLATE block into it)
cat > ~/models/vibethinker-3b/Modelfile <<'EOF'
FROM ./vibethinker-3b-Q8_0.gguf
PARAMETER temperature 1.0
PARAMETER top_p 0.95
PARAMETER top_k 0
PARAMETER num_ctx 32768
# TEMPLATE """..."""   # paste from the HF GGUF discussion so <think> is handled
EOF

# 3. build + run
ollama create vibethinker-3b -f ~/models/vibethinker-3b/Modelfile
ollama run --verbose vibethinker-3b "Prove there are infinitely many primes."
```

(`top_k 0` in Ollama = disabled, the equivalent of `top_k -1` elsewhere.)

### B. llama.cpp server (more control over template + context)
See [stacks/llama-cpp.md](../stacks/llama-cpp.md).

```bash
llama-server -m ~/models/vibethinker-3b/vibethinker-3b-Q8_0.gguf \
  -ngl 99 -c 32768 --temp 1.0 --top-p 0.95 --top-k 0 \
  --chat-template-file vibethinker-template.jinja
```

### C. vLLM / transformers (reference, the makers' path)
The report evaluates with **vLLM==0.10.1** (or SGLang) and `transformers>=4.54.0`,
BF16, temp 1.0 / top_p 0.95 / top_k -1. On 8 GB VRAM BF16 (~6 GB) fits but leaves
little room for KV at long context; prefer a GGUF quant locally. vLLM here is a
stretch given the [8 GB ceiling](../stacks/vllm.md).

## Can it run here?

Yes, comfortably - this is a small model. The per-machine fit verdict for the
ProArt P16 lives in the test experiment:
[lab/experiments/2026-06-18-vibethinker-3b-first-run](../../lab/experiments/2026-06-18-vibethinker-3b-first-run/README.md).
Short version: **Q8_0 fully on the 8 GB GPU with 32K context** should fit with
room to spare; [WSL RAM](../concepts/wsl2-memory.md) is not a constraint at this
size. The thing to watch is generation *time* on long reasoning traces, which is
memory-bandwidth bound.

## Evaluated as a decision-maker / reasoner (2026-06-19)

First real benchmark run on this machine, testing it **outside its specialty** on a
fresh, hand-authored [decision-reasoning](../benchmarks/decision-reasoning.md) set
(6 real operational tradeoff scenarios), judged by **claude-opus-4.8**. Verdict:
**decisive but unreliable - 1/6 above bar, mean ~4.3/10** (`observed_pass@1=0.167`).
Runs at **~71 tok/s** (Q8, full GPU, 32K ctx) and completed its `<think>` reasoning
with a clear `Recommendation:` on every item, so the low scores are genuine
judgment failures, not truncation.

Failure pattern (per the judge): it commits hard to a clean recommendation - its
reasoning-model training showing - but frequently **misreads the scenario or
inverts the crux**: a quantitative miscalculation that argued for the opposite
choice (d1), inventing a nonexistent option (d2), inverting the risk logic (claimed
low oversight *reduces* corner-cutting risk - backwards) (d6), and assuming instead
of proposing the cheap investigation the scenario invited (d5). Its narrow
verifiable-reasoning (math/code) training does **not** transfer to messy practical
judgment, and the hard-commit style makes its misreads more dangerous. This matches
the makers' own warning that it is **not for general use**.

Run + per-item rationales: [lab/experiments/2026-06-19-vibethinker-decision-reasoning](../../lab/experiments/2026-06-19-vibethinker-decision-reasoning/README.md).

## Open questions
- Does it actually deliver on its *home turf*? Benchmark it on competitive coding
  (sandboxed `code_tests` / LiveCodeBench) - the decision-reasoning result only
  tests the out-of-domain boundary.
- Quant sensitivity: does Q4_K_M measurably degrade reasoning vs Q8_0? Good
  [quant-sweep](../concepts/quantization.md) candidate.
- Did any decision failures stem from the "I am ChatGPT" identity confusion in its
  CoT, or purely from reasoning transfer limits?
