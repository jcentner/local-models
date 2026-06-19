# decision-reasoning (v0.1)

A fresh, hand-authored set of **real-world decision scenarios** to evaluate a
model as a **decision-maker / reasoner** - judgment under uncertainty, tradeoff
analysis, and decisiveness. Built specifically to test VibeThinker-3B *outside*
its declared math/code specialty (a boundary test).

- **Measures:** decision quality + reasoning on open-ended operational/strategic
  scenarios (prioritization, risk, resource allocation, hiring, ambiguity).
- **Scoring:** `llm_judge` against [rubric.md](rubric.md), judged by a **frontier
  model** (default `claude-opus-4.8` via Copilot CLI - never a local small model).
- **Format:** 6 scenario prompts; the model reasons and ends with a clear
  `Recommendation:`. No answer key (rubric-scored).
- **Provenance:** authored 2026-06-19 by hand; original scenarios, not from any
  public set. **Contamination: fresh.**
- **Difficulty:** deliberately has genuine tradeoffs with no single "correct"
  answer - tests judgment, not recall.

> Note: this was hand-seeded to reach a first run. Formalize future versions via
> `/author-benchmark` (interview + verifiability gate + gpt-5.5/opus-4.8 critic loop).

Run it:

```bash
cd lab/benchmarks
python3 -m harness.run --benchmark ../../benchmarks/decision-reasoning \
  --model vibethinker-3b --num-ctx 32768 --num-predict 4096 \
  --temperature 1.0 --top-p 0.95 --top-k 0 --judge-model claude-opus-4.8
```
