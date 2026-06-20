---
title: decision-reasoning (authored)
tags: [benchmark, reasoning, decision-making, authored, llm-judge]
updated: 2026-06-20
status: authored
---

# decision-reasoning (authored)

A fresh, hand-authored set of **real-world decision scenarios** for evaluating a
model as a **decision-maker / reasoner** - judgment under uncertainty, tradeoff
analysis, and decisiveness. Built to probe reasoning models *outside* narrow
math/code specialties.

## What it measures
Decision quality + reasoning on open-ended operational/strategic scenarios
(prioritization, risk, resource allocation, hiring, ambiguity). There is no single
"correct" answer - it tests judgment, not recall.

## Format
[`benchmarks/decision-reasoning/`](../../benchmarks/decision-reasoning/README.md):
6 scenario prompts; the model reasons and ends with a clear `Recommendation:`.
A system prompt asks for assumptions + tradeoffs + a final recommendation. No
answer key (rubric-scored).

## Scoring
`llm_judge` against [the rubric](../../benchmarks/decision-reasoning/rubric.md),
scored 0-10 by a **frontier judge** (default `claude-opus-4.8` via Copilot CLI -
**never a local small model**). Pass threshold 6.0. Criteria: crux identification,
reasoning quality, handling uncertainty/constraints, decisiveness, practical judgment.
Judge config (model + date + rubric) is recorded with each result.

## Results so far (local)
Canonical numbers (with cost, host, date) live in
[`lab/benchmarks/results.csv`](../../lab/benchmarks/results.csv); this is a quick
orientation, not the source of truth.
- [VibeThinker-3B](../models/vibethinker-3b.md) (2026-06-19): **1/6 above bar,
  mean ~4.3/10** - decisive but frequently misreads the crux. See the
  [experiment](../../lab/experiments/2026-06-19-vibethinker-decision-reasoning/README.md).
- [MiniCPM5-1B](../models/minicpm5-1b.md): over Ollama (2026-06-19) **0/6, mean
  ~0.17/10** - degenerate `<think>`, **confounded** by uncontrollable thinking.
  **Clean re-test over [SGLang](../stacks/sglang.md) (2026-06-20):** still **0/6**
  but now *coherent* - No-Think mean ~2.7/10, Think mean ~3.0/10 (CoT completes, no
  truncation). The Ollama 0.17 was a **serving artifact**; the real verdict is
  coherent-but-shallow (a genuine 1B judgment ceiling, same shape as VibeThinker).
  See the [model page](../models/minicpm5-1b.md).
- No baseline from a general model yet (run qwen3.5:9b next to calibrate).

## Contamination / freshness
**Fresh** - authored 2026-06-19, original scenarios, not from any public set.
Re-authoring/expanding should go through `/author-benchmark` (critic loop).

## Relevant model-types
General assistants and reasoning models. Especially useful as a **boundary test**
for narrow specialists (math/code models) and as a practical-judgment gauge for
models you'd actually delegate decisions to.

## Gotchas
- Reasoning models emit long CoT (`<think>`); set `--num-predict` high enough
  (>=4096) so they reach the final `Recommendation:` - otherwise you score a
  truncation, not a decision.
- LLM-judge scores only compare within the same judge config; keep the judge pinned.
- Small set (6 items) + holistic judging = treat as a rough gauge, not a precise rank.
