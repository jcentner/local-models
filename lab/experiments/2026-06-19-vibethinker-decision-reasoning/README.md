# VibeThinker-3B as a decision-maker / reasoner

- Date: 2026-06-19
- Machine: ASUS ProArt P16 (RTX 5070 Laptop, 8 GB, WSL2)
- Question: Does VibeThinker-3B - a math/competitive-code reasoning *specialist* -
  transfer to **general decision-making / practical reasoning**? (A deliberate
  out-of-specialty boundary test; the makers say it's not for general use.)
- Model: [vibethinker-3b](../../../wiki/models/vibethinker-3b.md) (Q8_0 GGUF, full GPU)
- Benchmark: [decision-reasoning v0.1](../../../wiki/benchmarks/decision-reasoning.md)
  (6 fresh hand-authored operational tradeoff scenarios), `llm_judge`
- Judge: **claude-opus-4.8** via Copilot CLI ([copilot-cli skill](../../../.github/skills/copilot-cli/SKILL.md))
- Setup: temp 1.0, top_p 0.95, top_k 0, num_ctx 32768, num_predict 4096, seed 0, k=1

## Method

```bash
cd lab/benchmarks
python3 -m harness.run --benchmark ../../benchmarks/decision-reasoning \
  --model vibethinker-3b --num-ctx 32768 --num-predict 4096 \
  --temperature 1.0 --top-p 0.95 --top-k 0 --seed 0 --judge-model claude-opus-4.8
```

## Result

**observed_pass@1 = 0.167 (1/6 above the 6.0 bar), mean ~4.3/10. ~71 tok/s.**
Every response closed its `<think>` block and gave a clear `Recommendation:`, so
these are genuine judgment scores, not truncation.

| Item | Scenario | Score | Judge's core critique |
|---|---|---|---|
| d1 | ship feature vs small fix | 5 | miscalculated the savings (math error) - argued for the opposite choice |
| d2 | engineer threatens to quit | 3 | invented a nonexistent option; misread the real tradeoff |
| d3 | bet-the-company enterprise deal | 5 | dismissed the explicit concentration risk + tight cash margin; no de-risking |
| d4 | marketing budget split | **6** | decisive sensible 80/20 to the proven channel; split asserted not justified |
| d5 | silently dropped 2% of records | 3 | assumed records critical; skipped the cheap "check downstream" investigation |
| d6 | hire the risky-but-able candidate | 4 | **inverted the crux** - claimed low oversight *reduces* corner-cutting risk |

## Learnings

- **Decisive but unreliable.** VibeThinker always commits to a clear recommendation
  (its reasoning-model training showing), but the decisions frequently rest on
  **misread scenarios or inverted cruxes** - including a quantitative miscalculation
  (d1) and backwards risk logic (d6). The hard-commit style makes the misreads more
  dangerous, not less.
- **Specialty does not transfer.** Narrow verifiable-reasoning (math/code) training
  does not generalize to messy practical judgment. Confirms the makers' "not for
  general use" warning - empirically, on fresh prompts.
- **Harness/judge stack works end to end.** First real run: local model under test
  (Ollama) + frontier judge (opus-4.8 via Copilot CLI) + fail-closed validation +
  recorded metadata. ~6 items took a few minutes (gen + ~10s/judge).
- **Caveat:** its CoT repeatedly said "we are ChatGPT" (a training artifact) - worth
  checking whether that identity confusion contributed to any misreads.

## Next

- Benchmark it on its **home turf** (competitive coding, sandboxed) to contrast the
  in-domain vs out-of-domain gap - that's the fair comparison.
- Run a stronger local model (e.g. qwen3.5:9b) on the same decision set for a
  baseline - is 4.3/10 bad for a 3B, or bad for *this* model specifically?
