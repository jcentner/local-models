# lab/experiments

One folder per experiment. The point is **reproducibility**: anyone (including
future me, or the agent) should be able to re-run it from the README alone.

## Structure

```
lab/experiments/<YYYY-MM-DD-slug>/
  README.md      hypothesis -> method (exact commands) -> result -> learnings
  (artifacts)    configs, small outputs, charts (keep big/raw stuff out of git)
```

## README template

```markdown
# <title>

- Date:
- Hypothesis / question:
- Setup: model, quant, runner+version, GPU layers (-ngl), context length, WSL RAM

## Method
<exact commands, copy-pasteable>

## Result
<numbers, screenshots, what happened>

## Learnings
<what I now believe; what to try next; link wiki pages updated>
```

After finishing, update the relevant `wiki/` page(s), append a `## [date]
experiment | ...` line to [../../wiki/log.md](../../wiki/log.md), and file durable
findings back into the wiki.

## Candidate experiments
- DiffusionGemma first run (Unsloth Studio) — see [../../wiki/models/diffusiongemma.md](../../wiki/models/diffusiongemma.md).
- Quant sweep (Q4_K_M / Q5_K_M / Q8_0) on one model — see [../../wiki/concepts/quantization.md](../../wiki/concepts/quantization.md).
- NPU vs GPU vs CPU on a small model (Windows-side Lemonade) — see [../../wiki/hardware/xdna2-npu.md](../../wiki/hardware/xdna2-npu.md).
