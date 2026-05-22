"""Microphone capture — push-to-talk style recorder."""

from __future__ import annotations

import logging
import threading
from collections import deque

import numpy as np
import sounddevice as sd

from . import config

logger = logging.getLogger(__name__)


class MicrophoneUnavailable(RuntimeError):
    """Raised when the input stream can't be opened — usually a permission issue."""


class Recorder:
    """Start/stop microphone capture and return a float32 numpy array.

    Audio is buffered while `recording` is True. `stop()` returns mono 16kHz
    samples normalized to [-1.0, 1.0], ready to feed into Whisper.
    """

    def __init__(self) -> None:
        self._stream: sd.InputStream | None = None
        self._chunks: deque[np.ndarray] = deque()
        self._lock = threading.Lock()
        self._recording = False
        # Most recent block's RMS, scaled ~0..1 — read by the UI indicator.
        self._current_level = 0.0

    @property
    def is_recording(self) -> bool:
        return self._recording

    def peak_level(self) -> float:
        """Return the most recent mic level (0..1) for UI consumption.

        Updated by the audio callback at PortAudio's block rate (~750 Hz for
        16 kHz mono with default blocksize). Reads are lock-free; the value
        is a plain float and atomic on CPython.
        """
        return self._current_level

    def _callback(self, indata, frames, time, status) -> None:
        if status:
            logger.debug("input stream status: %s", status)
        with self._lock:
            recording = self._recording
            if recording:
                self._chunks.append(indata.copy())
        if recording and indata.size > 0:
            mono = indata.reshape(-1)
            rms = float(np.sqrt(np.mean(mono * mono)))
            # Speech RMS is usually 0.01..0.3 in float32. Scale + clamp for UI.
            self._current_level = min(1.0, rms * 10.0)

    def start(self) -> None:
        if self._recording:
            return
        with self._lock:
            self._chunks.clear()
            self._recording = True
        try:
            self._stream = sd.InputStream(
                samplerate=config.SAMPLE_RATE,
                channels=config.CHANNELS,
                dtype="float32",
                device=config.INPUT_DEVICE,
                callback=self._callback,
                blocksize=0,
            )
            self._stream.start()
        except (sd.PortAudioError, OSError) as e:
            with self._lock:
                self._recording = False
            logger.exception("failed to open input stream")
            raise MicrophoneUnavailable(str(e)) from e

    def stop(self) -> np.ndarray:
        if not self._recording:
            return np.zeros(0, dtype=np.float32)
        with self._lock:
            self._recording = False
            chunks = list(self._chunks)
            self._chunks.clear()
        self._current_level = 0.0
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                logger.exception("error closing input stream")
            self._stream = None
        if not chunks:
            return np.zeros(0, dtype=np.float32)
        audio = np.concatenate(chunks, axis=0).reshape(-1)
        return audio.astype(np.float32)

    def duration_so_far(self) -> float:
        with self._lock:
            total = sum(c.shape[0] for c in self._chunks)
        return total / config.SAMPLE_RATE
