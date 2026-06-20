# Gemma-4-12B v2 — quant × KV × offload sweep (8 GB VRAM)

- Date: staged 2026-06-20 (container verified; sweep not yet run)
- Machine: ASUS ProArt P16 (RTX 5070 Laptop, 8 GB VRAM, WSL2, ~15 GB WSL RAM) — see [proart-p16](../../../wiki/hardware/proart-p16.md)
- Model: [gemma-4-12b-agentic-fable5](../../../wiki/models/gemma-4-12b-agentic-fable5.md) (yuxinlu1 v2 GGUF)
- Runner: **llama.cpp `llama-server` in a rootless-podman CUDA container** (`gemma4_unified` + `--jinja` native tool-calls — Ollama can't do KV-quant / fine offload / native Gemma 4 tools). See [stacks/llama-cpp.md](../../../wiki/stacks/llama-cpp.md).

## Real VRAM budget (verified 2026-06-20, in-container)

`llama-server --list-devices` inside the container reports
**CUDA0: RTX 5070 Laptop, 8150 MiB total, ~6999 MiB free** — desktop/WSL eat
~1.1 GB, so the usable budget is **~6.8 GB, not 8**. This is the binding
constraint and the whole reason for the sweep:

- **Q3_K_M (~6.1 GB weights):** fits full-GPU, leaving only ~0.7–0.9 GB for KV +
  compute buffers → needs a small ctx or `q4_0` KV.
- **Q4_K_M (~7.4 GB weights):** **exceeds the ~6.8 GB free** → likely **cannot run
  full-GPU at all** (expect OOM at `-ngl 99`); partial CPU offload is probably the
  only Q4 path. Confirming this is a result, not a failure.

## Question / hypothesis

Two knobs to fit a higher-quality Q4 (or stretch Q3 context) on a ~6.8 GB budget:
shrink KV (`q4_0`) or offload layers to CPU. Which wins on **throughput ↔ quality**?

5-cell matrix (fixed: `--ctx-size 16384` except D, `-fa on`, `-fit off`, `--jinja`,
temp/top_p/top_k = 1.0 / 0.95 / 64; greedy `temp 0` for the deterministic coding run):

| Cell | Quant | KV | -ngl | ctx | Isolates |
|---|---|---|---|---|---|
| **A** | Q3_K_M | f16 | 99 | 16K | full-GPU baseline |
| **A′** | Q3_K_M | **q4_0** | 99 | 16K | KV-quant effect (vs A) |
| **B** | Q4_K_M | q4_0 | 99 | 16K | Q4 full-GPU via shrunk KV |
| **C** | Q4_K_M | f16 | ~30 | 16K | Q4 + full KV via CPU offload |
| **D** | Q4_K_M | f16 | 99 | 4K | Q4 full-GPU, tiny ctx (offload isolator) |

Reads cleanly: **A vs A′** = KV-quant effect at fixed weights; **A/A′ vs B/C/D** =
Q3 vs Q4 weights; **B vs C vs D** = three ways to fit Q4 on 6.8 GB. Hypotheses:
throughput **A ≈ A′ ≳ B ≫ C** (C is CPU-bandwidth-bound), with **B and D likely
OOM** on weights alone; quality **Q4 ≥ Q3**, **q4_0 KV ≤ f16 KV** (watch long-ctx
agentic). Net: is Q4 even runnable here, and is it worth it over Q3?

> **Confound note:** B vs A still mixes weight-quant + KV-type; the A′ and D cells
> are the isolators that let us attribute differences. If B/D OOM, the practical
> answer is "Q3 full-GPU (A/A′) is the daily driver; Q4 only via offload (C)."

## Verified setup — llama.cpp CUDA container (mirrors the SGLang setup)

```bash
# Image pulled + GPU verified 2026-06-20 (llama-server build 9737):
#   podman pull ghcr.io/ggml-org/llama.cpp:server-cuda
#   podman run --rm --device nvidia.com/gpu=all --security-opt=label=disable \
#     ghcr.io/ggml-org/llama.cpp:server-cuda --list-devices
#   -> CUDA0: RTX 5070 Laptop GPU (8150 MiB, 6999 MiB free)   OK
```

## Method (planned — confirm before the ~13 GB download + run)

`-hf` lets llama-server download the GGUF straight into the mounted HF cache, so
no separate `hf download` step. One server per cell; swap `-m`/`-ctk`/`-ngl`/`-c`.

```bash
# Cell A (Q3_K_M, f16 KV, full GPU, 16K). Reuse ~/.cache/huggingface like SGLang.
podman run -d --name g4v2-A \
  --device nvidia.com/gpu=all --security-opt=label=disable --ipc=host \
  -p 18080:18080 -v ~/.cache/huggingface:/root/.cache/huggingface \
  ghcr.io/ggml-org/llama.cpp:server-cuda \
  -hf yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF:Q3_K_M \
  --host 0.0.0.0 --port 18080 -ngl 99 -fa on -fit off --jinja \
  --ctx-size 16384 --temp 1.0 --top-p 0.95 --top-k 64 --repeat-penalty 1.1 --metrics
# A′: add  -ctk q4_0 -ctv q4_0
# B : :Q4_K_M  + -ctk q4_0 -ctv q4_0           (expect possible OOM at -ngl 99)
# C : :Q4_K_M  + -ngl 30  (CPU offload, f16 KV) (bounded by WSL RAM)
# D : :Q4_K_M  + -ngl 99 --ctx-size 4096        (expect possible OOM)

# Per cell, run BOTH benchmarks against the server (throughput comes back in each
# response's `timings`: prompt_per_second / predicted_per_second — also /metrics):
cd /home/jakce/utils/local-models/lab/benchmarks
# deterministic coding (clean quality signal, Podman sandbox):
python3 -m harness.run --benchmark ../../benchmarks/code-basics \
  --model g4v2-A --provider openai-compatible \
  --base-url http://127.0.0.1:18080/v1 --temperature 0 \
  --num-ctx 16384 --num-predict 2048 --code-sandbox podman
# agentic tool-use (the capability that matters; native Gemma 4 tool format):
python3 -m harness.run --benchmark ../../benchmarks/home-automation \
  --model g4v2-A --provider openai-compatible \
  --base-url http://127.0.0.1:18080/v1 --tool-protocol native \
  --num-ctx 16384 --num-predict 2048 --user-model claude-opus-4.8

podman rm -f g4v2-A   # then start the next cell
```

Relabel `--model` per cell so [results.csv](../../benchmarks/results.csv) keeps
them distinct. Capture VRAM/RAM with `nvidia-smi` / `podman stats` while loaded.

> **MTP speculative-decoding caveat:** the model's MTP draft is verified only on
> llama.cpp **b9553**; the current image is build **9737** and newer builds were
> reported to crash on the draft loader. Skip the draft for this sweep (it doesn't
> affect quality), or pin a b9553 image separately if testing speed.

## Result (matrix to fill)

| Cell | Quant | KV | -ngl | ctx | loaded? | prompt tok/s | gen tok/s | VRAM | RAM | code-basics | home-automation |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A | Q3_K_M | f16 | 99 | 16K | | | | | | | |
| A′ | Q3_K_M | q4_0 | 99 | 16K | | | | | | | |
| B | Q4_K_M | q4_0 | 99 | 16K | | | | | | | |
| C | Q4_K_M | f16 | ~30 | 16K | | | | | | | |
| D | Q4_K_M | f16 | 99 | 4K | | | | | | | |

Record per the harness: model, quant, runner+version (llama.cpp build 9737),
context, `-ngl`, tok/s (prompt+gen), VRAM/RAM, **machine = ProArt P16**, date.

## Learnings

(blank — after the run, update
[wiki/models/gemma-4-12b-agentic-fable5.md](../../../wiki/models/gemma-4-12b-agentic-fable5.md)
"Can it run here?" with the winning config, append a `bench` line to
[wiki/log.md](../../../wiki/log.md), and record whether v2 beat base on our own
agentic set — the unverified-self-eval question.)

Capture specifically:
- **Does Q4 run at all** on ~6.8 GB free, or is Q3 full-GPU the only practical path?
- Best **throughput ↔ quality** config; is Q4's quality bump worth any speed cost?
- Does `q4_0` KV measurably hurt agentic/long-ctx quality vs f16 (A vs A′)?
- v2 **vs base** gemma-4-12B-it on our agentic set (tests the ~3.5× self-eval claim
  under our harness).
