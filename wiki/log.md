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

## [2026-06-19] note | Docs consistency pass
Brought docs in sync with the current state: judge backend is now opus-4.8 via
Copilot CLI everywhere (llm_judge.py, harness + benchmark READMEs, AGENTS.md,
/benchmark prompt - "never a local small model"); root README gained a repo-map
entry for benchmarks/ + .github/ and a Workflows section; wiki/benchmarks overview
got a current-state status line. Added the first lab/journal entry since kickoff
(benchmark framework + VibeThinker arc).

## [2026-06-19] note | Podman sandbox for code_tests (now working)
Built the locked-down Podman runner (scorers/code_exec.py): `--network none`,
read-only rootfs, tmpfs workdir, memory/pid/cpu caps, non-root, no-new-privileges,
caps dropped. `--code-sandbox {podman|local-unsafe}` (podman recommended, gated).
Verified: network blocked + real passes/fails (selftest 31/31, incl 3 podman).
Added `--no-think` - thinking models over-think trivial code tasks and exhaust
`--num-predict` before emitting code (empty output). First sandboxed run: authored
`code-basics` smoke set, qwen3.5:4b **3/4** with `--no-think`. Image:
docker.io/library/python:3.12-slim (WSL2 podman per jcentner/podman-wsl-setup).
`code_tests` is the third fully-working scorer.

## [2026-06-19] note | API inference first-class + vision pass (docs)
Gave the project a lighthouse: **evaluate models local AND API to pick the brain
for a local-agent home-automation system** (external benchmarks for my interests -
decision-making, agentic/triage; custom for my use-cases - home automation, email
triage; capability AND cost). Top-down docs pass before any runtime change: vision
in README + AGENTS north-star; schema generalized **per-machine -> per-environment**
(per-provider + per-date for API); API inference named a first-class runner with
`cost_usd`; copilot-instructions + all four workflow prompts taught `--provider`/
cost; wiki benchmark overview rewritten around **external-first** + a local-vs-API
section; BFCL identified as the first external wrap (runs here via Ollama
`:11434/v1` `--skip-server-setup`, or an API model directly; install `bfcl-eval`).
Journal: lab/journal/2026-06-19-api-first-class-and-vision.md. Plan (local scratch):
tmp/api-inference-refactor-plan.md. Next: harness provider code (L3) + the
`benchmark-harness` skill.

## [2026-06-19] ingest | BFCL benchmark page + bfcl-eval wrap setup
First external benchmark wrap (the external-first strategy in action). Wrote
wiki/benchmarks/bfcl.md (BFCL_v4 categories, FC/Prompt, AST+state+subset scoring,
contamination, run recipe). Installed `bfcl-eval 2026.3.23` in `~/.venvs/bfcl`
(outside repo); needed a manual `pip install soundfile` (transitive qwen_agent
gap). **Key finding (verified in base_oss_handler.py):** BFCL has NO generic
Ollama handler. `--skip-server-setup` loads the model's HF tokenizer and sends
BFCL's *exact registered model name* to the endpoint, so a tag like `qwen3.5:4b`
won't run; the local route needs Ollama serving the registered name (e.g.
`Qwen/Qwen3-4B-Instruct-2507`) + matching tokenizer, or vLLM/sglang (the 8 GB
stretch). Practical route = an API model (`glm-4.6-FC`/`qwen3-4b-FC`, needs a key)
or pulling the matching GGUF. Subset run pending a model decision. Skill:
.github/skills/wrap-external-benchmark. Experiment:
lab/experiments/2026-06-19-bfcl-wrap-setup.

## [2026-06-19] note | BFCL deprioritized -> model-agnostic agentic scorer
Decision after the BFCL finding + a last30days scan of current 8 GB models. BFCL's
**registered-models-only** design (per-model tool-call parsers) structurally lags
the frontier - it can't score brand-new small models (MiniCPM-5, Qwen3.5-4B) until
someone writes a handler. For a fast-moving space that's the wrong daily driver.
Pivot: the **primary** agentic eval becomes a **lightweight tau-bench-style scorer
in our harness** - model-agnostic (any Ollama tag / API model, day one), with the
**Copilot CLI as the user-simulator** (same mechanism as the judge) and
state/policy scoring on our use-cases (home automation, email-triage escalation).
[tau3-bench](https://github.com/sierra-research/tau2-bench) is the external
cross-check. BFCL kept as a published-comparison **reference** (status: reference);
demoted in wiki/benchmarks/README + index + bfcl.md. Removed the local
`~/.venvs/bfcl` (5.5 GB) + runs/bfcl. last30days standout new model: **MiniCPM-5**
(agentic tool-use, 4-8 GB tier) - queued for `/new-model`. GLM-5.2 = the new
open-weights leader but API-scale, not 8 GB-local.

## [2026-06-19] ingest | MiniCPM5-1B model page
OpenBMB's MiniCPM5-1B ("MiniCPM-5"), released 2026-05-19: a 1B dense
`LlamaForCausalLM` on-device model, Apache-2.0, 128K context, hybrid Think/No
Think in one checkpoint. Positioned as 1B-class open-source SOTA (avg 42.57 vs
35.61 in-class), strongest at agentic tool use, code, and competition math — the
tool-use tilt makes it a real home-agent-brain candidate, unlike the math-only
specialists. Stock arch = loads in Ollama/llama.cpp/vLLM/SGLang directly; GGUF
Q4_K_M 688 MB / Q8_0 1.15 GB / F16 2.17 GB, runs trivially on the 8 GB GPU
(community: 100+ tok/s). Flagged the competition-math benchmaxxing risk (Reasoning
RL on DAPO-Math-17k) — verify on fresh problems + the tool-use axis. Wrote
wiki/models/minicpm5-1b.md; staged lab/experiments/2026-06-19-minicpm5-1b-first-run.
Weights not pulled yet (awaiting go-ahead).
