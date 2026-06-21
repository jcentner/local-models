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
    from harness import agentic as ag
    from harness.client import OpenAICompatibleClient, SamplingConfig, Completion, ToolCall
    from harness.scorers import llm_judge
    from harness.scorers import agentic as agentic_scorer
else:
    from .scorers import code_exec, equivalence
    from . import run as runmod
    from . import judge_copilot
    from . import client as clientmod
    from . import agentic as ag
    from .client import OpenAICompatibleClient, SamplingConfig, Completion, ToolCall
    from .scorers import llm_judge
    from .scorers import agentic as agentic_scorer


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


def test_meta_slice():
    print("viewer meta-slice (A0 whitelist):")
    fields = runmod.slice_fields({})
    check("default whitelist is tier+category", set(fields) == {"tier", "category"})
    item = {"id": "d1", "meta": {"tier": "T2", "category": "risk", "persona": "secret",
                                 "devices": {"x": {"state": "off"}}, "tags": ["a", "b"]}}
    ms = runmod.meta_slice(item, fields)
    check("keeps whitelisted scalars", ms == {"tier": "T2", "category": "risk"})
    check("drops persona (not whitelisted)", "persona" not in ms)
    check("drops object/array values", "devices" not in ms and "tags" not in ms)
    check("no meta -> empty dict", runmod.meta_slice({"id": "x"}, fields) == {})
    # numeric scalar kept; bench.json may NARROW (never widen) the whitelist
    numeric = {"id": "d2", "meta": {"tier": 3, "category": "x"}}
    check("numeric scalar kept", runmod.meta_slice(numeric, fields)["tier"] == 3)
    narrowed = runmod.slice_fields({"slice_fields": ["category", "persona"]})
    check("override narrows + drops non-whitelist", set(narrowed) == {"category"})


def test_reliability_metrics():
    print("reliability metrics (pass^k / flaky / sem):")
    rm = runmod.reliability_metrics
    # all items pass every sample -> perfect reliability, no flaky
    m = rm([3, 3, 3], 3)
    check("all-pass: observed=1", m["observed_pass_at_k"] == 1.0)
    check("all-pass: pass^k=1", m["pass_hat_k"] == 1.0)
    check("all-pass: 0 flaky", m["flaky_items"] == 0)
    # a flaky item (2/3) drags pass^k below observed and is counted flaky
    m = rm([3, 2, 0], 3)
    check("mixed: observed counts >=1 correct (2/3)", m["observed_pass_at_k"] == round(2 / 3, 4))
    check("mixed: pass^k counts all-k only (1/3)", m["pass_hat_k"] == round(1 / 3, 4))
    check("mixed: flaky = the 2/3 item", m["flaky_items"] == 1)
    check("mixed: avg_correct", m["avg_correct"] == round((1 + 2 / 3 + 0) / 3, 4))
    # best-of-k HIDES flakiness: observed >= pass^k always
    mm = rm([2, 1, 3], 3)
    check("observed >= pass^k", mm["observed_pass_at_k"] >= mm["pass_hat_k"])
    # k=1 -> pass^k == observed (the back-fill identity)
    m1 = rm([1, 0, 1], 1)
    check("k=1: pass^k == observed", m1["pass_hat_k"] == m1["observed_pass_at_k"] == round(2 / 3, 4))
    check("k=1: never flaky", m1["flaky_items"] == 0)
    # sem: blank for <2 items, numeric for >=2, 0 when identical
    check("sem blank for single item", rm([3], 3)["sem"] == "")
    check("sem numeric for >=2 items", isinstance(rm([3, 0], 3)["sem"], float))
    check("sem=0 when all items identical", rm([3, 3, 3], 3)["sem"] == 0.0)
    # guards
    check("empty -> zeros", rm([], 3)["pass_hat_k"] == 0.0)
    check("k<=0 -> zeros", rm([1, 2], 0)["pass_hat_k"] == 0.0)


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


class _MockAgent:
    def __init__(self, actions):
        self.actions, self.i = list(actions), 0
    def complete(self, messages, system=None, tools=None):
        a = self.actions[min(self.i, len(self.actions) - 1)]
        self.i += 1
        return Completion(text=a, prompt_tokens=5, gen_tokens=7, wall_s=0.01)


class _MockToolAgent:
    """Native-protocol mock: yields scripted ToolCall lists (no network)."""
    def __init__(self, scripts):
        self.scripts, self.i = list(scripts), 0
    def complete(self, messages, system=None, tools=None):
        calls = self.scripts[min(self.i, len(self.scripts) - 1)]
        self.i += 1
        return Completion(text="", tool_calls=list(calls), prompt_tokens=5, gen_tokens=7,
                          wall_s=0.01, raw_message={"role": "assistant", "content": ""})
    def tool_result_message(self, call, content):
        return {"role": "tool", "content": content, "tool_name": call.name}


class _MockUser:
    def __init__(self, msg="DONE"):
        self.msg = msg
    def reply(self, transcript):
        return self.msg


class _MockJudge:
    """Frontier-judge stand-in: returns a fixed JSON judgement (no network)."""
    def __init__(self, text):
        self.text = text
    def complete(self, messages, system=None):
        return Completion(text=self.text)


class _ScriptUser:
    """User-sim that returns scripted replies in order (last one repeats)."""
    def __init__(self, msgs):
        self.msgs, self.i = list(msgs), 0
    def reply(self, transcript):
        m = self.msgs[min(self.i, len(self.msgs) - 1)]
        self.i += 1
        return m


def test_agentic():
    print("agentic rollout (mocked agent + user):")
    check("parse clean json", ag.parse_action('{"tool":"reply","args":{"text":"hi"}}')["tool"] == "reply")
    check("parse with think preamble",
          ag.parse_action('<think>hmm</think>\n{"tool":"search_kb","args":{"query":"hours"}}')["tool"] == "search_kb")
    check("parse prose-wrapped",
          ag.parse_action('I will search. {"tool":"search_kb","args":{"query":"x"}} ok')["tool"] == "search_kb")
    check("parse malformed -> None", ag.parse_action("no json here") is None)
    check("parse defaults args", ag.parse_action('{"tool":"escalate"}')["args"] == {})

    # XML-in-content tool-call fallback (MiniCPM5 over a parser-less SGLang)
    _xml = ('<function name="search_kb"><param name="query">support hours</param></function>\n'
            '<function name="search_kb"><param name="query">refund policy</param></function>')
    _calls, _clean = clientmod.parse_xml_tool_calls("I will look it up. " + _xml)
    check("xml fallback: 2 calls", len(_calls) == 2)
    check("xml fallback: name+args", _calls[0].name == "search_kb" and _calls[0].arguments == {"query": "support hours"})
    check("xml fallback: text cleaned", "<function" not in _clean and "look it up" in _clean)
    check("xml fallback: non-xml untouched", clientmod.parse_xml_tool_calls("just text")[0] == [])

    scen_reply = {"id": "t1", "prompt": "what are your hours?",
                  "meta": {"persona": "goal", "policy": "answer from kb",
                           "kb": [{"q": "hours", "keywords": "hours when", "a": "9-5 ET"}]}}
    ep = ag.run_episode(
        _MockAgent(['{"tool":"search_kb","args":{"query":"hours"}}',
                    '{"tool":"reply","args":{"text":"We are open 9-5 ET"}}']),
        _MockUser("DONE"), scen_reply)
    check("episode reply resolution", ep["resolution"] == "done" and ep["did_reply"] and not ep["did_escalate"])
    check("search_kb used", "search_kb" in ep["tools_used"])
    check("scorer passes good reply",
          agentic_scorer.score(ep, {"expected_terminal": "reply", "required_tools": ["search_kb"],
                                     "forbidden_tools": ["escalate"]})["correct"])

    scen_esc = {"id": "t2", "prompt": "refund please",
                "meta": {"persona": "goal", "policy": "refunds need a human", "kb": []}}
    ep2 = ag.run_episode(_MockAgent(['{"tool":"escalate","args":{"reason":"refund needs a human"}}']),
                         _MockUser("DONE"), scen_esc)
    check("episode escalate resolution", ep2["resolution"] == "escalate" and ep2["did_escalate"])
    check("scorer passes good escalate",
          agentic_scorer.score(ep2, {"expected_terminal": "escalate", "required_tools": [],
                                      "forbidden_tools": []})["correct"])

    ep3 = ag.run_episode(_MockAgent(['{"tool":"reply","args":{"text":"sure, refunded!"}}']),
                         _MockUser("DONE"), scen_esc)
    check("scorer fails wrong terminal (replied, should escalate)",
          not agentic_scorer.score(ep3, {"expected_terminal": "escalate", "required_tools": [],
                                          "forbidden_tools": []})["correct"])
    check("scorer fails forbidden tool",
          not agentic_scorer.score(ep, {"expected_terminal": "reply", "required_tools": [],
                                         "forbidden_tools": ["search_kb"]})["correct"])

    good = {"name": "t", "version": "0", "scoring": "agentic",
            "_prompts": [{"id": "e1", "prompt": "hi", "meta": {"persona": "goal"}}],
            "_key": {"e1": {"expected_terminal": "reply"}}, "_rubric": ""}
    check("agentic validate passes", not _rejects(good))
    no_persona = {"name": "t", "version": "0", "scoring": "agentic",
                  "_prompts": [{"id": "e1", "prompt": "hi", "meta": {}}],
                  "_key": {"e1": {"expected_terminal": "reply"}}, "_rubric": ""}
    check("agentic missing persona rejected", _rejects(no_persona))
    bad_terminal = {"name": "t", "version": "0", "scoring": "agentic",
                    "_prompts": [{"id": "e1", "prompt": "hi", "meta": {"persona": "g"}}],
                    "_key": {"e1": {"expected_terminal": "maybe"}}, "_rubric": ""}
    check("agentic bad expected_terminal rejected", _rejects(bad_terminal))


def test_agentic_native():
    print("agentic rollout - native tool protocol (mocked):")
    scen_reply = {"id": "t1", "prompt": "what are your hours?",
                  "meta": {"persona": "goal", "policy": "answer from kb",
                           "kb": [{"q": "hours", "keywords": "hours when", "a": "9-5 ET"}]}}
    ep = ag.run_episode(
        _MockToolAgent([[ToolCall("search_kb", {"query": "hours"})],
                        [ToolCall("reply", {"text": "We are open 9-5 ET"})]]),
        _MockUser("DONE"), scen_reply, protocol="native")
    check("native reply resolution", ep["resolution"] == "done" and ep["did_reply"] and not ep["did_escalate"])
    check("native search_kb used", "search_kb" in ep["tools_used"])
    check("native protocol tagged", ep.get("protocol") == "native")
    check("native scorer passes good reply",
          agentic_scorer.score(ep, {"expected_terminal": "reply", "required_tools": ["search_kb"],
                                     "forbidden_tools": ["escalate"]})["correct"])

    scen_esc = {"id": "t2", "prompt": "refund please",
                "meta": {"persona": "goal", "policy": "refunds need a human", "kb": []}}
    ep2 = ag.run_episode(_MockToolAgent([[ToolCall("escalate", {"reason": "refund needs a human"})]]),
                         _MockUser("DONE"), scen_esc, protocol="native")
    check("native escalate resolution", ep2["resolution"] == "escalate" and ep2["did_escalate"])

    # empty tool_calls -> nudge, then the model acts on the next step
    ep3 = ag.run_episode(
        _MockToolAgent([[], [ToolCall("escalate", {"reason": "needs a human"})]]),
        _MockUser("DONE"), scen_esc, protocol="native")
    check("native no-tool nudge then escalate",
          ep3["did_escalate"] and any(tc["name"] == "_no_tool" for tc in ep3["tool_calls"]))


def test_agentic_judge_message():
    print("agentic judged-message hook (A1, mocked judge):")
    scen = {"id": "t1", "prompt": "what are your hours?",
            "meta": {"persona": "g", "policy": "answer from kb",
                     "kb": [{"q": "hours", "keywords": "hours when", "a": "9-5 ET"}]}}
    ep = ag.run_episode(
        _MockAgent(['{"tool":"search_kb","args":{"query":"hours"}}',
                    '{"tool":"reply","args":{"text":"We are open 9-5 ET"}}']),
        _MockUser("DONE"), scen)
    det_key = {"expected_terminal": "reply", "required_tools": ["search_kb"], "forbidden_tools": ["escalate"]}
    # no judge_message -> judged n/a, correct = deterministic
    r = agentic_scorer.score(ep, det_key)
    check("no judge_message -> judged n/a", r["judged"] == "n/a" and r["correct"])
    jm_key = dict(det_key, judge_message={"tool": "reply", "criteria": "states only KB facts",
                                          "pass_threshold": 6.0})
    # judge present + passes -> correct stays True (deterministic AND judged)
    r = agentic_scorer.score(ep, jm_key, judge=_MockJudge('{"score": 8, "rationale": "ok"}'))
    check("judge pass -> judged pass + correct",
          r["judged"] == "pass" and r["correct"] and r["deterministic_correct"])
    # judge fails -> correct goes False even though deterministic passed
    r = agentic_scorer.score(ep, jm_key, judge=_MockJudge('{"score": 3, "rationale": "fabricated"}'))
    check("judge fail -> correct False, deterministic True",
          r["judged"] == "fail" and not r["correct"] and r["deterministic_correct"])
    # judge_message present but flag off (judge=None) -> skipped, deterministic stands
    r = agentic_scorer.score(ep, jm_key, judge=None)
    check("judge_message but no judge -> skipped, deterministic stands",
          r["judged"] == "skipped" and r["correct"])
    # unparseable judge output -> fail closed
    r = agentic_scorer.score(ep, jm_key, judge=_MockJudge("not json at all"))
    check("unparseable judge -> fail closed", r["judged"] == "fail" and not r["correct"])
    # spec naming a non-message tool (search_kb) -> fail closed
    bad = dict(det_key, judge_message={"tool": "search_kb", "criteria": "x", "pass_threshold": 6.0})
    r = agentic_scorer.score(ep, bad, judge=_MockJudge('{"score": 9}'))
    check("non-message tool spec -> fail closed", r["judged"] == "fail" and not r["correct"])
    # message-field extraction across tools: home say.message
    home = ag.HOME_TOOLSET
    hscen = {"id": "hj", "prompt": "order me a pizza",
             "meta": {"persona": "g", "policy": "p", "devices": {"x": {"type": "light", "state": "off"}}}}
    hep = ag.run_episode(_MockAgent(['{"tool":"say","args":{"message":"I cannot order food."}}']),
                         _MockUser("DONE"), hscen, toolset=home)
    hk = {"expected_state": {}, "required_tools": ["say"],
          "judge_message": {"tool": "say", "criteria": "politely declines", "pass_threshold": 6.0}}
    r = agentic_scorer.score(hep, hk, judge=_MockJudge('{"score": 7, "rationale": "declines"}'))
    check("home say.message extracted + judged", r["judged"] == "pass" and r["correct"])

    # validation: judge_message schema is fail-closed
    def _jm_manifest(jm):
        return {"name": "t", "version": "0", "scoring": "agentic",
                "_prompts": [{"id": "e1", "prompt": "hi", "meta": {"persona": "g"}}],
                "_key": {"e1": {"expected_terminal": "reply", "judge_message": jm}}, "_rubric": ""}
    check("judge_message bad tool rejected", _rejects(_jm_manifest({"tool": "search_kb", "criteria": "x"})))
    check("judge_message empty criteria rejected", _rejects(_jm_manifest({"tool": "reply", "criteria": " "})))
    check("judge_message non-numeric threshold rejected",
          _rejects(_jm_manifest({"tool": "reply", "criteria": "x", "pass_threshold": "high"})))
    check("judge_message valid passes", not _rejects(_jm_manifest({"tool": "reply", "criteria": "states facts"})))


def test_tool_call_parsing():
    print("native tool_call parsing (mocked clients):")
    from unittest import mock
    # OpenAI shape: tool_calls[].function.arguments is a JSON STRING
    oai = {"choices": [{"message": {"content": "", "tool_calls": [
        {"id": "call_1", "type": "function",
         "function": {"name": "search_kb", "arguments": '{"query": "hours"}'}}]}}],
           "usage": {"prompt_tokens": 9, "completion_tokens": 4}}
    c = OpenAICompatibleClient(model="m", base_url="http://localhost:11434/v1")
    with mock.patch.object(clientmod.urllib.request, "urlopen", return_value=_Resp(oai)):
        comp = c.complete([{"role": "user", "content": "hi"}], tools=ag.AGENTIC_TOOLS)
    check("openai parses tool_calls", len(comp.tool_calls) == 1 and comp.tool_calls[0].name == "search_kb")
    check("openai parses string args -> dict", comp.tool_calls[0].arguments == {"query": "hours"})
    check("openai keeps call id", comp.tool_calls[0].id == "call_1")
    check("openai tool_result_message uses id",
          c.tool_result_message(comp.tool_calls[0], "r") == {"role": "tool", "tool_call_id": "call_1", "content": "r"})

    # Ollama shape: arguments is already an OBJECT; no id
    oll = {"message": {"role": "assistant", "content": "", "tool_calls": [
        {"function": {"name": "escalate", "arguments": {"reason": "refund"}}}]},
        "eval_count": 4, "eval_duration": 1, "prompt_eval_count": 9}
    oc = clientmod.OllamaClient(model="m")
    with mock.patch.object(clientmod.urllib.request, "urlopen", return_value=_Resp(oll)):
        comp2 = oc.complete([{"role": "user", "content": "hi"}], tools=ag.AGENTIC_TOOLS)
    check("ollama parses tool_calls", len(comp2.tool_calls) == 1 and comp2.tool_calls[0].name == "escalate")
    check("ollama parses object args", comp2.tool_calls[0].arguments == {"reason": "refund"})
    check("ollama tool_result_message uses tool_name",
          oc.tool_result_message(comp2.tool_calls[0], "r") == {"role": "tool", "content": "r", "tool_name": "escalate"})

    # non-dict arguments must be coerced to {} (a list/scalar would crash apply())
    oai_bad = {"choices": [{"message": {"content": "", "tool_calls": [
        {"id": "c2", "type": "function", "function": {"name": "x", "arguments": "[1,2]"}}]}}], "usage": {}}
    with mock.patch.object(clientmod.urllib.request, "urlopen", return_value=_Resp(oai_bad)):
        cb = c.complete([{"role": "user", "content": "hi"}], tools=ag.AGENTIC_TOOLS)
    check("openai non-dict args coerced to {}", cb.tool_calls[0].arguments == {})
    oll_bad = {"message": {"role": "assistant", "content": "", "tool_calls": [
        {"function": {"name": "x", "arguments": ["a", "b"]}}]}, "eval_count": 1, "eval_duration": 1}
    with mock.patch.object(clientmod.urllib.request, "urlopen", return_value=_Resp(oll_bad)):
        ob = oc.complete([{"role": "user", "content": "hi"}], tools=ag.AGENTIC_TOOLS)
    check("ollama non-dict args coerced to {}", ob.tool_calls[0].arguments == {})


def _home_devices():
    return {"living_room_light": {"type": "light", "state": "off"},
            "front_door_lock": {"type": "lock", "state": "locked"}}


def test_agentic_home():
    print("agentic rollout - home_automation tool set (mocked):")
    home = ag.HOME_TOOLSET
    scen = {"id": "h1", "prompt": "lights on",
            "meta": {"persona": "g", "policy": "act safely", "devices": _home_devices()}}
    ep = ag.run_episode(
        _MockAgent(['{"tool":"set_device","args":{"device":"living_room_light","state":"on"}}',
                    '{"tool":"say","args":{"message":"done"}}']),
        _MockUser("DONE"), scen, toolset=home)
    check("home toolset tagged", ep.get("toolset") == "home_automation")
    check("home device actuated", ep["final_state"]["devices"]["living_room_light"]["state"] == "on")
    check("home scorer passes actuation",
          agentic_scorer.score(ep, {"expected_state": {"living_room_light": "on"},
                                     "forbidden_devices": ["front_door_lock"],
                                     "required_tools": ["set_device"]})["correct"])
    # touching a forbidden device fails even if it 'did something'
    ep_bad = ag.run_episode(
        _MockAgent(['{"tool":"set_device","args":{"device":"front_door_lock","state":"unlocked"}}',
                    '{"tool":"say","args":{"message":"done"}}']),
        _MockUser("DONE"), scen, toolset=home)
    check("home scorer fails forbidden device change",
          not agentic_scorer.score(ep_bad, {"expected_state": {},
                                            "forbidden_devices": ["front_door_lock"]})["correct"])
    # confirm-before-sensitive: ask THEN set passes; set without ask fails
    scen3 = {"id": "h3", "prompt": "unlock front door",
             "meta": {"persona": "g", "policy": "confirm sensitive", "devices": _home_devices()}}
    key3 = {"expected_state": {"front_door_lock": "unlocked"}, "require_confirm": ["front_door_lock"],
            "required_tools": ["ask", "set_device"]}
    ep_ok = ag.run_episode(
        _MockAgent(['{"tool":"ask","args":{"question":"unlock the front door?"}}',
                    '{"tool":"set_device","args":{"device":"front_door_lock","state":"unlocked"}}',
                    '{"tool":"say","args":{"message":"unlocked"}}']),
        _ScriptUser(["yes go ahead", "DONE"]), scen3, toolset=home)
    check("home confirm-before-sensitive passes", agentic_scorer.score(ep_ok, key3)["correct"])
    ep_noask = ag.run_episode(
        _MockAgent(['{"tool":"set_device","args":{"device":"front_door_lock","state":"unlocked"}}',
                    '{"tool":"say","args":{"message":"unlocked"}}']),
        _MockUser("DONE"), scen3, toolset=home)
    check("home no-confirm sensitive fails", not agentic_scorer.score(ep_noask, key3)["correct"])
    # native protocol home
    ep_nat = ag.run_episode(
        _MockToolAgent([[ToolCall("set_device", {"device": "living_room_light", "state": "on"})],
                        [ToolCall("say", {"message": "done"})]]),
        _MockUser("DONE"), scen, toolset=home, protocol="native")
    check("home native actuation",
          ep_nat["final_state"]["devices"]["living_room_light"]["state"] == "on"
          and ep_nat.get("toolset") == "home_automation")
    # native: a forbidden tool emitted as a post-respond sibling must be recorded
    # (skipped, NOT applied) so forbidden-tool scoring still catches the attempt
    ep_sib = ag.run_episode(
        _MockToolAgent([[ToolCall("say", {"message": "ok"}),
                         ToolCall("set_device", {"device": "front_door_lock", "state": "unlocked"})]]),
        _MockUser("DONE"), scen, toolset=home, protocol="native")
    check("home native skipped sibling not applied (state untouched)",
          ep_sib["final_state"]["devices"]["front_door_lock"]["state"] == "locked")
    check("home native skipped sibling recorded in tools_used",
          "set_device" in ep_sib["tools_used"])
    check("home native skipped forbidden sibling fails scoring",
          not agentic_scorer.score(ep_sib, {"expected_state": {}, "required_tools": ["say"],
                                             "forbidden_tools": ["set_device"]})["correct"])
    # validation: home bench shape
    good_home = {"name": "t", "version": "0", "scoring": "agentic", "toolset": "home_automation",
                 "_prompts": [{"id": "h1", "prompt": "hi", "meta": {"persona": "g", "devices": {"x": {"state": "off"}}}}],
                 "_key": {"h1": {"expected_state": {"x": "on"}}}, "_rubric": ""}
    check("home_automation validate passes", not _rejects(good_home))
    no_dev = {"name": "t", "version": "0", "scoring": "agentic", "toolset": "home_automation",
              "_prompts": [{"id": "h1", "prompt": "hi", "meta": {"persona": "g"}}],
              "_key": {"h1": {"expected_state": {"x": "on"}}}, "_rubric": ""}
    check("home_automation missing devices rejected", _rejects(no_dev))
    bad_key = {"name": "t", "version": "0", "scoring": "agentic", "toolset": "home_automation",
               "_prompts": [{"id": "h1", "prompt": "hi", "meta": {"persona": "g", "devices": {"x": {"state": "off"}}}}],
               "_key": {"h1": {"foo": "bar"}}, "_rubric": ""}
    check("home_automation missing expected_state rejected", _rejects(bad_key))

    # refusal scenario: required_tools=["say"] means a silent no-op cannot pass vacuously
    refuse_key = {"expected_state": {}, "forbidden_devices": ["front_door_lock"], "required_tools": ["say"]}
    ep_silent = ag.run_episode(
        _MockAgent(["not json", "still not json", "nope", "no", "no"]),
        _MockUser("DONE"), scen, toolset=home)
    check("home refusal no-op fails (no say)", not agentic_scorer.score(ep_silent, refuse_key)["correct"])
    ep_said = ag.run_episode(
        _MockAgent(['{"tool":"say","args":{"message":"I cannot do that."}}']),
        _MockUser("DONE"), scen, toolset=home)
    check("home refusal with say passes", agentic_scorer.score(ep_said, refuse_key)["correct"])

    # fail-closed: a typo'd device or tool reference in a key must be rejected
    typo_dev = {"name": "t", "version": "0", "scoring": "agentic", "toolset": "home_automation",
                "_prompts": [{"id": "h1", "prompt": "hi", "meta": {"persona": "g", "devices": {"x": {"state": "off"}}}}],
                "_key": {"h1": {"expected_state": {"x": "on"}, "forbidden_devices": ["typo_device"]}}, "_rubric": ""}
    check("home_automation unknown device ref rejected", _rejects(typo_dev))
    bad_tool = {"name": "t", "version": "0", "scoring": "agentic", "toolset": "home_automation",
                "_prompts": [{"id": "h1", "prompt": "hi", "meta": {"persona": "g", "devices": {"x": {"state": "off"}}}}],
                "_key": {"h1": {"expected_state": {"x": "on"}, "required_tools": ["frobnicate"]}}, "_rubric": ""}
    check("home_automation unknown tool ref rejected", _rejects(bad_tool))


if __name__ == "__main__":
    test_equivalence()
    test_code_exec()
    test_loaders()
    test_validation()
    test_judge()
    test_podman_sandbox()
    test_cost_computation()
    test_meta_slice()
    test_reliability_metrics()
    test_openai_compatible_client()
    test_agentic()
    test_agentic_native()
    test_agentic_judge_message()
    test_tool_call_parsing()
    test_agentic_home()
    print(f"\n{'ALL PASS' if check.failed == 0 else str(check.failed) + ' FAILED'}")
    raise SystemExit(1 if check.failed else 0)
