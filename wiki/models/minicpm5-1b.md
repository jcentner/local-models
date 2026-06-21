---
title: MiniCPM5-1B
tags: [model, dense, small, on-device, llama-arch, hybrid-reasoning, tool-use, code, to-try]
updated: 2026-06-19
status: tried
---

# MiniCPM5-1B (a.k.a. "MiniCPM-5")

A **1B dense Transformer** from **OpenBMB** (Open Lab for Big Model Base —
Modelbest + THUNLP + RUC GSAI), released **2026-05-19** as the first checkpoint
of the **MiniCPM5** series. Built for **on-device / local deployment**: a single
hybrid-reasoning checkpoint that serves as both a fast assistant (No Think) and a
deliberate reasoner (Think) via the same chat template. The pitch: **1B-class
open-source SOTA**, strongest at **agentic tool use, code, and competition math**.

Sources: [GitHub OpenBMB/MiniCPM](https://github.com/OpenBMB/MiniCPM) ·
[HF openbmb/MiniCPM5-1B](https://huggingface.co/openbmb/MiniCPM5-1B) ·
[HF openbmb/MiniCPM5-1B-GGUF](https://huggingface.co/openbmb/MiniCPM5-1B-GGUF) ·
[Tech report (MiniCPM4) arXiv 2506.07900](https://arxiv.org/abs/2506.07900) ·
[online demo](https://huggingface.co/spaces/openbmb/MiniCPM5-1B-Demo). Community
signal via last30days (2026-06-19): heavy hype on X
([@socialwithaayan benchmark thread](https://x.com/socialwithaayan/status/2059979793408692360)),
[Bijan Bowen "Is This a USABLE 1B Model?"](https://www.youtube.com/watch?v=ZWwtHS1iW-k)
(16.5K views), [Prompt Engineer "1B agent, 100+ tok/s on 8GB GPU"](https://www.youtube.com/watch?v=i-Oq_CcFsT4).

## Identity & shape

| Field | Value |
|---|---|
| Maker | OpenBMB (Modelbest · THUNLP · RUC GSAI) |
| Released | 2026-05-19 |
| Architecture | standard `LlamaForCausalLM` — **no custom kernels, no model-code fork** |
| Params | **1,080,632,832** total · 679,552,512 non-embedding · **dense** |
| Layers | 24 · GQA: 16 Q heads / 2 KV heads |
| Modality | text only |
| Context | **131,072** (128K) native |
| Native precision | BF16 |
| License | **Apache-2.0** (code *and* weights) |
| Variants | `MiniCPM5-1B` (RL+OPD final), `-SFT` (pre-RL), `-Base` (pretrain only), `-GGUF`, `-MLX` |
| Ollama tag | no official `ollama.com/library` tag yet — run the official GGUF directly (see below) |

## What it's for (and not for)

- **For:** local assistants, **coding agents**, **tool-use / function-calling
  workflows**, and reasoning where a compact model is preferred. Native long
  context (128K) and Think / No Think modes in one checkpoint.
- **Not for (caveats):** it is still a **1B model** — the maker frames it as a
  *practical* small-model choice, not a frontier general assistant. Expect the
  usual small-model limits on broad world knowledge and reliability; outputs need
  review in high-stakes settings (the card says so explicitly). Unlike
  [VibeThinker-3B](vibethinker-3b.md), tool use **is** an intended, trained
  capability here — this is the relevant axis for a home-automation agent.

This is a **generalist-leaning on-device model with an agentic/tool-use tilt**,
the opposite positioning to a math-only specialist.

## Hybrid reasoning & sampling (run-critical)

One checkpoint, two modes via the chat template's `enable_thinking` flag (built-in
`<think>` block):

| Mode | Sampling | Flag |
|---|---|---|
| **Think** (deliberate reasoner) | temperature **0.9**, top_p **0.95** | `enable_thinking=True` |
| **No Think** (fast assistant) | temperature **0.7**, top_p **0.95** | `enable_thinking=False` |

Like any thinking model, in Think mode the `<think>` CoT consumes output tokens —
budget a generous `num_predict` / `max_tokens` or the final answer can be
truncated. RL+OPD
post-training specifically **cut overlong responses by ~29 pts**, so Think mode is
less runaway than a pure-CoT specialist, but still budget headroom.

## Tool calling

MiniCPM5-1B emits **XML-style tool calls**. The maker's recommended path is
**SGLang** with the built-in `minicpm5` parser, which converts them to
OpenAI-compatible `tool_calls` natively:

```bash
python -m sglang.launch_server --model-path openbmb/MiniCPM5-1B --port 30000 \
    --tool-call-parser minicpm5      # or: --tool-call-parser auto
```

Over llama.cpp/Ollama you get the raw XML and parse it yourself. For evaluating
tool-use quality see [benchmarks/bfcl.md](../benchmarks/bfcl.md).

## Benchmarks

**Official headline:** average **42.57** across reasoning, knowledge, code,
instruction-following, math, logic, and agentic benchmarks — vs a best **35.61**
among strong open-source models in the same size class (the maker's comparison
set: LFM2.5-1.2B-Thinking, Qwen3-0.6B/think, Qwen3.5-0.8B/think). Source: the
[GitHub README](https://github.com/OpenBMB/MiniCPM) / HF card leaderboard figure.

**Per-benchmark (community-reported from the official leaderboard figure, via X —
treat as untrusted until reproduced):** MiniCPM5-1B vs Qwen3.5-0.8B —
MMLU-Pro 48.85 (42.74), MMLU-Redux 70.06 (61.50), **MATH-500 91.60 (30.40)**,
**AIME-2025 40.42 (1.04)**, **τ²-Bench 79.53 (19.60)**
([@socialwithaayan](https://x.com/socialwithaayan/status/2059979793408692360)).

> **Benchmaxxing flag.** The math jumps (MATH-500 ~91, AIME ~40 at 1B) are
> extraordinary and the Reasoning RL was trained on
> [DAPO-Math-17k](https://huggingface.co/datasets/BytedTsinghua-SIA/DAPO-Math-17k) —
> exactly the kind of narrow, verifiable-reward training that inflates competition-math
> scores without proving general capability. Verify on **fresh, unpublished**
> problems and on the **tool-use** axis that actually matters here, not the
> headline numbers. Same lesson as [VibeThinker-3B](vibethinker-3b.md).

## Size & resource requirements (machine-independent)

A 1B model — footprints are tiny; the binding constraint is KV cache at long
context, not weights. Official GGUF sizes:

| Quant | File size | Approx weights in VRAM | Notes |
|---|---|---|---|
| Q4_K_M GGUF | **688 MB** | ~0.7 GB | smallest sane |
| Q8_0 GGUF | **1.15 GB** | ~1.2 GB | safest quant for a small model |
| F16 GGUF | **2.17 GB** | ~2.2 GB | full precision |
| BF16 (safetensors) | ~2.2 GB | ~2.2 GB | original weights |

KV cache at 128K is the real cost; at modest contexts (8–32K) it adds only a few
hundred MB to ~1 GB. Community report: F16 runs in ~7–8 GB VRAM at long context
and **100+ tok/s on an 8 GB GPU**
([Prompt Engineer](https://www.youtube.com/watch?v=i-Oq_CcFsT4)). See
[concepts/quantization.md](../concepts/quantization.md) for the VRAM math.

## Runnability

Because it's **stock `LlamaForCausalLM`**, mainstream engines load it directly —
no branch, no custom sampler. Official cookbooks exist for Transformers, vLLM,
SGLang, llama.cpp, **Ollama**, LM Studio, MLX, and ArcLight (see the
[deployment docs](https://github.com/OpenBMB/MiniCPM/tree/main/docs/deployment)).
No CUDA-arch gotcha for GGUF inference; [Blackwell sm_120](../hardware/blackwell-rtx5070.md)
only matters for from-source vLLM/SGLang builds.

## How to run it

### A. Ollama (daily driver) — needs the official Go TEMPLATE

> **Gotcha (verified 2026-06-19):** Ollama does **not** evaluate the GGUF's embedded
> Jinja chat template — it falls back to the Modelfile's Go `TEMPLATE`. A bare
> `ollama run hf.co/openbmb/MiniCPM5-1B-GGUF:Q8_0` (or an auto-detected template)
> produces **degenerate output** (`"Short Un In Short Un In..."`). You **must**
> supply the [official cookbook](https://github.com/OpenBMB/MiniCPM/blob/main/docs/deployment/ollama.md)
> template, which ranges over `.Messages` (multi-turn) with no stray leading `<s>`:

```bash
cat > Modelfile <<'EOF'
FROM hf.co/openbmb/MiniCPM5-1B-GGUF:Q8_0
TEMPLATE """{{- if .Messages -}}
{{- range .Messages -}}
<|im_start|>{{ .Role }}
{{ .Content }}<|im_end|>
{{ end -}}
<|im_start|>assistant
{{ end -}}"""
PARAMETER stop "<|im_end|>"
PARAMETER stop "</s>"
PARAMETER temperature 0.7
PARAMETER top_p 0.95
PARAMETER num_ctx 8192
EOF
ollama create minicpm5-1b -f Modelfile
ollama run --verbose minicpm5-1b "List 3 uses for a 1B local model."   # ~150-185 tok/s
```

**Think vs No Think:** the template above is No-Think (temp 0.7). For Think mode
raise `temperature 0.9`. Note that over Ollama you **cannot reliably suppress**
the model's `<think>` CoT (the `think:false` / `--no-think` flag is ignored by this
GGUF), so budget a generous `num_predict`. Native **tool calls are XML** and need
SGLang's `minicpm5` parser; over Ollama you parse them yourself. See
[stacks/ollama.md](../stacks/ollama.md).

### B. llama.cpp (engine-level control)
```bash
llama-server -m MiniCPM5-1B-Q8_0.gguf -ngl 99 -c 32768 --temp 0.7 --top-p 0.95
```
See [stacks/llama-cpp.md](../stacks/llama-cpp.md).

### C. SGLang / vLLM (BF16; required for native tool-call parsing)
```bash
pip install "sglang[srt]>=0.5.12"
python -m sglang.launch_server --model-path openbmb/MiniCPM5-1B --port 30000 \
    --tool-call-parser minicpm5
```
vLLM (`pip install "vllm>=0.21"; vllm serve openbmb/MiniCPM5-1B`) is a
[stretch on 8 GB](../stacks/vllm.md) but trivial at 1B — useful for the
OpenAI-compatible tool-use path.

## Can it run here?

Trivially — this is one of the smallest models in the wiki. The per-machine fit
verdict for the [ProArt P16](../hardware/proart-p16.md) lives in the test
experiment: [lab/experiments/2026-06-19-minicpm5-1b-first-run](../../lab/experiments/2026-06-19-minicpm5-1b-first-run/README.md).
Short version: **any quant (even F16) fits fully on the 8 GB GPU with a large
context**, and [WSL RAM](../concepts/wsl2-memory.md) is irrelevant at this size.
Expect high tok/s (community: 100+ on comparable 8 GB hardware).

## Why it matters for the home-automation north star

Unlike the math/code specialists already in the wiki, MiniCPM5-1B is explicitly
trained for **tool use and agentic workflows** at a footprint small enough to run
always-on. That makes it a real candidate **brain** for a local-agent home
system — and a natural fit for the act-vs-ask-vs-nothing skill. The open question
is whether 1B is *reliable* enough for the job (the Bijan Bowen "USABLE?" framing),
which is what testing
decides.

## First-run finding (2026-06-19)

Ran on the [email-triage](../../benchmarks/email-triage/README.md) agentic set
(act/ask/escalate): **0/5** at recommended No-Think sampling *and* at temp 0
(vs qwen3.5:4b which passed e1). It (a) can't suppress `<think>` over Ollama so the
JSON action truncates, (b) never commits to a terminal `reply`/`escalate`, and
(c) misused the tool-arg schema (`question` vs `query`). **Caveat:** this is partly
a **protocol mismatch** - our prompt-mode "JSON only" rollout is adversarial to a
hybrid-thinking model whose native tool format is XML (SGLang `minicpm5` parser).
It does **not** refute the headline tau-2-Bench number; a fair tool-use test needs
the native path. The harness now has a **native-tool-calling mode**
(`--tool-protocol native`, added 2026-06-19) that reads `message.tool_calls` from
the provider - but MiniCPM5's **stock Ollama template is tool-blind**, so the fair
re-test must go through **SGLang `--tool-call-parser minicpm5`** over the
`openai-compatible` provider (its XML calls become OpenAI `tool_calls`). Full writeup:
[lab/experiments/2026-06-19-minicpm5-1b-first-run](../../lab/experiments/2026-06-19-minicpm5-1b-first-run/README.md).

## Decision-reasoning finding (2026-06-19)

Ran on the fresh [decision-reasoning](../benchmarks/decision-reasoning.md) set
(6 tradeoff scenarios, opus-4.8-judged): **0/6, mean ~0.17/10** (vs
[VibeThinker-3B](vibethinker-3b.md) 1/6, mean ~4.3/10). The dominant failure mode
is a **runaway / degenerate `<think>`** that loops, restates the prompt, and burns
the whole `num_predict` budget without landing a `Recommendation:` - at Think temp
0.9 it degenerated into gibberish with leaking `<|fim_middle|>` tokens; at the
template-tuned No-Think temp 0.7 it produced 16-19k-char repetitive rambles. Same
root cause as the tool-use finding: **MiniCPM5's hybrid `<think>` is uncontrollable
over Ollama** - the Go-template path has no `enable_thinking` selection, so the
model neither runs clean No-Think nor cleanly closes its CoT. Even the coherent
fragments misread the scenarios. **Caveat:** confounded by the serving limitation,
not a clean reasoning verdict - but note VibeThinker (also a thinking model, also
over Ollama) *did* produce parseable answers on the same set, so MiniCPM5's
degeneration is worse. A clean read needs the proper chat template
(Transformers/vLLM/SGLang with `enable_thinking` control), deferred with the SGLang
tool-use re-test.

## SGLang controlled-serving verdict (2026-06-20)

Served via the **[SGLang container](../stacks/sglang.md)** (rootless Podman + CDI
on Blackwell) so thinking is finally controllable. This is the **clean** re-test
of the confounded 2026-06-19 Ollama runs.

- **`enable_thinking` works:** `chat_template_kwargs={"enable_thinking":false}`
  reliably suppresses the CoT (the control Ollama lacked).
- **Decision-reasoning still 0/6 in both modes**, but now *coherent*: No-Think
  mean **~2.7/10**, Think mean **~3.0/10** (CoT completes, 259-2788 tok, no
  truncation) — vs the Ollama **~0.17/10** gibberish. So the Ollama score was a
  **serving artifact**; the real verdict is **coherent-but-shallow** judgment
  (inverts risk, self-contradictory) — a genuine 1B ceiling, same shape as
  [VibeThinker-3B](vibethinker-3b.md). **Not a viable reasoning brain** here.
- **Tool-use — SGLang's parser is broken, but a harness XML fallback recovers it.**
  The model emits the **right intent** (`search_kb` + correct query) as native
  **XML**, which SGLang 0.5.13's `--tool-call-parser minicpm5` **swallows** (no
  `tool_calls`). Running the server *without* the parser + a new harness
  `parse_xml_tool_calls()` fallback gives a real score: **email-triage 2/5,
  home-automation 7/12** (native, No-Think). It handles act / confirm-unlock /
  read-only / **ambiguity→ask**, and fails refuse / scene / compound. **Its agentic
  tool-use tilt is real** — a plausible home-agent *tool-executor* even if not the
  deliberation brain.

Writeup: [lab/experiments/2026-06-20-minicpm5-sglang-controlled](../../lab/experiments/2026-06-20-minicpm5-sglang-controlled/README.md).

## Open questions
- Does the agentic/tool-use strength survive on its **native tool path**?
  **Answered (2026-06-20):** SGLang 0.5.13's `minicpm5` parser swallows the
  model's `<function>` XML, but running **without** the parser + the harness
  `parse_xml_tool_calls()` fallback scores it fairly — **email-triage 2/5,
  home-automation 7/12** (native). The tool-use tilt is real; it's a decent
  home-automation *executor*. (Open: a newer SGLang build with a working parser.)
- How does it do on the fresh [decision-reasoning](../benchmarks/decision-reasoning.md)
  set vs [VibeThinker-3B](vibethinker-3b.md)? **Answered (2026-06-19, over Ollama):**
  0/6 vs VibeThinker 1/6 - but confounded by the uncontrollable-`<think>` serving
  limitation (see the Decision-reasoning finding above); a clean read still needs a
  controlled-template run (Transformers/vLLM/SGLang).
- Is the headline competition-math real, or DAPO-Math benchmaxxing? Quick check on
  fresh problems.
- Quant sensitivity at 1B: does Q4_K_M (688 MB) hold up vs Q8_0 on reasoning/tool
  use? Cheap [quant sweep](../concepts/quantization.md).
