"""Susurro Pro backend — talks to our hosted API at api.susurro.live.

The user signs in once via the menu (`Sign in to Susurro Pro…`), the menu
opens https://api.susurro.live/auth/desktop in the browser, the user gets a
token, pastes it back, and the token gets stored in ~/.susurro/auth.json.

Each transcribe call POSTs the audio to /api/transcribe with the token as a
bearer header. The server runs Whisper + Llama on Groq (our keys), meters
usage, and returns polished text. The desktop app does no polish locally
when this backend is active — the server handles both stages.
"""

from __future__ import annotations

import contextlib
import json
import logging
import time

import numpy as np

from .. import config
from .audio_io import to_wav_bytes
from .base import BackendError, BackendUnavailable

logger = logging.getLogger(__name__)

AUTH_FILE = config.HOME_DIR / "auth.json"


def _load_token() -> str | None:
    try:
        with open(AUTH_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return data.get("token")


def save_token(token: str, email: str | None = None) -> None:
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {"token": token.strip()}
    if email:
        payload["email"] = email
    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    AUTH_FILE.chmod(0o600)


def clear_token() -> None:
    with contextlib.suppress(FileNotFoundError):
        AUTH_FILE.unlink()


def is_signed_in() -> bool:
    return _load_token() is not None


class SusurroProTranscriber:
    """STT + polish in one call to the Susurro Pro backend."""

    name = "susurro_pro"

    def warmup(self) -> None:
        if not _load_token():
            raise BackendUnavailable(
                "Susurro Pro: no auth token. Use the menu → 'Sign in to Susurro Pro…' first."
            )
        logger.info("Susurro Pro ready: %s", config.SUSURRO_PRO_API_URL)

    def transcribe(self, audio: np.ndarray) -> str:
        if audio.size == 0:
            return ""
        token = _load_token()
        if not token:
            raise BackendUnavailable("Susurro Pro: not signed in.")
        wav = to_wav_bytes(audio, config.SAMPLE_RATE)
        t0 = time.perf_counter()
        try:
            import httpx

            with httpx.Client(timeout=45.0) as client:
                response = client.post(
                    f"{config.SUSURRO_PRO_API_URL.rstrip('/')}/api/transcribe",
                    headers={"Authorization": f"Bearer {token}"},
                    files={"audio": ("audio.wav", wav, "audio/wav")},
                    data={
                        "polish": config.POLISH_MODE,
                        "language": config.LANGUAGE or "",
                    },
                )
        except Exception as e:
            logger.exception("Susurro Pro transcribe network error")
            raise BackendError(f"Susurro Pro network: {e}") from e

        if response.status_code == 401:
            clear_token()
            raise BackendUnavailable("Susurro Pro: token revoked. Sign in again.")
        if response.status_code == 402:
            raise BackendError(
                f"Susurro Pro: monthly quota reached. Upgrade at {config.SUSURRO_PRO_WEB_URL}/dashboard"
            )
        if response.status_code >= 400:
            raise BackendError(f"Susurro Pro HTTP {response.status_code}: {response.text[:200]}")

        data = response.json()
        elapsed = time.perf_counter() - t0
        logger.info(
            "[susurro-pro] %d words, %s/%s used, %.2fs round-trip",
            data.get("words", 0),
            data.get("words_used_this_period", "?"),
            data.get("quota", "?"),
            elapsed,
        )
        # The polished text IS the final output. We return it as-is; the Polisher
        # in smart mode would normally also LLM-polish, but the server already did.
        # When the desktop app uses this backend, set POLISH_MODE="off" so we
        # don't double-process.
        return data.get("polished") or data.get("raw") or ""
