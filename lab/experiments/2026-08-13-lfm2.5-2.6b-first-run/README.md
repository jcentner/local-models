# LFM2.5-2.6B — first run (agentic re-baseline candidate)

- Date: 2026-08-13 (staged; not yet run)
- Hypothesis / question: Liquid's on-device agentic flagship claims
  instruction-following + tool-use wins over Qwen3.5-9B at 2.6B. Does it beat
  our reliability champ **qwen3.5:4b** (HA v0.4 obs@3 0.789 / pass^3 0.684, ET
  v0.3 0.917 / 0.833) — and approach gemma-4-12b's ceiling (HA 0.947) — from a
  1.7 GB Q4 file? Secondary: does always-on thinking cost episode wall-clock
  the way qwen's CoT did on decision-reasoning, or did agentic RL train it to
  think briefly and act?
- Model page: [wiki/models/lfm2.5-2.6b.md](../../../wiki/models/lfm2.5-2.6b.md).
- Setup: **torrent** ([hardware page](../../../wiki/hardware/torrent.md)) — RTX
  3070 Ti 8 GB (Ampere sm_86), WSL2. **Ollama is not installed on this box yet**;
  neither the llama.cpp nor SGLang container has been stood up here (recipes:
  [podman-gpu](../../../wiki/stacks/podman-gpu.md)). First run on torrent doubles
  as the serving-stack bring-up for this host.

## Method

### 0. Serving bring-up (pick one; verify template fidelity before benchmarking)
Preflight either path with `bash scripts/verify-stack.sh`.

**Path A — Ollama (daily-driver parity with the qwen rows):**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama run hf.co/LiquidAI/LFM2.5-2.6B-GGUF:Q8_0 "Say hi in one short sentence."
```
Gate: inspect `ollama show --template` + one `/api/chat` call with a dummy tool.
Confirm (a) output is coherent (not MiniCPM5-style template degeneration),
(b) `<think>` appears/strips sanely, (c) native `tools` round-trips into
`message.tool_calls`. If (c) fails → Path B.

**Path B — llama.cpp CUDA container (controlled, `--jinja`):**
```bash
podman run --rm --device nvidia.com/gpu=all --security-opt=label=disable --ipc=host \
  -v ~/.cache/huggingface:/root/.cache/huggingface -p 18080:18080 \
  ghcr.io/ggml-org/llama.cpp:server-cuda \
  -hf LiquidAI/LFM2.5-2.6B-GGUF:Q8_0 --jinja -ngl 99 -fa on --ctx-size 16384 \
  --temp 0.1 --top-k 50 --repeat-penalty 1.1 --host 0.0.0.0 --port 18080
```
If neither stack parses the Pythonic `<|tool_call_start|>` protocol into
`tool_calls`, add a Pythonic fallback to `harness/client.py` next to
`parse_xml_tool_calls()` (the MiniCPM5 pattern) — serve parser-less and let the
harness read the raw markup.

### 1. Smoke (tok/s + tool-call fidelity)
One code-basics item + one hand-driven HA episode; record gen tok/s, VRAM, and
whether tool calls arrive native or via fallback.

### 2. Agentic pair (the decision runs — matched to the standing matrix)
k=3, native protocol (or fallback, recorded), gpt-5.5 user-sim + `--judge-messages`,
vendor sampling (temp 0.1 / top_k 50 / repeat_penalty 1.1), think=default:
```bash
cd lab/benchmarks
python3 harness/run.py --bench ../../benchmarks/home-automation/bench.json \
  --model hf.co/LiquidAI/LFM2.5-2.6B-GGUF:Q8_0 --base-model lfm2.5-2.6b \
  --tool-protocol native --k 3 --judge-messages --user-model gpt-5.5 \
  --temp 0.1 --top-k 50 --repeat-penalty 1.1
python3 harness/run.py --bench ../../benchmarks/email-triage/bench.json \
  --model hf.co/LiquidAI/LFM2.5-2.6B-GGUF:Q8_0 --base-model lfm2.5-2.6b \
  --tool-protocol native --k 3 --judge-messages --user-model gpt-5.5 \
  --temp 0.1 --top-k 50 --repeat-penalty 1.1
```
(Adjust `--model`/provider flags to the serving path chosen in step 0; exact
flag names per `harness/README.md`.)

**Cross-host caveat:** every existing agentic row was measured on the ProArt
P16; capability metrics are machine-independent but tok/s / wall-clock columns
are per-host — results.csv records the machine, keep the comparison honest.

### 3. Optional third axis
decision-reasoning v0.2 (`llm_judge`) — the vendor says knowledge/reasoning is
the weak side; a cheap k=3 run quantifies the brain-vs-executor split the way
MiniCPM5's 0/6 did. Watch the always-on CoT cost first (step 1 tok/s ×
observed CoT length); if it's qwen-scale (~5-7K tokens/item) defer.

## Result
<blank — not yet run>

Fields to record: model, quant, runner+version, machine, context, temp/top_k/rep_pen,
think label, tool protocol (native | pythonic-fallback), obs@3, pass^3, flaky,
sem, wall_clock_s, gen tok/s, VRAM.

## Learnings
<blank — does it displace qwen3.5:4b as default brain candidate; does the
Pythonic protocol need a harness fallback; CoT length in agentic episodes;
whether temp-0.1 reliability advantage shows up as structurally higher pass^3>
