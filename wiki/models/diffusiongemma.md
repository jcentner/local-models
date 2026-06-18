---
title: DiffusionGemma (26B-A4B)
tags: [model, diffusion, moe, multimodal, first-target]
updated: 2026-06-14
status: to-try
---

# DiffusionGemma (26B-A4B)

The first model I want to run here. A **diffusion / block-autoregressive** text +
vision model on the Gemma 4 MoE architecture: **26B total, 4B active**. Instead of
left-to-right decoding, it refines a "canvas" of tokens in parallel (like image
diffusion, but for text), so it can emit many tokens in fewer forward passes.

Source: [unsloth.ai/docs/models/diffusiongemma](https://unsloth.ai/docs/models/diffusiongemma).

## Can it run here? Yes — but not on stock Ollama

- **Ollama: no.** It needs a diffusion sampler that stock Ollama / llama.cpp don't
  have. ([Why Ollama can't](../stacks/ollama.md).)
- **Memory:** Q4_K_M is ~16 GB to download and needs **~18 GB total** to run. The
  default [WSL cap of ~15 GB](../concepts/wsl2-memory.md) is too small —
  **raise WSL RAM first** ([template](../../env/wslconfig.template)). With 8 GB
  VRAM + ~24 GB WSL RAM it runs as **CPU + partial-GPU** (modest speed; diffusion's
  parallel decode helps).

## Two ways to run it

### A. Unsloth Studio (easiest) — recommended first
Auto-tuned params, llama.cpp backend, web UI. See [stacks/unsloth.md](../stacks/unsloth.md).

```bash
curl -fsSL https://unsloth.ai/install.sh | sh
unsloth studio -H 0.0.0.0 -p 8888        # search "DiffusionGemma", pick Q4_K_M
```

### B. llama.cpp diffusion branch (more learning)
Build the PR that adds `llama-diffusion-cli`, then run with a live denoising view.
Needs the [CUDA toolkit](../hardware/blackwell-rtx5070.md). See
[stacks/llama-cpp.md](../stacks/llama-cpp.md).

```bash
# in a CUDA-toolkit-enabled llama.cpp checkout on the diffusion PR branch:
hf download unsloth/diffusiongemma-26B-A4B-it-GGUF --include "*Q4_K_M*" \
  --local-dir models/diffusiongemma
./build/bin/llama-diffusion-cli \
  -m models/diffusiongemma/diffusiongemma-26B-A4B-it-Q4_K_M.gguf \
  -ngl 99 -cnv -n 2048 --diffusion-visual
```

`-ngl` = layers to GPU (lower it if VRAM overflows), `-cnv` = chat,
`--diffusion-visual` = watch the canvas denoise (great demo footage).

## Sampling notes (it's not a normal LLM)

- Generates a 256-token canvas, iteratively denoises it, keeps confident tokens,
  re-noises uncertain ones, then appends and continues. Entropy-Bound sampler on
  by default.
- Supports a Gemma-4 thinking mode (`<|think|>` token). Multimodal: put image/
  frame content **before** text instructions.

## Why it's a good first target

- Genuinely novel (diffusion LLM) — strong learning + blog/Twitter material.
- Days-old **beta** (unmerged llama.cpp PR, Studio in beta) — rough edges expected,
  which is the point: document the bumps.

## Plan
- [ ] Raise WSL RAM to ~24 GB ([how](../concepts/wsl2-memory.md)).
- [ ] Try via Unsloth Studio; capture first impressions in `lab/journal/`.
- [ ] Record an experiment (tok/s, RAM/VRAM, quality) in `lab/experiments/`.
- [ ] Bonus: `--diffusion-visual` screen capture for a post.

## Related
- [concepts/quantization.md](../concepts/quantization.md) · [concepts/wsl2-memory.md](../concepts/wsl2-memory.md) · [stacks/unsloth.md](../stacks/unsloth.md) · [stacks/llama-cpp.md](../stacks/llama-cpp.md)
