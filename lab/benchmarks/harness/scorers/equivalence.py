"""Math / numeric answer equivalence.

Extracts a final answer from a model completion and checks it against the gold
answer. Uses sympy for symbolic/numeric equivalence when available, with a
normalized-string + float fallback so the harness still runs without sympy.
"""
from __future__ import annotations

import re

try:  # optional dependency
    import sympy
    from sympy.parsing.sympy_parser import parse_expr

    _HAVE_SYMPY = True
except Exception:  # pragma: no cover
    _HAVE_SYMPY = False


_BOXED = re.compile(r"\\boxed\{([^{}]*)\}")
_ANSWER_IS = re.compile(r"(?:final answer|answer)\s*(?:is|:)?\s*\$?([^\n$]+)", re.I)
_NUMBER = re.compile(r"-?\d+(?:,\d{3})*(?:\.\d+)?")


def extract_final(text: str) -> str:
    """Best-effort pull of the final answer from a completion."""
    if not text:
        return ""
    boxed = _BOXED.findall(text)
    if boxed:
        return boxed[-1].strip()
    m = _ANSWER_IS.search(text)
    if m:
        ans = m.group(1).strip().rstrip(".").strip()
        return ans
    nums = _NUMBER.findall(text)
    if nums:
        return nums[-1].replace(",", "").strip()
    return text.strip().splitlines()[-1].strip() if text.strip() else ""


def _normalize(s: str) -> str:
    s = s.strip().strip("$").replace(",", "").replace(" ", "")
    s = s.rstrip(".")
    return s.lower()


def equivalent(pred: str, gold: str) -> bool:
    if _normalize(pred) == _normalize(gold):
        return True
    # numeric compare
    try:
        if abs(float(_normalize(pred)) - float(_normalize(gold))) < 1e-6:
            return True
    except ValueError:
        pass
    if _HAVE_SYMPY:
        try:
            diff = parse_expr(_normalize(pred)) - parse_expr(_normalize(gold))
            return bool(sympy.simplify(diff) == 0)
        except Exception:
            return False
    return False


def score(prediction: str, answer: str) -> dict:
    pred = extract_final(prediction)
    ok = equivalent(pred, str(answer))
    return {"correct": ok, "extracted": pred, "gold": str(answer)}
