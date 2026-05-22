"""Backend factories — hot-swappable STT and polish providers.

Adding a new backend means dropping a new module in this directory and
adding a branch to the relevant factory. Backends are constructed lazily;
heavy work (model loading, key verification) happens in `warmup()`.

Currently implemented:
    STT:    local (MLX Whisper), groq (Whisper hosted)
    Polish: groq (Llama 3.3 70B)

Planned (see backends/STUBS.md for protocol expectations):
    STT:    openai, deepgram, gemini, anthropic
    Polish: anthropic, openai, gemini
"""

from __future__ import annotations

from .base import BackendError, BackendUnavailable, PolishLLM, Transcriber


def make_transcriber(backend: str) -> Transcriber:
    """Construct an STT backend by name. Does not warm it up."""
    backend = backend.lower()
    if backend == "local":
        from .local_mlx import MLXTranscriber

        return MLXTranscriber()
    if backend == "groq":
        from .groq import GroqTranscriber

        return GroqTranscriber()
    raise ValueError(
        f"Unknown STT backend: {backend!r}. "
        "Available: local, groq. Planned: openai, deepgram, gemini, anthropic."
    )


def make_polish_llm(backend: str) -> PolishLLM:
    """Construct a polish LLM backend by name. Does not warm it up."""
    backend = backend.lower()
    if backend == "groq":
        from .groq import GroqPolishLLM

        return GroqPolishLLM()
    raise ValueError(
        f"Unknown polish backend: {backend!r}. Available: groq. Planned: anthropic, openai, gemini."
    )


__all__ = [
    "BackendError",
    "BackendUnavailable",
    "PolishLLM",
    "Transcriber",
    "make_polish_llm",
    "make_transcriber",
]
