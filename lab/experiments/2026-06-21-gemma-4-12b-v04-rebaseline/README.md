# Gemma-4-12B v2 — re-baseline on the current agentic suite (HA v0.4 + ET v0.3)

- Date: 2026-06-21
- Machine: ASUS ProArt P16 (RTX 5070 Laptop, 8 GB VRAM, WSL2) — [proart-p16](../../../wiki/hardware/proart-p16.md)
- Model: [gemma-4-12b-agentic-fable5](../../../wiki/models/gemma-4-12b-agentic-fable5.md) (yuxinlu1 v2 GGUF), **Q3_K_M, f16 KV, full-GPU** (Cell A — the verified sweet spot)
- Serving: llama.cpp `server-cuda` in rootless-podman ([llama-cpp](../../../wiki/stacks/llama-cpp.md)), `--jinja` native Gemma 4 tool-calls, `:18080/v1`
- Scorer: `agentic`, `--tool-protocol native`, **`--judge-messages`**, gpt-5.5 user-sim + message-judge, `--k 3`, temp 1.0 / top_p 0.95 / top_k 64, `num_ctx 16384`, think=default

## Hypothesis / why

Gemma was the strongest local agent here, but its only k=3 numbers were on **older
benchmark versions** (HA v0.3, ET v0.2, no `--judge-messages`). The suite has since
advanced — **HA v0.4** (h5 split into grounding vs the new **h19 compound
double-confirm**; list-valued `expected_state`; skipped-sibling
`forbidden_device_attempts`) and **ET v0.3** — and every other model was re-run on
the new versions **with the message-judge AND-gate**. The backlog flagged gemma +
qwen3.5:4b as the last two still on HA v0.3. This run closes the gemma gap so the
home-agent verdict is comparable across the current matrix.

## Method

Cached Q3_K_M GGUF (`~/.cache/huggingface`, from the 2026-06-20 sweep — **no
re-download**), restarted the Cell-A llama.cpp container (7780 MiB VRAM, ~4 s load),
ran both agentic sets back to back against `:18080/v1`. See the two `runs/*.jsonl`
named in [results.csv](../../benchmarks/results.csv).

> **Harness fix mid-run (committed separately).** The first HA attempt aborted at
> 25/57 when the Copilot user-sim hit a transient **`Failed to load models` /
> `Failed to list models`** blip that `judge_copilot._classify_copilot` treated as
> *permanent* (fail-fast). A probe proved it recovers in seconds with no config
> change, so the model-list-failure signatures were added to `_TRANSIENT_SIGNS`
> (retry, not abort) + a selftest case. Re-ran clean. This is exactly the
> blip-shouldn't-kill-a-run case the Phase-1 retry/backoff work targets.

## Result

| Benchmark | obs@3 | **pass^3** | avg | flaky | sem | wall_clock |
|---|---|---|---|---|---|---|
| **home-automation v0.4** (19) | 0.947 | **0.632** | 0.789 | 6/19 | 0.073 | 1058 s |
| **email-triage v0.3** (12) | 1.000 | **0.667** | 0.861 | 4/12 | 0.064 | 393 s |

- **HA flaky** (inconsistent across k): h4, h7, h9, h14, h15, h17. **Hard fail: h19
  (0/3)** — the new compound double-confirm.
- **ET flaky**: e6, e8, e10, e12 (e12 worst at 1/3 — wrongly **escalates** instead
  of replying on 2 of 3).

### vs the prior gemma rows (different versions — not apples-to-apples)
| | obs@k | pass^k |
|---|---|---|
| HA **v0.3** (2026-06-20, no msgjudge) | 0.889 | 0.722 |
| HA **v0.4** (this run, +msgjudge) | **0.947** | **0.632** |
| ET **v0.2** (2026-06-20, no msgjudge) | 0.917 | 0.833 |
| ET **v0.3** (this run, +msgjudge) | **1.000** | **0.667** |

`observed_pass@k` rose on both; `pass^k` fell on both. This is **not a regression** —
it's the harder v0.4/v0.3 content (esp. the **h19** hard fail that didn't exist in
v0.3) plus the **`--judge-messages` AND-gate** (can only tighten a pass), all of
which the prior numbers never faced.

### vs other models on the SAME versions (the comparable read)
| Model | HA v0.4 obs / pass^3 | ET v0.3 obs / pass^3 |
|---|---|---|
| **gemma-4-12b v2 (this)** | **0.947 / 0.632** | **1.000 / 0.667** |
| MiniCPM5-1B (think) | 0.632 / 0.210 | 0.833 / 0.333 |
| qwen3.5:4b | *still on HA v0.3 (0.778 / 0.667)* | *only k=1 A/B rows* |

Gemma is **far ahead of MiniCPM5-1B** on both at matched version+judge (HA pass^3
0.632 vs 0.210; ET 0.667 vs 0.333).

## The one systematic gap: h19 (compound double-confirm)

`require_confirm: [security_system, back_door_lock]` — the spec wants **each**
sensitive device confirmed with its name in `ask.device` **before** acting. Across
all 3 samples `confirm_ok=False`: gemma confirms the alarm (names `security_system`)
but **folds the back-door unlock into that same single `ask`** instead of a separate
`ask.device=back_door_lock`; one sample also stalled polling `get_status`, another
used a non-accepted `alarm_off` state. It understands confirm-before-act but not
**per-device structured confirmation on compound requests** — a real capability
gap, not a scorer artifact.

## Learnings / verdict (per-environment: ProArt P16, llama.cpp Q3_K_M)

- **Gemma-4-12b v2 stays the strongest local agent in the wiki** — capability ceiling
  is near-perfect (obs@3 0.947 / 1.000), and even under the stricter v0.4/v0.3 +
  msgjudge regime its reliability (pass^3 0.632 / 0.667) **dominates the 1B class**.
- **The home-agent weak point is the compound-confirm flow (h19)** — worth a targeted
  look (does prompting for per-device confirmation fix it, or is it a training gap?).
- **Quant-robust, fits 8 GB** at ~32 tok/s single-stream (Cell A); the agentic
  per-stream tok/s here (~10) is the concurrency=3 queue split, not a slowdown.
- **Caveat:** this is gemma's **absolute** capability; the author's relative ~3.5×-
  over-base claim remains untested (no base head-to-head).

## Repro

```bash
podman run -d --name g4v2-A --device nvidia.com/gpu=all --security-opt=label=disable \
  --ipc=host -p 18080:18080 -v ~/.cache/huggingface:/root/.cache/huggingface \
  ghcr.io/ggml-org/llama.cpp:server-cuda \
  -hf yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF:Q3_K_M \
  --host 0.0.0.0 --port 18080 -ngl 99 -fa on -fit off --jinja \
  --ctx-size 16384 --temp 1.0 --top-p 0.95 --top-k 64 --repeat-penalty 1.1 --metrics

cd lab/benchmarks
for B in home-automation email-triage; do
  python3 -m harness.run --benchmark ../../benchmarks/$B \
    --model g4v2-A-Q3KM-f16-ngl99 --base-model gemma-4-12b-agentic-fable5 \
    --provider openai-compatible --base-url http://127.0.0.1:18080/v1 \
    --tool-protocol native --k 3 --temperature 1.0 --top-p 0.95 --top-k 64 \
    --num-ctx 16384 --num-predict 2048 \
    --user-model gpt-5.5 --judge-model gpt-5.5 --judge-messages
done
podman rm -f g4v2-A
```
