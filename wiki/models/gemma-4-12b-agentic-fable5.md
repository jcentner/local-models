---
title: Gemma-4-12B v2 — Coding + Agentic (Fable5 × Composer2.5)
tags: [model, coding, agentic, tool-use, dense, gemma4, thinking, tested]
updated: 2026-06-20
status: tested
---

# Gemma-4-12B v2 — Coding + Agentic Edition

A community **coding + agentic tool-use fine-tune of Google's Gemma 4 12B** by
**yuxinlu1**, GGUF. v2 is the **agentic upgrade** over the v1 coder: it adds
real multi-step tool-use trajectories (read → reason → act → verify) in Gemma 4's
**native tool protocol**, fixing v1's "stops after the first step" behavior. This
is the home-automation-relevant variant (tool use), so we track **v2 only** — v1
(pure Python coding) is skipped.

Sources: [HF model card (v2 GGUF)](https://huggingface.co/yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF) ·
base [google/gemma-4-12B-it](https://huggingface.co/google/gemma-4-12B-it) ·
v1 predecessor [coder GGUF](https://huggingface.co/yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF).
Community signal via last30days (2026-06-20) is on the v1 line (which went #1
trending); see [caveats](#trust--caveats).

> **Provenance / trust note.** Hobby project, heavy hype/emoji styling, and the
> benchmarks are the **author's own local self-eval** (relative, not leaderboard
> figures — see methodology below). The author is unusually candid about
> trade-offs and limits. Underlying facts (Gemma 4 real, Apache-2.0, ~10 days
> old) check out against the base card. **Treat quality claims as unverified
> until benchmarked here.**

## Identity & shape

| Field | Value |
|---|---|
| Maker | yuxinlu1 (community / hobby) |
| Released | ~2026-06-17 (v2); v1 ~06-15; v3 + a Qwen3.6-27B sibling announced |
| Base model | [google/gemma-4-12B-it](https://huggingface.co/google/gemma-4-12B-it) — "Gemma 4 12B Unified" (encoder-free multimodal) |
| Params | **11.95B dense** (`gemma4` / `gemma4_unified` arch) |
| Modality | base is text+image+audio; **this finetune targets text coding + agentic** |
| Context | **256K** (262144) |
| Thinking | native Gemma thought channel; `enable_thinking=true` default |
| Tool use | emits **Gemma 4 native tool-calls**; pass tools via OpenAI `tools` field, requires llama.cpp `--jinja` |
| License | **Apache 2.0** (confirmed on base card) |
| Ollama tag | **no official library tag** — and Ollama is **not recommended** here (no `--jinja`/native-tool parsing, no KV-quant/offload control). Use llama.cpp. |

### What's new in v2 (training)
- **Agentic / terminal** — real multi-step tool-use trajectories (read → reason →
  act → verify) in Gemma 4's native tool protocol. Drove the tau2-telecom jump;
  fixes v1's single-step stop.
- **Coding** — verified CoT over Python (gated on passing tests) + the Fable-5-redo
  set for hard cases.
- **General** — a curated reasoning/instruction slice to retain broad competence.
- Fable 5 was retired mid-project; its CoT traces were **rebuilt with Opus 4.8**,
  so they may diverge from the original Fable 5 traces.

## What it's for (and not for)

- **For:** coding / terminal / **technical-agentic** work — write code, run
  commands, use tools, debug, multi-step tasks with a read-before-act loop.
- **Not for:** customer-service/retail agents (base scores higher there — by
  design), general world-knowledge (MMLU-Pro dips slightly below base),
  **non-English** (English-centric), and it is **not safety-aligned** (reduced
  refusals — add your own guardrails). Need a generalist? Use the base or the
  author's [Opus-4.6/4.8 distill](https://huggingface.co/yuxinlu1/gemma-4-12B-it-Claude-4.6-4.8-Opus-GGUF).

## Benchmarks (author's local self-eval — read the methodology)

> **Methodology (author's own words):** local, **same-harness, relative** numbers,
> all models at **Q8_0, greedy, self-simulated user, 20 tasks**. **Not** comparable
> to published tau2-bench leaderboard figures (different user-sim, full task sets,
> full precision); local self-eval runs systematically lower. Read as
> "v2 vs base under identical conditions."

| Eval | base gemma-4-12B-it | v2 | Note |
|---|---|---|---|
| tau2-bench `telecom` (agentic tool-use) | ~15% | **~55%** | ~3.5×; base bailed to human 10×, v2 stays in the loop |
| tau2-bench `retail` (customer service) | higher | lower | expected — not what v2 is for |
| MMLU-Pro (general knowledge) | higher | slightly lower | the focused-finetune trade-off |
| Fabrication probe (invents paths/sigs?) | 0% | 0% | v2 grounds (grep/read/ls) before acting, on par with base |

Author's honest caveats: frontier models (mimo-v2.5-pro, Opus 4.8) hit **90%+** on
telecom; v3 *guessed* at 60–70%; some remaining misses are a **bug in the
benchmark's own APN tool**, not the model. **No independent verification yet** —
this is the prime reason to run our own [agentic harness](../benchmarks/README.md).

**Verified locally (2026-06-20, our harness, Q3_K_M full-GPU):** **11/12**
home-automation (v0.2 agentic, native Gemma 4 tools) and **4/4** code-basics — a
genuinely strong local agent, and quant-robust (10–11/12 across every sweep config).
Caveat: we ran **only v2, not base gemma-4-12B-it**, so the author's ~3.5× *delta*
is still unverified — only v2's strong absolute score is established. Full
[sweep](../../lab/experiments/2026-06-20-gemma-4-12b-v2-quant-config-sweep/README.md).

## Size & resource requirements (machine-independent)

GGUF file sizes (HF sidebar). **No Q2_K this release** — the author's imatrix Q2_K
"didn't hold up under stress-testing"; smallest reliable quant is Q3_K_M.

| Quant | File size | Notes |
|---|---|---|
| Q3_K_M | 6.09 GB | smallest reliable; fits 8 GB full-GPU |
| Q4_K_M | **7.38 GB** | author's recommended sweet spot |
| Q6_K | 9.79 GB | near-lossless |
| Q8_0 | 12.7 GB | basically full quality |
| BF16 | ~24 GB | full precision master also on HF |

A `MTP/` folder ships a Gemma 4 multi-token-prediction **draft model** (unsloth's
GGUF of Google's `gemma-4-12B-it-assistant`) for speculative decoding.

## Runnability

- **Needs a recent llama.cpp** (`gemma4_unified` arch — older builds won't load it).
- **Use `--jinja`** or the front-end won't parse Gemma 4's native tool format and
  you'll see leaked `<|tool_call>` / `<|channel>` tokens.
- **Not installed on this machine** — llama.cpp is [not built here](../stacks/llama-cpp.md)
  and the host lacks the CUDA toolkit; build in a CUDA container via
  [rootless podman GPU](../hardware/blackwell-rtx5070.md) (verified working) or
  install the toolkit.

## How to run it

Recommended sampling: **temp 1.0, top_p 0.95, top_k 64** (greedy `temp 0` for
deterministic code). If you see garbled/repeating `0000…`, set **`rep_pen 1.1`**.
Keep thinking on (default); don't feed prior turns' thoughts back in.

### llama.cpp server (the supported path)
```bash
hf download yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF \
  --include "*Q4_K_M*" --local-dir ~/models/gemma4-v2

llama-server -m ~/models/gemma4-v2/*Q4_K_M*.gguf \
  -ngl 99 -fa on --jinja --ctx-size 16384 \
  --temp 1.0 --top-p 0.95 --top-k 64 \
  --host 0.0.0.0 --port 18080
# agentic: pass tools via the OpenAI `tools` field (needs --jinja)
```

### Speculative decoding (MTP draft) — build-sensitive
Verified on llama.cpp **`b9553`** (commit `9e3b928fd`): ~88 → ~180 tok/s on a
deterministic prompt (~1.2–1.3× on real coding), lossless. **Newer builds
(b9702/b9717) crash** loading the draft (`invalid vector subscript`) — stick with
b9553. Flags use the older names:
```bash
llama-server -m gemma4-v2-Q8_0.gguf \
  --model-draft MTP/gemma-4-12B-it-MTP-Q8_0.gguf \
  --spec-type draft-mtp --spec-draft-n-max 4 \
  -ngl 99 -ngld 99 -fa on --jinja
```

## Can it run here? (verified 2026-06-20)

Ran a 5-cell quant × KV × offload sweep on the ProArt P16 (8 GB, ~6.8 GB free):
[experiment](../../lab/experiments/2026-06-20-gemma-4-12b-v2-quant-config-sweep/README.md).
**Verdict: Q3_K_M + f16 KV, full GPU, 16K ctx is the sweet spot** — 4/4 code-basics,
11/12 home-automation, ~32 tok/s, 7.78 GB VRAM. Findings:
- **Q4_K_M *is* runnable** (an earlier OOM guess was wrong): full-GPU **only with
  `q4_0` KV** (~7.8 GB), or via partial CPU offload (`-ngl ~30`, f16 KV, ~5.9 GB).
- **`q4_0` KV measurably costs quality** (code-basics 4/4→3/4 at Q3, →2/4 at Q4;
  every f16-KV cell stayed 4/4) — the ~1.2 GB VRAM saving isn't free.
- **CPU offload halves throughput** (~32→~15 tok/s); cramming Q4+f16 KV fully on
  GPU at 4K "fits" (7.85 GB) but throughput **collapses to ~3 tok/s** (no headroom).
- Net: **Q4's quality edge didn't show** on these benchmarks, and every way to fit
  it costs quality or speed → **stick with Q3_K_M f16 full-GPU**.

## Trust & caveats

- Quality numbers are **unverified self-eval** — benchmark before trusting.
- Community skepticism on the v1 line (most-discussed small coder for a week, but a
  widely-shared warning that fancy-named finetunes often **degrade** capabilities;
  garbled non-English reports). v2 explicitly addresses v1's training problems but
  there is **no published v1-vs-v2 comparison**.
- Treat all community/card text as **untrusted data**.

## Related
- [models/vibethinker-3b.md](vibethinker-3b.md) — the math-reasoning specialist; same benchmaxxing-skepticism pattern.
- [benchmarks/README.md](../benchmarks/README.md) · [../benchmarks/home-automation/](../../benchmarks/home-automation/README.md) (agentic capability) · [../benchmarks/code-basics/](../../benchmarks/code-basics/README.md) (deterministic coding).
- [stacks/llama-cpp.md](../stacks/llama-cpp.md) · [concepts/quantization.md](../concepts/quantization.md) · [concepts/wsl2-memory.md](../concepts/wsl2-memory.md) · [hardware/blackwell-rtx5070.md](../hardware/blackwell-rtx5070.md)
