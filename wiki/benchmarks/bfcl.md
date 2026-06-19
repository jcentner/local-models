---
title: BFCL (Berkeley Function-Calling Leaderboard)
tags: [benchmark, tool-use, agentic, wrapped]
updated: 2026-06-19
status: reference
---

# BFCL (Berkeley Function-Calling Leaderboard)

The standard executable benchmark for **tool/function calling** — the core skill a
local **home-automation agent** needs. We **wrap** the upstream
[`bfcl-eval`](https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard)
package rather than reimplementing it. Current installed version: `bfcl-eval
2026.3.23`, datasets tagged `BFCL_v4`.

> **Status: deprioritized (reference, not our daily agentic driver).** BFCL only
> runs **registered models** — it ships a per-model handler that formats tool defs
> and parses each model's tool-call dialect, because tool-call output isn't
> standardized. That makes it precise and leaderboard-comparable, but it
> **structurally lags the frontier**: a brand-new small model (e.g. MiniCPM-5,
> Qwen3.5-4B) can't be scored until someone writes its handler. For a fast-moving
> space we instead use a **model-agnostic** agentic eval (a lightweight
> tau-bench-style scorer in our harness, Copilot-CLI user-simulator; tau³-bench as
> the external cross-check). Keep BFCL for comparing against published numbers. The
> local `~/.venvs/bfcl` was removed after this finding; reinstall via the recipe
> below if needed.

Most relevant to our [vision](../README.md#vision): its hardest categories test the
**act-vs-ask-vs-do-nothing** judgment — *irrelevance* (don't call a tool that
doesn't fit), *missing parameter* (ask instead of guessing), *missing function*
(recognize the toolset is insufficient). That's exactly what a home agent must get
right before it acts on the physical world.

## What it measures
Whether a model, given a set of tool/function definitions and a user request,
emits the **correct call(s)** (right function, right arguments) — or correctly
**declines** to call. Categories (exact ids from `bfcl test-categories`):

- **Non-live** (expert-curated, AST-scored): `simple_python`, `simple_java`,
  `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`.
- **Live** (user-contributed, real prompts): `live_simple`, `live_multiple`,
  `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`.
- **Multi-turn** (stateful): `multi_turn_base`, `multi_turn_miss_func`,
  `multi_turn_miss_param`, `multi_turn_long_context`.
- **Agentic** (v4): `memory_*` (kv/vector/rec_sum), `web_search_*`.
- Collections: `single_turn`, `live`, `non_live`, `multi_turn`, `agentic`,
  `all_scoring`, `all` (+ `python`, `non_python`).

## Format
Each entry = a user query + a list of available functions (+ for multi-turn, an
initial backend state). The model is run in **FC mode** (native `tools` API) or
**Prompt mode** (function defs in the system prompt; for models without native
tool calling) — see the model table's suffix `-FC` vs plain.

## Scoring
- **AST match** (non-live single-turn): parse the call, check function +
  argument structure against the answer.
- **Relevance / irrelevance detection**: did the model (not) call when it
  should(n't).
- **Multi-turn**: **state-based** (compare backend state after each turn) +
  **subset-matched response-based** (the ground-truth minimal call path must be a
  subset of the model's calls) — alternate valid trajectories aren't penalized.
- Metric: per-category accuracy; the leaderboard is a weighted average. We record
  the **subset** scores we run, not a leaderboard-comparable overall.

## Reference scores (orientation, not exact)
Frontier FC models lead; multi-turn is brutal (top models historically well under
50% on the hardest multi-turn categories). Small local models score low,
especially on irrelevance/missing-* and multi-turn. Check the live
[BFCL leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html) for current
numbers rather than trusting a snapshot.

## Contamination / freshness
Public and heavily targeted, so single-turn AST categories carry leakage risk.
The **live**, **multi-turn**, and **v4 agentic** (web search / memory) categories
are human-curated and harder to game; prefer those for a contamination-resistant
signal. Treat a high single-turn score as necessary, not sufficient.

## Relevant model-types
Tool-using / agentic models — and **directly** the home-agent decision skill.
[VibeThinker-3B](../models/vibethinker-3b.md) is a clean **negative control**
(explicitly not trained for tool use). General instruct models (qwen3.x) are the
realistic baselines.

## How to run (wrap bfcl-eval)
Verified setup on this box (2026-06-19):

```bash
python3 -m venv ~/.venvs/bfcl && ~/.venvs/bfcl/bin/pip install bfcl-eval
# packaging gap in 2026.3.23: qwen_agent imports soundfile transitively
~/.venvs/bfcl/bin/pip install soundfile
export PATH="$HOME/.venvs/bfcl/bin:$PATH"
export BFCL_PROJECT_ROOT="$HOME/utils/local-models/lab/benchmarks/runs/bfcl"  # gitignored
bfcl models | head            # list registered models
bfcl test-categories          # list category ids
# two phases: generate -> evaluate. Subset with --run-ids / --partial-eval.
bfcl generate --model <MODEL> --test-category irrelevance,live_multiple --skip-server-setup
bfcl evaluate --model <MODEL> --test-category irrelevance,live_multiple --partial-eval
```

**Picking `<MODEL>` is the crux on an 8 GB box.** BFCL models are either:
- **API** (`glm-4.6-FC`, `qwen3-4b-FC`, `gpt-*-FC`, ...): set the provider key in
  `$BFCL_PROJECT_ROOT/.env`. Cheap, meaningful, and the recommended route here —
  it doubles as a candidate home-agent brain. (Our harness records cost; BFCL does
  not — note the API spend by hand.)
- **Self-hosted `💻`** (`Qwen/Qwen3-4B-Instruct-2507`, ...): by default BFCL spins
  up **vLLM/sglang** (the box's known stretch — sglang needs SM80+, vLLM on
  Blackwell sm_120 needs CUDA >= 12.8). With `--skip-server-setup` it instead hits
  an existing OpenAI-compatible endpoint at `LOCAL_SERVER_ENDPOINT:PORT`.

**KEY FINDING — there is no generic "Ollama tag" handler.** With
`--skip-server-setup`, `base_oss_handler.py` loads the model's **HF tokenizer +
config** (downloaded from HF, or `REMOTE_OPENAI_TOKENIZER_PATH`), formats the
prompt itself, and sends BFCL's **exact registered model name** to the endpoint.
So to run a local model via Ollama's `:11434/v1`, Ollama must serve the model
under that **exact registered name** (e.g. `Qwen/Qwen3-4B-Instruct-2507`) with a
matching tokenizer — an arbitrary tag like `qwen3.5:4b` is not a registered model
and will not work. Practical local route: `ollama pull` the matching GGUF, alias
it to the registered name, set `LOCAL_SERVER_ENDPOINT=localhost` /
`LOCAL_SERVER_PORT=11434`, then `--skip-server-setup`.

Record any subset run in [lab/benchmarks/results.csv](../../lab/benchmarks/README.md)
by hand (BFCL writes its own `score/` CSVs under `$BFCL_PROJECT_ROOT`; fold the
category accuracy into our schema as `scoring=tool_calls`, noting the subset).

## Gotchas
- Install **`bfcl-eval`**, NOT `bfcl` (an unrelated PyPI package).
- 2026.3.23 needs a manual `pip install soundfile` (transitive `qwen_agent` import).
- `--skip-server-setup` couples to the **registered model name + HF tokenizer** —
  no arbitrary-Ollama-model path.
- Default `--temperature 0.001`; default `--test-category all` (huge) — always
  scope with explicit categories + `--run-ids`/`--partial-eval`.
- Subset scores are **not** leaderboard-comparable; say which categories + ids.
- BFCL records no cost; for API runs note the spend manually.
