"""Execute candidate code against tests in a best-effort sandbox.

Extracts code from a completion (strips markdown fences), concatenates the test
snippet, and runs it in a subprocess with a wall-clock timeout and (on Linux)
CPU/address-space rlimits. This is a *best-effort* sandbox - for fully untrusted
code prefer a container or a dedicated jail. Never run this on code you wouldn't
want touching the machine without isolation.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import textwrap

_FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.S | re.I)


def extract_code(text: str) -> str:
    """Pull the largest fenced code block, else assume the whole text is code."""
    blocks = _FENCE.findall(text or "")
    if blocks:
        return max(blocks, key=len).strip()
    return (text or "").strip()


def _limit_resources(cpu_s: int, mem_mb: int):  # pragma: no cover - child process
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_CPU, (cpu_s, cpu_s))
        nbytes = mem_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (nbytes, nbytes))
    except Exception:
        pass


def score(prediction: str, tests: str, timeout: int = 10, mem_mb: int = 1024) -> dict:
    code = extract_code(prediction)
    program = code + "\n\n" + textwrap.dedent(tests or "")
    with tempfile.TemporaryDirectory() as tmp:
        try:
            proc = subprocess.run(
                [sys.executable, "-I", "-c", program],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=timeout,
                preexec_fn=(lambda: _limit_resources(timeout, mem_mb))
                if sys.platform != "win32"
                else None,
            )
        except subprocess.TimeoutExpired:
            return {"correct": False, "error": "timeout", "extracted_len": len(code)}
        ok = proc.returncode == 0
        return {
            "correct": ok,
            "returncode": proc.returncode,
            "stderr": proc.stderr[-2000:] if not ok else "",
            "extracted_len": len(code),
        }
