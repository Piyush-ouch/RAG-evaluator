"""
Billing API Endpoints — Stripe Integration
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Request

from app.api.deps import CurrentUser, DbSession, require_role
from app.core.constants import UserRole

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/billing", tags=["Billing"])


@router.get("/")
async def get_billing_info(
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Get current billing information."""
    from sqlalchemy import select
    from app.models.billing import BillingAccount
    stmt = select(BillingAccount).where(BillingAccount.org_id == current_user.org_id)
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()
    if not account:
        return {"plan": "free", "evaluations_used": 0, "evaluation_limit": 100}
    return {
        "plan": account.plan,
        "billing_interval": account.billing_interval,
        "evaluations_used": account.evaluations_used,
        "evaluation_limit": account.evaluation_limit,
        "trial_ends_at": account.trial_ends_at.isoformat() if account.trial_ends_at else None,
        "current_period_end": account.current_period_end.isoformat() if account.current_period_end else None,
    }


@router.post("/checkout", dependencies=[Depends(require_role(UserRole.OWNER))])
async def create_checkout_session(
    plan: str,
    interval: str = "monthly",
    db: DbSession = None,
    current_user: CurrentUser = None,
) -> dict:
    """Create a Stripe Checkout session."""
    import stripe
    from app.config import get_settings

    settings = get_settings()
    stripe.api_key = settings.stripe_secret_key

    price_map = {
        ("pro", "monthly"): settings.stripe_price_pro_monthly,
        ("pro", "annual"): settings.stripe_price_pro_annual,
        ("enterprise", "monthly"): settings.stripe_price_enterprise_monthly,
        ("enterprise", "annual"): settings.stripe_price_enterprise_annual,
    }
    price_id = price_map.get((plan, interval))
    if not price_id:
        return {"error": "Invalid plan or interval."}

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.cors_origins[0]}/settings/billing?success=true",
        cancel_url=f"{settings.cors_origins[0]}/settings/billing?cancelled=true",
        client_reference_id=str(current_user.org_id),
        metadata={"org_id": str(current_user.org_id)},
    )

    return {"checkout_url": session.url}


@router.post("/portal", dependencies=[Depends(require_role(UserRole.OWNER))])
async def create_portal_session(
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Create a Stripe Customer Portal session."""
    import stripe
    from app.config import get_settings
    from sqlalchemy import select
    from app.models.billing import BillingAccount

    settings = get_settings()
    stripe.api_key = settings.stripe_secret_key

    stmt = select(BillingAccount).where(BillingAccount.org_id == current_user.org_id)
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()
    if not account or not account.stripe_customer_id:
        return {"error": "No billing account found."}

    session = stripe.billing_portal.Session.create(
        customer=account.stripe_customer_id,
        return_url=f"{settings.cors_origins[0]}/settings/billing",
    )
    return {"portal_url": session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request) -> dict:
    """Handle Stripe webhook events."""
    import stripe
    from app.config import get_settings

    settings = get_settings()
    stripe.api_key = settings.stripe_secret_key

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except Exception:
        return {"error": "Invalid signature."}

    logger.info("stripe_webhook", event_type=event["type"])

    # Handle events
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        logger.info("checkout_completed", session_id=session["id"])
        # Update billing account with subscription details

    elif event["type"] == "invoice.paid":
        logger.info("invoice_paid")

    elif event["type"] == "customer.subscription.updated":
        logger.info("subscription_updated")

    elif event["type"] == "customer.subscription.deleted":
        logger.info("subscription_cancelled")

    return {"received": True}
