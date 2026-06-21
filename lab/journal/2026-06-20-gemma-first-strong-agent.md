# 2026-06-20 — gemma-4-12B: a first genuinely strong local agent

## Why

Everything I'd run through the agentic harness so far had been a small model with
an asterisk. qwen3.5:4b was the workhorse but middling; VibeThinker is a math
specialist that doesn't transfer; MiniCPM5-1B is a 1B executor with a low ceiling.
I wanted to know what the harness says when a *capable* model meets it — and whether
a 12B model can even fit the 8 GB budget while staying capable.

The candidate: a community **coding + agentic** finetune of Google's new (~10-day-old)
**Gemma 4 12B v2** — `gemma4_unified`, dense 11.95B, Apache-2.0, 256K context, with
native tool-use and thinking. The lineage is a coder base plus agentic trajectories
and a general slice, with the Fable-5 synthetic CoT rebuilt using Opus 4.8. The
author's own self-eval claims ~3.5× the base on `tau2-telecom` but is explicitly
relative and unverified. Exactly the kind of hyped-but-unproven model the
[/new-model](../../.github/prompts/new-model.prompt.md) flow exists to pin down.

## Ingest, and a pivot to v2-only

I'd started ingesting the v1 *pure-coding* variant, but it's the wrong tool for the
home-automation north star. So I dropped the v1 page and experiment and replaced them
with the v2 **coding + agentic** model — the one with native Gemma 4 tool-use. Note
to self that bit me later: v2 needs llama.cpp's `--jinja` to get the tool template;
without it the native tool path is silent.

## The serving budget is brutal at 12B on 8 GB

Before any quality run I needed llama.cpp serving, and I took the same container path
as SGLang: the official prebuilt CUDA image (`ghcr.io/ggml-org/llama.cpp:server-cuda`,
build 9737) under rootless Podman + CDI. The GPU showed up — and so did the real
constraint. With the container and the desktop overhead, only about **6999 of 8150
MiB** were actually free. The usable budget is **~6.8 GB**, not 8.

That number reframed the whole experiment. A 12B model in Q4_K_M is ~7 GB of weights
*before* KV cache. The question stopped being "which quant is best" and became
"**can Q4 run on this box at all, or is Q3 the only full-GPU option?**"

## The sweep

So I ran a 5-cell quant × KV × offload sweep, scored on `code-basics` (sandboxed)
and `home-automation` for quality plus throughput:

- **A — Q3_K_M, f16 KV, full GPU** — the winner. Fits with headroom, ~32 tok/s.
- **A′ — Q3_K_M, q4_0 KV** — isolates the KV-quant effect.
- **B — Q4_K_M, q4_0 KV** — Q4 only squeezes onto the GPU if you quantize the KV cache…
- **C — Q4_K_M, f16 KV, 30 layers offloaded** — …or spill layers to CPU, which tanks throughput.
- **D — Q4_K_M, f16 KV, full GPU @ 4K ctx** — to isolate offload from context.

The verdict: **Q3_K_M f16 full-GPU wins** on the 8 GB budget. Pushing to Q4 costs
you either KV precision (q4_0, which measurably hurt quality) or speed (CPU offload).
On this hardware the higher-quant dream isn't worth it — the cheaper weights that
stay fully resident in fast memory beat the richer weights that don't.

## The result that made me sit up

At Q3_K_M, full GPU, the agentic numbers:

- **home-automation: 11/12.**
- **code-basics: 4/4.**

That's the first model in this wiki that's just… *good* at the lighthouse use-case.
It acts when it should, confirms before sensitive actions, doesn't over-actuate, and
writes working code. After a parade of asterisked small models, a genuinely strong
local agent that fits on a laptop GPU is a real milestone — and a useful anchor at the
top of the capability range for everything I benchmark below it.

## What I learned

- **The 8 GB budget is really ~6.8 GB once you serve in a container.** Design quant
  experiments around the measured free VRAM, not the sticker number.
- **Lower quant + full residency beats higher quant + offload/KV-quant** on
  bandwidth-bound laptop hardware. Q3_K_M was not a compromise here; it was the right
  answer.
- I now have a strong-end reference point. The interesting follow-ups are a v3 (already
  announced) and whether the agentic strength holds up under the reliability lens
  (pass^k), which is the next thread.

Experiment:
[lab/experiments/2026-06-20-gemma-4-12b-v2-quant-config-sweep](../experiments/2026-06-20-gemma-4-12b-v2-quant-config-sweep/README.md).
Model page: [models/gemma-4-12b-agentic-fable5.md](../../wiki/models/gemma-4-12b-agentic-fable5.md).
