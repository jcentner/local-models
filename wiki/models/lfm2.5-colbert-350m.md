---
title: LFM2.5-ColBERT-350M
tags: [aide, reranker, embeddings, retrieval, late-interaction, colbert, multilingual, to-try]
updated: 2026-06-20
status: to-try
---

# LFM2.5-ColBERT-350M

A **late-interaction retriever** (ColBERT-style) from **Liquid AI** — part of the
**LFM2.5 retriever pair** (released alongside the dense bi-encoder
[LFM2.5-Embedding-350M](https://huggingface.co/LiquidAI/LFM2.5-Embedding-350M)),
the **first bidirectional** members of the LFM family. It encodes queries and
documents into **per-token** 128-dim vectors and scores them with **MaxSim** —
preserving much of a cross-encoder's expressivity at near bi-encoder cost. For
this repo it is the **router** [aide model](../concepts/aide-models.md): the
candidate for **tool selection / context management** (rank a large tool pool down
to the few relevant to a query) and for **RAG reranking**.

> Liquid ships an **official tool-selection demo** built on this exact model
> ([HF Space: LiquidAI/colbert-tool-selection](https://huggingface.co/spaces/LiquidAI/colbert-tool-selection)) —
> our intended use-case is a first-class one for it, not a stretch.

Sources: [HF LiquidAI/LFM2.5-ColBERT-350M](https://huggingface.co/LiquidAI/LFM2.5-ColBERT-350M) ·
[GGUF](https://huggingface.co/LiquidAI/LFM2.5-ColBERT-350M-GGUF) ·
[blog "LFM2.5 retrievers"](https://www.liquid.ai/blog/lfm2-5-retrievers) ·
[LFM2 Technical Report arXiv 2511.23404](https://arxiv.org/abs/2511.23404) ·
[base LFM2.5-350M-Base](https://huggingface.co/LiquidAI/LFM2.5-350M-Base) ·
[PyLate](https://github.com/lightonai/pylate) ·
[Liquid Nanos collection](https://huggingface.co/collections/LiquidAI/liquid-nanos) ·
[license](https://www.liquid.ai/lfm-license). Community signal is light (a
research-grade retriever, not a hyped chat model) — facts here are primary-source.

## 1. Identity & license

| Field | Value |
|---|---|
| Maker | Liquid AI |
| Family | LFM2.5 / **Liquid Nanos** (task-specific edge models); base [LFM2.5-350M-Base](https://huggingface.co/LiquidAI/LFM2.5-350M-Base) |
| Sibling | [LFM2.5-Embedding-350M](https://huggingface.co/LiquidAI/LFM2.5-Embedding-350M) — dense bi-encoder (single 1024-dim vector); smaller/faster index, slightly lower accuracy |
| Paper | LFM2 Technical Report ([arXiv 2511.23404](https://arxiv.org/abs/2511.23404), Nov 28 2025) |
| License | **LFM Open License v1.0** (see below) |

**License (read it).** [LFM Open License v1.0](https://www.liquid.ai/lfm-license)
is **Apache-2.0 with one added clause**: free, royalty-free, perpetual use/modify/
distribute **except** that **Commercial Use ends if your Legal Entity's annual
revenue reaches $10M USD** (then you must buy a commercial license). No copyleft
(fine-tunes may stay proprietary); attribution required; research and qualified
non-profit use exempt. **For this personal home-automation project the threshold
is irrelevant** — fully usable. Flag it only if this ever ships in a $10M+
commercial product.

## 2. Class & pipeline slot

**Reranker / late-interaction retriever** (dual-use: first-stage **retrieval**
with a PLAID index, *or* pure **reranking** on top of another retriever). In the
[home-agent pipeline](../concepts/aide-models.md#the-four-classes) it is the
**router**: narrow a big set of candidate **tools** (or RAG passages) to the
relevant handful the chat brain should see — directly the "many tools -> top-k,
manage context" use case (and Liquid's own showcased demo).

## 3. I/O contract

Replaces the sampling/chat-template block of a generative model:

| Property | Value |
|---|---|
| Input | text (queries and documents, encoded separately) |
| **Query max length** | **32 tokens** |
| **Document max length** | **512 tokens** (transformer `max_seq_length` 511) |
| **Output** | **multi-vector** — one **128-dim** vector per token (not a single embedding) |
| **Similarity** | **MaxSim** (sum over query tokens of max cosine to any doc token) |
| Languages | **11** — English, Spanish, German, French, Italian, Portuguese, Arabic, Swedish, Norwegian, Japanese, Korean |
| `is_query` flag | encode with `is_query=True` for queries, `False` for documents (asymmetric) |
| `trust_remote_code` | **required** (`True`) — applies the bidirectional patches |

The multi-vector output is the defining trait: storage and scoring cost scale with
**tokens x 128**, not one vector per doc — handled by the PLAID index (compressed)
or computed on the fly for reranking. The dense sibling trades this for a single
1024-dim cosine vector (smaller index, slightly lower accuracy).

## 4. Architecture & backbone

| Field | Value |
|---|---|
| Params | **~353M** |
| Backbone | **LFM2.5-350M-Base + bi-directional patches** (`Lfm2BidirectionalModel`) — first bidirectional LFM |
| Layers | 17 (**10 gated short-range conv + 6 GQA attention + 1 dense**) |
| Vocab | 64,402 |
| Projection | Dense 1024 -> 128 (no bias, identity activation) |
| Modality | text only |
| Training precision | BF16 |

The LFM2 conv/attention hybrid is why a 350M model encodes a query in ~8 ms on a
laptop (see speed below).

## 5. Size & footprint per format (machine-independent)

| Format | Size | Notes |
|---|---|---|
| safetensors (BF16) | ~0.7 GB | native precision (HF tensor type BF16) |
| **GGUF (llama.cpp)** | varies by quant | official [LFM2.5-ColBERT-350M-GGUF](https://huggingface.co/LiquidAI/LFM2.5-ColBERT-350M-GGUF) (fp16 + quants) |

**Binding constraint is not weights** (tiny) — it's **index size** and **encode
throughput**. A PLAID multi-vector index is larger than a single-embedding index
(tokens x 128, PLAID-compressed); the dense sibling is the smaller-index option.
For a home-scale tool/doc set (hundreds to low-thousands of items) both are
negligible.

## 6. Runtime / serving

**Not an Ollama chat model**, but two real runtimes:

1. **[PyLate](https://github.com/lightonai/pylate) + [FastPLAID](https://github.com/lightonai/fast-plaid)** (the reference path) — full indexing/retrieval/rerank API in Python (sentence-transformers under the hood). Needs `trust_remote_code=True`.
2. **llama.cpp via the official GGUF** — Liquid measured query-embedding latency here (~8 ms on an M4 Max), so the lighter llama.cpp path works for the encode step.

A 350M encoder runs **trivially on the 8 GB GPU** (and acceptably on CPU). GPU-arch
note: PyTorch inference on [Blackwell sm_120](../hardware/blackwell-rtx5070.md)
needs a **CUDA >= 12.8 torch wheel**; use a venv (this box's torch lives in a venv).

### Install + reranking (index-free — the tool-selection path)
```bash
python3 -m venv ~/.venvs/pylate && source ~/.venvs/pylate/bin/activate
pip install -U pylate            # pulls torch + sentence-transformers + fast-plaid
```
```python
from pylate import rank, models

model = models.ColBERT(model_name_or_path="LiquidAI/LFM2.5-ColBERT-350M", trust_remote_code=True)

queries = ["turn off the kitchen lights"]
documents = [[
    "light.set_state(room, on|off) - control a room's lights",
    "lock.set_state(door, locked|unlocked) - control a door lock",
    "thermostat.set(temp) - set the target temperature",
    # ... up to N tool descriptions
]]
documents_ids = [[0, 1, 2]]

q = model.encode(queries, is_query=True)
d = model.encode(documents, is_query=False)
ranked = rank.rerank(documents_ids=documents_ids, queries_embeddings=q, documents_embeddings=d)
# -> documents ranked by MaxSim; take top-k as the tools to expose to the brain
```

### Indexed retrieval (PLAID — larger corpora / RAG)
```python
from pylate import indexes, models, retrieve
model = models.ColBERT(model_name_or_path="LiquidAI/LFM2.5-ColBERT-350M", trust_remote_code=True)
index = indexes.PLAID(index_folder="pylate-index", index_name="index", override=True)
index.add_documents(documents_ids=ids, documents_embeddings=model.encode(docs, is_query=False))
retriever = retrieve.ColBERT(index=index)
scores = retriever.retrieve(queries_embeddings=model.encode(queries, is_query=True), k=5)
```

## 7. Benchmarks (official, with source)

Evaluated on Liquid's **multilingual NanoBEIR-extended** (NDCG@10) and **MKQA-11**
(cross-lingual Recall@20). Averages, vs notable baselines:

| Model | Type | NanoBEIR avg NDCG@10 | MKQA-11 avg Recall@20 |
|---|---|---|---|
| **LFM2.5-ColBERT-350M** | late | **0.605** | **0.694** |
| LFM2.5-Embedding-350M (sibling) | dense | 0.577 | 0.691 |
| Qwen3-Embedding-0.6B | dense | 0.556 | 0.638 |
| LFM2-ColBERT-350M (prior gen) | late | 0.540 | 0.646 |
| GTE-ModernColBERT-v1 (150M) | late | 0.489 | 0.459 |

Headline: **best-in-class multilingual retrieval** at 350M — beats its own dense
sibling, the prior LFM2-ColBERT, and Qwen3-Embedding-0.6B; strong cross-lingual.
**Speed (llama.cpp, M4 Max, fp16):** query embedding ~8 ms (docs cached);
query+doc+MaxSim end-to-end ~34 ms. Enterprise GPU serving as low as ~1-3 ms.

> **Relevance caveat for us.** NanoBEIR/MKQA measure *document* retrieval. Our
> use-case is **tool selection** (short, structured tool descriptions; small N;
> "is the right tool in top-k"). The headline numbers say "competent multilingual
> retriever" — Liquid's tool-selection demo is encouraging, but the home-agent
> fitness still needs the custom eval below on *our* tools.

## 8. Eval path

Per [external-first](../benchmarks/README.md): wrap the standard retrieval eval,
**and** hand-roll the one use-case scorer with no off-the-shelf equivalent.

- **Standard (sanity / comparison):** a NanoBEIR-multilingual-extended slice via
  PyLate — confirms the model reproduces its published NDCG@10 on this box.
- **Custom (the decision metric) — tool-selection Recall@k:** a small labeled set
  of `{query -> relevant tool id(s)}` over a pool of N home-automation tool
  descriptions; rerank; score **Recall@k** (relevant tool in top-k, e.g. k=5 from
  N=50-250) plus **MRR** and per-query latency. Deterministic, no judge. Seed for a
  future `benchmarks/tool-selection` dataset. A natural **A/B**: the dense sibling
  [LFM2.5-Embedding-350M](https://huggingface.co/LiquidAI/LFM2.5-Embedding-350M)
  (smaller index) vs this late-interaction model — does MaxSim's accuracy edge
  justify the multi-vector index cost for short tool descriptions?

The decision: **does it reliably surface the right tool(s) in the top-k so the
chat brain sees a short, relevant tool list?**

## 9. Why it matters for the north star

A local home agent will accrue **many tools/devices**; stuffing all of them into
the brain's context every turn is costly and error-prone (the agentic harness
already showed small models **over-actuate** when given broad tool access). A fast,
on-device late-interaction retriever that pre-selects the relevant few is the
**context-management layer** that makes a small local brain viable — and the
11-language coverage is a bonus for mixed-language households. It also doubles as
the RAG reranker for the memory ([embedding](../concepts/aide-models.md#3-embedding--text-to-dense-vector-bi-encoder-the-memory))
stage.

## Can it run here?

Yes, trivially — 353M encoder fits the [8 GB GPU](../hardware/proart-p16.md) with
room to spare, runs on CPU if needed; no KV-cache or thinking-budget concerns. Two
paths: a **PyLate venv** (Blackwell-compatible torch wheel, CUDA >= 12.8) for the
full retrieval/rerank API, or the **GGUF on llama.cpp** for the encode step.
Per-machine fit + the staged eval:
[lab/experiments/2026-06-20-lfm2.5-colbert-tool-selection](../../lab/experiments/2026-06-20-lfm2.5-colbert-tool-selection/README.md).

## See also
- [concepts/aide-models.md](../concepts/aide-models.md) — the aide-model track + eval contract.
- [benchmarks/home-automation](../../benchmarks/home-automation/README.md) — the toolset this would pre-filter for.
