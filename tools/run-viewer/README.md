# run-viewer

A local, minimal web app to review benchmark **run content** from
[`lab/benchmarks`](../../lab/benchmarks/). Reads the committed index
(`results.csv`), lazy-loads the gitignored raw runs (`runs/*.jsonl`) on click, and
serves the [`wiki/`](../../wiki/) markdown read-only.

- **Stack:** stdlib Python server + Preact/htm via CDN (no build step, no `pip install`).
- **Aesthetic:** Vercel / Geist — see [DESIGN.md](DESIGN.md).
- **Scope:** read-only viewer. Only `GET`; file access confined to `results.csv`,
  `runs/`, and `wiki/`.

## Run

```bash
cd tools/run-viewer
python3 server.py            # → http://127.0.0.1:8777
# options: --port 8777 --host 127.0.0.1
```

Open the printed URL. The front-end fetches Preact/htm/marked from a CDN, so the
first load needs internet; runs and wiki data are served locally.

## What it shows

Opening **Runs** lands on a **cross-model leaderboard**: every `base_model` ranked
by mean **pass^k** (reliability — items correct on *all* k samples) across the
benchmarks it ran, as a model × benchmark matrix. Each cell shows the best
`pass^k` with the best-of-k `pass@k` capability as a muted `@` secondary when they
differ (at k=1 they're equal). Benchmark columns are version-aware (`v0.1` and
`v0.2` are separate). Click a model name to compare its variants; click a cell to
open that benchmark's best run (greyed = its raw `.jsonl` is absent here). The
rail's `▣ leaderboard` button returns here anytime.

The left rail groups every row in `results.csv` by **base model → variant → run**
(`base_model` is the harness-recorded canonical id; the `model` column is the
config/quant variant label) and has a **filter box** (token match, so "gemma 4"
finds `gemma-4-12b-…`). Runs whose raw `.jsonl` is absent on this machine
show `no raw` and are disabled. Clicking a **base-model header** opens a comparison
matrix (variants × benchmarks, best pass^k per cell) — handy for quant/serving
sweeps. Clicking a **run** renders one card per item, adapted to the scorer:

| scoring | card content |
|---------|--------------|
| `code_tests` | completion (Python-highlighted), returncode, stderr, sandbox |
| `llm_judge` | score, per-criterion bars, rationale, completion (collapsible `<think>`) |
| `agentic` | transcript bubbles, tool-call rows, final-state diff, check flags |
| other | completion + raw `result` JSON (generic fallback) |

A run's detail header shows the variant label, its **base model**, and a
`model page ↗` link to `wiki/models/<base_model>.md` when that page exists
(`base_model` doubles as the wiki slug, so no separate mapping is needed). For
multi-pass runs (**k>1**) the header also surfaces **pass^k** (reliability),
**flaky** (items inconsistent across samples), and **±sem** alongside `pass@k`;
each item is grouped into one card showing its `n/k` pass count and per-sample
dots, a representative sample (a failing one if any) expanded, and the rest
collapsed. Its **controls** row adds a `failures N` toggle (items with any failed
sample) and a `compare vs…` dropdown (any other run of the same benchmark).
**Compare** lines the two runs up **item-by-item** by id, side by side with each
item's `n/k`; rows where their pass rate differs are flagged `differs`, and a
`differences N` toggle hides the rest.

When a run's per-item records carry a `meta` object (e.g. `tier`/`category`), a
`slice by…` dropdown appears: it shows a per-group reliability breakdown
(`n · pass^k · pass@k · flaky`) and clicking a group filters the items to it.
Sliceable keys are auto-discovered (small categorical fields; unique-per-item
keys like `persona` are excluded). This is inert until the harness emits `meta`
on the sample lines.

The **wiki** tab lists `wiki/**/*.md` grouped by collapsible folders and renders a
page read-only (YAML frontmatter stripped, `[[wikilinks]]` flattened), with a
**full-text search** box (ranked pages + line-numbered snippets; click to open).
Links between
wiki pages navigate **in-app**; external and repo-relative (`../`) links open in a
new tab. It is deliberately a minimal reader, **not** Obsidian — no graph,
backlinks, dataview, or embeds. Use Obsidian for real wiki navigation.

## Endpoints

- `GET /api/runs` → `results.csv` rows (+ `raw_exists`).
- `GET /api/run?file=<name.jsonl>` → parsed items (bare filename within `runs/`).
- `GET /api/wiki` → list of markdown paths; `?path=<rel.md>` → raw markdown.
- `GET /api/wiki/search?q=<text>` → per-file substring hits (path, count, line snippets).

## Notes / limits

- The front-end loads Preact/htm/marked from a CDN (esm.sh) + fonts from Google.
  A strict CSP (`script-src 'self' esm.sh`, `connect-src 'self'`) limits a
  compromised dependency to local-only access; fully removing CDN trust (vendoring
  + SRI) is deferred. First load needs internet; run/wiki data is served locally.
- Wiki markdown is sanitized (CSP + a DOM denylist pass that strips scripts, `on*`
  handlers, and `javascript:` URLs). It still only reads this repo's own `wiki/` —
  don't point it at untrusted markdown.
- Run-file access is basename- and symlink-guarded to `runs/`; the viewer is
  read-only (`GET` only) and never writes anything.
