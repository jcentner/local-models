# local-models — Claude Code entry point

@AGENTS.md

The schema above is agent-agnostic. Claude-specific notes: worker/review dispatch
mechanics live in the global `dispatch` skill, with `codex-worker` and
`claude-worker` for the harnesses; the repo-local `.github/skills/` (benchmark
harness, copilot-cli judge, wrap-external-benchmark) apply to any agent working here.

Commit and push as you go — this repo syncs two machines, and uncommitted work
strands on one of them (the 2026-07-17 Bonsai ingest sat unpushed for a month and
caused a cross-machine conflict).
