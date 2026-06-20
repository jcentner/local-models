# Gemma-4-12B-Coder (Fable5 × Composer2.5) v1 — first run

- Date: ~2026-06-15 model release; experiment staged 2026-06-20 (not yet run)
- Machine: ASUS ProArt P16 (RTX 5070 Laptop, 8 GB, WSL2) — see [proart-p16](../../../wiki/hardware/proart-p16.md)
- Hypothesis / question: Does this Python-coding finetune actually beat base
  Gemma 4 12B on real coding tasks, or is it a benchmaxxed/degraded "fancy-named
  finetune" (per the community warning)? Does it hold up on **fresh, unpublished**
  problems, and is the open reasoning helping or just burning tokens?
- Model: [gemma-4-12b-coder-fable5](../../../wiki/models/gemma-4-12b-coder-fable5.md) (yuxinlu1 GGUF)
- Quant: start **Q3_K_M** (6.09 GB, full-GPU); compare Q4_K_M (7.38 GB, partial offload) if time
- Runner: llama.cpp server (recent build, `gemma4_unified`); or Ollama via Modelfile if its bundled llama.cpp supports `gemma4`
- Context: 8192 to start (q8_0 KV); stretch with `q4_0` KV cache
- GPU layers: `-ngl 99` (Q3_K_M); expect partial offload at Q4_K_M

## Fit verdict (this machine)

- **Q3_K_M (6.09 GB): fits fully on the 8 GB GPU** with ~8K context (q8_0 KV +
  ~1.5 GB overhead ≈ within 8 GB). This is the full-GPU default.
- **Q4_K_M (7.38 GB): does NOT fit full-GPU** with usable context — needs partial
  CPU offload (slower, bounded by [WSL RAM ~15 GB](../../../wiki/concepts/wsl2-memory.md))
  or a tiny (~2–4K) context. Use `q4_0` KV cache to roughly double context if needed.
- No `wslconfig` bump required for Q3_K_M full-GPU. Raise WSL RAM only to try
  Q4_K_M/Q6_K with CPU offload.

## Method (planned — do NOT run weights until confirmed)

```bash
# 1. Download a quant (Q3_K_M = full-GPU fit on 8 GB)
hf download yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF \
  --include "*Q3_K_M*" --local-dir ~/models/gemma4-coder

# 2. Serve via recent llama.cpp (gemma4_unified arch — older builds won't load)
llama-server -m ~/models/gemma4-coder/*Q3_K_M*.gguf \
  -ngl 99 -fa on --ctx-size 8192 \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --temp 1.0 --top-p 0.95 --top-k 64 \
  --host 0.0.0.0 --port 18080

# 3. Benchmark: the authored code-basics set (code_tests, Podman sandbox),
#    pointing the harness at the llama.cpp OpenAI-compatible endpoint.
#    Compare head-to-head against BASE gemma-4-12B-it to isolate the finetune delta.
cd ../../  # repo root → lab/benchmarks
# python3 -m harness.run --benchmark ../../benchmarks/code-basics \
#   --provider openai-compatible --base-url http://localhost:18080/v1 \
#   --model gemma4-coder --code-sandbox podman ...
```

Record per the harness: model, quant, runner+version, context length, `-ngl`,
tok/s (prompt + gen), VRAM/RAM used, **machine** (ProArt P16), date.

## Result

(blank — not yet run)

## Learnings

(blank — fill in after the run; then update
[wiki/models/gemma-4-12b-coder-fable5.md](../../../wiki/models/gemma-4-12b-coder-fable5.md)
and append a `bench`/`experiment` line to [wiki/log.md](../../../wiki/log.md))

Key things to capture:
- Finetune **delta vs base** gemma-4-12B-it on the same prompts (the whole point).
- Whether the open reasoning improves correctness or just adds latency.
- Quant sensitivity (Q3_K_M vs Q4_K_M) on coding correctness.
- Does it generalize off published problems, or show benchmaxxing?
