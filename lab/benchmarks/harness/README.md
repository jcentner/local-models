# lab/benchmarks/harness

A thin, local-first benchmark runner. Samples prompts against a local model
(Ollama) and scores them. It is the engine for our **authored** datasets under
[`benchmarks/<name>/`](../../../benchmarks/README.md); for standard public suites
we wrap the upstream framework instead (see the per-benchmark wiki pages).

## Layout

```
harness/
  client.py            Ollama /api/chat client (sampling + num_ctx + tok/s)
  run.py               CLI: load dataset -> sample k -> score -> results.csv + runs/
  selftest.py          offline test of the scoring core (no model needed)
  scorers/
    equivalence.py     math/numeric answer matching (sympy optional)
    code_exec.py       sandboxed code execution against tests
    llm_judge.py       rubric LLM-judge (pinned judge model)
```

## Dataset format (`benchmarks/<name>/`)

```
bench.json       {"name","version","scoring":equivalence|code_tests|llm_judge,"system"?,"judge"?}
prompts.jsonl    {"id","prompt","meta"?}
answer_key.jsonl equivalence: {"id","answer"} | code_tests: {"id","tests"} | llm_judge: (rubric.md)
rubric.md        for llm_judge benchmarks
```

The answer key is loaded separately and **never sent to the model under test**.

## Run

```bash
cd lab/benchmarks
# verify the scoring core (no model/network):
python3 -m harness.selftest

# dry run (prints config + first prompt, no model call):
python3 -m harness.run --benchmark ../../benchmarks/<name> --model qwen3.5:4b --dry-run

# real run against a pulled Ollama model:
python3 -m harness.run --benchmark ../../benchmarks/<name> \
  --model qwen3.5:4b --k 1 --temperature 0.0 --num-ctx 8192 --seed 0

# observed pass@k for a stochastic reasoning model:
python3 -m harness.run --benchmark ../../benchmarks/<name> \
  --model vibethinker-3b --k 8 --temperature 1.0 --top-p 0.95 --num-ctx 32768

# code_tests is GATED - it must be opted into a sandbox mode:
python3 -m harness.run --benchmark ../../benchmarks/<code-bench> \
  --model qwen3.5:4b --code-sandbox local-unsafe

# llm-judged (open-ended) benchmark with a local judge model:
python3 -m harness.run --benchmark ../../benchmarks/<name> \
  --model <under-test> --judge-model <strong-judge-tag>
```

Datasets live under [`benchmarks/<name>/`](../../../benchmarks/README.md) and are
created with `/author-benchmark`. Output: a row appended to
[`../results.csv`](../README.md) and raw completions under `../runs/` (git-ignored).

## Scoring methods

- **equivalence** — extracts `\boxed{}` / "answer is" / last number, compares
  numerically (sympy if installed). Deterministic.
- **code_tests** — strips code fences, appends the test snippet, runs in a
  subprocess with a timeout + (Linux) CPU/memory rlimits. **This is best-effort,
  NOT real isolation** - it runs as you on the host. It is therefore **gated**:
  the runner refuses `code_tests` unless you pass `--code-sandbox local-unsafe` to
  accept the risk. Prefer an upstream runner (evalplus) for public suites; a
  locked-down Podman mode is the next build (Batch B).
- **observed pass@k** — the runner reports `observed_pass_at_k` = fraction of
  items with >=1 correct sample in k. This is **not** the formal unbiased pass@k
  estimator used on public leaderboards; don't compare the two directly.
- **llm_judge** — a pinned judge model scores the response against `rubric.md`
  and returns JSON. The judge config (model+version+rubric) is recorded with the
  result; LLM-judged scores only compare within the same judge config. For
  highest-quality judging (creative writing), the `/benchmark` and
  `/author-benchmark` prompts can drive a frontier judge (gpt-5.5 / opus-4.8) via
  the agent or a subagent instead of this code path.

## Wrapping upstream frameworks

For HumanEval+/MBPP+ use [evalplus](https://github.com/evalplus/evalplus); for
broad task coverage use [lm-eval-harness](https://github.com/EleutherAI/lm-evaluation-harness)
(both can target Ollama's OpenAI-compatible endpoint on `:11434`). Document the
exact command on the benchmark's wiki page and record results in the same
`results.csv` schema. Don't reimplement these.

## Dependencies

stdlib only for the core. `sympy` optionally improves math equivalence
(`pip install sympy` in a venv). Upstream frameworks (evalplus, lm-eval) install
into a venv per their docs.
