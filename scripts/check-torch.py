#!/usr/bin/env python3
"""Confirm PyTorch is installed and actually works on this machine's GPU.

Run with whichever interpreter you care about — the system python or a venv:

    python3 scripts/check-torch.py
    ~/.venvs/pylate/bin/python scripts/check-torch.py

Exit codes: 0 = torch present and (if a GPU is expected) a real CUDA op ran;
1 = torch not installed; 2 = torch installed but the GPU op failed (usually a
CUDA-wheel / arch mismatch — on this box, Blackwell sm_120 needs a CUDA>=12.8
wheel). See wiki/hardware/proart-p16.md and wiki/hardware/blackwell-rtx5070.md.
"""
import importlib.util
import sys

if importlib.util.find_spec("torch") is None:
    print(f"torch: NOT installed in {sys.executable}")
    print("  -> create a venv and install a CUDA>=12.8 wheel, e.g.:")
    print("     python3 -m venv ~/.venvs/pylate && source ~/.venvs/pylate/bin/activate")
    print("     pip install --index-url https://download.pytorch.org/whl/cu128 torch")
    sys.exit(1)

import torch

print(f"python     : {sys.executable}")
print(f"torch      : {torch.__version__}")
print(f"CUDA build : {torch.version.cuda}")
print(f"CUDA avail : {torch.cuda.is_available()}")

if not torch.cuda.is_available():
    print("note       : no CUDA device visible — CPU-only torch (fine for small "
          "aide models, but no GPU accel).")
    sys.exit(0)

name = torch.cuda.get_device_name(0)
cap = torch.cuda.get_device_capability(0)
print(f"device     : {name}")
print(f"capability : sm_{cap[0]}{cap[1]}" + (" (Blackwell)" if cap == (12, 0) else ""))

# Prove kernels actually run on this arch — an import-clean wheel can still fail
# the first real op if it was built for the wrong compute capability.
try:
    x = torch.randn(512, 512, device="cuda")
    y = (x @ x).sum().item()
    torch.cuda.synchronize()
    print(f"gpu matmul : OK (checksum {y:.1f})")
except Exception as e:  # noqa: BLE001 - we want the raw failure surfaced
    print(f"gpu matmul : FAILED -> {type(e).__name__}: {e}")
    print("  -> likely a CUDA-arch/wheel mismatch; reinstall the cu128 wheel.")
    sys.exit(2)

print("result     : torch is installed and working on the GPU.")
