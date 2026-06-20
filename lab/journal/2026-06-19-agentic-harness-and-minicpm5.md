# 2026-06-19 — Agentic harness: native tool-calling, tool sets, home-automation, MiniCPM5

A long build-and-evaluate day. Arc: make the agentic harness fair and general,
add the lighthouse benchmark, evaluate MiniCPM5-1B on two axes, and adopt a
commit-as-you-go + background cross-model review workflow.

## What got built

1. **Native tool-calling mode** (`--tool-protocol native`, commit `bc5ec38`). The
   agentic harness now drives tools two ways: `prompt` (one JSON action per step,
   model-agnostic) and `native` (provider function-calling — Ollama `/api/chat`
   `tools` or OpenAI `tools`, reading `message.tool_calls`). Clients gained a
   normalized `ToolCall` + `tool_result_message`. This gives thinking/XML-tool
   models a fair footing instead of being penalized by prompt-mode JSON.

2. **Tool-set-driven harness + home-automation set** (`6e1b233`). Generalized
   `run_episode` to a `ToolSet` (schemas + per-tool behavior `act|respond|
   respond_terminal` + state + apply-fn + scenario context). Two domains now:
   `support` (email-triage) and `home_automation` — the **lighthouse** use-case
   (`get_status`/`set_device`/`ask`/`say` over a device world; scored on device
   end-state + forbidden-devices-untouched + ask-before-sensitive + tools).

3. **Harness hardening from a gpt-5.5 review** (`c39e68c`). See below.

## Key findings

- **Protocol effect is model- and task-dependent.** qwen3.5:4b: email-triage
  3/5 prompt → **4/5 native** (native won); home-automation **6/6 prompt → 5/6
  native** (prompt won). On the home refuse scenario, native's eagerness to call
  tools made it **over-actuate and fabricate** ("I have disabled the security
  system" with no such tool) — exactly the safety failure that scenario exists to
  catch, and the scorer caught it. Native ≠ strictly better.

- **MiniCPM5-1B is hobbled over Ollama by uncontrollable `<think>`.** Two
  evaluations, same root cause: email-triage **0/5** (`c136a20`) and
  decision-reasoning **0/6** (`8453dfd`). Ollama's Go-template path has no
  `enable_thinking` selection, so the model can neither run clean No-Think nor
  cleanly close its CoT — it runs away into degenerate, repetitive rambles (and at
  temp 0.9, gibberish with leaking `<|fim_middle|>` tokens). **Confounded**, not a
  clean capability verdict — but VibeThinker-3B (also a thinking model, also over
  Ollama) produced parseable answers, so MiniCPM5 degenerates worse. A clean read
  needs a controlled-template path (Transformers/vLLM/SGLang with `enable_thinking`).
  Also: the bare GGUF pull is degenerate; the official Go `TEMPLATE` is required.

- **MiniCPM5 verdict (for now): not usable over Ollama for any task needing a
  crisp final answer.** Tool-use and reasoning both blocked on the same serving
  limitation. The home-agent question for it is parked on a controlled-template run.

## Workflow adopted

Commit-as-you-go + **background cross-model review**: after a step lands, a
read-only **gpt-5.5** audit runs in the background (the
`copilot-cli-background-tasks` skill) while the next step proceeds; then validate/
refute each finding (file:line evidence or push back) and fix the real ones. First
run was high-signal — gpt-5.5 found a real Critical (a silent no-op could pass the
home refuse scenario) plus three Majors; two findings were fair to push back on.
Notes land in `tmp/review-*.md` (gitignored).

## State of play (for the next session)

- **Harness:** 4 scorers (`equivalence`, `code_tests`/Podman, `llm_judge`/opus-4.8,
  `agentic`); agentic = 2 tool sets × 2 protocols. Selftest **58 checks, all pass**
  (`cd lab/benchmarks && python3 -m harness.selftest`).
- **Authored benchmarks:** decision-reasoning, code-basics, email-triage,
  home-automation. Results in `lab/benchmarks/results.csv`.
- **Models tried:** qwen3.5:4b (the workhorse), VibeThinker-3B, MiniCPM5-1B.

## Next steps (priority order)

1. **CLI-tool self-correction benchmark** (user idea, notes in repo memory): real
   CLI tools + a SKILL.md, scored on success-within-N-attempts against real
   stderr in a Podman sandbox. Tests *operational competence* (form a correct
   invocation, read the error, self-correct) vs the current mocked-tool
   *decision/policy* axis. Consider wrapping terminal-bench instead of hand-rolling.
2. **home-automation v0.2:** scenes/routines, multi-step dependencies, ambiguity→ask,
   structured `ask.device` for `require_confirm`, judge-assisted refuse-message content.
3. **qwen3.5:9b baseline** on decision-reasoning (calibrate the judge scale).
4. **MiniCPM5 controlled-template re-test** (Transformers/vLLM/SGLang) — the only
   fair read of its tool-use/reasoning; an 8 GB/Blackwell-from-source stretch.
5. Quant sweep (Q4_K_M vs Q8_0); tau³-bench external cross-check.
