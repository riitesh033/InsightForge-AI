from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.dataset import Dataset
from app.models.subscription import PlanType, Subscription, SubscriptionStatus
from app.models.user import User
from app.services.payment import payment_service

API = "/api/v1"


def get_user(db, user_dict):
    return db.query(User).filter_by(email=user_dict["email"]).one()


def make_dataset(db, user_id, filename="test.csv"):
    dataset = Dataset(
        filename=filename,
        original_filename=filename,
        file_type="csv",
        file_size=16,
        file_path="not-used.csv",
        rows=1,
        columns=1,
        owner_id=user_id,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def test_free_dataset_limit_is_enforced_before_upload(
    client, auth_headers, user_dict, db, monkeypatch, tmp_path
):
    user = get_user(db, user_dict)
    for index in range(3):
        make_dataset(db, user.id, f"existing-{index}.csv")

    monkeypatch.setattr(settings, "DATASET_STORAGE_DIR", str(tmp_path))
    response = client.post(
        f"{API}/datasets/upload",
        headers=auth_headers,
        files={"file": ("new.csv", b"a\n1\n", "text/csv")},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "PLAN_LIMIT_REACHED"
    assert response.json()["detail"]["limit_name"] == "max_datasets"
    assert response.json()["detail"]["required_plan"] == "pro"
    assert list(tmp_path.iterdir()) == []


def test_free_plan_feature_routes_are_server_gated(
    client, auth_headers, user_dict, db, monkeypatch, tmp_path
):
    user = get_user(db, user_dict)
    dataset = make_dataset(db, user.id)

    cleaning = client.post(
        f"{API}/cleaning/{dataset.id}/preview",
        headers=auth_headers,
    )
    report = client.get(
        f"{API}/reports/{dataset.id}/pdf",
        headers=auth_headers,
    )
    analysis_report = client.get(
        f"{API}/analysis/{dataset.id}/report",
        headers=auth_headers,
    )

    for response, feature in (
        (cleaning, "data_cleaning"),
        (report, "professional_reports"),
        (analysis_report, "professional_reports"),
    ):
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "PLAN_FEATURE_REQUIRED"
        assert response.json()["detail"]["feature"] == feature
        assert response.json()["detail"]["required_plan"] == "pro"


def test_only_webhook_active_paid_subscription_grants_plan(db, user_dict):
    user = get_user(db, user_dict)
    subscription = Subscription(
        user_id=user.id,
        plan=PlanType.PRO,
        status=SubscriptionStatus.PAST_DUE,
        current_period_end=datetime.now(UTC).replace(tzinfo=None)
        + timedelta(days=5),
    )
    db.add(subscription)
    db.commit()

    response = payment_service.get_plan_features("pro")
    from app.services.entitlements import resolve_plan

    assert resolve_plan(db, user.id)[0] == "free"

    subscription.status = SubscriptionStatus.ACTIVE
    db.commit()
    assert resolve_plan(db, user.id)[0] == "pro"

    subscription.current_period_end = (
        datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=1)
    )
    db.commit()
    assert resolve_plan(db, user.id)[0] == "free"
    assert response["feature_access"]["data_cleaning"] is True


@pytest.mark.parametrize(
    ("plan", "file_size_mb"),
    [("pro", 100), ("business", 500)],
)
def test_paid_upload_size_limits_follow_catalog(db, user_dict, plan, file_size_mb):
    user = get_user(db, user_dict)
    db.add(
        Subscription(
            user_id=user.id,
            plan=PlanType(plan),
            status=SubscriptionStatus.ACTIVE,
        )
    )
    db.commit()

    from app.services.entitlements import enforce_upload_size

    enforce_upload_size(db, user.id, file_size_mb * 1024 * 1024)
    with pytest.raises(HTTPException) as error:
        enforce_upload_size(db, user.id, (file_size_mb + 1) * 1024 * 1024)
    assert error.value.status_code == (413 if plan == "business" else 403)


def test_chat_limit_counts_monthly_user_messages_and_blocks_next_request(
    client, auth_headers, user_dict, db, monkeypatch, tmp_path
):
    user = get_user(db, user_dict)
    monkeypatch.setattr(settings, "DATASET_STORAGE_DIR", str(tmp_path))
    upload = client.post(
        f"{API}/datasets/upload",
        headers=auth_headers,
        files={"file": ("chat.csv", b"rows\n1\n", "text/csv")},
    )
    assert upload.status_code == 201, upload.text
    monkeypatch.setitem(
        payment_service.plans["free"]["limits"],
        "ai_queries_per_month",
        1,
    )

    async def answer(**_kwargs):
        return "A deterministic answer."

    monkeypatch.setattr(
        "app.api.v1.endpoints.chat.generate_chat_answer",
        answer,
    )
    chat_url = f"{API}/chat/{upload.json()['id']}"
    first = client.post(
        chat_url,
        headers=auth_headers,
        json={"message": "First question"},
    )
    second = client.post(
        chat_url,
        headers=auth_headers,
        json={"message": "Second question"},
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 403
    assert second.json()["detail"]["code"] == "AI_QUERY_LIMIT_REACHED"
    assert second.json()["detail"]["usage"] == 1
    assert (
        db.query(ChatMessage)
        .join(ChatSession, ChatSession.id == ChatMessage.session_id)
        .filter(ChatSession.user_id == user.id, ChatMessage.role == "user")
        .count()
        == 1
    )


def test_subscription_response_returns_effective_plan_and_usage(
    client, auth_headers
):
    response = client.get(f"{API}/payments/subscription", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["plan"] == "free"
    assert body["feature_access"]["professional_reports"] is False
    assert body["usage"] == {"datasets": 0, "ai_queries_this_month": 0}
    assert body["limits"]["max_datasets"] == 3



def test_effective_subscription_ignores_historical_canceled_rows(db, user_dict):
    from app.services.entitlements import resolve_plan

    user = get_user(db, user_dict)
    db.add_all([
        Subscription(
            user_id=user.id,
            plan=PlanType.PRO,
            status=SubscriptionStatus.CANCELED,
            current_period_end=datetime.now(UTC) - timedelta(days=30),
        ),
        Subscription(
            user_id=user.id,
            plan=PlanType.PRO,
            status=SubscriptionStatus.ACTIVE,
            current_period_end=datetime.now(UTC) + timedelta(days=10),
        ),
    ])
    db.commit()

    assert resolve_plan(db, user.id)[0] == "pro"


def test_expired_paid_subscription_does_not_block_checkout_before_stripe_call(
    client, auth_headers, user_dict, db
):
    user = get_user(db, user_dict)
    db.add(
        Subscription(
            user_id=user.id,
            plan=PlanType.PRO,
            status=SubscriptionStatus.ACTIVE,
            current_period_end=datetime.now(UTC) - timedelta(days=1),
            provider_subscription_id="sub_expired",
        )
    )
    db.commit()

    response = client.post(
        f"{API}/payments/create-checkout",
        headers=auth_headers,
        params={"plan_type": "pro"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Payment processing is not available."
