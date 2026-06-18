"""Thin, local-first benchmark harness for the local-models lab.

A benchmark = prompts + a scoring method. This package runs prompts against a
local model (Ollama by default) and scores completions one of three ways:

- ``equivalence``  math/numeric answer matching (``scorers.equivalence``)
- ``code_tests``   execute candidate code against tests in a sandbox (``scorers.code_exec``)
- ``llm_judge``    rubric-scored by a pinned judge model (``scorers.llm_judge``)

For standard public coding/math suites, prefer wrapping the upstream framework
(evalplus, lm-eval-harness, livecodebench) - see the wiki benchmark pages. This
harness is the engine for our own authored datasets under ``benchmarks/<name>/``.
"""

__all__ = ["client", "run", "scorers"]
