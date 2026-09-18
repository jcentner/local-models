# Bonsai 2 27B first run

- Date staged: 2026-09-18
- Status: staged; `PTQ1_0` download to daedalus in progress, nothing run
- Supersedes: [Bonsai 27B ternary vs 1-bit comparison](../2026-07-17-bonsai-27b-test-systems-comparison/README.md)
  (never run; Bonsai 2 replaces the ternary arm and has no 1-bit build)
- Hypothesis / question: the dense `PTQ1_0` packing (5.54 GiB) puts a 27B
  thinking, tool-calling model fully on an 8 GB GPU for the first time. Does it
  fit with a usable context, is it fast enough for a home-agent turn, and does
  PrismML's claimed tool-calling retention show up as reliability on our sets?
- First host: **daedalus** (ASUS ProArt P16, RTX 5070 Laptop 8 GB, WSL2;
  [hardware page](../../../wiki/hardware/proart-p16.md)). Windows-side CUDA on
  daedalus or torrent is an accepted alternative (Jake 2026-09-18): the fork
  ships Windows CUDA 12.4 / 13.3 binaries and the demo has `.ps1` launchers.

## Fit verdict before the run (daedalus, 2026-09-18)

GPU 8151 MiB (7.96 GiB), 785 MiB in use at idle from the Windows desktop, so
about 7.2 GiB available. WSL sees 15 GiB RAM.

| Packing | Weights | + ~1.2 GiB overhead + FP16 KV | Verdict |
|---|---:|---|---|
| `PTQ1_0` | 5.54 GiB | 7.0 GiB at 4K, 7.2 GiB at 8K | fits full-GPU at 4K, marginal at 8K; close other GPU users; 4-bit KV for more context |
| `PQ2_0` | 6.71 GiB | 8.2 GiB at 4K | does not fit full-GPU; partial offload only |

The vendor says `PTQ1_0` is the slower decode on Blackwell (about 7% on a 5090)
and about half the prompt-processing speed. On this box it is the only packing
that stays on the GPU, so that cost is accepted; Stage A measures it.

## Method

### Stage 0: artifacts

Weights (download started 2026-09-18; verify against the HF LFS sha256 on the model page before use):
`~/models/prism-ml/Ternary-Bonsai-2-27B-gguf/Ternary-Bonsai-2-27B-PTQ1_0.gguf`.

Binary, the release the demo pins (`prism-b10685-7dffb15`):

```bash
mkdir -p ~/models/prism-llama && cd ~/models/prism-llama
curl -fLO https://github.com/PrismML-Eng/llama.cpp/releases/download/prism-b10685-7dffb15/llama-prism-b10685-7dffb15-bin-linux-cuda-12.8-x64.tar.gz
mkdir -p bin && tar -xzf llama-prism-b10685-7dffb15-bin-linux-cuda-12.8-x64.tar.gz -C bin --strip-components=1
LD_LIBRARY_PATH=bin bin/llama-server --version
```

If the prebuilt binary fails on sm_120 or on the WSL CUDA runtime, build the fork
in the CUDA container per [podman-gpu](../../../wiki/stacks/podman-gpu.md)
(`-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=120`, CUDA 12.8 or newer), or run the
Windows CUDA binary.

### Stage A: load, memory, speed, smokes

```bash
cd ~/models/prism-llama
M=~/models/prism-ml/Ternary-Bonsai-2-27B-gguf/Ternary-Bonsai-2-27B-PTQ1_0.gguf

/usr/lib/wsl/lib/nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader   # before
LD_LIBRARY_PATH=bin bin/llama-bench -m $M -ngl 99 -fa 1 -p 512 -n 128

LD_LIBRARY_PATH=bin bin/llama-server -m $M -ngl 99 -fa on -c 4096 --jinja \
  --temp 1.0 --top-p 0.95 --top-k 20 --reasoning-budget 2048 \
  --host 127.0.0.1 --port 8080
curl -s http://127.0.0.1:8080/health; curl -s http://127.0.0.1:8080/v1/models
```

Record VRAM at load and after a long generation, at `-c 4096` and `-c 8192`, then
at `-c 32768` with `--cache-type-k q4_0 --cache-type-v q4_0`. One concise
reasoning prompt; one native tool-call smoke (does `tool_calls` come back parsed,
with thinking separated). Watch for spill into shared memory: on WSL the driver
can page VRAM to system RAM silently, and the tell is tok/s collapsing, not an
OOM.

Stop here if it does not load, spills at 4K, or tool calls do not parse; record
why.

### Stage B: the standing matrix

Home-automation v0.4 and email-triage v0.3, `--k 3`, native tools, the model's
recommended thinking sampling, `--provider openai-compatible` at
`http://127.0.0.1:8080/v1`, `+--judge-messages`; code-basics as the cheap tell.
One-item smoke before the full run. The exact command depends on the model id
the server reports; record it here at run time. Harness mechanics:
[harness README](../../benchmarks/harness/README.md).

The bar: gemma-4-12b ceilings HA 0.947 / ET 1.000; qwen3.5:4b `pass^3` HA 0.684 /
ET 0.833.

Thinking budget is a run parameter: start at `--reasoning-budget 2048` and record
it. If wall time is unworkable, a second run at `medium` effort or a smaller
budget is a separate row, never a silent change.

Row fields: model, packing, fork release tag, context, GPU layers, sampling,
thinking budget, prompt and gen tok/s, wall time, VRAM/RAM, endpoint, machine.

## Result

### Stage A

- Host:
- Binary / release tag:
- Context / GPU layers / KV type:
- VRAM at load / after generation:
- PP512 / TG128:
- Reasoning smoke:
- Tool-call smoke:

### Stage B

- HA v0.4 obs@3 / pass^3 / flaky:
- ET v0.3 obs@3 / pass^3 / flaky:
- code-basics:
- wall time per scenario:

## Learnings

- Does a ternary 27B on 8 GB beat the 12B and 4B champions where it counts
  (`pass^3`)?
- Is the thinking cost acceptable for a home-agent turn?
- Is `PQ2_0` with partial offload, or on a bigger GPU, worth a follow-up?

Model page: [Bonsai 2 27B](../../../wiki/models/bonsai-2-27b.md).
