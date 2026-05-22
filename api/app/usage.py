"""Usage metering — count words per calendar month per user."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func
from sqlmodel import Session, select

from .models import PlanTier, UsageEvent, User
from .settings import get_settings


def current_period_ym(now: datetime | None = None) -> str:
    now = now or datetime.now(UTC)
    return f"{now.year:04d}-{now.month:02d}"


def words_used_this_period(session: Session, user_id: int) -> int:
    period = current_period_ym()
    total = session.exec(
        select(func.coalesce(func.sum(UsageEvent.words), 0)).where(
            UsageEvent.user_id == user_id,
            UsageEvent.period_ym == period,
        )
    ).one()
    # SQLAlchemy may return a Row or a scalar depending on driver — normalize.
    return int(total[0] if isinstance(total, tuple) else total)


def quota_for(user: User) -> int:
    settings = get_settings()
    return settings.pro_word_quota if user.plan == PlanTier.PRO else settings.free_word_quota


def hard_cap_for(user: User) -> int:
    settings = get_settings()
    return settings.pro_hard_cap if user.plan == PlanTier.PRO else settings.free_word_quota


def record(session: Session, user_id: int, words: int, audio_seconds: float) -> None:
    session.add(
        UsageEvent(
            user_id=user_id,
            words=words,
            audio_seconds=audio_seconds,
            period_ym=current_period_ym(),
        )
    )
    session.commit()
