# 2026-06-21 — Feeding the GPU while the judge thinks: harness concurrency

## The observation

Watching an agentic benchmark run, the GPU was idle most of the time. Each
episode in the email-triage / home-automation suites alternates between the model
under test generating a step (GPU work) and a **Copilot-CLI user-simulator**
replying (a blocking `subprocess`, ~10-15s, a frontier model thinking). The
`llm_judge` path is the same shape: generate, then a ~10-15s judge call. During
every one of those Copilot calls the local model sits idle.

The kicker: the harness couldn't even *see* the idle. The recorded `wall_s_total`
only summed model-generation wall time — the user-sim/judge waits were never
timed. So the first instinct ("the GPU looks idle") wasn't measurable from the
data we kept.

## The honest reframe

It's tempting to frame this as "maximize GPU utilization." But on this box the
model under test is small and fast (1B-12B, 18-185 tok/s) — the GPU is *cheap*.
The genuinely scarce resources are **wall-clock** and **Copilot premium calls**.
So the goal isn't to pin the GPU; it's to **hide Copilot latency behind GPU work**
and, critically, to **measure** it so the win is provable. Keeping the GPU busy is
the mechanism, not the objective.

And the constraint that shapes everything: **Ollama serves generation serially**
(one model, 8 GB). Concurrency can't give GPU *parallelism* — only *overlap*. The
win is "the one GPU slot is always busy on some episode while others wait on
Copilot," not "N generations at once."

## How it went

Worked the plan phase-by-phase, each phase its own commit with a background
`gpt-5.5` review running while I built the next phase — and each review's fixes
committed and reviewed in turn (the recursive cadence is now first-class in
`AGENTS.md`).

- **Phase 0 — measure first.** Added true elapsed `wall_clock_s` (results.csv
  schema v5), timed the Copilot calls, and pulled the queue-free GPU-compute number
  from Ollama's own `eval_duration`. A live smoke at N=1 printed the money line:
  `wall_clock 40.3s = request_wall 26.5 + copilot 13.8` — perfectly additive, zero
  overlap, copilot = 34% of wall-clock. You can't optimize what you can't see;
  now we could see it.
- **Phase 1 — resilience before concurrency.** Copilot rate-limits on rapid
  successive calls, and a single failure used to abort the whole run. So retry/
  backoff landed *before* the pool (the plan review caught that ordering). The
  Phase 1 review then caught a real bug I'd written: the transient-vs-permanent
  classifier scanned *successful* model output for keywords, so a user-sim reply
  saying "can you temporarily turn it off" or a judge rationale mentioning "429"
  would be wrongly retried. Fix: never keyword-scan real model text — only
  diagnostics.
- **Phase 2 — the core.** Refactored the serial `for item: for k:` loop into a
  **pure per-sample worker** plus a **single-threaded ordered collector**, run
  through a `ThreadPoolExecutor` (inline at `--concurrency 1`). Results are keyed
  `(item, sample)` and folded/written in **deterministic order**, and the
  scoring/aggregation code is untouched — concurrency changes only wall-clock,
  not scoring logic. With **deterministic (mocked) clients** the raw output is
  byte-for-byte identical regardless of N (proven in the selftest); **live**
  model/Copilot outputs are stochastic (temp > 0), so observed scores vary
  run-to-run by chance, not by concurrency. A worker exception or Ctrl-C cancels pending
  work and writes no results row (fail-closed). `--concurrency auto` = 3 for the
  Copilot-bound methods, 1 for equivalence/code_tests.

## The result

A/B on the full email-triage v0.3 set, qwen3.5:4b, same seed:

| run | wall_clock | copilot_wall | obs@1 |
|-----|-----------|--------------|-------|
| `--concurrency 1` | **123.7s** | 55.9s | 0.833 |
| `--concurrency auto` (3) | **81.7s** | 70.0s | 0.917 |

**~34% faster** (1.51×); the scoring *logic* is unchanged — the obs@1 0.833 vs
0.917 is run-to-run sampling variance (temp > 0), not a concurrency effect. The
N=1 row is perfectly additive (`123.7 ≈ 67.7 model + 55.9 copilot`), confirming
zero overlap serially. At N=3 the
Copilot waits collapse into other episodes' generation, landing the run near the
**Ollama serial-GPU floor** (~68s of actual GPU+load time). That floor is the
honest ceiling on the win here: the GPU work can't parallelize, only the waits can.
(In `results.csv` these two rows carry no concurrency column — it's a perf knob,
not a scoring input — but they're unambiguous via `wall_clock_s`: 123.7 =
`--concurrency 1`, 81.7 = `auto`.)

## Insights & open questions

- **The breakdown taught me to distrust my own metric.** Under concurrency, the
  per-request wall absorbs Ollama queue time, so `request_wall_sum` inflates and a
  naive "overlap_saved" overstates. The review and I both flagged it; the only
  honest "time saved" number is the N=1-vs-default `wall_clock_s` delta.
- **A batching server would likely win bigger** (hypothesis, unmeasured here).
  Ollama is the worst case (serial). On SGLang / llama.cpp the GPU floor itself
  drops (continuous batching), so concurrency *should* buy more than 34% — bounded
  by the 8 GB KV budget. The MiniCPM5/SGLang generalization is deferred (SGLang was
  down; the Ollama result already proves the thesis).
- **Bigger benchmarks, bigger absolute savings** (expected, pending measurement).
  home-automation (more turns, more Copilot calls) *should* show a larger
  wall-clock drop than email-triage.
- The review loop keeps paying off: every phase's cross-model review found a *real*
  issue (ordering, classifier scope, misleading metric). Authoring with the working
  model and reviewing with a different one is cheap insurance.

Plan + reviews: `tmp/harness-concurrency-plan.md`, `tmp/review-phase{0,1,2}.md`.
