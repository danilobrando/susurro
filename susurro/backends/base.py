"""Backend protocols and shared exceptions.

A backend is a pluggable implementation of either:
- `Transcriber` — turns audio into raw text
- `PolishLLM` — turns raw text into structured text

Backends are constructed lazily by the factories in `susurro.backends`. They
must be safe to construct without a network or model load — heavy work happens
in `warmup()`.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np


class BackendError(RuntimeError):
    """Raised when a backend fails to perform its operation."""


class BackendUnavailable(BackendError):
    """Raised when a backend can't be used at all (missing key, no network, etc.)."""


@runtime_checkable
class Transcriber(Protocol):
    """Speech-to-text backend."""

    name: str

    def warmup(self) -> None:
        """Load models / verify credentials. Called once at app startup."""

    def transcribe(self, audio: np.ndarray) -> str:
        """Return the raw transcript for a mono float32 16 kHz numpy array."""


@runtime_checkable
class PolishLLM(Protocol):
    """LLM-based text polishing backend."""

    name: str

    def warmup(self) -> None:
        """Load models / verify credentials."""

    def polish(self, raw: str, *, system_prompt: str) -> str:
        """Return the polished version of `raw` driven by `system_prompt`."""
