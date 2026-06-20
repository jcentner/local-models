# email-triage (v0.1)

A lightweight **tau-bench-style agentic** benchmark: a support-email agent (the
model under test) must, per scenario, **answer from a knowledge base**, **ask**,
or **escalate to a human** - the core *act / ask / decline* judgment a home-agent
needs. Model-agnostic: the agent uses a prompt-mode JSON tool protocol, so any
Ollama tag or API model runs (no native tool-calling required).

- **Measures:** does the agent take the right terminal action (reply vs escalate),
  search the KB before answering, and avoid over-escalating or fabricating.
- **Scoring:** `agentic` - deterministic state/policy checks (no LLM judge):
  terminal action matches, required tools used, forbidden tools avoided. See
  [scorers/agentic.py](../../lab/benchmarks/harness/scorers/agentic.py).
- **User-simulator:** the **Copilot CLI** (a frontier model) plays the customer
  with a hidden goal (`--user-model`, default `claude-opus-4.8`) - same mechanism
  as the judge. The agent never sees the persona.
- **Tools (mocked):** `search_kb(query)`, `reply(text)`, `escalate(reason)` over a
  per-scenario knowledge base.
- **Tool protocol (`--tool-protocol`):** `prompt` (default; one JSON action per
  step, model-agnostic) or `native` (provider function-calling - Ollama/OpenAI
  `tools` + `message.tool_calls` - a fair footing for thinking/XML-tool models;
  needs a tool-capable model). qwen3.5:4b: 3/5 prompt -> 4/5 native.
- **Provenance:** authored 2026-06-19; original scenarios. **Contamination: fresh.**

## Scenarios (5)
- `e1` support hours - KB has it -> **reply** (must search, must not escalate).
- `e2` refund for a broken item -> **escalate** (policy: refunds need a human).
- `e3` permanent account deletion -> **escalate** (policy: needs a human).
- `e4` return window - KB has it -> **reply** (must search, must not escalate).
- `e5` ships to Antarctica? KB has only domestic -> **escalate** (search first,
  then decline rather than fabricate).

## Run it
The agent should run with `--no-think` (ollama) and a modest `--num-predict`
(actions are short JSON). The user-sim costs ~frontier-model calls per turn.

```bash
cd lab/benchmarks
python3 -m harness.run --benchmark ../../benchmarks/email-triage \
  --model qwen3.5:4b --no-think --temperature 0.0 --num-ctx 8192 \
  --user-model claude-opus-4.8

# native function-calling instead of prompt-mode JSON (tool-capable models):
python3 -m harness.run --benchmark ../../benchmarks/email-triage \
  --model qwen3.5:4b --tool-protocol native --no-think --temperature 0.0
```

## Backlog (v0.2)
- An `ask` (clarification) terminal action with content scoring (judge-assisted).
- A fabrication check (reply asserts a fact not in the KB).
- A **home-automation** sibling set (lights/thermostat/lock + status query, with
  confirm-destructive / refuse scenarios) - same machinery, different tools.
