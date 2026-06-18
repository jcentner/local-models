---
mode: agent
description: Interactively author a fresh, held-out custom benchmark for a scenario, with a gpt-5.5/opus-4.8 critic loop, then wire it into the harness.
---

# /author-benchmark — create a custom, held-out benchmark

The scenario/use-case is whatever I name after the command (e.g.
`/author-benchmark "tool-use: multi-step calendar scheduling"`,
`/author-benchmark "noir flash fiction under 200 words"`). Call it
`${input:scenario}`.

Goal: a **fresh, contamination-resistant** benchmark for something the public
sets don't cover. Read [wiki/benchmarks/README.md](../../wiki/benchmarks/README.md)
first. The output is a `benchmarks/<name>/` dataset + a `wiki/benchmarks/<name>.md`
page, wired into the [harness](../../lab/benchmarks/harness/README.md).

## 1. Interview me (don't skip — design before drafting)
Ask a focused set of questions (`vscode_askQuestions`):
- **Capability under test** — what exactly are we measuring? (one sentence)
- **Scoring method** — `equivalence` / `code_tests` / `llm_judge`? This is the
  **gate**: if there's no reliable way to verify an answer, redesign the scenario
  until there is. State how each item will be scored *before* writing items.
- Format (input shape, output shape, length), difficulty target + spread, number
  of items, any tools/environment needed (for agentic).
- For `llm_judge`: which rubric (reuse/adapt
  [creative-writing](../../benchmarks/_rubrics/creative-writing.md) or write a new
  one), and the judge model (opus-4.8 / gpt-5.5).

## 2. Draft
Write candidate items: `prompts.jsonl` (id + prompt) and the **separate**
`answer_key.jsonl` (equivalence: `answer`; code_tests: `tests`; llm_judge: rubric
in `rubric.md`). Make items **fresh** — original wording/scenarios, not copies of
known public items. Keep the answer key out of the prompts.

## 3. Critic loop (generate -> critique -> revise)
Spawn a subagent critic via `runSubagent` on **gpt-5.5** (and optionally a second
pass on **opus-4.8** — both are available). Give it the drafted items + keys and
this rubric; have it score each item and the set:
- **Unambiguous?** Exactly one defensible interpretation.
- **Machine-verifiable?** The declared scoring method actually works for this item.
  (Fail -> the item or the scoring must change.)
- **Difficulty calibrated?** Not trivial, not impossible; spread across the set.
- **Contamination-resistant?** Not copy-pasteable from a known public set.
- **Construct validity?** Measures the claimed capability, not a proxy.
- **Fair to model types?** Doesn't smuggle in an out-of-scope requirement.

Have the critic return per-item verdicts + concrete fixes. **Revise and re-run the
critic until it passes** (or I explicitly accept documented limitations). Don't
rubber-stamp a single pass. Record the final critic sign-off (model + version +
date) for the page.

## 4. Verify it runs
Dry-run the dataset through the harness to confirm it loads and scores:
```bash
cd lab/benchmarks
python3 -m harness.run --benchmark ../../benchmarks/<name> --model <tag> --dry-run
```
For `equivalence`/`code_tests`, sanity-check the scorer against a known-good and
known-bad sample answer.

## 5. Write it down
- Save `benchmarks/<name>/` (bench.json, prompts.jsonl, answer_key.jsonl,
  rubric.md if judged, README with provenance + **critic sign-off**). Answer key
  separate; never paste it into model context except via the harness.
- Write `wiki/benchmarks/<name>.md` (definition, scoring, **contamination = fresh/
  authored**, relevant model-types, how to run). Mark `status: authored`.
- Add lines to [wiki/index.md](../../wiki/index.md) (## Benchmarks) and
  "Documented benchmarks" in the [overview](../../wiki/benchmarks/README.md).
- Append `## [YYYY-MM-DD] note | authored <name> benchmark` to [wiki/log.md](../../wiki/log.md).

## 6. Report back
Summarize what it measures, how it's scored, why it's contamination-resistant,
the critic's final verdict, and the exact `/benchmark` command to run it. Suggest
which wiki models to run it against first.
