---
title: Ornith-1.5-9B
tags: [model, agentic, coding, tool-use, thinking, dense, qwen-lineage, to-try]
updated: 2026-08-19
status: to-try
---

# Ornith-1.5-9B

Ornith AI's **agentic-coding 9B dense** model (released **2026-08-18**), the
edge-deployable member of the MIT-licensed Ornith-1.5 family (9B dense /
35B-A3B MoE / 397B MoE). The research story is **end-to-end self-improvement**:
extending Ornith-1.0's self-scaffolding, the model proposes its own training
tasks (rewarded for validity, ~20%-success frontier difficulty, and novelty),
generates task-specific scaffolds (rewarded for alignment and
resistance-to-gaming), and produces solution rollouts — all three stages
jointly optimized with GRPO. For this repo the story is simpler: a first-party,
MIT, tool-native agentic model that fits the 8 GB class and claims to beat
Qwen3.5-9B across coding, reasoning, and agentic benchmarks — a direct
challenger to [gemma-4-12b-agentic](gemma-4-12b-agentic-fable5.md) for
strongest local agent.

Sources: [HF model card](https://huggingface.co/ornith-ai/Ornith-1.5-9B) ·
[official GGUF](https://huggingface.co/ornith-ai/Ornith-1.5-9B-GGUF) ·
[collection](https://huggingface.co/collections/ornith-ai/ornith-15) ·
[Ornith-1.5 blog](https://ornith.ai/ornith_1_5.html) ·
[Ornith-1.0 blog](https://ornith.ai/ornith_1_0.html) ·
[announcement](https://x.com/ornith_/status/2090074077084127302).
Community signal via last30days (2026-08-19, release-day — thin by definition;
re-scan in a few weeks): [HN 164pts](https://news.ycombinator.com/item?id=49362401) ·
[r/LocalLLaMA release thread](https://www.reddit.com/r/LocalLLaMA/comments/1vsn2xw/we_have_q38_35b_at_home_3x_new_ornith_15_released/) ·
[9B first impressions](https://www.reddit.com/r/LocalLLaMA/comments/1vsvr7f/ornith15_9b_might_not_be_bad_at_all/).

## Identity & shape

| Field | Value |
|---|---|
| Maker | Ornith AI (startup; Ornith-1.0 family: 12M HF downloads in 30 days) |
| Released | 2026-08-18 (Ornith-1.0 predecessor: 2026-06) |
| Params | **9B dense** (~19 GB bf16) |
| Base model | **Qwen lineage, exact base unstated on card** — card benches vs Qwen3.5-9B and uses `qwen3` parsers; community says the family is "mainly a fine-tune of Qwen 3.6" ([Reddit](https://www.reddit.com/r/LocalLLaMA/comments/1vsn2xw/we_have_q38_35b_at_home_3x_new_ornith_15_released/)); the 35B card states Qwen3.5-MoE base. **Verify from `config.json` at download time.** |
| Modality | text (the 35B-A3B sibling is multimodal; this one is not) |
| Context | **262,144** native; ~1M via YaRN factor 4.0 (static YaRN slightly hurts short-context quality — enable only when needed) |
| Thinking | **on by default** — assistant turns open with `<think>…</think>` |
| Tool use | OpenAI-style `tools` → native `tool_calls`; parsers: vLLM `--tool-call-parser qwen3_xml --reasoning-parser qwen3`, SGLang `--tool-call-parser qwen3_coder --reasoning-parser qwen3` |
| License | **MIT** (whole family incl. quants) |
| Runtimes | transformers ≥ 5.8.1, vLLM ≥ 0.19.1, SGLang ≥ 0.5.9, llama.cpp/Ollama via official GGUF |
| Recommended sampling | general: **temp 1.0, top_p 0.95, top_k 20, min_p 0, presence_penalty 1.5**; precise coding: **temp 0.6, top_p 0.95, top_k 20, presence_penalty 0** |

## What it's for (and not for)

- **For (vendor):** agentic coding is the training target — terminal work,
  SWE-bench-style repo tasks, tool use, long-horizon agentic workflows.
- **Not-for is unstated** — the card lists no limitations beyond the YaRN
  caveat. Note the family's benchmark tables are coding/agentic/reasoning
  only; nothing on instruction-following, safety, or multilinguality. The
  home-agent fit (confirm flows, refusals, ambiguity→ask) is exactly the
  untested surface our suite measures.

## Benchmarks (vendor, HF card — unverified)

Comparison set per the card; all vendor-run:

| Benchmark | Ornith-1.5-9B | Ornith-1.0-9B | Qwen3.5-9B | Qwen3.6-35B-A3B | Gemma-4-31B |
|---|---|---|---|---|---|
| Terminal-Bench 2.1 (Terminus-2) | 46.2 | 43.1 | 21.3 | 52.5 | 42.1 |
| SWE-bench Verified | 70.6 | 69.4 | 53.2 | 73.4 | 52.0 |
| SWE-bench Pro | 47.5 | 42.9 | 31.3 | 49.5 | 35.7 |
| NL2Repo | 32.4 | 27.2 | 16.2 | 29.4 | 15.5 |
| GPQA Diamond | 86.4 | 82.5 | 81.7 | 86.0 | 84.3 |
| HLE (with tools) | 30.5 | 26.4 | 24.5 | 28.9 | 26.5 |
| MCP-Atlas | 54.2 | 49.4 | 46.8 | 62.8 | 55.0 |
| Toolathlon-Verified | 41.2 | 33.4 | 29.6 | 41.7 | 52.8 |
| ClawEval | 66.5 | 63.1 | 53.2 | 68.7 | 48.5 |

Headline: a 9B claiming ~2× Qwen3.5-9B on terminal/repo coding and parity
with 30B-class models on GPQA. **Extraordinary-claims caveat:** these are
vendor numbers on a day-old release with heavy benchmark-training incentive
(the self-improvement loop optimizes toward exactly these task shapes) —
treat as unverified until our harness says otherwise
([eval-reliability](../concepts/eval-reliability.md), and the
[gemma](gemma-4-12b-agentic-fable5.md) / [VibeThinker](vibethinker-3b.md)
benchmaxxing pattern).

## Community signal (release day, 2026-08-19)

- **Skepticism is the median take** — "I dare you to say 'big if true'"
  ([release thread](https://www.reddit.com/r/LocalLLaMA/comments/1vsn2xw/we_have_q38_35b_at_home_3x_new_ornith_15_released/),
  45 upvotes); benchmaxxing suspicion is explicit.
- **But Ornith-1.0 survived one independent check:** a user ran 1.0 on Aider
  (not in Ornith's own tables) and it scored ~Qwen3.6-27B level
  ([thread](https://www.reddit.com/r/LocalLLaMA/comments/1vsnllv/ornith_15_9b_dense_and_35b397b_moes/)) —
  off-table performance held up once already.
- Early 9B hands-on impressions positive but anecdotal
  ("[might not be bad at all](https://www.reddit.com/r/LocalLLaMA/comments/1vsvr7f/ornith15_9b_might_not_be_bad_at_all/)").
- **Official GGUFs include MTP heads** (community quantizers noticed theirs
  lacked them) — speculative decoding is on the table, same pattern as
  gemma's MTP draft.
- HN front page ([164 pts](https://news.ycombinator.com/item?id=49362401));
  discussion centers on the self-improvement method, not run reports.

## Size & resource requirements (machine-independent)

Official GGUF ([Ornith-1.5-9B-GGUF](https://huggingface.co/ornith-ai/Ornith-1.5-9B-GGUF)):

| Quant | File size |
|---|---|
| Q4_K_M | **5.63 GB** |
| Q5_K_M | 6.47 GB |
| Q6_K | 7.36 GB |
| Q8_0 | 9.53 GB |
| BF16 | 17.9 GB |

**Format note:** the family's FP8/NVFP4 builds exist only for the 35B-A3B and
397B MoEs — there is no 9B NVFP4/FP8. Moot for this fleet anyway: NVFP4 needs
Blackwell FP4 kernels (vLLM/TensorRT-LLM) and the smallest NVFP4 artifact is
the ~19 GB 35B; GGUF K-quants are the 9B's only sub-bf16 path.

On the 8 GB class: **Q4_K_M full-GPU** is the target (5.63 GB + KV — smaller
file than gemma's verified Q3_K_M 6.09 GB, so the same 16K-f16-KV envelope
should close; measure at test time). Q5_K_M is the stretch at reduced context;
Q8_0 needs partial offload. KV math: [quantization](../concepts/quantization.md).

## How to run it

Card-official paths (template fidelity unverified — see caveats):

```bash
# Ollama (daily driver)
ollama run hf.co/ornith-ai/Ornith-1.5-9B-GGUF:Q4_K_M

# llama.cpp server, OpenAI-compatible
llama-server -hf ornith-ai/Ornith-1.5-9B-GGUF:Q4_K_M \
  --jinja -ngl 99 -fa on --ctx-size 16384 \
  --temp 1.0 --top-p 0.95 --top-k 20 \
  --host 0.0.0.0 --port 18080
```

SGLang (if the GGUF/llama.cpp path fails tool parsing):
`--tool-call-parser qwen3_coder --reasoning-parser qwen3` — the
[sglang](../stacks/sglang.md) serving-aware routing.

## Harness caveats (read before benchmarking)

1. **Template fidelity gate (the MiniCPM5 lesson):** verify the served
   template opens `<think>` and round-trips OpenAI `tools` into
   `message.tool_calls` before trusting any agentic run. Qwen-lineage XML
   tool markup means the harness's `parse_xml_tool_calls()` fallback likely
   works if native parsing fails — probe one episode first.
2. **`presence_penalty 1.5`** in the vendor's general-task sampling is
   unusually high; check the harness/runner exposes it (Ollama maps it;
   llama-server flag is `--presence-penalty`). Record whatever is actually
   applied.
3. **Thinking default-on** — run and record `think=default` per house policy;
   CoT cost per agentic episode is unmeasured. Coding runs use the temp-0.6
   profile; agentic runs the temp-1.0 profile (matches qwen's t=1.0 rows for
   flakiness comparability).

## Why it matters for the north star

The first first-party release aimed at the exact gap between our two
champions: gemma-4-12b's ceiling (HA v0.4 obs@3 **0.947**, ET v0.3 **1.000**)
and qwen3.5:4b's reliability (pass^3 **0.684 / 0.833**). Same Qwen lineage as
qwen3.5:4b, agentic-RL post-training like gemma's finetune, but MIT, smaller
than gemma (5.63 GB Q4 vs 6.09 GB Q3), and with a coding claim strong enough
that [code-basics](../benchmarks/README.md) plus the agentic pair covers all
three axes in one session. If the vendor table survives contact with HA/ET at
k=3, this displaces gemma as default strongest-local-agent.

## Can it run here?

Q4_K_M targets any 8 GB host in [hardware/](../hardware/); per-machine verdict
at test time. First-run experiment (torrent):
[lab/experiments/2026-08-19-ornith-1.5-9b-first-run](../../lab/experiments/2026-08-19-ornith-1.5-9b-first-run/README.md).

## Related

- [models/gemma-4-12b-agentic-fable5.md](gemma-4-12b-agentic-fable5.md) — the incumbent to beat; same agentic-finetune species, community vs first-party.
- [models/lfm2.5-2.6b.md](lfm2.5-2.6b.md) — the other staged challenger (reliability/footprint lane vs Ornith's capability lane).
- 35B-A3B sibling: multimodal MoE (~3B active, ~20 GB Q4) — penciled in [backlog](../backlog.md) "Models to consider"; over the 8 GB/16 GB envelopes here.
- [benchmarks/home-automation.md](../benchmarks/home-automation.md) · [benchmarks/email-triage.md](../benchmarks/email-triage.md) · [concepts/eval-reliability.md](../concepts/eval-reliability.md) · [stacks/sglang.md](../stacks/sglang.md) · [concepts/quantization.md](../concepts/quantization.md)
