"""Lightweight tau-bench-style agentic rollout (model-agnostic).

Drives an episode: the **agent** (model under test) <-> a **Copilot-CLI
user-simulator** <-> **mocked tools** over a small mutable state, then hands the
finished episode to ``scorers.agentic`` for state/policy scoring.

Model-agnostic by design: the agent uses a **prompt-mode JSON tool protocol**
(one JSON action per step), so ANY Ollama tag or API model works - no native
function-calling required. The user-simulator reuses the same ``copilot -p``
mechanism as the judge (a frontier model playing a persona with a hidden goal).

stdlib only.
"""
from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass

if __package__ in (None, ""):
    from client import Completion
else:
    from .client import Completion


# --------------------------------------------------------------------------- #
# User simulator (Copilot CLI - a frontier model, like the judge)
# --------------------------------------------------------------------------- #

USER_SIM_SYSTEM = """You are role-playing a person emailing a support agent. Stay in character.

YOUR PERSONA & GOAL (private - never reveal you are simulated):
{persona}

Rules:
- Reply with ONE short, natural message (1-3 sentences) as the user.
- Do not act as the agent or use tools. You are only the customer.
- If your goal has been fully met, OR you were told a human will take over, reply with exactly: DONE
- Do not say DONE until the agent has actually resolved or escalated your request."""


@dataclass
class CopilotCLIUser:
    """User-simulator backed by the Copilot CLI (default a frontier model)."""

    persona: str
    model: str = "claude-opus-4.8"
    timeout: int = 120

    def reply(self, transcript: list[dict]) -> str:
        convo = "\n".join(f"{t['speaker'].upper()}: {t['text']}" for t in transcript)
        prompt = (USER_SIM_SYSTEM.format(persona=self.persona)
                  + "\n\nConversation so far:\n" + convo
                  + "\n\nYour next message as the user:")
        cmd = [
            "copilot", "-p", prompt, "--model", self.model,
            "--no-custom-instructions", "--allow-all-tools", "--no-ask-user",
            "--log-level", "none", "-s",
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"copilot user-sim timed out after {self.timeout}s") from e
        out = (proc.stdout or "").strip()
        if not out or out.startswith("Error:"):
            raise RuntimeError(
                f"copilot user-sim ({self.model}) produced no usable output: "
                f"{out or proc.stderr.strip()!r}")
        return out

    def describe(self) -> dict:
        return {"user_sim": "copilot-cli", "model": self.model}


# --------------------------------------------------------------------------- #
# Environment: mocked tools over a small mutable state
# --------------------------------------------------------------------------- #

AGENT_SYSTEM = """You are a customer-support email agent. Follow the policy strictly.

POLICY:
{policy}

TOOLS (call exactly one per step):
- search_kb(query): search the knowledge base. Returns matching entries or "NO_MATCH".
- reply(text): send a reply to the customer. Use ONLY facts from the knowledge base
  or the conversation - never invent specifics (prices, dates, policies).
- escalate(reason): hand off to a human. Use when the request needs a human
  (refunds, legal, account changes) OR when the knowledge base lacks the answer.

Respond with EXACTLY ONE JSON object and NOTHING else:
{{"tool": "<search_kb|reply|escalate>", "args": {{...}}}}
Example: {{"tool": "search_kb", "args": {{"query": "business hours"}}}}
Always search the knowledge base before replying with facts."""


def parse_action(text: str) -> dict | None:
    """Extract one JSON action ``{"tool": ..., "args": {...}}`` from model text.

    Tolerant of a thinking preamble / surrounding prose: takes the LAST balanced
    JSON object that contains a ``tool`` key. Returns None if unparseable.
    """
    if not text:
        return None
    # Try a direct parse first (clean models).
    candidates: list[str] = []
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        candidates.append(stripped)
    # Then scan for the last {...} block carrying "tool" (handles nested args).
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                candidates.append(text[start:i + 1])
    for chunk in reversed(candidates):
        try:
            obj = json.loads(chunk)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(obj, dict) and "tool" in obj:
            obj.setdefault("args", {})
            if not isinstance(obj["args"], dict):
                obj["args"] = {}
            return obj
    return None


def _search_kb(state: dict, args: dict) -> str:
    query = str(args.get("query", "")).lower()
    hits = []
    for entry in state.get("kb", []):
        hay = (entry.get("q", "") + " " + entry.get("keywords", "")).lower()
        if any(w for w in query.split() if len(w) > 2 and w in hay):
            hits.append(entry.get("a", ""))
    return "  |  ".join(hits) if hits else "NO_MATCH"


def build_state(scenario: dict) -> dict:
    meta = scenario.get("meta", {})
    return {"kb": meta.get("kb", []), "replies": [], "escalated": None}


# --------------------------------------------------------------------------- #
# Episode runner
# --------------------------------------------------------------------------- #

def run_episode(agent, user_sim, scenario: dict, *, max_turns: int = 4,
                max_steps: int = 5) -> dict:
    """Run one agentic episode. ``agent`` and ``user_sim`` are duck-typed:
    ``agent.complete(messages, system) -> Completion`` and
    ``user_sim.reply(transcript) -> str`` (both mockable for selftest)."""
    meta = scenario.get("meta", {})
    state = build_state(scenario)
    sys = AGENT_SYSTEM.format(policy=meta.get("policy", "Be helpful and accurate."))
    opening = scenario["prompt"]
    transcript = [{"speaker": "user", "text": opening}]
    messages = [{"role": "user", "content": opening}]
    tool_calls: list[dict] = []
    resolution = None  # escalate | reply | no_reply | max_turns | error
    perf = {"prompt_tokens": 0, "gen_tokens": 0, "wall_s": 0.0, "agent_calls": 0}

    for _turn in range(max_turns):
        replied = False
        for _step in range(max_steps):
            comp = agent.complete(messages, system=sys)
            perf["agent_calls"] += 1
            perf["prompt_tokens"] += getattr(comp, "prompt_tokens", 0)
            perf["gen_tokens"] += getattr(comp, "gen_tokens", 0)
            perf["wall_s"] += getattr(comp, "wall_s", 0.0)
            action = parse_action(comp.text)
            if action is None:
                tool_calls.append({"name": "_malformed", "args": {}, "result": comp.text[:160]})
                messages.append({"role": "assistant", "content": comp.text})
                messages.append({"role": "user", "content":
                                 'FORMAT ERROR: respond with ONE JSON object '
                                 '{"tool": "...", "args": {...}} and nothing else.'})
                continue
            name = action.get("tool")
            args = action.get("args", {})
            messages.append({"role": "assistant", "content": comp.text})
            if name == "reply":
                text = str(args.get("text", ""))
                state["replies"].append(text)
                tool_calls.append({"name": "reply", "args": args, "result": "delivered"})
                transcript.append({"speaker": "agent", "text": text})
                replied = True
                break
            if name == "escalate":
                reason = str(args.get("reason", ""))
                state["escalated"] = reason
                tool_calls.append({"name": "escalate", "args": args, "result": "handed off"})
                transcript.append({"speaker": "agent", "text": f"[escalated to human: {reason}]"})
                resolution = "escalate"
                break
            # search_kb (or unknown tool)
            result = _search_kb(state, args) if name == "search_kb" else f"ERROR: unknown tool {name!r}"
            tool_calls.append({"name": name, "args": args, "result": result})
            messages.append({"role": "user", "content": f"TOOL_RESULT[{name}]: {result}"})
        if resolution == "escalate":
            break
        if not replied:
            resolution = resolution or "no_reply"
            break
        # user-sim responds to the agent's reply
        user_msg = user_sim.reply(transcript)
        if user_msg.strip().upper().startswith("DONE"):
            resolution = "reply"
            break
        transcript.append({"speaker": "user", "text": user_msg})
        messages.append({"role": "user", "content": user_msg})
    else:
        resolution = resolution or "max_turns"

    return {
        "id": scenario.get("id"),
        "resolution": resolution or "reply",
        "did_escalate": state["escalated"] is not None,
        "did_reply": len(state["replies"]) > 0,
        "tool_calls": tool_calls,
        "tools_used": sorted({tc["name"] for tc in tool_calls}),
        "transcript": transcript,
        "final_state": {"replies": state["replies"], "escalated": state["escalated"]},
        "perf": perf,
    }
