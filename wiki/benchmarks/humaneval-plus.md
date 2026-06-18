---
title: HumanEval+ / MBPP+ (evalplus)
tags: [benchmark, code, wrapped]
updated: 2026-06-18
status: documented
---

# HumanEval+ / MBPP+ (evalplus)

Functional-correctness coding benchmarks. **HumanEval+** and **MBPP+** take the
classic HumanEval and MBPP problems and add ~80x more test cases
([evalplus](https://github.com/evalplus/evalplus)), which catches solutions that
pass the original sparse tests but are actually wrong. We **wrap evalplus** rather
than reimplementing it.

## What it measures
- Python function synthesis from a signature + docstring/spec.
- Scored by **executing** the generated function against the (expanded) hidden
  test suite. Metric: **pass@1** (and pass@k).
- Tests *functional correctness on self-contained problems* — not large-codebase
  reasoning, not tool use, not multi-file edits.

## Format
Each task gives a prompt (signature + docstring); the model returns a function
body; evalplus runs it against the test suite in a sandbox.

## Scoring
`code_tests` (execution). evalplus ships its own runner + sandbox; use it directly.

## Reference scores (orientation, not exact)
Frontier code models land in the **~85-95% pass@1** range on HumanEval+ and
somewhat lower on MBPP+; small/older models drop off sharply. Check the live
[evalplus leaderboard](https://evalplus.github.io/leaderboard.html) for current
numbers rather than trusting a snapshot here.

## Contamination / freshness
**High contamination risk.** HumanEval (2021) and MBPP are old and pervasive in
training data; the `+` test expansion catches overfit solutions but the *problems*
themselves have leaked. For contamination-resistant coding signal use
**[LiveCodeBench](https://github.com/LiveCodeBench/LiveCodeBench)** (dated,
post-cutoff problems) alongside this. Treat a high HumanEval+ score as necessary,
not sufficient.

## Relevant model-types
General + coding models. Useful as a baseline for any model claiming coding
ability. For a math specialist like [VibeThinker-3B](../models/vibethinker-3b.md)
it's a partial fit (the makers target *competitive* coding, not function synthesis,
and explicitly say it's **not** for agentic/tool-use coding) — run it, but read
the score in that light.

## How to run (wrap evalplus, target Ollama)
```bash
# in a venv
pip install "evalplus[vllm]"   # or the base package; see evalplus docs
# evalplus can hit an OpenAI-compatible endpoint; Ollama serves one on :11434/v1
evalplus.evaluate --model <ollama-tag> --dataset humaneval \
  --backend openai --base-url http://localhost:11434/v1 --greedy
```
Record the result in [lab/benchmarks/results.csv](../../lab/benchmarks/README.md)
with the full schema (model, quant, sampling, k, machine, date). Exact flags
shift across evalplus versions — confirm against its README at run time.

## Gotchas
- Sandbox is mandatory (you're executing model-written code) — evalplus handles
  this; don't bypass it.
- "greedy" pass@1 vs sampled pass@k are different numbers; report which.
- Small-context models can truncate long docstrings — set an adequate `num_ctx`.
