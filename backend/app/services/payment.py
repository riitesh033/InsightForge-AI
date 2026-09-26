import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)


class PaymentService:
    """Stripe checkout and signed-webhook processing."""

    def __init__(self) -> None:
        self.stripe_secret_key = settings.STRIPE_SECRET_KEY
        self.stripe_webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        self.stripe_price_id_pro = settings.STRIPE_PRICE_ID_PRO
        self.stripe_price_id_business = settings.STRIPE_PRICE_ID_BUSINESS
        self.frontend_url = settings.FRONTEND_URL.rstrip("/")
        self.is_configured = bool(self.stripe_secret_key)

        self.plans: dict[str, dict[str, Any]] = {
            "free": {
                "name": "Free",
                "price": 0,
                "currency": "USD",
                "features": [
                    "Basic dataset analysis",
                    "Up to 3 datasets",
                    "Standard reports",
                    "Community support",
                ],
                "limits": {
                    "max_datasets": 3,
                    "max_file_size_mb": 10,
                    "ai_queries_per_month": 10,
                },
            },
            "pro": {
                "name": "Pro",
                "price": 29.0,
                "currency": "USD",
                "features": [
                    "Advanced dataset analysis",
                    "Unlimited datasets",
                    "Professional reports (PDF)",
                    "AI dataset chat",
                    "Priority support",
                    "Data cleaning tools",
                ],
                "limits": {
                    "max_datasets": -1,
                    "max_file_size_mb": 100,
                    "ai_queries_per_month": 500,
                },
            },
            "business": {
                "name": "Business",
                "price": 99.0,
                "currency": "USD",
                "features": [
                    "Everything in Pro",
                    "Team collaboration",
                    "API access",
                    "Custom integrations",
                    "Dedicated support",
                    "Advanced security",
                    "SLA guarantee",
                ],
                "limits": {
                    "max_datasets": -1,
                    "max_file_size_mb": 500,
                    "ai_queries_per_month": -1,
                },
            },
        }

    @staticmethod
    def _value(obj: Any, key: str, default: Any = None) -> Any:
        if obj is None:
            return default
        getter = getattr(obj, "get", None)
        if getter is not None:
            return getter(key, default)
        return getattr(obj, key, default)

    @classmethod
    def _identifier(cls, value: Any) -> str | None:
        if isinstance(value, str):
            return value
        identifier = cls._value(value, "id")
        return identifier if isinstance(identifier, str) else None

    @staticmethod
    def _timestamp(value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value.astimezone(UTC).replace(tzinfo=None) if value.tzinfo else value
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, UTC).replace(tzinfo=None)
        return None

    @staticmethod
    def _stripe_error_class(stripe_module: Any) -> type[BaseException]:
        error_class = getattr(stripe_module, "StripeError", None)
        if error_class is not None:
            return error_class
        return stripe_module.error.StripeError

    def _get_stripe_client(self) -> Any | None:
        if not self.is_configured:
            return None
        try:
            import stripe
        except ImportError:
            logger.warning("Stripe SDK is unavailable")
            return None
        stripe.api_key = self.stripe_secret_key
        return stripe

    def _require_stripe(self, *, webhook: bool = False) -> Any:
        if not self.is_configured or (webhook and not self.stripe_webhook_secret):
            raise HTTPException(
                status_code=503,
                detail="Payment processing is not available.",
            )
        stripe = self._get_stripe_client()
        if stripe is None:
            raise HTTPException(
                status_code=503,
                detail="Payment service temporarily unavailable.",
            )
        return stripe

    async def create_checkout_session(
        self,
        user_id: int,
        user_email: str,
        plan_type: str,
    ) -> dict[str, str]:
        if plan_type not in {"pro", "business"}:
            raise HTTPException(status_code=400, detail="Invalid plan type")

        stripe = self._require_stripe(webhook=True)
        price_id = (
            self.stripe_price_id_pro
            if plan_type == "pro"
            else self.stripe_price_id_business
        )
        if not price_id:
            raise HTTPException(
                status_code=503,
                detail="The selected payment plan is not configured.",
            )

        metadata = {"user_id": str(user_id), "plan_type": plan_type}
        try:
            session = stripe.checkout.Session.create(
                customer_email=user_email,
                payment_method_types=["card"],
                line_items=[{"price": price_id, "quantity": 1}],
                mode="subscription",
                success_url=(
                    f"{self.frontend_url}/payment-success"
                    "?session_id={CHECKOUT_SESSION_ID}"
                ),
                cancel_url=f"{self.frontend_url}/payment-cancelled",
                metadata=metadata,
                subscription_data={"metadata": metadata},
            )
        except self._stripe_error_class(stripe) as error:
            logger.error("Stripe checkout creation failed (%s)", type(error).__name__)
            raise HTTPException(
                status_code=502,
                detail="Failed to create checkout session.",
            ) from None
        except Exception as error:
            logger.error("Checkout creation failed (%s)", type(error).__name__)
            raise HTTPException(
                status_code=502,
                detail="Failed to create checkout session.",
            ) from None

        checkout_url = self._value(session, "url")
        session_id = self._value(session, "id")
        if not isinstance(checkout_url, str) or not isinstance(session_id, str):
            logger.error("Stripe returned an incomplete checkout session")
            raise HTTPException(
                status_code=502,
                detail="Failed to create checkout session.",
            )
        return {"checkout_url": checkout_url, "session_id": session_id}

    async def get_checkout_status(
        self,
        session_id: str,
        expected_user_id: int,
        db: Session,
    ) -> dict[str, Any]:
        stripe = self._require_stripe(webhook=True)
        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except self._stripe_error_class(stripe) as error:
            logger.info("Checkout status lookup failed (%s)", type(error).__name__)
            raise HTTPException(
                status_code=404,
                detail="Payment session not found.",
            ) from None

        metadata = self._value(session, "metadata", {})
        try:
            session_user_id = int(self._value(metadata, "user_id", ""))
        except (TypeError, ValueError):
            session_user_id = None
        if session_user_id != expected_user_id:
            raise HTTPException(status_code=404, detail="Payment session not found.")

        if self._value(session, "status") == "expired":
            return {"status": "failed", "success": False}

        subscription_id = self._identifier(self._value(session, "subscription"))
        if subscription_id is None:
            return {"status": "pending", "success": False}

        from app.models.subscription import Subscription, SubscriptionStatus

        subscription = db.query(Subscription).filter(
            Subscription.user_id == expected_user_id,
            Subscription.provider_subscription_id == subscription_id,
        ).first()
        if (
            subscription is not None
            and subscription.status in {
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIALING,
            }
        ):
            return {
                "status": "success",
                "success": True,
                "plan": subscription.plan.value,
                "message": "Subscription confirmed.",
            }

        return {"status": "pending", "success": False}

    async def handle_webhook(
        self,
        payload: bytes,
        sig_header: str,
        db: Session,
    ) -> dict[str, Any]:
        stripe = self._require_stripe(webhook=True)
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                self.stripe_webhook_secret,
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid webhook payload") from None
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid webhook signature") from None

        event_id = self._value(event, "id")
        event_type = self._value(event, "type")
        if not isinstance(event_id, str) or not isinstance(event_type, str):
            raise HTTPException(status_code=400, detail="Invalid webhook event")

        from app.models.subscription import StripeWebhookEvent

        existing_event = db.get(StripeWebhookEvent, event_id)
        if existing_event is not None:
            return {"status": "duplicate", "event_type": event_type}

        try:
            db.add(StripeWebhookEvent(event_id=event_id, event_type=event_type))
            db.flush()
            event_data = self._value(self._value(event, "data"), "object")
            confirmation = await self._process_event(
                event_type,
                event_data,
                db,
                stripe,
            )
            db.commit()
            if confirmation is not None:
                await self._send_purchase_confirmation(confirmation)
        except IntegrityError:
            db.rollback()
            if db.get(StripeWebhookEvent, event_id) is not None:
                return {"status": "duplicate", "event_type": event_type}
            logger.exception("Stripe webhook event could not be persisted")
            raise HTTPException(
                status_code=500,
                detail="Webhook processing failed.",
            ) from None
        except HTTPException:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            logger.exception("Stripe webhook processing failed")
            raise HTTPException(
                status_code=500,
                detail="Webhook processing failed.",
            ) from None

        return {"status": "success", "event_type": event_type}

    async def _process_event(
        self,
        event_type: str,
        data: Any,
        db: Session,
        stripe: Any,
    ) -> dict[str, Any] | None:
        if event_type in {
            "checkout.session.completed",
            "checkout.session.async_payment_succeeded",
        }:
            return await self._handle_checkout_completed(data, db, stripe)
        elif event_type in {
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.paused",
            "customer.subscription.resumed",
        }:
            subscription_id = self._identifier(self._value(data, "id"))
            if subscription_id is None:
                raise HTTPException(status_code=400, detail="Invalid Stripe subscription.")
            canonical_subscription = await self._retrieve_subscription(
                stripe,
                subscription_id,
                self._identifier(self._value(data, "customer")),
            )
            self._apply_subscription(canonical_subscription, db)
        elif event_type == "customer.subscription.deleted":
            self._apply_subscription(data, db, deleted=True)
        elif event_type in {"invoice.payment_succeeded", "invoice.payment_failed"}:
            await self._handle_invoice(data, event_type, db, stripe)
        return None

    async def _handle_checkout_completed(
        self,
        session: Any,
        db: Session,
        stripe: Any,
    ) -> dict[str, Any] | None:
        if self._value(session, "mode") != "subscription":
            raise HTTPException(status_code=400, detail="Invalid checkout session.")
        if self._value(session, "payment_status") not in {"paid", "no_payment_required"}:
            return None

        metadata = self._value(session, "metadata", {})
        try:
            user_id = int(self._value(metadata, "user_id", ""))
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid checkout owner.") from None
        plan_type = self._value(metadata, "plan_type")
        subscription_id = self._identifier(self._value(session, "subscription"))
        customer_id = self._identifier(self._value(session, "customer"))
        if (
            plan_type not in {"pro", "business"}
            or subscription_id is None
            or customer_id is None
        ):
            raise HTTPException(status_code=400, detail="Invalid checkout session.")

        stripe_subscription = await self._retrieve_subscription(
            stripe,
            subscription_id,
            customer_id,
        )

        subscription_metadata = self._value(stripe_subscription, "metadata", {})
        if (
            self._value(subscription_metadata, "user_id") != str(user_id)
            or self._value(subscription_metadata, "plan_type") != plan_type
        ):
            raise HTTPException(status_code=400, detail="Invalid checkout ownership.")

        self._apply_subscription(
            stripe_subscription,
            db,
            expected_user_id=user_id,
            expected_customer_id=customer_id,
            expected_plan=plan_type,
        )
        if self._value(session, "payment_status") != "paid":
            return None

        from app.models.subscription import Subscription, SubscriptionStatus
        from app.models.user import User

        stored_subscription = db.query(Subscription).filter_by(
            provider_subscription_id=subscription_id
        ).one()
        if stored_subscription.status not in {
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING,
        }:
            return None
        user = db.get(User, user_id)
        if user is None:
            return None
        return {
            "email": user.email,
            "name": user.full_name,
            "plan": plan_type,
            "session_id": self._value(session, "id"),
        }

    async def _retrieve_subscription(
        self,
        stripe: Any,
        subscription_id: str,
        expected_customer_id: str | None = None,
    ) -> Any:
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
        except Exception as error:
            logger.error("Stripe subscription lookup failed (%s)", type(error).__name__)
            raise HTTPException(
                status_code=503,
                detail="Unable to confirm the subscription with Stripe.",
            ) from None

        if self._identifier(self._value(subscription, "id")) != subscription_id:
            raise HTTPException(status_code=400, detail="Invalid Stripe subscription.")
        customer_id = self._identifier(self._value(subscription, "customer"))
        if expected_customer_id is not None and customer_id != expected_customer_id:
            raise HTTPException(status_code=400, detail="Subscription customer mismatch.")
        return subscription

    async def _send_purchase_confirmation(
        self,
        confirmation: dict[str, Any],
    ) -> None:
        from app.services.email import email_service

        plan = self.get_plan_features(confirmation["plan"])
        try:
            await email_service.send_purchase_confirmation(
                to_email=confirmation["email"],
                user_name=confirmation["name"],
                plan_type=confirmation["plan"],
                amount=plan["price"],
                currency=plan["currency"],
                transaction_id=confirmation["session_id"],
                purchase_date=datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
                features=plan["features"],
            )
        except Exception as error:
            logger.error(
                "Purchase confirmation email failed (%s)",
                type(error).__name__,
            )

    def _apply_subscription(
        self,
        stripe_subscription: Any,
        db: Session,
        *,
        expected_user_id: int | None = None,
        expected_customer_id: str | None = None,
        expected_plan: str | None = None,
        deleted: bool = False,
    ) -> None:
        from app.models.notification import Notification, NotificationType
        from app.models.subscription import (
            PlanType,
            Subscription,
            SubscriptionStatus,
        )
        from app.models.user import User

        subscription_id = self._identifier(self._value(stripe_subscription, "id"))
        customer_id = self._identifier(self._value(stripe_subscription, "customer"))
        metadata = self._value(stripe_subscription, "metadata", {})
        raw_user_id = self._value(metadata, "user_id")
        raw_plan = self._value(metadata, "plan_type")
        try:
            user_id = int(raw_user_id)
        except (TypeError, ValueError):
            user_id = None

        if (
            subscription_id is None
            or customer_id is None
            or user_id is None
            or raw_plan not in {"pro", "business"}
        ):
            raise HTTPException(status_code=400, detail="Invalid Stripe subscription.")
        if expected_user_id is not None and user_id != expected_user_id:
            raise HTTPException(status_code=400, detail="Subscription owner mismatch.")
        if expected_customer_id is not None and customer_id != expected_customer_id:
            raise HTTPException(status_code=400, detail="Subscription customer mismatch.")
        if expected_plan is not None and raw_plan != expected_plan:
            raise HTTPException(status_code=400, detail="Subscription plan mismatch.")

        price_id = self._subscription_price_id(stripe_subscription)
        configured_plans = {
            self.stripe_price_id_pro: "pro",
            self.stripe_price_id_business: "business",
        }
        if price_id is None or configured_plans.get(price_id) != raw_plan:
            raise HTTPException(status_code=400, detail="Subscription plan mismatch.")

        user = db.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=400, detail="Subscription user not found.")

        subscription = db.query(Subscription).filter(
            Subscription.provider_subscription_id == subscription_id
        ).first()
        user_subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).first()
        if subscription is None and user_subscription is not None:
            if (
                user_subscription.provider_subscription_id is not None
                and user_subscription.provider_subscription_id != subscription_id
                and user_subscription.plan != PlanType.FREE
                and user_subscription.status not in {
                    SubscriptionStatus.CANCELED,
                    SubscriptionStatus.INCOMPLETE_EXPIRED,
                }
            ):
                if expected_user_id is not None:
                    raise HTTPException(
                        status_code=409,
                        detail="An active subscription already exists.",
                    )
                return
            subscription = user_subscription
        if subscription is not None and (
            subscription.user_id != user_id
            or (
                subscription.provider_customer_id is not None
                and subscription.provider_customer_id != customer_id
            )
        ):
            raise HTTPException(status_code=400, detail="Subscription owner mismatch.")
        customer_owner = db.query(Subscription).filter(
            Subscription.provider_customer_id == customer_id,
            Subscription.user_id != user_id,
        ).first()
        if customer_owner is not None:
            raise HTTPException(status_code=400, detail="Subscription customer mismatch.")

        if subscription is None:
            subscription = Subscription(
                user_id=user_id,
                provider_subscription_id=subscription_id,
                provider_customer_id=customer_id,
                plan=PlanType(raw_plan),
                status=SubscriptionStatus.INCOMPLETE,
                started_at=self._timestamp(self._value(stripe_subscription, "start_date")),
            )
            db.add(subscription)

        raw_status = "canceled" if deleted else self._value(stripe_subscription, "status")
        try:
            status_value = SubscriptionStatus(raw_status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Unsupported subscription status.") from None

        plan_value = (
            PlanType.FREE
            if deleted or raw_status in {"canceled", "incomplete_expired"}
            else PlanType(raw_plan)
        )
        was_new = subscription.id is None
        changed = (
            was_new
            or subscription.plan != plan_value
            or subscription.status != status_value
            or subscription.cancel_at_period_end
            != bool(self._value(stripe_subscription, "cancel_at_period_end", False))
        )
        subscription.plan = plan_value
        subscription.status = status_value
        subscription.provider_subscription_id = subscription_id
        subscription.provider_customer_id = customer_id
        subscription.cancel_at_period_end = (
            False if deleted else bool(self._value(stripe_subscription, "cancel_at_period_end", False))
        )
        subscription.canceled_at = self._timestamp(
            self._value(stripe_subscription, "canceled_at")
        )
        subscription.current_period_start = self._subscription_period(
            stripe_subscription, "current_period_start"
        )
        subscription.current_period_end = self._subscription_period(
            stripe_subscription, "current_period_end"
        )
        if subscription.started_at is None:
            subscription.started_at = self._timestamp(
                self._value(stripe_subscription, "start_date")
            ) or datetime.now(UTC).replace(tzinfo=None)

        if changed:
            db.add(
                Notification(
                    user_id=user_id,
                    title="Subscription updated",
                    message=(
                        "Your subscription has ended."
                        if deleted
                        else f"Your {plan_value.value.capitalize()} subscription is {status_value.value}."
                    ),
                    notification_type=(
                        NotificationType.WARNING
                        if deleted or status_value in {
                            SubscriptionStatus.CANCELED,
                            SubscriptionStatus.PAST_DUE,
                            SubscriptionStatus.UNPAID,
                        }
                        else NotificationType.SUCCESS
                    ),
                    action_url="/dashboard/settings",
                )
            )
        db.flush()

    def _subscription_price_id(self, stripe_subscription: Any) -> str | None:
        items = self._value(self._value(stripe_subscription, "items"), "data", [])
        if not items:
            return None
        price = self._value(items[0], "price")
        return self._identifier(price)

    def _subscription_period(self, stripe_subscription: Any, field: str) -> datetime | None:
        value = self._value(stripe_subscription, field)
        if value is None:
            items = self._value(self._value(stripe_subscription, "items"), "data", [])
            if items:
                value = self._value(items[0], field)
        return self._timestamp(value)

    async def _handle_invoice(
        self,
        invoice: Any,
        event_type: str,
        db: Session,
        stripe: Any,
    ) -> None:
        from app.models.notification import Notification, NotificationType
        from app.models.subscription import PaymentHistory, Subscription

        invoice_id = self._identifier(self._value(invoice, "id"))
        subscription_id = self._invoice_subscription_id(invoice)
        if invoice_id is None or subscription_id is None:
            raise HTTPException(status_code=400, detail="Invalid Stripe invoice.")

        stripe_subscription = await self._retrieve_subscription(
            stripe,
            subscription_id,
            self._identifier(self._value(invoice, "customer")),
        )
        self._apply_subscription(stripe_subscription, db)
        subscription = db.query(Subscription).filter(
            Subscription.provider_subscription_id == subscription_id
        ).first()
        if subscription is None:
            raise HTTPException(status_code=400, detail="Invoice subscription not found.")

        invoice_customer = self._identifier(self._value(invoice, "customer"))
        if (
            invoice_customer is not None
            and subscription.provider_customer_id != invoice_customer
        ):
            raise HTTPException(status_code=400, detail="Invoice customer mismatch.")

        succeeded = event_type == "invoice.payment_succeeded"
        raw_amount = self._value(invoice, "amount_paid" if succeeded else "amount_due", 0)
        currency = str(self._value(invoice, "currency", "usd")).upper()
        amount = self._major_amount(int(raw_amount or 0), currency)
        payment = db.query(PaymentHistory).filter(
            PaymentHistory.provider_payment_id == invoice_id
        ).first()
        if payment is not None and payment.user_id != subscription.user_id:
            raise HTTPException(status_code=400, detail="Invoice owner mismatch.")
        if payment is None:
            payment = PaymentHistory(
                user_id=subscription.user_id,
                subscription_id=subscription.id,
                provider_payment_id=invoice_id,
                payment_provider="stripe",
                plan_type=subscription.plan.value,
                amount=amount,
                currency=currency,
                payment_status="completed" if succeeded else "failed",
                description=self._value(invoice, "description"),
            )
            db.add(payment)
        else:
            payment.subscription_id = subscription.id
            payment.amount = amount
            payment.currency = currency
            payment.payment_status = "completed" if succeeded else "failed"
            payment.plan_type = subscription.plan.value

        db.add(
            Notification(
                user_id=subscription.user_id,
                title="Payment received" if succeeded else "Payment failed",
                message=(
                    "Your subscription payment was received."
                    if succeeded
                    else "Your subscription payment could not be processed."
                ),
                notification_type=(
                    NotificationType.SUCCESS if succeeded else NotificationType.ERROR
                ),
                action_url="/dashboard/settings",
            )
        )

    def _invoice_subscription_id(self, invoice: Any) -> str | None:
        direct = self._identifier(self._value(invoice, "subscription"))
        if direct is not None:
            return direct
        parent = self._value(invoice, "parent")
        details = self._value(parent, "subscription_details")
        return self._identifier(self._value(details, "subscription"))

    @staticmethod
    def _major_amount(amount_minor: int, currency: str) -> float:
        zero_decimal = {
            "BIF", "CLP", "DJF", "GNF", "ISK", "JPY", "KMF", "KRW",
            "MGA", "PYG", "RWF", "UGX", "VND", "VUV", "XAF", "XOF", "XPF",
        }
        three_decimal = {"BHD", "JOD", "KWD", "OMR", "TND"}
        exponent = 0 if currency in zero_decimal else 3 if currency in three_decimal else 2
        return float(Decimal(amount_minor) / (Decimal(10) ** exponent))

    def get_plan_features(self, plan_type: str) -> dict[str, Any]:
        if plan_type not in self.plans:
            raise HTTPException(status_code=400, detail="Invalid plan type")
        return self.plans[plan_type]

    def get_all_plans(self) -> list[dict[str, Any]]:
        return [
            {**plan_info, "plan_key": key}
            for key, plan_info in self.plans.items()
        ]


payment_service = PaymentService()
