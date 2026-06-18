"""Rubric LLM-judge scorer for open-ended benchmarks (creative writing, agentic).

The judge is a pinned model (ideally stronger than the model under test, e.g.
opus-4.8 or gpt-5.5) served over an OpenAI-compatible or Ollama endpoint. The
judge config (model + version + rubric) is part of the result and must be
recorded - LLM-judged scores are only comparable against the same judge config.

This module is endpoint-agnostic: pass any object with a ``complete(messages,
system=...) -> Completion`` interface (e.g. ``client.ChatClient`` for a local
judge model). For judging via a frontier model you can point ChatClient at an
OpenAI-compatible base_url, or drive the judge from the /benchmark prompt using
the agent / a subagent instead of this code path.
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
    s = judgement.get("score")
    judgement["correct"] = (s is not None and float(s) >= pass_threshold)
    return judgement
