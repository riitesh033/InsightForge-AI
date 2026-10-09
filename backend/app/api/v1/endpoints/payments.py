import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.models.subscription import (
    PaymentHistory,
    PlanType,
    Subscription,
    SubscriptionStatus,
)
from app.services.entitlements import get_active_subscription, get_usage, resolve_plan
from app.models.user import User
from app.models.subscription import Invoice
from app.services.payment import payment_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/invoices/{invoice_id}")
def download_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id,
    ).first()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    return Response(
        content=invoice.pdf_data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{invoice.invoice_number}.pdf"'
            )
        },
    )


@router.get("/plans")
def get_plans() -> dict[str, list[dict[str, Any]]]:
    return {"plans": payment_service.get_all_plans()}


@router.post("/create-checkout")
async def create_checkout(
    plan_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if plan_type not in {"pro", "business"}:
        raise HTTPException(status_code=400, detail="Invalid plan type")

    current_subscription = get_active_subscription(db, current_user.id)
    if (
        current_subscription is not None
        and current_subscription.plan != PlanType.FREE
        and current_subscription.status not in {
            SubscriptionStatus.CANCELED,
            SubscriptionStatus.INCOMPLETE_EXPIRED,
        }
    ):
        raise HTTPException(
            status_code=409,
            detail="An active subscription already exists.",
        )

    return await payment_service.create_checkout_session(
        user_id=current_user.id,
        user_email=current_user.email,
        plan_type=plan_type,
    )


@router.get("/success")
async def payment_success(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Report webhook-confirmed state; this redirect endpoint never activates plans."""
    return await payment_service.get_checkout_status(
        session_id=session_id,
        expected_user_id=current_user.id,
        db=db,
    )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> JSONResponse:
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature header")

    result = await payment_service.handle_webhook(payload, signature, db)
    return JSONResponse(content=result)


@router.get("/subscription")
def get_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    subscription = get_active_subscription(db, current_user.id)
    if subscription is None:
        subscription = (
            db.query(Subscription)
            .filter(Subscription.user_id == current_user.id)
            .order_by(Subscription.id.desc())
            .first()
        )
    plan_key, plan_info = resolve_plan(db, current_user.id)

    if subscription is None:
        return {
            "plan": plan_key,
            "status": SubscriptionStatus.ACTIVE.value,
            "features": plan_info["features"],
            "feature_access": plan_info["feature_access"],
            "limits": plan_info["limits"],
            "usage": get_usage(db, current_user.id),
            "current_period_start": None,
            "current_period_end": None,
            "cancel_at_period_end": False,
            "started_at": None,
        }

    status_value = getattr(subscription.status, "value", subscription.status)
    if (
        status_value in {"active", "trialing"}
        and subscription.current_period_end is not None
        and subscription.current_period_end <= datetime.now(UTC).replace(tzinfo=None)
        and plan_key == PlanType.FREE.value
    ):
        status_value = "expired"
    return {
        "plan": plan_key,
        "status": status_value,
        "features": plan_info["features"],
        "feature_access": plan_info["feature_access"],
        "limits": plan_info["limits"],
        "usage": get_usage(db, current_user.id),
        "current_period_start": (
            subscription.current_period_start.isoformat()
            if subscription.current_period_start
            else None
        ),
        "current_period_end": (
            subscription.current_period_end.isoformat()
            if subscription.current_period_end
            else None
        ),
        "cancel_at_period_end": subscription.cancel_at_period_end,
        "started_at": (
            subscription.started_at.isoformat()
            if subscription.started_at
            else None
        ),
    }


@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    subscription = get_active_subscription(db, current_user.id)
    if subscription is None or subscription.status in {
        SubscriptionStatus.CANCELED,
        SubscriptionStatus.INCOMPLETE_EXPIRED,
    }:
        raise HTTPException(status_code=400, detail="There is no active subscription to cancel")
    if not subscription.provider_subscription_id:
        raise HTTPException(status_code=503, detail="Subscription cancellation is not available.")

    stripe = payment_service._require_stripe()
    stripe_id = subscription.provider_subscription_id
    invoice = None
    amount_minor = 0
    currency = "USD"
    refund_status = "not_available"
    refund_id = None

    try:
        invoices = stripe.Invoice.list(subscription=stripe_id, status="paid", limit=10)
        for item in (payment_service._value(invoices, "data", []) or []):
            paid = int(payment_service._value(item, "amount_paid", 0) or 0)
            if paid > 0 and payment_service._value(item, "payment_intent"):
                invoice = item
                amount_minor = int(paid * 0.70)
                currency = str(payment_service._value(item, "currency", "usd")).upper()
                break
    except Exception as error:
        logger.warning("Paid invoice lookup failed (%s)", type(error).__name__)

    try:
        stripe.Subscription.cancel(stripe_id)
    except Exception as error:
        logger.error("Stripe cancellation failed (%s)", type(error).__name__)
        raise HTTPException(
            status_code=502,
            detail="Stripe could not cancel this subscription. No local changes were made.",
        ) from None

    canceled_at = datetime.now(UTC).replace(tzinfo=None)
    subscription.status = SubscriptionStatus.CANCELED
    subscription.plan = PlanType.FREE
    subscription.cancel_at_period_end = False
    subscription.canceled_at = canceled_at
    subscription.current_period_end = canceled_at
    db.commit()

    if invoice is not None and amount_minor > 0:
        payment_intent = payment_service._identifier(
            payment_service._value(invoice, "payment_intent")
        )
        if payment_intent:
            try:
                refund = stripe.Refund.create(
                    payment_intent=payment_intent,
                    amount=amount_minor,
                    idempotency_key=f"cancel-refund-70-{stripe_id}",
                )
                refund_id = payment_service._identifier(refund)
                refund_status = str(payment_service._value(refund, "status", "pending"))
            except Exception as error:
                logger.error("Stripe refund request failed (%s)", type(error).__name__)
                refund_status = "failed"

    from app.services.email import email_service

    email_refund_status = refund_status
    if refund_status not in {"pending", "succeeded", "requires_action"}:
        email_refund_status = "failed" if invoice is not None else "not_available"
    try:
        await email_service.send_subscription_cancellation_email(
            to_email=current_user.email,
            user_name=current_user.full_name,
            plan_type="paid",
            refund_amount=amount_minor / 100,
            currency=currency,
            refund_status=email_refund_status,
        )
    except Exception as error:
        logger.error("Cancellation email failed (%s)", type(error).__name__)

    refund_requested = refund_status in {"pending", "succeeded", "requires_action"}
    message = (
        f"Subscription canceled. A 70% refund of {currency} {amount_minor / 100:.2f} "
        "has been submitted; your bank may take several business days to post it."
        if refund_requested
        else "Subscription canceled. An automatic 70% refund could not be confirmed; please contact support."
    )
    return {
        "success": True,
        "status": "canceled",
        "message": message,
        "refund_status": refund_status,
        "refund_amount": amount_minor / 100 if refund_requested else 0,
        "refund_currency": currency,
        "refund_id": refund_id,
        "end_date": canceled_at.isoformat(),
    }

@router.get("/history")
def get_payment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    query = db.query(PaymentHistory).filter(
        PaymentHistory.user_id == current_user.id
    )
    payments = query.order_by(
        PaymentHistory.created_at.desc()
    ).offset(offset).limit(limit).all()

    return {
        "payments": [
            {
                "id": payment.id,
                "amount": payment.amount,
                "currency": payment.currency,
                "status": payment.payment_status,
                "plan_type": payment.plan_type,
                "created_at": payment.created_at.isoformat(),
                "description": payment.description,
            }
            for payment in payments
        ],
        "total": query.count(),
    }
