"""Judge client backed by GitHub Copilot CLI (a frontier model, e.g. claude-opus-4.8).

This is THE judge path for `llm_judge` benchmarks. **Never use a local small model
as a judge** - judging open-ended work (reasoning, decision-making, creative
writing) needs a frontier model. Plugs into `scorers.llm_judge` via the same
`.complete(messages, system=...)` interface as `client.ChatClient`.

Verified invocation (see .github/skills/copilot-cli/SKILL.md):
    copilot -p '<prompt>' --model claude-opus-4.8 --no-custom-instructions \
        --allow-all-tools --no-ask-user --log-level none -s
"""
from __future__ import annotations

import random
import subprocess
import time
from dataclasses import dataclass

if __package__ in (None, ""):
    from client import Completion
else:
    from .client import Completion


# --------------------------------------------------------------------------- #
# Shared Copilot-CLI runner with bounded retry. Copilot rate-limits / has
# transient auth blips on rapid successive calls (confirmed); a single failure
# must not abort a whole run - especially once calls fan out concurrently. Retry
# ONLY transient signatures; FAIL FAST on permanent config errors (e.g. an
# invalid --model exits 0 but prints `Error: Model ... not available` on stdout).
# --------------------------------------------------------------------------- #

_TRANSIENT_SIGNS = ("authentication failed", "rate limit", "rate_limit", "429",
                    "overloaded", "temporarily", "timed out", "timeout", "503")


def _classify_copilot(out: str, err: str) -> str:
    """Return 'ok' | 'transient' | 'permanent' for a finished copilot run.

    Only DIAGNOSTIC streams are keyword-scanned. A successful response is real model
    text (a user-sim reply or judge JSON) and may legitimately contain words like
    "temporarily" or "429", so it is NEVER scanned: non-empty stdout that is not a
    CLI ``Error:`` line is returned as-is.
    """
    if out and not out.startswith("Error:"):
        return "ok"
    diag = (err + " " + out).lower()   # out is "" or an "Error: ..." CLI line here
    if any(s in diag for s in _TRANSIENT_SIGNS):
        return "transient"
    if out.startswith("Error:") or err:
        return "permanent"    # a real diagnostic with no transient marker -> fail fast
    return "transient"        # empty stdout + empty stderr = the classic silent blip


def run_copilot_cli(cmd: list[str], timeout: int, tries: int = 3,
                    label: str = "copilot", backoff_base: float = 2.0) -> str:
    """Run a ``copilot -p`` command, returning clean stdout.

    Retries TRANSIENT failures (timeout, empty stdout, auth/rate-limit text) with
    exponential backoff + jitter, up to ``tries``. FAILS FAST on a permanent config
    error (retrying just delays the real error). Raises ``RuntimeError`` on a
    permanent error or after ``tries`` transient failures.
    """
    last = ""
    for attempt in range(1, tries + 1):
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            last = f"timed out after {timeout}s"
        else:
            out = (proc.stdout or "").strip()
            err = (proc.stderr or "").strip()
            kind = _classify_copilot(out, err)
            if kind == "ok":
                return out
            if kind == "permanent":
                raise RuntimeError(f"{label} permanent error (not retried): {out!r}")
            last = f"stdout={out!r} stderr={err!r}" if (out or err) else "empty output"
        if attempt < tries:
            delay = backoff_base * (2 ** (attempt - 1))
            time.sleep(delay + random.uniform(0, 0.5 * delay))
    raise RuntimeError(f"{label} failed after {tries} tries (transient): {last}")


@dataclass
class CopilotCLIJudge:
    model: str = "claude-opus-4.8"
    timeout: int = 180
    effort: str | None = None  # low|medium|high|xhigh|max
    tries: int = 3

    def complete(self, messages: list[dict], system: str | None = None) -> Completion:
        user = "\n\n".join(m["content"] for m in messages if m.get("role") == "user")
        prompt = f"{system}\n\n{user}" if system else user
        cmd = [
            "copilot", "-p", prompt,
            "--model", self.model,
            "--no-custom-instructions",  # do NOT load AGENTS.md into the judge
            "--allow-all-tools",         # required for non-interactive -p
            "--no-ask-user",             # judge never blocks asking a question
            "--log-level", "none",
            "-s",                        # response only (clean stdout)
        ]
        if self.effort:
            cmd += ["--reasoning-effort", self.effort]
        t0 = time.monotonic()
        out = run_copilot_cli(cmd, self.timeout, tries=self.tries,
                              label=f"copilot judge ({self.model})")
        wall = round(time.monotonic() - t0, 2)
        return Completion(text=out, wall_s=wall)

    def describe(self) -> dict:
        return {"judge_backend": "copilot-cli", "model": self.model, "effort": self.effort or "default"}
