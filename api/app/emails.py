"""Resend wrapper for transactional email.

When RESEND_API_KEY is unset (dev mode) we just print the message — useful for
testing the magic-link flow without hooking up DNS + Resend domain verification.
"""

from __future__ import annotations

import logging

from .settings import get_settings

logger = logging.getLogger(__name__)


def send_magic_link(email: str, link: str, *, purpose: str) -> None:
    settings = get_settings()
    subject = "Sign in to Susurro" if purpose == "signin" else "Connect your Mac to Susurro Pro"
    html = _magic_link_html(link, purpose=purpose)
    text = f"{subject}\n\nClick this link to continue:\n{link}\n\nIt expires in 15 minutes."

    if not settings.resend_api_key:
        logger.warning("[dev] no RESEND_API_KEY — printing magic link instead of sending:\n%s", link)
        return

    import resend

    resend.api_key = settings.resend_api_key
    resend.Emails.send(
        {
            "from": settings.email_from,
            "to": [email],
            "subject": subject,
            "html": html,
            "text": text,
        }
    )


def _magic_link_html(link: str, *, purpose: str) -> str:
    heading = "Sign in to Susurro" if purpose == "signin" else "Connect your Mac"
    body = (
        "Click the button below to sign in to Susurro Pro. The link expires in 15 minutes."
        if purpose == "signin"
        else "Click the button below to pair this email with the Susurro app on your Mac. The link expires in 15 minutes."
    )
    return f"""<!doctype html>
<html><body style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 540px; margin: 0 auto; padding: 32px 24px; background: #fafafa; color: #111;">
  <h2 style="margin: 0 0 16px;">{heading}</h2>
  <p style="color: #555; line-height: 1.5; margin: 0 0 24px;">{body}</p>
  <p style="margin: 0 0 32px;">
    <a href="{link}" style="display: inline-block; background: #111; color: #fff; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 500;">Continue</a>
  </p>
  <p style="color: #999; font-size: 13px; margin: 0;">If the button doesn't work, paste this URL into your browser:</p>
  <p style="color: #555; font-size: 13px; word-break: break-all; margin: 4px 0 0;">{link}</p>
  <hr style="border: none; border-top: 1px solid #e5e5e5; margin: 32px 0;" />
  <p style="color: #999; font-size: 12px; margin: 0;">If you didn't request this, just ignore the email.<br/>Susurro · susurro.live</p>
</body></html>"""
