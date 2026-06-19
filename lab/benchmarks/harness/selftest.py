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
    from harness import judge_copilot
    from harness import client as clientmod
    from harness.client import OpenAICompatibleClient, SamplingConfig
    from harness.scorers import llm_judge
else:
    from .scorers import code_exec, equivalence
    from . import run as runmod
    from . import judge_copilot
    from . import client as clientmod
    from .client import OpenAICompatibleClient, SamplingConfig
    from .scorers import llm_judge


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


def test_judge():
    print("copilot judge (mocked subprocess):")
    import subprocess
    from unittest import mock

    class _Proc:
        def __init__(self, stdout, stderr=""):
            self.stdout, self.stderr, self.returncode = stdout, stderr, 0

    # valid JSON judgement -> llm_judge parses + thresholds
    judge = judge_copilot.CopilotCLIJudge(model="claude-opus-4.8")
    with mock.patch.object(subprocess, "run", return_value=_Proc('{"score": 8, "rationale": "good"}')):
        res = llm_judge.score("task", "response", "rubric", judge, pass_threshold=6.0)
    check("judge JSON parsed + passes threshold", res.get("correct") is True and res.get("score") == 8)

    with mock.patch.object(subprocess, "run", return_value=_Proc('{"score": 3, "rationale": "weak"}')):
        res = llm_judge.score("task", "response", "rubric", judge, pass_threshold=6.0)
    check("judge below threshold fails", res.get("correct") is False)

    # empty stdout (or "Error: Model ...") must raise, not silently pass
    raised = False
    with mock.patch.object(subprocess, "run", return_value=_Proc("")):
        try:
            judge.complete([{"role": "user", "content": "hi"}])
        except RuntimeError:
            raised = True
    check("empty judge output raises", raised)

    raised = False
    with mock.patch.object(subprocess, "run", return_value=_Proc("Error: Model \"x\" not available.")):
        try:
            judge.complete([{"role": "user", "content": "hi"}])
        except RuntimeError:
            raised = True
    check("judge error string raises", raised)


def test_podman_sandbox():
    print("podman sandbox:")
    if not code_exec.podman_available():
        print("  SKIP  podman not available")
        return
    good = "```python\ndef add(a, b):\n    return a + b\n```"
    r = code_exec.score(good, "assert add(2, 3) == 5", mode="podman")
    check("podman: passing code", r.get("correct") and r.get("sandbox") == "podman")
    bad = "```python\ndef add(a, b):\n    return a - b\n```"
    check("podman: failing code rejected", not code_exec.score(bad, "assert add(2, 3) == 5", mode="podman")["correct"])
    net = "```python\nimport socket\nsocket.create_connection(('1.1.1.1', 80), timeout=3)\n```"
    check("podman: network blocked", not code_exec.score(net, "", mode="podman")["correct"])


def test_cost_computation():
    print("cost computation:")
    check("priced run computes USD",
          runmod.compute_cost(1_000_000, 2_000_000, 1.0, 3.0) == 7.0)
    check("local run is free", runmod.compute_cost(100, 200, 0.0, 0.0) == 0.0)


class _Resp:
    def __init__(self, payload):
        self._b = json.dumps(payload).encode("utf-8")
    def read(self):
        return self._b
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False


def test_openai_compatible_client():
    print("openai-compatible client (mocked):")
    from unittest import mock
    payload = {"choices": [{"message": {"content": "hello world"}}],
               "usage": {"prompt_tokens": 11, "completion_tokens": 5}}
    c = OpenAICompatibleClient(model="m", base_url="http://localhost:11434/v1",
                              sampling=SamplingConfig(seed=0))
    with mock.patch.object(clientmod.urllib.request, "urlopen", return_value=_Resp(payload)):
        comp = c.complete([{"role": "user", "content": "hi"}], system="sys")
    check("parses content", comp.text == "hello world")
    check("parses token usage", comp.prompt_tokens == 11 and comp.gen_tokens == 5)
    check("wall-based tok/s set", comp.gen_tok_per_s >= 0.0)
    # remote host + named-but-empty key must raise (secrets path)
    import os
    raised = False
    bad = OpenAICompatibleClient(model="m", base_url="https://api.example.com/v1",
                                api_key_env="DEFINITELY_UNSET_KEY_XYZ")
    os.environ.pop("DEFINITELY_UNSET_KEY_XYZ", None)
    try:
        bad._auth_header()
    except RuntimeError:
        raised = True
    check("remote host w/ empty key env raises", raised)


if __name__ == "__main__":
    test_equivalence()
    test_code_exec()
    test_loaders()
    test_validation()
    test_judge()
    test_podman_sandbox()
    test_cost_computation()
    test_openai_compatible_client()
    print(f"\n{'ALL PASS' if check.failed == 0 else str(check.failed) + ' FAILED'}")
    raise SystemExit(1 if check.failed else 0)
