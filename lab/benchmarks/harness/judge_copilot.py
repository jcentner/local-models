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

import subprocess
import time
from dataclasses import dataclass

if __package__ in (None, ""):
    from client import Completion
else:
    from .client import Completion


@dataclass
class CopilotCLIJudge:
    model: str = "claude-opus-4.8"
    timeout: int = 180
    effort: str | None = None  # low|medium|high|xhigh|max

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
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"copilot judge timed out after {self.timeout}s") from e
        wall = round(time.monotonic() - t0, 2)
        out = (proc.stdout or "").strip()
        # Invalid model / errors exit 0 but print "Error: Model ..." - check stdout.
        if not out or out.startswith("Error:"):
            raise RuntimeError(
                f"copilot judge ({self.model}) produced no usable output: "
                f"{out or proc.stderr.strip()!r}")
        return Completion(text=out, wall_s=wall)

    def describe(self) -> dict:
        return {"judge_backend": "copilot-cli", "model": self.model, "effort": self.effort or "default"}
