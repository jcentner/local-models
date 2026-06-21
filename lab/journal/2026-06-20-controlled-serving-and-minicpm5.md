# 2026-06-20 — Controlled serving, and a 1B model that was lying about being bad

## Why

MiniCPM5-1B looked like a washout. Over Ollama it scored **0/6** on
decision-reasoning — degenerate, looping `<think>` output, sometimes leaking raw
`<|fim_middle|>` tokens — and **0/5** on email-triage. But every one of those
failures came with an asterisk I'd written into the model page myself: *Ollama
can't control this model's thinking.* The Go-template path has no `enable_thinking`
switch, so the hybrid checkpoint neither runs a clean No-Think pass nor cleanly
closes its CoT. I was scoring the serving stack, not the model.

So before writing MiniCPM5 off, I had to serve it *faithfully* — which meant
finally standing up the second runner I'd been deferring: SGLang, the one with
`enable_thinking` and the `minicpm5` tool parser.

## Standing up SGLang — the hard way, then the right way

First attempt: `pip install sglang`. Dead end on this box. SGLang 0.5.13 JIT-compiles
kernels at runtime, and the toolchain it needs isn't here — FlashInfer wants a C
compiler (Triton), the fused-RoPE path wants `CUDA_HOME` for `tvm_ffi`. I have a
Blackwell driver but **no CUDA toolkit and no `nvcc`**. Building from source was a
rabbit hole.

The right way turned out to be the same pattern I'd want for everything else:
**the official container**. `lmsysorg/sglang:latest` ships CUDA 13 and the whole
toolchain inside it, so the host stays clean. I ran it under **rootless Podman +
CDI** — installed `nvidia-container-toolkit`, ran `nvidia-ctk cdi generate`, and the
RTX 5070 showed up inside the container with the default cu130 build running happily
on `sm_120`. I later factored that one-time GPU-in-Podman setup into its own page
([stacks/podman-gpu.md](../../wiki/stacks/podman-gpu.md)) so the next box — and the
llama.cpp container that followed — can reproduce it from one place.

Two bits of housekeeping fell out of this: I lowered the WSL memory cap from 24 to
16 GB (the container does the heavy lifting now, not a host venv), and I deleted the
dead pip-SGLang venv — about 10 GB back.

While I was in serving-infra mode I also stood up the first **PyTorch** environment
on this machine: `~/.venvs/pylate` with `torch 2.11.0+cu128`, and confirmed a real
matmul runs on `sm_120` via a new reusable checker
([scripts/check-torch.py](../../scripts/check-torch.py)). There's still no *system*
torch, but the `cu128` wheel works in a venv — the standard path for the aide models
and PyLate work coming next. A small machine-fact correction to the hardware page,
but a real unblock.

## The reveal: the score was a serving artifact

With SGLang up, `chat_template_kwargs={"enable_thinking": false}` did exactly what
Ollama couldn't: it reliably suppressed the CoT. So I re-ran the confounded sets.

Decision-reasoning was **still 0/6** — but now *coherent*. No-Think landed a mean of
**~2.7/10**, Think **~3.0/10**, the CoT completing in a few hundred to a few thousand
tokens with no truncation. Compare that to Ollama's **~0.17/10** of looping gibberish.
The Ollama number was never a verdict on the model; it was a verdict on the
serving. The *real* verdict is gentler but still clear: coherent-but-shallow
judgment — it inverts risk, contradicts itself — a genuine 1B ceiling, the same shape
as [VibeThinker-3B](../../wiki/models/vibethinker-3b.md). Not a deliberation brain.

That's the lesson I want to keep: **a benchmark score on an uncontrolled serving
stack is measuring the stack.** I'd half-known it; this made it concrete.

## The tool-use twist: a broken parser, and a fallback that salvages it

The more interesting half was tool use. MiniCPM5's whole pitch is agentic tool
calling, and the maker's recommended path is SGLang's `--tool-call-parser minicpm5`.
Except in 0.5.13 that parser **swallows** the model's output: it emits its calls as
`<function name="search_kb"><param name="query">...</param></function>` XML, and the
parser produces *no* `tool_calls` at all. The model's intent was correct; the plumbing
ate it.

So I verified the exact emitted format against a parser-*less* server, then added a
small guarded fallback to the harness — `parse_xml_tool_calls()` — that converts that
`<function ...>` XML in the message content into native `tool_calls` and synthesizes
a valid assistant message when the provider returns none. Run the server **without**
the parser, let the fallback read the raw XML, and suddenly there's a real score.

The numbers: email-triage **0/5 → 2/5**, home-automation **7/12 (0.583)**, both native,
No-Think. It handles act, confirm-before-unlock, read-only status, and — nicely —
ambiguity → `ask`. It fails the refuse, scene/routine, and compound-instruction
scenarios.

## What I learned

**Two verdicts for one model.** MiniCPM5-1B is a weak abstract reasoner
(decision-reasoning 0/6, and now we *know* that's real, not serving noise) but a
**decent home-automation tool-executor** (7/12). Its agentic tilt is genuine. So it's
back in the running — not as the brain that decides, but as a small, always-on
*executor* that the brain delegates to. That's a more useful place to land than the
flat "0/5, washout" I started the day with.

The meta-takeaway is the one worth blogging: **serve it faithfully before you judge
it.** And the cheapest way to faithful serving on a toolchain-less Blackwell box is
an official container under rootless Podman, not a from-source build.

Full writeup:
[lab/experiments/2026-06-20-minicpm5-sglang-controlled](../experiments/2026-06-20-minicpm5-sglang-controlled/README.md).
Stack page: [stacks/sglang.md](../../wiki/stacks/sglang.md).
