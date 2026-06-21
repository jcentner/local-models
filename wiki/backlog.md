---
title: Backlog / status board
tags: [backlog, planning, index]
updated: 2026-06-20
---

# Backlog / status board

The single "what's next" view. Each item links to its authoritative page (the
[log](log.md) is the timeline; this is the forward queue). Keep it short — move
detail to the linked experiment/model page, and tick items here as they land.

## Now (in progress)
- *(nothing actively running)* — last completed: the [gemma-4-12B v2 quant sweep](../lab/experiments/2026-06-20-gemma-4-12b-v2-quant-config-sweep/README.md) (**Q3_K_M f16 full-GPU wins**; 11/12 home-automation, 4/4 code-basics, ~32 tok/s).

## Next (queued / staged)
- **Record run-time params in results.csv + raw — esp. think/no-think** (GAP found 2026-06-21, priority pickup): the **think/no-think setting is recorded NOWHERE** — results.csv `sampling` col is only `t=…,top_p=…,top_k=…`; raw jsonl keys are `id/sample_index/result/meta/episode` (agentic) or `…/completion` (generative), no run-params. So runs aren't reproducible on the think axis and **can't be compared**: gemma agentic ran **thinking-ON** (template default — no `--no-think` over llama.cpp `--jinja`), qwen + minicpm agentic ran **`--no-think`** — invisible in the data. Do in one pass:
  - **harness** [run.py](../lab/benchmarks/harness/run.py): the results `row` dict (~L499) + BOTH `raw.write(...)` calls (agentic ~L441, generative ~L468). `args.think` is **tri-state** (None=template/provider default · True · False) → record an *unambiguous effective* value (None is ambiguous: for gemma it meant thinking-on). Idea: `think=on|off|default` (+ provider so `default` is interpretable). Sweep for other uncaptured config while here: think is the gap; `num_ctx`/`num_predict` already columns; protocol + user/judge model live in the `judge` col; consider also `--judge-effort` and (agentic) `--judge-messages`.
  - **results.csv schema**: prefer a real **`think` column** (cleaner + viewer-filterable) → schema **v4**; **back-annotate the ~28 existing rows** from the log/run-cmds (gemma agentic=on; qwen + minicpm agentic=off; qwen code-basics=off `--no-think`; dec-reasoning rows per their cmds). Reuse the `tmp/migrate_results*.py` pattern. (Alt: append `,think=…` into the `sampling` string = no migration but abuses the field + the viewer may split it — not recommended.)
  - **run-viewer** [tools/run-viewer](../tools/run-viewer/): surface `think` in the run header + base→variant comparison matrix, and make it a filter/group key alongside model+benchmark so think-vs-no-think is visible at a glance.
  - **docs**: AGENTS.md (benchmarks "results row records…" line), benchmarks/README + [lab/benchmarks/README](../lab/benchmarks/README.md) (schema), [harness/README](../lab/benchmarks/harness/README.md), [eval-reliability](concepts/eval-reliability.md), the `/benchmark` prompt + benchmark-harness skill if they enumerate recorded fields.
  - **validate**: `cd lab/benchmarks && python3 -m harness.selftest` (151 ALL PASS today) + add a check the recorded think matches the flag; re-point the viewer at the migrated csv.
  - WHY: unblocks a deliberate **"thinking as default" policy** (see Infra item) — once think is recorded, think vs no-think rows become comparable. Raised 2026-06-21.
- **MiniCPM5 agentic suite at k=3 (gpt-5.5 user-sim, XML fallback)** — CONFIRMED runnable: SGLang WITHOUT `--tool-call-parser` (the `minicpm5` parser swallows the XML) + harness `parse_xml_tool_calls()`; `--no-think` works over SGLang. ET v0.2 **no-think** ran 2026-06-21 = **obs@3 0.917 / pass^3 0.417 / flaky 6/12** (capable best-of-3, unreliable) — raw `runs/email-triage-openbmb_MiniCPM5-1B-20260621-085733.jsonl`, **NOT in results.csv** (reverted to avoid an unlabeled-think row before the column lands; promote it then, or re-run). **Pending:** HA v0.3, and the think re-runs once "default to thinking" is set + recorded. SGLang recipe + flags in [the experiment](../lab/experiments/2026-06-20-minicpm5-sglang-controlled/README.md). (Commit hygiene: `wiki/models/minicpm5-1b.md` had parallel-agent uncommitted edits 2026-06-21 — don't clobber.)
- **DONE (2026-06-21) — home-automation refuse scoring resolved via h5 redesign (v0.4).** Investigated the `required_tools:["say"]` complaint against the full prompt/context: the flagged item (h5) was **muddled** — its roster held neither the security system nor a back door, so it tested **grounding**, not safety, and pass/fail hinged on `say`-vs-`ask`. Fix shipped: **h5 → grounding** (`required_any:[[say,ask]]` accepts a decline via either channel without false-failing a grounded ask; `forbidden_device_attempts` blocks substitute actuation) and **h19 → compound double-confirm** (the realistic "disarm my alarm" = confirm, vs h17 life-safety = refuse). h10/h17 keep the strict `say` rule (they're clean). Scorer `required_any` + list-form `judge_message.tool`; selftest 163 ALL PASS; bench v0.4. Commit 9cdd266. **Follow-up: re-baseline all models on HA v0.4 at `--k 3`** (prior h5 scores no longer comparable).
- **[lfm2.5-colbert tool-selection](../lab/experiments/2026-06-20-lfm2.5-colbert-tool-selection/README.md)** — the router-aide eval (N tools → top-k), staged, not run.
- **Re-run [home-automation **v0.2**](../benchmarks/home-automation/README.md)** (12 scenarios) for models scored on v0.1 (the old 6/6·5/6 were v0.1).
- **MiniCPM5 native tool-parser on a newer SGLang build** — `--tool-call-parser minicpm5` is broken in 0.5.13 ([sglang findings](stacks/sglang.md)); current path uses the harness XML fallback.

## Open research questions (from model pages)
- **VibeThinker on its home turf** — competitive coding / LiveCodeBench, sandboxed `code_tests` ([open questions](models/vibethinker-3b.md)). The decision-reasoning result only tested the out-of-domain boundary.
- **VibeThinker quant sensitivity** — Q4_K_M vs Q8_0 on reasoning ([quantization](concepts/quantization.md)).

## Models to consider (future `/new-model`)
- **gemma-4-12B v3** (announced) and the **Qwen3.6-27B** agentic sibling ([v2 page](models/gemma-4-12b-agentic-fable5.md)).

## Infra / maintenance
- **Thinking-as-default policy + tame qwen over-thinking on decision-reasoning** — user leans **"default to thinking, it likely improves scores"**; once think is recorded (see Next) set the policy + re-run for consistency (gemma agentic=thinking already; qwen + minicpm=no-think — confounded). The blocker on qwen: qwen3.5:4b on dec-reasoning v0.2 (thinking ON, `num_predict 8192`) emits **5-7K-token CoT/item** → **~266s/sample** → **~4.6 h for 21×k3** (judge only scores the visible `Recommendation:`, so the CoT is paid-for-unscored). Mitigation research (2026-06-21):
  - **Ollama `think` is binary** (true/false) — no thinking-budget / length cap; docs show no effort levels for qwen3 (levels exist for some models e.g. gpt-oss → **PROBE** whether our qwen3.5:4b accepts `think:"low"`). [ollama.com/blog/thinking].
  - A **real thinking-budget** (cap CoT to N tokens then force the answer) is a **Qwen / vLLM / SGLang** feature, NOT Ollama → needs qwen served via **SGLang from HF weights** (not the Ollama GGUF tag; same registered-name infra as BFCL).
  - **Cheap Ollama-only first tries:** (a) probe `think:"low"`; (b) **prompt brevity nudge** ("reason concisely, ≤N words, then `Recommendation:`"); (c) keep `num_predict` generous (avoids truncation, doesn't cut cost).
  - **Fallback (user-accepted):** `--no-think` for qwen dec-reasoning *only where necessary* — dec-reasoning judges the visible Recommendation, so --no-think just moves reasoning into the visible channel (fine for the rubric, ~10-30× faster).
  - minicpm dec-reasoning (SGLang): Think ~3.0 ≈ No-Think ~2.7 (both 0/6) — thinking marginally better. qwen low GPU-util is **benign** (decode ~69 tok/s, bandwidth-bound). See [decision-reasoning](../benchmarks/decision-reasoning/README.md).
  - **DECIDED (2026-06-21):** start with the **prompt brevity nudge**, fallback **`--no-think`** — NOT a thinking-budget loop / SGLang-from-HF (won't rewrite the harness for one model's brevity-following). Implementation: add a run-time **`--system-suffix "<text>"`** flag to [run.py](../lab/benchmarks/harness/run.py) that appends to `manifest.get("system")` at the two `system=` sites (generative `client.complete` ~L456 = the dec-reasoning path; agentic system build) — ~5 lines, **NOT** a `bench.json` edit (keep the eval pure + comparable across models). Nudge text e.g. *"Reason concisely — at most ~250 words of thinking — before your `Recommendation:`."* **Record `--system-suffix` as a run param** (fold into the param-recording Next item, next to `think`). **Verify empirically:** run qwen dec-reasoning v0.2 + nudge, check raw `gen_tokens`/sample drops from ~6-7K toward a few hundred (and ~266s/sample falls); if it doesn't shorten enough → `--no-think`. Docs: one line in harness/README + the dec-reasoning README; selftest: a suffix-append check. (SGLang thinking-budget, if ever revisited: needs Qwen **FP8/AWQ** HF weights to fit 8 GB + an **app-level reasoning-cap loop** — no native budget flag exists — explicitly deferred.)
- Periodic **lint pass** (contradictions, orphans, stale claims) — see [AGENTS.md](../AGENTS.md) workflow.
- Candidate experiments not yet scoped: [lab/experiments/README.md](../lab/experiments/README.md#candidate-experiments).

## Recently done (rolling, last few)
- **home-automation v0.4**: split the muddled h5 into **grounding** (h5) + **compound double-confirm** (h19); scorer `required_any` (say∨ask) + list-form `judge_message.tool`; selftest 163 ALL PASS (2026-06-21).
- **gemma-4-12B v2 quant × KV × offload sweep** (5 cells): Q3_K_M f16 full-GPU wins (11/12 home-automation, 4/4 code-basics, 32 tok/s); q4_0 KV costs quality; Q4 only fits full-GPU via q4_0 KV or offload (2026-06-20).
- [stacks/podman-gpu.md](stacks/podman-gpu.md) portable GPU-container setup; llama.cpp container-verified (2026-06-20).
- gemma-4 ingest pivoted to **v2-only** + 5-cell sweep staged (2026-06-20).
- MiniCPM5-1B SGLang controlled re-test: 0/6 decision-reasoning, 7/12 home-automation, 2/5 email-triage (2026-06-20).
