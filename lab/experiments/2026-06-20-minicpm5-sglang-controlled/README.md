# MiniCPM5-1B via SGLang — controlled thinking + native tool-calling

- Date: 2026-06-20 (run complete — see Result below)
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

## Result (run 2026-06-20)

**Serving path — pip FAILED, container WORKED.** Stock `pip install sglang`
(0.5.13) on this box **JIT-compiles kernels at runtime** and dies twice for lack
of a toolchain: FlashInfer's KV-index Triton kernel needs **`gcc`** ("Failed to
find C compiler"), and the fused-RoPE `tvm_ffi` kernel needs the **CUDA toolkit**
("Could not find CUDA installation / CUDA_HOME"). This box has the CUDA *runtime*
(driver 13.2) but **no `nvcc` and no `gcc`**. Switching to `--attention-backend
torch_native --disable-cuda-graph` got past the first crash but hit the second.
**Fix = the official container** (`lmsysorg/sglang:latest`, CUDA-13, bundles the
toolchain), run under **rootless Podman + CDI GPU passthrough** (needed
`nvidia-container-toolkit` + `nvidia-ctk cdi generate`; the GPU showed up as
`nvidia.com/gpu=all`). The default `cu130` torch runs on Blackwell **sm_120** with
no cu12 dance. Model loads 2.16 GB on the 8 GB GPU; cuda-graph capture succeeds
**inside** the container. `--mem-fraction-static 0.7 --context-length 16384`.

**`enable_thinking` toggle WORKS (the headline).** Over the OpenAI endpoint,
`chat_template_kwargs={"enable_thinking":false}` -> clean `"Paris"` (no `<think>`);
default -> CoT present. This is the control Ollama lacked. Wired into the harness:
`OpenAICompatibleClient` now sends `chat_template_kwargs.enable_thinking` when
`--think/--no-think` is set (was Ollama-only). ~107-147 gen tok/s.

**Decision-reasoning (llm_judge, opus-4.8, bar 6.0) - clean 0/6 in BOTH modes:**
| Serving | mode | pass@1 | mean score | character |
|---|---|---|---|---|
| Ollama (old) | No-Think | 0/6 | ~0.17/10 | degenerate gibberish / runaway `<think>` |
| **SGLang** | **No-Think** (t=0.7) | **0/6** | **~2.7/10** | coherent, decisive, **shallow/wrong** (inverts risk) |
| **SGLang** | **Think** (t=0.9, 8k) | **0/6** | **~3.0/10** | CoT **completes** (259-2788 tok, no truncation), still self-contradictory |

The serving fix lifted output from *gibberish* (0.17) to *coherent-but-shallow*
(~3) - proving the Ollama score was a **serving artifact** - but MiniCPM5-1B's
judgment genuinely doesn't clear the bar. Same failure shape as VibeThinker
(decisive, misreads the crux).

**Tool-use - SGLang's `minicpm5` parser is BROKEN, but a harness XML fallback
recovers it -> a REAL tool-use signal.** The model emits the **correct tool
intent** (`search_kb` with the right query) in its native **XML**
(`<function name="search_kb"><param ...>`). SGLang 0.5.13's
`--tool-call-parser minicpm5` (vendor-recommended, auto-detected) **swallows that
XML and emits no `tool_calls`** (verified by direct curl: content empty,
`tool_calls: null`). **Fix:** run the server *without* a tool-call parser (XML
stays in `content`) and added `parse_xml_tool_calls()` to the harness clients - a
guarded fallback that converts `<function name=...><param ...>` into native
`tool_calls` when the provider returns none. With that:

| benchmark (native, No-Think) | before (parser swallows) | **after (XML fallback)** |
|---|---|---|
| email-triage (5) | 0/5 | **2/5** (e2, e4) |
| home-automation (12) | n/a | **7/12** (0.583) |

**home-automation 7/12 is the headline:** MiniCPM5-1B handles concrete home
tool-use well - act (h1/h2), confirm-before-unlock (h3), multi-device (h4),
read-only (h6/h11), **ambiguity -> ask (h8)** - and fails the harder ones: refuse
(h5/h10), scene/routine (h7), a second confirm (h9), compound act+read (h12). So
its agentic *tool-use tilt is real*, unlike its abstract reasoning.

`results.csv`: 4 rows kept (decision-reasoning No-Think + Think 0/6; **email-triage
2/5; home-automation 7/12**). Dropped the parser-swallowed 0/5 and earlier
misconfigured runs.

## Learnings

- **Two different verdicts for one model.** Served correctly, MiniCPM5-1B is a
  **weak abstract reasoner** (decision-reasoning 0/6, coherent-but-shallow - a real
  1B ceiling) **but a decent home-automation tool-user** (7/12: act/confirm/read/
  disambiguate). For the home-agent lighthouse that tool-use competence matters
  more than tradeoff-reasoning - so MiniCPM5-1B is **back in the running as a
  tool-executor**, just not as the deliberation brain.
- **The SGLang `minicpm5` parser is broken in 0.5.13** (swallows the XML). The
  durable workaround is the harness's `parse_xml_tool_calls()` fallback +
  **launching the server without `--tool-call-parser`**. Revisit a newer SGLang
  build later; the fallback also helps any XML-tool model.
- **Infra is the durable win:** Blackwell + rootless Podman + CDI + the SGLang
  container is now a working **second runner** for thinking/tool models. Recorded
  on the [SGLang stack page](../../../wiki/stacks/sglang.md). pip SGLang is a dead
  end on this toolchain-less box; the container is the path.
- Fed back into [minicpm5-1b.md](../../../wiki/models/minicpm5-1b.md).

