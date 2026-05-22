"""Decide whether a transcript is worth sending to the LLM.

LLM polish costs ~300 ms (Groq) or ~1 s (local). For most short, simple
transcripts the regex rules cover everything, so we skip the network call.
A transcript triggers the LLM if:

- It contains ordinal markers (likely a list).
- It contains explicit backtrack phrases ("en realidad", "actually", "digo").
- It's long enough (>40 words) that paragraph breaks become useful.
"""

from __future__ import annotations

import re

_ORDINAL_RE = re.compile(
    r"\b("
    r"primer[oa]s?|segund[oa]s?|tercer[oa]s?|cuart[oa]s?|quint[oa]s?|"
    r"en primer lugar|en segundo lugar|en tercer lugar|"
    r"first|second|third|fourth|fifth|"
    r"finalmente|por último|finally"
    r")\b",
    re.IGNORECASE,
)

_BACKTRACK_RE = re.compile(
    r"\b(en realidad|actually|i mean|digo|mejor dicho|wait no|scratch that)\b",
    re.IGNORECASE,
)

_LONG_THRESHOLD_WORDS = 40


def should_invoke_llm(text: str) -> bool:
    """Return True if the LLM is likely to add value over plain rules."""
    if not text:
        return False
    if _ORDINAL_RE.search(text):
        return True
    if _BACKTRACK_RE.search(text):
        return True
    return len(text.split()) > _LONG_THRESHOLD_WORDS
