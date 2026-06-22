---
title: Benchmarks — overview
tags: [benchmark, concept, index]
updated: 2026-06-20
status: living
---

# Benchmarks

How this repo thinks about, documents, runs, and authors benchmarks. Read this
before using any of the benchmark prompts.

> **Aide models eval differently.** STT / TTS / embeddings / retrieval don't use
> these scorers — they have objective metrics (WER / NDCG@k / Recall@k / MOS) and
> their own track: [concepts/aide-models.md](../concepts/aide-models.md) +
> [`/new-aide`](../../.github/prompts/new-aide.prompt.md).

**Status (2026-06-20):** **four working scorers** — `llm_judge` (frontier judge =
opus-4.8 via Copilot CLI), `equivalence`, `code_tests` (locked-down **Podman**
sandbox, `--code-sandbox podman`), and **`agentic`** (model-agnostic tau-bench-style
rollout + Copilot-CLI user-simulator; two **tool sets** — `support` (act/ask/escalate)
and `home_automation` (act/confirm/refuse) — over a `prompt` or `native`
function-calling protocol). Authored benchmarks run end to end:
[decision-reasoning](decision-reasoning.md) (VibeThinker 1/6, MiniCPM5 0/6),
`code-basics` (qwen3.5:4b 3/4), [email-triage](../../benchmarks/email-triage/README.md)
(**v0.3, 12 scenarios** - ask/ambiguity, prompt-injection, judged fabrication),
[home-automation](../../benchmarks/home-automation/README.md) (**v0.4, 19 scenarios** -
grounding + compound double-confirm, device-aware `ask.device` confirm, a dependency
precondition, injection-via-status, judged refuse/confirm). The agentic scorer gained a respond-and-continue `ask`,
structured `ask.device` confirmation, `device.requires` preconditions,
`forbidden_device_attempts`, and an optional `--judge-messages` hybrid layer; each
raw run line now carries a sliceable `meta` ({tier,category}) for the run-viewer.
Pre-v0.2/v0.3 reference numbers (qwen3.5:4b, gemma-4-12b 11/12, MiniCPM5-1B 7/12) are
superseded - re-run at `--k 3`.
**MiniCPM5-1B was re-tested over [SGLang](../stacks/sglang.md)** (container,
controllable thinking) — its Ollama scores were a serving artifact: a **weak
abstract reasoner** (decision 0/6, now coherent) but a **decent home-automation
tool-executor** (7/12).
Models under test run **local (Ollama) or API (OpenAI-compatible,
e.g. Z.AI GLM)** via `--provider`; results record **cost** alongside capability.
**External-first:** wrap existing benchmarks aligned with my interests
(decision-making, agentic/triage) before authoring custom ones; custom benchmarks
earn their keep for my own use-cases (home automation, email triage).

## A benchmark = prompts + a scoring harness

A list of questions is the easy 10%. The 90% is **automated, reproducible
scoring**, and it differs by domain:

| Domain | Scoring method | Notes |
|---|---|---|
| Math (AIME/HMMT/IMO-style) | answer extraction + symbolic/numeric equivalence | scorer exists; not a current focus |
| Code (HumanEval+/MBPP+/LiveCodeBench) | execute candidate code against hidden tests in a **Podman sandbox** (`--code-sandbox podman`) | locked-down container; `--no-think` for thinking models |
| Open-ended (creative writing, reasoning) | **rubric LLM-judge** by a frontier model (opus-4.8 via Copilot CLI; never a local small model) | pin judge model+version+rubric; judge config is part of the result |
| Tool-use / agentic | model-agnostic **rollout**: agent + Copilot user-sim + mocked tools; deterministic state/policy scored | **built** (`agentic`); 2 tool sets (`support`, `home_automation`) x 2 protocols (`prompt`, `native`); email-triage + home-automation |

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
results are per-environment (lab)** — per-machine for local models, per-provider +
per-date for API models (prices and hosted models drift).

### Local vs API (a first-class comparison)

The harness runs the same benchmark against either a **local** model (Ollama,
`--provider ollama`) or an **API** model (OpenAI-compatible, `--provider
openai-compatible` + `--base-url` + `--api-key-env`). Each run records token
totals and `cost_usd` (from `--price-in/--price-out`, USD per 1M tokens; local =
0). Running both and putting **capability next to cost** is the core decision for
the home agent: a $20/mo API may beat buying hardware to run a weaker local model.
Ollama also serves an OpenAI-compatible endpoint on `:11434/v1`, so the
`openai-compatible` path can target a local model too (handy for wrapping external
harnesses like BFCL). **[SGLang](../stacks/sglang.md)** is the other local
`openai-compatible` target — for **thinking / tool models** Ollama can't serve
faithfully (`enable_thinking`, native tool parsers incl. `minicpm5`).

## Methodology (non-negotiable)

- **Stochasticity & reliability:** reasoning models run hot (VibeThinker temp 1.0)
  and small/quantized models flake. A single pass is noise — default **`--k 3`** and
  report **both** `observed_pass@k` (best-of-k ceiling) **and** `pass^k` (all-k
  reliability, the home-agent signal) + `flaky_items` + `sem`. Run reliability
  passes at the recommended temp, not temp=0. See
  [eval-reliability](../concepts/eval-reliability.md).
- **Concurrency is free speed, not a result:** agentic/llm_judge runs default to
  `--concurrency auto` (3 Copilot-bound samples in flight, 1 for equivalence/
  code_tests) to overlap the frontier user-sim/judge waits with GPU generation —
  `wall_clock_s` drops (measured **~34%** on email-triage) with **scoring unchanged**
  vs serial. It does not parallelize the (serial) Ollama GPU; `results.csv`
  `wall_clock_s` is true elapsed (vs `wall_s_total` = per-request wall, queue-
  inflated at N>1). A transient Copilot blip is retried; a bad `--model` fails fast.
- **Pin everything:** model+quant, **provider** (local/API), runner+version,
  sampling (temp/top_p/top_k), **think** (`on|off|default` CoT control), context
  length, seed, n-samples/k, judge config, machine/endpoint, **cost** (`cost_usd`),
  date. See the [results schema](../../lab/benchmarks/README.md).
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

Aligned with the [vision](../../README.md#vision): **LLMs as decision-makers**,
**agentic workflows / triage**, and **coding** — building toward a home-automation
agent (with email triage as a sibling use-case) — plus standard math/reasoning for
cross-checking published claims. **External-first:** wrap an existing benchmark
that fits these interests before hand-authoring. See the
[refactor plan](../../tmp/api-inference-refactor-plan.md) (local scratch).

### Scoring approach per use-case
- **Coding** — `code_tests` (execute against tests). Runs in a locked-down **Podman**
  sandbox (`--code-sandbox podman`; `local-unsafe` host exec is opt-in). Wrap
  [evalplus](humaneval-plus.md) for HumanEval+/MBPP+; add LiveCodeBench for
  contamination-resistance. *Working.*
- **Creative writing** — `llm_judge` with a pinned strong judge (opus-4.8 / gpt-5.5)
  against the reusable [creative-writing rubric](../../benchmarks/_rubrics/creative-writing.md).
  Prefer pairwise-vs-reference to cut judge variance. *Judge path built; author a
  fresh prompt set via `/author-benchmark`.*
- **Tool-use / agentic** — ***Built (v0): the `agentic` scorer.*** A lightweight
  tau-bench-style **rollout** in our harness — model-agnostic (runs any Ollama tag
  or API model via a prompt-mode JSON tool protocol, so brand-new models like
  MiniCPM-5 work day one), with the **Copilot CLI as the user-simulator** (same
  frontier-model mechanism as the judge) and deterministic state/policy scoring
  (terminal action + required/forbidden tools) on *our* use-cases. First set:
  [email-triage](../../benchmarks/email-triage/README.md) (escalation). External
  cross-check: **[tau³-bench](https://github.com/sierra-research/tau2-bench)**
  (model-agnostic via litellm). **[BFCL](bfcl.md)** is a rigid **reference**
  (registered models only — lags new models), for published comparisons only.
  VibeThinker is a good **negative control** here.

## Documented benchmarks

- [bfcl.md](bfcl.md) — Berkeley Function-Calling Leaderboard (tool-use/agentic; wraps bfcl-eval); **reference only** — registered-models-only rigidity lags new models; use for published comparisons, not the daily agentic driver.
- [humaneval-plus.md](humaneval-plus.md) — HumanEval+/MBPP+ coding (wraps evalplus); high contamination risk.
- [decision-reasoning.md](decision-reasoning.md) — authored decision-making/reasoning scenarios (v0.2, 21 items; tiers + categories + traps); `llm_judge` (opus-4.8); fresh/held-out.
- [email-triage.md](email-triage.md) — authored **agentic** support set (answer-from-KB vs escalate); `agentic` rollout + Copilot user-sim; fresh/held-out.
- [home-automation.md](home-automation.md) — authored **agentic** lighthouse set (v0.4, 19 scenarios; act/confirm/refuse/ground over a device world); `agentic` rollout, deterministic state/policy scoring; fresh/held-out.
