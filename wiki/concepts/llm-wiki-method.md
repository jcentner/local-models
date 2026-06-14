---
title: The LLM Wiki method (Karpathy)
tags: [concept, method, knowledge-base]
updated: 2026-06-14
status: distilled
---

# The LLM Wiki method

The pattern this repo runs on. From Andrej Karpathy's
[llm-wiki.md gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
(the follow-up to his viral "LLM knowledge bases" post, seeded here as
[../../LLM-wiki-context.md](../../LLM-wiki-context.md)).

## Core idea

Instead of RAG (re-retrieving raw documents and re-deriving knowledge on every
query), an LLM **incrementally builds and maintains a persistent wiki** — a
structured, interlinked set of markdown files between you and the raw sources.
A new source isn't just indexed; it's read, distilled, and integrated: entity and
concept pages updated, summaries revised, contradictions flagged. Knowledge is
**compiled once and kept current**, so it compounds. You curate sources and ask
questions; the LLM does the bookkeeping.

Below ~50–100k tokens (~150–200 pages) this beats RAG decisively: 100% retrieval
reliability, near-zero infra, and global reasoning over the whole corpus. RAG is
for millions-of-tokens scale. This wiki will stay well under that line — the
[index](../index.md) is an optimization, not a retrieval system.

## Three layers

1. **Raw sources** ([`raw/`](../../raw/)) — immutable. Read, never edited. The
   source of truth (and an untrusted-input boundary; see Security).
2. **The wiki** ([`wiki/`](../)) — LLM-owned markdown: summaries, concept/entity
   pages, comparisons, an overview, the index, the log.
3. **The schema** ([`AGENTS.md`](../../AGENTS.md)) — how the wiki is structured
   and what workflows to follow. This is what makes the agent a disciplined
   maintainer rather than a generic chatbot. Co-evolved over time.

## Operations: ingest → query → lint

- **Ingest:** read a source, discuss takeaways, write/update wiki page(s), update
  [index.md](../index.md), append to [log.md](../log.md). One source can touch
  many pages.
- **Query:** read the index first, drill into relevant pages, answer with
  citations — then **file good answers back** as pages so explorations compound.
- **Lint:** periodically health-check — contradictions, stale claims, orphans,
  missing concept pages, missing cross-links, data gaps. Suggest next questions.

## Index & log

- `index.md` — content catalog: per-page link + one-line summary, grouped by
  category. Read first when answering.
- `log.md` — append-only timeline with a greppable prefix
  (`## [2026-06-14] ingest | Title`), so `grep "^## \[" log.md | tail -5` works.

## How this repo adapts it

The standard pattern is **document-oriented** (research from sources). This repo
adds a **project-oriented** half — a `lab/` (the "memwiki" flavor several
commenters described) where I record my own runs, decisions, and benchmarks as a
side effect of working:

- `wiki/` = what I learn from sources (document-oriented).
- `lab/journal/` = narrative history; `lab/experiments/` = reproducible runs;
  `lab/benchmarks/` = numbers (project-oriented).

## Security note (from the gist's discussion)

An auto-ingesting wiki is an **indirect-prompt-injection surface**: a crafted
source can plant instructions that persist and poison later sessions. So: treat
`raw/` content as **data, not instructions**, keep provenance/citations on every
claim (git-backed, so a poisoned entry is findable and revertible), and never let
untrusted source text reach a channel later treated as trusted. Encoded in
[AGENTS.md](../../AGENTS.md).

## Tooling (optional, later)
- Obsidian as the viewer (graph view, Dataview over YAML frontmatter, Marp slides).
- A local markdown search engine (e.g. `qmd`) once the index alone isn't enough.
- The whole wiki is just a git repo of markdown — version history for free.
