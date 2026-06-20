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
- **Run the [gemma-4-12B v2 quant × KV × offload sweep](../lab/experiments/2026-06-20-gemma-4-12b-v2-quant-config-sweep/README.md)** — 5 cells (A/A′/B/C/D); container verified, model download + run pending. Includes **v2 vs base** on the agentic set (tests the unverified ~3.5× self-eval claim).

## Next (queued / staged)
- **[lfm2.5-colbert tool-selection](../lab/experiments/2026-06-20-lfm2.5-colbert-tool-selection/README.md)** — the router-aide eval (N tools → top-k), staged, not run.
- **Re-run [home-automation **v0.2**](../benchmarks/home-automation/README.md)** (12 scenarios) for models scored on v0.1 (the old 6/6·5/6 were v0.1).
- **MiniCPM5 native tool-parser on a newer SGLang build** — `--tool-call-parser minicpm5` is broken in 0.5.13 ([sglang findings](stacks/sglang.md)); current path uses the harness XML fallback.

## Open research questions (from model pages)
- **VibeThinker on its home turf** — competitive coding / LiveCodeBench, sandboxed `code_tests` ([open questions](models/vibethinker-3b.md)). The decision-reasoning result only tested the out-of-domain boundary.
- **VibeThinker quant sensitivity** — Q4_K_M vs Q8_0 on reasoning ([quantization](concepts/quantization.md)).
- **gemma-4-12B v2 vs base** on our agentic harness (folded into the sweep above).

## Models to consider (future `/new-model`)
- **gemma-4-12B v3** (announced) and the **Qwen3.6-27B** agentic sibling ([v2 page](models/gemma-4-12b-agentic-fable5.md)).

## Infra / maintenance
- Periodic **lint pass** (contradictions, orphans, stale claims) — see [AGENTS.md](../AGENTS.md) workflow.
- Candidate experiments not yet scoped: [lab/experiments/README.md](../lab/experiments/README.md#candidate-experiments).

## Recently done (rolling, last few)
- [stacks/podman-gpu.md](stacks/podman-gpu.md) portable GPU-container setup; llama.cpp container-verified (2026-06-20).
- gemma-4 ingest pivoted to **v2-only** + 5-cell sweep staged (2026-06-20).
- MiniCPM5-1B SGLang controlled re-test: 0/6 decision-reasoning, 7/12 home-automation, 2/5 email-triage (2026-06-20).
