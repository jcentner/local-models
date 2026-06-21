"""Rubric LLM-judge scorer for open-ended benchmarks (creative writing, agentic, reasoning).

The judge MUST be a frontier model - never a local small model. The default
backend is ``judge_copilot.CopilotCLIJudge`` (claude-opus-4.8 via the GitHub
Copilot CLI; see ``../judge_copilot.py`` and the copilot-cli skill). The judge
config (model + version + rubric) is part of the result and must be recorded -
LLM-judged scores are only comparable against the same judge config.

This module is backend-agnostic: it accepts any object exposing a
``complete(messages, system=...) -> Completion`` interface, so a different
frontier backend (or the hosting agent / a subagent) can be swapped in. It is
never wired to a local Ollama judge.
"""
from __future__ import annotations

import json
import re

_JSON = re.compile(r"\{.*\}", re.S)

JUDGE_SYSTEM = (
    "You are a strict, calibrated evaluator. Score the RESPONSE against the "
    "RUBRIC. Return ONLY a JSON object: {\"score\": <0-10 number>, "
    "\"per_criterion\": {<criterion>: <0-10>}, \"rationale\": <one sentence>}. "
    "Do not reward verbosity or sycophancy. Be specific."
)


def build_prompt(task: str, response: str, rubric: str) -> str:
    return (
        f"TASK GIVEN TO THE MODEL:\n{task}\n\n"
        f"RUBRIC (score each criterion 0-10):\n{rubric}\n\n"
        f"RESPONSE TO EVALUATE:\n{response}\n\n"
        "Return the JSON object now."
    )


def parse_judgement(text: str) -> dict:
    m = _JSON.search(text or "")
    if not m:
        return {"score": None, "rationale": "unparseable judge output", "raw": text}
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {"score": None, "rationale": "invalid JSON from judge", "raw": text}
    return obj


def score(task: str, response: str, rubric: str, judge_client, pass_threshold: float = 6.0) -> dict:
    """Judge one response. ``judge_client`` must expose ``complete(messages, system=)``."""
    prompt = build_prompt(task, response, rubric)
    out = judge_client.complete([{"role": "user", "content": prompt}], system=JUDGE_SYSTEM)
    judgement = parse_judgement(getattr(out, "text", str(out)))
    judgement["judge_wall_s"] = getattr(out, "wall_s", None)
    s = judgement.get("score")
    try:
        judgement["correct"] = (s is not None and float(s) >= pass_threshold)
    except (TypeError, ValueError):
        # a parseable-but-non-numeric score must FAIL closed, never abort the run
        judgement["correct"] = False
        judgement.setdefault("rationale", "non-numeric judge score")
    return judgement
