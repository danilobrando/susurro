"""Whisper inference via mlx-whisper — runs entirely on-device."""

from __future__ import annotations

import logging
import time

import mlx_whisper
import numpy as np

from . import config

logger = logging.getLogger(__name__)


class Transcriber:
    """Thin wrapper that warms the model on first use and reuses it after."""

    def __init__(self) -> None:
        self._warmed = False

    def warmup(self) -> None:
        """First call downloads weights and JIT-compiles graphs — do it eagerly."""
        if self._warmed:
            return
        silence = np.zeros(config.SAMPLE_RATE // 2, dtype=np.float32)
        mlx_whisper.transcribe(
            silence,
            path_or_hf_repo=config.MODEL_REPO,
            language=config.LANGUAGE,
            verbose=None,
        )
        self._warmed = True
        logger.info("model ready: %s", config.MODEL_REPO)

    def transcribe(self, audio: np.ndarray) -> str:
        if audio.size == 0:
            return ""
        t0 = time.perf_counter()
        result = mlx_whisper.transcribe(
            audio,
            path_or_hf_repo=config.MODEL_REPO,
            language=config.LANGUAGE,
            verbose=None,
            temperature=0.0,
            condition_on_previous_text=False,
        )
        elapsed = time.perf_counter() - t0
        text = (result.get("text") or "").strip()
        audio_secs = audio.size / config.SAMPLE_RATE
        rtf = elapsed / audio_secs if audio_secs > 0 else 0
        logger.info("%.1fs audio → %.2fs (%.2fx RTF)", audio_secs, elapsed, rtf)
        logger.debug("transcript: %r", text)
        return text
