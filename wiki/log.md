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

## [2026-06-20] note | Aide-model track + /new-aide prompt
Opened a second model track for the **non-generative support models** the home
agent needs: STT (ears), TTS (voice), embeddings (memory), reranker/late-interaction
(router for tool + context selection). Wrote concepts/aide-models.md — the durable
schema: the four classes + home-agent pipeline slot, the per-class **eval contract**
(STT=WER/CER+RTF via jiwer; TTS=round-trip WER + MOS, no audio judge; embeddings=
MTEB NDCG@k/Recall@k; reranker=NanoBEIR **plus** a custom **tool-selection Recall@k**,
e.g. 250 tools -> right one in top-5), and the aide-model **page schema** (I/O
contract replaces sampling/template). Built .github/prompts/new-aide.prompt.md — the
ingest sibling of /new-model that classifies, researches (reuses the last30days
recipe), writes the page, and **stages an external eval** (external-first; hand-roll
only the tool-selection scorer). Key differences captured: aide models are **mostly
not on Ollama** (only some embeddings; STT/TTS/ColBERT run via faster-whisper /
piper-Kokoro / PyLate+FastPLAID), footprint is bound by RTF / throughput / index
size, and the Copilot-CLI judge **can't hear** so TTS naturalness isn't LLM-judgeable.
Grounded the reranker class on **LFM2.5-ColBERT-350M** (Liquid AI, 353M, MaxSim, 11
languages, LFM Open License v1.0, arXiv 2511.23404) — the tool-selection candidate.
No weights pulled, no eval harness built yet (external-first). index updated (Aide
models subsection + concept line).

## [2026-06-20] note | Home-automation benchmark v0.2 (+6 scenarios)
Extended the lighthouse agentic set from 6 to **12 scenarios**, data-only on the
existing tool-set-driven harness (no scorer change). New: **h7** scene/routine
("good night" = all lights off + thermostat 65 + lock front door, routine defined
in scenario policy); **h8** ambiguity -> must `ask` which light before acting
(scored by reusing `require_confirm` on the disambiguated device); **h9** a second
sensitive-confirm (open the garage); **h10** capability-refuse with no tool (order
a pizza -> `say` a decline, change nothing - a non-security refuse contrasting
h5); **h11** multi-device read-only (which doors are unlocked, front unlocked /
back locked); **h12** compound act+read in one turn (set heat 74 AND report the
lock status). Sharpened the *sensitive* definition in the v0.2 scenario policies
(security-**reducing** actions need confirm; locking / closing / lights /
thermostat do not); left v0.1 policy text unchanged so prior results stay
comparable. Validated: `validate_benchmark` passes; all 6 ideal episodes score
correct and two adversarial controls (h8 no-ask, h12 touched-lock) correctly fail
through the real scorer; selftest still ALL PASS. v0.3 backlog (needs harness
work, not data): structured `ask.device`, cross-device dependency ordering,
judge-assisted refuse/confirm message content. Not yet run live against a model.

## [2026-06-20] ingest | LFM2.5-ColBERT-350M aide-model page
First `/new-aide` run — the reranker/late-interaction class. Liquid AI's
LFM2.5-ColBERT-350M (353M, first bidirectional LFM, base LFM2.5-350M-Base): a ColBERT
late-interaction retriever — per-token 128-dim vectors, MaxSim, 32-tok query /
512-tok doc, **11 languages**. Dual-use: PLAID-indexed retrieval or index-free
reranking via PyLate (`trust_remote_code=True`); also **official GGUF for llama.cpp**;
**not an Ollama model**, runs in a venv (Blackwell needs CUDA>=12.8 torch wheel; 353M
fits the 8 GB GPU trivially, CPU-OK). **License read:** LFM Open License v1.0 =
Apache-2.0 + commercial use limited to <$10M-revenue entities — irrelevant for this
personal project, fully usable. Benchmarks: NanoBEIR-multilingual-extended avg
NDCG@10 **0.605** + MKQA-11 Recall@20 **0.694** (beats LFM2-ColBERT, Qwen3-Embedding-
0.6B, and its own dense sibling LFM2.5-Embedding-350M); flagged these test *document*
retrieval, NOT our **tool selection** use-case — though Liquid ships an official
tool-selection demo on this model. Eval staged: NanoBEIR sanity + a hand-rolled
**tool-selection Recall@k** (query -> right tool in top-k from a pool of N) — the
home-agent decision metric and seed for a future benchmarks/tool-selection set, with
an A/B vs the dense sibling. Wrote wiki/models/lfm2.5-colbert-350m.md (aide page
schema, sections 1-9); index Aide subsection updated; experiment staged at
lab/experiments/2026-06-20-lfm2.5-colbert-tool-selection. No weights pulled, no scorer
built (external-first; awaiting go-ahead).

## [2026-06-20] note | PyTorch venv set up + verified (Blackwell)
Stood up the first torch environment on this box: `~/.venvs/pylate` with **torch
2.11.0+cu128** + **pylate 1.6.0** (numpy 2.4.6). Confirmed a real GPU op runs on
**sm_120** (Blackwell) via the new reusable checker
[scripts/check-torch.py](../scripts/check-torch.py) (interpreter-aware: prints
torch/CUDA/device + runs a matmul; exit 1 = missing, 2 = arch/wheel mismatch).
Corrects the prior "no torch" machine fact — there is still **no system torch**,
but the cu128 wheel works in a venv (the standard path for aide models / PyLate /
future vLLM-SGLang). Updated hardware/proart-p16.md (torch-venv row + confirmed-
working note) and the LFM2.5-ColBERT experiment (env now DONE, not pending).

## [2026-06-20] note | Docs-consistency pass (register aide track + SGLang)
Swept the schema/overview docs to match the latest additions (SGLang stack + the
aide-model track had landed in pages/index but not in the canonical docs).
AGENTS.md: new "Models & aide models" convention subsection (two tracks, two
ingest verbs), an SGLang/serving-aware-per-model bullet in stacks constraints
(+`cu128`-verified note, +PyLate/SGLang in the venv list), and a `/new-aide`
pointer on the workflow-verbs line. README: repo-map (+sglang, models = generative
+ aide), workflows table (+`/new-aide`), and a vision paragraph naming the aide
models. wiki/benchmarks/README.md: an "aide models eval differently" callout, the
SGLang local `openai-compatible` target in the local-vs-API section, and **fixed a
stale fact** — the 6/6·5/6 home-automation scores were v0.1 (6 scenarios); marked
them v0.1 and noted v0.2 (12 scenarios) is not yet re-run. Also propagated the
verified `cu128`-on-sm_120 finding to stacks/vllm.md (+a SGLang cross-ref) and
softened the SGLang page's vLLM contrast. Docs-only; index needed no new lines.

## [2026-06-20] ingest | gemma-4-12B-coder-fable5 (Composer2.5 × Fable5) model page
Community Python-coding finetune of the new (~10-day-old) Google Gemma 4 12B
(`gemma4_unified`, dense 11.95B, Apache-2.0, 256K ctx, native thinking), distilled
from execution-verified CoT (Composer 2.5 real + Fable 5 synthetic second-attempt).
Researched via HF card + base model card + last30days (mixed reception: viral but
with real benchmaxxing/degradation skepticism, garbled non-English, narrow Python
specialist). Card ships **no v1 benchmarks** (its one table is the separate v2
agentic model) -> staged a benchmark-it-vs-base experiment. Page + index updated;
experiment stub at lab/experiments/2026-06-20-gemma-4-12b-coder-fable5-first-run.
Fit: Q3_K_M (6.09 GB) full-GPU on 8 GB; Q4_K_M needs CPU offload. Not yet run.

## [2026-06-20] bench | MiniCPM5-1B via SGLang container (clean re-test)
Stood SGLang up to remove the Ollama confounds. **pip SGLang 0.5.13 can't run on
this toolchain-less box** (JIT kernels need gcc + CUDA toolkit we lack: FlashInfer
Triton → C compiler, fused-RoPE tvm_ffi → CUDA_HOME). **Fix = the official
container** (`lmsysorg/sglang:latest`, CUDA-13, bundles the toolchain) under
**rootless Podman + CDI** (installed nvidia-container-toolkit + `nvidia-ctk cdi
generate`; RTX 5070 visible in-container; default cu130 runs on sm_120). Cleaned up
the dead pip venv (-9.8 GB). Lowered `.wslconfig` memory 24→16 GB (deferred reboot).
Harness: `OpenAICompatibleClient` now sends `chat_template_kwargs.enable_thinking`
for `--think/--no-think` (was Ollama-only); fixed `/` in model-name raw filenames;
selftest green. **Findings:** `enable_thinking` toggle WORKS. Decision-reasoning
still **0/6** but *coherent* — No-Think mean ~2.7, Think mean ~3.0 (CoT completes,
no truncation) vs Ollama's ~0.17 gibberish → the Ollama score was a serving
artifact; real verdict = coherent-but-shallow (genuine 1B ceiling, NOT a home-agent
reasoning brain). Tool-use (email-triage native) **0/5 — blocked by SGLang**:
0.5.13's `minicpm5` parser swallows the model's `<function>` XML and emits no
`tool_calls` (model intent is correct). results.csv: 3 rows kept. Stack page +
model page + experiment updated. NEXT: newer SGLang build or XML-tolerant harness
fallback to salvage a fair tool-use score.

## [2026-06-20] bench | MiniCPM5-1B tool-use unblocked via XML fallback (2/5, 7/12)
Did the "XML-tolerant fallback" from the previous entry. Verified MiniCPM5's exact
emitted format (`<function name="search_kb"><param name="query">...</param></function>`)
against a parser-less server, then added `parse_xml_tool_calls()` to harness
`client.py` — a guarded fallback (both clients) that converts `<function ...>` XML
in `content` into native `tool_calls` + a synthesized valid assistant message when
the provider returns none. **Run the SGLang server WITHOUT `--tool-call-parser`**
(0.5.13's `minicpm5` parser swallows the XML); the fallback reads the raw XML.
Result: email-triage native **0/5 → 2/5**, home-automation native **7/12 (0.583)** —
MiniCPM5-1B handles act / confirm-unlock / read-only / **ambiguity→ask**, fails
refuse / scene / compound. **Two verdicts for one model:** weak abstract reasoner
(decision-reasoning 0/6) but a **decent home-automation tool-executor** (7/12) — its
tool-use tilt is real, back in the running as an executor (not the deliberation
brain). selftest +4 checks (XML fallback) ALL PASS. results.csv: 4 MiniCPM5 rows
(dec-reasoning No-Think/Think, email-triage 2/5, home-automation 7/12). Updated
client/selftest + experiment + model page + stack page (omit the broken parser,
use the fallback).

## [2026-06-20] note | pivot gemma-4 ingest to v2-only + quant-config sweep
Dropped the v1 (pure-coding) page + experiment (git-removed) and replaced with the
v2 **coding + agentic** variant
(gemma-4-12B-agentic-fable5-composer2.5-v2), the home-automation-relevant one
(native Gemma 4 tool-use, needs llama.cpp `--jinja`). v2 = v1 coder + agentic
trajectories + a general slice; Fable 5 CoT rebuilt with Opus 4.8. Author self-eval
(local, relative, Q8 greedy, 20 tasks) ~3.5x base on tau2-telecom, slightly below
base on retail/MMLU-Pro by design - **unverified**. No Q2_K this release. Staged a
3-cell 8 GB sweep (Q3_K_M full-GPU vs Q4_K_M+q4_0 KV vs Q4_K_M+CPU offload) for
throughput + code-basics + home-automation quality. Prereq: llama.cpp not built
here (no host CUDA toolkit) -> build via rootless-podman CUDA. Page + index
updated; experiment at lab/experiments/2026-06-20-gemma-4-12b-v2-quant-config-sweep.

## [2026-06-20] note | llama.cpp CUDA container verified + v2 sweep expanded to 5 cells
Stood up llama.cpp via the official prebuilt CUDA image
(ghcr.io/ggml-org/llama.cpp:server-cuda, build 9737) in rootless Podman+CDI -
same pattern as the SGLang container. GPU visible (RTX 5070, **only ~6999 of 8150
MiB free** - real budget ~6.8 GB). Grounded in primary docs: llama.cpp docker.md
(server-cuda/-cuda13 images, entrypoint=llama-server), server README (-ctk/-ctv
q4_0, -ngl, -fa, --jinja default-on, -hf auto-download, -fit, timings tok/s), and
NVIDIA CDI docs. Marked stacks/llama-cpp.md container-verified with the recipe.
Expanded the gemma-4-12B v2 quant sweep to **5 cells** (added A2: Q3+q4_0 KV to
isolate KV effect; D: Q4 full-GPU @4K to isolate offload) - the 6.8 GB budget
means Q4_K_M likely cannot run full-GPU (expect OOM), making the sweep about
whether Q4 runs at all vs Q3. Container up; model download + run pending confirm.

## [2026-06-20] ingest | stacks/podman-gpu.md — portable GPU-container setup
Factored the shared one-time GPU-in-Podman setup (was buried in stacks/sglang.md)
into a canonical stacks/podman-gpu.md so the container serving stack can be
reproduced on a new box from one page. Concrete + verified: podman 4.9.3,
nvidia-container-toolkit 1.19.1, CDI at /etc/cdi/nvidia.yaml (device
nvidia.com/gpu=all), the shared run pattern (--device nvidia.com/gpu=all
--security-opt=label=disable --ipc=host + shared ~/.cache/huggingface mount), and
a SGLang-vs-llama.cpp "pick per model" table. De-duplicated the CDI steps in
sglang.md + cross-linked llama-cpp.md and hardware/proart-p16.md; added the index
line. Machine-specific bits (free VRAM, -ngl, mem-fraction) kept on the hardware
/ experiment pages per the portability rule.

## [2026-06-20] note | consolidated backlog board + fixed stale experiment headers
Added wiki/backlog.md (the single forward "what's next" queue, link-heavy:
now/next/research/models/maintenance), linked from index.md. Fixed two stale
experiment headers that said "not yet run" but had completed Results: the
MiniCPM5 SGLang-controlled run (2026-06-20) and the MiniCPM5 Ollama first-run
(2026-06-19, the run that motivated the SGLang re-test).
