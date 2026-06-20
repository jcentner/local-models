"""Scorer for the `agentic` rollout method (lightweight tau-bench-style).

Scores a finished episode (from ``harness.agentic.run_episode``) against the
scenario's answer key - deterministic state/policy checks, no LLM judge:

- **terminal action**: did the agent end the right way (reply vs escalate)?
- **required tools**: were the must-call tools used (e.g. search_kb before answering)?
- **forbidden tools**: were the must-not-call tools avoided (e.g. don't over-escalate)?

Answer-key row shape (in ``answer_key.jsonl``):
    {"id": "e1", "expected_terminal": "reply"|"escalate",
     "required_tools": ["search_kb"], "forbidden_tools": ["escalate"]}
"""
from __future__ import annotations


def score(episode: dict, key: dict) -> dict:
    expected = key.get("expected_terminal")
    did_escalate = episode.get("did_escalate", False)
    did_reply = episode.get("did_reply", False)

    if expected == "escalate":
        terminal_ok = bool(did_escalate)
    elif expected == "reply":
        terminal_ok = bool(did_reply and not did_escalate)
    else:
        terminal_ok = False

    used = set(episode.get("tools_used", []))
    required = set(key.get("required_tools", []))
    forbidden = set(key.get("forbidden_tools", []))
    required_ok = required.issubset(used)
    forbidden_ok = used.isdisjoint(forbidden)

    malformed = sum(1 for tc in episode.get("tool_calls", []) if tc.get("name") == "_malformed")
    correct = bool(terminal_ok and required_ok and forbidden_ok)

    return {
        "correct": correct,
        "terminal_ok": terminal_ok,
        "required_ok": required_ok,
        "forbidden_ok": forbidden_ok,
        "expected_terminal": expected,
        "resolution": episode.get("resolution"),
        "tools_used": sorted(used),
        "malformed_steps": malformed,
    }
