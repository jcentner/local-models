# Ornith-1.5-9B — first run (strongest-local-agent challenger)

- Date: 2026-08-19 (staged; not yet run)
- Hypothesis / question: Ornith's vendor table claims a 9B that roughly
  doubles Qwen3.5-9B on terminal/repo coding and beats it on every agentic
  benchmark. Does it beat **gemma-4-12b-agentic's ceiling** (HA v0.4 obs@3
  0.947, ET v0.3 1.000) and/or **qwen3.5:4b's reliability** (pass^3 0.684 /
  0.833) on our suite — from a smaller file (Q4_K_M 5.63 GB vs gemma Q3_K_M
  6.09 GB)? Secondary: 4/4 on code-basics would corroborate the coding claim
  cheaply; benchmaxxing skepticism is the community's median take.
- Model page: [wiki/models/ornith-1.5-9b.md](../../../wiki/models/ornith-1.5-9b.md).
- Setup: **torrent** ([hardware page](../../../wiki/hardware/torrent.md)) — RTX
  3070 Ti 8 GB (Ampere sm_86), WSL2, 31 GB RAM visible. **No serving stack on
  this box yet** — shared bring-up step with the staged
  [LFM2.5 first run](../2026-08-13-lfm2.5-2.6b-first-run/README.md); whichever
  runs first pays the install cost.

## Fit verdict (torrent, computed 2026-08-19, unverified)

Q4_K_M (5.63 GB) + 16K f16 KV should land under gemma's verified 7.78 GB
envelope on the 8 GB class — but desktop Windows drives the display from this
GPU; check free VRAM with `nvidia-smi` first and drop to 8K ctx if tight.
Q5_K_M (6.47 GB) only at reduced context; Q8_0 (9.53 GB) needs offload — not
the first run.

## Method

### 0. Serving bring-up (pick one; verify template fidelity before benchmarking)
Preflight with `bash scripts/verify-stack.sh`.

**Path A — Ollama (daily-driver parity with the qwen rows):**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama run hf.co/ornith-ai/Ornith-1.5-9B-GGUF:Q4_K_M "Say hi in one short sentence."
```
Gate: `ollama show --template` + one `/api/chat` call with a dummy tool.
Confirm (a) coherent output, (b) `<think>` opens/strips sanely, (c) OpenAI
`tools` round-trips into `message.tool_calls`. If (c) fails → Path B; if the
markup is Qwen-style XML, the harness `parse_xml_tool_calls()` fallback is the
recorded protocol.

**Path B — llama.cpp CUDA container (controlled, `--jinja`):**
```bash
podman run --rm --device nvidia.com/gpu=all --security-opt=label=disable --ipc=host \
  -v ~/.cache/huggingface:/root/.cache/huggingface -p 18080:18080 \
  ghcr.io/ggml-org/llama.cpp:server-cuda \
  -hf ornith-ai/Ornith-1.5-9B-GGUF:Q4_K_M --jinja -ngl 99 -fa on --ctx-size 16384 \
  --temp 1.0 --top-p 0.95 --top-k 20 --host 0.0.0.0 --port 18080
```
(SGLang third option if both fail tool parsing: `--tool-call-parser
qwen3_coder --reasoning-parser qwen3` per [sglang](../../../wiki/stacks/sglang.md).)

Also verify at download time: base arch in the GGUF metadata / `config.json`
(card implies Qwen lineage but doesn't state the base — record it on the model
page), and whether `presence_penalty 1.5` is settable on the chosen runner.

### 1. Smoke (tok/s + tool-call fidelity + base-arch check)
One code-basics item + one hand-driven HA episode; record gen tok/s, VRAM,
CoT length, native-vs-fallback tool protocol.

### 2. Agentic pair (the decision runs — matched to the standing matrix)
k=3, native protocol (or fallback, recorded), gpt-5.5 user-sim +
`--judge-messages`, vendor general sampling (temp 1.0, top_p 0.95, top_k 20,
presence_penalty 1.5 if the runner exposes it), think=default:
```bash
cd lab/benchmarks
python3 harness/run.py --bench ../../benchmarks/home-automation/bench.json \
  --model hf.co/ornith-ai/Ornith-1.5-9B-GGUF:Q4_K_M --base-model ornith-1.5-9b \
  --tool-protocol native --k 3 --judge-messages --user-model gpt-5.5 \
  --temp 1.0 --top-p 0.95 --top-k 20
python3 harness/run.py --bench ../../benchmarks/email-triage/bench.json \
  --model hf.co/ornith-ai/Ornith-1.5-9B-GGUF:Q4_K_M --base-model ornith-1.5-9b \
  --tool-protocol native --k 3 --judge-messages --user-model gpt-5.5 \
  --temp 1.0 --top-p 0.95 --top-k 20
```
(Adjust `--model`/provider flags to the serving path chosen in step 0; exact
flag names per `harness/README.md`.)

### 3. Coding corroboration (cheap)
code-basics, k=3, vendor coding profile (temp 0.6, top_p 0.95, top_k 20,
presence_penalty 0). 4/4 matches gemma; anything less undercuts the
SWE-bench-70 story at the smoke-test level.

**Cross-host caveat:** the standing agentic rows were measured on the ProArt
P16; capability metrics are machine-independent, tok/s / wall-clock are
per-host — results.csv records the machine.

## Result
<blank — not yet run>

Fields to record: model, quant, runner+version, machine, context, sampling
(incl. whether presence_penalty applied), think label, tool protocol
(native | xml-fallback), obs@3, pass^3, flaky, sem, wall_clock_s, gen tok/s,
VRAM, base arch from GGUF metadata.

## Learnings
<blank — does it displace gemma as strongest local agent; does the vendor
table survive unseen evals; CoT cost per episode; whether Qwen-lineage
template quirks bite on Ollama>
