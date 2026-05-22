"""Data model — kept intentionally small.

User → has one Subscription (free by default) and many UsageEvents.
MagicLink → one-time token sent by email, expires in 15 min.
DesktopToken → long-lived bearer the desktop app sends with each transcribe call.
"""

from __future__ import annotations

import secrets
import string
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


def _random_token(length: int = 48) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class PlanTier(StrEnum):
    FREE = "free"
    PRO = "pro"


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    plan: PlanTier = Field(default=PlanTier.FREE, index=True)
    stripe_customer_id: str | None = Field(default=None, index=True)
    stripe_subscription_id: str | None = Field(default=None, index=True)
    subscription_period_end: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)


class MagicLink(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    token: str = Field(default_factory=lambda: _random_token(40), unique=True, index=True)
    purpose: str = Field(default="signin")  # "signin" | "desktop_pair"
    consumed_at: datetime | None = None
    expires_at: datetime = Field(default_factory=lambda: utcnow() + timedelta(minutes=15))
    created_at: datetime = Field(default_factory=utcnow)

    @property
    def is_valid(self) -> bool:
        return self.consumed_at is None and self.expires_at > utcnow()


class DesktopToken(SQLModel, table=True):
    """Long-lived bearer token the desktop app stores in ~/.susurro/auth.json."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    token: str = Field(default_factory=lambda: _random_token(64), unique=True, index=True)
    label: str = Field(default="Susurro for Mac")
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)


class UsageEvent(SQLModel, table=True):
    """One row per successful transcription. Words = output words after polish."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    words: int
    audio_seconds: float
    period_ym: str = Field(index=True)  # "2026-05" — fast monthly aggregation
    created_at: datetime = Field(default_factory=utcnow)


class WaitlistEntry(SQLModel, table=True):
    """For folks who land on susurro.live before they're ready to sign up."""

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    source: str = Field(default="landing")
    created_at: datetime = Field(default_factory=utcnow)
