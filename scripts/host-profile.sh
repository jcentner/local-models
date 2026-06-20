#!/usr/bin/env bash
# host-profile.sh — generate a wiki/hardware/<host>.md skeleton from live probes.
# Read-only w.r.t. the system (same probes as verify-stack.sh). Prints the page to
# stdout by default; pass -w to write it to wiki/hardware/<slug>.md (won't clobber
# an existing file unless -f is given). Fill the prose sections by hand afterward.
#
# Usage:
#   bash scripts/host-profile.sh            # print to stdout
#   bash scripts/host-profile.sh -w         # write wiki/hardware/<slug>.md
#   bash scripts/host-profile.sh -w -f      # overwrite the verified table on re-run

set -uo pipefail

WRITE=0
FORCE=0
while [ $# -gt 0 ]; do
  case "$1" in
    -w|--write) WRITE=1 ;;
    -f|--force) FORCE=1 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATE="$(date +%F)"
HOST="$(hostname 2>/dev/null || echo unknown-host)"
SLUG="$(printf '%s' "$HOST" | tr '[:upper:] ' '[:lower:]-' | tr -cd 'a-z0-9-')"

# --- probes (best-effort; absent tools yield "n/a") -------------------------
if grep -qi microsoft /proc/version 2>/dev/null; then
  WSL="yes (WSL2)"
  OS="$(grep -o 'Ubuntu[^"]*' /etc/os-release 2>/dev/null | head -1) on WSL2"
else
  WSL="no"
  OS="$(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME")"
fi
[ -n "${OS:-}" ] || OS="n/a"

MEM_GB="$(awk '/MemTotal/ {printf "%.0f", $2/1024/1024}' /proc/meminfo 2>/dev/null)"
[ -n "${MEM_GB:-}" ] || MEM_GB="n/a"
CORES="$(nproc 2>/dev/null || echo n/a)"
CPU="$(lscpu 2>/dev/null | awk -F: '/Model name/ {gsub(/^ +/,"",$2); print $2; exit}')"
[ -n "${CPU:-}" ] || CPU="n/a"

if command -v nvidia-smi >/dev/null 2>&1; then
  GPU="$(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null | head -1 | sed 's/ *, */, /g')"
  CUDA_RT="$(nvidia-smi --query 2>/dev/null | awk -F': ' '/CUDA Version/ {print $2; exit}')"
  [ -n "${CUDA_RT:-}" ] || CUDA_RT="$(nvidia-smi 2>/dev/null | sed -n 's/.*CUDA Version: \([0-9.]*\).*/\1/p' | head -1)"
else
  GPU="none (no nvidia-smi)"
  CUDA_RT=""
fi
[ -n "${GPU:-}" ] || GPU="n/a"
[ -n "${CUDA_RT:-}" ] || CUDA_RT="n/a"

if command -v nvcc >/dev/null 2>&1; then
  NVCC="$(nvcc --version 2>/dev/null | awk '/release/ {print $5,$6}')"
else
  NVCC="not installed (Ollama needs none; source builds want >= 12.8)"
fi

if command -v ollama >/dev/null 2>&1; then
  OLLAMA="$(ollama --version 2>/dev/null | awk '{print $NF}')"
else
  OLLAMA="not installed"
fi
[ -n "${OLLAMA:-}" ] || OLLAMA="n/a"

PY="$(python3 --version 2>/dev/null | awk '{print $2}')"
[ -n "${PY:-}" ] || PY="n/a"
DISK="$(df -h "$REPO_ROOT" 2>/dev/null | tail -1 | awk '{print $4" free"}')"
[ -n "${DISK:-}" ] || DISK="n/a"

# --- emit markdown ----------------------------------------------------------
emit() {
cat <<EOF
---
title: ${HOST} — host profile
tags: [hardware, host]
updated: ${DATE}
status: generated
---

# ${HOST} (host profile)

Generated ${DATE} by \`scripts/host-profile.sh\` (live probes). The **Verified
specs** table is machine-generated; the prose sections below are filled by hand.
Re-run with \`-w -f\` to refresh the table. Per-host facts only — portable rules
(quant math, WSL cap) live under [concepts/](../concepts/).

## Verified specs (${DATE})

| Component | Value |
|---|---|
| Hostname | ${HOST} |
| OS | ${OS} |
| WSL2 | ${WSL} |
| RAM (visible) | ${MEM_GB} GB$( [ "$WSL" != "no" ] && echo " — WSL cap; see [concepts/wsl2-memory.md](../concepts/wsl2-memory.md)") |
| CPU | ${CPU} (${CORES} logical cores) |
| GPU | ${GPU} |
| CUDA runtime | ${CUDA_RT} |
| CUDA toolkit (nvcc) | ${NVCC} |
| Ollama | ${OLLAMA} |
| Python | ${PY} |
| Disk (repo fs) | ${DISK} |

## What fits (rule of thumb)

_TODO: derive the VRAM budget from the GPU above (KV cache eats into it) and fill
from [concepts/quantization.md](../concepts/quantization.md) + experiments._

## Known constraints / gotchas

_TODO: driver/CUDA/toolchain quirks, WSL RAM cap, NPU visibility, etc._

## Related
- [concepts/quantization.md](../concepts/quantization.md) · [concepts/wsl2-memory.md](../concepts/wsl2-memory.md)
- [stacks/podman-gpu.md](../stacks/podman-gpu.md) — portable GPU-container setup
EOF
}

if [ "$WRITE" -eq 1 ]; then
  OUT="$REPO_ROOT/wiki/hardware/${SLUG}.md"
  if [ -e "$OUT" ] && [ "$FORCE" -ne 1 ]; then
    echo "refusing to overwrite existing $OUT (use -f)" >&2
    exit 1
  fi
  emit > "$OUT"
  echo "wrote $OUT" >&2
else
  emit
fi
