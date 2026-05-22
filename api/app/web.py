"""User-facing HTML pages: signup, magic link verify, dashboard, desktop pairing, waitlist."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from .auth import (
    consume_magic_link,
    current_user_web,
    get_or_create_user,
    issue_desktop_token,
    issue_session_cookie,
)
from .db import get_session
from .emails import send_magic_link
from .models import MagicLink, User, WaitlistEntry
from .settings import get_settings
from .usage import quota_for, words_used_this_period

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def home(request: Request, user: User | None = Depends(current_user_web)):
    """Tiny landing on the API host. The marketing site lives at susurro.live."""
    return templates.TemplateResponse(
        "home.html", {"request": request, "user": user, "settings": get_settings()}
    )


# --- Magic link sign-in (web) ---


@router.get("/signin", response_class=HTMLResponse)
def signin_page(request: Request):
    return templates.TemplateResponse("signin.html", {"request": request, "purpose": "signin"})


@router.post("/signin")
def signin_submit(
    request: Request,
    email: str = Form(...),
    session: Session = Depends(get_session),
):
    email = email.strip().lower()
    link = MagicLink(email=email, purpose="signin")
    session.add(link)
    session.commit()
    session.refresh(link)
    verify_url = f"{get_settings().api_url}/auth/verify?token={link.token}"
    send_magic_link(email, verify_url, purpose="signin")
    return templates.TemplateResponse("magic_sent.html", {"request": request, "email": email})


@router.get("/auth/verify", response_class=HTMLResponse)
def signin_verify(
    request: Request,
    token: str,
    session: Session = Depends(get_session),
):
    link = consume_magic_link(session, token, purpose="signin")
    if link is None:
        return templates.TemplateResponse("magic_expired.html", {"request": request})
    user = get_or_create_user(session, link.email)
    cookie = issue_session_cookie(user.id)
    resp = RedirectResponse("/dashboard", status_code=303)
    resp.set_cookie(
        "susurro_session",
        cookie,
        max_age=60 * 60 * 24 * 30,
        secure=True,
        httponly=True,
        samesite="lax",
    )
    return resp


# --- Desktop pairing ---


@router.get("/auth/desktop", response_class=HTMLResponse)
def desktop_signin_page(request: Request):
    return templates.TemplateResponse("signin.html", {"request": request, "purpose": "desktop_pair"})


@router.post("/auth/desktop")
def desktop_signin_submit(
    request: Request,
    email: str = Form(...),
    session: Session = Depends(get_session),
):
    email = email.strip().lower()
    link = MagicLink(email=email, purpose="desktop_pair")
    session.add(link)
    session.commit()
    session.refresh(link)
    verify_url = f"{get_settings().api_url}/auth/desktop/verify?token={link.token}"
    send_magic_link(email, verify_url, purpose="desktop_pair")
    return templates.TemplateResponse(
        "magic_sent.html", {"request": request, "email": email, "desktop": True}
    )


@router.get("/auth/desktop/verify", response_class=HTMLResponse)
def desktop_signin_verify(
    request: Request,
    token: str,
    session: Session = Depends(get_session),
):
    link = consume_magic_link(session, token, purpose="desktop_pair")
    if link is None:
        return templates.TemplateResponse("magic_expired.html", {"request": request})
    user = get_or_create_user(session, link.email)
    dt = issue_desktop_token(session, user.id)
    return templates.TemplateResponse(
        "desktop_token.html",
        {"request": request, "user": user, "desktop_token": dt.token, "settings": get_settings()},
    )


# --- Dashboard ---


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    user: User | None = Depends(current_user_web),
    session: Session = Depends(get_session),
):
    if user is None:
        return RedirectResponse("/signin", status_code=303)
    used = words_used_this_period(session, user.id)
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "used": used,
            "quota": quota_for(user),
            "settings": get_settings(),
        },
    )


@router.get("/signout")
def signout():
    resp = RedirectResponse("/", status_code=303)
    resp.delete_cookie("susurro_session")
    return resp


# --- Waitlist (collects emails before the desktop app is in their hands) ---


@router.post("/waitlist")
def waitlist_signup(
    request: Request,
    email: str = Form(...),
    source: str = Form(default="landing"),
    session: Session = Depends(get_session),
):
    email = email.strip().lower()
    existing = session.exec(select(WaitlistEntry).where(WaitlistEntry.email == email)).first()
    if existing is None:
        session.add(WaitlistEntry(email=email, source=source))
        session.commit()
    return templates.TemplateResponse("waitlist_done.html", {"request": request, "email": email})


# --- Billing convenience: signed-in upgrade button → redirect through /billing/checkout ---


@router.get("/billing/upgrade")
def billing_upgrade(
    user: User | None = Depends(current_user_web),
):
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in first")
    return RedirectResponse("/billing/checkout", status_code=303)
