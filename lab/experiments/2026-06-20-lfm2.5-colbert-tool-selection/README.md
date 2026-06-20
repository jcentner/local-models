# LFM2.5-ColBERT-350M — tool-selection retriever (first run)

- Date: 2026-06-20 (staged; not yet run)
- Hypothesis / question: Can LFM2.5-ColBERT-350M, used as an index-free reranker,
  reliably surface the **right home-automation tool(s) in the top-k** from a pool
  of N tool descriptions — i.e. is it a viable **context-management / tool-selection**
  layer for a small local home-agent brain? (Liquid ships an official
  [tool-selection demo](https://huggingface.co/spaces/LiquidAI/colbert-tool-selection)
  on this model — confirm it holds on *our* home-automation tools.)
- Class: reranker / late-interaction retriever (the [router aide](../../../wiki/concepts/aide-models.md)).
- Model page: [wiki/models/lfm2.5-colbert-350m.md](../../../wiki/models/lfm2.5-colbert-350m.md).
- Setup: ProArt P16 ([proart-p16](../../../wiki/hardware/proart-p16.md)), RTX 5070
  Laptop 8 GB (Blackwell sm_120). Runtime = **PyLate venv** (not Ollama; GGUF on
  llama.cpp is the alt encode path); 353M encoder, BF16 ~0.7 GB — fits the GPU
  trivially, CPU acceptable.
  Binding constraints are encode throughput + index size, both negligible at home
  scale. **Needs a CUDA >= 12.8 torch wheel** for Blackwell (this box has no system
  torch — venv required).

## Method

### 0. Environment (DONE 2026-06-20 — venv `~/.venvs/pylate` ready)
Already set up and verified (torch 2.11.0+cu128 + pylate 1.6.0, GPU op OK on
sm_120). To recreate from scratch:
```bash
python3 -m venv ~/.venvs/pylate && source ~/.venvs/pylate/bin/activate
# Blackwell sm_120: ensure a CUDA>=12.8 torch wheel
pip install --index-url https://download.pytorch.org/whl/cu128 torch
pip install -U pylate
python /home/jakce/utils/local-models/scripts/check-torch.py   # expect sm_120 + gpu matmul OK
```

### 1. Smoke / get-a-feel (Tier 1 — do this first; the near-term goal)
The cheapest signal, and the venv is ready. Index-free rerank a handful of queries
against a tiny tool pool (~10-20 home-automation tool descriptions) and eyeball
whether the right tool tops the list; note encode latency. Enough to "get a feel"
and decide whether the fuller Tier-2 eval below is warranted.
```python
from pylate import rank, models
model = models.ColBERT(model_name_or_path="LiquidAI/LFM2.5-ColBERT-350M", trust_remote_code=True)
q = model.encode(["turn off the kitchen lights"], is_query=True)
d = model.encode([["light.set_state(room, on|off)", "lock.set_state(door, locked|unlocked)",
                   "thermostat.set(temp)", "media.play(device)", "... ~10-20 tools"]], is_query=False)
print(rank.rerank(documents_ids=[[0, 1, 2, 3, 4]], queries_embeddings=q, documents_embeddings=d))
```

### 2. Standard sanity (Tier 2 — does it reproduce its published retrieval quality here?)
Run a NanoBEIR (or NanoBEIR-multilingual-extended) slice via PyLate and compare
NDCG@10 to the [model card](https://huggingface.co/LiquidAI/LFM2.5-ColBERT-350M)
numbers (NanoBEIR-multilingual-extended avg ~0.605). Confirms the install + GPU
path are correct before trusting use-case numbers.

### 3. Custom — tool-selection Recall@k (Tier 2 — the decision metric)
A small **authored** labeled set `{query -> relevant tool id(s)}` over a pool of N
home-automation tool descriptions (seed from the
[home-automation toolset](../../../benchmarks/home-automation/README.md):
get_status / set_device / ask / say, plus distractors to reach N=50-250).
Index-free rerank, then score:

- **Recall@k** — relevant tool in the top-k (primary; target k=5).
- **MRR** — rank of the first relevant tool.
- **per-query latency** + index-build time (cost axis).

```python
from pylate import rank, models
model = models.ColBERT(model_name_or_path="LiquidAI/LFM2.5-ColBERT-350M", trust_remote_code=True)
# encode query (is_query=True) + tool descriptions (is_query=False),
# rank.rerank(...), check whether the labeled tool id(s) land in top-k.
```

Sweep N (small vs large tool pool) and k to find where Recall@k degrades — that
bounds how many tools the brain can be shielded from.

## Result
<blank — not yet run>

Fields to record (per-environment): model, format (F32/BF16), runtime + PyLate +
torch versions, machine, N (pool size), k, Recall@k, MRR, encode tok/s, index
size, per-query latency.

## Learnings
<blank — what to believe; whether to promote the tool-selection set into a real
`benchmarks/tool-selection` dataset + a hand-rolled scorer; and the A/B vs the dense
sibling LFM2.5-Embedding-350M (smaller single-vector index) to decide whether
MaxSim's accuracy edge justifies the multi-vector index cost for short tool descriptions>
