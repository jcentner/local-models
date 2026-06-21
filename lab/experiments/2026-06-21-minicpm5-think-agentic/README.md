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

| Benchmark | mode | observed_pass@3 | pass^3 | avg | flaky | tok/s |
|---|---|---|---|---|---|---|
| home-automation **v0.4** | **Think** | **0.632** | **0.210** | 0.404 | 8/19 | 137.8 |
| email-triage **v0.3** | **Think** | **0.833** | **0.333** | 0.611 | 6/12 | 143.9 |
| email-triage v0.2 (prior) | No-Think | 0.917 | 0.417 | 0.694 | 6/12 | — |

Both rows in [results.csv](../../benchmarks/results.csv) (`think=on`,
`judge=usersim:copilot:gpt-5.5:native+msgjudge:gpt-5.5`). Local SGLang inference =
**$0**; cost was Copilot premium requests (gpt-5.5 user-sim + message judge).

### The headline: Think mode makes a 1B *narrate instead of act*

The dominant failure is the **`_no_tool` no-op** — the model writes natural-language
narration of its intent into the answer channel instead of emitting the tool call:

- home-automation: **268 of 530 agent steps (51%) were `_no_tool` prose** — and
  **0** of them contained unparsed tool markup (verified by scanning for
  `<function`/`{"name":`/`set_device(`), so this is **genuine model behaviour, not
  a parser miss**.
- email-triage: **63 of 166 steps (38%)** `_no_tool`.

Representative `_no_tool` content: *"I need to clarify which specific light you
want to turn on…"*, *"I don't have a tool to place orders…"*, *"I'll use the ask
tool to clarify…"* — the model **describes** the action rather than **calling** the
tool. The CoT appears to leak its deliberation into `content` as prose, suppressing
the actual `<function>` emission.

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

- **Thinking-as-default is the wrong default for this 1B model on agentic tool-use.**
  Think mode did **not** improve email-triage (0.833 / pass^3 0.333 vs the prior
  No-Think 0.917 / 0.417) and the mechanism actively hurts: half the
  home-automation steps became prose no-ops. **Recommend `--no-think` for MiniCPM5
  agentic runs.** (Caveat: ET is v0.3-think vs v0.2-no-think — version + the new
  `--judge-messages` layer differ, so it's not a pure A/B; the *mechanism* finding
  is clean regardless.)
- **First HA v0.4 datapoint for MiniCPM5: pass^3 0.210** — weak. Even with a
  decent best-of-3 ceiling (0.632), it lands all three only ~21% of the time. The
  v0.4 redesign (grounding h5, compound double-confirm h19, `say`-required refuses)
  is harder than the v0.1 world where it scored 7/12.
- The earlier "decent tool-executor (7/12)" read holds for the *easy* act/ask/
  read-only items; the v0.4 grounding/refuse/compound items expose that it
  **narrates** rather than reliably acting through the tool interface.
- **Clean follow-up A/B:** run **home-automation v0.4 + email-triage v0.3 in
  No-Think** (same v0.4/v0.3 + `--judge-messages`) to isolate the think axis
  without the version confound. Strong prior: No-Think wins.

## Reproducibility notes

- Smoke first: `enable_thinking=true` over `/v1/chat/completions` returns clean
  content (CoT routed to `reasoning_content` by the deepseek-r1 parser).
- `SGLANG_KEY=local` is a throwaway value — the localhost shim needs no real key;
  the var only satisfies `--api-key-env`.
- Raw episodes (gitignored): `lab/benchmarks/runs/home-automation-openbmb_MiniCPM5-1B-20260621-123253.jsonl`,
  `email-triage-openbmb_MiniCPM5-1B-20260621-125552.jsonl`.
