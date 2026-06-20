# decision-reasoning (v0.2)

A fresh, hand-authored set of **real-world decision scenarios** to evaluate a
model as a **decision-maker / reasoner** - judgment under uncertainty, tradeoff
analysis, and decisiveness. Originally built to test VibeThinker-3B *outside* its
declared math/code specialty (a boundary test); v0.2 broadens it into a structured,
sliceable eval.

- **Measures:** decision quality + reasoning on open-ended operational/strategic
  scenarios, across 7 categories and 3 difficulty tiers.
- **Scoring:** `llm_judge` against [rubric.md](rubric.md), judged by a **frontier
  model** (default `claude-opus-4.8` via Copilot CLI - never a local small model).
- **Format:** 21 scenario prompts; the model reasons and ends with a clear
  `Recommendation:`. No answer key (rubric-scored). Each item carries
  `meta.tier` + `meta.category` for `--slice-by`.
- **Provenance:** v0.1 (d1-d6) authored 2026-06-19; v0.2 (d7-d21) added 2026-06-20.
  Original scenarios, not from any public set. **Contamination: fresh.** v0.1 prompt
  text is unchanged, so prior d1-d6 results stay comparable.
- **Difficulty:** deliberately has genuine tradeoffs with no single "correct"
  answer - tests judgment, not recall.

## Structure (21 items)
- **Categories** (`meta.category`, 3 each): prioritization, risk, resource-allocation,
  people, ethics, ambiguous, reversible-vs-irreversible.
- **Tiers** (`meta.tier`): **T1** a defensible best answer exists (d7, d12, d19);
  **T2** a genuine tradeoff, no single right call (the majority); **T3**
  adversarial / under-specified - rewards spotting missing info or resisting a
  tempting-but-wrong option (d8 unsigned-deal, d10 artificial-urgency, d15
  peek-at-competitor, d17 diagnose-before-acting). The v0.1 misreads suggested T3 is
  where small reasoners fail hardest.

> Slice a run by tier or category to make the score diagnostic, e.g.
> `--slice-by tier` / `--slice-by category`. Future expansion should go through
> `/author-benchmark` (interview + verifiability gate + gpt-5.5/opus-4.8 critic loop).

Run it (k defaults to 3 -> reports observed_pass@k AND pass^k reliability; run at
the model's recommended temp, not temp=0):

```bash
cd lab/benchmarks
python3 -m harness.run --benchmark ../../benchmarks/decision-reasoning \
  --model vibethinker-3b --num-ctx 32768 --num-predict 4096 \
  --temperature 1.0 --top-p 0.95 --top-k 0 --judge-model claude-opus-4.8 \
  --slice-by tier
```

## Backlog

v0.2 landed the structured expansion (done): difficulty **tiers** + **categories**
(3 each, 21 total), **trap / under-specified** items (d8/d10/d15/d17), and harness
**`--slice-by`** so the score is diagnostic per group. Remaining:

- Re-author/expand toward ~24-28 via **`/author-benchmark`** (critic loop) rather
  than hand-seeding; have a frontier critic vet each item's tier label and that the
  T3 traps are fair.
- Add a couple more T1 items (only 3 today) so the easy floor is well sampled.
- Consider a paired-comparison report across models on the shared items (see
  [eval-reliability](../../wiki/concepts/eval-reliability.md)).

