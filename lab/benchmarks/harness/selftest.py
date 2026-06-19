"""Offline self-test for the harness scoring core (no model / network needed).

Run from ``lab/benchmarks/``:  ``python -m harness.selftest``
Exercises the equivalence and code-execution scorers and the run.py loaders with
a temporary dataset and a mock client, so the scoring logic can be verified
without Ollama running or any model pulled.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from harness.scorers import code_exec, equivalence
    from harness import run as runmod
else:
    from .scorers import code_exec, equivalence
    from . import run as runmod


def check(name: str, cond: bool):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        check.failed += 1
check.failed = 0


def test_equivalence():
    print("equivalence:")
    check("boxed answer", equivalence.score(r"so \boxed{42}.", "42")["correct"])
    check("answer-is phrasing", equivalence.score("The final answer is 3.14", "3.14")["correct"])
    check("last-number fallback", equivalence.score("computing... 17", "17")["correct"])
    check("comma normalization", equivalence.score(r"\boxed{1,000}", "1000")["correct"])
    check("wrong answer rejected", not equivalence.score(r"\boxed{41}", "42")["correct"])


def test_code_exec():
    print("code_exec:")
    good = "```python\ndef add(a, b):\n    return a + b\n```"
    tests = "assert add(2, 3) == 5"
    check("passing code", code_exec.score(good, tests)["correct"])
    bad = "```python\ndef add(a, b):\n    return a - b\n```"
    check("failing code rejected", not code_exec.score(bad, tests)["correct"])
    slow = "```python\nwhile True:\n    pass\n```"
    check("timeout handled", not code_exec.score(slow, "add(1,1)", timeout=2)["correct"])


def test_loaders():
    print("loaders + scoring wire-up:")
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "bench.json").write_text(json.dumps({"name": "t", "version": "0.0", "scoring": "equivalence"}))
        (d / "prompts.jsonl").write_text(json.dumps({"id": "q1", "prompt": "2+2?"}) + "\n")
        (d / "answer_key.jsonl").write_text(json.dumps({"id": "q1", "answer": "4"}) + "\n")
        m = runmod.load_benchmark(d)
        check("manifest loaded", m["name"] == "t" and len(m["_prompts"]) == 1)
        res = runmod.score_one("equivalence", m, m["_prompts"][0], r"\boxed{4}")
        check("score_one routes correctly", res["correct"])


def _manifest(scoring="equivalence", prompts=None, key=None, rubric=""):
    return {
        "name": "t", "version": "0.0", "scoring": scoring,
        "_prompts": prompts if prompts is not None else [{"id": "q1", "prompt": "p"}],
        "_key": key if key is not None else {"q1": {"answer": "4"}},
        "_rubric": rubric,
    }


def _rejects(manifest) -> bool:
    try:
        runmod.validate_benchmark(manifest)
        return False
    except SystemExit:
        return True


def test_validation():
    print("fail-closed validation:")
    check("valid passes", not _rejects(_manifest()))
    bad = _manifest(); bad.pop("scoring")
    check("missing scoring rejected", _rejects(bad))
    check("unknown method rejected", _rejects(_manifest(scoring="vibes")))
    check("empty prompts rejected", _rejects(_manifest(prompts=[])))
    check("blank id rejected", _rejects(_manifest(prompts=[{"id": "", "prompt": "p"}])))
    dupe = _manifest(prompts=[{"id": "q1", "prompt": "a"}, {"id": "q1", "prompt": "b"}],
                     key={"q1": {"answer": "4"}})
    check("duplicate ids rejected", _rejects(dupe))
    check("blank prompt text rejected", _rejects(_manifest(prompts=[{"id": "q1", "prompt": "  "}])))
    check("missing answer key rejected", _rejects(_manifest(key={})))
    check("empty answer rejected", _rejects(_manifest(key={"q1": {"answer": ""}})))
    check("orphan key rejected",
          _rejects(_manifest(key={"q1": {"answer": "4"}, "q2": {"answer": "5"}})))
    check("empty tests rejected",
          _rejects(_manifest(scoring="code_tests", key={"q1": {"tests": ""}})))
    check("code_tests with tests passes",
          not _rejects(_manifest(scoring="code_tests", key={"q1": {"tests": "assert True"}})))
    check("llm_judge needs rubric", _rejects(_manifest(scoring="llm_judge", key={})))
    check("llm_judge with rubric passes",
          not _rejects(_manifest(scoring="llm_judge", key={}, rubric="score it")))


if __name__ == "__main__":
    test_equivalence()
    test_code_exec()
    test_loaders()
    test_validation()
    print(f"\n{'ALL PASS' if check.failed == 0 else str(check.failed) + ' FAILED'}")
    raise SystemExit(1 if check.failed else 0)
