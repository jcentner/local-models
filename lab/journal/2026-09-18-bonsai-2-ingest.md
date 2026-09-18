# 2026-09-18 — Bonsai 2: the 27B that fits in 8 GB, on paper

PrismML released Ternary Bonsai 2 27B yesterday, two months after the first
Bonsai 27B. Jake asked for it to be onboarded from daedalus in a short session,
with the laptop needed for other things, so today is an ingest and a download
and nothing is run.

The first Bonsai never got its run here. The July experiment staged a ternary
against 1-bit comparison, and the ternary file was 7.17 GB against an 8 GB GPU
with a published 7.8 GiB peak at 4K. It was always going to be a fight with the
Windows desktop for the last few hundred megabytes, and other models kept going
first. Bonsai 2 changes that arithmetic. The new dense packing, `PTQ1_0`, stores
trits at 1.75 bits per weight, and the file is 5.95 GB, which is 5.54 GiB.
Add the demo's 1.2 GiB of overhead and 64 KiB of KV cache per token and a 4K
context lands near 7.0 GiB on a card with about 7.2 free. That is the first
27B-class model in this wiki that should sit fully on the laptop GPU.

The catch is printed in the vendor's own table. Unpacking dense trits costs
arithmetic, and on Blackwell cards `PTQ1_0` decodes about 7% slower than the
7.21 GB `PQ2_0` packing and processes prompts at about half the speed. The
packing that fits this machine is the slow one on this machine's architecture.
Whether that matters at laptop memory bandwidth is what Stage A measures.

The quality claim is the interesting part for the agent suite. The first Bonsai
lost most where this repo cares: instruction following at 91% of its baseline
and tool calling at 92.5%. Bonsai 2's card shows instruction following slightly
above the FP16 Qwen3.8 and BFCL v3 at 74.92 against 76.74. PrismML also dropped
the old "not for agentic coding" disclaimer. These are vendor numbers on one
tool-calling benchmark that this wiki already treats as reference only, and the
first Bonsai's launch scores met community reports of reasoning loops and
hallucination. The standing matrix is the test: home-automation v0.4 and
email-triage v0.3 at k=3, against gemma-4-12b's ceiling and qwen3.5:4b's
`pass^3`.

Two process notes. The announcement page and the model card print different
category tables, and a summarizing fetch of the card got the reasoning-effort
line wrong (it said medium was unsupported; the card says medium works and only
low is unsupported). The page was written from the card's raw text, downloaded
beside the weights. And the newest fork release, b10687, ships only Windows CUDA
runtime zips; the demo repo pinned b10685 this morning with the commit message
"Pin demo binaries to complete Prism b10685 release", so that is the binary to
use.

One open cost: the model thinks at `xhigh` effort by default at temperature 1.0.
A 27B thinking model on a laptop GPU may spend most of a home-agent turn
reasoning. The run records `--reasoning-budget` as a parameter, and a `medium`
effort row is a separate row if the default is too slow to be usable.
