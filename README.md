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
  hardware/  this machine, the GPU, the NPU
  stacks/    ollama, llama.cpp, vllm, lemonade, unsloth
  models/    one page per model tried
  concepts/  quantization, the llm-wiki method, wsl2 memory, ...
lab/         the playground
  journal/   dated narrative entries (history, insights, questions)
  experiments/  one folder per run: hypothesis -> method -> result -> learnings
  benchmarks/   harness + results
env/         environment setup, pinned versions, .wslconfig template
scripts/     helper CLIs (verify-stack, ...)
```

## Quickstart

```bash
# 1. Verify the machine is ready (GPU, CUDA, Ollama, RAM headroom)
bash scripts/verify-stack.sh

# 2. Smoke-test the daily-driver runner (already installed)
ollama run qwen3.5:4b "Say hi in one short sentence."
```

## This machine (verified 2026-06-14)

ASUS ProArt P16 — RTX 5070 Laptop (8 GB), Ryzen AI 9 HX 370 (NPU), 32 GB host RAM,
**WSL2 Ubuntu 24.04 on Windows 11**. Full details + the important WSL RAM caveat:
[wiki/hardware/proart-p16.md](wiki/hardware/proart-p16.md).

> [!IMPORTANT]
> WSL2 only sees ~15 GB of the 32 GB host RAM by default. Bigger models
> (e.g. DiffusionGemma needs ~18 GB) require raising the cap via
> [`env/wslconfig.template`](env/wslconfig.template). See
> [wiki/concepts/wsl2-memory.md](wiki/concepts/wsl2-memory.md).

## Status

Bootstrapped 2026-06-14. Seed source: [LLM-wiki-context.md](LLM-wiki-context.md)
(Karpathy's original post). See [wiki/log.md](wiki/log.md) for the timeline and
[lab/journal/](lab/journal/) for the narrative.
