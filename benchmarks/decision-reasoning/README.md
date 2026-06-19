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

## Backlog (v0.2 — come back to this)

v0.1 is a flat 6-item set. Expand it into a structured eval, **built via
`/author-benchmark`** (interview + verifiability gate + gpt-5.5/opus-4.8 critic
loop) rather than hand-seeded:

- **Difficulty tiers** (tag each item `meta.tier`): T1 = a defensible best answer
  exists; T2 = genuine tradeoff, no single right call; T3 = adversarial /
  under-specified — rewards spotting missing info or resisting a tempting-but-wrong
  option. The v0.1 misreads suggest T3 is where models like VibeThinker fail hardest.
- **Categories** (tag `meta.category`): prioritization, risk/uncertainty, resource
  allocation, people/hiring, ethics/stakeholder tradeoffs, ambiguous-information,
  reversible-vs-irreversible. ~3-4 items each → ~20-25 total.
- **Slice results by tier + category** so the score is diagnostic ("strong on
  prioritization, fails under-specified") not just one number. (Harness change:
  aggregate `observed_pass_at_k` per `meta` group.)
- Add a couple of **trap items** with a tempting-but-wrong obvious answer to test
  whether a model resists the bait.

