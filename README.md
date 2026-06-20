# local-models

A one-stop playground for running LLMs locally — organized as a self-maintaining
knowledge base (the [LLM Wiki pattern](wiki/concepts/llm-wiki-method.md)) plus a
hands-on lab. The wiki is the compounding record of what I learn; the lab is
where I actually run, optimize, and benchmark models; the journal is the
narrative thread (and the raw material for blog / Twitter posts).

> GitHub Copilot (VS Code + CLI) is the **agent that drives** the research here.
> The local models are the **subject of study**, not Copilot's backend.

## The three layers (Karpathy LLM-wiki)

| Layer | Folder | Who owns it |
|---|---|---|
| Immutable sources | [`raw/`](raw/) | You curate; never edited by the agent. Git-ignored. |
| Compiled knowledge | [`wiki/`](wiki/) | The agent writes & maintains. You read. |
| The schema / operating rules | [`AGENTS.md`](AGENTS.md) + [`.github/copilot-instructions.md`](.github/copilot-instructions.md) | Co-evolved by you + agent. |

The loop is **ingest → query → lint** (see [AGENTS.md](AGENTS.md)). Knowledge is
compiled once and kept current, not re-derived on every question.

## Repo map

```
raw/         immutable source docs (articles, papers, screenshots) — local only
wiki/        LLM-maintained knowledge base
  index.md   catalog of every page (read this first)
  log.md     append-only timeline (greppable: "## [date] type | title")
  hardware/  one page per host under test (dev boxes + the deploy target)
  stacks/    ollama, llama.cpp, vllm, sglang, lemonade, unsloth
  models/    one page per model tried (generative + aide: STT/TTS/embeddings/retrieval)
  benchmarks/ what each benchmark measures + how it's scored (definitions)
  concepts/  quantization, the llm-wiki method, wsl2 memory, ...
benchmarks/  authored benchmark datasets (prompts + separate answer keys)
lab/         the playground
  journal/   dated narrative entries (history, insights, questions)
  experiments/  one folder per run: hypothesis -> method -> result -> learnings
  benchmarks/   harness (runner + scorers) + results.csv (per-machine)
env/         environment setup, pinned versions, .wslconfig template
scripts/     helper CLIs (verify-stack, ...)
tools/       local utilities
  run-viewer/  minimal web app to browse benchmark runs + wiki (Python + Preact, read-only)
.github/
  prompts/   workflow slash-prompts (see Workflows below)
  skills/    agent skills (e.g. copilot-cli: frontier-model judge backend)
```

## Workflows

Slash-prompts in [`.github/prompts/`](.github/prompts/) drive the recurring work:

| Prompt | Does |
|---|---|
| `/new-model <model>` | research a model (last30days + primary sources), write its wiki page, stage testing |
| `/new-aide <model>` | research a support model (STT / TTS / embeddings / retrieval), document it, stage a get-a-feel test |
| `/new-benchmark <name>` | ingest + document an existing public benchmark |
| `/benchmark <model>` | recommend relevant benchmarks, estimate cost, run via the harness, record results |
| `/author-benchmark <scenario>` | author a fresh held-out benchmark with a gpt-5.5/opus-4.8 critic loop |

Benchmark scoring is `equivalence` (math), `code_tests` (sandboxed execution),
`llm_judge` (frontier judge = opus-4.8 via Copilot CLI), or `agentic` (model-agnostic
tool-use rollout with a Copilot-CLI user-simulator). Models can be **local
(Ollama) or API (OpenAI-compatible)** — results capture capability *and* cost. See
[wiki/benchmarks/README.md](wiki/benchmarks/README.md).

## Quickstart

```bash
# 1. Verify the machine is ready (GPU, CUDA, Ollama, RAM headroom)
bash scripts/verify-stack.sh

# 2. Smoke-test the daily-driver runner (already installed)
ollama run qwen3.5:4b "Say hi in one short sentence."

# 3. Browse benchmark runs (and the wiki) in a local viewer
python3 tools/run-viewer/server.py   # → http://127.0.0.1:8777
```

## Dev box (verified 2026-06-14)

ASUS ProArt P16 — RTX 5070 Laptop (8 GB), Ryzen AI 9 HX 370 (NPU), 32 GB host RAM,
**WSL2 Ubuntu 24.04 on Windows 11**. One of several hosts under test (generate a
new host's page with `scripts/host-profile.sh`). Full details + the important WSL
RAM caveat: [wiki/hardware/proart-p16.md](wiki/hardware/proart-p16.md).

> [!IMPORTANT]
> WSL2 only sees ~15 GB of the 32 GB host RAM by default. Bigger models
> (e.g. DiffusionGemma needs ~18 GB) require raising the cap via
> [`env/wslconfig.template`](env/wslconfig.template). See
> [wiki/concepts/wsl2-memory.md](wiki/concepts/wsl2-memory.md).

## Vision

**Evaluate models — local *and* API — to decide which should run a local-agent
suite: home automation, email triage, a website/product support bot (more
use-cases as they arise).** The dev/test boxes and the eventual deployment target
are different machines, so capability findings stay portable while hardware facts
are per-host. The benchmark wiki is flexible but not overcomplicated:
**external** benchmarks where they match my interests (LLMs as decision-makers,
agentic workflows / triage) and **custom** benchmarks for my use-cases, runnable
against local or API inference, with results (capability + cost) captured
uniformly. Local (Ollama) is the daily driver and the bias; API inference (e.g.
Z.AI GLM) is a first-class comparison point — a $20/mo API may beat buying
hardware to run a weaker model.

The agent also needs **aide models** around its brain — STT (ears), TTS (voice),
embeddings (memory), retrieval (the tool router) — tracked separately via
[`/new-aide`](.github/prompts/new-aide.prompt.md)
([concepts/aide-models.md](wiki/concepts/aide-models.md)). Build toward the lighthouse.

## Status

Bootstrapped 2026-06-14. Seed source: [LLM-wiki-context.md](LLM-wiki-context.md)
(Karpathy's original post). See [wiki/log.md](wiki/log.md) for the timeline and
[lab/journal/](lab/journal/) for the narrative.
