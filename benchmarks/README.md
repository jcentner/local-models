# benchmarks/ — authored custom datasets

Version-controlled, **hand-authored** benchmark datasets — the fresh, held-out
evals we build for our own use-cases (the antidote to public-benchmark
contamination). Public benchmarks we merely *run* are wrapped by the
[harness](../lab/benchmarks/harness/README.md) and documented in
[wiki/benchmarks/](../wiki/benchmarks/README.md); they don't live here.

## Layout (one folder per benchmark)

```
benchmarks/<name>/
  README.md       provenance, design rationale, what it measures, critic sign-off
  prompts.jsonl   one JSON object per line: {"id", "prompt", "meta": {...}}
  answer_key.jsonl   {"id", "answer"|"tests"|"rubric_ref"} — SEPARATE from prompts
  rubric.md       for LLM-judged (open-ended) benchmarks
```

The matching human-readable page is `wiki/benchmarks/<name>.md` (definition,
scoring, reference scores, contamination status). This folder holds the *data*.

## Answer-key hygiene (important)

- **Keep the answer key in a separate file from the prompts.** The harness loads
  prompts and keys independently and never sends the key to the model under test.
- **Never paste an answer key into model context** except through the scoring
  step. Leaking keys contaminates your own eval (and any future fine-tune).
- For LLM-judged benchmarks, the rubric *may* be shown to the judge but **not** to
  the model under test.
- **Critic exception (`/author-benchmark`):** the design-review critic (gpt-5.5 /
  opus-4.8) *may* see answer keys to check verifiability and difficulty. That is an
  explicit, recorded choice - the benchmark's README logs which critic model/
  provider saw the keys and when. Keys remain held out from the local models under
  test; they are only exposed to that one critic path for QA.

## Scoring method per benchmark

Declared in `wiki/benchmarks/<name>.md` and consumed by the harness:
- `equivalence` — short-answer/numeric matching (sympy + normalizer)
- `code_tests` — execute candidate against `tests` (gated; best-effort local exec today, Podman mode coming)
- `llm_judge` — rubric-scored by a **frontier** judge (claude-opus-4.8 via Copilot CLI; never a local small model)

## Creating one

Use `/author-benchmark <scenario>` — it interviews you, drafts prompts + key,
runs a gpt-5.5/opus-4.8 critic loop against a rubric, and writes both this folder
and the wiki page. Don't hand-create unless you want to; the prompt enforces the
verifiability gate and provenance.
