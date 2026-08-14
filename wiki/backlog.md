---
title: Backlog / status board
tags: [backlog, planning, index]
updated: 2026-08-13
---

# Backlog / status board

The single "what's next" view. Each item links to its authoritative page (the
[log](log.md) is the timeline; this is the forward queue). Keep it short — move
detail to the linked experiment/model page, and tick items here as they land.

## Now (in progress)
- **LFM2.5 pair ingested (2026-08-13), first runs staged** — [LFM2.5-2.6B](models/lfm2.5-2.6b.md) (on-device agentic flagship, the direct qwen3.5:4b challenger) + [LFM2.5-VL-3B](models/lfm2.5-vl-3b.md) (first vision model in the wiki). Session context: first session on **torrent** ([new host page](hardware/torrent.md)) — **no serving stack installed here yet**, so the 2.6B first run doubles as bring-up. Prior completed milestone: the full v0.4/v0.3 agentic re-baseline (qwen HA 0.789/0.684 + ET 0.917/0.833; the reliability-inversion finding vs gemma).

## Next (queued / staged)
- **[LFM2.5-2.6B first run](../lab/experiments/2026-08-13-lfm2.5-2.6b-first-run/README.md)** — serving bring-up on torrent → tool-protocol probe (Pythonic special tokens; fallback parser if no server handles it) → HA v0.4 + ET v0.3 at k=3 against the standing matrix. The bar: qwen pass^3 0.684/0.833.
- **[LFM2.5-VL-3B first look](../lab/experiments/2026-08-13-lfm2.5-vl-3b-first-look/README.md)** — manual vision smoke (HomeView-shaped fixture probe + screen/OCR); feeds the vision-benchmark go/no-go below.
- **qwen3.5:4b dec-reasoning v0.2 `--no-think`, k=3, temp 1.0** — the decided next action from the brevity-nudge dead end (2026-06-22); still not run.
- *Optional, low priority:* MiniCPM5 ET v0.3 No-Think run for a same-version think pair (the think-axis read is already clear: mixed/task-dependent, weak either way — see [experiment](../lab/experiments/2026-06-21-minicpm5-think-agentic/README.md); SGLang serving recipe lives in the [controlled-serving experiment](../lab/experiments/2026-06-20-minicpm5-sglang-controlled/README.md)).
- **[lfm2.5-colbert tool-selection](../lab/experiments/2026-06-20-lfm2.5-colbert-tool-selection/README.md)** — the router-aide eval (N tools → top-k), staged, not run.
- **MiniCPM5 native tool-parser on a newer SGLang build** — `--tool-call-parser minicpm5` is broken in 0.5.13 ([sglang findings](stacks/sglang.md)); current path uses the harness XML fallback.

## Open research questions (from model pages)
- **Home-automation benchmark v0.5 direction (penciled 2026-08-13; evaluate later, data-only re-skin).** Two ideas from the ~/olympus + ~/homeview review: (1) ground the device world in the **real house** — homeview's 37-type asset library + ~30 named rooms/zones, with the ~8 genuinely actuatable/confirm-worthy types (thermostat, garage-door, water-shutoff, gas-fireplace, hot-tub, sprinkler zones, garbage-disposal, electrical-panel) as the actuation set and real slugs (`furnace-filter`, "Drip — zone 3") as device ids; (2) adopt **Iris's ratified policy idioms** as scenario classes — proposals-never-silent-writes (a confirm idiom we don't test), exec-approval per action, and global-deny + two-person allowlist (an "unrecognized requester → refuse" class the set lacks). Context: no physical home automation exists in the fleet yet (HA integration killed/hardware-gated; Iris's HA adapter is the named future door), so the benchmark stays the lighthouse — this just replaces the generic smart home with the house the agent will actually run in. Scenario-realism reference: homeview `docs/reference/research-2026-07-prior-art.md`.
- **VibeThinker on its home turf** — competitive coding / LiveCodeBench, sandboxed `code_tests` ([open questions](models/vibethinker-3b.md)). The decision-reasoning result only tested the out-of-domain boundary.
- **VibeThinker quant sensitivity** — Q4_K_M vs Q8_0 on reasoning ([quantization](concepts/quantization.md)).

## Models to consider (future `/new-model`)
- **gemma-4-12B v3** (announced) and the **Qwen3.6-27B** agentic sibling ([v2 page](models/gemma-4-12b-agentic-fable5.md)).

## Infra / maintenance
- **Vision benchmark track (penciled 2026-08-13; go/no-go after the VL-3B smoke test).** The harness is text-only (no image field in `bench.json`, no image plumbing in the clients). When it's worth building, **external-first**: wrap homeview's `docs/reference/vision-eval/` (18 ground-truth house photos, required/optional fixtures with regex matchers, deterministic scoring, measured Claude/OpenAI comparison rows) rather than authoring a fresh set — it is simultaneously homeview's own "local vision provider behind `VisionProvider`" API-vs-local benchmark (their backlog names our future local VLM as the missing piece). First candidate model: [LFM2.5-VL-3B](models/lfm2.5-vl-3b.md).
- **last30days on torrent: engine installed + credentials copied from daedalus (2026-08-13, tailscale ssh).** `~/.agents/last30days-repo` → symlink `~/.agents/skills/last30days` (recipe path verified); `~/.config/last30days/.env` carries X cookies (`AUTH_TOKEN`/`CT0`) + `FROM_BROWSER`. Cookie freshness unverified — run `scripts/last30days.py doctor --probe` before the first real research pass; the LFM2.5 pair was ingested via plain web search, so **re-scan their community signal** on the first working run.
- *(Standing benchmark policies — tool protocol=native, thinking default, k=3, comparability — graduated to [AGENTS.md](../AGENTS.md) "House policies", 2026-08-13; the thinking/brevity-nudge evidence trail lives in the [decision-reasoning README](../benchmarks/decision-reasoning/README.md) + log 2026-06-21/22. The qwen `--no-think` re-run itself is queued under Next.)*
- **Record `--system-suffix` as a results.csv run-param** — still open (the flag exists and is written to raw jsonl, but not the results schema).
- Periodic **lint pass** (contradictions, orphans, stale claims) — see [AGENTS.md](../AGENTS.md) workflow.
- Candidate experiments not yet scoped: [lab/experiments/README.md](../lab/experiments/README.md#candidate-experiments).

## Recently done (rolling, last few)
- **qwen3.5:4b re-baseline on the current agentic suite (HA v0.4 + ET v0.3)** — **HA 0.789 / 0.684** (flaky 2/19) + **ET 0.917 / 0.833** (flaky 1/12), k=3, native, +`--judge-messages`, gpt-5.5 user-sim+judge. **Reliability inversion on BOTH:** qwen's pass^3 beats gemma's (HA 0.684 vs 0.632, ET 0.833 vs 0.667) despite gemma's higher ceilings — the most consistent model in the matrix (HA 2 flaky vs gemma's 6; ET 1 vs 4), from a 3.4 GB model. But four HA hard-fails incl. a **safety** fail (h17 disables a smoke detector) + the ambiguity-ask miss (h8/e7 act-or-escalate without the required clarify). **Completes the v0.4/v0.3 re-baseline for every model.** Now apples-to-apples with gemma/MiniCPM5 ([experiment](../lab/experiments/2026-06-21-qwen3.5-4b-v04-rebaseline/README.md)) (2026-06-21).
- **gemma-4-12b v2 re-baseline on the current agentic suite** — HA v0.4 **0.947 / 0.632** (hard-fail h19 compound double-confirm) + ET v0.3 **1.000 / 0.667**, k=3 +`--judge-messages`, gpt-5.5 user-sim+judge; still the strongest local agent, far ahead of MiniCPM5-1B (HA pass^3 0.632 vs 0.210). obs↑/pass^k↓ vs older versions = harder content + msgjudge, not a regression. Mid-run harness fix: Copilot `Failed to load models`/`Failed to list models` blip reclassified **transient** (retry, not abort) + selftest (216 ALL PASS) (2026-06-21).
- **Harness concurrency — overlap Copilot-CLI waits with GPU work** (`--concurrency auto` = 3 for agentic/llm_judge, 1 else): the serial sample loop → a pure per-sample worker + ordered collector (`ThreadPoolExecutor`, fail-fast cancel); +retry/backoff on Copilot (transient blip recovers, bad-`--model` fails fast); Phase 0 measurement added `wall_clock_s` (schema v5) + a gen-vs-Copilot breakdown. **email-triage v0.3 qwen3.5:4b 123.7s → 81.7s (~34%), scoring unchanged.** gpt-5.5 reviewed each phase (3 real findings folded: classifier false-transient, overlap_saved overstated, label); selftest 171→215 ALL PASS (2026-06-21).
- **`--system-suffix` flag** — run-time system-prompt suffix (e.g. a brevity nudge), appended at the generative + agentic sites, whitespace-only = no-op; selftest + docs; gpt-5.5-reviewed (3 Minor folded). Built for the qwen-dec-reasoning over-thinking mitigation; **the empirical qwen run is the remaining step** (commits `02cb50d`, `f8f1c8e`, 2026-06-21).
- **MiniCPM5-1B think-vs-no-think agentic suite** — HA v0.4 **Think 0.632 / 0.210 vs No-Think 0.474 / 0.158** (Think modestly ahead) + ET v0.3 Think 0.833; **mixed / task-dependent, weak either way** (`_no_tool` flail in both modes is the 1B's ceiling). No-Think needs parser-less SGLang + 32K ctx. Revises the earlier "`--no-think` better" call (2026-06-21).
- **MiniCPM5-1B email-triage no-think promoted to results.csv** (`think=off`) + **e5 parity** (s2 flip, matches the qwen v0.2 post-correction) — avg 0.667→0.694, headline obs/pass^3/flaky unchanged (2026-06-21).
- **Journal backfill** (3 catch-up entries) + prompt/skill doc sync (2026-06-21).
- **Record think/no-think axis (results.csv schema v4 + raw + run-viewer)** — new `think` column (`on|off|default`) after `sampling`; harness `think_label()` + both raw writes; 12 rows back-annotated (`tmp/migrate_results_v4.py`); viewer surfaces it in the header/pill + keys the variant matrix on (model, think); docs synced; selftest 175 ALL PASS. Unblocks thinking-as-default comparability (2026-06-21).
- **home-automation v0.4**: split the muddled h5 into **grounding** (h5) + **compound double-confirm** (h19); scorer `required_any` (say∨ask) + list-form `judge_message.tool` + skipped-sibling `forbidden_device_attempts` + list-valued `expected_state`; gpt-5.5 cross-review folded; selftest 171 ALL PASS (2026-06-21).
- [stacks/podman-gpu.md](stacks/podman-gpu.md) portable GPU-container setup; llama.cpp container-verified (2026-06-20).
- gemma-4 ingest pivoted to **v2-only** + 5-cell sweep staged (2026-06-20).
- MiniCPM5-1B SGLang controlled re-test: 0/6 decision-reasoning, 7/12 home-automation, 2/5 email-triage (2026-06-20).
