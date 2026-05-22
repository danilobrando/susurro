"""Transcription proxy.

Receives audio + bearer token, calls Groq for STT and polish, records usage,
returns polished text. Audio is never persisted — bytes live in memory only
for the duration of the request.

Polish prompt is the same one used by the desktop app (`susurro.polish.prompt`)
so cloud and local users see identical formatting.
"""

from __future__ import annotations

import logging
import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import Session

from .auth import current_user_bearer
from .db import get_session
from .models import User
from .settings import get_settings
from .usage import hard_cap_for, quota_for, record, words_used_this_period

logger = logging.getLogger(__name__)

router = APIRouter()

# Mirrors susurro/polish/prompt.py — keep them in sync.
SYSTEM_PROMPT = """\
Eres un editor de transcripciones de voz dictadas. Tu trabajo es pulir
SOLO la estructura visual sin cambiar las palabras del hablante.

REGLAS:
1. Conservá el idioma del input (no traduzcas nunca).
2. Si detectas un patrón de lista enumerada (ordinales como primero/segundo/
   tercero/cuarto, uno/dos/tres, en primer lugar, first/second/third), formatea
   como lista markdown numerada en secuencia 1, 2, 3, con una línea en blanco
   antes del primer ítem y cada ítem en su propia línea.
3. Quitá muletillas obvias: "eh", "mmm", "este pues", "o sea sí", "you know",
   "um", "uh". Quitá disfluencias y falsos arranques.
4. Aplicá backtrack: si el hablante dice "X, en realidad Y" o "X, digo Y" o
   "X, actually Y" o "X, I mean Y", conservá SOLO Y para esa parte.
5. Quebrá en párrafos cuando el contenido cambia de tema y supera ~3 oraciones.

PROHIBIDO:
- Parafrasear o reemplazar palabras del hablante por sinónimos.
- Traducir.
- Resumir o acortar el contenido.
- Agregar contenido que el hablante no dijo.
- Cambiar el orden de las ideas.
- Devolver explicaciones o comentarios.

OUTPUT: SOLO el texto pulido. Sin comentarios. Sin disclaimers. Sin
"Aquí está la versión pulida:". Solo el texto."""


def _count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def _groq_client():
    settings = get_settings()
    if not settings.groq_api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Susurro Pro is not fully configured — GROQ_API_KEY missing on the server.",
        )
    from openai import OpenAI

    return OpenAI(base_url="https://api.groq.com/openai/v1", api_key=settings.groq_api_key, timeout=30.0)


@router.post("/api/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    language: str | None = Form(default=None),
    polish: str = Form(default="smart"),  # "smart" | "rules" | "off"
    user: User = Depends(current_user_bearer),
    session: Session = Depends(get_session),
):
    settings = get_settings()
    # Quota check first — refuse if user is already over their hard cap.
    used = words_used_this_period(session, user.id)
    hard = hard_cap_for(user)
    if used >= hard:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            {
                "error": "quota_exceeded",
                "plan": user.plan,
                "used": used,
                "quota": quota_for(user),
                "upgrade_url": f"{settings.web_url}/billing/upgrade",
            },
        )

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty audio")

    client = _groq_client()

    # STT
    stt_result = client.audio.transcriptions.create(
        file=("audio.wav", audio_bytes, audio.content_type or "audio/wav"),
        model=settings.groq_stt_model,
        response_format="text",
        language=language,
    )
    raw = stt_result if isinstance(stt_result, str) else getattr(stt_result, "text", str(stt_result))
    raw = (raw or "").strip()

    # Polish
    if polish == "off" or not raw:
        polished = raw
    else:
        completion = client.with_options(timeout=15.0).chat.completions.create(
            model=settings.groq_polish_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": raw},
            ],
            temperature=0.0,
            max_tokens=min(4096, len(raw) * 4),
        )
        polished = (completion.choices[0].message.content or "").strip()

    # Audio duration approximated from byte size — accurate enough for usage display.
    # 16kHz mono 16-bit = 32000 bytes/sec.
    audio_seconds = max(0.0, len(audio_bytes) / 32000.0)
    words = _count_words(polished)
    record(session, user.id, words, audio_seconds)

    return {
        "polished": polished,
        "raw": raw,
        "words": words,
        "words_used_this_period": used + words,
        "quota": quota_for(user),
        "plan": user.plan,
    }
