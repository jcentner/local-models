---
mode: agent
description: Research a new aide model (STT / TTS / embedding / reranker-retriever), document it in the wiki, and stage the right external eval. The support-model sibling of /new-model.
---

# /new-aide — research, document, and stage an aide model

The model to investigate is whatever I name after the command (e.g.
`/new-aide LiquidAI/LFM2.5-ColBERT-350M`, `/new-aide whisper-large-v3-turbo`,
`/new-aide nomic-embed-text`, `/new-aide kokoro`). Call it `${input:model}`.

This is the **aide-model** track: the non-generative support models the
[home-automation agent](../../README.md#vision) needs around its chat brain — the
ears (STT), the voice (TTS), the memory (embeddings), and the router (retrieval /
reranking for tool + context selection). Read
[concepts/aide-models.md](../../wiki/concepts/aide-models.md) first — it is the
durable schema (taxonomy, eval contract, page schema) this prompt executes.

Follow the repo schema in [AGENTS.md](../../AGENTS.md) and the **ingest** loop:
research -> write wiki -> update index + log -> stage an eval. Keep me in the loop
before writing if anything is ambiguous.

**Why this is not `/new-model`.** Aide models break every generative-LLM
assumption: no chat template / sampling / thinking mode (an **I/O contract** takes
their place); **mostly not on Ollama** (per-class Python libs / ONNX); footprint
binding constraint is **RTF / encode throughput / index size**, not VRAM-for-KV;
and eval is **objective metrics** (WER, NDCG@k, Recall@k, MOS) via an **external
eval**, not the [`/benchmark`](benchmark.prompt.md) harness. The Copilot-CLI judge
**cannot hear audio**, so TTS naturalness can't be LLM-judged — plan for that.

## 0. Classify

Decide which of the four classes `${input:model}` is — **STT/ASR**, **TTS**,
**embedding** (bi-encoder), or **reranker / late-interaction retriever** — from
its model card. The class drives every checklist below. If it's genuinely
multi-purpose (e.g. a model that both embeds and reranks, like ColBERT), note
both roles. If it's none of the four (e.g. VAD, diarization), flag it and ask
before proceeding.

## 1. Research

Use the **last30days** skill for community signal and **primary sources**
(HF model card, GitHub, paper) for authoritative facts — the exact recipe and
untrusted-content caveat are in [`/new-model` § 1](new-model.prompt.md); reuse it.
Aide models have less hype drama than chat LLMs, so weight primary sources
heavily; last30days is for run reports, quant/ONNX links, and gotchas.

Capture, per [the page schema](../../wiki/concepts/aide-models.md#aide-model-page-schema-what-new-aide-captures):

**Identity & sources** — name, maker, release date, model card / GitHub / paper,
HF repo(s), and **license (read it)** — several aide models use **custom licenses**
(e.g. LFM Open License v1.0), not Apache/MIT; note any usage restriction.

**Class & pipeline slot** — which class; where it sits in the home-agent pipeline.

**I/O contract** (this replaces sampling/chat-template):
- STT: input sample rate, streaming?, channels, languages, output format (text / timestamps).
- TTS: output sample rate, streaming?, voices / cloning, time-to-first-audio.
- Embedding: output **dimension**, **max seq len**, **similarity fn** (cosine/dot), **normalization**, Matryoshka truncation.
- Reranker/late-interaction: query/doc **max length**, **output token dim** (multi-vector), index type (e.g. PLAID), MaxSim vs cross-encoder.

**Architecture & backbone** — params, base model, modality, language coverage.

**Size & footprint per format** (machine-independent) — safetensors / ONNX /
CTranslate2 / GGUF where they exist; and the **binding constraint** for this class
(RTF for audio, encode throughput for embeddings, index/storage size for retrieval).

**Runtime / serving** — exact library + command (faster-whisper, piper/Kokoro,
sentence-transformers, **PyLate + FastPLAID**, etc.); **does Ollama serve it?**
(only some embedding models do); GPU-arch caveats
([Blackwell sm_120 -> CUDA 12.8](../../wiki/hardware/blackwell-rtx5070.md)).

**Benchmarks** — official class-specific metrics with source (WER/CER; NDCG@k /
Recall@k / MRR; round-trip WER / MOS). Flag benchmaxxing / contamination as usual.

## 2. Update the wiki

- Create `wiki/models/<slug>.md`. Frontmatter: `title`, `tags`
  (`aide` + subtype `stt`|`tts`|`embeddings`|`reranker`), `updated` (today),
  `status` (`to-try` until run). Use the
  [aide-model page schema](../../wiki/concepts/aide-models.md#aide-model-page-schema-what-new-aide-captures)
  (sections 1-9), **not** the generative-LLM shape. Keep facts machine-independent;
  cross-link to [concepts/aide-models.md](../../wiki/concepts/aide-models.md),
  relevant [stacks](../../wiki/stacks/), and [hardware](../../wiki/hardware/).
- **Usage / running instructions are required** — exact install + encode/transcribe/
  synthesize/retrieve commands for the real runtime, plus the I/O contract.
- Add a one-line entry under **## Aide models** in
  [wiki/index.md](../../wiki/index.md) (create the subsection under Models if absent).
- Append one line to [wiki/log.md](../../wiki/log.md):
  `## [YYYY-MM-DD] ingest | <model> aide-model page` + a short body.

## 3. Stage the eval (external-first)

Pick the **external eval to wrap** for the class — do **not** hand-roll a harness
up front:
- **STT** -> LibriSpeech / Common Voice / FLEURS + [`jiwer`](https://github.com/jitsi/jiwer) WER (Open ASR Leaderboard methodology).
- **TTS** -> round-trip WER (synthesize -> trusted STT -> WER) over a fixed sentence set; MOS via human / UTMOS / NISQA (no audio judge).
- **Embedding** -> [MTEB](https://github.com/embeddings-benchmark/mteb), or a targeted retrieval subset.
- **Reranker / late interaction** -> BEIR / NanoBEIR; **and** the custom
  **tool-selection Recall@k** (pool of N tools -> is the relevant one in the top-k,
  e.g. 250 -> top-5) — the home-agent-relevant, deterministic test with no
  off-the-shelf equivalent. This is the one case worth hand-rolling a scorer for.

Then, per current machine:
- Read the [hardware](../../wiki/hardware/) page(s) and compute the fit verdict
  against the **runtime** (not `ollama run`): which format/precision fits, expected
  RTF / throughput / index size. Record as a per-machine note, not a core fact.
- Scaffold `lab/experiments/<slug>/README.md` (hypothesis -> method with exact
  commands -> result blank -> learnings blank), recording the class-specific
  fields (metric, dataset, runtime + version, machine).
- Do **not** download weights or run anything unless I confirm.

## 4. Report back

End with: the class + pipeline slot; the verdict (runs on this machine? on which
runtime? which format?); the exact external eval + metric that will decide
fitness; the next command to test it; and open questions worth a follow-up
`/new-aide` or a lint pass.
