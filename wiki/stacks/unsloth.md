---
title: Unsloth + Unsloth Studio
tags: [stack, finetuning, studio, diffusiongemma]
updated: 2026-06-14
status: researched
---

# Unsloth + Unsloth Studio

Fast, memory-efficient fine-tuning (2x faster, ~70% less VRAM) and **Unsloth
Studio**, an open-source local web UI for running/training models. The
lowest-friction path to [DiffusionGemma](../models/diffusiongemma.md) here.

## Two reasons it's in the toolbox

1. **Unsloth Studio** runs DiffusionGemma locally with auto-tuned inference
   params via a llama.cpp backend — the easiest way to try it on this machine
   (no source build, no branch wrangling).
2. **Fine-tuning**: 4-bit (bitsandbytes nf4) training that fits in modest VRAM —
   relevant once I want to adapt a small model to a task. (Heavy training still
   wants more than 8 GB; small LoRA jobs are feasible.)

## Install / run Studio

```bash
# Linux / WSL:
curl -fsSL https://unsloth.ai/install.sh | sh
unsloth studio -H 0.0.0.0 -p 8888
# then open http://127.0.0.1:8888, search a model, pick a quant, run.
```

Python/training work belongs in a **venv**, never system python.

## Caveats

- DiffusionGemma support is days-old **beta** — expect rough edges (good blog
  material). Needs the [WSL RAM bump](../concepts/wsl2-memory.md) to reach ~18 GB.
- For Blackwell from-source training paths, mind the
  [CUDA >= 12.8 requirement](../hardware/blackwell-rtx5070.md).

Source: [unsloth.ai/docs](https://unsloth.ai/docs/models/diffusiongemma).

## First tasks
- [ ] Install Studio, run a small GGUF to confirm the UI + backend work.
- [ ] Attempt DiffusionGemma Q4_K_M after raising WSL RAM; capture the run.
