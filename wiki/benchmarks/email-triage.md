---
title: email-triage (authored)
tags: [benchmark, agentic, tool-use, triage, authored, fresh]
updated: 2026-06-20
status: authored
---

# email-triage (authored)

A lightweight **tau-bench-style agentic** benchmark: a support-email agent (the
model under test) must, per scenario, **answer from a knowledge base**, or
**escalate to a human** - the core *act / ask / decline* judgment a home-agent
needs. Model-agnostic: a prompt-mode JSON tool protocol means any Ollama tag or
API model runs without native tool-calling.

## What it measures
Does the agent take the **right terminal action** (reply vs escalate), **search
the KB before answering**, and avoid **over-escalating** or **fabricating** facts
the KB doesn't contain.

## Format
[`benchmarks/email-triage/`](../../benchmarks/email-triage/README.md): 5 scenarios
(v0.1). Each item's `meta` carries a `persona` (the user-sim's hidden goal), a
`policy`, and a small `kb`. The answer key is
`{expected_terminal, required_tools, forbidden_tools}` - held out from the agent.

## Scoring
`agentic` (support branch) - **deterministic** state/policy checks, no LLM judge:
terminal action matches `expected_terminal` (reply|escalate), `required_tools` were
used, `forbidden_tools` were not. See
[scorers/agentic.py](../../lab/benchmarks/harness/scorers/agentic.py).
- **Tools (mocked):** `search_kb(query)`, `reply(text)`, `escalate(reason)`.
- **User-simulator:** the **Copilot CLI** (a frontier model) plays the customer
  with a hidden goal (`--user-model`, default `claude-opus-4.8`) - the same
  mechanism as the judge. The agent never sees the persona.
- **Tool protocol (`--tool-protocol`):** `prompt` (default, model-agnostic) or
  `native` (provider function-calling - a fair footing for thinking/XML-tool models).
- Runs default to **`--k 3`**; report **`pass^k`** (reliability) next to
  `observed_pass@k` ([eval-reliability](../concepts/eval-reliability.md)).

## Reference scores
- [qwen3.5:4b](../models/) (2026-06-19, v0.1, k=1): **4/5 native** · **3/5 prompt**.
  Native correctly escalates the refund (e2) that prompt-mode flubbed; both miss e5
  (fabricated "we don't ship to Antarctica" instead of escalating an unknown) - a
  real policy-adherence failure the scorer correctly fails.
- [MiniCPM5-1B](../models/minicpm5-1b.md) (2026-06-20, SGLang, native): **2/5**.
  Its 0/5 over Ollama was a serving artifact (uncontrollable `<think>`,
  tool-blind template); a controlled template lifted it to 2/5.

> k=1 reference scores predate the multi-pass default; re-run at `--k 3` to get
> `pass^k` reliability (small models flake on these).

## Contamination / freshness
**Fresh** - authored 2026-06-19, original scenarios, not from any public set.

## Relevant model-types
Tool-using assistants / agents - the act-vs-escalate skill a home-agent and a
support bot both need. A good **negative control** for narrow specialists.

## Gotchas
- The user-sim costs ~frontier-model calls per turn; `--k 3` triples that.
- Run the agent with `--no-think` (Ollama) + a modest `--num-predict` (actions are
  short JSON); thinking models can truncate before emitting an action.
- e5 is the discriminator: an unknown not in the KB must be **escalated**, not
  answered from invention.

## See also
- [home-automation](home-automation.md) - the sibling agentic set (device world).
- [benchmarks/README](README.md) · [eval-reliability](../concepts/eval-reliability.md) · [bfcl](bfcl.md) (the rigid external reference).
