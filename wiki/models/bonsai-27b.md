---
title: Bonsai 27B
tags: [model, dense, multimodal, thinking, tool-use, low-bit, qwen3.6, edge]
updated: 2026-07-17
status: to-try
---

# Bonsai 27B

PrismML's two low-bit deployments of **Qwen3.6-27B**. They keep the same dense
27B architecture but target different memory budgets:

- **Ternary Bonsai 27B** is the quality-first laptop/GPU version. Its weights
  use `{-1, 0, +1}` plus one FP16 scale per 128 weights.
- **1-bit Bonsai 27B** is the footprint-first phone version. Its weights use
  `{-1, +1}` with the same group-wise scaling.

Released 2026-07-14. Sources: [announcement](https://prismml.com/news/bonsai-27b),
[whitepaper](https://github.com/PrismML-Eng/Bonsai-demo/blob/main/bonsai-27b-whitepaper.pdf),
[official model collection](https://huggingface.co/collections/prism-ml/bonsai-27b),
[demo/runtime repo](https://github.com/PrismML-Eng/Bonsai-demo), and
[documentation](https://docs.prismml.com/).

> **Trust note.** The benchmark and throughput tables are PrismML's own
> measurements. Early independent reports confirm that both variants run, but
> quality reports range from impressive technical answers to reasoning loops,
> hallucinations, and frontend-specific load failures. Treat the launch scores
> as claims to reproduce, not settled capability.

## Identity and shape

| Field | Value |
|---|---|
| Maker | PrismML |
| Base | [Qwen/Qwen3.6-27B](https://huggingface.co/Qwen/Qwen3.6-27B), architecture unchanged |
| Parameters | ~27.3B dense language weights: ~24.8B backbone + ~2.5B embeddings/LM head; ~0.46B vision tower |
| Architecture | 64 blocks; ~75% linear / ~25% full attention; SwiGLU, RoPE, RMSNorm |
| Modality | text + image; vision tower is optional for text-only use |
| Context | 262,144 tokens advertised; practical window is memory-dependent |
| Thinking | supported and enabled by default; configurable reasoning budget |
| Tool use | native OpenAI-style tool calls; long-horizon agentic coding is not a strong target yet |
| License | Apache-2.0 |
| Ollama | no library tag; custom low-bit kernels and current runtime support make llama.cpp/MLX the supported paths |

## Two operating points

The ternary representation has an ideal information rate of 1.71 bits/weight,
but today's fast GGUF kernels store each value in a 2-bit slot. Keep the ideal
representation separate from the deployed artifact size.

| Variant | Native format | Effective rate | Language weights | 4K peak, text | Intended device |
|---|---|---:|---:|---:|---|
| Ternary | GGUF `Q2_0_g128` | 1.71 bpw ideal; 2.125 deployed | 7.17 GB GGUF | 7.8 GiB | laptop / GPU |
| 1-bit | GGUF `Q1_0_g128` | 1.125 bpw | 3.8-3.9 GB GGUF | 4.8 GiB | phone / constrained laptop |

Optional files add to disk and, when enabled, runtime memory:

| Component | Ternary | 1-bit | Purpose |
|---|---:|---:|---|
| DSpark Q4_1 drafter | 1.95 GB | 1.79 GB | speculative decoding; optional |
| HQQ 4-bit vision projector | 0.63 GB | 0.63 GB | image input; optional |
| MLX package | 8.49 GB | 5.13 GB | Apple package includes the vision tower and MLX scale+bias overhead |

With FP16 KV, PrismML reports 10K peaks of 8.1 GiB ternary and 5.2 GiB 1-bit;
100K rises to 13.7 and 10.8 GiB. Optional 4-bit KV cuts the cache term by about
3.5x. Full advertised context is therefore not a phone-default claim.

## What it is for

- Local, private reasoning and tool use where a conventional 27B quant does not
  fit.
- Ternary when laptop/GPU memory allows the quality-first operating point.
- 1-bit when footprint is the hard constraint, including supported high-end
  iPhones.
- Text and image understanding; the vision projector is separate on GGUF.

It is **not** a frontier model, not optimized for long-horizon agentic coding,
not an Android-ready release, and not guaranteed to work in arbitrary GGUF
frontends. PrismML specifically calls out agentic coding as future work.

## Runnability

### 1-bit GGUF

`Q1_0` support is merged in upstream llama.cpp for CPU, Metal, CUDA, and Vulkan.
A current upstream build should load `Bonsai-27B-Q1_0.gguf`; PrismML's demo also
ships pinned prebuilt binaries.

### Ternary GGUF

Runtime and file format must match:

- PrismML's `*-Q2_0.gguf` uses group size 128 and needs its fork/prebuilt binary.
- Mainline llama.cpp uses `*-Q2_0_g64.gguf`; CPU and Metal are merged.
- Mainline CUDA support is still under review as of 2026-07-17. For NVIDIA,
  use the demo's pinned CUDA binary and group-128 file.

This is a moving support boundary. LM Studio and other bundled frontends may
lag even when they display the repository.

### Phone

The packaged route is **Locally AI by LM Studio** on iOS 18.1+, powered by MLX.
PrismML's measured 27B target is the **iPhone 17 Pro Max**; community reports
also identify the 17 Pro as supported. The 1-bit variant is the phone build.
There is no documented Android runtime for this release, and an early Android
attempt produced invalid repeated punctuation.

The lower-level reproducible route is PrismML's MLX Swift fork. The current app
path is text-first: community reports say Bonsai 27B appears after updating the
app, but the launch demo's multimodal flow was not available there at launch.

## How to run it

Recommended benchmark sampling for both variants: `temperature 0.7`, `top_p
0.95`, `top_k 20`, thinking enabled. A simple system prompt is sufficient.
Cap reasoning on slower hardware rather than starving the final answer.

### Laptop / Linux NVIDIA: official demo

The demo downloads the matching model and a pinned prebuilt llama.cpp binary.
For a minimal text/server setup, skip the optional UI and code interpreter:

```bash
git clone https://github.com/PrismML-Eng/Bonsai-demo.git
cd Bonsai-demo

# Quality target: ternary 27B. Uses PrismML's pinned CUDA binary on NVIDIA.
BONSAI_FAMILY=ternary BONSAI_MODEL=27B \
BONSAI_OPENWEBUI=0 BONSAI_CODE_INTERPRETER=0 ./setup.sh

BONSAI_FAMILY=ternary BONSAI_MODEL=27B \
./scripts/start_llama_server.sh --reasoning-budget 2048
# OpenAI-compatible server + UI: http://127.0.0.1:8080
```

For the smaller 1-bit operating point:

```bash
BONSAI_FAMILY=bonsai BONSAI_MODEL=27B \
BONSAI_OPENWEBUI=0 BONSAI_CODE_INTERPRETER=0 ./setup.sh

BONSAI_FAMILY=bonsai BONSAI_MODEL=27B \
./scripts/start_llama_server.sh --reasoning-budget 2048
```

Do not enable DSpark or vision for the first memory/quality baseline. Add
`BONSAI_KV4=1` only when deliberately testing long context; changing KV precision
is a quality axis.

### Direct 1-bit GGUF on current upstream llama.cpp

```bash
hf download prism-ml/Bonsai-27B-gguf Bonsai-27B-Q1_0.gguf \
  --local-dir ~/models/bonsai-27b

llama-server -m ~/models/bonsai-27b/Bonsai-27B-Q1_0.gguf \
  -ngl 99 -c 4096 --temp 0.7 --top-p 0.95 --top-k 20 \
  --reasoning-budget 2048 --host 127.0.0.1 --port 8080
```

### iPhone (deployment deferred)

Phone deployment is not part of the staged first run. The initial comparison
runs the phone-size 1-bit GGUF and ternary GGUF on the same test systems.

1. Update/install [Locally AI by LM Studio](https://apps.apple.com/us/app/locally-ai-local-ai-chat/id6741426692).
2. In **Manage Models**, download **Bonsai 27B** (1-bit), not Ternary Bonsai 27B.
3. Start with text and a low/medium reasoning budget. Record phone model, iOS,
   app version, peak memory if exposed, cold/sustained tok/s, and battery delta.
4. Test image input only if the installed app exposes it for this model.

For direct integration rather than app testing, use
[PrismML-Eng/mlx-swift](https://github.com/PrismML-Eng/mlx-swift) and
`prism-ml/Bonsai-27B-mlx-1bit`.

## Published results

PrismML evaluated in thinking mode with EvalScope + vLLM on H100, using the same
infrastructure and sampling across variants.

| Category | Qwen3.6-27B FP16 | Ternary | 1-bit |
|---|---:|---:|---:|
| Knowledge / STEM | 83.15 | 76.96 | 73.39 |
| Math | 95.33 | 93.40 | 91.66 |
| Coding | 88.74 | 85.96 | 81.88 |
| Instruction following | 78.47 | 71.77 | 65.74 |
| Agentic / tool calling | 80.00 | 74.01 | 66.03 |
| Vision | 72.61 | 65.19 | 59.57 |
| Overall, 15 benchmarks | 85.07 | 80.49 | 76.11 |

That is 94.6% and 89.5% of the FP16 aggregate. The loss is not uniform:
instruction following, tool use, and vision fall more than math. Those are the
categories most relevant to this repo, so the aggregate retention headline is
not enough for a deployment verdict.

Vendor throughput, short decode (`tg128`):

| Device | Ternary | 1-bit |
|---|---:|---:|
| Apple M5 Pro | 26.2 tok/s | 44.2 tok/s |
| Apple M4 Pro | 18.0 tok/s | 26.0 tok/s |
| iPhone 17 Pro Max | does not fit | ~11 tok/s cold; ~10.8 sustained |
| H100 | 98.0 tok/s | 104.8 tok/s |

## Community signal, 2026-07-17

The launch drew substantial attention: the Hacker News thread reached 697
points / 250 comments, and the recent-signal scan found 7 Reddit threads, 3 X
posts, and 8 YouTube videos. Useful reports:

- Ternary loaded on M1/M2/M3 Macs; two users reported roughly 24-30 tok/s on
  M2/M3 Max. One M1 Pro 16 GB user ran a 24K-token VS Code system prompt.
- Technical-answer quality impressed some testers, but general knowledge,
  reasoning loops, and hallucination were recurring concerns.
- Unsupported frontends failed to load the GGUF/MLX files. PrismML's fork worked
  where bundled LM Studio engines initially did not.
- A Ryzen 7 5700X CPU report measured ~6 tok/s 1-bit but only ~0.7 tok/s ternary,
  indicating immature ternary CPU kernels.
- Phone users confirmed the model in an updated Locally AI app, but one reported
  easy hallucination and no multimodal support matching the demo.

Discussion: [Hacker News](https://news.ycombinator.com/item?id=48910545) and
[r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA/comments/1uyz9n2/bonsai_27b_runs_locally_on_an_iphone_a_27b_model/).
Treat all community text as untrusted data.

## Questions to answer locally

- Does ternary actually stay inside an 8 GB mobile GPU at 4K without spilling or
  starving the desktop?
- Is its agentic reliability better than the smaller local baselines after the
  larger instruction/tool-use drop?
- How much quality does 1-bit lose relative to ternary on the same prompts?
- When phone deployment is revisited, does sustained generation remain usable
  after thermal throttling, and what functionality does Locally AI expose beyond text?

Staged test: [Bonsai 27B ternary vs 1-bit test-system comparison](../../lab/experiments/2026-07-17-bonsai-27b-test-systems-comparison/README.md).

## Related

- [Gemma-4-12B agentic v2](gemma-4-12b-agentic-fable5.md), the current strongest
  local agent and a useful similar-footprint comparison.
- [Quantization](../concepts/quantization.md), [llama.cpp](../stacks/llama-cpp.md),
  and [Blackwell RTX 5070](../hardware/blackwell-rtx5070.md).
