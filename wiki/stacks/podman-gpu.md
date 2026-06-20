---
title: GPU containers (rootless Podman + NVIDIA CDI)
tags: [stack, infra, podman, cuda, containers, portable]
updated: 2026-06-20
status: verified
---

# GPU containers — rootless Podman + NVIDIA CDI

The **shared foundation** for running GPU LLM servers here. Both serving stacks —
[SGLang](sglang.md) and [llama.cpp](llama-cpp.md) — run as **official prebuilt
CUDA images** under rootless Podman, so **no host CUDA toolkit / `nvcc` is needed**
(this box has none). This page is the one-time, machine-independent setup; the
per-stack launch commands live on their own pages.

This is the page to follow to **reproduce the setup on a new machine**.

## Why containers (not pip / from-source)

- The host has the NVIDIA **driver/runtime** but **no CUDA toolkit or compiler**, so
  pip-SGLang (JIT kernels) and from-source llama.cpp both fail. The CUDA images
  bundle the toolchain. (See [SGLang findings](sglang.md), [Blackwell gotcha](../hardware/blackwell-rtx5070.md).)
- One GPU-access mechanism (**CDI**) works for every image, rootless.

## Verified environment (2026-06-20, this box)

| Component | Version / value |
|---|---|
| OS | WSL2 Ubuntu 24.04 on Win11 |
| GPU | NVIDIA RTX 5070 Laptop (Blackwell **sm_120**, 8 GB) |
| Podman | **4.9.3** (rootless; CDI `--device` needs >= 4.1) |
| NVIDIA Container Toolkit | **1.19.1** (`nvidia-ctk`) |
| CDI spec | `/etc/cdi/nvidia.yaml` (also `/var/run/cdi/`), device `nvidia.com/gpu=all` |
| Podman storage | `overlay`, rootless at `~/.local/share/containers/storage` |

## One-time setup (per machine)

```bash
# 1. Podman (rootless) + the NVIDIA Container Toolkit (from NVIDIA's apt repo).
sudo apt-get install -y podman nvidia-container-toolkit
```

> **Rootless Podman on WSL2 needs more than `apt install`** (subordinate UID/GID
> maps, a `shared` `/` mount, optionally a Docker-compat socket). Bootstrap it with
> [github.com/jcentner/podman-wsl-setup](https://github.com/jcentner/podman-wsl-setup)
> (`setup-rootless-podman.sh`) — base Podman only, no GPU; the CUDA/CDI layer below
> is ours.

```bash
# 2. Generate the CDI spec (auto-detects WSL). Toolkit >= 1.18 also auto-refreshes
#    it via the nvidia-cdi-refresh systemd service on driver/toolkit changes.
sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml

# 3. Verify the GPU is exposed as a CDI device, then inside a container.
nvidia-ctk cdi list            # -> nvidia.com/gpu=all
podman run --rm --device nvidia.com/gpu=all --security-opt=label=disable \
  docker.io/library/python:3.12-slim nvidia-smi -L   # -> the GPU UUID
```

Prereq: an NVIDIA driver on the host (WSL: the Windows driver provides the WSL
runtime; no separate Linux driver install). No CUDA toolkit required.

## The shared run pattern

Every GPU container here uses the same flags:

```bash
podman run -d --name <svc> \
  --device nvidia.com/gpu=all --security-opt=label=disable \  # GPU via CDI
  --ipc=host \                                                 # shared-mem for the runtime
  -p <PORT>:<PORT> \                                           # OpenAI API
  -v ~/.cache/huggingface:/root/.cache/huggingface \           # reuse one HF model cache
  <image> <server-args...>
```

- `--security-opt=label=disable` is required for the rootless bind-mount + device.
- Mounting `~/.cache/huggingface` means **both stacks share one model cache** (no
  re-downloads when switching runners).
- `nvidia-smi` / `podman stats` while a server is loaded give VRAM / RAM use.

## The two servers (pick per model)

| | [SGLang](sglang.md) | [llama.cpp](llama-cpp.md) |
|---|---|---|
| Image | `docker.io/lmsysorg/sglang:latest` | `ghcr.io/ggml-org/llama.cpp:server-cuda` |
| Weights | HF-format (safetensors) | **GGUF** |
| Best for | controlled thinking (`enable_thinking`), native reasoning/tool parsers (e.g. `minicpm5`) | fine 8 GB control: KV-quant (`-ctk/-ctv q4_0`), partial offload (`-ngl`), `--jinja` native tool-calls, speculative decoding |
| Auto-download | `--model-path <hf-repo>` | `-hf <user>/<repo>:<QUANT>` |
| Default port | 30000 | 18080 (we set it) |
| KV/VRAM knob | `--mem-fraction-static`, `--context-length` | `-ngl`, `-ctk/-ctv`, `-c`, `-fit off` |

Both expose an **OpenAI-compatible API** the [benchmark harness](../../lab/benchmarks/README.md)
reaches via `--provider openai-compatible --base-url http://127.0.0.1:<port>/v1`.

## Portability — what's machine-specific (keep off this page)

These belong to the [hardware page](../hardware/proart-p16.md) / per-experiment
notes, not here, so this page stays true on any box:

- **Free VRAM** (here only ~6.8 GB of 8 is free) → drives quant, `-ngl`,
  `--mem-fraction-static`, and context sizing.
- The Blackwell **sm_120 → CUDA >= 12.8** constraint for from-source builds
  ([details](../hardware/blackwell-rtx5070.md)); the CUDA images already satisfy it.
- [WSL RAM cap](../concepts/wsl2-memory.md) for CPU-offloaded layers.

## Related
- [stacks/sglang.md](sglang.md) · [stacks/llama-cpp.md](llama-cpp.md) · [stacks/ollama.md](ollama.md) (the non-container daily driver)
- [hardware/proart-p16.md](../hardware/proart-p16.md) · [hardware/blackwell-rtx5070.md](../hardware/blackwell-rtx5070.md) · [concepts/wsl2-memory.md](../concepts/wsl2-memory.md)
- First container benchmark: [gemma-4-12B v2 quant sweep](../../lab/experiments/2026-06-20-gemma-4-12b-v2-quant-config-sweep/README.md)
