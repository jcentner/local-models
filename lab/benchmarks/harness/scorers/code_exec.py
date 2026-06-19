"""Execute candidate code against tests in a sandbox.

Two modes (selected by the caller / ``--code-sandbox``):

- ``podman`` (recommended): run in a throwaway, locked-down container -
  ``--network none``, read-only rootfs, tmpfs workdir, memory/pid/cpu caps,
  non-root, no-new-privileges, all caps dropped. Real isolation for untrusted
  model-written code.
- ``local-unsafe``: host subprocess with a timeout + (Linux) rlimits. Best-effort
  only - NO filesystem/network isolation. Explicit opt-in.

Both extract code from the completion (strip markdown fences), append the test
snippet, and check the exit code (tests use ``assert``).
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import textwrap

PODMAN_IMAGE = os.environ.get("HARNESS_PODMAN_IMAGE", "docker.io/library/python:3.12-slim")

_FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.S | re.I)


def extract_code(text: str) -> str:
    """Pull the largest fenced code block, else assume the whole text is code."""
    blocks = _FENCE.findall(text or "")
    if blocks:
        return max(blocks, key=len).strip()
    return (text or "").strip()


def podman_available() -> bool:
    try:
        subprocess.run(["podman", "--version"], capture_output=True, timeout=10, check=True)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def sandbox_available(mode: str) -> bool:
    return True if mode == "local-unsafe" else podman_available()


def _limit_resources(cpu_s: int, mem_mb: int):  # pragma: no cover - child process
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_CPU, (cpu_s, cpu_s))
        nbytes = mem_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (nbytes, nbytes))
    except Exception:
        pass


def _run_local(program: str, timeout: int, mem_mb: int, code_len: int) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        try:
            proc = subprocess.run(
                [sys.executable, "-IB", "-c", program],
                cwd=tmp, capture_output=True, text=True, timeout=timeout,
                preexec_fn=(lambda: _limit_resources(timeout, mem_mb)) if sys.platform != "win32" else None,
            )
        except subprocess.TimeoutExpired:
            return {"correct": False, "error": "timeout", "sandbox": "local-unsafe", "extracted_len": code_len}
        ok = proc.returncode == 0
        return {"correct": ok, "returncode": proc.returncode,
                "stderr": proc.stderr[-2000:] if not ok else "",
                "sandbox": "local-unsafe", "extracted_len": code_len}


def _run_podman(program: str, timeout: int, mem_mb: int, code_len: int) -> dict:
    cmd = [
        "podman", "run", "--rm", "-i",
        "--timeout", str(timeout),          # conmon kills the container after N seconds
        "--network", "none",
        "--read-only", "--tmpfs", "/tmp:size=64m",
        "--workdir", "/tmp",
        "--memory", f"{mem_mb}m", "--memory-swap", f"{mem_mb}m",
        "--pids-limit", "128", "--cpus", "1",
        "--user", "65534:65534",            # nobody:nogroup
        "--security-opt", "no-new-privileges",
        "--cap-drop", "ALL",
        PODMAN_IMAGE, "python3", "-IB", "-",
    ]
    try:
        proc = subprocess.run(cmd, input=program, capture_output=True, text=True, timeout=timeout + 10)
    except subprocess.TimeoutExpired:
        return {"correct": False, "error": "timeout", "sandbox": "podman", "extracted_len": code_len}
    except FileNotFoundError as e:
        raise RuntimeError("podman not found on PATH") from e
    ok = proc.returncode == 0
    return {"correct": ok, "returncode": proc.returncode,
            "stderr": proc.stderr[-2000:] if not ok else "",
            "sandbox": "podman", "extracted_len": code_len}


def score(prediction: str, tests: str, timeout: int = 10, mem_mb: int = 512,
          mode: str = "local-unsafe") -> dict:
    code = extract_code(prediction)
    program = code + "\n\n" + textwrap.dedent(tests or "")
    if mode == "podman":
        return _run_podman(program, timeout, mem_mb, len(code))
    if mode == "local-unsafe":
        return _run_local(program, timeout, mem_mb, len(code))
    raise SystemExit(f"unknown code sandbox mode: {mode!r}")
