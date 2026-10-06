# Stripe Subscription Repair

> Historical implementation and test snapshot. Its migration head
> `f3a1b9c8d7e6` was current at the time of that work; the current repository
> has one later head, `20261001_student_verification`. The historical
> migration and test results below are not the current full-suite results.

## Payment flow

```text
Frontend Pricing
  ├─ GET /api/v1/payments/plans
  ├─ Free plan ──> register or dashboard/settings (no checkout)
  └─ Pro / Business
       ├─ Anonymous ──> login?plan=<plan> ──> resume checkout after login
       └─ Authenticated ──> POST /api/v1/payments/create-checkout?plan_type=<plan>
                                  │
                                  ├─ Stripe Checkout Session
                                  │    session metadata: user_id, plan_type
                                  │    subscription metadata: user_id, plan_type
                                  ├─ success_url ──> /payment-success?session_id=...
                                  │                    └─ GET /api/v1/payments/success
                                  │                       read-only status polling;
                                  │                       never activates a plan
                                  └─ cancel_url ──> /payment-cancelled

Stripe-signed event
  └─ POST /api/v1/payments/webhook
       ├─ verify Stripe signature and configured webhook secret
       ├─ claim unique Stripe event ID in stripe_webhook_events
       ├─ validate Stripe customer, subscription, plan, and bound user
       ├─ sync the current Stripe subscription state
       ├─ invoice payment event ──> upsert payment_history by invoice ID
       ├─ append an in-app notification
       ├─ commit event + subscription + history + notification atomically
       └─ send purchase confirmation email after commit for paid checkout

Dashboard Settings
  ├─ GET /api/v1/payments/subscription ──> webhook-confirmed subscription
  ├─ GET /api/v1/payments/history ───────> current user's invoice history
  └─ POST /api/v1/payments/cancel ───────> request Stripe cancellation
                                            └─ subscription state changes only
                                               when Stripe webhook confirms it
```

The success redirect is deliberately informational. The browser cannot activate,
change, or cancel a subscription by presenting a session ID.

## API contract audit

All routes are mounted once under `/api/v1/payments` in the API router. Frontend
requests use the canonical Axios client and its bearer token for authenticated
routes.

| Method | Route | Authentication | Request | Behavior/response |
|---|---|---|---|---|
| `GET` | `/api/v1/payments/plans` | Public | None | Returns the backend catalog for Free, Pro, and Business plans. |
| `POST` | `/api/v1/payments/create-checkout?plan_type=pro` (or `business`) | Bearer | `plan_type` query parameter | Returns `checkout_url` and `session_id`; invalid plan is 400 and missing Stripe configuration is 503. |
| `GET` | `/api/v1/payments/success?session_id=...` | Bearer | Checkout session ID | Confirms session ownership and reports `success`, `pending`, or `failed` based on the webhook-written subscription. Read-only. |
| `POST` | `/api/v1/payments/webhook` | Stripe signature, not user auth | Raw event body and `Stripe-Signature` header | Verifies signature; records supported or ignored event ID once; returns `success` or `duplicate`. |
| `GET` | `/api/v1/payments/subscription` | Bearer | None | Returns the current user's subscription or the default Free plan. |
| `POST` | `/api/v1/payments/cancel` | Bearer | None | Requests `cancel_at_period_end` in Stripe; local state remains unchanged until the webhook. |
| `GET` | `/api/v1/payments/history?limit=20&offset=0` | Bearer | Pagination query parameters | Returns only the current user's payment history; limit is 1–100. |

## Repair changes

- Removed activation, payment-history creation, and notifications from the browser
  success endpoint. It now checks that the session belongs to the signed-in user
  and only reports state already committed from Stripe webhooks.
- Added Stripe webhook signing-secret validation and fail-closed behavior when
  Stripe or webhook configuration is missing. Removed the development-only
  in-memory mock checkout/activation path; it could not provide a signed,
  persistent, authoritative payment event.
- Added `subscription_data.metadata` alongside Checkout Session metadata. The
  webhook checks both owner and plan, binds Stripe customer/subscription IDs to
  that user, and verifies configured price IDs before changing the database.
- Subscription create/update/paused/resumed events retrieve the current
  subscription from Stripe before applying it, avoiding stale event snapshots
  overwriting newer Stripe state. Subscription deletion marks the plan Free and
  status canceled while retaining provider identifiers/history.
- Added persistent event-ID idempotency in
  `stripe_webhook_events`. Event claim, subscription changes, payment history,
  and in-app notifications are committed in one transaction. Failed processing
  rolls back the event claim so Stripe can retry.
- Added `invoice.payment_succeeded` and `invoice.payment_failed` handling.
  `PaymentHistory` is upserted by invoice ID, so a later successful retry updates
  an earlier failed invoice record instead of creating another one.
- Cancellation now requests the change in Stripe and waits for the subscription
  webhook before changing the user's local subscription state.
- Prevented duplicate paid checkout creation for users who already have a
  non-terminal paid subscription. When a user has a prior Free/canceled record,
  the webhook updates that existing row rather than creating a second
  subscription row for the same user.
- Added Alembic revision `f3a1b9c8d7e6` after `42420889e6ec`. It creates only the
  event-idempotency table and index; it does not rewrite or reset existing
  migration history or billing data.
- Wired pricing cards to the backend catalog, aligned displayed plan names,
  prices, and features to that response, resumed paid checkout after login or
  registration, and added loading/error handling for checkout and subscription
  status. Added a cancellation return route and billing/payment history to
  Settings.
- Purchase confirmation email now originates from the paid checkout webhook,
  not from the browser redirect.

## Automated validation

| Check | Result | Notes |
|---|---|---|
| `pytest -q tests\test_payments.py` | PASS — 21 passed | Stripe API responses are mocked; no charges or Stripe network requests are made by the mocked tests. One test uses the installed Stripe SDK to validate a locally generated signature; it also makes no network request. One Starlette TestClient deprecation warning remains. |
| `python -m compileall app alembic tests\test_payments.py` (from `backend`) | PASS | Changed backend, migration, and payment tests compile. |
| `npm run build` (from `frontend`) | PASS | Vite production build succeeds; existing large-chunk advisory remains. |
| `npm run lint` (from `frontend`) | PASS — 0 errors | Three existing React Fast Refresh warnings remain. |
| `python -m alembic heads` (from `backend`) | PASS — one head | Head is `f3a1b9c8d7e6`. |
| `python -m alembic history` (from `backend`) | PASS | New revision resolves to parent `42420889e6ec`; existing history remains intact. |
| `python -m alembic check` | NOT RUN | Requires a reachable database at the current configured URL. |
| `python -m alembic upgrade head` | NOT RUN | Not run against an unverified configured database. The available PostgreSQL service was unreachable at `localhost:5432` (connection refused during test-app startup), so no fresh-PostgreSQL or existing-database migration result is claimed. |

When a disposable PostgreSQL database is available, run from `backend`:

```powershell
python -m alembic upgrade head
python -m alembic check
```

## Not verified against external services

- No Stripe test-mode account or deployed webhook endpoint was configured for
  this work. A real test-mode checkout, delivery/retry behavior from Stripe,
  and production Stripe behavior remain unverified; no production claim is made.
- SMTP delivery is not tested live. Automated payment tests mock Stripe and the
  purchase-confirmation sender.
- No live browser session was used to exercise the complete hosted Checkout
  journey, cancellation return, or dashboard refresh after webhook delivery.
- Before rollout, configure test-mode secret key, webhook signing secret, and
  Pro/Business recurring Price IDs; register `/api/v1/payments/webhook` for
  checkout completion, subscription create/update/delete, invoice payment
  success/failure, and async checkout payment success. Then run test-mode
  checkout/cancel and webhook replay tests against a disposable database.
- The UI catalog currently uses the existing backend catalog amounts ($29 for
  Pro and $99 for Business). Confirm the configured Stripe Price amounts and
  currency match that catalog in Stripe test mode before enabling checkout.
