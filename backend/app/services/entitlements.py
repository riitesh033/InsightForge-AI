from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.dataset import Dataset
from app.models.subscription import Subscription
from app.models.student_verification import (
    StudentVerificationApplication,
    StudentVerificationStatus,
)
from app.models.user import User
from app.services.payment import payment_service

PAID_STATUSES = {"active", "trialing"}


def _utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def get_active_subscription(db: Session, user_id: int) -> Subscription | None:
    """Return the currently effective paid subscription deterministically."""
    now = _utcnow_naive()
    return (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user_id,
            Subscription.plan != "free",
            Subscription.status.in_(PAID_STATUSES),
            (Subscription.current_period_end.is_(None))
            | (Subscription.current_period_end > now),
        )
        .order_by(
            Subscription.current_period_end.desc().nullslast(),
            Subscription.id.desc(),
        )
        .first()
    )



def _value(value: Any) -> str:
    return str(getattr(value, "value", value))


def resolve_plan(db: Session, user_id: int) -> tuple[str, dict[str, Any]]:
    subscription = get_active_subscription(db, user_id)
    plan_key = "free"
    if subscription is not None:
        candidate = _value(subscription.plan)
        if candidate in payment_service.plans and candidate != "free":
            plan_key = candidate

    if plan_key == "free":
        now = _utcnow_naive()
        student_access = (
            db.query(StudentVerificationApplication)
            .filter(
                StudentVerificationApplication.user_id == user_id,
                StudentVerificationApplication.status
                == StudentVerificationStatus.APPROVED,
                StudentVerificationApplication.student_entitlement_expires_at
                > now,
            )
            .order_by(
                StudentVerificationApplication.student_entitlement_expires_at.desc()
            )
            .first()
        )
        if student_access is not None:
            plan_key = "pro"

    return plan_key, payment_service.get_plan_features(plan_key)


def _required_plan(feature: str) -> str | None:
    for plan_key in payment_service.plans:
        plan = payment_service.get_plan_features(plan_key)
        if plan["feature_access"].get(feature, False):
            return plan_key
    return None


def require_feature(db: Session, user_id: int, feature: str) -> None:
    plan_key, plan = resolve_plan(db, user_id)
    if plan["feature_access"].get(feature, False):
        return

    required_plan = _required_plan(feature)
    detail: dict[str, Any] = {
        "code": "PLAN_FEATURE_REQUIRED",
        "feature": feature,
        "plan": plan_key,
        "required_plan": required_plan,
        "message": (
            f"This feature is not available on the {plan['name']} plan. "
            f"Upgrade to {required_plan.title()} to use it."
            if required_plan
            else "This feature is not available on your plan."
        ),
    }
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _limit_error(
    *,
    code: str,
    message: str,
    plan_key: str,
    limit: int,
    usage: int,
    required_plan: str | None,
    limit_name: str,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": code,
            "message": message,
            "plan": plan_key,
            "limit": limit,
            "usage": usage,
            "limit_name": limit_name,
            "required_plan": required_plan,
        },
    )


def _first_plan_meeting_limit(limit_name: str, requested: int) -> str | None:
    for plan_key in payment_service.plans:
        plan_limit = payment_service.get_plan_features(plan_key)["limits"][
            limit_name
        ]
        if plan_limit == -1 or plan_limit >= requested:
            return plan_key
    return None


def enforce_dataset_count(db: Session, owner_id: int) -> None:
    plan_key, plan = resolve_plan(db, owner_id)
    limit = int(plan["limits"]["max_datasets"])
    if limit == -1:
        return

    usage = db.query(func.count(Dataset.id)).filter(
        Dataset.owner_id == owner_id
    ).scalar() or 0
    if usage >= limit:
        required_plan = _first_plan_meeting_limit("max_datasets", usage + 1)
        raise _limit_error(
            code="PLAN_LIMIT_REACHED",
            message=(
                f"The {plan['name']} plan allows up to {limit} datasets. "
                + (
                    f"Upgrade to {required_plan.title()} to upload more."
                    if required_plan
                    else "Delete a dataset to upload another."
                )
            ),
            plan_key=plan_key,
            limit=limit,
            usage=usage,
            required_plan=required_plan,
            limit_name="max_datasets",
        )


def enforce_upload_size(db: Session, owner_id: int, file_size: int) -> None:
    plan_key, plan = resolve_plan(db, owner_id)
    limit_mb = int(plan["limits"]["max_file_size_mb"])
    limit_bytes = limit_mb * 1024 * 1024
    if file_size <= limit_bytes:
        return

    requested_mb = (file_size + 1024 * 1024 - 1) // (1024 * 1024)
    required_plan = _first_plan_meeting_limit(
        "max_file_size_mb", int(requested_mb)
    )
    if required_plan is None:
        max_supported_mb = max(
            int(item["limits"]["max_file_size_mb"])
            for item in payment_service.plans.values()
        )
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"The maximum supported upload size is {max_supported_mb} MB.",
        )

    raise _limit_error(
        code="PLAN_LIMIT_REACHED",
        message=(
            f"The {plan['name']} plan allows files up to {limit_mb} MB. "
            f"Upgrade to {required_plan.title()} for larger uploads."
        ),
        plan_key=plan_key,
        limit=limit_mb,
        usage=int(requested_mb),
        required_plan=required_plan,
        limit_name="max_file_size_mb",
    )


def ai_query_usage(db: Session, user_id: int, now: datetime | None = None) -> int:
    current = now or _utcnow_naive()
    month_start = current.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    return (
        db.query(func.count(ChatMessage.id))
        .join(ChatSession, ChatSession.id == ChatMessage.session_id)
        .filter(
            ChatSession.user_id == user_id,
            ChatMessage.role == "user",
            ChatMessage.created_at >= month_start,
        )
        .scalar()
        or 0
    )


def enforce_ai_query_limit(db: Session, user_id: int) -> None:
    plan_key, plan = resolve_plan(db, user_id)
    limit = int(plan["limits"]["ai_queries_per_month"])
    if limit == -1:
        return

    usage = ai_query_usage(db, user_id)
    if usage >= limit:
        required_plan = _first_plan_meeting_limit(
            "ai_queries_per_month", usage + 1
        )
        raise _limit_error(
            code="AI_QUERY_LIMIT_REACHED",
            message=(
                f"The {plan['name']} plan includes {limit} AI queries per month. "
                + (
                    f"Upgrade to {required_plan.title()} to continue."
                    if required_plan
                    else "Try again next month."
                )
            ),
            plan_key=plan_key,
            limit=limit,
            usage=usage,
            required_plan=required_plan,
            limit_name="ai_queries_per_month",
        )


def lock_user_for_quota(db: Session, user_id: int) -> None:
    user = db.query(User).filter(User.id == user_id).with_for_update().first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )


def get_usage(db: Session, user_id: int) -> dict[str, int]:
    return {
        "datasets": db.query(func.count(Dataset.id))
        .filter(Dataset.owner_id == user_id)
        .scalar()
        or 0,
        "ai_queries_this_month": ai_query_usage(db, user_id),
    }
