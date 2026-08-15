# 2026-08-14 — The archive run lands, and a 14MB model earns a second look

Tonight torrent did the job the daedalus session planned for it. The weight
archive — our hedge against upstream removal of Chinese-origin and
startup-risk models — went from a plan with an empty manifest to ~107G of
verified bits. Jake trimmed the priority list live ("I want bonsai, lfm trio,
and the qwen3.8-27B, nothing else for now"), and the reduced set is now cold
storage on NTFS: Qwen3.8-27B in both BF16 (18 shards, 52G) and FP8 (29G),
the Bonsai low-bit pair with their mmprojs and the pinned-binary demo repo,
and the LFM2.5 trio Q8_0s. Every LFS file checked against Hugging Face's
upstream sha256 digests — 95 files, zero mismatches. First reality check of
the plan: torrent has no D: drive. The archive lives at `C:\model-archive`,
same design intent (Backblaze sees NTFS files individually; the WSL vdisk is
one opaque blob).

Two lessons paid for cheaply. The `hf` CLI has a nasty quiet failure:
`hf download --include 'a' 'b' 'c'` binds only `'a'` to the flag, then
*ignores it* — a warning goes to stderr, the exit code stays 0, and `'b'`
onward are treated as explicit filenames. Net effect: every include-based
repo silently dropped its first pattern, which was always the main GGUF. The
sizes gave it away (a "done" LFM repo at 20K), a fix pass with positional
filenames recovered all five files, and the gotcha is documented in the
archive page. Second lesson: I edited the driver script while a bash process
was still executing it — bash reads scripts incrementally, so the running
interpreter resumed at a garbage byte offset and died mid-run. The
done-markers made the rerun free, but it's a good reminder that a running
script is not yours to touch.

The more interesting story is Needle 2. Jake pointed at Cactus Compute's
new release — a 45M-parameter tool-calling specialist in a 14MB binary,
~28MB RAM, grammar-constrained JSON output, a trained confidence head. The
community signal was brutal in an instructive way: the web demo turned
"do not lock the door" into `lock_door(front door)`, and off-topic garbage
("potato", "I'm hungover") into the same call. My first verdict was pass —
it structurally can't do the confirm flows and clarifying questions our
home-automation benchmark treats as required, and its whole value is a
hardware constraint we don't have. Jake reversed me with one fact from the
olympus fleet docs: **talos, the box the agent suite will actually live on,
is CPU-only with a 16GB cap**, Iris runs on a metered OpenAI key, and the
standing decision says going local-model means buying talos a GPU. Suddenly
a 14MB CPU model that handles the routine actuation slice is the cheapest
possible attack on that purchase.

The reframe also sharpened the experiment. Every one of those HN failures
carried `confidence: 0` — the gate may actually work — but Jake's skepticism
about self-reported confidence is exactly right for verbalized confidence,
and this is a trained scalar head, which is a measurable thing rather than a
trustable one. So the staged experiment makes calibration a first-class
result: a probe set full of negation, off-topic, and ambiguity traps; ECE
and a reliability curve on the stock model; a LoRA fine-tune on a
Luna-synthesized household dataset; the same probe after; then a deploy
check on talos itself. If the gate is trustworthy, a 14MB model routes the
boring 80% and escalates the rest. If it isn't, the whole pattern dies
regardless of accuracy — which is the honest way to find out.

Also decided tonight: the two 50-GiB Bonsai F16 masters stay deferred — the
point of Bonsai here was always the low-bit deployment quants, which are
archived — revisit if cheap storage shows up. And the LFM2.5 Q8_0 GGUFs
being local means the staged first-runs on torrent no longer wait on
downloads. That's probably the next session.
