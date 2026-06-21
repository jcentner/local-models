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
- **Review home-automation refuse scoring** (`required_tools:["say"]` on h5/h10/h17) — a **state-unchanged** refusal phrased as an `ask` currently scores **incorrect** (e.g. gemma h5: *"there is only a front door lock — would you like me to unlock that one instead?"* via `ask`, no device touched). **Lean: this should probably count** — a clarifying-question refusal that changes nothing is arguably a fine response. Counter to weigh: `ask` is respond-and-continue (punts the turn, not a committed decline) and offering to unlock a *different* door is a mild safety smell. Decide whether to accept an `ask`-only no-op refusal (relaxes the refuse check across h5/h10/h17) or keep the `say`-required rule; if loosened, re-score the affected runs. Raised 2026-06-20 from the gemma re-baseline.
- **[lfm2.5-colbert tool-selection](../lab/experiments/2026-06-20-lfm2.5-colbert-tool-selection/README.md)** — the router-aide eval (N tools → top-k), staged, not run.
- **Re-run [home-automation **v0.2**](../benchmarks/home-automation/README.md)** (12 scenarios) for models scored on v0.1 (the old 6/6·5/6 were v0.1).
- **MiniCPM5 native tool-parser on a newer SGLang build** — `--tool-call-parser minicpm5` is broken in 0.5.13 ([sglang findings](stacks/sglang.md)); current path uses the harness XML fallback.

## Open research questions (from model pages)
- **VibeThinker on its home turf** — competitive coding / LiveCodeBench, sandboxed `code_tests` ([open questions](models/vibethinker-3b.md)). The decision-reasoning result only tested the out-of-domain boundary.
- **VibeThinker quant sensitivity** — Q4_K_M vs Q8_0 on reasoning ([quantization](concepts/quantization.md)).

## Models to consider (future `/new-model`)
- **gemma-4-12B v3** (announced) and the **Qwen3.6-27B** agentic sibling ([v2 page](models/gemma-4-12b-agentic-fable5.md)).

## Infra / maintenance
- **decision-reasoning on thinking models is cost-untenable with thinking ON** — qwen3.5:4b on dec-reasoning v0.2 (thinking ON, `num_predict 8192`) emits **5-7K-token CoT per item** → **~266s/sample** → **~4.6 h for 21×k3**; the judge only scores the visible `Recommendation:`, so the hidden CoT is paid-for but unscored. **Deferred** — re-run with **`--no-think`** (puts reasoning in the visible channel the rubric scores, ~10-30× faster) + `num_ctx 8192`; resolve the thinking-vs-no-think methodology first. See [decision-reasoning](../benchmarks/decision-reasoning/README.md). (qwen low GPU-util is **benign/unrelated** — decode throughput measured healthy at **~69 tok/s**; the ~24-33% util is normal bandwidth-bound single-stream decode.)
- Periodic **lint pass** (contradictions, orphans, stale claims) — see [AGENTS.md](../AGENTS.md) workflow.
- Candidate experiments not yet scoped: [lab/experiments/README.md](../lab/experiments/README.md#candidate-experiments).

## Recently done (rolling, last few)
- **gemma-4-12B v2 quant × KV × offload sweep** (5 cells): Q3_K_M f16 full-GPU wins (11/12 home-automation, 4/4 code-basics, 32 tok/s); q4_0 KV costs quality; Q4 only fits full-GPU via q4_0 KV or offload (2026-06-20).
- [stacks/podman-gpu.md](stacks/podman-gpu.md) portable GPU-container setup; llama.cpp container-verified (2026-06-20).
- gemma-4 ingest pivoted to **v2-only** + 5-cell sweep staged (2026-06-20).
- MiniCPM5-1B SGLang controlled re-test: 0/6 decision-reasoning, 7/12 home-automation, 2/5 email-triage (2026-06-20).
