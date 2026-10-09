from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import json
from types import SimpleNamespace
import time

import pytest

from app.models.notification import Notification
from app.models.subscription import (
    PaymentHistory,
    PlanType,
    StripeWebhookEvent,
    Subscription,
    SubscriptionStatus,
)
from app.models.user import User
from app.services.payment import payment_service

API = "/api/v1"


def stripe_subscription(
    user_id: int,
    *,
    subscription_id: str = "sub_test",
    customer_id: str = "cus_test",
    plan: str = "pro",
    status: str = "active",
) -> dict:
    now = datetime.now(UTC)
    return {
        "id": subscription_id,
        "customer": customer_id,
        "status": status,
        "metadata": {"user_id": str(user_id), "plan_type": plan},
        "cancel_at_period_end": False,
        "current_period_start": int(now.timestamp()),
        "current_period_end": int((now + timedelta(days=30)).timestamp()),
        "items": {"data": [{"price": {"id": f"price_{plan}"}}]},
    }


def checkout_session(user_id: int, plan: str = "pro") -> dict:
    return {
        "id": "cs_test",
        "mode": "subscription",
        "status": "complete",
        "payment_status": "paid",
        "metadata": {"user_id": str(user_id), "plan_type": plan},
        "customer": "cus_test",
        "subscription": "sub_test",
    }


def install_stripe(
    monkeypatch,
    *,
    event: dict | None = None,
    subscription: dict | None = None,
    checkout: dict | None = None,
    signature_error: Exception | None = None,
    create_result: dict | None = None,
    modified: list | None = None,
    invoices: list | None = None,
    refunds: list | None = None,
) -> SimpleNamespace:
    modified = modified if modified is not None else []
    refunds = refunds if refunds is not None else []
    monkeypatch.setattr(payment_service, "is_configured", True)
    monkeypatch.setattr(payment_service, "stripe_webhook_secret", "whsec_unit_test")
    monkeypatch.setattr(payment_service, "stripe_price_id_pro", "price_pro")
    monkeypatch.setattr(payment_service, "stripe_price_id_business", "price_business")

    def construct_event(payload: bytes, signature: str, secret: str):
        assert payload == b"unit-test-payload"
        assert secret == "whsec_unit_test"
        if signature_error:
            raise signature_error
        if signature != "t=1,v1=valid":
            raise RuntimeError("bad signature")
        return event

    def retrieve_checkout(session_id: str):
        assert session_id == "cs_test"
        return checkout

    def create_checkout(**kwargs):
        if create_result is not None:
            return create_result
        return {"id": "cs_test", "url": "https://checkout.stripe.com/c/pay/cs_test"}

    def modify_subscription(subscription_id: str, **kwargs):
        modified.append((subscription_id, kwargs))
        return {"id": subscription_id, **kwargs}

    def cancel_subscription(subscription_id: str):
        modified.append((subscription_id, {"cancel": True}))
        return {"id": subscription_id, "status": "canceled"}

    def create_refund(**kwargs):
        refunds.append(kwargs)
        return {"id": "re_test", "status": "succeeded"}

    fake = SimpleNamespace(
        StripeError=RuntimeError,
        Webhook=SimpleNamespace(construct_event=construct_event),
        checkout=SimpleNamespace(
            Session=SimpleNamespace(
                create=create_checkout,
                retrieve=retrieve_checkout,
            )
        ),
        Subscription=SimpleNamespace(
            retrieve=lambda subscription_id: subscription,
            modify=modify_subscription,
            cancel=cancel_subscription,
        ),
        Invoice=SimpleNamespace(
            list=lambda **kwargs: {"data": invoices or []},
        ),
        Refund=SimpleNamespace(create=create_refund),
    )
    monkeypatch.setattr(payment_service, "_get_stripe_client", lambda: fake)
    return fake


def event(event_id: str, event_type: str, data: dict) -> dict:
    return {
        "id": event_id,
        "type": event_type,
        "data": {"object": data},
    }


def send_event(client, stripe_event: dict, signature: str = "t=1,v1=valid"):
    return client.post(
        f"{API}/payments/webhook",
        content=b"unit-test-payload",
        headers={"stripe-signature": signature},
    )


def test_plan_catalog_and_default_free_subscription(client, auth_headers):
    plans_response = client.get(f"{API}/payments/plans")
    assert plans_response.status_code == 200
    plans = {
        item["plan_key"]: item
        for item in plans_response.json()["plans"]
    }
    assert set(plans) == {
        "free",
        "pro",
        "business",
    }
    assert [plans[key]["price"] for key in ("free", "pro", "business")] == [
        0,
        29.0,
        99.0,
    ]
    assert plans["free"]["limits"] == {
        "max_datasets": 3,
        "max_file_size_mb": 10,
        "ai_queries_per_month": 10,
    }
    assert plans["pro"]["limits"] == {
        "max_datasets": -1,
        "max_file_size_mb": 100,
        "ai_queries_per_month": 500,
    }
    assert plans["business"]["limits"] == {
        "max_datasets": -1,
        "max_file_size_mb": 500,
        "ai_queries_per_month": -1,
    }
    assert not any(
        "support" in feature.lower()
        or "collaboration" in feature.lower()
        or "integration" in feature.lower()
        or "sla" in feature.lower()
        for plan in plans.values()
        for feature in plan["features"]
    )

    subscription_response = client.get(
        f"{API}/payments/subscription",
        headers=auth_headers,
    )
    assert subscription_response.status_code == 200
    assert subscription_response.json()["plan"] == "free"
    assert subscription_response.json()["status"] == "active"


def test_checkout_uses_query_contract_and_session_metadata(
    client, user_dict, auth_headers, monkeypatch
):
    calls = []
    install_stripe(
        monkeypatch,
        create_result={
            "id": "cs_test",
            "url": "https://checkout.stripe.com/c/pay/cs_test",
        },
    )

    fake = payment_service._get_stripe_client()

    def capture_checkout(**kwargs):
        calls.append(kwargs)
        return {
            "id": "cs_test",
            "url": "https://checkout.stripe.com/c/pay/cs_test",
        }

    fake.checkout.Session.create = capture_checkout
    response = client.post(
        f"{API}/payments/create-checkout?plan_type=pro",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "checkout_url": "https://checkout.stripe.com/c/pay/cs_test",
        "session_id": "cs_test",
    }
    kwargs = calls[0]
    assert kwargs["mode"] == "subscription"
    assert kwargs["line_items"] == [{"price": "price_pro", "quantity": 1}]
    assert kwargs["metadata"] == {
        "user_id": str(client.get(f"{API}/users/me", headers=auth_headers).json()["id"]),
        "plan_type": "pro",
    }
    assert kwargs["subscription_data"]["metadata"] == kwargs["metadata"]
    assert kwargs["success_url"].startswith("http://localhost:5173/payment-success?")
    assert kwargs["cancel_url"] == "http://localhost:5173/payment-cancelled"
    assert user_dict["email"] == "alice@example.com"


def test_checkout_rejects_invalid_plan_and_requires_auth(
    client, user_dict, auth_headers
):
    anonymous = client.post(
        f"{API}/payments/create-checkout?plan_type=pro",
    )
    invalid = client.post(
        f"{API}/payments/create-checkout?plan_type=free",
        headers=auth_headers,
    )
    assert anonymous.status_code == 401
    assert invalid.status_code == 400


def test_existing_paid_subscription_prevents_duplicate_checkout(
    client, user_dict, auth_headers, db
):
    user = db.query(User).filter_by(email=user_dict["email"]).one()
    db.add(
        Subscription(
            user_id=user.id,
            plan=PlanType.PRO,
            status=SubscriptionStatus.ACTIVE,
            provider_customer_id="cus_existing",
            provider_subscription_id="sub_existing",
        )
    )
    db.commit()

    response = client.post(
        f"{API}/payments/create-checkout?plan_type=business",
        headers=auth_headers,
    )

    assert response.status_code == 409


def test_checkout_and_webhook_fail_closed_without_stripe_configuration(
    client, auth_headers, monkeypatch
):
    monkeypatch.setattr(payment_service, "is_configured", False)

    checkout_response = client.post(
        f"{API}/payments/create-checkout?plan_type=pro",
        headers=auth_headers,
    )
    webhook_response = client.post(
        f"{API}/payments/webhook",
        content=b"{}",
        headers={"stripe-signature": "not-used"},
    )

    assert checkout_response.status_code == 503
    assert webhook_response.status_code == 503
    assert "secret" not in checkout_response.text.lower()
    assert "secret" not in webhook_response.text.lower()


def test_success_redirect_does_not_activate_subscription(
    client, user_dict, auth_headers, monkeypatch, db
):
    current_user = client.get(f"{API}/users/me", headers=auth_headers).json()
    install_stripe(
        monkeypatch,
        checkout=checkout_session(current_user["id"]),
    )
    response = client.get(
        f"{API}/payments/success?session_id=cs_test",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert db.query(Subscription).count() == 0


def test_success_redirect_is_bound_to_the_session_owner(
    client, auth_headers, monkeypatch
):
    install_stripe(
        monkeypatch,
        checkout=checkout_session(999),
    )
    response = client.get(
        f"{API}/payments/success?session_id=cs_test",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.parametrize(
    ("plan", "expected_plan"),
    [("pro", PlanType.PRO), ("business", PlanType.BUSINESS)],
)
def test_checkout_webhook_activates_bound_subscription_and_deduplicates(
    client, user_dict, db, monkeypatch, plan, expected_plan
):
    from app.services.email import email_service

    sent_confirmation = []

    async def capture_confirmation(**details):
        sent_confirmation.append(details)
        return True

    monkeypatch.setattr(
        email_service,
        "send_purchase_confirmation",
        capture_confirmation,
    )
    user_id = db.query(User).filter_by(email=user_dict["email"]).one().id
    db.add(
        Subscription(
            user_id=user_id,
            plan=PlanType.FREE,
            status=SubscriptionStatus.ACTIVE,
        )
    )
    db.commit()
    checkout = checkout_session(user_id, plan=plan)
    event_data = event(
        f"evt_checkout_{plan}",
        "checkout.session.completed",
        checkout,
    )
    install_stripe(
        monkeypatch,
        event=event_data,
        subscription=stripe_subscription(user_id, plan=plan),
    )
    response = send_event(client, event_data)
    duplicate = send_event(client, event_data)

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert duplicate.status_code == 200
    assert duplicate.json()["status"] == "duplicate"
    stored = db.query(Subscription).one()
    assert stored.user_id == user_id
    assert stored.plan == expected_plan
    assert stored.status == SubscriptionStatus.ACTIVE
    assert stored.provider_customer_id == "cus_test"
    assert db.query(StripeWebhookEvent).count() == 1
    welcome_count = db.query(Notification).filter(
        Notification.title == "Welcome to InsightForge AI"
    ).count()
    assert welcome_count == 1
    assert db.query(Notification).count() == welcome_count + 1
    assert db.query(Notification).filter(
        Notification.title == "Subscription updated"
    ).count() == 1
    assert len(sent_confirmation) == 1


def test_unpaid_checkout_completion_does_not_create_a_subscription(
    client, user_dict, db, monkeypatch
):
    user_id = db.query(User).filter_by(email=user_dict["email"]).one().id
    unpaid_session = checkout_session(user_id)
    unpaid_session["payment_status"] = "unpaid"
    unpaid_event = event(
        "evt_checkout_unpaid",
        "checkout.session.completed",
        unpaid_session,
    )
    install_stripe(monkeypatch, event=unpaid_event)

    response = send_event(client, unpaid_event)

    assert response.status_code == 200
    assert db.query(Subscription).count() == 0
    welcome_count = db.query(Notification).filter(
        Notification.title == "Welcome to InsightForge AI"
    ).count()
    assert welcome_count == 1
    assert db.query(Notification).count() == welcome_count


def test_invalid_signature_is_rejected(client, monkeypatch):
    install_stripe(
        monkeypatch,
        signature_error=RuntimeError("invalid signature"),
    )
    response = send_event(
        client,
        event("evt_invalid", "customer.subscription.updated", {}),
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid webhook signature"


def test_stripe_sdk_verifies_webhook_signature_without_network(
    client, monkeypatch, db
):
    import stripe

    secret = "whsec_local_test_only"
    payload = json.dumps(
        {
            "id": "evt_crypto_signature",
            "object": "event",
            "type": "unhandled.test_event",
            "data": {"object": {}},
        },
        separators=(",", ":"),
    ).encode()
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.{payload.decode()}".encode()
    signature = hmac.new(
        secret.encode(),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    monkeypatch.setattr(payment_service, "is_configured", True)
    monkeypatch.setattr(payment_service, "stripe_webhook_secret", secret)
    monkeypatch.setattr(payment_service, "_get_stripe_client", lambda: stripe)

    valid = client.post(
        f"{API}/payments/webhook",
        content=payload,
        headers={"stripe-signature": f"t={timestamp},v1={signature}"},
    )
    invalid = client.post(
        f"{API}/payments/webhook",
        content=payload + b" ",
        headers={"stripe-signature": f"t={timestamp},v1={signature}"},
    )

    assert valid.status_code == 200
    assert valid.json()["event_type"] == "unhandled.test_event"
    assert invalid.status_code == 400
    assert invalid.json()["detail"] == "Invalid webhook signature"
    assert db.query(StripeWebhookEvent).count() == 1


def test_checkout_webhook_rejects_conflicting_session_and_subscription_owners(
    client, user_dict, db, monkeypatch
):
    other = client.post(
        f"{API}/auth/register",
        json={
            "full_name": "Other Account",
            "email": "other-payment@example.com",
            "password": "OtherPassword123",
        },
    )
    assert other.status_code == 201
    primary_id = db.query(User).filter_by(email=user_dict["email"]).one().id
    checkout = checkout_session(primary_id)
    stripe_sub = stripe_subscription(other.json()["id"])
    event_data = event("evt_wrong_owner", "checkout.session.completed", checkout)
    install_stripe(monkeypatch, event=event_data, subscription=stripe_sub)

    response = send_event(client, event_data)
    assert response.status_code == 400
    assert db.query(Subscription).count() == 0
    assert db.query(StripeWebhookEvent).count() == 0


def test_subscription_update_and_deletion_follow_signed_state(
    client, user_dict, auth_headers, db, monkeypatch
):
    user = client.get(f"{API}/users/me", headers=auth_headers).json()
    db.add(
        Subscription(
            user_id=user["id"],
            plan=PlanType.PRO,
            status=SubscriptionStatus.ACTIVE,
            provider_customer_id="cus_test",
            provider_subscription_id="sub_test",
        )
    )
    db.commit()

    current_state = stripe_subscription(user["id"], status="past_due")
    current_state["cancel_at_period_end"] = True
    stale_event_state = stripe_subscription(user["id"], status="active")
    update_event = event(
        "evt_update",
        "customer.subscription.updated",
        stale_event_state,
    )
    install_stripe(
        monkeypatch,
        event=update_event,
        subscription=current_state,
    )
    response = send_event(client, update_event)

    assert response.status_code == 200
    subscription = db.query(Subscription).one()
    assert subscription.status == SubscriptionStatus.PAST_DUE
    assert subscription.cancel_at_period_end is True

    deleted = stripe_subscription(user["id"], status="canceled")
    delete_event = event("evt_delete", "customer.subscription.deleted", deleted)
    install_stripe(monkeypatch, event=delete_event, subscription=deleted)
    deletion = send_event(client, delete_event)
    assert deletion.status_code == 200
    assert subscription.status == SubscriptionStatus.CANCELED
    assert subscription.plan == PlanType.FREE
    assert subscription.cancel_at_period_end is False


def test_subscription_event_cannot_reassign_an_existing_stripe_subscription(
    client, user_dict, db, monkeypatch
):
    primary = db.query(User).filter_by(email=user_dict["email"]).one()
    other_response = client.post(
        f"{API}/auth/register",
        json={
            "full_name": "Second Account",
            "email": "second-payment@example.com",
            "password": "OtherPassword123",
        },
    )
    assert other_response.status_code == 201
    db.add(
        Subscription(
            user_id=primary.id,
            plan=PlanType.PRO,
            status=SubscriptionStatus.ACTIVE,
            provider_customer_id="cus_test",
            provider_subscription_id="sub_test",
        )
    )
    db.commit()
    wrong_owner_subscription = stripe_subscription(other_response.json()["id"])
    wrong_owner_event = event(
        "evt_reassign",
        "customer.subscription.updated",
        wrong_owner_subscription,
    )
    install_stripe(
        monkeypatch,
        event=wrong_owner_event,
        subscription=wrong_owner_subscription,
    )

    response = send_event(client, wrong_owner_event)
    assert response.status_code == 400
    assert db.query(Subscription).one().user_id == primary.id
    assert db.query(StripeWebhookEvent).count() == 0


@pytest.mark.parametrize(
    ("event_type", "expected_status"),
    [
        ("invoice.payment_failed", "failed"),
        ("invoice.payment_succeeded", "completed"),
    ],
)
def test_invoice_events_create_and_update_payment_history(
    client, user_dict, auth_headers, db, monkeypatch, event_type, expected_status
):
    user = client.get(f"{API}/users/me", headers=auth_headers).json()
    subscription = Subscription(
        user_id=user["id"],
        plan=PlanType.PRO,
        status=SubscriptionStatus.ACTIVE,
        provider_customer_id="cus_test",
        provider_subscription_id="sub_test",
    )
    db.add(subscription)
    db.commit()

    invoice = {
        "id": "in_test",
        "subscription": "sub_test",
        "customer": "cus_test",
        "amount_paid": 0 if expected_status == "failed" else 2900,
        "amount_due": 2900,
        "currency": "usd",
        "description": "Pro monthly subscription",
    }
    invoice_event = event(f"evt_{expected_status}", event_type, invoice)
    current_stripe_state = stripe_subscription(
        user["id"],
        status="past_due" if expected_status == "failed" else "active",
    )
    install_stripe(
        monkeypatch,
        event=invoice_event,
        subscription=current_stripe_state,
    )
    response = send_event(client, invoice_event)

    assert response.status_code == 200
    payment = db.query(PaymentHistory).one()
    assert payment.user_id == user["id"]
    assert payment.subscription_id == subscription.id
    assert payment.payment_status == expected_status
    assert payment.provider_payment_id == "in_test"
    assert payment.amount == 29
    welcome_count = db.query(Notification).filter(
        Notification.title == "Welcome to InsightForge AI"
    ).count()
    payment_notice = "Payment failed" if expected_status == "failed" else "Payment received"
    assert db.query(Notification).filter(
        Notification.title == payment_notice
    ).count() == 1
    assert db.query(Notification).count() == (
        welcome_count + (2 if expected_status == "failed" else 1)
    )
    if expected_status == "failed":
        assert subscription.status == SubscriptionStatus.PAST_DUE


def test_payment_history_is_user_scoped_and_pagination_is_bounded(
    client, auth_headers, user_dict, db
):
    current_user = db.query(User).filter_by(email=user_dict["email"]).one()
    other = client.post(
        f"{API}/auth/register",
        json={
            "full_name": "Other Billing User",
            "email": "other-billing@example.com",
            "password": "OtherPassword123",
        },
    )
    assert other.status_code == 201
    other_user = db.query(User).filter_by(email="other-billing@example.com").one()
    db.add(
        PaymentHistory(
            user_id=current_user.id,
            amount=29,
            currency="USD",
            payment_status="completed",
            plan_type="pro",
            provider_payment_id="in_user",
        )
    )
    db.add(
        PaymentHistory(
            user_id=other_user.id,
            amount=99,
            currency="USD",
            payment_status="completed",
            plan_type="business",
            provider_payment_id="in_other",
        )
    )
    db.commit()

    response = client.get(
        f"{API}/payments/history?limit=1&offset=0",
        headers=auth_headers,
    )
    invalid_limit = client.get(
        f"{API}/payments/history?limit=101",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["payments"]) == 1
    assert invalid_limit.status_code == 422


def test_cancel_subscription_cancels_stripe_and_updates_local_plan_immediately(
    client, auth_headers, user_dict, db, monkeypatch
):
    user = db.query(User).filter_by(email=user_dict["email"]).one()
    subscription = Subscription(
        user_id=user.id,
        plan=PlanType.PRO,
        status=SubscriptionStatus.ACTIVE,
        provider_customer_id="cus_test",
        provider_subscription_id="sub_test",
        cancel_at_period_end=False,
    )
    db.add(subscription)
    db.commit()
    modified = []
    install_stripe(monkeypatch, modified=modified)

    response = client.post(f"{API}/payments/cancel", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "canceled"
    assert modified == [("sub_test", {"cancel": True})]
    assert subscription.status == SubscriptionStatus.CANCELED
    assert subscription.plan == PlanType.FREE
    assert subscription.cancel_at_period_end is False
    assert subscription.canceled_at is not None


def test_cancel_subscription_refunds_70_percent_of_latest_paid_invoice(
    client, auth_headers, user_dict, db, monkeypatch
):
    user = db.query(User).filter_by(email=user_dict["email"]).one()
    subscription = Subscription(
        user_id=user.id,
        plan=PlanType.PRO,
        status=SubscriptionStatus.ACTIVE,
        provider_customer_id="cus_test",
        provider_subscription_id="sub_test",
        cancel_at_period_end=False,
    )
    db.add(subscription)
    db.commit()

    modified = []
    refunds = []
    install_stripe(
        monkeypatch,
        modified=modified,
        invoices=[{
            "id": "in_paid",
            "amount_paid": 2900,
            "currency": "usd",
            "payment_intent": "pi_paid",
        }],
        refunds=refunds,
    )

    response = client.post(f"{API}/payments/cancel", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "canceled"
    assert response.json()["refund_amount"] == 20.3
    assert response.json()["refund_status"] == "succeeded"
    assert modified == [("sub_test", {"cancel": True})]
    assert refunds[0]["payment_intent"] == "pi_paid"
    assert refunds[0]["amount"] == 2030
    assert subscription.status == SubscriptionStatus.CANCELED
    assert subscription.plan == PlanType.FREE


def test_cancel_without_provider_subscription_is_not_reported_as_success(
    client, auth_headers, user_dict, db
):
    user = db.query(User).filter_by(email=user_dict["email"]).one()
    db.add(
        Subscription(
            user_id=user.id,
            plan=PlanType.PRO,
            status=SubscriptionStatus.ACTIVE,
        )
    )
    db.commit()

    response = client.post(f"{API}/payments/cancel", headers=auth_headers)
    assert response.status_code == 503


def test_missing_webhook_signature_is_rejected(client):
    response = client.post(f"{API}/payments/webhook", content=b"{}")
    assert response.status_code == 400
