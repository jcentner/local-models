---
title: Weight archive
tags: [archive, infra, planning]
updated: 2026-08-14
---

# Weight archive

Local archive of model weights we fear may become unavailable upstream —
primarily Chinese-origin models (anticipating possible US access restrictions)
plus startup-risk artifacts (PrismML). Decided 2026-08-14 (daedalus session).

## Threat model → design

The threat is **upstream removal, not disk failure**. Consequences:

1. **Speed first** — get bits onto any local disk before a block lands;
   redundancy second.
2. **Archive originals (safetensors), not just GGUFs** — quants can be
   regenerated from originals; the reverse is impossible, and originals stay
   compatible with future runtimes/quant formats.
3. **Two copies** — if upstream is gone forever, one disk holding the only
   copy is the single point of failure.

## Layout (decided)

- **Canonical archive: torrent's 2TB, on NTFS** (e.g. `D:\model-archive\<org>\<repo>\`,
  visible from WSL at `/mnt/d/model-archive/`). NOT inside the WSL vdisk:
  Backblaze sees NTFS files individually; the vdisk is one opaque `.vhdx` blob
  (churn re-uploads, restore all-or-nothing). Copy a GGUF into ext4 when
  actually serving; NTFS read speed is fine for cold storage.
- **Mirror: Backblaze** (torrent is backed up). Verified sufficient with
  caveats: `.gguf`/`.safetensors` are not on the default exclusion list (VM
  images/installers are — one-time check that no size cap is set); default
  **30-day version history means local deletion propagates** — Backblaze
  mirrors the disk, it does not independently archive (Extended Version
  History ~$2/mo closes this if wanted); if the 2TB is external it must stay
  connected (30-day disconnect rule). Correlated-risk caveat: in the
  regulatory scenario a US cloud provider is the copy that complies — the
  local disk is the resilient one.
- **daedalus**: working copies only (Ollama tags + HF cache), no full mirror.
- **Manifest: this page** — record source URL, sha256, license snapshot,
  download date per artifact as downloads land. The manifest is what verifies
  a Backblaze restore round-tripped.

## Download list (priority order, verified live + ungated 2026-08-14)

| # | Artifact | Repo / files | Size | Why |
|---|---|---|---|---|
| 1 | Qwen3.8-27B | `Qwen/Qwen3.8-27B` (BF16, 18 shards) + `Qwen/Qwen3.8-27B-FP8` | 51.8 + 28.8 GiB | Landed on HF 2026-08-14; successor to Qwen3.6-27B; archive before any restriction, while community quants are scarce |
| 2 | Qwen3.5-4B + 9B originals | `Qwen/Qwen3.5-4B`, `Qwen/Qwen3.5-9B` safetensors | ~26 GB est. | **Standing baseline champ (qwen3.5:4b) exists locally only as Ollama quants** — no originals held |
| 3 | Bonsai 27B set | `prism-ml/Bonsai-27B-gguf`: `Q1_0` (3.54) + mmproj-Q8_0 (0.59); `prism-ml/Ternary-Bonsai-27B-gguf`: `Q2_0` (6.67) + `Q2_g64` (7.06) + mmproj-Q8_0 (0.59); clone `PrismML-Eng/Bonsai-demo` (pinned CUDA binary — ternary g128 needs their fork) | ~18 GiB | Startup risk + Qwen3.6-derived; weights without the demo repo are half an artifact |
| 3b | Bonsai F16 masters (**OPEN — Jake to decide**) | `Bonsai-27B-F16.gguf` + `Ternary-Bonsai-27B-F16.gguf` | 2× 50.1 GiB | The QAT-trained weights — unique artifacts nobody can regenerate from Qwen3.6 |
| 4 | VibeThinker-3B originals | `WeiboAI/VibeThinker-3B` | ~6.6 GB | Chinese-origin (WeiboAI); only the Q8 GGUF held |
| 5 | MiniCPM5-1B | `openbmb/MiniCPM5-1B` (+ GGUF repo) | ~2.5 GB | Chinese-origin (OpenBMB); daedalus HF cache partial |
| 6 | LFM2.5 trio | `LiquidAI/LFM2.5-2.6B-GGUF` Q8_0 (2.68) + `LFM2.5-VL-3B-GGUF` Q8_0 + mmproj-Q8_0 (3.22) + `LFM2.5-ColBERT-350M-GGUF` Q8_0 (0.35) | ~6.5 GiB | Low risk (custom LFM Open License could re-gate); trivially cheap; unblocks the staged torrent first-runs |
| 7 | gemma-4 agentic finetune | `yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF` Q3_K_M + Q4_K_M | 13 GB | Community-finetune deletion risk; already in daedalus HF cache — copy into archive for the Backblaze mirror |

Total ~135 GB (~235 GB with the F16 masters). Out of reach: `Qwen/Qwen3.8-2.4T-A95B`
(~2.4 TB even at FP8 — exceeds the drive; open-weighted 2026-08-12, not archivable here).

## Fetch pattern (on torrent)

```bash
pip install -U huggingface_hub  # one-time; then per repo:
hf download Qwen/Qwen3.8-27B --local-dir /mnt/d/model-archive/Qwen/Qwen3.8-27B
# after each: sha256sum > SHA256SUMS in the repo dir; add a manifest row here
```

## Manifest

| Date | Artifact | Location | sha256 | License |
|---|---|---|---|---|
| *(fill as downloads land)* | | | | |
