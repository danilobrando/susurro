"""Groq backends — OpenAI-compatible API for Whisper (STT) and Llama (polish).

Groq is currently the cheapest + lowest-latency provider for both Whisper
(`whisper-large-v3-turbo`) and a polish LLM (`llama-3.3-70b-versatile`).
TOS: they explicitly do not store or train on customer data via the API.
"""

from __future__ import annotations

import logging
import time

import numpy as np

from .. import config
from .audio_io import to_wav_bytes
from .base import BackendError
from .credentials import require_key

logger = logging.getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def _client(timeout: float):
    """Lazy import keeps openai out of the import graph for users on local-only setups."""
    from openai import OpenAI

    return OpenAI(
        base_url=GROQ_BASE_URL,
        api_key=require_key("groq"),
        timeout=timeout,
    )


class GroqTranscriber:
    name = "groq"

    def __init__(self, model: str | None = None, language: str | None = None) -> None:
        self.model = model or config.GROQ_STT_MODEL
        self.language = language if language is not None else config.LANGUAGE
        self._client = None

    def warmup(self) -> None:
        # Verifies key is present + reachable. No actual transcription.
        if self._client is None:
            self._client = _client(timeout=30.0)
        logger.info("groq STT ready: %s", self.model)

    def transcribe(self, audio: np.ndarray) -> str:
        if audio.size == 0:
            return ""
        if self._client is None:
            self.warmup()
        wav = to_wav_bytes(audio, config.SAMPLE_RATE)
        t0 = time.perf_counter()
        try:
            result = self._client.audio.transcriptions.create(
                file=("audio.wav", wav, "audio/wav"),
                model=self.model,
                response_format="text",
                language=self.language,
            )
        except Exception as e:
            logger.exception("groq STT failed")
            raise BackendError(f"groq STT: {e}") from e
        elapsed = time.perf_counter() - t0
        audio_secs = audio.size / config.SAMPLE_RATE
        # SDK returns a string when response_format="text", but some SDK versions
        # wrap it; handle both.
        text = result if isinstance(result, str) else getattr(result, "text", str(result))
        text = text.strip()
        logger.info("[groq-stt] %.1fs audio → %.2fs network+inference", audio_secs, elapsed)
        return text


class GroqPolishLLM:
    name = "groq"

    def __init__(self, model: str | None = None) -> None:
        self.model = model or config.GROQ_POLISH_MODEL
        self._client = None

    def warmup(self) -> None:
        if self._client is None:
            self._client = _client(timeout=15.0)
        logger.info("groq polish LLM ready: %s", self.model)

    def polish(self, raw: str, *, system_prompt: str) -> str:
        if not raw:
            return raw
        if self._client is None:
            self.warmup()
        t0 = time.perf_counter()
        try:
            completion = self._client.with_options(timeout=10.0).chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": raw},
                ],
                temperature=0.0,
                max_tokens=min(4096, len(raw) * 4),
            )
        except Exception as e:
            logger.exception("groq polish failed")
            raise BackendError(f"groq polish: {e}") from e
        elapsed = time.perf_counter() - t0
        text = (completion.choices[0].message.content or "").strip()
        logger.info("[groq-polish] %d→%d chars in %.2fs", len(raw), len(text), elapsed)
        return text
