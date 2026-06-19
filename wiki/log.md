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

## [2026-06-18] ingest | VibeThinker-3B model page
First `/new-model` run. Researched WeiboAI VibeThinker-3B via last30days (Reddit/
X/YouTube/GitHub) + primary sources (GitHub, HF card, arXiv 2606.16140). 3B dense
Qwen2.5-based verifiable-reasoning specialist, MIT, released 2026-06-16. Wrote
models/vibethinker-3b.md (benchmarks, run paths, caveats) and staged a first-run
experiment. Fits 8 GB full-GPU at Q8_0; watch context size (long CoT) and
benchmaxxing skepticism. See lab/experiments/2026-06-18-vibethinker-3b-first-run.

## [2026-06-18] note | Benchmark framework — M1 + M2
Stood up the benchmark system. Schema in AGENTS.md (definitions vs results;
benchmark = prompts + scoring harness). New wiki/benchmarks/ (overview + 2 pages:
humaneval-plus wrapping evalplus, example-arithmetic authored), top-level
benchmarks/ for authored datasets, extended lab/benchmarks/ results schema
(sampling/seed/k/judge/machine). Built lab/benchmarks/harness/ (Ollama client +
equivalence/code_exec/llm_judge scorers + run.py CLI); offline selftest passes
10/10. Plan: tmp/benchmark-framework-plan.md. Next: /benchmark, /new-benchmark,
/author-benchmark prompts.

## [2026-06-19] note | Benchmark framework — Batch A (post-critique hardening)
Acted on an external critique (tmp/benchmark-framework-critique.md). Added
fail-closed validate_benchmark() (rejects missing/empty/mismatched keys, empty
tests, dup ids, unknown methods) before any model call; gated code_tests behind
--code-sandbox (refuses to run model-written code unsandboxed); renamed the metric
to observed_pass_at_k with a caveat; the runner now records full perf metadata
(token totals, wall time, tok/s, ollama version, raw file). Documented the critic
answer-key exception. Dropped the math benchmark (example-arithmetic) per user.
Selftest now 24/24. Deferred to Batch B: locked-down Podman sandbox mode, a proven
upstream coding wrapper, and a minimal agentic scorer.

## [2026-06-19] bench | VibeThinker-3B as a decision-maker (first real run)
End-to-end: local model under test (Ollama) + frontier judge (claude-opus-4.8 via
Copilot CLI). Built the copilot-cli skill + CopilotCLIJudge (opus-4.8 is now the
only judge; local-model judge removed; selftest 28/28). Pulled VibeThinker Q8 GGUF
(~71 tok/s, full GPU). Authored a fresh decision-reasoning set (6 tradeoff
scenarios) and ran it: **1/6 above bar, mean ~4.3/10** - decisive but frequently
misreads the crux (math slip, inverted risk logic). Specialty doesn't transfer to
practical judgment; confirms "not for general use". First results.csv row. See
lab/experiments/2026-06-19-vibethinker-decision-reasoning.
