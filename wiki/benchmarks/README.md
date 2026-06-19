---
title: Benchmarks — overview
tags: [benchmark, concept, index]
updated: 2026-06-19
status: living
---

# Benchmarks

How this repo thinks about, documents, runs, and authors benchmarks. Read this
before using any of the benchmark prompts.

**Status (2026-06-19):** `llm_judge` fully working (frontier judge = opus-4.8 via
Copilot CLI); `equivalence` works; `code_tests` works via a locked-down **Podman**
sandbox (`--code-sandbox podman`). Two authored benchmarks have run end to end:
[decision-reasoning](decision-reasoning.md) (VibeThinker-3B) and a `code-basics`
smoke set (qwen3.5:4b 3/4).

## A benchmark = prompts + a scoring harness

A list of questions is the easy 10%. The 90% is **automated, reproducible
scoring**, and it differs by domain:

| Domain | Scoring method | Notes |
|---|---|---|
| Math (AIME/HMMT/IMO-style) | answer extraction + symbolic/numeric equivalence | scorer exists; not a current focus |
| Code (HumanEval+/MBPP+/LiveCodeBench) | execute candidate code against hidden tests in a **Podman sandbox** (`--code-sandbox podman`) | locked-down container; `--no-think` for thinking models |
| Open-ended (creative writing, agentic, reasoning) | **rubric LLM-judge** by a frontier model (opus-4.8 via Copilot CLI; never a local small model) | pin judge model+version+rubric; judge config is part of the result |

**Prefer wrapping existing eval frameworks** ([evalplus](https://github.com/evalplus/evalplus),
[lm-eval-harness](https://github.com/EleutherAI/lm-evaluation-harness),
[livecodebench](https://github.com/LiveCodeBench/LiveCodeBench),
[BFCL](https://github.com/ShishirPatil/gorilla)) — hand-roll a scorer only when no
good one exists (mostly our custom use-case evals).

## Where things live (definitions vs results)

- **`wiki/benchmarks/<name>.md`** — the **definition** (machine-independent): what
  it measures, format, scoring method + harness command, reference/SOTA scores,
  **contamination/freshness status**, which model-types it's relevant for, gotchas.
- **`benchmarks/<name>/`** ([top-level](../../benchmarks/README.md)) — **authored
  custom datasets** (version-controlled): prompts, a *separate* answer key, an
  optional rubric, and provenance + critic sign-off.
- **`lab/benchmarks/`** ([harness](../../lab/benchmarks/harness/README.md) +
  [results](../../lab/benchmarks/README.md)) — the runner/scorers and the
  per-machine `results.csv`.

Same portability rule as models: **definitions are machine-independent (wiki);
results are per-machine (lab), tagged with the machine.**

## Methodology (non-negotiable)

- **Stochasticity:** reasoning models run at high temperature (VibeThinker uses
  temp 1.0). A single pass is noise — report **pass@k / avg@k**, not one sample.
- **Pin everything:** model+quant, runner+version, sampling (temp/top_p/top_k),
  context length, seed, n-samples/k, judge config, machine, date. See the
  [results schema](../../lab/benchmarks/README.md).
- **Contamination is the whole game.** Public benchmarks leak into training data
  (we hit this with [VibeThinker](../models/vibethinker-3b.md) — "benchmaxxing"
  skepticism). Every benchmark page records a freshness/contamination note, and
  **fresh, held-out custom benchmarks are the antidote.**
- **Sandbox** untrusted generated code. **Cost/time:** an 8 GB bandwidth-bound GPU
  + long traces + pass@k can mean hours — estimate before running.

## The four workflow verbs

| Prompt | Purpose |
|---|---|
| [`/new-model`](../../.github/prompts/new-model.prompt.md) | research + document a model, stage testing |
| `/new-benchmark <name>` | ingest + document an existing public benchmark (mirrors `/new-model`) |
| `/benchmark <model>` | recommend relevant benchmarks for a model, estimate cost, run, record results |
| `/author-benchmark <scenario>` | interactively create a custom held-out benchmark, with a gpt-5.5/opus-4.8 critic loop |

## Priority use-cases (build scorers for these first)

Creative writing, tool-use/agentic workflows, and coding — plus standard
math/reasoning for cross-checking published claims. See the
[buildout plan](../../tmp/benchmark-framework-plan.md) (local scratch) for milestones.

### Scoring approach per use-case
- **Coding** — `code_tests` (execute against tests). Runs in a locked-down **Podman**
  sandbox (`--code-sandbox podman`; `local-unsafe` host exec is opt-in). Wrap
  [evalplus](humaneval-plus.md) for HumanEval+/MBPP+; add LiveCodeBench for
  contamination-resistance. *Working.*
- **Creative writing** — `llm_judge` with a pinned strong judge (opus-4.8 / gpt-5.5)
  against the reusable [creative-writing rubric](../../benchmarks/_rubrics/creative-writing.md).
  Prefer pairwise-vs-reference to cut judge variance. *Judge path built; author a
  fresh prompt set via `/author-benchmark`.*
- **Tool-use / agentic** — needs a rollout harness: give the model tools (real or
  mocked), run a multi-step task, and check success (right tools, right order,
  goal achieved). *Planned* — wrap an existing agentic eval (BFCL for
  function-calling; tau-bench-style for workflows) or build a minimal
  transcript-checking scorer tied to our own tool defs. VibeThinker is a good
  **negative control** here (explicitly not trained for tool use).

## Documented benchmarks

- [humaneval-plus.md](humaneval-plus.md) — HumanEval+/MBPP+ coding (wraps evalplus); high contamination risk.
- [decision-reasoning.md](decision-reasoning.md) — authored decision-making/reasoning scenarios; `llm_judge` (opus-4.8); fresh/held-out.
