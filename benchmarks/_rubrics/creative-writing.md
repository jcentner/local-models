# Creative-writing rubric (v1)

Reusable rubric for `llm_judge` creative-writing benchmarks. Reference it from a
benchmark's `rubric.md` (or copy + adapt). The judge scores each criterion 0-10
and returns JSON; the harness records the judge model+version with the result.

> Judging guidance: be strict and calibrated. Do **not** reward length,
> verbosity, or flattery. Penalize generic "AI voice", cliché, and hedging.
> Compare against what a skilled human writer would produce for the same brief.

## Criteria (score each 0-10)

1. **Instruction adherence** — Did it satisfy the brief's explicit constraints
   (form, length, POV, required elements, tone)? Missing a hard constraint caps
   this low regardless of prose quality.
2. **Voice & originality** — Distinct, intentional voice; fresh imagery and
   phrasing. Penalize stock openings ("In a world where..."), filler, and
   recognizable LLM slop.
3. **Coherence & structure** — Internally consistent; deliberate arc or shape;
   no contradictions, no aimless drift.
4. **Craft** — Sentence-level control: rhythm, word choice, concrete detail,
   showing vs telling. Penalize purple prose and padding equally.
5. **Engagement** — Would a discerning reader keep reading? Does it land its
   intended effect (tension, humor, poignancy)?

## Output (the judge returns this JSON)

```json
{
  "score": <overall 0-10, holistic — NOT a mean>,
  "per_criterion": {
    "instruction_adherence": <0-10>,
    "voice_originality": <0-10>,
    "coherence_structure": <0-10>,
    "craft": <0-10>,
    "engagement": <0-10>
  },
  "rationale": "<one specific sentence citing the text>"
}
```

The overall `score` is a holistic judgement, not an average — a piece that fails
a hard constraint or reads as generic slop should score low even if individual
criteria look fine.

## Notes
- **Prefer pairwise comparison** against a reference answer when you can (less
  judge-variance than absolute 0-10). For pairwise, adapt the prompt to "which of
  A/B better satisfies the brief, and why" and score win/loss/tie.
- **Pin the judge** (model + version + this rubric version) in the result row;
  creative-writing scores only compare within the same judge config.
- A single judge is noisy. For higher confidence, average 2-3 judgements or use a
  small panel (e.g. opus-4.8 + gpt-5.5) and record each.
