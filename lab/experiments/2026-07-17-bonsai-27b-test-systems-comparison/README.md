# Bonsai 27B ternary vs 1-bit test-system comparison

- Date: 2026-07-17
- Status: staged; no weights downloaded
- Hypothesis / question: Ternary Bonsai 27B should preserve more capability but
  fit the RTX 5070 Laptop only narrowly at 4K; 1-bit Bonsai 27B should trade
  measurable quality for a much safer memory margin on the same test systems.
- First host: **Daedalus**, ASUS ProArt P16, RTX 5070 Laptop 8 GB, Ryzen AI 9 HX 370,
  WSL2 Ubuntu 24.04; currently 15 GiB WSL RAM. See
  [hardware page](../../../wiki/hardware/proart-p16.md).
- Additional hosts: record each test system's hardware, OS, runner, and available
  memory before running the same pair. Phone deployment is explicitly deferred.

## Fit verdict before download

| Operating point | Artifact | Published 4K peak | Verdict on Daedalus |
|---|---|---:|---|
| Quality target | Ternary GGUF `Q2_0_g128`, 7.17 GB | 7.8 GiB | borderline full-GPU; close other GPU users; use PrismML CUDA 12.8 binary |
| Compact comparison | 1-bit GGUF `Q1_0_g128`, 3.8-3.9 GB | 4.8 GiB | comfortable full-GPU |

The WSL RAM cap is sufficient for either first-run text configuration. Raise it
before testing very long context or loading optional vision/drafter components.

## Method

### Stage A: per-host smoke and memory

Do not run until weight download is confirmed.

```bash
git clone https://github.com/PrismML-Eng/Bonsai-demo.git ~/models/Bonsai-demo
cd ~/models/Bonsai-demo

# Ternary quality target. The setup fetches the pinned CUDA binary and weights.
BONSAI_FAMILY=ternary BONSAI_MODEL=27B \
BONSAI_OPENWEBUI=0 BONSAI_CODE_INTERPRETER=0 ./setup.sh

BONSAI_FAMILY=ternary BONSAI_MODEL=27B \
./scripts/start_llama_server.sh --reasoning-budget 2048
```

Record before/after with:

```bash
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free \
  --format=csv,noheader
curl -s http://127.0.0.1:8080/health
```

Run one concise reasoning prompt, one native tool-call smoke test, and
`llama-bench` PP512/TG128 if the bundled binary exposes it. Keep context at 4096,
sampling at temp 0.7 / top_p 0.95 / top_k 20, and thinking capped at 2048.

After the ternary run, repeat with 1-bit even if ternary succeeds. If ternary
OOMs or spills, record that result and continue with 1-bit:

```bash
cd ~/models/Bonsai-demo
BONSAI_FAMILY=bonsai BONSAI_MODEL=27B \
BONSAI_OPENWEBUI=0 BONSAI_CODE_INTERPRETER=0 ./setup.sh
BONSAI_FAMILY=bonsai BONSAI_MODEL=27B \
./scripts/start_llama_server.sh --reasoning-budget 2048
```

### Stage B: matched harness comparison

Expose the server at `http://127.0.0.1:8080/v1`, verify its advertised model id,
then run the same current agentic slice against ternary and 1-bit. Default to
native tool calling; do not run prompt protocol unless native is unavailable.

Use the same 4096 context, sampling, reasoning budget, prompts, and harness
version for both variants on each host. Capture for each row: model + family,
base model, GGUF format, PrismML llama.cpp
commit/binary tag, context length, GPU layers, sampling, thinking budget,
prompt/gen tok/s, wall time, VRAM/RAM, provider endpoint, and machine.

Start with a one-item smoke before any full `--k 3` benchmark. The full command
depends on the exact model id returned by the server and must be recorded here
at run time rather than guessed. Repeat the pair on additional test systems
before drawing a portability conclusion.

No secrets or Hugging Face tokens go in commands or this file.

## Result

### Ternary by test system

- Host:
- Runner/version:
- Context / GPU layers:
- VRAM / RAM:
- PP512 / TG128:
- Reasoning smoke:
- Tool-call smoke:

### 1-bit by test system

- Host:
- Runner/version:
- Context / GPU layers:
- VRAM / RAM:
- PP512 / TG128:
- Reasoning smoke:
- Tool-call smoke:

### Matched comparison

- Quality delta:
- Speed delta:
- Memory delta:
- Reliability delta:

## Learnings

- Which variant should be the test-system default?
- Does ternary's quality justify its memory edge-case on 8 GB?
- How much capability does the phone-size 1-bit artifact retain on the same
  hardware and prompts?
- Which benchmark should run at `--k 3` next?

Model page: [Bonsai 27B](../../../wiki/models/bonsai-27b.md).
