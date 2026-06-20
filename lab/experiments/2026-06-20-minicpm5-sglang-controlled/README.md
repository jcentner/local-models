# MiniCPM5-1B via SGLang — controlled thinking + native tool-calling

- Date staged: 2026-06-20 (not yet run)
- Machine: ASUS ProArt P16 (RTX 5070 Laptop, 8 GB, Blackwell sm_120, WSL2) —
  see [proart-p16](../../../wiki/hardware/proart-p16.md)
- Stack under test: [SGLang](../../../wiki/stacks/sglang.md) (new second runner)
- Model: [minicpm5-1b](../../../wiki/models/minicpm5-1b.md) — `openbmb/MiniCPM5-1B`
  (BF16 safetensors, **not** the GGUF; SGLang loads HF weights)

## Hypothesis

MiniCPM5-1B's two failures so far — 0/5 on [email-triage](../../../benchmarks/email-triage/README.md)
(tool-use) and 0/6 on [decision-reasoning](../../../wiki/benchmarks/decision-reasoning.md) —
were **confounded by Ollama**, not pure incapability:

- Ollama can't disable the hybrid `<think>` (`--no-think`/`think:false` ignored
  by this GGUF) -> long CoT truncates before a final answer.
- Ollama's Go template for MiniCPM5 is **tool-blind** (no `.Tools`) -> it can't
  emit `tool_calls` at all, so the model never gets a fair native-tool run.

SGLang removes both confounds: `enable_thinking` controls the CoT, and the
vendor-confirmed `--tool-call-parser minicpm5` converts its XML tool calls to
OpenAI `tool_calls`. **Prediction:** scores improve materially under controlled
serving; if they don't, the limitation is the model, not the runner.

## Fit verdict (this machine)

Comfortable. BF16 weights ~2.2 GB on the 8 GB GPU; set
`--mem-fraction-static 0.7` and `--context-length 16384` so the static KV pool
doesn't claim all of VRAM. [WSL RAM](../../../wiki/concepts/wsl2-memory.md) is a
non-issue at 1B. The risk is **serving setup** (FlashInfer JIT vs missing `nvcc`;
Podman-vs-Docker GPU passthrough), not capacity — see the
[SGLang stack page](../../../wiki/stacks/sglang.md#the-real-quirks-to-expect-verify-on-first-run).

## Method (planned)

### 0. Stand up SGLang (resolve the serving path first)

```bash
python3 -m venv ~/.venvs/sglang && source ~/.venvs/sglang/bin/activate
pip install --upgrade pip uv && uv pip install "sglang[srt]>=0.5.12"
# If FlashInfer JIT fails for lack of nvcc:
#   add --attention-backend triton --sampling-backend pytorch
# If the pip build misbehaves on Blackwell, fall back to the CUDA-13 docker image
#   via Podman CDI (--device nvidia.com/gpu=all --ipc=host --shm-size 32g).
```

### 1. Smoke test (serving sanity + thinking toggle)

```bash
python -m sglang.launch_server --model-path openbmb/MiniCPM5-1B \
  --port 30000 --mem-fraction-static 0.7 --context-length 16384 &
# Recommended sampling: Think temp 0.9/top_p 0.95; No-Think temp 0.7/top_p 0.95.
curl http://localhost:30000/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"openbmb/MiniCPM5-1B","messages":[{"role":"user","content":"Who are you?"}],"max_tokens":128,"temperature":0.7}'
# Confirm: coherent output, and that enable_thinking=false (via chat_template_kwargs
# in extra_body) actually suppresses <think>. Record the exact request field used.
```

### 2. Decision-reasoning re-test (No-Think, isolates reasoning)

```bash
cd lab/benchmarks
python3 -m harness.run --benchmark ../../benchmarks/decision-reasoning \
  --model openbmb/MiniCPM5-1B --provider openai-compatible \
  --base-url http://localhost:30000/v1 --api-key-env SGLANG_KEY \
  --temperature 0.7 --num-predict 4096 --judge-model claude-opus-4.8
# Goal: a CLEAN reasoning verdict (vs Ollama 0/6, mean ~0.17/10) now that the
# final "Recommendation:" can actually be reached. Compare to VibeThinker 1/6.
```

### 3. Tool-use re-test (native, the whole point)

```bash
# Relaunch with the tool parser:
python -m sglang.launch_server --model-path openbmb/MiniCPM5-1B \
  --port 30000 --tool-call-parser minicpm5 --mem-fraction-static 0.7 &
python3 -m harness.run --benchmark ../../benchmarks/email-triage \
  --model openbmb/MiniCPM5-1B --provider openai-compatible \
  --base-url http://localhost:30000/v1 --api-key-env SGLANG_KEY \
  --tool-protocol native --user-model claude-opus-4.8
# Also run home-automation (home_automation toolset) the same way.
# Goal: a FAIR native-tool score (vs Ollama 0/5, which was a protocol mismatch).
```

Harness note: the openai-compatible client + `native` protocol already parse
`message.tool_calls` ([client.py](../../benchmarks/harness/client.py)); no harness
change needed beyond pointing `--base-url` at SGLang. `--no-think` is
Ollama-only — over SGLang, control thinking via the request body instead.

## Result

_Pending first run._ Record per stage: serving path that worked (pip vs Podman;
attention backend), tok/s + VRAM, decision-reasoning score, email-triage +
home-automation native scores, and whether `enable_thinking=false` reliably
suppresses CoT. Write rows to `results.csv` with
`provider=openai-compatible`, `runner=openai-compatible-harness`,
`endpoint=sglang-local`.

## Learnings

_Pending._ Key question to answer cleanly: **is MiniCPM5-1B a viable home-agent
brain once served properly, or does the 1B ceiling hold even with the confounds
removed?** Feed the verdict back into
[minicpm5-1b.md](../../../wiki/models/minicpm5-1b.md) and the
[SGLang stack page](../../../wiki/stacks/sglang.md).
