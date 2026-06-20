# 2026-06-20 — A local viewer for benchmark run content

## Why

`results.csv` tells me *that* `g4v2-A` scored 0.92 on home-automation. It can't
tell me *why* — whether the agent confirmed before unlocking the door, what the
judge's per-criterion breakdown was, where a code completion went wrong. All of
that lives in the gitignored `runs/*.jsonl`, which until today I read by hand with
`jq`. I wanted a convenient, readable, lightweight way to actually *look* at run
content — and, since I keep the wiki in Obsidian, a read-only window onto the wiki
markdown alongside it.

## Discovery first

Before writing any UI I did a deliberate pass on what's out there to help an agent
build frontends well. `last30days` was thin (mostly generic "MCP vs Agent Skills"
chatter; the one useful signal was that Obsidian-as-markdown + MCP is a recognized
pattern). The web search paid off:

- **[Impeccable](https://github.com/pbakaus/impeccable)** (`pbakaus/impeccable`,
  Apache-2.0) — the upgrade to Anthropic's `frontend-design` skill. 23 commands
  *plus* a no-LLM CLI detector (`npx impeccable detect`) that flags 44
  deterministic "AI-slop" tells. It's Copilot-native (`.github/skills/`) and works
  on this box.
- **[awesome-design-md](https://github.com/VoltAgent/awesome-design-md)** (MIT) —
  73 ready `DESIGN.md` token systems lifted from real sites (Google's Stitch
  `DESIGN.md` concept: a plain-text design system the agent reads).
- **Anthropic skills** — `frontend-design` (anti-slop direction),
  `web-artifacts-builder` (React/shadcn single-bundle — heavier than I wanted),
  `webapp-testing` (Playwright).

On the skills question I confirmed something worth remembering: VS Code Copilot
loads skills by **three-level progressive disclosure** — only the one-line
`description` sits in context for discovery; the body loads only on match. So
installing Impeccable globally costs ~nothing in context. I put it in
`~/.agents/skills/` skill-only (`--providers=codex --scope=global --no-hooks`); the
machine went from 4 to 5 global skills. No committed hooks anywhere.

## Decisions

- **Stack:** minimal **Python + Preact**. A stdlib `http.server` (the repo is
  Python-first already) + Preact/htm from a CDN — no build toolchain, no
  `pip install`. The server reads `results.csv` as the index and lazy-loads a
  `runs/*.jsonl` only when I click a run, so there's no data duplication and
  nothing new to keep in sync.
- **Aesthetic:** I mocked the same master/detail layout in three design languages
  (Ollama-terminal, Linear, Vercel/Geist) on real run data and screenshotted them
  to choose. **Vercel/Geist** won — pure black, Geist + Geist Mono, one mint/amber/
  red status accent. Most of the content is monospace data anyway, and the sharp
  B&W reads cleanest. Tokens distilled into `tools/run-viewer/DESIGN.md`.

## The build

The only real problem is that the runs aren't uniform — three scorer schemas need
three renderers:

- `code_tests` → highlighted completion + returncode + stderr + sandbox.
- `llm_judge` → score, per-criterion bars, rationale, collapsible `<think>`.
- `agentic` → transcript bubbles, tool-call rows, a **final-state diff** (changed
  devices in amber), and the correctness sub-flags (state/unchanged/confirm/…).

One schema gotcha cost a few minutes: the harness nests `initial_devices` *inside*
`final_state`, not at the episode top level, so my first diff came back empty.
Caught it visually, fixed the path, and the changed-device chip correctly computed
to amber (the screenshot's JPEG compression briefly fooled me into thinking it was
still mint — `getComputedStyle` settled it).

## Linting with Impeccable

`npx impeccable detect` flagged two `border-left: 2px` "side-tab" tells — on the
judge rationale and the wiki blockquote. The rule targets colored side-tabs on
*cards*; mine were quote elements, where a left rule is conventional. But the
honest call was that a filled callout (rationale) and a plain indent (blockquote)
are *more* Vercel anyway, so I changed them rather than suppressing the rule.
Detector now passes clean.

## Workflow note

Committed the viewer, then kicked off a read-only **gpt-5.5** review of the commit
in the background (the `copilot-cli-background-tasks` loop) while I wrote these
docs — cross-model critique of Opus's work, focused on path-traversal/XSS in the
server, schema correctness, and robustness. It came back high-signal (no Critical,
5 Major, 4 Minor) and I took most of it: CSP + a DOM sanitizer on the wiki render,
symlink-safe run-file access, a generalized agentic renderer that finally handles
the `support`/email-triage runs (`terminal_ok`/`expected_terminal`/`malformed_steps`),
an old→new device diff, tri-state correctness, and real fetch-error states. I pushed
back on full item pagination (runs are ≤12 items) and on vendoring the CDN libs
(disproportionate for a localhost tool — the strict CSP's `connect-src 'self'` already
blocks exfiltration), documenting both as deliberate.

## Open / next

- Code completions that are prose + a ```python fence get the prose keywords
  highlighted too — minor; could highlight only inside fences.
- Wiki markdown is sanitized (CSP + DOM denylist) but still reads only my own
  `wiki/`; I wouldn't point it at untrusted markdown.
- Possible later: a top-level results table / sort+filter, and folding this into
  the `/benchmark` flow as the "go look at what happened" step.
