# 2026-06-21 — Reliability, a cross-model critic, and a second model track

## Why

Two things had been nagging me. First, my agentic scores were all single-sample —
one rollout, pass or fail. Small and quantized models *flake*; one sample is noise
dressed up as a verdict. Second, the agentic benchmarks themselves were young, and I
only had my own eyes on the scorer. This was the day I tightened both, and then
widened the project's scope to the support models the home agent will actually need
around its brain.

## Reliability: measure the flakiness, don't hide it

The methodology I'd written down but not yet *lived* is observed pass@k vs pass^k.
`observed_pass@k` is best-of-k — a capability ceiling that only rises with k.
`pass^k` (tau-bench's reliability metric) is the opposite: did it get the item right
on **all** k samples. The gap between them is the flakiness, and for a home agent
that gap is the whole ballgame — I don't want a light switch that works two times in
three.

So I re-baselined at **k=3, at the recommended temperature** (not temp=0, which would
hide the very flakiness I'm trying to see). The story the two numbers tell together is
exactly why it's worth the cost:

- **gemma-4-12B (Q3_K_M):** email-triage obs **0.92** / pass^3 **0.83**;
  home-automation obs **0.89** / pass^3 **0.72**. Strong *and* fairly reliable.
- **qwen3.5:4b:** email-triage obs **0.83** / pass^3 **0.75**; home-automation obs
  **0.78** / pass^3 **0.67**. Solid mid-tier.
- **MiniCPM5-1B:** email-triage obs **0.92** / pass^3 **0.42**, with **6 of 12** items
  flaky. That single line is the entire argument for the method: read only the
  ceiling and the 1B model looks as good as the 12B; read pass^k and it's
  **capable-but-unreliable** — it *can* do it, but not *dependably*. For an executor
  you trust unattended, that's disqualifying in a way a single sample would have hidden.

## A cross-model critic on my own benchmark

Before trusting the home-automation numbers I had **gpt-5.5** review the v0.3 suite
in the background — a read-only audit while I worked on something else (the
commit-as-you-go + background-review workflow). It came back with real findings, and
triaging them produced **v0.4**:

- **The one that mattered:** `forbidden_device_attempts` only scanned *applied* tool
  calls. So a native, post-respond skipped sibling — `[say, set_device(back_door_lock)]`
  — an *attempted* substitute actuation that happened to leave state unchanged, slipped
  right past the refuse scenarios. Now it scans every emitted `set_device`, applied or
  not. An attempted forbidden change fails even when nothing moved. That's the correct
  safety semantics, and I'd had it subtly wrong.
- **A fairness fix:** one scenario required `security_system == "disarmed"` *exactly*,
  but a model saying "off" or "disabled" is perfectly correct. `expected_state` values
  can now be a scalar **or a list** of acceptable answers — a false-fail removed.
- **Fail-closed hardening** on the manifest validation, and a documented decision to
  *not* change one thing: with the message-judge off, a verbal-only fabrication that
  changes no state isn't caught. That's consistent across the suite, so rather than
  paper over it I made the recommendation explicit — **run the v0.4 baseline with
  `--judge-messages`**, the optional frontier-judge AND-gate that grades the message
  text on top of the deterministic state check.

Having a frontier model from a *different* family audit the harness caught things I'd
have stared past. I'm keeping that in the loop.

## A second model track: the aide models

The chat brain is only part of a home agent. It needs **ears** (STT), a **voice**
(TTS), a **memory** (embeddings), and a **router** (retrieval / reranking to pick the
right tool and context). Those are non-generative *aide models*, and they break every
assumption `/new-model` makes — no chat template, no sampling, no thinking mode; an
**I/O contract** takes their place; most don't run on Ollama; and they're judged on
objective metrics (WER, NDCG@k, Recall@k, MOS) via external evals, not the harness.
The Copilot-CLI judge can't even *hear*, so TTS naturalness isn't LLM-judgeable at all.

So I opened the track properly: a concept page
([concepts/aide-models.md](../../wiki/concepts/aide-models.md)) with the taxonomy,
per-class eval contract, and a distinct page schema, plus a sibling ingest prompt,
[/new-aide](../../.github/prompts/new-aide.prompt.md).

Its first subject is the **router**: **LFM2.5-ColBERT-350M** (Liquid AI, 353M, a
late-interaction retriever — per-token vectors, MaxSim, 11 languages). The off-the-shelf
benchmarks test *document* retrieval (NanoBEIR NDCG@10 0.605, MKQA-11 Recall@20 0.694),
but the home-agent question is **tool selection** — given a pool of N tools, does the
right one land in the top-k? That's the one metric here worth hand-rolling a scorer
for, and it seeds a future `benchmarks/tool-selection` set. The PyTorch/Blackwell venv
I stood up yesterday is what makes running it possible.

## What I learned

- **Report the ceiling and the reliability side by side, always.** MiniCPM5's
  0.92/0.42 split is the cleanest demonstration I have of why a single pass lies.
- **A cross-family critic on your own eval is worth the premium request.** gpt-5.5
  found a genuine safety-scoring hole in the refuse logic that I owned.
- The project is widening from "which brain?" to "which brain, how *reliably*, and
  with which ears/voice/memory/router around it" — which is the actual shape of the
  home-agent suite I'm building toward.
