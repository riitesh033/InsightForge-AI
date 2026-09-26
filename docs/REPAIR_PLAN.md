# InsightForge AI — Forensic Repair Plan

**Audit date:** 2026-09-26  
**Scope:** Static, read-only recheck of the existing application. This document is the only requested deliverable. No application, configuration, or migration code was changed; no files were deleted. Generated/dependency/cache directories (`backend/venv`, `frontend/node_modules`, `.git`, Python caches, build output) were excluded. No test, build, migration, or runtime command was run.

**Evidence labels:** **Confirmed** = directly visible in current source/config or tracked-file metadata; **Risk** = a code path is apparent but needs runtime/integration verification; **External blocker** = cannot settle without an isolated database/provider/environment. The earlier [FULL_SYSTEM_AUDIT.md](FULL_SYSTEM_AUDIT.md) was used as a lead, not treated as proof.

## Contents

- [A. Architecture map](#a-architecture-map)
- [B. Suspected bugs and repairs](#b-suspected-bugs-and-repairs)
- [C. Duplicate, empty, dead, and generated code](#c-duplicate-empty-dead-and-generated-code)
- [D. Frontend-to-FastAPI contract comparison](#d-frontend-to-fastapi-contract-comparison)
- [E. Models and Alembic audit](#e-models-and-alembic-audit)
- [F. Environment and container comparison](#f-environment-and-container-comparison)
- [G. Prioritized tests and exact validation commands](#g-prioritized-tests-and-exact-validation-commands)
- [Final triage and repair order](#final-triage-and-repair-order)

## A. Architecture map

| Area | Current implementation |
|---|---|
| Frontend entry | Vite/React starts at [`frontend/src/main.tsx`](../frontend/src/main.tsx#L1): `ThemeProvider`, `AuthProvider`, `BrowserRouter`, `App`, and Sonner toaster. [`App.tsx`](../frontend/src/App.tsx) delegates to [`routes/AppRouter.tsx`](../frontend/src/routes/AppRouter.tsx#L29). |
| Frontend routes/layouts | `/`, `/login`, `/register`, `/forgot-password`, `/reset-password`, protected `/dashboard` with index, `upload`, `datasets`, `analysis/:datasetId`, `reports`, optional `ai-chat/:datasetId?`, `settings`; `/demo` redirects home; `*` is Not Found. Active layouts are `src/layouts/{LandingLayout,AuthLayout,DashBoardLayout}.tsx`. No admin, payment-success, or pricing route is registered. |
| Frontend API clients | [`services/api.ts`](../frontend/src/services/api.ts#L8), [`lib/api.ts`](../frontend/src/lib/api.ts#L3), and [`lib/axios.ts`](../frontend/src/lib/axios.ts#L3) each construct separate Axios clients; unused empty API stubs have since been removed. Auth/context/admin use `services/api`; dataset/analysis/chat/dashboard/report use `lib/api`; reset-password page bypasses the `services/auth.ts` helper and uses `lib/axios`. See [C](#c-duplicate-empty-dead-and-generated-code). |
| Backend entry/API | Uvicorn target is `app.main:app` ([`backend/Dockerfile`](../backend/Dockerfile)). [`backend/app/main.py`](../backend/app/main.py) creates FastAPI, CORS, startup Alembic upgrade, root/health routes, and mounts [`api/api.py`](../backend/app/api/api.py) at `settings.API_V1_STR` (`/api/v1`). |
| Backend routers | `api/api.py` mounts health, auth, users, datasets, analysis, dashboard, chat, reports, cleaning, notifications, payments, admin. Implementations are under `backend/app/api/v1/endpoints/`. All effective route paths include `/api/v1`; note that payments and notifications each declare their own prefix and are also mounted with the same prefix, producing double-prefixed effective paths. |
| Auth/dependencies | JWT/password utilities: `core/security.py`; primary auth/admin dependency: `api/dependencies.py`; second current-user dependency: `crud/deps.py`. Database providers: `db/database.py` (engine, startup migration bootstrap, `get_db`) and `db/session.py` (second `get_db`). |
| Database/models | SQLAlchemy/PostgreSQL via `db/database.py`, `db/base.py`, and `db/base_models.py`. Eight model classes: `User`, `Dataset`, `Analysis`, `ChatSession`, `ChatMessage`, `Subscription`, `PaymentHistory`, `Notification`; enum types `PlanType`, `SubscriptionStatus`, `NotificationType`. |
| Schemas/services | Pydantic schemas cover user, dataset, analysis/report/insights, chat, cleaning, dashboard, and admin. Active service families include dataset ingestion, profiling, cleaning, AI provider/chat, verified/professional analysis/insights, reports, dashboard, email, payments, and admin. |
| Migrations | Alembic config and environment: `backend/alembic.ini`, `backend/alembic/env.py`; 14 revisions in `backend/alembic/versions/`. `env.py` imports models and uses `DATABASE_URL`; static graph is detailed in [E](#e-models-and-alembic-audit). |
| Tests/tooling | Two backend test files exist (`tests/conftest.py`, `tests/test_auth.py`); the test module covers register/login/current-user/password reset flows. Frontend `package.json` has `build`, `lint`, `dev`, `preview`, but no test script. |
| Containers | Compose defines postgres, backend, frontend (`docker-compose.yml`); backend image runs Uvicorn with `--reload`; frontend image runs Vite dev server. Compose has no DB health check/readiness condition. |

## B. Suspected bugs and repairs

| Priority / confidence | File and location | Problem and impact | Proposed repair | Minimum proving test |
|---|---|---|---|---|
| **P1 — Confirmed** | [`backend/app/services/admin_service.py:18`](../backend/app/services/admin_service.py#L18); [`models/analysis.py`](../backend/app/models/analysis.py#L14); [`endpoints/admin.py:35,71-79`](../backend/app/api/v1/endpoints/admin.py#L35) | Admin dashboard queries nonexistent `Analysis.report_path`; this raises before its response is built. Admin user/dataset endpoints also read nonexistent dataset attributes (`Dataset.user_id`, `row_count`, `column_count`, `file_size_bytes`; model uses `owner_id`, `rows`, `columns`, `file_size`). Those APIs fail when used. Separately, `admin_service.py:38` passes a raw SQL string to SQLAlchemy 2 `Session.execute`; its local `except` converts that failure into a misleading “Degraded” status rather than a health-check failure. | Count reports from the actual report/analysis relation (or remove unsupported statistic); align admin query and response schema with `Dataset` model names; use `text("SELECT 1")`. | Admin dashboard/users/datasets/system-health endpoint tests with an admin and sample data; assert correct JSON and DB “Healthy”. |
| **P0 — Confirmed** | [`backend/app/api/v1/endpoints/payments.py:48-64`](../backend/app/api/v1/endpoints/payments.py#L48); [`services/payment.py:211-310`](../backend/app/services/payment.py#L211) | `/payments/success` calls `verify_and_activate_subscription(session_id)` without its available `expected_user_id=current_user.id`. The service explicitly checks session ownership only when that argument is passed. Any authenticated caller with another checkout-session id can run the success side effects; the endpoint then writes history/confirmation/notification for the caller even though activation follows the session metadata owner. | Bind verified session to the authenticated user before any database/email/notification side effect; make the success path idempotent and do not treat browser redirect as authoritative payment proof. | Foreign-user session is rejected and makes no state changes; replay of the same session creates no duplicate history or email. |
| **P1 — Confirmed route defect** | [`backend/app/api/api.py:68-84`](../backend/app/api/api.py#L68); [`payments.py:17`](../backend/app/api/v1/endpoints/payments.py#L17); [`notifications.py:12`](../backend/app/api/v1/endpoints/notifications.py#L12) | The aggregator adds `/payments` and `/notifications`, while each router already has the same router prefix. Effective routes are `/api/v1/payments/payments/...` and `/api/v1/notifications/notifications/...`, not the conventional paths. Any UI/client using the expected single prefix gets 404; no current frontend caller exists to expose this in routine use. | Keep the prefix at only one level (router declaration or aggregator); document the final route and update OpenAPI/clients consistently. | Route inventory/OpenAPI test asserts each expected endpoint appears once at `/api/v1/payments/...` and `/api/v1/notifications/...`, and old doubled paths are absent. |
| **P1 — Confirmed feature gap** | [`frontend/src/components/landing/Pricing.tsx:3-34`](../frontend/src/components/landing/Pricing.tsx#L3); [`PricingCard.tsx:62-71`](../frontend/src/components/landing/PricingCard.tsx#L62); [`AppRouter.tsx`](../frontend/src/routes/AppRouter.tsx#L29); [`services/payment.py:144,183-184`](../backend/app/services/payment.py#L144) | Pricing is static; “Get Started” has no handler and no frontend calls `/payments/*`. Backend redirects to `/payment-success` and `/pricing`, neither of which is routed; `/pricing` is also used by the navbar. Paid-plan purchase/cancel/success cannot complete in the UI. Frontend `$19`/“Custom” labels do not match backend Pro `$29`/Business `$99`. | Connect plan selection to authenticated checkout, use server plan data, add payment success/cancel routes that verify status safely, and align displayed plans/prices. | UI/API integration tests for checkout selection, successful and canceled return paths, error/expired session, and price parity. |
| **P0 — Confirmed** | [`backend/app/crud/deps.py:16-52`](../backend/app/crud/deps.py#L16); [`backend/app/api/dependencies.py:15-55`](../backend/app/api/dependencies.py#L15); [`endpoints/payments.py:11-13`](../backend/app/api/v1/endpoints/payments.py#L11); [`endpoints/notifications.py:8-10`](../backend/app/api/v1/endpoints/notifications.py#L8) | Two `get_current_user` implementations differ: primary dependency blocks inactive users; CRUD dependency does not. Payments and notifications import the weaker dependency, so a still-valid token can continue using those routes after account deactivation. | Consolidate to the active-account-checking dependency and share it consistently. | Deactivate a user while retaining a token; assert payment and notification routes reject access. |
| **P1 — Confirmed** | [`frontend/src/components/datasets/DownloadDialog.tsx:8-28`](../frontend/src/components/datasets/DownloadDialog.tsx#L8); [`frontend/src/services/dataset.ts:165-181,261-282`](../frontend/src/services/dataset.ts#L165); [`backend/app/api/v1/endpoints/dataset.py:80-119`](../backend/app/api/v1/endpoints/dataset.py#L80); [`endpoints/cleaning.py:71-88`](../backend/app/api/v1/endpoints/cleaning.py#L71) | Download dialog labels CSV/XLSX as a **cleaned** dataset but calls `downloadDataset`, which hits the original-download endpoint. The cleaned helper sends `?format=...`, but the cleaning route accepts no format and returns the one stored cleaned file. A CSV choice for an XLSX source can therefore be named `.csv` while containing XLSX bytes. The original route likewise ignores its optional format query. | Route cleaned selections through the cleaning endpoint; either convert according to a validated `format` parameter or return the actual extension/filename and do not rename bytes incorrectly. Keep original-download semantics separate. | Upload CSV and XLSX fixtures; verify dialog downloads cleaned values and each extension matches detected file bytes/content type; original download remains byte-identical. |
| **P1 — Risk, needs integration test** | [`backend/app/services/payment.py:375-417`](../backend/app/services/payment.py#L375); [`endpoints/payments.py:112-128`](../backend/app/api/v1/endpoints/payments.py#L112) | Stripe webhook handles only checkout completion and subscription updated/deleted; webhook completion activates a subscription but does not call payment-history/email/notification recording, and no processed-event idempotency store is visible. A repeated browser success can separately attempt duplicate history (provider id is unique). | Make verified webhooks the authoritative, idempotent state transition; persist Stripe event ids and a linked payment record, and define handling for invoice paid/failed events. | Valid/invalid signature, duplicate event, out-of-order event, successful payment history/linkage, and failed invoice behavior against Stripe test fixtures. |
| **P1 — Confirmed feature gap** | [`backend/app/services/payment.py:28-79`](../backend/app/services/payment.py#L28); [`services/dataset.py:28-32, upload_dataset`](../backend/app/services/dataset.py#L28); [`services/chat.py`](../backend/app/services/chat.py); [`endpoints/dataset.py:41-51`](../backend/app/api/v1/endpoints/dataset.py#L41) | Plan limits are defined (e.g. Free max 3 datasets/10 MB and AI query cap) but repository search found them only in the plan definitions; upload enforces a fixed 20 MB cap, not subscription-specific limits, and chat does not enforce query quotas. | Add shared entitlement/quota checks before upload/chat work; define unlimited semantics and concurrency-safe counters. | Free/Pro/Business boundary tests for dataset count, upload bytes, monthly chat limit, and concurrent requests. |
| **P2 — Confirmed** | [`frontend/src/components/dashboard/TopNavbar.tsx:33-42`](../frontend/src/components/dashboard/TopNavbar.tsx#L33); [`frontend/src/pages/Dashboard/SettingsPage.tsx:80-89`](../frontend/src/pages/Dashboard/SettingsPage.tsx#L80); [`backend/app/api/v1/endpoints/users.py:158`](../backend/app/api/v1/endpoints/users.py#L158) | Backend persists an uploaded image URL beginning `/api/v1/users/profile-pictures/...`. The frontend prefixes it with `VITE_API_BASE_URL || "/api/v1"`; with the fallback (or a base URL already ending `/api/v1`) this produces `/api/v1/api/v1/...` and the image fails. | Store/return either relative route or absolute origin consistently; normalize base URL and avoid adding an API prefix twice. | Upload image and assert navbar/settings `<img>` URL resolves once and returns 200 with base URL unset and configured. |
| **P2 — Confirmed data-integrity mismatch** | [`backend/app/models/user.py:76-82`](../backend/app/models/user.py#L76); [`models/subscription.py:46-51`](../backend/app/models/subscription.py#L46); [`20240901...py:17-30`](../backend/alembic/versions/20240901abc12_add_subscriptions_payment_history_notifications.py#L17) | `User.subscription` is `uselist=False`, but `Subscription.user_id` is not unique in the model or migration. Multiple rows can exist although service code treats the relation as singular and selects `.first()`, making active-plan selection ambiguous. | Decide whether subscriptions are one-to-one or historical-many; add/retain a uniqueness rule or make active-subscription selection explicit and indexed. | Insert two subscriptions for one user and assert DB rejects or deterministic active/current selection. |
| **P2 — Confirmed risk** | [`core/security.py:72-108`](../backend/app/core/security.py#L72); [`endpoints/auth.py:129-207`](../backend/app/api/v1/endpoints/auth.py#L129) | Reset tokens are signed and expire after one hour, but there is no stored `jti`/used marker; a valid reset token can be reused until expiry. `forgot_password` returns `reset_token` for every environment other than the exact string `"production"`, not only local development. | Use a one-time persisted token/nonce and allow response token exposure only under an explicit local-development setting; keep generic account-existence response. | Invalid/expired/wrong-type/reused token tests; staging-like environment must never return a token. |
| **P2 — Confirmed** | [`frontend/src/services/api.ts:8-21`](../frontend/src/services/api.ts#L8); [`frontend/src/lib/api.ts:3-14`](../frontend/src/lib/api.ts#L3); [`frontend/src/lib/axios.ts:3-9`](../frontend/src/lib/axios.ts#L3); [`TopNavbar.tsx:41`](../frontend/src/components/dashboard/TopNavbar.tsx#L41) | Three live Axios instances have different fallback, timeout, token-clearing/redirect behavior; `lib/axios` has no API URL fallback, and UI also uses a second Vite variable name. A deployment with only one configured name can break password reset or image URLs and behavior differs by feature. | Consolidate to one configured client/interceptor; standardize on one documented `VITE_API_URL`/origin convention and add a frontend example file. | Build with no env and with production base URL; test all client calls, multipart, blob, 401 behavior. |
| **P2 — Confirmed** | [`SettingsPage.tsx:64-75,210-225`](../frontend/src/pages/Dashboard/SettingsPage.tsx#L64); [`TopNavbar.tsx:132-143`](../frontend/src/components/dashboard/TopNavbar.tsx#L132); [`endpoints/notifications.py`](../backend/app/api/v1/endpoints/notifications.py#L15) | Settings notification preferences persist only in browser `localStorage`; navbar bell/dot has no notifications API call; notification endpoints have no frontend service. Expiry values are stored but list query does not filter them. | Either label preferences client-only or persist via user settings; add notification list/count/read/delete client/UI and decide expiry handling. | Multi-user persistence, unread badge/read/delete/expiry tests. |
| **P2 — Risk, confirmed code path** | [`backend/app/services/dataset.py:87-105`](../backend/app/services/dataset.py#L87); [`crud/crud_dataset.py:10-17`](../backend/app/crud/crud_dataset.py#L10); [`services/dataset.py:145-203`](../backend/app/services/dataset.py#L145) | Ingestion writes the uploaded file, commits the `Dataset` via `create_dataset`, then creates/commits `Analysis` separately. If the second commit fails, the request fails but leaves a dataset/file without analysis. | Make both DB records one transaction and clean the file on rollback/failure; do not commit the dataset before analysis succeeds. | Force analysis insert/commit failure and assert no dataset/file remains. |
| **P2 — Risk; addressed in cleanup** | [`backend/app/main.py`](../backend/app/main.py); [`db/database.py`](../backend/app/db/database.py); [`docker-compose.yml`](../docker-compose.yml) | Startup migrations previously skipped existing Alembic-managed schemas, while startup failure was logged and swallowed; Compose did not wait for database readiness. | Compose now waits for PostgreSQL health, app startup runs idempotent `alembic upgrade head`, and migration failures are logged and re-raised so the API does not start against an incomplete schema. | Verified in an isolated empty Compose database: services became healthy; `/health`, `/api/v1/health`, and `/api/v1/health/db` returned 200. |
| **P2 — Environment exposure risk; contents intentionally not inspected** | `backend/.env` and `frontend/.env` were tracked; values were not read. Conservative cleanup removes them from the Git index while preserving ignored local files. | Tracked files could contain credentials. Whether they contain secrets is unknown because no values were read. | If either contains real credentials, rotate them and audit repository history. | Local files retained/ignored; repository history still requires an authorized secret scan. |

## C. Duplicate, empty, dead, and generated code

| Category | Evidence/status |
|---|---|
| Axios clients | **Confirmed duplicate clients:** `services/api.ts`, `lib/api.ts`, and `lib/axios.ts`; these live clients remain outside this cleanup. Unreferenced empty API stubs under `src/api/` were removed after reference search. |
| Layouts | **Confirmed parallel tree; likely obsolete copy:** router imports `src/layouts/*`; search found no imports from `src/components/layouts/*`. Do not delete before reference/build check. |
| CRUD | `app/crud/user.py` appears duplicate but remains untouched because this cleanup did not establish it was safe to remove. The zero-byte `app/crud/crud_report.py` had no references and was removed; report routes query inline. |
| Empty source files | Unreferenced zero-byte frontend API stubs, `backend/app/services/auth.py`, and `backend/app/crud/crud_report.py` were removed. Empty `__init__.py` package markers remain. `.editorconfig` remains untouched. Root `.env.example` is now a sanitized Compose template. |
| Unused helper/duplicate calls | `services/auth.ts::resetPassword` exists, but `ResetPasswordPage` submits directly through `lib/axios`; `AuthContext` separately duplicates the `GET /users/me` call. Reports PDF has two valid backend routes and frontend callers. Confirm call graphs before removal. |
| Unmounted UI/routes | **Confirmed:** `AdminDashboard` and `AdminRoute` exist but are not mounted in `AppRouter`; `ForbiddenPage` and `ServerErrorPage` are not routed. `/payment-success` and `/pricing` are referenced by payment/nav flows but absent from route table. `NotFoundPage` is mounted; `/demo` redirects. |
| Notification/billing UI | **Confirmed absence in inspected frontend callers:** no `/notifications` or `/payments` API calls; pricing has a static component and inert button. Backend routes remain available. |
| Generated/dependency artifacts | `frontend/package-lock.json` is generated dependency metadata and is retained. Python bytecode/cache directories are removed after validation and ignored. Dependency/build directories are not removed. `frontend/src/test.ts` remains untouched because it was not proven generated or dead. |

## D. Frontend-to-FastAPI contract comparison

The common backend prefix is `/api/v1`. Axios clients attach a bearer token when one is stored; unauthenticated endpoints are marked below. “Response” is the server response shape/content, not merely a frontend TypeScript assertion.

| Frontend caller (source) | Method + effective URL | Query/body | Backend response / auth | Result |
|---|---|---|---|---|
| `services/auth.ts::login` (`:53`) | POST `/auth/login` | Form-urlencoded `username`, `password` | `{access_token, token_type}`; public | **Match.** OAuth2 form handler. |
| `services/auth.ts::register` (`:81`) | POST `/auth/register` | JSON `{full_name,email,password}` | `UserResponse`, 201; public | **Match.** |
| `services/auth.ts::forgotPassword` (`:105`); `ForgotPassword.tsx:31` | POST `/auth/forgot-password` | JSON `{email}` | Generic `{message}`; may include `reset_token` outside exact production; public | **Route/body match.** Current page calls service; this corrects the stale lead’s claim that the page simulates success. |
| `services/auth.ts::resetPassword` (`:128`) and `ResetPasswordPage.tsx:40` (direct separate Axios call) | POST `/auth/reset-password` | JSON `{token,new_password}` | `{message}` on success; public | **Route/body match.** Reset page does not use the service helper. |
| `AuthContext.tsx:57`; `services/auth.ts::getCurrentUser` (`:157`) | GET `/users/me` | none | `UserResponse`; bearer required | **Match; duplicate callers.** |
| `services/auth.ts::updateProfile` (`:189`) | PATCH `/users/me` | JSON `{full_name,email}` | `UserResponse`; bearer | **Match.** |
| `services/auth.ts::changePassword` (`:219`) | POST `/users/me/change-password` | JSON `{current_password,new_password}` | `{message}`; bearer | **Match.** |
| `services/auth.ts::uploadProfilePicture` (`:251`) | POST `/users/me/profile-picture` | multipart `file` | `UserResponse`; bearer | **Match.** |
| `services/auth.ts::setBuiltinAvatar` (`:288`) | POST `/users/me/avatar` | query `avatar_id`; null body | `UserResponse`; bearer | **Match.** |
| `services/auth.ts::removeProfilePicture` (`:323`) | DELETE `/users/me/profile-picture` | none | `UserResponse`; bearer | **Match.** |
| `services/auth.ts::deleteAccount` (`:342`) | DELETE `/users/me` | none | 204; bearer | **Match.** |
| `services/dataset.ts::uploadDataset` (`:148`) | POST `/datasets/upload` | multipart `file` | `DatasetResponse`, 201; bearer | **Match.** |
| `services/dataset.ts::getDatasets` (`:102`) | GET `/datasets` | `page,page_size,search,sort_by,order` | `{items,total,page,page_size,pages}` of `DatasetResponse`; bearer | **Match.** Query names/defaults align. |
| `services/dataset.ts::renameDataset` (`:117`) | PATCH `/datasets/{id}` | JSON `{original_filename}` | `DatasetResponse`; bearer | **Match.** |
| `services/dataset.ts::deleteDataset` (`:134`) | DELETE `/datasets/{id}` | none | 204; bearer | **Match.** |
| `services/dataset.ts::downloadDataset` (`:165`); `DownloadDialog.tsx:24`; `DatasetCard.tsx:115` | GET `/datasets/{id}/download` | Optional `format` query | `FileResponse` original file; bearer | **Mismatch:** backend does not accept/use `format`; DownloadDialog incorrectly uses this original-file helper for “cleaned” CSV/XLSX options. |
| `services/dataset.ts::downloadOriginalDataset` (`:204`) and table original action | GET `/datasets/{id}/download` | none | Original `FileResponse`; bearer | **Match.** |
| `services/dataset.ts::previewCleaning` (`:233`) | POST `/cleaning/{id}/preview` | no body | `CleaningResponse`-shaped JSON; bearer | **Match by code shape.** |
| `services/dataset.ts::applyCleaning` (`:247`) | POST `/cleaning/{id}/apply` | no body | `CleaningResponse`-shaped JSON; bearer | **Match by code shape.** |
| `services/dataset.ts::downloadCleanedDataset` (`:261`); `DatasetCard.tsx:139` | GET `/cleaning/{id}/download` | `format` query (`csv`/`xlsx`) | `FileResponse` of single stored cleaned file; bearer | **Mismatch:** query ignored; response extension/content can differ from requested/name used. |
| `services/analysis.ts::getAnalysis` (`:245`) | GET `/analysis/{dataset_id}` | none | `VerifiedAnalysisResponse` (`analysis_id,created_at,verified_analysis,insights`); bearer | **Match** with `AnalysisData` interface structure. |
| `ReportButton.tsx:22` | GET `/analysis/{dataset_id}/report` | none, `responseType: blob` | PDF `StreamingResponse`; bearer | **Match.** |
| `services/dashboard.ts:80` | GET `/dashboard` (caller uses relative string `dashboard`) | none | `DashboardResponse`; bearer | **Match** with Axios base `/api/v1`; verify emitted URL in browser integration test. |
| `services/chat.ts:46` | GET `/chat/{dataset_id}/sessions` | none | list of `ChatSessionResponse`; bearer | **Match.** |
| `services/chat.ts:63` | POST `/chat/{dataset_id}/sessions` | no body | `ChatSessionResponse`; bearer | **Match.** |
| `services/chat.ts:80` | GET `/chat/sessions/{session_id}` | none | `{session_id,dataset_id,messages}`; bearer | **Match.** |
| `services/chat.ts:101` | DELETE `/chat/sessions/{session_id}` | none | 204; bearer | **Match.** |
| `services/chat.ts:113` | POST `/chat/{dataset_id}` | JSON `{message,session_id}` | `{session_id,dataset_id,answer,messages}`; bearer | **Match.** |
| `services/report.ts:11` | GET `/reports` | none | list `{dataset_id,dataset_name,uploaded_at,analysis_id,quality_score}`; bearer | **Compatible via FastAPI slash redirect:** backend declares `/reports/`, so this relies on redirect handling. |
| `services/report.ts:19`; `services/dataset.ts:300` | GET `/reports/{dataset_id}/pdf` | none, `responseType: blob` | PDF `StreamingResponse`; bearer | **Match; duplicate PDF downloader.** |
| `pages/Dashboard/AdminDashboard.tsx:14-15` | GET `/admin/dashboard`; GET `/admin/system-health` | none | `AdminDashboardStats`; `SystemHealthSchema`; admin bearer | **Paths/auth match**, but page is unrouted and dashboard/system-health have backend defects noted in B. |
| `TopNavbar.tsx` / `SettingsPage.tsx` image `src` | Browser GET `/api/v1/users/profile-pictures/{filename}` | URL, not Axios | `FileResponse`; no auth dependency | Endpoint exists; URL construction can double-prefix (B). |

**Backend routes without a frontend API caller in the inspected source:** `GET /auth/test`; `GET /api/v1/health/`, `/health`, `/api/v1/health/db`; payment plans/create-checkout/success/webhook/subscription/cancel/history are actually under `/api/v1/payments/payments/...`; notification list/count/read/mark-all/delete routes are under `/api/v1/notifications/notifications/...`; admin users/status/datasets/delete; profile-image GET is used only as an `<img>` URL. There is no `/auth/logout` backend route; logout currently clears local state only.

## E. Models and Alembic audit

### SQLAlchemy models

| Model/table | Fields and relations observed |
|---|---|
| `User` / `users` — `models/user.py:14-82` | `id,full_name,email,hashed_password,profile_picture,is_active,is_superuser,created_at,updated_at`; datasets cascade and one-to-one-style subscription relationship. |
| `Dataset` / `datasets` — `models/dataset.py:13-82` | `id,filename,original_filename,file_type,file_size,file_path,rows,columns,uploaded_at,owner_id`; owner FK cascade; one-to-one analysis relation. |
| `Analysis` / `analyses` — `models/analysis.py:14-122` | `id,dataset_id,summary,column_info,statistics,missing_values,duplicates,correlations,outliers,summary_text,quality_score,executive_summary,key_insights,recommendations,business_opportunities,distributions,data_quality_issues,created_at`; unique dataset FK cascade. No `report_path` field. |
| `ChatSession` / `chat_sessions` — `models/chat_session.py:13-72` | `id,dataset_id,user_id,title,created_at,updated_at`; dataset/user FKs cascade; messages relation cascade. |
| `ChatMessage` / `chat_messages` — `models/chat_message.py:14-54` | `id,session_id,role,content,created_at`; session FK cascade. |
| `Subscription` / `subscriptions` — `models/subscription.py:37-131` | `id,user_id,plan,status,provider_customer_id,provider_subscription_id,current_period_start,current_period_end,cancel_at_period_end,canceled_at,started_at,created_at,updated_at`; enum plan/status, unique provider subscription ID, user/payment relations. `user_id` itself is not unique. |
| `PaymentHistory` / `payment_history` — `models/subscription.py:134-212` | `id,user_id,subscription_id,amount,currency,payment_status,payment_provider,provider_payment_id,plan_type,description,metadata_json,created_at`; unique provider payment id. |
| `Notification` / `notifications` — `models/notification.py:25-93` | `id,user_id,title,message,type,is_read,action_url,metadata_json,created_at,expires_at`; enum `notification_type`; FK has DB `ON DELETE CASCADE`. |

### Migration dependency graph

Static graph read from all 14 revision files; **no duplicate revision IDs or broken `down_revision` values were seen**. It yields one intended head, `42420889e6ec`; `alembic heads/history/upgrade` were not run.

```text
48379796b0ac (users, root)
└─ 68daab538788 (datasets)
   └─ 3523d78a50b6 (add rows/columns; filename misleading)
      └─ f957ba39a00d (no-op placeholder)
         └─ 48e8bbad6175 (analyses)
            └─ c29672287d79 (no-op placeholder)
               └─ f259af705ecd (adds summary_text)
                  └─ 0179eb8e1705 (adds quality_score)
                     ├─ a1b2c3d4e5f6 (professional-analysis columns)
                     └─ c2cdee296c8e (chat tables; datasets FK/nullability adjustment)
                        └─ 55aa91c462ea (user profile_picture)
                     \______________________________/
                           658de0610bd9 (merge: 55aa..., a1b2...)
                           └─ 20240901abc12 (subscription/payment/notification tables)
                              └─ 42420889e6ec (sync fields/types/indexes; expected head)
```

| Revisions / files | Changes / observations |
|---|---|
| `48379796b0ac_create_users_table.py` | Creates `users`; root revision. |
| `68daab538788_create_datasets_table.py` | Creates datasets, initially with nullable `uploaded_at`/`owner_id`. |
| `3523d78a50b6_create_datasets_table.py` | Adds `rows` and `columns`; **not** a second table creation. |
| `f957ba39a00d_describe_change.py` | `upgrade`/`downgrade` are `pass`; placeholder no-op. |
| `48e8bbad6175_create_analyses_table.py` | Creates initial analysis columns and unique dataset FK. |
| `c29672287d79_add_summary_text.py` | `upgrade`/`downgrade` are `pass`; placeholder no-op. |
| `f259af705ecd_add_quality_score.py` | Adds `summary_text` (filename is misleading). |
| `0179eb8e1705_add_summary_text_and_quality_score.py` | Adds `quality_score` only. It does not re-add `summary_text`. |
| `c2cdee296c8e_add_chat_sessions_and_messages.py` | Creates chat tables; makes dataset owner/upload fields non-null and adds cascade FK. |
| `55aa91c462ea_add_profile_picture_to_users.py` | Adds `users.profile_picture`. |
| `a1b2c3d4e5f6_add_professional_analysis_fields.py` | Adds six professional-analysis fields. |
| `658de0610bd9_merge_migration_heads.py` | Merge revision; `pass` in both directions is normal for a merge. |
| `20240901abc12_add_subscriptions_payment_history_notifications.py` | Creates initial subscription/payment/notification tables. |
| `42420889e6ec_sync_subscriptions_payment_history_.py` | Adds missing model fields, converts relevant PostgreSQL enums, changes widths/defaults and adds indexes/unique constraints. PostgreSQL-specific migration behavior needs a real disposable PostgreSQL run. |

### Static model/schema comparison and caveats

- **No duplicate head columns found in the files inspected.** The older audit’s duplicate-column hypothesis is contradicted by current migration bodies: `f259...` adds `summary_text`; `0179...` adds `quality_score`; `c296...` is empty.
- At the intended head, each current model’s listed fields has a corresponding migration step, including profile picture, professional analysis, chat, notification expiry/metadata, and subscription/provider fields. This is a static comparison, not proof the migration chain succeeds on PostgreSQL.
- Model/migration reconciliation still needs `alembic check`: initial `datasets` uses unbounded `String` versus model lengths and nullable owner/time until later adjustment; subscription/payment/notification fields/types are intentionally reconciled in `424208...`. Do not rewrite applied migrations without checking deployed revision state.
- `User` has no ORM-side `chat_sessions`, `notifications`, or `payment_history` relationship; child FKs specify database cascade. Production PostgreSQL should cascade, but SQLite tests do not enable FK enforcement in the fixture as inspected; account-deletion cascade behavior needs explicit tests and fixture policy.
- **Confirmed cardinality mismatch:** `User.subscription.uselist=False` but neither model nor migration makes `subscriptions.user_id` unique. See B.

## F. Environment and container comparison

| Source | Variable names / behavior |
|---|---|
| Backend `Settings` (`backend/app/core/config.py:6-80`) | Requires `DATABASE_URL`, `SECRET_KEY`; optional/default `ENVIRONMENT`, `DEBUG`, `ALGORITHM`, token expiry, `FRONTEND_URL`; SMTP `SMTP_HOST/PORT/USERNAME/PASSWORD/FROM_EMAIL/FROM_NAME`; Stripe `STRIPE_SECRET_KEY/WEBHOOK_SECRET/PRICE_ID_PRO/PRICE_ID_BUSINESS`; AI provider/Gemini/OpenRouter/Ollama variables. |
| `backend/.env.example` (safe template; contents read) | Contains database/secret placeholders, algorithm, frontend URL, AI provider and Gemini/OpenRouter/Ollama names. Omits SMTP, Stripe, explicit environment/debug and token expiry; omitted settings use defaults (email/payments unconfigured by default). |
| Frontend variables referenced by source | `VITE_API_URL` in Axios clients; `VITE_API_BASE_URL` in profile-image URL construction. No `frontend/.env.example` exists. |
| Root `.env.example` | Present but zero bytes. |
| Actual env filenames/tracking | `backend/.env` and `frontend/.env` exist and are tracked, confirmed by filename/status metadata only. **No actual `.env` contents/values were opened or printed.** Whether they contain secrets is unknown. |
| Compose (`docker-compose.yml`) | Reads `./backend/.env` and `./frontend/.env`; Postgres service credentials are fixed development values, DB on port 5432, backend on 8000, frontend on 5173. `depends_on` has no readiness health check. |
| Dockerfiles | Backend uses Python 3.11, installs `requirements/dev.txt` then `base.txt`, copies source twice, starts `uvicorn ... --reload`. Frontend uses Node 22 Alpine, `npm install`, starts Vite dev server; this is a development topology, not a production serving setup. |
| Dependency manifests | `base.txt` pins bcrypt 4.0.1; checked-in `dev.txt` pins bcrypt 5.0.0. Docker installs dev then base, but local/dev environments can differ. Verify Passlib/bcrypt behavior and make one deliberate compatible pin. |

**Corrections to the earlier lead:** current `ForgotPassword.tsx` calls the real service; backend forgot-password sends through the configured `EmailService` and correctly handles unknown users generically; email config reads `Settings` names (no `SMTP_USER` mismatch observed); backend auth tests exist; migration bodies do not duplicate `summary_text`/`quality_score`. These earlier claims were not carried forward as bugs.

## G. Prioritized tests and exact validation commands

No validation commands below were run for this audit. They are the proposed repair-stage commands. Use a disposable PostgreSQL database for migration commands; never point them at production or a developer DB with data.

### P0 — environment, migration, authentication, and payment-integrity gate

1. Have the operator inspect tracked `.env` values privately, rotate any real credentials, and remove real env files from version control/history as appropriate. Do not paste them into logs or audit artifacts.
2. Validate Compose interpolation without dumping rendered values:

```powershell
Set-Location 'C:\Users\rites\OneDrive\Documents\Projects\InsightForge-AI\InsightForge-AI-New'
docker compose config -q
```

3. Set `DATABASE_URL` privately in the shell to a clean, disposable PostgreSQL database (never the production or developer database). Do not put credentials in this document or command history. Then run:

```powershell
Set-Location 'C:\Users\rites\OneDrive\Documents\Projects\InsightForge-AI\InsightForge-AI-New\backend'
python -m alembic heads
python -m alembic history --verbose
python -m alembic upgrade head
python -m alembic check
```

`insightforge_audit` must be an empty, disposable database; provision it separately if absent. PostgreSQL availability/credentials are external blockers and were not tested.

4. After adding the focused regression tests, validate account deactivation and payment ownership/idempotency:

```powershell
Set-Location 'C:\Users\rites\OneDrive\Documents\Projects\InsightForge-AI\InsightForge-AI-New\backend'
$env:DATABASE_URL = 'sqlite://'
$env:TEST_DATABASE_URL = 'sqlite://'
python -m pytest -q tests\test_auth.py tests\test_payments.py
```

### P1 — feature and backend contract tests

Existing authentication suite (test fixture uses in-memory SQLite for route tests; lifespan migration bootstrap may log a skipped/failing attempt):

```powershell
Set-Location 'C:\Users\rites\OneDrive\Documents\Projects\InsightForge-AI\InsightForge-AI-New\backend'
$env:DATABASE_URL = 'sqlite://'
$env:TEST_DATABASE_URL = 'sqlite://'
python -m pytest -q tests\test_auth.py
```

Add and run focused tests as repairs land:

```powershell
python -m pytest -q tests\test_admin.py tests\test_payments.py tests\test_dataset_downloads.py
```

Cover admin model attributes/health check; active-user access; foreign/replayed payment sessions; webhook idempotency/history; conversion/content-type and filename for original/cleaned CSV/XLSX; upload rollback; plan quotas.

### P2 — UI, environment and full regression checks

```powershell
Set-Location 'C:\Users\rites\OneDrive\Documents\Projects\InsightForge-AI\InsightForge-AI-New\frontend'
npm run build
npm run lint
```

After the API/UI repairs, manually or via browser tests cover sign-in restoration, all protected routes, image URLs, report downloads, admin-only access, and payment success/cancel. Once backend test coverage expands:

```powershell
Set-Location 'C:\Users\rites\OneDrive\Documents\Projects\InsightForge-AI\InsightForge-AI-New\backend'
$env:DATABASE_URL = 'sqlite://'
$env:TEST_DATABASE_URL = 'sqlite://'
python -m pytest -q
```

Container smoke tests should use the intended dev Compose environment only after private `.env` validation:

```powershell
Set-Location 'C:\Users\rites\OneDrive\Documents\Projects\InsightForge-AI\InsightForge-AI-New'
docker compose build
docker compose up -d
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/api/v1/health/db
```

## Final triage and repair order

### Critical blockers

- Tracked real `.env` files are a **confirmed exposure risk**, but contents were deliberately not read; actual secret exposure is **unknown** until an authorized private review.
- Payment success does not bind the Stripe checkout session to the authenticated user, and payments/notifications accept inactive users through a weaker auth dependency. Treat both as P0 until fixed and regression-tested.
- Paid checkout has no connected frontend flow or return routes; admin dashboard has a confirmed missing ORM attribute and several stale dataset field references.
- PostgreSQL migration success, schema drift, and actual provider/env behavior remain external verification blockers; no DB-backed command was run.

### High-priority bugs

1. Repair admin service and stale Dataset properties; use SQLAlchemy `text()` for DB ping.
2. Connect pricing/checkout/success/cancel routes and align server/client plans.
3. Correct original-vs-cleaned download handling and requested-format/actual-file behavior.
4. Enforce plan limits before upload/chat processing.

### Medium cleanup

- Normalize API base URL/image construction and consolidate Axios clients.
- Make reset tokens one-time; limit development token exposure to explicit local development.
- Define subscription cardinality; test deletion cascades and upload transaction rollback.
- Persist or clearly label client-only notification preferences; connect notification UI.
- Remove/repurpose only after validation: empty API shims, empty auth/report modules, unused CRUD duplicate, unmounted layouts/pages, unused reset helper. Keep package lock and normal package `__init__.py` files.

### Exact repair order

1. Privately review/rotate tracked env credentials; create a disposable PostgreSQL database and record its current revision.
2. Reproduce/repair migration head and model drift on that disposable database; capture `alembic heads`, `upgrade head`, `alembic check`.
3. Bind payment success to the current user, make payment processing idempotent, and consolidate active-account checks; add/run focused P0 regression tests.
4. Repair admin endpoints and stale Dataset properties; use SQLAlchemy `text()` for DB ping; add focused tests.
5. Connect pricing/checkout/success/cancel routes and align server/client plans; enforce quotas.
6. Repair download contracts and image URL generation; consolidate Axios/env naming.
7. Add one-time reset token policy and notification preference/UI behavior.
8. Validate backend tests, frontend build/lint, migration checks, then Compose health/startup and route smoke tests.

**Audit limit:** static review covered every frontend route and live API client, router registrations/route declarations, all eight models, all 14 migration files/dependencies, relevant schemas/services, settings/env templates, tests, and Docker/Compose. Presentational frontend components and every analytical-service implementation were not individually read line-by-line or behavior-tested; their existence was inventoried and relevant API consumers reviewed. Findings labeled “Risk” require the listed integration test before being treated as runtime-proven.
