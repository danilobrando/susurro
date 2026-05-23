"""Runtime config — all secrets come from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Database (Railway provides DATABASE_URL automatically when you add Postgres) ---
    database_url: str = "sqlite:///./susurro.db"

    # --- Public-facing URLs ---
    api_url: str = "http://localhost:8000"  # e.g. https://api.susurro.live
    web_url: str = "http://localhost:8000"  # e.g. https://susurro.live

    # --- Secrets ---
    session_secret: str = "dev-secret-please-set-SUSURRO_SESSION_SECRET-in-prod"

    # --- Email (Resend) ---
    resend_api_key: str = ""
    email_from: str = "Susurro <hi@susurro.live>"

    # --- Billing (Stripe) ---
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id_pro: str = ""  # the $10/mo recurring price

    # --- Inference (Groq) ---
    groq_api_key: str = ""
    groq_stt_model: str = "whisper-large-v3-turbo"
    groq_polish_model: str = "llama-3.3-70b-versatile"

    # --- Quotas (words per calendar month, UTC) ---
    free_word_quota: int = 2_000
    pro_word_quota: int = 100_000
    pro_hard_cap: int = 110_000  # cooldown beyond this

    # --- Plan name shown to users ---
    pro_plan_name: str = "Susurro Pro"
    pro_price_label: str = "$10/month"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
