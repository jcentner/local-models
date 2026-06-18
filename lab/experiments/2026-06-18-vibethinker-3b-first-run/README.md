# VibeThinker-3B — first run (math/reasoning sanity check)

- Date: 2026-06-18
- Machine: ASUS ProArt P16 ([wiki/hardware/proart-p16.md](../../../wiki/hardware/proart-p16.md)) — RTX 5070 Laptop, 8 GB VRAM, WSL2
- Hypothesis / question: Does VibeThinker-3B run comfortably full-GPU at Q8_0 on
  8 GB, and do its math/reasoning answers hold up on a *fresh* (unpublished)
  problem - i.e. is the headline benchmark hype real outside the benchmark sets?
- Model: [VibeThinker-3B](../../../wiki/models/vibethinker-3b.md) (WeiboAI, Qwen2.5-3B base, MIT)
- Setup (planned):
  - quant: Q8_0 GGUF (community, e.g. JohnRoger/VibeThinker-3B-Q8_0-GGUF)
  - runner + version: ollama 0.20.2 (custom Modelfile) — and/or llama.cpp llama-server
  - GPU layers (-ngl): 99 (full offload expected to fit)
  - context length (num_ctx): 32768 (long-CoT model; avoid the ~4K default trap)
  - sampling: temperature 1.0, top_p 0.95, top_k 0 (= -1 elsewhere)
  - WSL RAM: default (~15 GB) is fine at this size

## Method

```bash
# 1. download a Q8_0 GGUF
hf download JohnRoger/VibeThinker-3B-Q8_0-GGUF --include "*Q8_0*" \
  --local-dir ~/models/vibethinker-3b

# 2. Modelfile — paste the community chat TEMPLATE from the HF GGUF discussion
#    (https://huggingface.co/JohnRoger/VibeThinker-3B-Q8_0-GGUF/discussions/1)
cat > ~/models/vibethinker-3b/Modelfile <<'EOF'
FROM ./vibethinker-3b-Q8_0.gguf
PARAMETER temperature 1.0
PARAMETER top_p 0.95
PARAMETER top_k 0
PARAMETER num_ctx 32768
# TEMPLATE """..."""   # paste so the <think> reasoning block is parsed
EOF

# 3. build + run with timing
ollama create vibethinker-3b -f ~/models/vibethinker-3b/Modelfile
ollama run --verbose vibethinker-3b "<a fresh, non-benchmark hard math problem>"

# 4. capture footprint while it generates (separate shell)
ollama ps        # VRAM
nvidia-smi       # GPU
free -h          # RAM
```

Test prompts (use unseen problems, not the published AIME/HMMT sets):
1. A hard but checkable math/proof question.
2. A LeetCode-style algorithm problem (verify by running the code).
3. One out-of-domain general-knowledge question (expected to be weak — confirms
   it's a specialist, per the maker's own guidance).

## Result

<!-- fill after running: VRAM used, prompt tok/s, generation tok/s, time-to-answer,
     whether 32K context held, correctness on each prompt. Add a row to
     ../../benchmarks/results.csv (model, quant, runner+version, ctx, -ngl,
     prompt tok/s, gen tok/s, VRAM, RAM, machine, date). -->

## Learnings

<!-- what I now believe; quant sensitivity to try next (Q4_K_M vs Q8_0);
     update wiki/models/vibethinker-3b.md status to 'tried' and record the
     per-machine fit verdict; append a `## [date] experiment | ...` line to
     ../../../wiki/log.md. -->
