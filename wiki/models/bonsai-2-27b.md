---
title: Bonsai 2 27B (Ternary)
tags: [model, dense, multimodal, thinking, tool-use, low-bit, ternary, qwen3.8, edge]
updated: 2026-09-18
status: to-try
---

# Bonsai 2 27B (Ternary)

PrismML's second-generation ternary 27B: **Qwen3.8-27B** with every language
weight (embeddings, attention, MLP, LM head) in `{-1, 0, +1}` plus one FP16
scale per 128 weights, at a true 1.72 bits/weight. It succeeds
[Bonsai 27B](bonsai-27b.md) (Qwen3.6-based, 2026-07-14). This release is
**ternary only**; there is no 1-bit Bonsai 2.

Released 2026-09-17. Sources:
[announcement](https://prismml.com/news/bonsai-2-27b),
[GGUF model card](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf)
(the primary source for this page, read 2026-09-18),
[whitepaper](https://github.com/PrismML-Eng/Bonsai-demo/blob/main/bonsai-2-27b-whitepaper.pdf),
[demo/runtime repo](https://github.com/PrismML-Eng/Bonsai-demo) (PrismML calls it
"the source of truth for running these models"),
[llama.cpp fork](https://github.com/PrismML-Eng/llama.cpp),
[MLX build](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-mlx-2bit).

> **Trust note.** Every benchmark and throughput number below is PrismML's own
> measurement. The announcement page and the model card print different category
> tables (the announcement shows an 83.9 overall against a Qwen3.8 reference of
> 85.4; the card shows 84.78 against 86.32 over 14 named benchmarks). This page
> uses the card, which names its benchmarks. The first Bonsai's launch scores met
> mixed independent reports (reasoning loops, hallucination); treat these as
> claims to reproduce. No community scan has been run yet (released one day
> before this ingest).

## Identity and shape

| Field | Value |
|---|---|
| Maker | PrismML |
| Base | [Qwen/Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B), architecture unchanged |
| Parameters | 27.36B total: 24.35B backbone (64 blocks) + 2.54B embeddings/LM head + 0.46B vision tower (27 blocks) |
| Architecture | Hybrid attention, ~75% linear / ~25% full; SwiGLU, RoPE, RMSNorm |
| Weight format | Ternary g128, stored in a **rotated basis**: a blockwise Hadamard rotation (block 1024) is folded into the weights and the runtime applies the matching transform to activations |
| Higher-precision remainder | 26.2M parameters (0.0976%): the linear-attention recurrent state path and the norms |
| Modality | text + image; the vision tower is a separate optional file |
| Context | 262,144 tokens; FP16 KV costs 64 KiB per token (demo README) |
| Thinking | on by default at `xhigh` effort; `medium` is supported; `low` is not (it behaves like `xhigh`) |
| Tool use | native OpenAI-style `tool_calls` with round trips (demo `TOOLS.md`) |
| License | Apache-2.0 |
| Ollama | no; the formats need PrismML's fork |

What changed from the first Bonsai 27B: the base (Qwen3.6 to Qwen3.8), the
Hadamard rotation, a dense-trit packing that reaches the ideal size, and the
claimed retention (95% to 98.2%). PrismML dropped the first release's "not for
agentic coding" disclaimer and now lists coding agents and long-horizon tasks as
targets.

## Files

| File | Packing | True bpw | Size | sha256 (HF LFS) |
|---|---|---:|---:|---|
| `Ternary-Bonsai-2-27B-PTQ1_0.gguf` | dense trits | 1.75 | 5.95 GB (5.54 GiB) | `53107f53…fe33ee3` |
| `Ternary-Bonsai-2-27B-PQ2_0.gguf` | one trit per 2-bit slot | 2.13 | 7.21 GB (6.71 GiB) | `3907dc16…ae62ec1` |
| `Ternary-Bonsai-2-27B-mmproj-Q8_0.gguf` | vision tower | — | 0.63 GB | `6807ede6…d631903` |
| `Ternary-Bonsai-2-27B-mmproj-BF16.gguf` | vision tower, reference | — | 0.93 GB | `e287342d…6cfd7` |
| `Ternary-Bonsai-2-27B-F16.gguf` | the trained master | 16 | 53.8 GB | `f6f3b2c9…00c180` |

A separate `-gguf-dev` repo carries a group-64 `Q2_0` file (2.25 bpw, 7.6 GB)
marked testing only.

**Choosing a packing (vendor guidance).** The two are a trade, not an ordering.
`PQ2_0` decodes faster on H100, A100 and Blackwell and processes prompts faster
everywhere. `PTQ1_0` decodes faster on Ada-generation cards and the L4, and is
"the pick wherever memory is tightest". The demo downloads `PQ2_0` by default.

## Memory

Machine-independent pieces, for any host's fit math:

- resident weights: 5.54 GiB (`PTQ1_0`) or 6.71 GiB (`PQ2_0`);
- FP16 KV cache: 64 KiB per token (0.25 GiB at 4K, 0.5 GiB at 8K, 2 GiB at 32K,
  6.3 GiB at 100K); `--cache-type-k q4_0 --cache-type-v q4_0` (the demo's
  `BONSAI_KV4=1`) cuts it to about 18 KiB per token, and is a quality axis;
- about 1.2 GiB of activations and overhead (the demo's figure for the 27B);
- about 0.9 GiB more when the vision projector is loaded.

PrismML has not published a Bonsai 2 peak-memory table; the first Bonsai's
ternary `Q2_0` measured 7.8 GiB at 4K with 6.66 GiB of weights, which matches
this arithmetic.

## Runnability

**Stock llama.cpp cannot run these files.** It rejects `PQ2_0` and `PTQ1_0` as
unknown types. It loads the dev repo's `Q2_0` without a warning and produces
garbage, because it has no Hadamard activation runtime. Use the fork:

- prebuilt binaries: [fork releases](https://github.com/PrismML-Eng/llama.cpp/releases).
  As of 2026-09-18 the demo pins **`prism-b10685-7dffb15`**, which ships Linux
  CUDA 12.4 / 12.8 / 13.3, Windows CUDA 12.4 / 13.3, Vulkan, ROCm, macOS and
  Android archives. The newer `prism-b10687` release carries only Windows CUDA
  runtime zips; do not use it as the binary source.
- or build the fork: `cmake -B build -DGGML_CUDA=ON && cmake --build build -j`.
  Blackwell (sm_120) needs CUDA 12.8 or newer
  ([blackwell-rtx5070](../hardware/blackwell-rtx5070.md)); on a host without
  `nvcc`, build inside the CUDA container ([podman-gpu](../stacks/podman-gpu.md)).

Backends with the custom kernels: CUDA and Metal. CPU runs. Apple Silicon also
has the MLX 2-bit package.

## How to run it

Recommended sampling (the base model's `generation_config.json`, also carried in
the GGUF metadata, and the settings behind the published scores):

- thinking: `temperature 1.0, top_p 0.95, top_k 20, min_p 0, presence_penalty 0`;
- non-thinking: `temperature 0.7, top_p 0.80, top_k 20, min_p 0, presence_penalty 1.5`.

A plain system prompt ("You are a helpful assistant") is enough. Thinking is the
bulk of the wait on slow hardware; cap it server-wide with `--reasoning-budget N`
(the demo UI's levels are 512, 2,048, 8,192 and unlimited).

### Direct, with a fork binary (any packing)

```bash
# binary: the release the demo pins
mkdir -p ~/models/prism-llama && cd ~/models/prism-llama
curl -fLO https://github.com/PrismML-Eng/llama.cpp/releases/download/prism-b10685-7dffb15/llama-prism-b10685-7dffb15-bin-linux-cuda-12.8-x64.tar.gz
mkdir -p bin && tar -xzf llama-prism-b10685-7dffb15-bin-linux-cuda-12.8-x64.tar.gz -C bin --strip-components=1

# weights (explicit filename; see the --include gotcha in archive.md)
hf download prism-ml/Ternary-Bonsai-2-27B-gguf Ternary-Bonsai-2-27B-PTQ1_0.gguf \
  --local-dir ~/models/prism-ml/Ternary-Bonsai-2-27B-gguf

LD_LIBRARY_PATH=~/models/prism-llama/bin ~/models/prism-llama/bin/llama-server \
  -m ~/models/prism-ml/Ternary-Bonsai-2-27B-gguf/Ternary-Bonsai-2-27B-PTQ1_0.gguf \
  -ngl 99 -fa on -c 8192 --jinja \
  --temp 1.0 --top-p 0.95 --top-k 20 \
  --reasoning-budget 2048 --host 127.0.0.1 --port 8080
# OpenAI-compatible at http://127.0.0.1:8080/v1 → harness --provider openai-compatible
```

### The demo (downloads `PQ2_0`)

```bash
git clone https://github.com/PrismML-Eng/Bonsai-demo.git && cd Bonsai-demo
BONSAI_OPENWEBUI=0 BONSAI_CODE_INTERPRETER=0 ./setup.sh   # default family is bonsai2
./scripts/start_llama_server.sh --reasoning-budget 2048
```

`setup.ps1` and the `.ps1` launchers do the same on Windows with the Windows CUDA
binary. Image input: add `--mmproj …mmproj-Q8_0.gguf` (demo `VISION.md`).
Speculative decoding: demo `SPECULATIVE.md`; no Bonsai 2 drafter is listed in the
GGUF repo as of 2026-09-18.

## Published results (vendor)

EvalScope + vLLM on H100, thinking mode, 14 benchmarks, identical decoding and
scoring across rows.

| Variant | True bpw | Footprint | Average | vs FP16 |
|---|---:|---:|---:|---:|
| Qwen3.8-27B FP16 | 16.0 | 54 GB | 86.32 | 100% |
| Qwen3.8-27B UD-Q4_K_XL | 5.2 | 17.6 GB | 85.18 | 98.7% |
| Qwen3.8-27B IQ2_XXS | 2.8 | 9.4 GB | 72.59 | 84.1% |
| **Bonsai 2 27B** | **1.72** | **5.9 GB** | **84.78** | **98.2%** |
| Ternary Bonsai 27B (previous, same 14) | — | 5.75 GB | 80.98 | — |

| Category | Benchmarks | FP16 | Bonsai 2 |
|---|---|---:|---:|
| Knowledge and reasoning | MMLU-Redux, MuSR | 85.55 | 79.86 |
| Math | GSM8K, MATH-500, AIME25, AIME26 | 97.06 | 96.57 |
| Coding | HumanEval+, MBPP+, LiveCodeBench | 89.07 | 89.42 |
| Instruction following | IFEval, IFBench | 81.25 | 82.66 |
| Agentic / tool calling | BFCL v3 | 76.74 | 74.92 |
| Vision | MMMU-Pro, OCR Bench v2 | 71.36 | 66.19 |

The categories this repo cares about moved the most since the first Bonsai, each
measured on its own release's table and baseline: instruction following went
from 91% of baseline to slightly above it, and tool calling from 92.5% to 97.6%. The remaining loss sits in MuSR (79.63 to 70.63)
and vision. The agentic row is one benchmark (BFCL v3), which this wiki treats
as [reference only](../benchmarks/bfcl.md).

Vendor throughput, `llama-bench`, batch 1, depth 0, tokens/s:

| Platform | PQ2_0 TG128 | PQ2_0 PP512 | PTQ1_0 TG128 | PTQ1_0 PP512 |
|---|---:|---:|---:|---:|
| RTX 5090 (32 GB) | 129.9 | 3893 | 120.5 | 1805 |
| RTX PRO 6000 Blackwell | 124.8 | 4020 | 117.9 | 1972 |
| H100 (80 GB) | 113.9 | 2830 | 86.9 | 1237 |
| RTX 4090 (24 GB) | 81.2 | 3124 | 91.1 | 1645 |
| L4 (24 GB, 72 W) | 29.8 | 777 | 32.1 | 467 |
| Apple M5 Pro (Metal) | 28.1 | 387 | — | — |

On Blackwell the dense packing costs about 7% of decode and about half of prompt
processing. No 8 GB-class or laptop NVIDIA number is published.

## Questions to answer locally

- Does `PTQ1_0` run fully on an 8 GB GPU at a usable context, and at what tok/s
  on a laptop Blackwell part?
- With thinking at the recommended settings, is a home-agent turn fast enough to
  be usable, or does it need `--reasoning-budget` or `medium` effort, and what
  does that cost in reliability?
- Does the claimed tool-calling retention show up as `pass^3` on the
  home-automation and email-triage sets, against gemma-4-12b's ceiling and
  qwen3.5:4b's reliability?
- Do the first Bonsai's community complaints (reasoning loops, hallucination)
  persist?

Staged test: [Bonsai 2 27B first run](../../lab/experiments/2026-09-18-bonsai-2-27b-first-run/README.md).

## Related

- [Bonsai 27B](bonsai-27b.md), the first generation (keeps the 1-bit build).
- [Gemma-4-12B agentic v2](gemma-4-12b-agentic-fable5.md), the strongest local
  agent so far; [Ornith-1.5-9B](ornith-1.5-9b.md), the other staged challenger.
- [Quantization](../concepts/quantization.md), [llama.cpp](../stacks/llama-cpp.md),
  [podman-gpu](../stacks/podman-gpu.md), [Blackwell RTX 5070](../hardware/blackwell-rtx5070.md),
  [weight archive](../archive.md).
