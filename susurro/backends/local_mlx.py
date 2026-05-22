"""Local Whisper transcription via Apple's MLX framework.

Runs entirely on-device. No network calls after model weights are cached.
Apple Silicon only.
"""

from __future__ import annotations

import logging
import time

import mlx_whisper
import numpy as np

from .. import config

logger = logging.getLogger(__name__)


class MLXTranscriber:
    """Thin wrapper around `mlx_whisper.transcribe` with eager warmup."""

    name = "local"

    def __init__(self, model_repo: str | None = None, language: str | None = None) -> None:
        self.model_repo = model_repo or config.LOCAL_STT_MODEL
        self.language = language if language is not None else config.LANGUAGE
        self._warmed = False

    def warmup(self) -> None:
        if self._warmed:
            return
        # 0.5 s of silence is enough to trigger model load + JIT compile.
        silence = np.zeros(config.SAMPLE_RATE // 2, dtype=np.float32)
        mlx_whisper.transcribe(
            silence,
            path_or_hf_repo=self.model_repo,
            language=self.language,
            verbose=None,
        )
        self._warmed = True
        logger.info("local STT ready: %s", self.model_repo)

    def transcribe(self, audio: np.ndarray) -> str:
        if audio.size == 0:
            return ""
        t0 = time.perf_counter()
        result = mlx_whisper.transcribe(
            audio,
            path_or_hf_repo=self.model_repo,
            language=self.language,
            verbose=None,
            temperature=0.0,
            condition_on_previous_text=False,
        )
        elapsed = time.perf_counter() - t0
        text = (result.get("text") or "").strip()
        audio_secs = audio.size / config.SAMPLE_RATE
        rtf = elapsed / audio_secs if audio_secs > 0 else 0
        logger.info("[local-stt] %.1fs audio → %.2fs (%.2fx RTF)", audio_secs, elapsed, rtf)
        return text
