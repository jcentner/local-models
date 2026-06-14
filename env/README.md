# env/ — environment setup & pinned facts

Setup notes and version pins for this machine. Verified facts live in
[../wiki/hardware/proart-p16.md](../wiki/hardware/proart-p16.md); this folder is
for the actionable setup bits.

## Files

- [`wslconfig.template`](wslconfig.template) — raise WSL2's RAM cap (default
  ~15 GB) so bigger models fit. Apply on the Windows side; see the file header.

## Baseline (verified 2026-06-14)

| Thing | Version / value |
|---|---|
| OS | Ubuntu 24.04.4 LTS (WSL2, kernel 6.6.87.2-microsoft-standard-WSL2) |
| Host | Windows 11, 32 GB RAM |
| GPU | NVIDIA RTX 5070 Laptop, 8 GB, driver 595.97 (CUDA 13.2 runtime in WSL) |
| CPU | AMD Ryzen AI 9 HX 370 (24 logical cores in WSL) |
| CUDA toolkit | not installed (`nvcc` absent) |
| Ollama | 0.20.2 |
| Python | system 3.12.3 (no torch — use a venv) |
| git / gh | 2.43.0 / 2.45.0 (gh authed as jcentner) |

## Common setup tasks

```bash
# Raise WSL RAM (see wslconfig.template header) — do this before big models.

# Python venv for Unsloth / vLLM / HF work (never use system python):
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip

# CUDA toolkit (only needed to BUILD llama.cpp/vllm from source for Blackwell;
# Ollama bundles its own runtime and needs none). Prefer CUDA >= 12.8 for sm_120.
# Install via NVIDIA's WSL-Ubuntu repo or run inside an NVIDIA CUDA container.
```

See per-stack install steps in [../wiki/stacks/](../wiki/stacks/).
