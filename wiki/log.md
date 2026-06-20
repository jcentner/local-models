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

## [2026-06-19] note | Agentic harness (model-agnostic tau-bench-style scorer)
Built the flexible agentic eval BFCL couldn't give us (4th working scorer:
`agentic`). Runs ANY model (Ollama tag or API) via a **prompt-mode JSON tool
protocol** - no native tool-calling or model registration. `harness/agentic.py`:
episode runner (agent under test <-> **Copilot-CLI user-simulator** <-> mocked
tools over mutable state) + tolerant JSON action parser; `CopilotCLIUser` is the
user-sim twin of the judge (`--user-model`). `scorers/agentic.py`: deterministic
state/policy scoring (terminal action reply|escalate + required/forbidden tools).
run.py wires `method=agentic`; selftest +15 (mocked agent+user) = ALL PASS.
Authored `benchmarks/email-triage` v0 (5 scenarios: answer-from-KB vs escalate vs
search-then-decline). **Verified end-to-end live:** qwen3.5:4b passed e1
(search_kb -> reply), 0 malformed steps. Docs synced (harness/wiki READMEs, AGENTS,
index). tau3-bench remains the external cross-check; BFCL stays a reference.

## [2026-06-19] bench | MiniCPM5-1B on email-triage (agentic) — 0/5 + template fix
First real model run through the agentic harness. **Template gotcha (fixed):** the
bare `hf.co/openbmb/MiniCPM5-1B-GGUF` Ollama pull is **degenerate** ("Short Un In
Short Un...") — Ollama doesn't evaluate the GGUF Jinja template; you must supply the
official Go `TEMPLATE` (ranges over `.Messages`, no stray `<s>`). After the fix:
coherent, ~150-185 tok/s, 2.9 GB full-GPU. **Result: email-triage 0/5** at
recommended No-Think (temp 0.7) AND temp 0 (not sampling). Failure modes: can't
suppress `<think>` over Ollama (`--no-think` ignored) so the JSON action truncates;
never commits to a terminal reply/escalate (all `no_reply`); misused tool args
(`question` vs `query`). **Honest caveat:** partly a **protocol mismatch** — our
prompt-mode "JSON only" rollout is adversarial to a hybrid-thinking model whose
native tool format is XML (SGLang `minicpm5` parser); does NOT refute the tau-2-Bench
headline. **Harness takeaway:** build a **native-tool-calling mode** (Ollama
`/api/chat` `tools` + `message.tool_calls`) for a fair re-test. Model page ->
status tried + finding; experiment writeup updated. results.csv: one representative
row (kept the 4096/0.7 run, dropped the under-budgeted + duplicate rows).

## [2026-06-19] bench | Native tool-calling mode for the agentic harness
Built the `--tool-protocol native` path (the planned fair-footing fix): clients
gained a `tools` arg + normalized `tool_calls` + `tool_result_message` (Ollama
`/api/chat` `tools` with object-args/`tool_name`; OpenAI `tools` with
string-args/`tool_call_id`), `agentic.py` got a native branch + tool schema, run.py
a `--tool-protocol prompt|native` flag (recorded in the judge column). Verified APIs
against the Ollama + OpenBMB docs. Selftest now 41/41 (added native-episode + both
client tool-parse cases). **Live-validated** on qwen3.5:4b (tool-capable Ollama
template): email-triage **3/5 prompt -> 4/5 native** (native correctly escalates the
refund it flubbed in prompt-mode; the one miss fabricated a "no" instead of
escalating). **MiniCPM5 caveat:** its stock Ollama template is tool-blind, so its
fair re-test still needs SGLang `--tool-call-parser minicpm5` over the
openai-compatible provider — harness side ready, server not yet. Docs synced
(harness README, email-triage README, model page, experiment writeup, skill).

## [2026-06-19] bench | Home-automation agentic set (the lighthouse use-case)
Generalized the agentic harness to be **tool-set driven** (the abstraction earned
by a second domain): a `ToolSet` = schemas + per-tool behavior (act | respond |
respond_terminal) + state + apply-fn + scenario context. `run_episode` is now
domain-agnostic; `bench.json` declares `toolset` (support | home_automation).
Added the **home_automation** set: tools get_status / set_device / ask / say over a
device world; the home scorer checks device **end-state**, **forbidden devices
untouched**, **ask-before-sensitive** (confirm), and required/forbidden tools.
New benchmark `benchmarks/home-automation` (6 scenarios: act, param-act,
confirm-before-unlock, multi-device, refuse-unsupported, read-only status). The
agent is told its device roster (ids+types, not states) so it addresses real
devices; states are still discovered via get_status. Selftest 51/51 (added home +
confirm-flow + validation cases). Email-triage native unchanged at 4/5 (no
regression). **qwen3.5:4b home-automation: prompt 6/6, native 5/6** - opposite of
email-triage (native 4/5 > prompt 3/5): native's eagerness to call tools made it
**over-actuate AND fabricate** on the refuse scenario (unlocked the front door,
opened the garage, claimed it "disabled the security system" with no such tool),
which the scorer correctly failed. A real safety signal. Docs synced (harness +
benchmarks README, index, skill).

## [2026-06-19] bench | MiniCPM5-1B on decision-reasoning (llm_judge) — 0/6
Ran the fresh decision-reasoning set (6 tradeoff scenarios, opus-4.8-judged) on
minicpm5-1b over Ollama: **0/6, mean ~0.17/10** (vs VibeThinker-3B 1/6, mean
~4.3/10). Dominant failure = **runaway/degenerate `<think>`**: at Think temp 0.9 it
produced gibberish with leaking `<|fim_middle|>` tokens; at No-Think temp 0.7 it
produced 16-19k-char repetitive rambles that restate the prompt and never land a
`Recommendation:`. Same root cause as the email-triage tool-use finding: MiniCPM5's
hybrid thinking is **uncontrollable over Ollama** (Go-template path has no
`enable_thinking`). **Caveat:** confounded by the serving limitation, not a clean
reasoning verdict - but VibeThinker (also thinking, also over Ollama) produced
parseable answers, so MiniCPM5's degeneration is worse; clean read deferred to a
controlled-template run (Transformers/vLLM/SGLang). Kept the representative temp-0.7
row in results.csv, dropped the misconfigured temp-0.9 (Think-sampling-on-No-Think-
template) row. Minor: one judge call returned invalid JSON on an 18k-char degenerate
input (harness scored it not-correct; judge-robustness note). Model page + decision-
reasoning wiki updated.

## [2026-06-19] note | Harden agentic harness (gpt-5.5 cross-model review)
Adopted the **commit-as-you-go + background cross-model review** workflow
(copilot-cli-background-tasks skill): a read-only **gpt-5.5** audit of the agentic
commits ran in the background, then I triaged each finding (confirm with file:line
or push back). Fixes landed: (1) **Critical** - the home refuse scenario (h5) could
pass via a silent no-op; now `required_tools:["say"]` so a refusal must actually be
spoken. (2) **Major** - native multi-tool messages left unmatched `tool_call`s
before the next request (invalid on strict OpenAI providers); now synthesize a tool
result for every unprocessed sibling after a respond/terminal. (3) **Major** -
fail-closed validation now rejects answer-key references to unknown devices or tools
(a typo silently disabled a guard). (4) **Major** - non-dict tool arguments (a list/
scalar) are coerced to `{}` in both clients (would have crashed `apply()`). (5)
**Minor** - validation uses the `TOOLSETS` registry instead of a hardcoded set.
**Pushed back** on two: native parallel tool calls are legitimate (bounded, no
scoring impact) - documented not changed; and `require_confirm` is a v0.1 proxy
(ask-before-act, not ask-named-device) - documented + deferred to v0.2. Also added
`tools_used` to the agentic raw write (offline re-scoring footgun). Selftest 58
checks ALL PASS; both agentic benchmarks still validate; prompt-mode home 6/6 holds
(h5 re-scored True with the new key). Review notes: tmp/review-agentic-harness.md.

## [2026-06-20] ingest | SGLang stack page + MiniCPM5 controlled-serving experiment
Researched SGLang (LMSYS, Apache-2.0) from official docs + OpenBMB's MiniCPM5
card. Wrote stacks/sglang.md: the second runner for thinking/tool models —
`--reasoning-parser`, `enable_thinking`, and `--tool-call-parser minicpm5`
(vendor-confirmed; SGLang's own parser table lags and omits it). Reached via the
harness `--provider openai-compatible`, no client change. Blackwell sm_120 fits
the default CUDA-13 build; key quirks = FlashInfer JIT vs missing nvcc, and
Podman-vs-Docker GPU passthrough. Staged lab/experiments/2026-06-20-minicpm5-
sglang-controlled to re-test MiniCPM5-1B (decision-reasoning + native tool-use)
with Ollama's confounds removed. Supports the serving-aware-per-model direction:
Ollama stays daily driver; thinking/tool models route to SGLang.
