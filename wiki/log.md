# Log

Append-only timeline of what happened. Newest at the bottom. Each entry:
`## [YYYY-MM-DD] type | title`  (types: ingest, query, bench, experiment, lint, note).
Grep the last few with: `grep "^## \[" wiki/log.md | tail -5`.

## [2026-06-14] note | Repo bootstrapped
Set up the LLM-wiki + lab + journal skeleton. Verified the machine
(WSL2 Ubuntu 24.04, RTX 5070 8 GB, Ryzen AI 9 HX 370, Ollama 0.20.2 with two
qwen3.5 models). Captured the key WSL2 RAM-cap finding. Seed source:
LLM-wiki-context.md (Karpathy's post). See lab/journal/2026-06-14-kickoff.md.

## [2026-06-14] ingest | Karpathy llm-wiki.md gist
Distilled the canonical three-layer pattern (raw -> wiki -> schema) and the
ingest/query/lint loop into concepts/llm-wiki-method.md.

## [2026-06-14] ingest | Hardware + stacks + DiffusionGemma
Seeded hardware/ (proart-p16, blackwell-rtx5070, xdna2-npu), stacks/ (ollama,
llama-cpp, vllm, lemonade, unsloth), models/diffusiongemma, and concepts/
(quantization, wsl2-memory) from initial research.
