# MiniCPM5-1B first run (smoke + tool-use tilt)

- Date: 2026-05-19 model release; run 2026-06-19 (Ollama path — results below; motivated the [SGLang controlled re-test](../2026-06-20-minicpm5-sglang-controlled/README.md))
- Machine: ASUS ProArt P16 (RTX 5070 Laptop, 8 GB, WSL2) — see [proart-p16](../../../wiki/hardware/proart-p16.md)
- Question: Does MiniCPM5-1B actually deliver as a small **on-device tool-use /
  reasoning** model, or is the headline competition-math just DAPO-Math
  benchmaxxing? Is a 1B model *reliable* enough to be a home-agent brain?
- Model: [minicpm5-1b](../../../wiki/models/minicpm5-1b.md) (OpenBMB official GGUF)
- Quant: start **Q8_0** (1.15 GB) — safest at 1B; later sweep Q4_K_M (688 MB)
- Runner: Ollama (daily driver) running the HF GGUF directly; SGLang only if
  testing native `minicpm5` tool-call parsing

## Fit verdict (this machine)

Trivial. Q8_0 (~1.2 GB) or even F16 (~2.2 GB) fits **fully on the 8 GB GPU**
(`-ngl 99`) with a large context; KV at 8–32K adds only a few hundred MB.
[WSL RAM](../../../wiki/concepts/wsl2-memory.md) is a non-issue at 1B. No
wslconfig change needed.

## Method (as run, 2026-06-19)

```bash
# 1. Pull the official GGUF
ollama pull hf.co/openbmb/MiniCPM5-1B-GGUF:Q8_0      # 1.2 GB

# 2. CRITICAL: create the alias with the OFFICIAL MiniCPM5 Go TEMPLATE.
#    Ollama does NOT evaluate the GGUF's embedded Jinja chat template - it falls
#    back to the Modelfile TEMPLATE. The auto-detected template (single-turn
#    .System/.Prompt + a stray leading <s>) produces DEGENERATE output
#    ("Short Un In Short Un In..."). The cookbook template ranges over .Messages:
cat > Modelfile <<'MF'
FROM hf.co/openbmb/MiniCPM5-1B-GGUF:Q8_0
TEMPLATE """{{- if .Messages -}}
{{- range .Messages -}}
<|im_start|>{{ .Role }}
{{ .Content }}<|im_end|>
{{ end -}}
<|im_start|>assistant
{{ end -}}"""
PARAMETER stop "<|im_end|>"
PARAMETER stop "</s>"
PARAMETER temperature 0.7
PARAMETER top_p 0.95
PARAMETER num_ctx 8192
MF
ollama create minicpm5-1b -f Modelfile     # then "Paris." coherent; ~150-185 tok/s

# 3. Benchmark: the model-agnostic AGENTIC scorer (email-triage), not BFCL.
cd lab/benchmarks
python3 -m harness.run --benchmark ../../benchmarks/email-triage \
  --model minicpm5-1b --temperature 0.7 --top-p 0.95 --num-ctx 16384 \
  --num-predict 4096 --seed 0 --user-model claude-opus-4.8
# also ran temp 0 (greedy) as a confirmation; and decision-reasoning is a TODO.
```

## Fit verdict + speed (this machine, verified)
Q8_0 loads at **2.9 GB, 100% GPU**, num_ctx up to 16-32K, **~150-185 tok/s**.
Trivial fit, as predicted. The binding issue is *behavior*, not resources.

## Result
**email-triage v0.1 (agentic): 0/5** at recommended No-Think sampling
(temp 0.7, num_predict 4096) **and 0/5 at temp 0** (greedy) - not a sampling
artifact. Contrast: qwen3.5:4b passed e1 (search_kb -> reply) cleanly. Failure
modes (from the raw episodes):
- **Can't suppress thinking over Ollama.** `--no-think` (Ollama `think:false`) is
  ignored by this GGUF - it emits long `<think>` CoT every step. The CoT truncates
  mid-thought -> no parseable JSON action (`_malformed`).
- **Never commits to a terminal action.** All 5 episodes end `no_reply`: it loops
  on `search_kb` / malformed steps and never emits `reply` or `escalate` within
  the step budget.
- **Wrong tool-arg schema.** When it does emit JSON it called `search_kb(question=...)`
  instead of `search_kb(query=...)`, so its searches miss.

## Learnings
- **The MiniCPM5 Ollama template is a required fix** (above) - the bare `hf.co`
  pull is degenerate. This is the headline reproducibility gotcha.
- **0/5 is partly a protocol mismatch, not pure incapability.** Our prompt-mode
  "emit ONE JSON object, nothing else" protocol is adversarial to a *hybrid-thinking*
  1B whose thinking can't be turned off over Ollama and whose **native** tool-call
  format is **XML** (parsed by SGLang's `minicpm5` parser into OpenAI `tool_calls`).
  So this does **not** refute the headline tau-2-Bench 79.5 - it shows the model needs
  its native tool path. A *fair* tool-use number wants **SGLang native parsing**
  (the [8 GB/Blackwell stretch](../../../wiki/stacks/vllm.md)).
- **Harness implication (high-value, now DONE 2026-06-19):** added a **native
  tool-calling mode** to the agentic harness (`--tool-protocol native`: Ollama
  `/api/chat` `tools` + OpenAI `tools`, parsing `message.tool_calls`) as an
  alternative to prompt-mode. Validated live on qwen3.5:4b (3/5 prompt -> 4/5
  native). **But MiniCPM5's stock Ollama template is tool-blind**, so its fair
  re-test still needs SGLang `--tool-call-parser minicpm5` over the
  `openai-compatible` provider - the harness side is ready, the server isn't yet.
- A 1B model on a strict multi-step custom protocol is unreliable here; whether
  that's the model or the protocol is exactly what the native-mode test would isolate.

## Next
- **Re-run MiniCPM5 fairly** via SGLang `minicpm5` parser + `--tool-protocol native
  --provider openai-compatible` (native mode is built; needs SGLang stood up).
- Run [decision-reasoning](../../../wiki/benchmarks/decision-reasoning.md) on it
  (llm_judge) to contrast 1B tool-tilted generalist vs VibeThinker-3B math specialist
  on practical judgment - no tool protocol involved, so it isolates reasoning.
- Quant sweep Q4_K_M vs Q8_0 once a fair tool-use path exists.
