# 2026-06-19 — A benchmark framework, and VibeThinker as a decision-maker

Spent this stretch turning the repo from "run models and take notes" into
something that can actually *measure* them — and then ran the first real
measurement.

## Building the framework

The shape fell out of the repo's existing wiki/lab split: benchmark **definitions**
are durable knowledge (`wiki/benchmarks/`), authored **datasets** are
version-controlled artifacts (`benchmarks/`), and **results** are per-machine
(`lab/benchmarks/`). The one idea that mattered most: a benchmark is *prompts + a
scoring harness*, and the scoring is the hard 90%. So I built a small stdlib
harness with three scorers — `equivalence` (math/short-answer), `code_tests`
(execute against tests), and `llm_judge` (rubric) — plus four slash-prompts
(`/new-model`, `/benchmark`, `/new-benchmark`, `/author-benchmark`).

Then I had a different model family critique the whole thing. It was right about
the things that matter: a benchmark that scores *silently wrong* is worse than one
that refuses to run. So Batch A added fail-closed validation (no run if keys are
missing/mismatched/empty), gated code execution behind an explicit sandbox flag
(it was happily running model-written code on the host), renamed the metric to the
honest `observed_pass_at_k`, and started recording the run metadata that was being
thrown away. I deliberately did *not* take its heavier suggestions — formal pass@k
estimators, mandatory containers, content hashing — because I want a light personal
gauge, not a leaderboard.

## The judge pivot

The biggest design change: **never use a local 4B model as a judge.** Judging
open-ended work needs a frontier model. I verified — against the docs *and* live —
that GitHub Copilot CLI can be driven non-interactively as a clean judge:
`copilot -p '...' --model claude-opus-4.8 --no-custom-instructions --allow-all-tools -s`
returns clean JSON. (Nice catch: my account exposes `claude-opus-4.8` and `gpt-5.5`
even though the public docs list neither — always probe, don't trust the docs'
model list.) That became `CopilotCLIJudge`, now the only judge path. ~10s/call, so
batching will matter eventually.

## VibeThinker as a decision-maker

The real question I cared about: can VibeThinker-3B — a *math/competitive-code*
reasoning specialist — make good decisions? I pulled it (Q8, ~71 tok/s, full GPU),
hand-seeded six fresh operational tradeoff scenarios, and let opus-4.8 judge.

**1 of 6 above bar, mean ~4.3/10.** It finished its reasoning every time and
committed to a clear recommendation — but the recommendations frequently rested on
*misreads*: a flat arithmetic error that argued for the opposite choice, an
invented option that wasn't in the scenario, and — my favourite — inverting the
risk logic to claim that *less* oversight *reduces* the chance of someone cutting
corners. Backwards.

The lesson isn't "VibeThinker is bad." It's that narrow verifiable-reasoning
training (math, code, things with a checkable answer) does **not** transfer to
messy practical judgment, and the model's confident, hard-committing style makes
its misreads *more* dangerous, not less. The makers say it's not for general use;
now I've watched exactly how it fails. That's the whole point of building the
harness — turning "the docs say X" into "I saw X happen on my machine."

## Open threads
- Benchmark it on its home turf (competitive coding, sandboxed) for the fair
  in-domain contrast — which needs the Podman sandbox, up next.
- Baseline a general model (qwen3.5:9b) on the same decision set — is 4.3 bad for a
  3B, or bad for *this* model?
- Expand `decision-reasoning` into difficulty tiers + categories, built through
  `/author-benchmark` to finally exercise the critic loop.
