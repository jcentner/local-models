---
mode: agent
description: Recommend relevant benchmarks for a documented model, estimate cost, then run them via the harness and record results.
---

# /benchmark — run benchmarks against a model

The model to benchmark is whatever I name after the command (e.g.
`/benchmark vibethinker-3b`, an Ollama tag, an API model ref, or a slug). Call it
`${input:model}`.

Read the benchmark system first: [wiki/benchmarks/README.md](../../wiki/benchmarks/README.md).
Honor the methodology there (pass@k, pinned config, contamination, sandboxing,
cost awareness). Results are **per-environment** (per-machine for local; per-provider
+ per-date for API).

## 1. Load context
- Read the model's `wiki/models/<slug>.md` - especially **what it's for / not for**,
  recommended **sampling** (temp/top_p/top_k) and **context** needs, and quant.
- List documented benchmarks from [wiki/benchmarks/](../../wiki/benchmarks/) and
  any authored datasets in [benchmarks/](../../benchmarks/).
- Confirm the model is runnable: **local** = pulled in `ollama list` (if not, say
  so - don't pull without my go-ahead); **API** = an OpenAI-compatible endpoint +
  the key in the env var named by `--api-key-env` (never a literal key).

## 2. Recommend (with reasoning)
Propose which benchmarks to run and why, ranked by **relevance to this model's
declared purpose** and to the priority use-cases (decision-making, agentic/triage,
coding, then math/reasoning - aligned with the home-automation vision). Call out:
- Strong fits (matches the model's specialty).
- **Negative controls** worth running (e.g. a general-knowledge or tool-use eval
  on a math specialist - expected to be weak, confirms the specialty).
- **Contamination caveats** per benchmark (prefer fresh/held-out where it matters;
  cross-check published claims on contamination-resistant sets).

## 3. Estimate cost before running
For the proposed set, estimate token volume and rough cost: **local** = wall-clock
on this machine (8 GB GPU is memory-bandwidth bound; long reasoning traces x pass@k
can be hours); **API** = dollars (pass `--price-in/--price-out` so the run records
`cost_usd`). Give a **quick subset** vs **full run** option. Then **ask me** to
confirm the set, k, and sampling via a short question
(`vscode_askQuestions`) - don't start a long run unprompted.

## 4. Run
Use the harness ([lab/benchmarks/harness](../../lab/benchmarks/harness/README.md)):

```bash
cd lab/benchmarks
# local (Ollama):
python3 -m harness.run --benchmark ../../benchmarks/<name> --model <tag> \
  --base-model <id> --k <k> --temperature <t> --top-p <p> --top-k <tk> --num-ctx <ctx> --seed <s>
# API (OpenAI-compatible, e.g. Z.AI GLM):
python3 -m harness.run --benchmark ../../benchmarks/<name> --model <api-model> \
  --base-model <id> --provider openai-compatible --base-url <https://.../v1> --api-key-env <ENV_VAR> \
  --price-in <usd_per_1M> --price-out <usd_per_1M> --k <k> --temperature <t>
```

- Pass `--base-model <id>` so results group across config/serving variants. Use the
  model's `wiki/models/<id>.md` slug; **required when `--model` is a config-alias
  label** (e.g. `--model g4v2-A-Q3KM-f16-ngl99 --base-model gemma-4-12b-agentic-fable5`,
  or both MiniCPM5 serving labels → `--base-model minicpm5-1b`). Defaults to `--model`
  when omitted (fine for plain Ollama tags like `qwen3.5:4b`).

- Use the model's **recommended sampling** from its page (e.g. VibeThinker = temp
  1.0, top_p 0.95, top_k 0); for deterministic suites use temp 0.
- Set `--num-ctx` large enough for long-CoT models (avoid mid-thought truncation).
- For standard public suites that have an upstream framework (HumanEval+/MBPP+ via
  **evalplus**, broad coverage via **lm-eval-harness**), run that framework against
  Ollama's `:11434/v1` endpoint per the benchmark's wiki page - don't reimplement.
  Record results in the same `results.csv` schema.
- For `llm_judge` (creative-writing/reasoning) benchmarks the harness judge
  is a **frontier model via Copilot CLI** - `--judge-model` defaults to
  `claude-opus-4.8` (use `gpt-5.5` for a second opinion). **Never a local small
  model.** The judge config is recorded automatically; you may also drive a
  subagent judge for interactive runs.
- For `agentic` (tool-use) benchmarks the harness runs a model-agnostic rollout:
  the agent under test + a **Copilot-CLI user-simulator** (`--user-model`, default
  `claude-opus-4.8`) over mocked tools, scored on terminal action + tool policy.
  Use `--no-think` for thinking models (short JSON actions). The flexible
  alternative to registered-model benchmarks like BFCL.
- **Code execution is gated.** Run `code_tests` with `--code-sandbox podman`
  (recommended - locked-down container) or `local-unsafe` (host exec, opt-in). For
  thinking models add `--no-think` so CoT doesn't eat the token budget before the
  code. Prefer an upstream runner (evalplus) for public coding suites. Never run
  model-written code outside the gate.

## 5. Record
- The harness appends a row to [lab/benchmarks/results.csv](../../lab/benchmarks/README.md)
  (raw output in git-ignored `runs/`). Verify the row; add any missing fields
  (quant, VRAM from `ollama ps`, tok/s).
- Create/append `lab/experiments/<YYYY-MM-DD-slug>/README.md` with the run
  (hypothesis -> method -> result -> learnings) and the **per-environment** verdict.
- Update the model page's results/verdict link and append a
  `## [YYYY-MM-DD] bench | <model> on <benchmarks>` line to [wiki/log.md](../../wiki/log.md).

## 6. Report back
Lead with the scores in context (vs published claims, vs other models in the
wiki), the cost it took, what it means for this model on this machine, and any
follow-up (quant sweep, a fresher/contamination-resistant benchmark, or an
`/author-benchmark` for a gap the public sets don't cover).
