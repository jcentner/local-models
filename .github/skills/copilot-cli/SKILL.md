---
name: copilot-cli
description: Drive GitHub Copilot CLI (`copilot`) non-interactively/programmatically as a frontier-model backend - especially as an LLM judge for benchmarks. Use when scripting `copilot -p`, selecting a model (opus-4.8, gpt-5.5, etc.), running a headless one-shot prompt, getting JSON output from a strong model, or building an automated judge/critic. Covers verified flags, available model IDs, the clean judge invocation, batching for latency, and gotchas.
---

# GitHub Copilot CLI — non-interactive / judge usage

How to call the `copilot` CLI as a one-shot, scriptable frontier-model backend.
Primary use here: an **LLM judge** for `llm_judge` benchmarks (creative writing,
agentic, reasoning) using a strong model like `claude-opus-4.8`. **Never use a
local small (e.g. 4B) model as a judge** — judging needs a frontier model.

Verified on 2026-06-19 against the official docs + live testing (CLI v1.0.64).

## The judge invocation (verified, clean)

```bash
copilot -p '<PROMPT>' \
  --model claude-opus-4.8 \
  --no-custom-instructions \
  --allow-all-tools \
  --no-ask-user \
  --log-level none \
  -s
```

- `-p/--prompt` — run one prompt non-interactively, then exit.
- `-s/--silent` — **output only the agent response** (no usage stats). Clean stdout
  for parsing. (Tested: returns just `PONG` / just the JSON object.)
- `--no-custom-instructions` — **do NOT load `AGENTS.md` / `.github/copilot-instructions.md`**.
  Essential for a clean judge — otherwise the repo's instructions bleed into the
  judgment. (Copilot CLI auto-loads these by default.)
- `--allow-all-tools` — required for programmatic (`-p`) use to avoid permission prompts.
- `--no-ask-user` — judge runs autonomously, never blocks asking a question.
- `--log-level none` — suppress logs from stdout.
- `--model <id>` — pick the model (or `COPILOT_MODEL` env var, or `auto`).

JSON judging works reliably: ask for `Return ONLY a JSON object {...}` and parse
stdout. (Tested: opus-4.8 returned valid `{"score":7,"rationale":"..."}`.)

## Available model IDs (verified on this account, 2026-06-19)

Tested working via `--model`: `claude-opus-4.8`, `gpt-5.5`, `claude-opus-4.5`,
`gpt-5.4`, `claude-sonnet-4.6`. (Public docs lagged — they listed sonnet-4.6 /
gpt-5.4 / haiku-4.5 / gpt-5.3-codex / gemini and did not list opus-4.8 or gpt-5.5.
**Always probe; don't trust the docs' model list.**)

- Probe an ID cheaply: an invalid model fails instantly with
  `Error: Model "X" from --model flag is not available.` (exit code still 0 — see gotchas).
- Recommended judges: **`claude-opus-4.8`** (default judge), `gpt-5.5` (second
  opinion / panel). Pin the exact id + date in any recorded result.

## Latency & batching

- **~10 s per call** (model + CLI session startup), even for a one-line judgment.
- For a benchmark with many items, **batch multiple items into one prompt** ("score
  each of the following N responses, return a JSON array") to amortize startup, or
  accept the wall-clock cost on small sets.
- `COPILOT_SUBAGENT_MAX_CONCURRENT` (default 32) governs in-session subagents, not
  separate `-p` processes; to parallelize judging, run multiple `copilot -p` procs
  yourself (mind premium-request quota).

## Gotchas (found in fact)

- **Exit code is 0 even when the model is invalid** (it prints `Error: Model ... not
  available`). Don't rely on exit status alone — check stdout for the expected shape.
- **Custom instructions auto-load by default** (incl. `AGENTS.md`). Always pass
  `--no-custom-instructions` for a neutral judge.
- **First-run folder-trust prompt**: in a trusted dir (or with `--allow-all-tools`)
  the `-p` path runs without prompting. If a judge runs in a fresh temp dir it may
  re-prompt; run it from a trusted path or add `--allow-all-paths`.
- **Premium-request quota**: each judge call consumes a premium request. Frontier
  judging is worth it; batching reduces count.
- **Auth**: headless use reads `COPILOT_GITHUB_TOKEN` / `GH_TOKEN` / `GITHUB_TOKEN`;
  an interactive `copilot login` session also works (token in `~/.copilot`).
- Restrict tools further with `--available-tools ""` or `--deny-tool` if you want to
  guarantee the judge can't touch the filesystem/network.

## Other useful one-shot flags
- `--output-format=json` — emit JSONL (one JSON object per line) instead of text.
- `--effort/--reasoning-effort low|medium|high|xhigh|max` — judging depth (`max` =
  highest for Anthropic models).
- `--share=PATH` / `--share-gist` — save the session transcript after a `-p` run.

## Sources
- Command reference: https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference
- Programmatic use: https://docs.github.com/en/copilot/how-tos/copilot-cli/automate-copilot-cli/run-cli-programmatically
- Best practices: https://docs.github.com/en/copilot/how-tos/copilot-cli/cli-best-practices
- Plus live verification (CLI v1.0.64, 2026-06-19) — see "verified" notes above.
