# MiniCPM5-1B — Think-mode agentic suite (home-automation v0.4 + email-triage v0.3)

- Date: 2026-06-21 (run complete — see Result)
- Machine: ASUS ProArt P16 (RTX 5070 Laptop, 8 GB, Blackwell sm_120, WSL2) —
  see [proart-p16](../../../wiki/hardware/proart-p16.md)
- Stack under test: [SGLang](../../../wiki/stacks/sglang.md) container (rootless
  Podman + CDI), `openbmb/MiniCPM5-1B` BF16
- Model: [minicpm5-1b](../../../wiki/models/minicpm5-1b.md)
- Benchmarks: [home-automation v0.4](../../../benchmarks/home-automation/README.md)
  (19 scenarios), [email-triage v0.3](../../../benchmarks/email-triage/README.md)
  (12 scenarios)

## Hypothesis

Per the **thinking-as-default** policy question (user leans "default to thinking,
it likely improves scores"), re-run MiniCPM5's agentic suite with **Think mode on**
(`enable_thinking=true`, temp 0.9 / top_p 0.95) and compare to the prior No-Think
baselines. Prediction to test: does deliberate CoT help a 1B model act/ask/refuse
more reliably, or does the extra reasoning just cost tokens?

This is also the **first home-automation v0.4 run for MiniCPM5** (it had only ever
been scored on the older HA versions and on email-triage).

## Method

SGLang served **without** `--tool-call-parser` (the `minicpm5` parser swallows the
model's `<function>` XML — see the [2026-06-20 experiment](../2026-06-20-minicpm5-sglang-controlled/README.md));
the harness `parse_xml_tool_calls()` fallback recovers native tool calls from
`content`. `--reasoning-parser deepseek-r1` separates the `<think>` CoT into
`reasoning_content`.

```bash
podman run -d --name sglang-minicpm5 --device nvidia.com/gpu=all \
  --security-opt=label=disable --ipc=host -p 30000:30000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface lmsysorg/sglang:latest \
  python3 -m sglang.launch_server --model-path openbmb/MiniCPM5-1B \
  --host 0.0.0.0 --port 30000 --mem-fraction-static 0.7 \
  --context-length 16384 --reasoning-parser deepseek-r1

cd lab/benchmarks
SGLANG_KEY=local python3 -m harness.run \
  --benchmark ../../benchmarks/home-automation --model openbmb/MiniCPM5-1B \
  --base-model minicpm5-1b --provider openai-compatible \
  --base-url http://localhost:30000/v1 --api-key-env SGLANG_KEY \
  --tool-protocol native --think --temperature 0.9 --top-p 0.95 \
  --num-predict 4096 --k 3 --user-model gpt-5.5 \
  --judge-messages --judge-model gpt-5.5
# email-triage: same flags, --benchmark ../../benchmarks/email-triage
```

`--think` sends `chat_template_kwargs.enable_thinking=true`. `--judge-messages`
adds the frontier AND-gate over the deterministic score (recommended for the v0.4
baseline; grades h5/h17/h18 + the email-triage fabrication items). User-sim and
message-judge = **gpt-5.5** (cheaper than the opus default).

## Result

| Benchmark (k=3) | mode | observed_pass@3 | pass^3 | avg | flaky | tok/s |
|---|---|---|---|---|---|---|
| home-automation **v0.4** | **Think** (t0.9) | **0.632** | **0.210** | 0.404 | 8/19 | 137.8 |
| home-automation **v0.4** | **No-Think** (t0.7) | **0.474** | **0.158** | 0.333 | 6/19 | 105.7 |
| email-triage v0.3 | Think (t0.9) | 0.833 | 0.333 | 0.611 | 6/12 | 143.9 |
| email-triage v0.2 (prior) | No-Think (t1.0) | 0.917 | 0.417 | 0.694 | 6/12 | — |

Rows in [results.csv](../../benchmarks/results.csv)
(`judge=usersim:copilot:gpt-5.5:native+msgjudge:gpt-5.5`). Local SGLang inference =
**$0**; cost was Copilot premium requests (gpt-5.5 user-sim + message judge).

**Mixed, task-dependent — no clean think default.** On **home-automation** Think is
modestly ahead (0.632 vs 0.474); on **email-triage** No-Think leads (different
versions). Neither pair is a perfectly controlled A/B (the HA pair differs in
temp/parser/context per each mode's recommended serving — see Serving below), so read
the direction, not the decimals. Either way pass^3 is **0.16–0.21 on home-automation**
— a weak agentic ceiling.

### The dominant failure (both modes): a `_no_tool` flail

The model writes natural-language narration of its intent into the answer channel
instead of emitting the tool call. Step-level counts from the **Think** run (No-Think
flails at least as much — it scored lower and its episodes overflowed 16K context):

- home-automation: **268 of 530 agent steps (51%) were `_no_tool` prose** — and
  **0** of them contained unparsed tool markup (verified by scanning for
  `<function`/`{"name":`/`set_device(`), so this is **genuine model behaviour, not
  a parser miss**.
- email-triage: **63 of 166 steps (38%)** `_no_tool`.

Representative `_no_tool` content: *"I need to clarify which specific light you
want to turn on…"*, *"I don't have a tool to place orders…"*, *"I'll use the ask
tool to clarify…"* — the model **describes** the action rather than **calling** the
tool. It happens **with or without** thinking, so it is a failure to commit to the
`<function>` emission, not a CoT-leak artifact.

### Per-item shape

- **Clean wins (3/3):** h2 (param act), h6 / h11 (read-only status), h8
  (ambiguity→ask); e1 / e3 / e6 / e11.
- **Under-action (narrates, never acts/commits):** h4 over-clarifies an
  *unambiguous* "turn off all the lights" (asks which lights ×7); h5 grounding and
  h10 refuse narrate the decline instead of using the `say` tool
  (`required_any` fails); e7 narrates for 5 steps, never `escalate`s.
- **Confirm-loops:** h17 (disable smoke detector — a safety refuse) asks "are you
  sure?" four times, never refuses or acts → `max_turns`. h19 compound double-
  confirm never completes.
- **Mis-route:** e12 escalates a phone-support question that was answerable from
  the KB (`reply` expected) — over-escalation.

## Learnings / verdict

- **No clean think default — it's task-dependent, and weak either way.** On
  home-automation Think beats No-Think (0.632 / 0.210 vs 0.474 / 0.158); on
  email-triage No-Think leads (0.917 / 0.417 v0.2 vs 0.833 / 0.333 v0.3, different
  versions). This **revises** the first-pass "recommend `--no-think`" call (which
  leaned on email-triage alone): the No-Think HA run came in *lower*, not higher.
- **The `_no_tool` flail is the 1B's agentic ceiling, not a Think artifact.** Both
  modes narrate-instead-of-act and loop get_status→ask→narrate→nudge without
  committing (Think HA 51% of steps; No-Think flails at least as much — it scored
  lower and its episodes overflowed a 16K context). The brief Think CoT helps it
  commit slightly more often on the harder HA set.
- **Home-automation v0.4: pass^3 0.16–0.21** — weak both ways. A decent best-of-3
  ceiling (0.47–0.63) but it lands all three only ~16–21% of the time. The v0.4
  redesign (grounding h5, compound double-confirm h19, `say`-required refuses) is
  harder than the v0.1 world where it scored 7/12; the easy act / read-only /
  ambiguity→ask items still pass.
- **Can it handle the workload?** Mechanically yes — it completes 19×k3 at 32K with
  no crash; qualitatively it's a weak agentic executor at this size.

## Serving + context diagnosis (No-Think)

The No-Think HA run hit two SGLang serving gotchas before it could score:
- **Parser-less server required.** With `--reasoning-parser deepseek-r1`, No-Think
  output lands in `reasoning_content` and `content` is empty → the harness (which
  reads `content`) sees nothing → a false **0/19**. Fix: serve **without** the
  reasoning parser (and without `--tool-call-parser`; the harness
  `parse_xml_tool_calls()` handles tool calls).
- **≥32K context required.** No-Think first crashed at 16K with a 400 (input 13,961
  + 4,096 completion > 16,384). Diagnosed as **accumulation, not a runaway
  generation**: streaming every step (`tmp/h10_loop_probe.py`, `tmp/h10_real_user_probe.py`)
  showed all generations short (`finish=stop`, ≤~330 tok) across ~50 samples incl. a
  faithful gpt-5.5 user-sim replay; the model flails for up to `max_turns×max_steps`
  (≈28) steps and every step is appended to history. Think stayed under 16K only
  because its CoT goes to `reasoning_content` (not re-fed). Email-triage (shorter
  episodes) was fine at 16K.

## Reproducibility notes

- Smoke first: `enable_thinking=true` over `/v1/chat/completions` returns clean
  content (CoT routed to `reasoning_content` by the deepseek-r1 parser).
- `SGLANG_KEY=local` is a throwaway value — the localhost shim needs no real key;
  the var only satisfies `--api-key-env`.
- Raw episodes (gitignored): `lab/benchmarks/runs/home-automation-openbmb_MiniCPM5-1B-20260621-123253.jsonl`,
  `email-triage-openbmb_MiniCPM5-1B-20260621-125552.jsonl`.
