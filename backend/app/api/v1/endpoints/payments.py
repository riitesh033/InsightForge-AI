import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.subscription import Subscription, PlanType, SubscriptionStatus, PaymentHistory
from app.models.user import User
from app.crud.deps import get_current_user
from app.services.payment import payment_service
from app.services.email import email_service
from app.api.v1.endpoints.notifications import create_notification
from app.models.notification import NotificationType

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/plans")
def get_plans():
    """Get all available subscription plans."""
    return {"plans": payment_service.get_all_plans()}


@router.post("/create-checkout")
async def create_checkout(
    plan_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a checkout session for subscription purchase."""
    if plan_type not in ["pro", "business"]:
        raise HTTPException(status_code=400, detail="Invalid plan type")

    checkout_result = await payment_service.create_checkout_session(
        user_id=current_user.id,
        user_email=current_user.email,
        plan_type=plan_type,
    )

    return {
        "checkout_url": checkout_result["checkout_url"],
        "session_id": checkout_result["session_id"],
    }


@router.get("/success")
async def payment_success(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Handle successful payment redirect."""
    try:
        result = await payment_service.verify_and_activate_subscription(session_id)

        if result["success"]:
            # Record payment history
            plan_info = payment_service.get_plan_features(result["plan"])
            
            payment_id = await payment_service.record_payment(
                user_id=current_user.id,
                subscription_id=None,  # Will be linked later
                amount=plan_info["price"],
                currency=plan_info["currency"],
                payment_status="completed",
                plan_type=result["plan"],
                provider_payment_id=session_id if not result.get("is_mock") else None,
                description=f"{result['plan'].capitalize()} plan subscription",
            )

            # Send confirmation email
            await email_service.send_purchase_confirmation(
                to_email=current_user.email,
                user_name=current_user.full_name,
                plan_type=result["plan"],
                amount=plan_info["price"],
                currency=plan_info["currency"],
                transaction_id=session_id,
                purchase_date=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                features=plan_info["features"],
            )

            # Create in-app notification
            create_notification(
                db=db,
                user_id=current_user.id,
                title="Subscription Activated!",
                message=f"Your {result['plan'].capitalize()} plan is now active. Enjoy all premium features!",
                notification_type=NotificationType.SUCCESS,
                action_url="/dashboard",
            )

            return {
                "success": True,
                "plan": result["plan"],
                "message": "Subscription activated successfully",
            }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Payment verification failed: {str(e)}",
        )

    raise HTTPException(status_code=400, detail="Invalid session")


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing signature header")

    try:
        result = await payment_service.handle_webhook(payload, sig_header)
        return JSONResponse(content=result)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")


@router.get("/subscription")
def get_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's subscription details."""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    if not subscription:
        # Return free plan info
        free_plan = payment_service.get_plan_features("free")
        return {
            "plan": "free",
            "status": "active",
            "features": free_plan["features"],
            "limits": free_plan["limits"],
            "current_period_end": None,
            "cancel_at_period_end": False,
        }

    plan_info = payment_service.get_plan_features(subscription.plan.value)

    return {
        "plan": subscription.plan.value,
        "status": subscription.status.value,
        "features": plan_info["features"],
        "limits": plan_info["limits"],
        "current_period_start": subscription.current_period_start.isoformat() if subscription.current_period_start else None,
        "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        "cancel_at_period_end": subscription.cancel_at_period_end,
        "started_at": subscription.started_at.isoformat() if subscription.started_at else None,
    }


@router.post("/cancel")
def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel subscription at period end."""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    if not subscription or subscription.plan == PlanType.FREE:
        raise HTTPException(
            status_code=400,
            detail="No active subscription to cancel",
        )

    # If using Stripe, cancel via Stripe
    if subscription.provider_subscription_id and payment_service.is_configured:
        stripe = payment_service._get_stripe_client()
        if stripe:
            try:
                stripe.Subscription.modify(
                    subscription.provider_subscription_id,
                    cancel_at_period_end=True,
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to cancel subscription: {str(e)}",
                )

    subscription.cancel_at_period_end = True
    subscription.canceled_at = datetime.utcnow()
    db.commit()

    # Create notification
    create_notification(
        db=db,
        user_id=current_user.id,
        title="Subscription Canceled",
        message=f"Your {subscription.plan.value.capitalize()} subscription will end on {subscription.current_period_end}. You'll retain access until then.",
        notification_type=NotificationType.WARNING,
    )

    return {
        "success": True,
        "message": "Subscription will be canceled at the end of the billing period",
        "end_date": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
    }


@router.get("/history")
def get_payment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    """Get payment history for the current user."""
    payments = db.query(PaymentHistory).filter(
        PaymentHistory.user_id == current_user.id
    ).order_by(PaymentHistory.created_at.desc()).offset(offset).limit(limit).all()

    total = db.query(PaymentHistory).filter(
        PaymentHistory.user_id == current_user.id
    ).count()

    return {
        "payments": [
            {
                "id": p.id,
                "amount": p.amount,
                "currency": p.currency,
                "status": p.payment_status,
                "plan_type": p.plan_type,
                "created_at": p.created_at.isoformat(),
                "description": p.description,
            }
            for p in payments
        ],
        "total": total,
    }
