#!/usr/bin/env bash
# verify-stack.sh — read-only readiness check for local LLM work on this machine.
# Safe to run anytime. Prints a summary and warns about the WSL RAM cap.

set -uo pipefail

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
ok()   { printf '  \033[32m[ok]\033[0m   %s\n' "$1"; }
warn() { printf '  \033[33m[warn]\033[0m %s\n' "$1"; }
bad()  { printf '  \033[31m[miss]\033[0m %s\n' "$1"; }

bold "== OS / WSL =="
if grep -qi microsoft /proc/version 2>/dev/null; then
  ok "WSL2: $(grep -o 'Ubuntu[^"]*' /etc/os-release | head -1)"
else
  warn "Not detected as WSL — some notes in this repo assume WSL2."
fi

bold "== Memory (what WSL sees) =="
mem_total_gb=$(awk '/MemTotal/ {printf "%.0f", $2/1024/1024}' /proc/meminfo)
free -h | sed 's/^/  /'
if [ "${mem_total_gb:-0}" -lt 18 ]; then
  warn "WSL sees ~${mem_total_gb}GB. Models needing >~12GB (e.g. DiffusionGemma ~18GB) may not fit."
  warn "Raise it: see env/wslconfig.template, then 'wsl --shutdown' from Windows."
else
  ok "RAM headroom looks fine (~${mem_total_gb}GB)."
fi

bold "== CPU =="
printf '  cores: %s\n' "$(nproc)"
lscpu | awk -F: '/Model name/ {gsub(/^ +/,"",$2); print "  "$2; exit}'

bold "== GPU / NVIDIA =="
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,memory.total,memory.used,driver_version --format=csv,noheader \
    | sed 's/^/  /'
  ok "nvidia-smi present (GPU visible in WSL)."
else
  bad "nvidia-smi not found — GPU offload unavailable."
fi

bold "== CUDA toolkit (for source builds only) =="
if command -v nvcc >/dev/null 2>&1; then
  ok "nvcc: $(nvcc --version | awk '/release/ {print $5,$6}')"
else
  warn "nvcc not installed. Ollama needs none; building llama.cpp/vLLM from source does (CUDA >= 12.8)."
fi

bold "== Ollama (daily driver) =="
if command -v ollama >/dev/null 2>&1; then
  ok "ollama $(ollama --version 2>/dev/null | awk '{print $NF}')"
  if ollama list >/dev/null 2>&1; then
    ollama list | sed 's/^/  /'
  else
    warn "ollama daemon not responding (start it, or run 'ollama serve')."
  fi
else
  bad "ollama not found."
fi

bold "== Python / torch =="
python3 --version 2>/dev/null | sed 's/^/  /'
if python3 -c 'import torch' 2>/dev/null; then
  python3 -c 'import torch; print("  torch", torch.__version__, "| cuda", torch.cuda.is_available(), torch.version.cuda)'
else
  warn "no torch in system python (expected — use a venv for Unsloth/vLLM)."
fi

bold "== git / gh =="
git --version | sed 's/^/  /'
if command -v gh >/dev/null 2>&1; then
  gh --version | head -1 | sed 's/^/  /'
  gh auth status 2>&1 | grep -E 'Logged in|Active account' | sed 's/^/  /' || true
else
  warn "gh CLI not found."
fi

bold "== Disk (cwd) =="
df -h . | tail -1 | sed 's/^/  /'

echo
bold "Done. Re-run after changing .wslconfig or installing a stack."
