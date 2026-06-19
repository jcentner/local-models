# BFCL wrap — setup + integration finding (2026-06-19)

**Type:** experiment / ingest support. **Machine:** Daedalus (ProArt P16, RTX 5070
8 GB, WSL2). **Goal:** stand up [BFCL](../../../wiki/benchmarks/bfcl.md) as the
first external benchmark wrap and run a small tool-use subset against a local model.

## Hypothesis
`bfcl-eval` can run a small subset (e.g. `irrelevance`, `live_multiple`) against a
local Ollama model via Ollama's OpenAI-compatible `:11434/v1` endpoint with
`--skip-server-setup`, giving a cheap tool-use signal on this 8 GB box.

## Method
```bash
python3 -m venv ~/.venvs/bfcl
~/.venvs/bfcl/bin/pip install bfcl-eval          # 2026.3.23 (pulls torch + a big tree)
~/.venvs/bfcl/bin/pip install soundfile          # CLI import gap (qwen_agent -> soundfile)
export PATH="$HOME/.venvs/bfcl/bin:$PATH"
export BFCL_PROJECT_ROOT="$HOME/utils/local-models/lab/benchmarks/runs/bfcl"  # gitignored
bfcl --help; bfcl models; bfcl test-categories; bfcl generate --help
```
Then inspected `constants/category_mapping.py`, `SUPPORTED_MODELS.md`, and
`model_handler/local_inference/base_oss_handler.py` to find the local-run path.

## Result
- **Install works** but has a packaging gap: `bfcl --help` crashes with
  `ModuleNotFoundError: No module named 'soundfile'` until `soundfile` is added
  (qwen_agent imports it transitively). After that the CLI is healthy.
- **No subset run yet.** Root cause (verified in source): BFCL has **no generic
  Ollama/OpenAI-compatible pseudo-model**. Models are API (provider key) or
  self-hosted `💻` (vLLM/sglang). `--skip-server-setup` + `LOCAL_SERVER_ENDPOINT/
  PORT` still makes `base_oss_handler.py` (a) load the model's **HF tokenizer +
  config** and (b) send BFCL's **exact registered model name** to the endpoint. So
  pointing it at Ollama serving `qwen3.5:4b` cannot work — the name/tokenizer must
  match a registered model (e.g. `Qwen/Qwen3-4B-Instruct-2507`).

## Learnings
- BFCL is built for **API models** (keys) or **vLLM/sglang self-hosting** — not
  drop-in Ollama. On this box the practical routes are:
  1. **API model** (`glm-4.6-FC`, `qwen3-4b-FC`, ...): cheapest + most meaningful
     (a real candidate home-agent brain); needs a provider key. *Recommended.*
  2. **Pull the matching GGUF** into Ollama under the registered name + alias, then
     `--skip-server-setup`. Doable, more setup, real local number.
  3. vLLM/sglang self-host: the known 8 GB / Blackwell sm_120 stretch.
- This validates the **external-first** strategy's reality check from the
  [vision journal](../../journal/2026-06-19-api-first-class-and-vision.md): "wrap
  external" is a real wiring task, not free. The finding is itself the value.
- Reusable wrap know-how captured in the `wrap-external-benchmark` skill.

## Next
Pick a run route (API key vs pull matching GGUF) and run a scoped subset
(`irrelevance,live_multiple` first), then fold the category accuracy into
[results.csv](../../benchmarks/README.md) as `scoring=tool_calls` with the subset noted.
