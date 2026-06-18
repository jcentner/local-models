---
title: example-arithmetic (authored)
tags: [benchmark, math, authored, example]
updated: 2026-06-18
status: documented
---

# example-arithmetic (authored)

A tiny, hand-authored arithmetic word-problem set — the **first
`benchmarks/<name>/` example** and the harness smoke test. Not a serious eval;
it exists to demonstrate the authored-dataset format and to validate the runner
end to end.

## What it measures
Basic multi-step arithmetic word problems + final-answer formatting (`\boxed{}`).
3 items, trivial by design.

## Format
[`benchmarks/example-arithmetic/`](../../benchmarks/example-arithmetic/README.md):
`prompts.jsonl` (id + prompt), `answer_key.jsonl` (id + numeric answer),
`bench.json` (scoring = `equivalence`, with a `\boxed{}` system instruction).

## Scoring
`equivalence` — the [harness](../../lab/benchmarks/harness/README.md) extracts the
`\boxed{}` value (or final number) and compares numerically. Deterministic; no
judge needed.

## Reference scores
Any competent model should score 3/3 (pass@1) at temperature 0. A miss usually
means a *formatting* failure (no `\boxed{}`) rather than an arithmetic one — useful
for sanity-checking the extraction path.

## Contamination / freshness
Fresh wording, authored 2026-06-18; not from any public set. Difficulty is trivial
on purpose, so it carries no real capability signal — it's a plumbing test.

## How to run
```bash
cd lab/benchmarks
python3 -m harness.run --benchmark ../../benchmarks/example-arithmetic \
  --model <ollama-tag> --k 1 --temperature 0.0 --num-ctx 8192 --seed 0
```

## Note
Real authored benchmarks should come from `/author-benchmark` (interview +
verifiability gate + gpt-5.5/opus-4.8 critic loop), not be hand-written like this
stub. This page is the worked example of what such a benchmark's wiki page and
dataset folder look like.
