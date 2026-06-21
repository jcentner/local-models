---
title: Eval reliability — pass@k vs pass^k, flaky items, and error bars
tags: [concept, benchmark, methodology, reliability]
updated: 2026-06-20
status: living
---

# Eval reliability

How to run a benchmark so the score reflects the model, not the luck of one draw —
and so **inconsistency is visible instead of hidden**. This is the methodology
behind the harness's multi-pass metrics ([run.py](../../lab/benchmarks/harness/run.py)).

> **Why we care here.** The north star is picking a model to run a *local-agent
> suite* unattended. A model that does the right thing 70% of the time and silently
> the wrong thing 30% of the time is **worse** than a steady 60% one for home
> automation. Small and **quantized** small models flake; a single pass can't see it.

## The one-pass trap

Run each item once and you measure a coin flip, not a skill. Worse, the obvious fix
(run k times, count an item correct if *any* pass succeeded) measures the wrong
thing for our use-case. Two metrics, opposite directions:

- **`observed_pass_at_k`** — best-of-k: fraction of items with **≥1** correct in k
  samples. A **capability ceiling**. It **rises with k** — give a flaky model more
  tries and it looks better. On its own it *hides* instability. (This is *not* the
  HumanEval/Codex unbiased pass@k estimator; don't compare it to leaderboard pass@k.)
- **`pass_hat_k`** (τ-bench's **pass^k**) — all-of-k: fraction of items correct on
  **every** one of the k samples. **Reliability / consistency.** It **falls with k**
  as instability shows. For an unattended agent this is the number that matters.

`observed_pass_at_k ≥ pass_hat_k` always; the **gap between them is the flakiness**.
The harness also reports **`flaky_items`** = count of items with `0 < correct < k`
(passed some-but-not-all passes) — the items to actually go read.

τ-bench's headline makes the point: gpt-4o solves <50% of retail tasks and
**pass^8 < 25%** — "quite inconsistent" even when it *can* do the task
([Yao et al. 2024](https://arxiv.org/abs/2406.12045)).

## Error bars (don't over-read a small set)

Our custom sets are small (6–24 items). A point score with no spread invites
over-reading. Per Anthropic's *Adding Error Bars to Evals*
([Miller 2024, arXiv 2411.00640](https://arxiv.org/abs/2411.00640)):

- **Report SEM.** Treat items as draws from a "question universe"; by the CLT the
  mean has a standard error. The harness reports **`sem`** = std of per-item mean
  scores / √n. A 95% CI ≈ mean ± 1.96·SEM.
- **Resample non-deterministic outputs.** For CoT / sampled answers, take several
  samples per item and average per item before aggregating (Inspect calls this
  *epochs*) — exactly what k>1 does here.
- **Compare in pairs.** When ranking two models on the *same* items, a paired
  difference cancels per-item difficulty and tightens the comparison (free variance
  reduction). Frontier models correlate 0.3–0.7 on shared items.
- **Mind power.** Few items + high variance = wide CIs; small true differences won't
  be detectable. Expanding to ~20 items + k≥3 buys real power. Until then, treat a
  score as a **rough gauge**, not a precise rank.

## How we run it (house rules)

- **Default `--k 3`.** k=1 is a quick smoke only. Two passes can't break a tie on a
  flaky item; three give a majority + a meaningful pass^3.
- **Reliability passes at the model's recommended temperature, not `temp=0`.**
  Reliability is meaningless when sampling is near-deterministic — temp=0 hides the
  very instability we're measuring. Keep a separate temp=0 run for a deterministic
  *capability* read where useful (e.g. code).
- **Report both** `observed_pass@k` and `pass^k`, plus `flaky_items` and `sem`.
  Weight **pass^k** for the home-agent verdict.
- **Slice when structured.** `--slice-by <meta field>` (e.g. `tier`, `category`)
  prints per-group reliability so a score is diagnostic ("steady on prioritization,
  flaky under-specified"), not one opaque number.
- **Pin everything** (model+quant, provider, sampling, **think** (`on|off|default`
  CoT control), seed, k, judge config, machine/endpoint, cost, date) — see the
  [results schema](../../lab/benchmarks/README.md).

## Cost

k multiplies calls. For `agentic` sets that means k× the premium Copilot user-sim
turns; for `llm_judge` it means k× frontier-judge calls. k=3 is fine on the small
sets; drop to k=2 while iterating on the 12+-item home-automation set.

## See also
- [benchmarks/README](../benchmarks/README.md) — the four scorers + workflow.
- [decision-reasoning](../benchmarks/decision-reasoning.md) · [email-triage](../benchmarks/email-triage.md) · [home-automation](../benchmarks/home-automation.md) — the custom sets these metrics grade.
- [llm-wiki-method](llm-wiki-method.md) · [quantization](quantization.md) (why quantized small models flake).
