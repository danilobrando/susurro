"""Backend factories — local-only by default, extensible by external packages.

The OSS susurro ships ONE STT backend (`local` — MLX Whisper) and ONE polish
LLM backend (`local` — MLX-LM). Additional backends (cloud STT, cloud polish)
can register themselves via `register_transcriber()` and `register_polish_llm()`
from another package. See `susurro-pro` for the canonical example.

This keeps the OSS package free of network dependencies and any cloud-specific
configuration while still allowing rich extension by paid / private downstream
packages.
"""

from __future__ import annotations

from collections.abc import Callable

from .base import BackendError, BackendUnavailable, PolishLLM, Transcriber

# Registries populated by external packages on import.
_EXTRA_TRANSCRIBERS: dict[str, Callable[[], Transcriber]] = {}
_EXTRA_POLISH: dict[str, Callable[[], PolishLLM]] = {}


def register_transcriber(name: str, factory: Callable[[], Transcriber]) -> None:
    """Register a Transcriber factory under `name`. Idempotent overwrite."""
    _EXTRA_TRANSCRIBERS[name.lower()] = factory


def register_polish_llm(name: str, factory: Callable[[], PolishLLM]) -> None:
    """Register a PolishLLM factory under `name`. Idempotent overwrite."""
    _EXTRA_POLISH[name.lower()] = factory


def available_transcribers() -> list[str]:
    return ["local", *sorted(_EXTRA_TRANSCRIBERS.keys())]


def available_polish_llms() -> list[str]:
    return ["local", *sorted(_EXTRA_POLISH.keys())]


def make_transcriber(backend: str) -> Transcriber:
    """Construct an STT backend by name. Does not warm it up."""
    backend = backend.lower()
    if backend == "local":
        from .local_mlx import MLXTranscriber

        return MLXTranscriber()
    if backend in _EXTRA_TRANSCRIBERS:
        return _EXTRA_TRANSCRIBERS[backend]()
    raise ValueError(f"Unknown STT backend: {backend!r}. Available: {', '.join(available_transcribers())}")


def make_polish_llm(backend: str) -> PolishLLM:
    """Construct a polish LLM backend by name. Does not warm it up."""
    backend = backend.lower()
    if backend == "local":
        from .local_mlx_lm import LocalMLXPolishLLM

        return LocalMLXPolishLLM()
    if backend in _EXTRA_POLISH:
        return _EXTRA_POLISH[backend]()
    raise ValueError(f"Unknown polish backend: {backend!r}. Available: {', '.join(available_polish_llms())}")


__all__ = [
    "BackendError",
    "BackendUnavailable",
    "PolishLLM",
    "Transcriber",
    "available_polish_llms",
    "available_transcribers",
    "make_polish_llm",
    "make_transcriber",
    "register_polish_llm",
    "register_transcriber",
]
