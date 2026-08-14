---
title: LFM2.5-VL-3B
tags: [model, vision, vlm, multimodal, tool-use, grounding, ocr, on-device, to-try]
updated: 2026-08-13
status: to-try
---

# LFM2.5-VL-3B

Liquid AI's **on-device vision-language model** (released **2026-08-12**) — the
**first vision model in this wiki**. 3.1B total: a **SigLIP2 NaFlex 400M**
vision encoder on the [LFM2.5-2.6B](lfm2.5-2.6b.md) language backbone. Built
for exactly the edge-VLM jobs a home agent grows into: **reads screens**
(mobile/web/desktop), **grounds objects to coordinates**, parses documents and
charts (OCR + layout), handles multi-image input, and **calls tools from text
or image input**. Unlike its text sibling it is **non-thinking** — answers
directly, tuned for single-turn, high-throughput, low-latency use.

Sources: [HF model card](https://huggingface.co/LiquidAI/LFM2.5-VL-3B) ·
[GGUF](https://huggingface.co/LiquidAI/LFM2.5-VL-3B-GGUF) ·
[Liquid blog](https://www.liquid.ai/blog/lfm2-5-vl-3b) ·
[HF release blog](https://huggingface.co/blog/LiquidAI/lfm2-5-vl-3b) ·
coverage: [MarkTechPost](https://www.marktechpost.com/2026/08/13/liquid-ai-lfm2-5-vl-3b-on-device-vision-language-model/) ·
[GIGAZINE](https://gigazine.net/gsc_news/en/20260813-lfm2-5-vl-3b).
Researched 2026-08-13 (release day + 1) via web + primary sources; community
signal is necessarily thin this fresh — re-scan in a few weeks.

## Identity & shape

| Field | Value |
|---|---|
| Maker | Liquid AI |
| Released | 2026-08-12 |
| Params | **3.1B** = 2.6B language backbone ([LFM2.5-2.6B](lfm2.5-2.6b.md)) + 400M SigLIP2 NaFlex shape-optimized encoder + projector |
| Pre-training | ~34T tokens, **4× more vision data** than LFM2-VL; vocab 128,000 |
| Context | **32,768** — note: much shorter than the text sibling's 128K |
| Image handling | native resolution; large images → non-overlapping **512×512 patches + whole-image thumbnail** (NaFlex variable resolution) |
| Thinking | **none** — answers directly by design |
| Tool use | same Pythonic `<|tool_call_start|>`/`<|tool_call_end|>` protocol as the backbone; **works from image input too** |
| Languages | 16 (same list as the backbone) |
| License | **LFM Open License v1.0** (see the [ColBERT page's license read](lfm2.5-colbert-350m.md#1-identity--license)) |
| Recommended sampling | **temp 0.2, top_k 50, repetition_penalty 1.0**; image preprocessing per `processor_config.json` |
| Chat template | ChatML-like; `apply_chat_template()` auto-inserts `<image>` tags — don't add them manually |

## What it's for (and not for)

- **For (vendor):** single-turn, high-throughput, low-latency vision — near-realtime
  object detection, batch OCR of scanned documents (with layout), on-device
  translation, screen/UI understanding, image-triggered tool calls.
- **Not for (vendor, explicit):** long-context, **reasoning-intensive** visual
  tasks (visual web design, technical blueprint Q&A). It answers directly
  instead of reasoning.
- **Experimental:** the layout-annotation output format "may change, may be
  unreliable, may not be trivial to parse".

## Benchmarks (official, Liquid blog)

Avg **69.4 across 28 vision benchmarks** — matches InternVL-3.5-4B, 0.7 behind
Qwen3.5-4B (both 4.7B, ~1.5× its size). Selected rows:

| Benchmark | LFM2.5-VL-3B | LFM2-VL-3B (prior) | Gemma4-E2B | Gemma4-E4B | InternVL-3.5-2B | Qwen3.5-2B |
|---|---|---|---|---|---|---|
| ScreenSpot-v2 (UI grounding) | **80.7** | — | 31.1 | 50.9 | — | 66.5 |
| RefCOCO (object grounding) | **87.9** | 57.1 | 67.3 | 72.1 | — | 78.5 |
| BLINK (multi-image) | **61.5** | 50.2 | 51.8 | 56.4 | — | 59.3 |
| MuirBench (multi-image) | **58.3** | 34.9 | 40.7 | 48.9 | — | 49.0 |
| ToolSandbox (tool use) | 59.5 | 26.4 | 56.5 | **61.6** | — | 47.7 |
| MME | 73.1 | 73.0 | 54.9 | 68.1 | 73.3 | **76.4** |
| MMStar | 63.3 | 57.7 | 57.9 | 61.9 | 57.5 | **67.9** |
| MathVista | 68.5 | 68.5 | 62.1 | 52.9 | 56.6 | **68.8** |
| ChartQA | 81.3 | 80.4 | 43.5 | 41.9 | **81.8** | 78.3 |
| OCRBenchv2 | 47.5 | 43.9 | 44.7 | **48.7** | 45.5 | 48.0 |

The step-change vs its predecessor is **grounding and screens** (RefCOCO +30,
ScreenSpot new, ToolSandbox +33) — the agentic-vision axes, not generic VQA.
Vendor numbers, unverified here.

**Speed/footprint (vendor):** ~3.3 GB memory; 228 tok/s M5 Max, 116 tok/s
Ryzen AI Max+ 395, 20 tok/s Galaxy S26 Ultra; H100 ~11K tok/s, TTFT ~34 ms on
a 5-frame clip.

## Size & resource requirements (machine-independent)

GGUF quants mirror the 2.6B backbone (the vision encoder ships as a separate
**mmproj** file the fetch didn't size — assume ~0.8 GB f16 for 400M, verify at
download): Q4_K_M 1.67 GB · Q8_0 2.87 GB · F16 5.4 GB (+ mmproj). Also ONNX and
MLX-8bit exports.

## Runnability

- **Runtimes:** transformers ≥ 5.0 (`AutoModelForImageTextToText`), vLLM,
  SGLang, **llama.cpp multimodal** (`llama-mtmd-cli` / `llama-server` with the
  mmproj; interactive `/image <path>` then ask), MLX via `mlx-vlm`, ONNX.
- **Ollama:** no official tag observed at release; Ollama's multimodal support
  for the `lfm2-vl` arch is **unverified** — treat llama.cpp (container) as the
  default serving path.
- **Harness gap:** our benchmark harness is **text-only** — no image field in
  `bench.json`, no image plumbing in the clients. Vision eval is penciled as a
  future track (see [backlog](../backlog.md)); until then, evaluation is manual
  smoke tests.

## Why it matters for the north star

This is the **eyes** slot of the local-agent suite, and it arrives with a
concrete, already-built use-case: **HomeView's vision pipeline**
(photo → `propose_assets` fixture proposals, production on talos) is exactly
"image in, constrained tool call out" — and homeview's backlog explicitly waits
on a *local* vision provider behind its `VisionProvider` interface, with its
existing eval (18 ground-truth house photos, regex-scored required/optional
fixtures, ~$3 to run against 8 API models) doubling as the API-vs-local
benchmark. Wrapping that eval is the natural first vision benchmark here —
authored ground truth exists, scoring is deterministic, and the comparison set
(Claude/OpenAI production numbers) is already measured. Screen-understanding
(ScreenSpot 80.7) also opens the UI-automation door later. The 32K context and
no-reasoning design fit the single-shot proposal shape well; the open question
is whether 3B-class OCR/grounding clears HomeView's quality bar (the hard item:
a radon pipe identifiable only by a handwritten label — read by Claude models,
missed by all OpenAI configs).

## Can it run here?

Yes — ~3.3 GB fits any 8 GB host full-GPU. Needs a llama.cpp build with
multimodal (mtmd) support in the [CUDA container](../stacks/llama-cpp.md), or a
transformers venv. Smoke-test experiment:
[lab/experiments/2026-08-13-lfm2.5-vl-3b-first-look](../../lab/experiments/2026-08-13-lfm2.5-vl-3b-first-look/README.md).

## Related

- [models/lfm2.5-2.6b.md](lfm2.5-2.6b.md) — the text backbone (thinking, 128K ctx — both dropped here).
- [models/lfm2.5-colbert-350m.md](lfm2.5-colbert-350m.md) — same family, router aide.
- [concepts/aide-models.md](../concepts/aide-models.md) — where non-generative eyes/ears live; this model is generative, so it sits in the main model track.
