# MiniCPM5-1B first run (smoke + tool-use tilt)

- Date: 2026-05-19 model release; experiment staged 2026-06-19 (not yet run)
- Machine: ASUS ProArt P16 (RTX 5070 Laptop, 8 GB, WSL2) — see [proart-p16](../../../wiki/hardware/proart-p16.md)
- Question: Does MiniCPM5-1B actually deliver as a small **on-device tool-use /
  reasoning** model, or is the headline competition-math just DAPO-Math
  benchmaxxing? Is a 1B model *reliable* enough to be a home-agent brain?
- Model: [minicpm5-1b](../../../wiki/models/minicpm5-1b.md) (OpenBMB official GGUF)
- Quant: start **Q8_0** (1.15 GB) — safest at 1B; later sweep Q4_K_M (688 MB)
- Runner: Ollama (daily driver) running the HF GGUF directly; SGLang only if
  testing native `minicpm5` tool-call parsing

## Fit verdict (this machine)

Trivial. Q8_0 (~1.2 GB) or even F16 (~2.2 GB) fits **fully on the 8 GB GPU**
(`-ngl 99`) with a large context; KV at 8–32K adds only a few hundred MB.
[WSL RAM](../../../wiki/concepts/wsl2-memory.md) is a non-issue at 1B. No
wslconfig change needed.

## Method (planned — exact commands; do NOT run weights until confirmed)

```bash
# 1. Run the official GGUF directly via Ollama (No Think default)
ollama run hf.co/openbmb/MiniCPM5-1B-GGUF:Q8_0 "Briefly: what is MiniCPM5?"

# 2. Repeatable alias (No Think sampling: temp 0.7 / top_p 0.95)
cat > Modelfile <<'MF'
FROM hf.co/openbmb/MiniCPM5-1B-GGUF:Q8_0
PARAMETER temperature 0.7
PARAMETER top_p 0.95
PARAMETER num_ctx 32768
MF
ollama create minicpm5-1b -f Modelfile
ollama ps                       # confirm full-GPU load + VRAM
ollama run --verbose minicpm5-1b "List 3 uses for a 1B local model."   # tok/s

# 3. Benchmark via the harness (out-of-the-box generalist judgment)
cd lab/benchmarks
python3 -m harness.run --benchmark ../../benchmarks/decision-reasoning \
  --model minicpm5-1b --num-ctx 32768 --num-predict 4096 \
  --temperature 0.7 --top-p 0.95 --seed 0 --judge-model claude-opus-4.8

# 4. (later) Think mode: temp 0.9, larger --num-predict so <think> doesn't
#    truncate the answer; and tool-use via BFCL / SGLang minicpm5 parser.
```

## Fields to record (for results.csv comparability)

model, quant, runner+version (`ollama-harness` + ollama version), provider
(`ollama`), context length, GPU layers (-ngl 99), num_predict, tok/s (prompt +
gen), VRAM used (`ollama ps`), **machine** (ProArt P16), score, judge model, date.

## Result

_(blank — not run yet)_

## Learnings

_(blank — not run yet)_

## Next

- If the generalist score is decent, run [BFCL](../../../wiki/benchmarks/bfcl.md)
  irrelevance / multi-turn-miss-param — the home-agent tool-use categories — as
  the headline test for this model.
- Contrast against [VibeThinker-3B](../../../wiki/models/vibethinker-3b.md) on the
  same [decision-reasoning](../../../wiki/benchmarks/decision-reasoning.md) set:
  1B tool-tilted generalist vs 3B math specialist.
- Quant sweep Q4_K_M vs Q8_0 — does 688 MB hold up at 1B?
