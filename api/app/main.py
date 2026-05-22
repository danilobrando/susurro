"""FastAPI entry point — wires routers, runs DB init on startup."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import billing, transcribe, web
from .db import init_db
from .settings import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    settings = get_settings()
    logger.info(
        "Susurro API up — web=%s, free_quota=%s, pro_quota=%s",
        settings.web_url,
        settings.free_word_quota,
        settings.pro_word_quota,
    )
    yield


app = FastAPI(
    title="Susurro Pro API",
    description="Auth, billing, and transcription proxy for Susurro Pro.",
    version="0.1.0",
    lifespan=lifespan,
)

# The desktop app can be packaged with any bundle ID; we only need CORS for the
# web pages on susurro.live (same-site) and the eventual Stripe redirect targets.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://susurro.live", "https://www.susurro.live"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(web.router)
app.include_router(transcribe.router)
app.include_router(billing.router)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
