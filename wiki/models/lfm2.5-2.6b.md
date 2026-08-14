---
title: LFM2.5-2.6B
tags: [model, agentic, tool-use, thinking, hybrid-conv-attention, on-device, to-try]
updated: 2026-08-13
status: to-try
---

# LFM2.5-2.6B

Liquid AI's **on-device agentic flagship** (released **2026-08-04**) — the
generative sibling of the [LFM2.5-ColBERT-350M](lfm2.5-colbert-350m.md) router
aide already in the wiki. A 2.69B dense conv/attention hybrid, **128K context**,
**always-thinking** reasoning model with **tool calling as a first-class training
target**: post-training included agentic RL (GRPO) run *inside real agent
harnesses* (Hermes Agent, OpenClaw) against their actual tools and system
prompts. Liquid's pitch is precisely this repo's north star: high-volume agentic
workloads on edge devices — free inference, low latency, real privacy.

Sources: [HF model card](https://huggingface.co/LiquidAI/LFM2.5-2.6B) ·
[GGUF](https://huggingface.co/LiquidAI/LFM2.5-2.6B-GGUF) ·
[Liquid blog](https://www.liquid.ai/blog/lfm2-5-2-6b) ·
[LFM2 Technical Report arXiv 2511.23404](https://arxiv.org/abs/2511.23404) ·
base [LFM2.5-2.6B-Base](https://huggingface.co/LiquidAI/LFM2.5-2.6B-Base) ·
coverage: [VentureBeat](https://venturebeat.com/technology/no-cloud-no-gpus-no-problem-liquid-ais-new-model-lfm2-5-2-6b-brings-powerful-ai-agents-to-devices-as-small-as-a-raspberry-pi) ·
[MarkTechPost](https://www.marktechpost.com/2026/08/06/liquid-ai-lfm2-5-2-6b-on-device-agentic-model/).
Researched 2026-08-13 via web search + primary sources (last30days engine was
not yet set up on torrent — a community-signal pass can be re-run once it is).

## Identity & shape

| Field | Value |
|---|---|
| Maker | Liquid AI |
| Released | 2026-08-04 |
| Params | **2.69B dense** — hybrid: 30 layers = 22 double-gated short-conv + 8 GQA attention |
| Pre-training | ~34T tokens; vocab **128,000** (extended tokenizer) |
| Context | **131,072** (128K) |
| Thinking | **always-on** — a "pure reasoning model"; the chat template opens every assistant turn with `<think>` (see caveats) |
| Tool use | **Pythonic calls** between `<|tool_call_start|>`/`<|tool_call_end|>` special tokens; JSON format on request |
| Languages | 16 (EN, AR, ZH, FR, DE, IT, JA, KO, PT, ES, VI, TH, ID, HI, RU, PL) |
| License | **LFM Open License v1.0** — Apache-2.0 + the <$10M-revenue commercial clause; irrelevant for this project (see the [ColBERT page's license read](lfm2.5-colbert-350m.md#1-identity--license)) |
| Chat template | ChatML-like (`<|im_start|>`/`<|im_end|>`) |
| Recommended sampling | **temp 0.1, top_k 50, repetition_penalty 1.1** (vendor) |

## What it's for (and not for)

- **For (vendor):** agentic workloads, tool use, data extraction, RAG,
  long-context workflows — the home-agent-brain lane exactly.
- **Not for (vendor, explicit):** **agentic coding** and **knowledge-heavy**
  tasks — larger models keep the edge there.

## Benchmarks (official, Liquid blog)

Comparison set is all *larger* models: Gemma-4-E2B (5.1B), Gemma-4-E4B (8B),
Qwen3.5-4B (4.7B), Qwen3.5-9B (9.7B).

| Benchmark | LFM2.5-2.6B | Gemma-4-E2B | Gemma-4-E4B | Qwen3.5-4B | Qwen3.5-9B |
|---|---|---|---|---|---|
| IFBench | **59.17** | 34.08 | 39.24 | 48.40 | 56.47 |
| Multi-IF | **80.07** | 69.44 | 77.35 | 55.67 | 62.55 |
| IFStruct | **85.49** | 64.85 | 76.65 | 36.25 | 78.50 |
| ToolSandbox | **77.83** | 52.40 | 65.00 | 75.55 | 76.44 |
| BFCLv4 | 56.88 | 36.98 | 46.39 | 50.56 | **60.13** |
| τ³-Bench Banking | **5.67** | 3.35 | 4.12 | 5.45 | 5.15 |
| BrowseComp+ (OpenClaw) | 26.89 | 8.31 | 15.90 | 24.46 | **27.23** |
| AIME25 | 51.87 | 26.33 | 34.27 | 49.33 | **56.07** |
| LiveCodeBenchv6 | 59.41 | 54.92 | 63.77 | 60.85 | **69.86** |
| AA-Omniscience-Public | **-29.50** | -74.47 | -49.03 | -54.30 | -50.43 |
| Claw-Eval (EN) | 62.85 | 53.14 | 58.02 | 62.28 | **66.53** |
| PinchBench | 68.22 | 44.24 | 55.09 | 71.26 | **71.45** |

Headline: **leads every instruction-following benchmark and nearly every
tool-use benchmark** at 2.6B, beating the 9.7B Qwen3.5 on ToolSandbox — while
trailing on coding/math/knowledge, matching the vendor's own not-for list.
Vendor numbers, unverified here; our harness is the check that matters
(instruction-following + tool-use is what [home-automation](../benchmarks/home-automation.md)
and [email-triage](../benchmarks/email-triage.md) actually measure).

**Speed/footprint (vendor):** 220 tok/s on M5 Max CPU, 113 tok/s Ryzen AI
Max+ 395, ~30 tok/s phone-class, **< 2.5 GB memory**; ~15K tok/s on one H100.

## Size & resource requirements (machine-independent)

Official GGUF ([LFM2.5-2.6B-GGUF](https://huggingface.co/LiquidAI/LFM2.5-2.6B-GGUF)):

| Quant | File size |
|---|---|
| Q4_0 | 1.59 GB |
| Q4_K_M | 1.67 GB |
| Q5_K_M | 1.94 GB |
| Q6_K | 2.22 GB |
| Q8_0 | 2.87 GB |
| BF16/F16 | 5.4 GB |

Any 8 GB GPU runs **Q8_0 full-GPU with room for large context**; the KV/context
math is the binding factor only at extreme context (see
[quantization](../concepts/quantization.md)). Also ONNX + MLX exports.

## Runnability

- **Runtimes (official):** transformers ≥ 5.0, vLLM, SGLang, llama.cpp
  (official GGUF), LM Studio, MLX, ONNX. The `lfm2` architecture has been in
  llama.cpp/Ollama since LFM2 (2025) — stock support, no branch needed.
- **Ollama:** `ollama run hf.co/LiquidAI/LFM2.5-2.6B-GGUF:Q4_K_M` (card-official).
  **Template-fidelity caveat (the MiniCPM5 lesson):** a bare `hf.co/` pull does
  not evaluate the GGUF's Jinja template — verify the served template opens
  `<think>` and maps the Pythonic tool-call tokens before trusting any agentic
  run. An official `lfm2.5-thinking` library entry exists for the 1.2B sibling;
  check whether a first-party 2.6B tag lands.
- **Controlled path:** llama.cpp `--jinja` in the [CUDA container](../stacks/llama-cpp.md)
  or [SGLang](../stacks/sglang.md) — same serving-aware-per-model routing as
  MiniCPM5/gemma.

## Harness caveats (read before benchmarking)

1. **Thinking cannot be disabled.** The template always opens `<think>`; there
   is no `/no_think` and an open Ollama issue
   ([#14622](https://github.com/ollama/ollama/issues/14622), on the 1.2B-Thinking
   sibling) confirms no suppression path. For the harness: run `--think` /
   record `think=on` semantics via `default`; `--no-think` will be a no-op or
   break the template — **don't** repeat the qwen brevity-nudge detour
   ([dead end, 2026-06-22](../log.md)). CoT cost on agentic episodes is the open
   risk; unlike MiniCPM5 the model was *trained* to act after thinking, so the
   `_no_tool` narrate-instead-of-act flail is not expected — verify.
2. **Tool-call protocol is Pythonic-between-special-tokens**, not OpenAI JSON.
   Whether llama.cpp/Ollama/SGLang parse it into native `tool_calls` is
   **unverified** — probe one episode first; if the server returns raw text, the
   harness needs a Pythonic sibling of `parse_xml_tool_calls()` (the MiniCPM5
   XML-fallback pattern).
3. **Very low recommended temp (0.1).** Our reliability runs use
   vendor-recommended sampling, so `pass^k` flakiness should be structurally
   lower than qwen's t=1.0 — annotate comparisons accordingly.

## Why it matters for the north star

The most direct **home-agent brain candidate** since qwen3.5:4b: tool-use-first
training (including inside **Hermes Agent** — the same runtime Iris runs on),
instruction-following wins at half qwen's footprint (1.67 GB Q4 vs 3.4 GB), 128K
context, and per-vendor numbers it beats our current reliability champ's family
at its own game. The bar to clear: qwen3.5:4b HA v0.4 **0.789 / pass^3 0.684**,
ET v0.3 **0.917 / 0.833**; gemma-4-12b ceiling HA **0.947 / 0.632**. If
LFM2.5-2.6B matches gemma-class capability at qwen-class reliability in a 1.7 GB
file, it becomes the default brain.

## Can it run here?

Trivially, on every host page in [hardware/](../hardware/) — Q8_0 (2.87 GB)
full-GPU on any 8 GB card. First-run experiment (torrent-aware, exact commands):
[lab/experiments/2026-08-13-lfm2.5-2.6b-first-run](../../lab/experiments/2026-08-13-lfm2.5-2.6b-first-run/README.md).

## Related

- [models/lfm2.5-vl-3b.md](lfm2.5-vl-3b.md) — the vision sibling on the same backbone.
- [models/lfm2.5-colbert-350m.md](lfm2.5-colbert-350m.md) — same family, the router aide.
- [benchmarks/home-automation.md](../benchmarks/home-automation.md) · [benchmarks/email-triage.md](../benchmarks/email-triage.md) — the tests that decide.
- [concepts/eval-reliability.md](../concepts/eval-reliability.md) — pass^k; note the temp-0.1 comparison caveat.
