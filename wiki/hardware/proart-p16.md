---
title: ASUS ProArt P16 — this machine
tags: [hardware, wsl2]
updated: 2026-06-14
status: verified
---

# ASUS ProArt P16 (this machine)

Verified 2026-06-14 via `scripts/verify-stack.sh` / direct terminal. The binding
constraint for local LLMs here is **8 GB of VRAM**, then the **WSL RAM cap**.

## Verified specs

| Component | Value | Notes |
|---|---|---|
| OS | Ubuntu 24.04.4 LTS on **WSL2** | kernel 6.6.87.2-microsoft-standard-WSL2; host = Windows 11 |
| Host RAM | 32 GB | but WSL only sees ~15 GB by default — see [concepts/wsl2-memory.md](../concepts/wsl2-memory.md) |
| GPU | NVIDIA **RTX 5070 Laptop**, 8 GB (8151 MiB) | driver 595.97, CUDA 13.2 runtime in WSL; [details](blackwell-rtx5070.md) |
| CPU | **AMD Ryzen AI 9 HX 370** w/ Radeon 890M | 24 logical cores visible to WSL |
| NPU | XDNA 2 (~50 TOPS) | not usable from WSL2 — [details](xdna2-npu.md) |
| CUDA toolkit | not installed (`nvcc` absent) | Ollama needs none; source builds do |
| Ollama | 0.20.2 | models: `qwen3.5:9b-q4_K_M` (6.6 GB), `qwen3.5:4b` (3.4 GB) |
| Python | 3.12.3; **no system torch** | torch lives in venvs — see below |
| torch venv | `~/.venvs/pylate`: **torch 2.11.0+cu128**, pylate 1.6.0 (verified 2026-06-20) | GPU op confirmed on sm_120; check with [scripts/check-torch.py](../../scripts/check-torch.py) |
| Disk | ~920 GB free | WSL ext4 vhdx |

## What fits (rule of thumb)

- **Fully on GPU (fast):** ~7–9B models at 4-bit (Q4_K_M). The installed
  `qwen3.5:9b-q4_K_M` at 6.6 GB fits in 8 GB with room for KV cache.
- **Hybrid GPU+CPU (slower):** ~14–30B-class and MoE models via partial offload,
  bounded by WSL RAM. Needs the [WSL RAM bump](../concepts/wsl2-memory.md).
- **Won't fit comfortably:** dense >~13B at >4-bit, or anything whose quant file
  exceeds available RAM+VRAM.

VRAM math and quant trade-offs: [concepts/quantization.md](../concepts/quantization.md).

## Known constraints / gotchas

- **WSL RAM cap (~15 GB).** Biggest surprise. DiffusionGemma needs ~18 GB ->
  raise via [env/wslconfig.template](../../env/wslconfig.template).
- **Blackwell needs CUDA >= 12.8** for from-source builds and torch wheels
  (sm_120). Driver supports 13.2, so this is only about toolkit/wheel selection.
  **Confirmed working:** the `cu128` torch wheel (2.11.0) runs a real GPU op on
  sm_120 in `~/.venvs/pylate` (verify any interpreter with
  [scripts/check-torch.py](../../scripts/check-torch.py)).
- **NPU is effectively Windows-only** for LLM work today.
- Memory bandwidth (~384 GB/s on this GPU) caps token/s more than compute does.

## Upgrade notes

User plans a hardware upgrade later. When VRAM grows past ~16 GB, vLLM and
larger dense models at higher precision become practical; revisit
[stacks/vllm.md](../stacks/vllm.md).
