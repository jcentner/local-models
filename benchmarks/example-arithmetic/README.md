# example-arithmetic (v0.1)

A tiny, hand-authored arithmetic word-problem set. **Purpose: a format reference
and harness smoke test**, not a serious eval — 3 items, fresh (not from any public
set), scored by deterministic numeric equivalence.

- **Measures:** basic multi-step arithmetic + final-answer formatting (`\boxed{}`).
- **Scoring:** `equivalence` (harness extracts `\boxed{}` / final number, compares numerically).
- **Provenance:** authored 2026-06-18 by hand as the first `benchmarks/<name>/` example.
- **Contamination:** fresh wording; trivial difficulty by design.

Run it:

```bash
cd lab/benchmarks
python3 -m harness.run --benchmark ../../benchmarks/example-arithmetic \
  --model <ollama-tag> --k 1 --temperature 0.0 --num-ctx 8192 --seed 0
```

Real authored benchmarks should be created via `/author-benchmark` (interview +
verifiability gate + critic loop), not by hand like this stub.
