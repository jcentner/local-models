---
title: Needle 2 (Cactus Compute)
tags: [model, tool-calling, edge, tiny, finetune]
updated: 2026-08-14
status: to-try
---

# Needle 2 — 45M tool-calling specialist, 14MB binary

An open **45M-parameter function-calling specialist** from Cactus Compute,
shipped as a single **14MB** CQ2-bit ("Cactus Quants") binary that runs a full
session in **~28MB RAM**. Purpose-built for tool calling, device automation,
and structured extraction on CPU-only / sub-$200 hardware — phones, Raspberry
Pi, ESP32-class parts. **Not a chat model**: every input becomes a function
call (or an empty `[]`); there is no free-text channel, no multi-turn, no
clarifying questions.

Why it's in this wiki: **talos** (the home server that will host the agent
suite — olympus FLEET.md) is CPU-only with a 16GB hard cap, and the standing
olympus decision is "if the assistant goes local-model, talos gets a GPU."
A fine-tuned Needle that covers Iris's actuation surface on CPU is the
cheapest possible challenge to that GPU purchase. See the
[fine-tune experiment](../../lab/experiments/2026-08-14-needle2-finetune-household/README.md).

## Identity & sources

| | |
|---|---|
| Maker | Cactus Compute, Inc. |
| Released | Needle 2: ~2026-08-10 (Show HN, 527 pts) |
| GitHub | [cactus-compute/needle](https://github.com/cactus-compute/needle) (~5.5k stars, trending) |
| Weights | [Cactus-Compute/needle2](https://huggingface.co/Cactus-Compute/needle2) (auto-downloaded/cached by the runtime) |
| Paper | [arXiv 2607.18363](https://arxiv.org/abs/2607.18363) — "A Controlled Study of Attention-Only Transformers" (**preprint**, not peer-reviewed despite hype claims) |
| License | Code **MIT**, weights **Apache 2.0** |

## Architecture & shape

- **Simple Attention Network (SAN)**: no feed-forward layers — Hadamard MLP
  replaces the FFN, capacity reallocated into deeper attention. The paper's
  ablation: removing FFN costs 0.26 nats at matched FLOPs; reallocating into
  attention closes it to ~0.006. Deficit concentrates on *knowledge* recall,
  not context-grounded tasks — which is why a tool-calling specialist gets
  away with it. GQA, engram key-value memory, multi-lane hyper-connections.
- **~70 MFLOPs/token** (claimed) vs ~460 for LFM2.5-230M, ~540 for
  FunctionGemma-270M — the compute budget is the whole pitch.
- **Context: 256-token sliding window** with tool schemas pinned as KV sinks.
  This is a hard design limit, not a config knob.
- **Grammar-constrained decoding**: a byte-level grammar is compiled from the
  declared tool schemas, so output JSON is valid-by-construction against
  *your* tools. Unselected tools are unreachable, not merely unlikely.
- **Calibrated confidence head** (claimed): scalar confidence per response,
  intended for gating/escalation. Trained head, not verbalized confidence —
  calibration is measurable, and measuring it is a core goal of our
  experiment.
- **Built-in tool retrieval**: top-5 relevant tools from large catalogs.
- Languages: EN, DE, PL, FR, NL, IT (+ Latin), per the author on HN.

## Footprint & formats

| Artifact | Size | Notes |
|---|---|---|
| `.cact` binary (CQ2-bit) | 14 MB | weights baked into the inference engine; no separate model file |
| Peak session RAM | ~28 MB | claimed |
| Decode | ~500 tok/s on Raspberry Pi 5; 300–700 on budget phones | claimed; a desktop CPU should exceed this — measure |

**No GGUF, no Ollama, no safetensors distribution, no OpenAI-compatible
endpoint.** The runtime is the `cactus-needle` Python package (plus native
engines for ARM64/x86-64/ARMv7/RISC-V/WASM). This makes it
**benchmark-harness-incompatible** (our agentic rollout speaks
OpenAI-compatible multi-turn) — it gets an objective single-turn probe
instead, aide-style ([aide-models](../concepts/aide-models.md) I/O-contract
thinking applies even though it's generative).

## I/O contract

- **In**: one short natural-language instruction + declared tool schemas
  (Python functions via `@needle.tool`, or Pydantic models for extraction).
- **Out**: `{function_calls: [...], reasoning: str, confidence: float}` —
  JSON only, grammar-constrained. Off-topic input → empty `function_calls`
  with low confidence (inconsistently — see gotchas).

## How to run

```bash
# venv, never system python
python3 -m venv .venv && .venv/bin/pip install cactus-needle
```

```python
import needle

@needle.tool
def get_weather(city: str):
    "Get current weather for a city."
    return {"city": city, "temp_c": 27}

agent = needle.Needle(tools=[get_weather])
print(agent.run("what's it like in Lagos?")["results"])
```

Browser playground: `needle playground` → http://127.0.0.1:7860. Weights
auto-download from HF on first use; fully offline after that.

**Fine-tuning** (the interesting part): LoRA on the frozen base, adapters
merged at export into a single `.cact`, 2- or 4-bit export. Training is
JAX-based (NVIDIA CUDA or Apple Metal). The package ships a data-synthesis
path via OpenRouter — **we do not use that** (API-key policy); we synthesize
the dataset ourselves (see experiment).

## Benchmarks (claimed, unverified here)

- **BFCL v4 single-turn: 93.4%** well-formed/correct calls over 3,641 tests
  (claimed; via launch coverage — verify against the model card when running).
- "Trades wins" with FunctionGemma 270M, LFM2.5 230M, Apple FM at 5–70x
  smaller.
- The honest loss: **Apple FM 61.7 vs Needle 42.6** once tasks turn general —
  it was never in that fight.

## Community signal (last30days + HN, 2026-08-14)

Show HN 527 pts / 182 comments; #2 on GitHub trending (~661 stars/day).
Real-world pokes at the web demo found the failure floor fast:

- Off-topic input ("HN", "potato", "I'm hungover") → `lock_door(front door)`.
- **"do not lock the door" → locks the door** (negation blindness).
- "make it a little warmer" → thermostat to 65 in `cool` mode.
- **Every one of these carried `confidence: 0`** — the author's standing
  answer is "threshold on confidence, fine-tune for your device."
- Ambiguity is acted on, never asked about (no text channel to ask with).

Community independently converged on our architecture: Home Assistant
integration, STT (Whisper) → Needle on a Pi, and **confidence-gated
escalation** to a bigger model — see
[open question in backlog](../backlog.md#open-research-questions-from-model-pages).

## What it is NOT for

General chat, multi-turn conversation, confirm flows, clarifying questions,
anything needing >256 tokens of context. Our [home-automation
benchmark](../benchmarks/home-automation.md) treats ambiguity-ask and
double-confirm as *required* behaviors — stock Needle structurally fails
those classes, so it is **not a candidate for the standing agentic matrix**.
The bet is narrower: after a domain fine-tune, is single-shot actuation +
a trustworthy confidence gate enough for the *routine* slice of Iris's
surface, with everything else escalating to the API model? That question —
including "is the confidence head actually calibrated?" — is the
[experiment](../../lab/experiments/2026-08-14-needle2-finetune-household/README.md).

## Related

- [LFM2.5-ColBERT tool-selection](../../lab/experiments/2026-06-20-lfm2.5-colbert-tool-selection/README.md) — same single-turn objective-probe shape
- [aide-models](../concepts/aide-models.md) — I/O-contract eval pattern
- [eval-reliability](../concepts/eval-reliability.md) — k-run flakiness policy applies to the probe
