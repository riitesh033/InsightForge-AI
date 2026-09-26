# InsightForge AI — Full System Audit

**Date:** 2026-09-26
**Scope:** Complete repository inspection (backend, frontend, database/migrations, environment, Docker, API contracts). No code was modified in this phase.

Stack summary: React + TypeScript + Vite + Tailwind + React Router + Axios + Recharts (frontend); Python + FastAPI + SQLAlchemy + Pydantic v2 + Alembic + PostgreSQL + Pandas + Stripe + SMTP + Gemini/OpenRouter/Ollama (backend).

---

## 1. Repository Structure Overview

```
/workspace
├── backend/
│   ├── app/
│   │   ├── api/            (api.py aggregator, dependencies.py auth deps)
│   │   ├── api/v1/endpoints/ (admin, analysis, auth, chat, cleaning, dashboard,
│   │   │                       dataset, health, notifications, payments, reports, users)
│   │   ├── core/           (config.py, security.py, logging.py)
│   │   ├── crud/           (crud_user, crud_dataset, crud_analysis, crud_chat,
│   │   │                    crud_dashboard, deps.py, user.py [duplicate], crud_report.py [EMPTY])
│   │   ├── db/             (base.py, base_models.py, database.py, session.py)
│   │   ├── models/         (user, dataset, analysis, chat_session, chat_message,
│   │   │                    subscription [Subscription+PaymentHistory+enums], notification)
│   │   ├── schemas/        (user, dataset, analysis, chat, cleaning, dashboard, report, admin…)
│   │   └── services/       (auth.py [EMPTY], payment, email, chat, ai_provider, cleaning,
│   │                        dataset, profiling, professional_analysis, insight_engine,
│   │                        insights, verified_analysis, report, dashboard, admin_service)
│   ├── alembic/versions/   (13 migration files)
│   ├── requirements/       (base.txt, dev.txt)
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/            (axios.ts, auth.api.ts [EMPTY], dataset.api.ts [EMPTY], analysis.api.ts [EMPTY])
│   │   ├── services/       (api.ts [active axios instance], auth.ts, dataset.ts, analysis.ts,
│   │   │                    chat.ts, dashboard.ts, report.ts)
│   │   ├── lib/            (api.ts duplicate axios instance, axios.ts, toast.ts, utils.ts)
│   │   ├── context/        (AuthContext.tsx, ThemeContext.tsx, AdminRoute.tsx)
│   │   ├── routes/         (AppRouter.tsx, ProtectedRoute.tsx)
│   │   ├── pages/          (Auth: Login/Register/ForgotPassword/ResetPassword;
│   │   │                    Dashboard: DashBoard/Upload/Datasets/Analysis/AIChat/Reports/Settings/AdminDashboard;
│   │   │                    Error: NotFound/Forbidden/ServerError; Landing)
│   │   └── components/     (landing, dashboard, datasets, analysis, common, layouts, ui)
│   ├── .env                (VITE_API_URL=http://localhost:8000/api/v1 — committed)
│   └── package.json
├── docker-compose.yml      (postgres, backend, frontend)
└── docs/project-overview.md
```

No test suite exists anywhere (`pytest` tests absent; only a stray `frontend/src/test.ts`). No `tests/` directory in backend.

---

## 2. Feature-by-Feature Audit

Legend for CURRENT STATUS: ✅ works (by code trace), ⚠️ partial/broken connection, ❌ missing/unreachable.

### 2.1 Authentication

| Item | Frontend | Backend | DB | Status | Bugs / Missing | Required Fix | Test Required |
|---|---|---|---|---|---|---|---|
| Register | `pages/Auth/RegisterPage.tsx` → `services/auth.ts::register` → `POST /auth/register` | `endpoints/auth.py` | `users` | ⚠️ | Endpoint exists & hashes password, but **no login after register**; frontend must then log in separately. Duplicate legacy module `app/crud/user.py` and empty `app/services/auth.py`. | Decide product flow (auto-login or redirect to login); delete dead modules. | pytest register: 201, hash stored, dup email 400 |
| Login | `LoginPage.tsx` → `login()` sends form-urlencoded to `/auth/login` | `OAuth2PasswordRequestForm`, JWT via `create_access_token(subject=email)` | `users` | ✅ | Token subject is email (not id) — acceptable but couples token validity to email uniqueness; email change would invalidate old tokens silently. | Unit test wrong-password 401; store token in localStorage via AuthContext. | login ok/401 |
| Logout | `AuthContext.logout()` clears localStorage only; call to `/auth/logout` is commented out | **No `/auth/logout` endpoint exists** | n/a | ⚠️ | Client-only logout; JWT not invalidated server-side (stateless design acceptable, but the dead import path `"/auth/logout"` string appears in service grep — verify no runtime call to nonexistent route). | Either document as intentional client-only logout or implement token blocklist. | protected route inaccessible after logout |
| Current user | `AuthContext` fetches `/users/me` | `endpoints/users.py GET /me` | `users` | ✅ | Two different `get_current_user` dependencies exist (`api/dependencies.py` checks `is_active`; `crud/deps.py` does NOT check `is_active`) — inconsistent security. Payments/notifications use the weaker one. | Consolidate to one dependency that checks active status. | 401 without token; deactivated user blocked |
| Forgot password | `pages/Auth/ForgotPassword.tsx` | `POST /auth/forgot-password` | `users` | ❌ **CRITICAL** | (a) **Frontend never calls the API** — it fakes success with `await new Promise(setTimeout 1500ms)` ("Simulate API request for demo purposes"). Violates rules 3/4/12. (b) **Backend has unreachable code**: in `auth.py::forgot_password`, when `user is None` the function `return`s inside the `if`, and the token-generation block below is mis-indented *inside* the `if user is None:` branch (comment `# Generate reset token` is indented under the return) → for existing users the token/email code never runs; for unknown emails it is dead code after return. (c) Dev response leaks `reset_token` in body (acceptable only in dev, must be gated strictly). (d) Uses `print()` instead of logger. | Wire frontend to real `forgotPassword()` service; fix indentation/logic so token is generated for existing users; always return generic message; use `email_service.send_password_reset_email`; add logging. | valid/unknown email, invalid/expired/malformed token, single-use behavior |
| Reset password | `ResetPasswordPage.tsx` reads `?token=` → `POST /auth/reset-password` | decode token, update hash | `users` | ⚠️ | Backend logic OK, but tokens are **not single-use** (JWT reset token reusable until 1h expiry — violates Phase 6 "prefer single-use"). Frontend page exists but is unreachable from the fake forgot-password flow. | Implement token store/jti blacklist or DB-stored hashed token with used flag + expiry. | reuse-after-reset rejected |
| Change password | `SettingsPage.tsx` → `changePassword()` → `POST /users/me/change-password` | verifies current, rejects same password | `users` | ✅ | Response returns plain dict; fine. | — | old rejected/new accepted |
| Account deletion | `deleteAccount()` → `DELETE /users/me` | deletes custom avatar file, cascades | `users`,`datasets`,`subscriptions` | ⚠️ | Cascade relies on DB-level ON DELETE CASCADE; SQLite/tests need model cascade too (models do have `cascade="all, delete-orphan"` for datasets/subscription, but **chat_sessions/chat_messages and notifications relationships are not defined on User** — orphan rows may remain/block depending on FKs). | Add relationships + cascade for ChatSession/ChatMessage/Notification/PaymentHistory. | delete removes all owned rows |
| Protected routes | `routes/ProtectedRoute.tsx` | JWT deps | n/a | ✅ | Redirects to /login. | — | unauth access redirected |
| Admin routes | `context/AdminRoute.tsx` exists but **is NOT mounted in AppRouter** | `endpoints/admin.py` guarded by `get_current_admin_user` | n/a | ❌ | `AdminDashboard.tsx` page exists, service calls `/admin/dashboard` & `/admin/system-health`, but there is **no route** `/dashboard/admin` in `AppRouter.tsx` → page unreachable. | Register AdminRoute + admin route; link in sidebar. | non-admin gets 403/redirect |

### 2.2 Profile

| Item | Frontend | Backend | Status | Bugs |
|---|---|---|---|---|
| Update name/email | `updateProfile()` PATCH `/users/me` | exists, dup-email check | ✅ | Email change invalidates outstanding JWTs (subject=email) silently — note as limitation. |
| Upload picture | POST `/users/me/profile-picture` (multipart) | validates ext/size, UUID filename | ✅ | Served via `/users/profile-pictures/{filename}` with `..` guard — OK. Publicly readable (any authenticated/unauthenticated can fetch by UUID filename) — acceptable, note. |
| Remove picture | DELETE `/users/me/profile-picture` | exists (~line 240) | ✅ | |
| Built-in avatars | POST `/users/me/avatar?avatar_id=` | stores `builtin:avatar_XX` | ✅ | Frontend resolves to `/avatars/avatar_XX.svg` (public dir exists). |
| URL construction bug | `TopNavbar.getProfilePictureUrl()` prefixes `VITE_API_BASE_URL || "/api/v1"` + `/api/v1/users/profile-pictures/...` | | ⚠️ | Stored path already contains `/api/v1/...`; prefixing again yields `/api/v1/api/v1/users/...` → broken image. Also env var name mismatch: code uses `VITE_API_BASE_URL`, `.env` defines `VITE_API_URL`. Fix double-prefix and unify env var name. |

### 2.3 Dataset

| Item | Frontend | Backend | DB | Status | Bugs / Notes |
|---|---|---|---|---|---|
| Upload CSV/XLSX/XLS | `UploadDatasetPage` → `uploadDataset()` POST `/datasets/upload` | `services/dataset.upload_dataset` | `datasets`,`analyses` | ⚠️ | Extension whitelist, size cap 20MB (fixed; **plan limits `max_file_size_mb` never enforced**), UUID filenames (path-traversal safe). Analysis runs synchronously at upload. **Plan-based `max_datasets` limit never enforced.** Empty file (0 bytes) → pandas raises → 400 "Unable to read dataset" (OK but message generic). Corrupt files handled. |
| Listing/search/sort/pagination | GET `/datasets?page,page_size,search,sort_by,order` | `crud_dataset.get_datasets` | ✅ | Verify sort_by whitelist against SQL injection (check crud implementation). |
| Get one / rename / delete / download | GET/PATCH/DELETE `/datasets/{id}`, GET `/datasets/{id}/download` | ownership checked via `owner_id=current_user.id` | ✅ | Delete: confirm physical file removed (verify `crud_dataset.delete_dataset`). |
| Re-analysis | **No endpoint** (`POST /analysis/{id}/reanalyze` missing) | | ❌ | Phase 2 lists "Re-analysis"; feature absent. |

### 2.4 Analysis Engine

- `GET /analysis/{dataset_id}` → builds `VerifiedAnalysisResponse` from stored `Analysis` JSON columns + `verified_analysis.build_verified_analysis_report` + rule-based `insight_engine.generate_professional_insights`. Ownership enforced (✅).
- Profiling (`profiling.profile_dataframe`) computes rows/columns/dtypes/missing/duplicates/correlations/outliers/statistics; `professional_analysis.generate_professional_analysis` adds executive summary/insights/recommendations/distributions/quality issues. Quality score & summary text computed in `insights.py`.
- Concerns to test (Phase 11): NaN handling, zero-variance columns, all-categorical/all-numeric datasets, 1-row datasets, mixed-type columns, correlation crash when <2 numeric columns. Code volume (2442 lines) means these edge cases MUST be proven by tests, not assumed.
- `Analysis.report_path` column referenced by `admin_service.get_dashboard_stats` (`Analysis.report_path != None`) — **the model has NO `report_path` column** → AttributeError / 500 on `GET /admin/dashboard`. Confirmed bug.
- Persistence: analysis saved once at upload; no versioning; re-analysis missing.

### 2.5 Data Cleaning

- Preview: `POST /cleaning/{id}/preview` → `_clean_dataframe(df)` on a copy (verify preview truly doesn't persist — code reads original file each time, looks non-destructive ✅).
- Apply: `POST /cleaning/{id}/apply` writes `*_cleaned.csv/xlsx` next to original, returns summary. Download: `GET /cleaning/{id}/download` streams cleaned file (404 if not applied — verify `get_cleaned_file_path` raises HTTPException properly).
- Supported ops (per `services/cleaning.py`): drop duplicates, fill numeric mean/median, categorical mode, dropna rows, normalize categoricals — needs unit tests incl. empty-numeric-column case.
- **Cleaned dataset is NOT registered as a new Dataset row** — no DB persistence of cleaned version beyond filesystem; "Cleaned dataset persistence" (Phase 2) partially missing.

### 2.6 AI (Chat / Insights)

- Providers: `ai_provider.py` supports Gemini (`google-genai`), OpenRouter (httpx), Ollama (`ollama` client). Default `AI_PROVIDER=gemini`; `.env.example` ships `GEMINI_MODEL=gemini-3.7-flash` (**model name looks invalid/nonexistent** — likely typo; document correct model IDs).
- `chat.py` (1334 lines) builds dataset-aware context from stored Analysis, has `generate_fast_answer` deterministic fallback → good: basic answers don't depend on AI availability. `build_focused_prompt` injects real stats (must verify no invented numbers).
- Endpoints: `GET/POST /chat/{dataset_id}/sessions`, `GET/DELETE /chat/sessions/{id}`, `POST /chat/{dataset_id}` — all ownership-checked ✅.
- Failure handling: verify `generate_ai_response` raises `AIProviderError` and endpoint returns controlled 502/503 without stack trace.
- AI query limits (`ai_queries_per_month` plan limit) **never enforced**.

### 2.7 Reports

- `GET /reports/` lists datasets-with-analysis per user ✅. `GET /reports/{dataset_id}/pdf` and `GET /analysis/{dataset_id}/report` both stream ReportLab PDF built from DB analysis (not frontend guesses) ✅.
- `services/report.py` (2631 lines) generates charts into BytesIO (matplotlib Agg — verify thread safety & font issues in Docker).
- No report history table (report = derived view). Acceptable; document.

### 2.8 Payments / Subscriptions (CRITICAL AREA)

Backend endpoints (mounted twice: router has its own `prefix="/payments"` AND api.py includes with `prefix="/payments"` → final path `/api/v1/payments/payments/*`?? — VERIFY: `api_router.include_router(payments.router, prefix="/payments")` + `router = APIRouter(prefix="/payments")` ⇒ actual path is `/api/v1/payments/payments/...`. **Likely route-path duplication bug** breaking every frontend payment call.)

| Endpoint | Status | Bugs |
|---|---|---|
| GET plans | ⚠️ | Double-prefix issue above. |
| POST create-checkout | ⚠️ | Takes `plan_type` as raw body/query param (untyped str) — should be Pydantic model. Dev mock checkout allowed (server-side one-time sessions — reasonable), production correctly refuses when unconfigured. |
| GET success | ❌ design flaw | **Subscription activation happens on browser redirect**, not authoritatively via webhook (violates Phase 7 CRITICAL). `verify_and_activate_subscription(session_id)` called WITHOUT `expected_user_id` → any authenticated user passing another user's session id could activate their own… actually it activates the *session owner's* subscription using caller's identity for history/notification → cross-user record mixing. Payment history written here with `subscription_id=None` (never linked) and `provider_payment_id=session_id` (checkout-session id used as payment id — wrong field semantics). |
| POST webhook | ❌ incomplete | Handles only `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`. **Missing:** `customer.subscription.created`, `invoice.paid`, `invoice.payment_failed`. **No idempotency** (no event-id store; Stripe retries → duplicate activations/emails). Webhook path calls `verify_and_activate_subscription` which creates subscriptions but **never records PaymentHistory, never sends confirmation email, never creates notification** → the authoritative path produces no payment history. Signature verification present (good). If Stripe unconfigured, webhook returns "ignored" 200 (fine). |
| GET subscription | ✅⚠️ | Ownership OK; returns free-plan default when none. Expiry state not recomputed (`current_period_end` past → still shows active). |
| POST cancel | ⚠️ | Sets local `cancel_at_period_end` even when Stripe call fails mid-way? (stripe error → 500 before commit, OK). Notification created ✅. No cancellation email sent (Phase 5 requires). |
| GET history | ✅ | Ownership OK, pagination OK. |
| Plan limits enforcement | ❌ | Nothing checks `max_datasets` / `max_file_size_mb` / `ai_queries_per_month` anywhere in dataset upload or chat. |
| Frontend pricing | ❌ | `components/landing/Pricing.tsx` hard-codes a static `plans` array; `PricingCard` "Get Started" button has **no onClick / no API call / no redirect to checkout**. Entire purchase flow disconnected from backend (rule 12 violated). No `/payment-success` frontend route exists although success_url points to it → post-checkout lands on 404. No `/pricing` route either. |

Model layer: `Subscription.provider_subscription_id` unique ✅; `PaymentHistory.provider_payment_id` unique ✅ (dedupe possible). But nothing stores Stripe **event ids** → idempotency gap. `User.subscription` is one-to-one (`uselist=False`) — plan says recreate/update single sub; OK.

### 2.9 Notifications

- Backend CRUD complete: list (+unread_count), unread-count, mark-read, mark-all-read, delete; all ownership-filtered ✅. `create_notification()` helper used by payments ✅.
- Bugs: list serializes `n.notification_type` — value is an Enum object; FastAPI will serialize enum fine, but check `type` consistency. Route-order: `PUT /{notification_id}/read` vs `PUT /mark-all-read` — `/mark-all-read` matches `{notification_id}` pattern? No: `/{id}/read` has two segments, safe. ✅
- Frontend: **completely missing.** No `services/notification.ts`; TopNavbar bell is a static button with a permanently-on red dot; no dropdown, no badge count, no read/delete UI. Violates rules 12/14 (badge not connected to backend).
- Expiry (`expires_at`) never filtered/used.

### 2.10 Dashboard

- `GET /dashboard/stats` (`crud_dashboard` 249 lines) — recent datasets, totals, upload trend etc.; frontend `useDashboard` consumes it. Needs test for empty-user case.

### 2.11 Settings

- Change password, profile, avatar, account deletion wired ✅ (see above).
- Notification preferences (email/dataset alerts/weekly reports) stored **only in localStorage** — no backend persistence (rule 12 violation; either add user-preferences column+endpoint via Alembic migration or declare client-only intentionally).
- Theme handled by `ThemeContext` (client-only, acceptable).

### 2.12 Admin

- Backend endpoints exist with superuser guard ✅ but `total_reports` uses nonexistent `Analysis.report_path` → 500. `db.execute("SELECT 1")` on SQLAlchemy 2.x requires `text()` → system-health endpoint likely raises → 500. Both confirmed bugs.
- Frontend `AdminDashboard.tsx` + `AdminRoute.tsx` exist but **no route registered** → feature unreachable. Sidebar lacks admin link.

### 2.13 UI / Routing

- Routes present: `/`, `/login`, `/register`, `/forgot-password`, `/reset-password`, `/dashboard` (+upload, datasets, analysis/:id, reports, ai-chat/:id?, settings), `/demo`→/, `*`→404.
- **Missing routes:** `/payment-success`, `/pricing` (referenced by payment success_url/cancel_url), admin route, and error pages `ForbiddenPage`/`ServerErrorPage` are never routed (403/500 pages unreachable).
- Duplicate layout/component trees: `components/layouts/*` vs `layouts/*`, `components/common/*` vs unused copies; `services/api.ts` vs `lib/api.ts` vs `api/axios.ts` — three axios instances; only `@/services/api` is actually used by services; `lib/api.ts` (used by analysis/chat/dataset/dashboard/report services!) differs: baseURL = `import.meta.env.VITE_API_URL` with **no fallback** → if env missing, requests go to relative "" → broken. Wait — services import `@/lib/api` while AuthContext imports `@/services/api`: **two parallel stacks** with different interceptors/timeouts (30s vs 120s). Consolidate.
- `frontend/src/api/*.api.ts` are empty files (dead code). `src/test.ts` purpose unclear.
- Toast/loading/empty states: sonner-based `lib/toast` used across pages ✅ (spot-check each page during repair phase).

---

## 3. Database & Migration Audit

Models: `users`, `datasets`, `analyses`, `chat_sessions`, `chat_messages`, `subscriptions`, `payment_history`, `notifications`.

Issues found:
1. **Two `get_db` implementations** (`db/database.py` and `db/session.py`) — both used inconsistently across routers (payments/notifications import from `database`, others from `session`). Same engine, low risk, but consolidate.
2. `User` lacks relationships to `ChatSession`, `ChatMessage`, `Notification`, `PaymentHistory` (PaymentHistory has FK user_id CASCADE at DB level; ORM cascade for account-deletion path untested).
3. `Dataset.analysis` ↔ `Analysis.dataset` back_populates ✅, FK CASCADE ✅, unique dataset_id ✅.
4. Enums stored as PG `Enum` types — migration `20240901abc12` must create them; verify names match model (`plantype`, `subscriptionstatus`, `notificationtype`).
5. `datetime.utcnow` deprecated (Python 3.12+) — warnings only.
6. **Migration graph:** linear chain `48379796b0ac(users) → 68daab538788(datasets) → 3523d78a50b6(add cols) → f957ba39a00d → 48e8bbad6175(analyses) → c29672287d79(summary_text) → f259af705ecd(quality) → {0179eb8e1705, c2cdee296c8e(chat)} …` — BUT `0179eb8e1705.down_revision='f259af705ecd'` AND `c2cdee296c8e.down_revision='0179eb8e1705'` while merge `658de0610bd9` merges `(55aa91c462ea, a1b2c3d4e5f6)` where `a1b2c3d4e5f6.down='0179eb8e1705'` and `55aa91c462ea.down='c2cdee296c8e'` → DAG consistent-ish, single head `20240901abc12`. Suspicious items: duplicated "create_datasets_table" revisions (68daab538788 + 3523d78a50b6 whose title says create but actually add_column), `f957ba39a00d_describe_change` placeholder name, `0179eb8e1705` possibly re-adds summary_text/quality_score already added by c29672287d79/f259af705ecd → **duplicate column errors on fresh DB highly likely**. Must run `alembic upgrade head` on clean Postgres to prove; then fix (merge/rewrite offending migrations carefully).
7. `alembic.ini sqlalchemy.url` empty; env.py overrides from settings ✅. `alembic check` currently cannot pass because model `Analysis` has fields (executive_summary etc.) — verify covered by `a1b2c3d4e5f6`.
8. No `tests/` at all; no conftest; recommended SQLite/Postgres-test fixture setup missing.

---

## 4. Environment / Config / Security Audit

- `backend/.env.example`: missing `SMTP_*` keys entirely (config expects SMTP_HOST/PORT/USERNAME/PASSWORD/FROM_EMAIL), missing `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID_PRO/BUSINESS`, `ENVIRONMENT`, `DEBUG`. Incomplete (Phase 22).
- `email.py` reads `os.getenv("SMTP_USER"/"FROM_EMAIL"/"FROM_NAME")` while `core/config.py` defines `SMTP_USERNAME`/`SMTP_FROM_EMAIL` → **variable-name mismatch → email never configured even when env set**. Also bypasses pydantic settings. Fix to use `settings`.
- CORS: `allow_origins=[settings.FRONTEND_URL]` single origin ✅; wildcard methods/headers acceptable for bearer-token API.
- Secrets: no hard-coded secrets found in code ✅ (docker-compose has dev postgres password `postgres` — acceptable for local compose; document). `frontend/.env` committed — contains only public VITE_API_URL (OK, but add `.env.example` for frontend).
- JWT: HS256, SECRET_KEY required from env ✅; no algorithm confusion (algorithms pinned) ✅. Access token 60 min.
- Password hashing: bcrypt via passlib; pinned `bcrypt==4.0.1` in base.txt but dev.txt shows bcrypt 5.0.0 installed elsewhere — version pin conflict can break passlib hashing (known passlib/bcrypt incompatibility with 4.1+). Verify runtime.
- File uploads: UUID storage, extension whitelist, size caps, traversal guard on profile pictures ✅; dataset download uses stored absolute path ✅.
- Webhook signature verified via `construct_event` ✅.
- Rate limiting: none (note as known limitation).
- Stack traces: several handlers embed `str(e)` into HTTP detail (payments success 500, profile-picture errors, dataset profiling 500) → internal info leakage; sanitize.
- `print()` used instead of logger throughout email/payment/auth (logging.py exists but unused).

---

## 5. Docker Audit

- `docker-compose.yml`: postgres 16 + backend (uvicorn via Dockerfile) + frontend (vite dev). Backend `DATABASE_URL` in `.env.example` points to host `postgres` ✅ (compose-network correct). Ollama default `host.docker.internal:11434` — on Linux compose this fails unless `extra_hosts: host.docker.internal:host-gateway` added → **known gap**.
- Compose runs migrations? No command to `alembic upgrade head` on startup → fresh DB has no schema (gap).
- `version: "3.9"` obsolete key (warning only).
- Frontend container env: VITE_API_URL=http://localhost:8000/api/v1 → inside browser on host this works only if backend exposed 8000 ✅ (it is). Document.

---

## 6. Frontend ↔ Backend API Contract Map (as-called)

| Frontend call | Expected backend path | Actual mounted path | Match |
|---|---|---|---|
| POST /auth/register, /auth/login, /auth/forgot-password*, /auth/reset-password | /api/v1/auth/* | same | ✅ (*forgot-password never actually called from ForgotPassword page) |
| GET/PATCH/DELETE /users/me, POST /users/me/change-password, /users/me/profile-picture, DELETE /users/me/profile-picture, POST /users/me/avatar | /api/v1/users/* | same | ✅ |
| POST /datasets/upload, GET/PATCH/DELETE /datasets[/{id}], GET /datasets/{id}/download | /api/v1/datasets/* | same | ✅ |
| GET /analysis/{datasetId} | /api/v1/analysis/{id} | same | ✅ |
| GET/POST /chat/{id}/sessions, GET/DELETE /chat/sessions/{id}, POST /chat/{id} | /api/v1/chat/* | same | ✅ |
| POST /cleaning/{id}/preview|apply, GET /cleaning/{id}/download | /api/v1/cleaning/* | same | ✅ |
| GET /reports/, GET /reports/{id}/pdf | /api/v1/reports* | router prefix `/reports` + route `/` and `/{id}/pdf` | ✅ |
| GET /dashboard/stats | /api/v1/dashboard | same | ✅ |
| GET /admin/dashboard, /admin/system-health | /api/v1/admin/* | same | ✅ (but page unrouted; endpoint 500s) |
| **Payments** | frontend expects /api/v1/payments/* | router self-prefix `/payments` + include prefix `/payments` → **/api/v1/payments/payments/*** | ❌ |
| **Notifications** | frontend has NO service | /api/v1/notifications/* | ❌ (backend ready, UI missing) |

---

## 7. Prioritized Repair Plan

**P0 — Critical correctness/security**
1. Fix payments double-prefix routing; align frontend/backend paths; type create-checkout body.
2. Make Stripe webhook authoritative: handle all 6 events, idempotency via event-id table (new Alembic migration), create Subscription/PaymentHistory/Notification/email from webhook; remove activation-on-redirect reliance (success endpoint becomes read-only status check); pass `expected_user_id`.
3. Fix forgot-password: backend unreachable-code indentation bug; wire ForgotPassword page to real API; single-use reset tokens; keep token out of prod responses.
4. Fix email service env-var mismatch + route through settings; graceful SMTP-unavailable behavior; add subscription-cancelled email.
5. Enforce plan limits (datasets count, file size, AI queries) in upload/chat paths.
6. Fix admin dashboard crashes (`report_path`, `text("SELECT 1")`) and mount admin route/page.

**P1 — Feature completion**
7. Build notifications UI (service + TopNavbar dropdown, badge from `/unread-count`, mark read/all/delete).
8. Build pricing→checkout→`/payment-success` frontend flow + routes; subscription status page in settings; payment history UI; cancel button.
9. Re-analysis endpoint; cleaned-dataset persistence option; notification creation on dataset events.
10. Persist user notification preferences server-side (migration) or formally scope to client-only.
11. Add 403/500 error routes; protect against refresh/direct-URL issues.

**P2 — Hardening / cleanup / tests**
12. Migrations: verify clean `alembic upgrade head` from zero; fix duplicate-column migrations; `alembic check` green.
13. Consolidate axios instances & layouts; delete empty `src/api/*.api.ts`, duplicate `crud/user.py`, empty `services/auth.py`; replace prints with logger; sanitize `str(e)` details.
14. Unify `get_current_user` (active check), fix profile-picture URL double-prefix & env var naming.
15. pytest suite (auth, users, datasets, analysis edge cases, cleaning, notifications, payments w/ mocked stripe, email w/ mocked SMTP, AI w/ mocked providers, admin) + E2E journey script; frontend `npm run build`/`lint` green.
16. .env.example completeness (backend SMTP/Stripe/ENVIRONMENT; create frontend/.env.example); Docker: alembic upgrade on start, ollama extra_hosts note.

**Definition-of-done tracking:** after each batch, run targeted tests; final gate = pytest + alembic upgrade-head-from-zero + npm build/lint + scripted E2E (register→upload→analyze→chat→clean→report→notify→settings→reset→mock-stripe checkout/webhook→cancel→delete).

**Known limitations to carry forward:** stateless JWT (no server logout), no rate limiting, profile images publicly addressable by UUID, single subscription per user, GEMINI_MODEL example value needs correction.
