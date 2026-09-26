import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.crud.deps import get_current_user
from app.db.database import get_db
from app.models.subscription import (
    PaymentHistory,
    PlanType,
    Subscription,
    SubscriptionStatus,
)
from app.models.user import User
from app.services.payment import payment_service

router = APIRouter()
logger = logging.getLogger(__name__)


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

    current_subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()
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
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    if subscription is None:
        free_plan = payment_service.get_plan_features("free")
        return {
            "plan": PlanType.FREE.value,
            "status": SubscriptionStatus.ACTIVE.value,
            "features": free_plan["features"],
            "limits": free_plan["limits"],
            "current_period_start": None,
            "current_period_end": None,
            "cancel_at_period_end": False,
            "started_at": None,
        }

    plan_key = subscription.plan.value
    plan_info = payment_service.get_plan_features(plan_key)
    return {
        "plan": plan_key,
        "status": subscription.status.value,
        "features": plan_info["features"],
        "limits": plan_info["limits"],
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
def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()
    if subscription is None or subscription.plan == PlanType.FREE:
        raise HTTPException(
            status_code=400,
            detail="No active subscription to cancel",
        )
    if subscription.status in {
        SubscriptionStatus.CANCELED,
        SubscriptionStatus.INCOMPLETE_EXPIRED,
    }:
        raise HTTPException(
            status_code=400,
            detail="There is no active subscription to cancel",
        )
    if not subscription.provider_subscription_id:
        raise HTTPException(
            status_code=503,
            detail="Subscription cancellation is not available.",
        )

    stripe = payment_service._require_stripe(webhook=True)
    try:
        stripe.Subscription.modify(
            subscription.provider_subscription_id,
            cancel_at_period_end=True,
        )
    except Exception as error:
        logger.error("Stripe cancellation request failed (%s)", type(error).__name__)
        raise HTTPException(
            status_code=502,
            detail="Failed to request subscription cancellation.",
        ) from None

    return {
        "success": True,
        "status": "pending_webhook",
        "message": (
            "Cancellation requested. Your subscription status will update "
            "when Stripe confirms the change."
        ),
        "end_date": (
            subscription.current_period_end.isoformat()
            if subscription.current_period_end
            else None
        ),
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
