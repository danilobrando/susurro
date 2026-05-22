"""Deterministic rule-based polish — runs in <5 ms with no LLM.

Karpathy's principle: 70% of cleanups can be regex. Save the LLM for the
hard 30%. These rules are SAFE — they only remove or normalize whitespace
and a small set of clearly-filler words. They never restructure or rewrite.
"""

from __future__ import annotations

import re

# Standalone filler words. Only matched when surrounded by whitespace or
# punctuation, never as part of a longer word. Conservative on purpose —
# "like" and "como que" are often meaningful, so we don't touch them.
_FILLERS = [
    r"eh+",
    r"ah+",
    r"mmm+",
    r"hmm+",
    r"uhh+",
    r"umm+",
    r"este pues",
    r"o sea sí",
]
_FILLER_RE = re.compile(
    r"(?<![A-Za-zÁ-Úá-úñÑ])(?:" + "|".join(_FILLERS) + r")(?![A-Za-zÁ-Úá-úñÑ])",
    re.IGNORECASE,
)

# Cleanup steps for the commas/periods left dangling after filler removal.
# Run in order; each step assumes the previous succeeded.
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,;:.!?])")  # " ," → ","
_STRONG_THEN_SOFT = re.compile(r"([.!?])\s*[,;:]+")  # "." then "," → "."
_DOUBLED_SOFT = re.compile(r"([,;:])(?:\s*[,;:])+")  # ",," → ","
_REPEATED_WS = re.compile(r"\s+")
_LEADING_PUNCT = re.compile(r"^[\s,;:.!?]+")


def apply_rules(text: str) -> str:
    """Conservative cleanup — fillers + whitespace + dangling punctuation only."""
    if not text:
        return text
    out = _FILLER_RE.sub("", text)
    out = _SPACE_BEFORE_PUNCT.sub(r"\1", out)
    out = _STRONG_THEN_SOFT.sub(r"\1", out)
    out = _DOUBLED_SOFT.sub(r"\1", out)
    out = _REPEATED_WS.sub(" ", out)
    out = _LEADING_PUNCT.sub("", out)
    return out.strip()
