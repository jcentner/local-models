---
title: Backlog / status board
tags: [backlog, planning, index]
updated: 2026-06-21
---

# Backlog / status board

The single "what's next" view. Each item links to its authoritative page (the
[log](log.md) is the timeline; this is the forward queue). Keep it short — move
detail to the linked experiment/model page, and tick items here as they land.

## Now (in progress)
- *(nothing actively running)* — last completed: the **2026-06-21** batch — [home-automation v0.4](../benchmarks/home-automation/README.md) (h5 grounding + h19 compound double-confirm), the [think/no-think axis](log.md) recorded in results.csv (schema v4), and the MiniCPM5-1B email-triage no-think promotion + e5 parity.

## Next (queued / staged)
- **MiniCPM5 agentic suite — HA v0.4 + think re-runs** — ET v0.2 no-think is done (in results.csv; see Recently done). **Pending:** home-automation v0.4 (not yet run for MiniCPM5) and the think re-runs once the thinking-default policy is set. SGLang recipe (forward-useful): serve WITHOUT `--tool-call-parser` (the `minicpm5` parser swallows the XML) + harness `parse_xml_tool_calls()`; `--no-think` works — [experiment](../lab/experiments/2026-06-20-minicpm5-sglang-controlled/README.md).
- **Re-baseline all models on home-automation v0.4** (k=3, **with `--judge-messages`** so the h5/h17/h18 message content is graded) — the v0.4 grounding + double-confirm redesign means prior h5 scores aren't comparable; this **subsumes** re-running any model still on an older HA version (qwen/gemma are on v0.3; MiniCPM5 ET done, HA pending).
- **[lfm2.5-colbert tool-selection](../lab/experiments/2026-06-20-lfm2.5-colbert-tool-selection/README.md)** — the router-aide eval (N tools → top-k), staged, not run.
- **MiniCPM5 native tool-parser on a newer SGLang build** — `--tool-call-parser minicpm5` is broken in 0.5.13 ([sglang findings](stacks/sglang.md)); current path uses the harness XML fallback.

## Open research questions (from model pages)
- **VibeThinker on its home turf** — competitive coding / LiveCodeBench, sandboxed `code_tests` ([open questions](models/vibethinker-3b.md)). The decision-reasoning result only tested the out-of-domain boundary.
- **VibeThinker quant sensitivity** — Q4_K_M vs Q8_0 on reasoning ([quantization](concepts/quantization.md)).

## Models to consider (future `/new-model`)
- **gemma-4-12B v3** (announced) and the **Qwen3.6-27B** agentic sibling ([v2 page](models/gemma-4-12b-agentic-fable5.md)).

## Infra / maintenance
- **Tool-protocol policy (DECIDED 2026-06-21): default to `native`, don't run both.** Native function-calling is the faithful test (a deployed home-agent uses real tool-calling); prompt-mode is a portability shim, used **only as a fallback when native is unavailable** (tool-blind template / no function-calling). qwen3.5:4b + gemma → native; MiniCPM5 → native via SGLang + harness XML fallback (prompt-mode isn't usable there anyway). The prompt-vs-native contrast is a **banked finding** (model+task-dependent: qwen ET native 4/5>prompt 3/5, HA prompt 6/6>native 5/6), re-run both only when the protocol contrast is itself the question.
- **Thinking-as-default policy + tame qwen over-thinking on decision-reasoning** — user leans **"default to thinking, it likely improves scores"**; think is now **recorded** (results.csv `think` column, schema v4) so set the policy + re-run for consistency (gemma agentic=thinking already; qwen + minicpm=no-think — confounded). The blocker on qwen: qwen3.5:4b on dec-reasoning v0.2 (thinking ON, `num_predict 8192`) emits **5-7K-token CoT/item** → **~266s/sample** → **~4.6 h for 21×k3** (judge only scores the visible `Recommendation:`, so the CoT is paid-for-unscored). Mitigation research (2026-06-21):
  - **Ollama `think` is binary** (true/false) — no thinking-budget / length cap; docs show no effort levels for qwen3 (levels exist for some models e.g. gpt-oss → **PROBE** whether our qwen3.5:4b accepts `think:"low"`). [ollama.com/blog/thinking].
  - A **real thinking-budget** (cap CoT to N tokens then force the answer) is a **Qwen / vLLM / SGLang** feature, NOT Ollama → needs qwen served via **SGLang from HF weights** (not the Ollama GGUF tag; same registered-name infra as BFCL).
  - **Cheap Ollama-only first tries:** (a) probe `think:"low"`; (b) **prompt brevity nudge** ("reason concisely, ≤N words, then `Recommendation:`"); (c) keep `num_predict` generous (avoids truncation, doesn't cut cost).
  - **Fallback (user-accepted):** `--no-think` for qwen dec-reasoning *only where necessary* — dec-reasoning judges the visible Recommendation, so --no-think just moves reasoning into the visible channel (fine for the rubric, ~10-30× faster).
  - minicpm dec-reasoning (SGLang): Think ~3.0 ≈ No-Think ~2.7 (both 0/6) — thinking marginally better. qwen low GPU-util is **benign** (decode ~69 tok/s, bandwidth-bound). See [decision-reasoning](../benchmarks/decision-reasoning/README.md).
  - **DECIDED (2026-06-21):** start with the **prompt brevity nudge**, fallback **`--no-think`** — NOT a thinking-budget loop / SGLang-from-HF (won't rewrite the harness for one model's brevity-following). Implementation: add a run-time **`--system-suffix "<text>"`** flag to [run.py](../lab/benchmarks/harness/run.py) that appends to `manifest.get("system")` at the two `system=` sites (generative `client.complete` ~L456 = the dec-reasoning path; agentic system build) — ~5 lines, **NOT** a `bench.json` edit (keep the eval pure + comparable across models). Nudge text e.g. *"Reason concisely — at most ~250 words of thinking — before your `Recommendation:`."* **Record `--system-suffix` as a run param** (fold into the param-recording Next item, next to `think`). **Verify empirically:** run qwen dec-reasoning v0.2 + nudge, check raw `gen_tokens`/sample drops from ~6-7K toward a few hundred (and ~266s/sample falls); if it doesn't shorten enough → `--no-think`. Docs: one line in harness/README + the dec-reasoning README; selftest: a suffix-append check. (SGLang thinking-budget, if ever revisited: needs Qwen **FP8/AWQ** HF weights to fit 8 GB + an **app-level reasoning-cap loop** — no native budget flag exists — explicitly deferred.)
- Periodic **lint pass** (contradictions, orphans, stale claims) — see [AGENTS.md](../AGENTS.md) workflow.
- Candidate experiments not yet scoped: [lab/experiments/README.md](../lab/experiments/README.md#candidate-experiments).

## Recently done (rolling, last few)
- **MiniCPM5-1B email-triage no-think promoted to results.csv** (`think=off`) + **e5 parity** (s2 flip, matches the qwen v0.2 post-correction) — avg 0.667→0.694, headline obs/pass^3/flaky unchanged (2026-06-21).
- **Journal backfill** (3 catch-up entries) + prompt/skill doc sync (2026-06-21).
- **Record think/no-think axis (results.csv schema v4 + raw + run-viewer)** — new `think` column (`on|off|default`) after `sampling`; harness `think_label()` + both raw writes; 12 rows back-annotated (`tmp/migrate_results_v4.py`); viewer surfaces it in the header/pill + keys the variant matrix on (model, think); docs synced; selftest 175 ALL PASS. Unblocks thinking-as-default comparability (2026-06-21).
- **home-automation v0.4**: split the muddled h5 into **grounding** (h5) + **compound double-confirm** (h19); scorer `required_any` (say∨ask) + list-form `judge_message.tool` + skipped-sibling `forbidden_device_attempts` + list-valued `expected_state`; gpt-5.5 cross-review folded; selftest 171 ALL PASS (2026-06-21).
- [stacks/podman-gpu.md](stacks/podman-gpu.md) portable GPU-container setup; llama.cpp container-verified (2026-06-20).
- gemma-4 ingest pivoted to **v2-only** + 5-cell sweep staged (2026-06-20).
- MiniCPM5-1B SGLang controlled re-test: 0/6 decision-reasoning, 7/12 home-automation, 2/5 email-triage (2026-06-20).
