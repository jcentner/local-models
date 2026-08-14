# LFM2.5-VL-3B — first look (vision smoke test; no harness support yet)

- Date: 2026-08-13 (staged; not yet run)
- Hypothesis / question: Is a 3B-class on-device VLM already good enough for the
  home-agent **eyes** jobs — concretely, HomeView-style fixture identification
  from real house photos (image → constrained proposal), plus screen/OCR
  reading? The benchmark harness has **no image support**, so this is a manual
  smoke test to decide whether building the vision-benchmark track (see
  [backlog](../../../wiki/backlog.md)) is worth it.
- Model page: [wiki/models/lfm2.5-vl-3b.md](../../../wiki/models/lfm2.5-vl-3b.md).
- Setup: torrent ([hardware page](../../../wiki/hardware/torrent.md)), RTX 3070 Ti
  8 GB — ~3.3 GB footprint fits full-GPU. Serving: llama.cpp CUDA container with
  multimodal (mtmd) + the GGUF **mmproj** file (Ollama support unverified), or a
  transformers venv (`AutoModelForImageTextToText`, torch cu12x standard wheel —
  Ampere sm_86 has no Blackwell wheel constraint).

## Method

### 1. Bring-up + generic smoke
llama.cpp container, model + mmproj, `--temp 0.2 --top-k 50 --repeat-penalty 1.0`;
`/image <path>` on a few casual photos. Record load VRAM, tok/s, TTFT.

### 2. HomeView-shaped probe (the decision test)
Take ~5 photos of real house fixtures (or reuse homeview's
`docs/reference/vision-eval/` ground-truth photos + its 37-key fixture
vocabulary). Prompt: identify the fixture from a fixed vocabulary list + one
evidence phrase — the shape of homeview's `propose_assets` tool. Eyeball against
ground truth; note especially label-reading (the eval's hard item is a radon
pipe identified only by a handwritten label — frontier-discriminating).

### 3. Screen/OCR probe
One phone screenshot ("what would you tap to X?") + one document photo (extract
fields). ScreenSpot-v2 80.7 / ChartQA 81.3 are the claims under test.

## Result
<blank — not yet run>

## Learnings
<blank — feeds three decisions: (1) build the vision-benchmark track (likely by
wrapping homeview's vision-eval: 18 ground-truth photos, deterministic regex
scoring, measured Claude/OpenAI comparison rows — an external-first wrap, not a
fresh authoring job); (2) nominate it for homeview's "local vision provider
behind VisionProvider" backlog item; (3) whether image-triggered tool calling
is reliable enough to matter for the agentic suite>
