import secrets
from datetime import datetime
from typing import Optional

from fastapi import HTTPException

from app.core.config import settings


class PaymentService:
    """Payment service for handling subscriptions and payments."""

    def __init__(self):
        self.stripe_secret_key = settings.STRIPE_SECRET_KEY
        self.stripe_webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        self.stripe_price_id_pro = settings.STRIPE_PRICE_ID_PRO
        self.stripe_price_id_business = settings.STRIPE_PRICE_ID_BUSINESS
        self.frontend_url = settings.FRONTEND_URL

        self.is_configured = bool(self.stripe_secret_key)

        # Development-only mock checkout sessions:
        # session_id -> {"user_id": int, "plan_type": str}
        # Stored server-side so a URL parameter alone can NEVER activate
        # a subscription, and each mock session can be used exactly once.
        self._mock_sessions: dict = {}

        self.plans = {
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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_stripe_client(self):
        """Get Stripe client instance."""
        if not self.is_configured:
            return None

        try:
            import stripe
            stripe.api_key = self.stripe_secret_key
            return stripe
        except ImportError:
            print("Stripe package not installed. Install with: pip install stripe")
            return None

    @staticmethod
    def _stripe_error_class(stripe_module):
        """Return the StripeError class across stripe SDK versions."""
        # stripe >= 8: stripe.StripeError
        # stripe < 8:  stripe.error.StripeError
        err_cls = getattr(stripe_module, "StripeError", None)
        if err_cls is not None:
            return err_cls
        return stripe_module.error.StripeError

    def _get_db(self):
        from app.db.database import get_db
        db = next(get_db())
        return db

    # ------------------------------------------------------------------
    # Checkout
    # ------------------------------------------------------------------

    async def create_checkout_session(
        self,
        user_id: int,
        user_email: str,
        plan_type: str,
    ) -> dict:
        """Create a Stripe checkout session for subscription."""
        if plan_type not in ["pro", "business"]:
            raise HTTPException(status_code=400, detail="Invalid plan type")

        if not self.is_configured:
            # Mock checkout is ONLY available in development.
            if not settings.is_development:
                raise HTTPException(
                    status_code=503,
                    detail="Payment processing is not available.",
                )

            session_id = "mock_session_" + secrets.token_urlsafe(16)
            self._mock_sessions[session_id] = {
                "user_id": user_id,
                "plan_type": plan_type,
            }
            checkout_url = (
                f"{self.frontend_url}/payment-success"
                f"?session_id={session_id}"
            )
            return {
                "checkout_url": checkout_url,
                "session_id": session_id,
                "is_mock": True,
            }

        stripe = self._get_stripe_client()
        if not stripe:
            raise HTTPException(
                status_code=503,
                detail="Payment service temporarily unavailable",
            )

        price_id = (
            self.stripe_price_id_pro
            if plan_type == "pro"
            else self.stripe_price_id_business
        )

        if not price_id:
            raise HTTPException(
                status_code=500,
                detail="Plan configuration error",
            )

        try:
            session = stripe.checkout.Session.create(
                customer_email=user_email,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=f"{self.frontend_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{self.frontend_url}/pricing?canceled=true",
                metadata={
                    "user_id": str(user_id),
                    "plan_type": plan_type,
                },
            )

            return {
                "checkout_url": session.url,
                "session_id": session.id,
                "is_mock": False,
            }
        except self._stripe_error_class(stripe) as e:
            raise HTTPException(
                status_code=500,
                detail="Failed to create checkout session.",
            )
        except Exception:
            raise HTTPException(
                status_code=500,
                detail="Failed to create checkout session.",
            )

    # ------------------------------------------------------------------
    # Verification / activation
    # ------------------------------------------------------------------

    async def verify_and_activate_subscription(
        self,
        session_id: str,
        expected_user_id: Optional[int] = None,
    ) -> dict:
        """
        Verify payment and activate subscription.

        expected_user_id: when provided (and not None), the session must
        belong to this user. Prevents activating subscriptions with
        another user's session id.
        """
        if not self.is_configured:
            # --- Development-only mock path ---
            if settings.is_production:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid payment session.",
                )

            mock_data = self._mock_sessions.pop(session_id, None)
            if mock_data is None:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid or already-used payment session.",
                )

            if expected_user_id is not None and mock_data["user_id"] != expected_user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Payment session does not belong to this user.",
                )

            user_id = mock_data["user_id"]
            plan_type = mock_data["plan_type"]

            from app.models.subscription import (
                PlanType,
                Subscription,
                SubscriptionStatus,
            )

            db = self._get_db()
            try:
                existing_sub = db.query(Subscription).filter(
                    Subscription.user_id == user_id
                ).first()

                plan_enum = getattr(PlanType, plan_type.upper())

                if existing_sub:
                    existing_sub.plan = plan_enum
                    existing_sub.status = SubscriptionStatus.ACTIVE
                    existing_sub.started_at = datetime.utcnow()
                    db.commit()
                    db.refresh(existing_sub)
                else:
                    new_sub = Subscription(
                        user_id=user_id,
                        plan=plan_enum,
                        status=SubscriptionStatus.ACTIVE,
                        started_at=datetime.utcnow(),
                    )
                    db.add(new_sub)
                    db.commit()
                    db.refresh(new_sub)

                return {
                    "success": True,
                    "plan": plan_type,
                    "status": "active",
                    "is_mock": True,
                }
            finally:
                db.close()

        # --- Real Stripe path ---
        stripe = self._get_stripe_client()
        if not stripe:
            raise HTTPException(
                status_code=503,
                detail="Payment service temporarily unavailable",
            )

        try:
            session = stripe.checkout.Session.retrieve(session_id)

            if session.payment_status != "paid":
                raise HTTPException(
                    status_code=400,
                    detail="Payment not completed",
                )

            user_id = int(session.metadata.get("user_id", 0))
            plan_type = session.metadata.get("plan_type", "pro")

            if expected_user_id is not None and user_id != expected_user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Payment session does not belong to this user.",
                )

            from app.models.subscription import (
                PlanType,
                Subscription,
                SubscriptionStatus,
            )

            db = self._get_db()
            try:
                existing_sub = db.query(Subscription).filter(
                    Subscription.user_id == user_id
                ).first()

                plan_enum = getattr(PlanType, plan_type.upper())

                if existing_sub:
                    existing_sub.plan = plan_enum
                    existing_sub.status = SubscriptionStatus.ACTIVE
                    existing_sub.provider_subscription_id = session.subscription
                    existing_sub.started_at = datetime.utcnow()
                    if getattr(session, "current_period_start", None):
                        existing_sub.current_period_start = datetime.fromtimestamp(
                            session.current_period_start
                        )
                    if getattr(session, "current_period_end", None):
                        existing_sub.current_period_end = datetime.fromtimestamp(
                            session.current_period_end
                        )
                    db.commit()
                    db.refresh(existing_sub)
                else:
                    new_sub = Subscription(
                        user_id=user_id,
                        plan=plan_enum,
                        status=SubscriptionStatus.ACTIVE,
                        provider_subscription_id=session.subscription,
                        started_at=datetime.utcnow(),
                    )
                    db.add(new_sub)
                    db.commit()
                    db.refresh(new_sub)

                return {
                    "success": True,
                    "plan": plan_type,
                    "status": "active",
                    "is_mock": False,
                }
            finally:
                db.close()

        except HTTPException:
            raise
        except self._stripe_error_class(stripe) as e:
            raise HTTPException(
                status_code=400,
                detail="Payment verification failed.",
            )

    # ------------------------------------------------------------------
    # Webhook
    # ------------------------------------------------------------------

    async def handle_webhook(
        self,
        payload: bytes,
        sig_header: str,
    ) -> dict:
        """Handle Stripe webhook events."""
        if not self.is_configured:
            return {"status": "ignored", "reason": "Stripe not configured"}

        stripe = self._get_stripe_client()
        if not stripe:
            raise HTTPException(
                status_code=503,
                detail="Payment service temporarily unavailable",
            )

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.stripe_webhook_secret
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid webhook payload")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

        event_type = event["type"]

        if event_type == "checkout.session.completed":
            session = event["data"]["object"]
            await self.verify_and_activate_subscription(session["id"])

        elif event_type == "customer.subscription.updated":
            subscription_data = event["data"]["object"]
            await self._update_subscription_from_stripe(subscription_data)

        elif event_type == "customer.subscription.deleted":
            subscription_data = event["data"]["object"]
            await self._cancel_subscription_from_stripe(subscription_data)

        return {"status": "success", "event_type": event_type}

    async def _update_subscription_from_stripe(self, stripe_subscription: dict):
        """Update subscription from Stripe data."""
        from app.models.subscription import Subscription, SubscriptionStatus

        db = self._get_db()
        try:
            sub = db.query(Subscription).filter(
                Subscription.provider_subscription_id == stripe_subscription["id"]
            ).first()

            if sub:
                sub.status = SubscriptionStatus(stripe_subscription["status"])
                sub.cancel_at_period_end = stripe_subscription.get(
                    "cancel_at_period_end", False
                )
                if stripe_subscription.get("canceled_at"):
                    sub.canceled_at = datetime.fromtimestamp(
                        stripe_subscription["canceled_at"]
                    )
                db.commit()
        finally:
            db.close()

    async def _cancel_subscription_from_stripe(self, stripe_subscription: dict):
        """Cancel subscription from Stripe data."""
        from app.models.subscription import Subscription, SubscriptionStatus

        db = self._get_db()
        try:
            sub = db.query(Subscription).filter(
                Subscription.provider_subscription_id == stripe_subscription["id"]
            ).first()

            if sub:
                sub.status = SubscriptionStatus.CANCELED
                sub.canceled_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Plans
    # ------------------------------------------------------------------

    def get_plan_features(self, plan_type: str) -> dict:
        """Get plan details and features."""
        if plan_type not in self.plans:
            raise HTTPException(status_code=400, detail="Invalid plan type")
        return self.plans[plan_type]

    def get_all_plans(self) -> list[dict]:
        """Get all available plans."""
        return [
            {**plan_info, "plan_key": key}
            for key, plan_info in self.plans.items()
        ]

    # ------------------------------------------------------------------
    # Payment history
    # ------------------------------------------------------------------

    async def record_payment(
        self,
        user_id: int,
        subscription_id: Optional[int],
        amount: float,
        currency: str,
        payment_status: str,
        plan_type: str,
        provider_payment_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> int:
        """Record payment history."""
        from app.models.subscription import PaymentHistory

        db = self._get_db()
        try:
            payment = PaymentHistory(
                user_id=user_id,
                subscription_id=subscription_id,
                amount=amount,
                currency=currency,
                payment_status=payment_status,
                plan_type=plan_type,
                provider_payment_id=provider_payment_id,
                description=description,
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)
            return payment.id
        finally:
            db.close()


# Global instance
payment_service = PaymentService()