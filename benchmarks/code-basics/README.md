# code-basics (v0.1)

A small, hand-authored set of **Python function-implementation** tasks to validate
the `code_tests` path (sandboxed execution against hidden tests). 4 items, scored
by running the candidate against `assert` tests in a locked-down **Podman**
container.

- **Measures:** basic algorithmic coding (running max, bracket balancing, interval
  merge, word count). Smoke/validation set, not a serious coding eval.
- **Scoring:** `code_tests` - the harness strips the code fence, appends the tests,
  and runs it in a container (`--network none`, read-only rootfs, resource caps).
- **Provenance:** authored 2026-06-19; original task wordings.
- **Contamination:** the *tasks* are common patterns (low novelty); fine for a
  plumbing test, not for measuring real coding ability. Use evalplus/LiveCodeBench
  for that.

Run it (Podman sandbox required):

```bash
cd lab/benchmarks
python3 -m harness.run --benchmark ../../benchmarks/code-basics \
  --model qwen3.5:4b --code-sandbox podman --temperature 0.0 --num-ctx 8192 --seed 0
```
