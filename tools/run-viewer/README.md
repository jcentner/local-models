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

The left rail lists every row in `results.csv` (runs whose raw `.jsonl` is absent
on this machine are shown as `no raw` and disabled). Selecting a run renders one
card per item, adapted to the scorer:

| scoring | card content |
|---------|--------------|
| `code_tests` | completion (Python-highlighted), returncode, stderr, sandbox |
| `llm_judge` | score, per-criterion bars, rationale, completion (collapsible `<think>`) |
| `agentic` | transcript bubbles, tool-call rows, final-state diff, check flags |
| other | completion + raw `result` JSON (generic fallback) |

The **wiki** tab lists `wiki/**/*.md` grouped by folder and renders a page
read-only (YAML frontmatter stripped, `[[wikilinks]]` flattened).

## Endpoints

- `GET /api/runs` → `results.csv` rows (+ `raw_exists`).
- `GET /api/run?file=<name.jsonl>` → parsed items (bare filename within `runs/`).
- `GET /api/wiki` → list of markdown paths; `?path=<rel.md>` → raw markdown.

## Notes / limits

- Wiki markdown is rendered without an HTML sanitizer — acceptable here because it
  only reads this repo's own agent-authored `wiki/`. Don't point it at untrusted
  markdown.
- Run files live in the gitignored `runs/`; the viewer never writes anything.
