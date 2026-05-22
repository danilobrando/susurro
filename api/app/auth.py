"""Magic-link sign-in + desktop token issuance.

Web flow:
    1. POST /auth/magic  { email }  → creates MagicLink + sends email
    2. GET  /auth/verify?token=...  → consumes link, sets session cookie, redirects to /dashboard

Desktop pairing flow:
    1. Desktop opens browser to /auth/desktop  (user types email)
    2. POST /auth/desktop  { email }            → creates MagicLink with purpose="desktop_pair"
    3. User clicks emailed link → /auth/desktop/verify?token=...
    4. Page shows the generated desktop token; user copy-pastes into the menu bar app
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import Depends, HTTPException, Request, status
from itsdangerous import BadSignature, URLSafeSerializer
from sqlmodel import Session, select

from .db import get_session
from .models import DesktopToken, MagicLink, User
from .settings import get_settings


def _serializer() -> URLSafeSerializer:
    return URLSafeSerializer(get_settings().session_secret, salt="susurro-session")


def issue_session_cookie(user_id: int) -> str:
    return _serializer().dumps({"uid": user_id})


def parse_session_cookie(value: str) -> int | None:
    try:
        data = _serializer().loads(value)
    except BadSignature:
        return None
    if not isinstance(data, dict) or "uid" not in data:
        return None
    return int(data["uid"])


def get_or_create_user(session: Session, email: str) -> User:
    email = email.strip().lower()
    user = session.exec(select(User).where(User.email == email)).first()
    if user:
        return user
    user = User(email=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def consume_magic_link(session: Session, token: str, purpose: str) -> MagicLink | None:
    link = session.exec(select(MagicLink).where(MagicLink.token == token)).first()
    if link is None or link.purpose != purpose or not link.is_valid:
        return None
    link.consumed_at = datetime.now(UTC)
    session.add(link)
    session.commit()
    session.refresh(link)
    return link


def issue_desktop_token(session: Session, user_id: int, label: str = "Susurro for Mac") -> DesktopToken:
    token = DesktopToken(user_id=user_id, label=label)
    session.add(token)
    session.commit()
    session.refresh(token)
    return token


# --- FastAPI dependencies ---


def current_user_web(
    request: Request,
    session: Session = Depends(get_session),
) -> User | None:
    """Read the session cookie (set after magic-link verify). None if not signed in."""
    raw = request.cookies.get("susurro_session")
    if not raw:
        return None
    uid = parse_session_cookie(raw)
    if uid is None:
        return None
    return session.get(User, uid)


def require_user_web(user: User | None = Depends(current_user_web)) -> User:
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")
    return user


def current_user_bearer(
    request: Request,
    session: Session = Depends(get_session),
) -> User:
    """Authenticate a desktop request via `Authorization: Bearer <DesktopToken>`."""
    header = request.headers.get("authorization") or ""
    if not header.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = header.split(" ", 1)[1].strip()
    dt = session.exec(select(DesktopToken).where(DesktopToken.token == token)).first()
    if dt is None or dt.revoked_at is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    user = session.get(User, dt.user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User missing")
    dt.last_used_at = datetime.now(UTC)
    session.add(dt)
    session.commit()
    return user
