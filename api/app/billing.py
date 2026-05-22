"""Stripe Checkout + webhook for the Susurro Pro $16/mo subscription.

Flow:
    1. Signed-in user clicks "Upgrade" on /dashboard → POST /billing/checkout
       → returns Stripe Checkout URL → redirect.
    2. Stripe finishes payment → calls /billing/webhook with event.
    3. We update User.plan = PRO + stripe_* fields, set subscription_period_end.
    4. Customer Portal at /billing/portal lets the user cancel / change card.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from .auth import require_user_web
from .db import get_session
from .models import PlanTier, User
from .settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


def _stripe():
    settings = get_settings()
    if not settings.stripe_secret_key or not settings.stripe_price_id_pro:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Billing not configured — STRIPE_SECRET_KEY / STRIPE_PRICE_ID_PRO missing.",
        )
    import stripe as stripe_lib

    stripe_lib.api_key = settings.stripe_secret_key
    return stripe_lib


@router.post("/billing/checkout")
def create_checkout(
    user: User = Depends(require_user_web),
    session: Session = Depends(get_session),
):
    stripe = _stripe()
    settings = get_settings()

    # Reuse the existing Stripe customer if we already created one.
    customer_id = user.stripe_customer_id
    if not customer_id:
        customer = stripe.Customer.create(email=user.email, metadata={"user_id": str(user.id)})
        customer_id = customer.id
        user.stripe_customer_id = customer_id
        session.add(user)
        session.commit()

    checkout = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": settings.stripe_price_id_pro, "quantity": 1}],
        success_url=f"{settings.web_url}/dashboard?upgraded=1",
        cancel_url=f"{settings.web_url}/dashboard?upgrade_cancelled=1",
        allow_promotion_codes=True,
    )
    return RedirectResponse(checkout.url, status_code=303)


@router.post("/billing/portal")
def open_portal(
    user: User = Depends(require_user_web),
):
    stripe = _stripe()
    settings = get_settings()
    if not user.stripe_customer_id:
        raise HTTPException(400, "No Stripe customer yet — upgrade first.")
    portal = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=f"{settings.web_url}/dashboard",
    )
    return RedirectResponse(portal.url, status_code=303)


@router.post("/billing/webhook")
async def stripe_webhook(
    request: Request,
    session: Session = Depends(get_session),
):
    stripe = _stripe()
    settings = get_settings()
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except Exception as e:
        logger.warning("invalid stripe signature: %s", e)
        raise HTTPException(400, "Invalid signature") from e

    etype = event["type"]
    obj = event["data"]["object"]
    logger.info("stripe event: %s", etype)

    if etype in (
        "checkout.session.completed",
        "customer.subscription.created",
        "customer.subscription.updated",
    ):
        customer_id = obj.get("customer")
        subscription_id = obj.get("subscription") or obj.get("id")
        period_end_ts = obj.get("current_period_end")
        status_str = obj.get("status", "active")
        if customer_id and subscription_id:
            user = session.exec(select(User).where(User.stripe_customer_id == customer_id)).first()
            if user:
                user.stripe_subscription_id = subscription_id
                if status_str in ("active", "trialing"):
                    user.plan = PlanTier.PRO
                else:
                    user.plan = PlanTier.FREE
                if period_end_ts:
                    user.subscription_period_end = datetime.fromtimestamp(period_end_ts, tz=UTC)
                session.add(user)
                session.commit()

    elif etype in ("customer.subscription.deleted",):
        customer_id = obj.get("customer")
        if customer_id:
            user = session.exec(select(User).where(User.stripe_customer_id == customer_id)).first()
            if user:
                user.plan = PlanTier.FREE
                user.stripe_subscription_id = None
                session.add(user)
                session.commit()

    return {"received": True}
