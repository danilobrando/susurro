"""Convert in-memory float32 audio to WAV bytes for cloud upload."""

from __future__ import annotations

import io
import wave

import numpy as np


def to_wav_bytes(audio: np.ndarray, sample_rate: int = 16_000) -> bytes:
    """Encode mono float32 audio in [-1, 1] as a 16-bit PCM WAV byte string."""
    if audio.ndim != 1:
        audio = audio.reshape(-1)
    audio_i16 = np.clip(audio * 32767.0, -32768, 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_i16.tobytes())
    return buf.getvalue()
