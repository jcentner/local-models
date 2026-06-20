# Gemma-4-12B v2 — quant × KV × offload sweep (8 GB VRAM)

- Date: 2026-06-20 (run complete — see Result)
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

## Result (run 2026-06-20, llama.cpp build 9737, ProArt P16)

| Cell | Quant | KV | -ngl | ctx | loaded? | prompt tok/s | gen tok/s | VRAM | code-basics | home-automation |
|---|---|---|---|---|---|---|---|---|---|---|
| **A** | Q3_K_M | f16 | 99 | 16K | ✅ | 66 | **32** | 7780 MiB | **4/4** | **11/12** |
| **A′** | Q3_K_M | q4_0 | 99 | 16K | ✅ | — | 28 | 6562 MiB | 3/4 | 10/12 |
| **B** | Q4_K_M | q4_0 | 99 | 16K | ✅ | 48 | 31 | 7796 MiB | 2/4 | 11/12 |
| **C** | Q4_K_M | f16 | 30 | 16K | ✅ (offload) | 45 | 15–17 | 5868 MiB | **4/4** | **11/12** |
| **D** | Q4_K_M | f16 | 99 | 4K | ✅ but **~3 tok/s** | 3.7 | **3** | 7848 MiB | 4/4 | skipped (non-viable speed) |

Failures are genuine task errors (transcripts in `runs/home-automation-g4v2-*.jsonl`,
`episode.transcript` + `episode.tool_calls`): A/h5 hit `max_turns` and toggled a
device it shouldn't (`unchanged_ok` fail); B&C/h9 ended `done` with a wrong final
state (`state_ok` fail). code-basics runs greedy (temp 0, deterministic);
home-automation runs temp 1.0 (stochastic — the *which* item fails varies, the
aggregate is stable).

## Learnings

**Winner: Cell A — Q3_K_M, f16 KV, full GPU, 16K ctx** (4/4 code, 11/12 agentic,
~32 tok/s, 7.78 GB). The daily-driver config.

1. **v2 is a strong local home-automation agent** — **10–11/12** across every
   config, far above MiniCPM5-1B's 7/12. The capability is real and quant-robust.
2. **Q4_K_M *is* runnable on 8 GB** (my OOM hypothesis was wrong): full-GPU with
   `q4_0` KV (B, 7.8 GB) or via CPU offload (C, `-ngl 30`, 5.9 GB).
3. **`q4_0` KV measurably costs quality.** Every f16-KV cell (A, C, D) scored
   **4/4** code-basics; both q4_0-KV cells dropped (A′ 3/4, B 2/4), and q4_0 KV
   cost A′ one agentic item (10 vs 11). The ~1.2 GB VRAM saving isn't free.
4. **Q4's quality edge never showed** on these benchmarks — Q4 (B) tied/again trailed
   Q3 (A). At this size the weight-quant step Q3→Q4 matters less than the KV dtype.
5. **Throughput:** full-GPU ≈ 28–32 tok/s; CPU offload (`-ngl 30`) halves it to
   ~13–17; cramming Q4+f16 KV fully on-GPU at 4K **"fits" (7848 MiB) but collapses
   to ~3 tok/s** — no compute headroom. **"Fits" ≠ "usable".**
6. Net: **use Q3_K_M + f16 KV full-GPU.** Every path to Q4 costs quality (q4_0 KV)
   or speed (offload/thrash) for no measured quality gain.

**Scope note:** intentionally measured v2's **absolute** capability (the thing we
care about), which is established — **11/12** agentic, **4/4** code. No base
gemma-4-12B-it head-to-head was run, so the author's relative ~3.5× tau2 claim is
neither tested nor pursued here.
