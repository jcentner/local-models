---
title: SGLang
tags: [stack, serving, thinking-models, tool-calling]
updated: 2026-06-20
status: planned
---

# SGLang — controlled-thinking + native tool-calling server

[SGLang](https://github.com/sgl-project/sglang) is LMSYS's high-performance LLM
serving engine (Apache-2.0, RadixAttention prefix caching, continuous batching,
OpenAI-compatible API). For this repo its value is **not** throughput — it's that
it gives the two controls [Ollama](ollama.md) can't:

1. **Reasoning control / separation** — a `--reasoning-parser` splits chain-of-
   thought into a separate `reasoning_content` field, and hybrid models'
   `enable_thinking` flag is honored through the chat template. This is the fix
   for the recurring "[uncontrollable `<think>` over Ollama](../models/minicpm5-1b.md)"
   problem that has confounded our [decision-reasoning](../benchmarks/decision-reasoning.md)
   and tool-use runs.
2. **Native function-calling parsers** — a `--tool-call-parser` converts a
   model's native tool-call syntax (XML, pythonic, etc.) into OpenAI
   `tool_calls`, including a **`minicpm5`** parser that Ollama's tool-blind
   template can't provide.

It speaks the OpenAI API, so our harness reaches it via
`--provider openai-compatible` with **zero client changes** — see
[harness README](../../lab/benchmarks/harness/README.md). This is the concrete
enabler for the **serving-aware-per-model** plan: Ollama stays the daily driver;
thinking/tool models route here.

Docs: [install](https://docs.sglang.io/docs/get-started/install.md) ·
[OpenAI API](https://docs.sglang.io/docs/basic_usage/openai_api.md) ·
[tool parser](https://docs.sglang.io/docs/advanced_features/tool_parser.md) ·
[reasoning parser](https://docs.sglang.io/docs/advanced_features/separate_reasoning.md) ·
[server args](https://docs.sglang.io/docs/advanced_features/server_arguments.md) ·
[embeddings](https://docs.sglang.io/docs/supported-models/embedding_models.md).

## Fit on this machine

This box: [ProArt P16](../hardware/proart-p16.md), RTX 5070 Laptop (Blackwell
**sm_120**, 8 GB), WSL2, no `nvcc` toolkit, Podman (not Docker).

- **Blackwell is supported.** SGLang ships CUDA-13 wheels/images by default and
  lists Blackwell (5090) under supported hardware; our driver exposes a CUDA 13.2
  runtime, so the default build matches — no `-cu12` gymnastics needed (vLLM has
  you pick the matching cu12x/cu13 wheel — doable, and a `cu128` torch wheel is
  confirmed working on sm_120 here).
- **8 GB is workable for small models.** A 1B like [MiniCPM5-1B](../models/minicpm5-1b.md)
  is ~2.2 GB in BF16 and fits with room for KV cache. The catch is SGLang
  **pre-allocates a static KV pool** (`--mem-fraction-static`, default ~0.9);
  on a shared WSL GPU lower it (e.g. `0.7`) and cap `--context-length` so it
  doesn't grab all 8 GB. Throughput-oriented serving of bigger models is still a
  stretch here — that's [vLLM](vllm.md)'s lane post-upgrade.
- **Min Python 3.10.** Install in a venv outside the repo, never system python.

## Verified on this box (2026-06-20) — pip is a dead end, the container works

Stood SGLang up for [MiniCPM5-1B](../models/minicpm5-1b.md). Findings:

- **Stock `pip install sglang` (0.5.13) CANNOT run here** — it **JIT-compiles
  kernels at runtime** and this box has the CUDA *runtime* (driver 13.2) but **no
  `gcc` and no `nvcc` toolkit**. Two distinct failures: FlashInfer's KV-index
  **Triton** kernel needs a **C compiler** ("Failed to find C compiler"); the
  fused-RoPE **`tvm_ffi`** kernel needs the **CUDA toolkit** ("Could not find CUDA
  installation / `CUDA_HOME`"). `--attention-backend triton --sampling-backend
  pytorch --disable-cuda-graph` clears the first but not the second. **Installing
  the toolchain (`build-essential` + a matching CUDA toolkit) is the alternative,
  but the docs steer toolchain-less boxes to the container instead.**
- **The official container is the working path.** `lmsysorg/sglang:latest`
  (CUDA-13) bundles gcc + toolkit, so the JIT kernels compile and **cuda-graph
  capture succeeds inside the container**. The default `cu130` torch runs on
  Blackwell **sm_120** — no cu12 dance.
- **Rootless Podman + CDI works** (the repo runs Podman, not Docker). One-time GPU
  setup: install `nvidia-container-toolkit`, then `sudo nvidia-ctk cdi generate
  --output=/etc/cdi/nvidia.yaml` (auto-detects WSL); verify with
  `podman run --rm --device nvidia.com/gpu=all --security-opt=label=disable <img>
  nvidia-smi -L`. The RTX 5070 shows up inside the container.
- **`--tool-call-parser minicpm5` is BROKEN for MiniCPM5-1B in 0.5.13.** It's
  vendor-recommended and auto-detected, but it **swallows the model's `<function
  name=...>` XML and emits no `tool_calls`** (verified: content empty,
  `tool_calls: null`). **Workaround that works:** run the server **without**
  `--tool-call-parser` (XML stays in `content`) and let the harness's
  `parse_xml_tool_calls()` fallback convert it -> MiniCPM5 then scored **2/5
  email-triage, 7/12 home-automation** (native). Revisit a newer build for a
  native parser. (Reasoning control is fine either way:
  `chat_template_kwargs={"enable_thinking":false}` reliably suppresses the CoT.)
- **8 GB fit:** 1B BF16 ~2.16 GB; `--mem-fraction-static 0.7 --context-length
  16384` leaves headroom. **WSL RAM** is a non-issue at 1B ([wsl2-memory](../concepts/wsl2-memory.md)).

## Install — the container route (recommended here)

```bash
# One-time GPU-in-Podman setup (toolkit + CDI) is shared across stacks -> see
# stacks/podman-gpu.md. Then just pull the SGLang image:
podman pull docker.io/lmsysorg/sglang:latest

# Serve MiniCPM5-1B (GPU via CDI, reuse the HF model cache, OpenAI API on :30000)
podman run -d --name sglang-minicpm5 \
  --device nvidia.com/gpu=all --security-opt=label=disable --ipc=host \
  -p 30000:30000 -v ~/.cache/huggingface:/root/.cache/huggingface \
  docker.io/lmsysorg/sglang:latest \
  python3 -m sglang.launch_server --model-path openbmb/MiniCPM5-1B \
    --host 0.0.0.0 --port 30000 --mem-fraction-static 0.7 --context-length 16384 \
    --reasoning-parser deepseek-r1
    # NB: OMIT --tool-call-parser minicpm5 (broken in 0.5.13 - swallows the XML);
    # the harness parse_xml_tool_calls() fallback reads the raw <function> XML instead.
```

**pip/uv install is documented but does NOT work on this toolchain-less box** (see
findings above); use it only on a machine with `gcc` + a CUDA toolkit:
`uv pip install --prerelease=allow "sglang>=0.5.12"` (the `srt` extra is gone in
0.5.13; `flash-attn-4` is a prerelease dep, hence `--prerelease=allow`).


## Launch patterns

```bash
# Plain OpenAI-compatible server (chat) on :30000 -> /v1
python -m sglang.launch_server --model-path openbmb/MiniCPM5-1B \
  --port 30000 --mem-fraction-static 0.7 --context-length 16384

# Native tool-calling (MiniCPM5 emits XML -> OpenAI tool_calls)
python -m sglang.launch_server --model-path openbmb/MiniCPM5-1B \
  --port 30000 --tool-call-parser minicpm5    # or: --tool-call-parser auto

# Reasoning separation (CoT -> message.reasoning_content) for a Qwen3-class model
python -m sglang.launch_server --model-path Qwen/Qwen3-... \
  --port 30000 --reasoning-parser qwen3
```

- **Tool calls** arrive as standard `choices[].message.tool_calls` — exactly the
  shape our harness's `native` protocol already parses
  ([client.py](../../lab/benchmarks/harness/client.py)).
- **Reasoning** is returned separately as `message.reasoning_content`; toggle per
  request with `extra_body={"separate_reasoning": true|false}`
  ([reasoning parser docs](https://docs.sglang.io/docs/advanced_features/separate_reasoning.md)).
- **enable_thinking** (suppress CoT entirely on a hybrid model) is a *chat-
  template* flag, passed through `chat_template_kwargs` in the request body.
  Confirm the exact field name on first run — this is the lever Ollama lacked.

## Reasoning / tool parser support (selected, from the docs tables)

| Model family | `--reasoning-parser` | `--tool-call-parser` |
|---|---|---|
| MiniCPM5 | (hybrid `<think>` via `enable_thinking`; no named parser yet) | `minicpm5` / `auto` (vendor-confirmed) |
| Qwen3 / Qwen3-Thinking | `qwen3` (supports `enable_thinking`) | `qwen` |
| DeepSeek-R1 family | `deepseek-r1` | — |
| DeepSeek-V3.1/3.2 | `deepseek-v3` (`thinking` param) | `deepseekv31` / `deepseekv32` |
| GPT-OSS | `gpt-oss` | `gpt-oss` |
| Llama 3/4 | — | `llama3` / `llama4` / `pythonic` |

Full lists: [tool parser](https://docs.sglang.io/docs/advanced_features/tool_parser.md),
[reasoning parser](https://docs.sglang.io/docs/advanced_features/separate_reasoning.md).

## Embeddings (relevant to the aide-model track)

SGLang also serves embedding models with `--is-embedding`, exposing
`/v1/embeddings` (Qwen3-Embedding, BGE, GTE-Qwen2, E5, CLIP, plus Matryoshka
truncation). A candidate backend for the planned embeddings aide work, though
[Ollama](ollama.md) already covers basic local embeddings more cheaply. See the
[embedding-models doc](https://docs.sglang.io/docs/supported-models/embedding_models.md).

## Verdict for now

Stand it up **for a specific model that Ollama can't serve faithfully** — first
target [MiniCPM5-1B](../models/minicpm5-1b.md), to unblock its stuck tool-use and
reasoning verdicts (see the
[experiment](../../lab/experiments/2026-06-20-minicpm5-sglang-controlled/README.md)).
Not a general replacement for Ollama; a second, controlled runner for
thinking/tool models. Compare with [vLLM](vllm.md): vLLM is the throughput play
(stretch on 8 GB); SGLang is the **control** play (parsers + enable_thinking),
which is what we actually need now.
