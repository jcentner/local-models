---
title: Torrent — host profile
tags: [hardware, host]
updated: 2026-08-13
status: generated
---

# Torrent (host profile)

Generated 2026-08-13 by `scripts/host-profile.sh` (live probes). The **Verified
specs** table is machine-generated; the prose sections below are filled by hand.
Re-run with `-w -f` to refresh the table. Per-host facts only — portable rules
(quant math, WSL cap) live under [concepts/](../concepts/).

## Verified specs (2026-08-13)

| Component | Value |
|---|---|
| Hostname | Torrent |
| OS | Ubuntu 26.04 LTS on WSL2 |
| WSL2 | yes (WSL2) |
| RAM (visible) | 31 GB — WSL cap; see [concepts/wsl2-memory.md](../concepts/wsl2-memory.md) |
| CPU | Intel(R) Core(TM) Ultra 7 270K Plus (24 logical cores) |
| GPU | NVIDIA GeForce RTX 3070 Ti, 8192 MiB, 610.88 |
| CUDA runtime | 13.3 [Deprecated; will be removed in CUDA 14.0. Use CUDA UMD Version instead] |
| CUDA toolkit (nvcc) | not installed (Ollama needs none; source builds want >= 12.8) |
| Ollama | not installed |
| Python | 3.14.4 |
| Disk (repo fs) | 946G free |

## What fits (rule of thumb)

Same **8 GB class** as the [ProArt P16](proart-p16.md), so its fit math carries
over: ~12B dense at Q3_K_M full-GPU (gemma-4-12b Q3_K_M = 7.78 GB incl. 16K f16
KV on the P16), 4B-class at Q8 with headroom, 2-3B (MiniCPM5, LFM2.5-2.6B)
trivial. Desktop Windows drives the display from this GPU — check *free* VRAM
with `nvidia-smi` before assuming the full 8150 MiB (the P16 showed ~6.8 GB
usable; measure here). 31 GB visible RAM gives comfortable CPU-offload room.

## Known constraints / gotchas

- **No serving stack installed yet** (2026-08-13): no Ollama, no llama.cpp/SGLang
  containers, no torch venv. First model run on this box is also the bring-up —
  follow [stacks/podman-gpu.md](../stacks/podman-gpu.md) for the container path.
- **Ampere (sm_86), not Blackwell** — none of the P16's CUDA ≥ 12.8 wheel
  constraints apply; any recent torch/CUDA build works. No NPU on this box.
- No CUDA toolkit (`nvcc`) on the host — from-source builds go through the CUDA
  container, same as the other hosts.
- WSL2 RAM cap applies (31 GB visible); `.wslconfig` template in
  [env/](../../env/README.md) if a bigger cap is ever needed.

## Related
- [concepts/quantization.md](../concepts/quantization.md) · [concepts/wsl2-memory.md](../concepts/wsl2-memory.md)
- [stacks/podman-gpu.md](../stacks/podman-gpu.md) — portable GPU-container setup
