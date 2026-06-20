# Decision-reasoning rubric (v1)

Score a model's response to a real-world **decision scenario**. The response may
include long chain-of-thought (e.g. a `<think>` block); evaluate the **quality of
the decision and the reasoning behind it**, weighting the final recommendation
most. Be strict and calibrated. Do not reward length, hedging, or restating the
prompt. A long ramble with no clear decision should score low.

## Criteria (score each 0-10)

1. **Crux identification** - Does it surface the *real* tradeoff/decision at stake
   (not just restate the scenario)? Names what actually drives the choice.
2. **Reasoning quality** - Logically sound, considers second-order consequences,
   no fallacies or hand-waving. The conclusion follows from the analysis.
3. **Handles uncertainty & constraints** - States key assumptions, flags missing
   information, weighs risks/downside, respects the stated constraints.
4. **Decisiveness & actionability** - Commits to a clear, specific recommendation
   (not "it depends" with no call). Says what to actually do.
5. **Practical judgment** - The recommendation is sensible and realistic for the
   situation; a seasoned operator would respect it.

## Output (return ONLY this JSON)

```json
{
  "score": <overall 0-10, holistic - NOT a mean>,
  "per_criterion": {
    "crux_identification": <0-10>,
    "reasoning_quality": <0-10>,
    "handles_uncertainty": <0-10>,
    "decisiveness": <0-10>,
    "practical_judgment": <0-10>
  },
  "rationale": "<one specific sentence citing the response>"
}
```

The overall `score` is holistic: a response with no clear decision, or whose
recommendation contradicts its own analysis, should score low even if individual
parts look fine. A crisp, well-reasoned, decisive answer scores high.

**Under-specified or "trap" scenarios (v0.2):** some scenarios are deliberately
under-specified or carry a tempting-but-wrong obvious answer (e.g. artificial
urgency, a shiny unsigned deal, an unethical shortcut). Reward responses that name
the missing information, ask the right diagnostic question, or resist the bait and
explain why; penalize confidently committing to the tempting wrong option or
inventing facts to resolve the ambiguity. Decisiveness still matters - a good answer
commits to a sensible course (which may be "diagnose X before acting"), it does not
hide in "it depends."
