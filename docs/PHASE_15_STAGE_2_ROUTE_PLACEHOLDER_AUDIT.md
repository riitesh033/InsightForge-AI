# PHASE 15–17 — STAGE 2: Frontend Route + Production Behavior Audit

**Date:** 2026-09-26
**Mode:** READ-ONLY audit (no application code modified)
**Authoritative companion:** `docs/PHASE_15_STAGE_1_API_AUDIT.md`

> ⚠️ **CRITICAL CONTEXT DISCOVERY (read first):** The working tree is a clean git checkout of commit `2643721` ("Implement authentication and password reset flows…"). `git status --short` = empty; `git ls-files` shows that several files referenced by the Stage 1 audit and later-phase reports **do not exist in this repository state**: `frontend/src/services/payments.ts`, `notifications.ts`, `admin.ts`, `ai.ts`, `users.ts`, `PricingPage.tsx`, `SuccessPage.tsx`, `PaymentHistoryPage.tsx`, and the Phase 4–7 report/test artifacts. What DOES exist for payments/admin/chat is: `backend/app/api/v1/endpoints/payments.py`, `admin.py`, `chat.py`, `notifications.py`, plus frontend `AdminDashboard.tsx` (orphaned), `services/chat.ts`, and landing `Pricing.tsx`. All findings below are verified against THIS actual repository state, with line-number evidence.

---

## 1. Complete Route Inventory

Router source: `frontend/src/routes/AppRouter.tsx` (the only router file; `src/main.tsx` wraps `BrowserRouter` + `AuthProvider` + `ThemeProvider` + sonner `Toaster`).

| # | Route | Component | Layout | Protected? | Params | API dependencies | Loading | Error | Status |
|---|-------|-----------|--------|-----------|--------|------------------|---------|-------|--------|
| 1 | `/` | `pages/Landing/LandingPage` | LandingLayout | Public | – | none (static marketing incl. Pricing section) | n/a | n/a | OK |
| 2 | `/login` | `pages/Auth/LoginPage` | AuthLayout | Public | – | `POST /auth/login` via services/auth.ts | ✅ (`loading`) | ✅ detail/message branches | OK (minor E1) |
| 3 | `/register` | `pages/Auth/RegisterPage` | AuthLayout | Public | – | `POST /auth/register` then auto-login | ✅ | ✅ | OK |
| 4 | `/forgot-password` | `pages/Auth/ForgotPassword.tsx` | AuthLayout | Public | – | `POST /auth/forgot-password` | ✅ | ⚠️ uses `error.message` not axios `detail` (E2) | FUNCTIONAL but degraded errors |
| 5 | `/reset-password` | `pages/Auth/ResetPasswordPage` | AuthLayout | Public | `?token=` query | `POST /auth/reset-password` via **4th axios instance** `lib/axios.ts` | ✅ | ✅ reads `detail` correctly | OK (instance sprawl S2) |
| 6 | `/dashboard` (index) | `DashBoardPage` | DashboardLayout | ✅ ProtectedRoute | – | `GET /dashboard` (services/dashboard.ts) | ✅ skeleton | ✅ | OK |
| 7 | `/dashboard/upload` | `UploadDatasetPage` | DashboardLayout | ✅ | – | `POST /datasets/upload` | ✅ | ✅ detail-aware | OK (debug logs D1/D2) |
| 8 | `/dashboard/datasets` | `DatasetsPage` | DashboardLayout | ✅ | – | `GET /datasets`, patch/delete, cleaning, downloads | ✅ | ✅ | OK |
| 9 | `/dashboard/analysis/:datasetId` | `AnalysisPage` | DashboardLayout | ✅ | `datasetId` ↔ `useParams` | `GET /analysis/{id}`, `/reports/{id}/pdf`, `/analysis/{id}/report` | ✅ | ✅ | OK |
| 10 | `/dashboard/reports` | `ReportsPage` | DashboardLayout | ✅ | – | `GET /reports` (trailing-slash mismatch R1), `GET /reports/{id}/pdf` | ✅ | ✅ setError | OK after fix |
| 11 | `/dashboard/ai-chat/:datasetId?` | `AIChatPage` | DashboardLayout | ✅ | optional `datasetId` | `services/chat.ts` → `/chat/*` | ✅ | ✅ console.error + generic error | OK contract-wise (see §B2) |
| 12 | `/dashboard/settings` | `SettingsPage` | DashboardLayout | ✅ | – | users endpoints (change-password, avatar, delete account) | ✅ | partial | ⚠️ prefs localStorage-only (M1) |
| 13 | `/demo` | `<Navigate to="/">` | – | – | – | – | – | – | Redirect only |
| 14 | `*` | `Error/NotFoundPage` | – | Public | – | – | – | – | OK |

### Routes WITHOUT any route registration (orphans / missing pages)

| Item | Evidence | Consequence |
|------|----------|-------------|
| **`pages/Dashboard/AdminDashboard.tsx`** | Exists on disk; `grep -rn "AdminDashboard" src` finds it only in its own file. Never imported in `AppRouter.tsx`. `AdminRoute.tsx` guard exists in `src/context/` but is also never used anywhere. | Admin UI unreachable. Its API calls (`/admin/dashboard`, `/admin/system-health`) DO exist on backend and field names match (see §B3). |
| **Pricing page** | Only `components/landing/Pricing.tsx` (static marketing section on `/`). No route, no plan buttons wired to checkout. | Users cannot start a subscription from the app. |
| **Checkout flow** | `payments.py` has `POST /payments/create-checkout` returning `{checkout_url}`; NO frontend caller exists anywhere (`grep create-checkout frontend/src` = 0 hits). | Payment feature dead from UI. |
| **Payment success page** | No component, no route. Stripe `success_url` (payments.py) points at a frontend URL that doesn't exist in this build. | Post-payment redirect lands on 404. |
| **Payment history page** | None. `GET /payments/history` unused by frontend. | Dead endpoint from UI perspective. |
| **Subscription/cancel UI** | None. `GET /payments/subscription`, `POST /payments/cancel` unused. | Dead endpoints. |
| **Notifications UI** | Backend `notifications.py` fully implemented (list/unread-count/read/mark-all-read/delete). Frontend: `TopNavbar.tsx:132-144` renders a **hard-coded red dot** next to the Bell icon with no dropdown, no fetch, no click handler. | Notification badge is fake (F1). |
| **ForbiddenPage / ServerErrorPage** | Exist in `pages/Error/` but no routes reference them. | 403/500 pages unreachable. |
| **Profile page** | No dedicated route; profile editing lives inside SettingsPage. | Acceptable (documented). |

---

## 2. Route Protection Findings

- `ProtectedRoute.tsx` (lines 9–34): uses `useAuth()` → while `loading` renders text "Loading...", unauthenticated → `<Navigate to="/login" replace/>`. Applied to the entire `/dashboard` subtree (AppRouter lines 71–78). ✅ Real guard, not menu-hiding.
- Session restore: `AuthContext.restoreSession()` (AuthContext.tsx ~89–133) sets `api.defaults.headers.common.Authorization` from stored token then verifies via real `GET /users/me`; on failure clears storage. Refresh persists login correctly. ✅
- `isAuthenticated = Boolean(token && user)` — both required. ✅
- **Admin authorization:** `context/AdminRoute.tsx` checks `user.is_superuser` client-side, and backend `admin.py` uses `Depends(get_current_admin_user)` (verified line 6/16 of admin.py) — so even without a frontend route, backend enforcement exists. But because no route mounts `AdminDashboard`, the whole admin surface is dead code. (R-NOT-ROUTES)
- **Logout** (AuthContext ~224–242): contains a COMMENTED-OUT `await api.post("/auth/logout")` inside try/catch that swallows nothing (nothing is called); effectively client-only logout — appropriate for stateless JWT, but the dead commented block is misleading (classify: DEBUG/DEAD CODE).
- **401 handling** is implemented **three times differently** (S1/S2/S3 below) — see §5.

---

## 3. User-Flow Trace Results (route → component → service → endpoint)

| Flow | Chain | Verdict |
|------|-------|---------|
| Login → Dashboard | LoginPage → `services/auth.login()` (form-urlencoded `username`/`password` → matches OAuth2 form expected by `auth.py` line 70) → AuthContext stores token, calls `/users/me` → navigate `/dashboard` | ✅ WORKS |
| Register → Login | RegisterPage → `register()` → AuthContext.register() auto-logins | ✅ WORKS |
| Forgot → Reset | ForgotPassword.tsx → `forgotPassword()` → `auth.py:104` (generic message; dev-mode extra `reset_token` field) → email link `{FRONTEND_URL}/reset-password?token=...` (email.py:245 & auth.py:131) → ResetPasswordPage reads `searchParams.get("token")` → `POST /auth/reset-password {token,new_password}` | ✅ CONTRACT MATCHES (query-param style). ⚠️ Error toast on ForgotPassword uses `error.message` (will show "Request failed with status code 4xx" instead of backend `detail`) |
| Dashboard → Dataset → Analysis | DashBoardPage → `GET dashboard` (⚠️ no leading slash — axios resolves relative to baseURL `…/api/v1` dropping last segment when no trailing slash; risk R-PATH) ; DatasetsPage → `GET /datasets`; AnalysisPage → `GET /analysis/:datasetId` | ✅ mostly; verify `getDashboard("dashboard")` path quirk in Stage 3 |
| Dataset → AI Chat | AIChatPage → `services/chat.ts` → `/chat/{id}/sessions`, `/chat/sessions/{id}`, `/chat/{id}` | ✅ paths/methods/bodies all match `chat.py` (verified line-by-line). NOT broken as previously claimed (see §B2 correction) |
| Dataset → Report | ReportsPage → `GET /reports` ❌ vs backend `@router.get("/")` mounted at `/reports` → FastAPI issues 307 to `/reports/` (browser axios follows it fine, but blob responseType + redirect works; still a contract mismatch worth fixing) ; ReportButton → `GET /analysis/{id}/report` (exists, analysis.py:85) ✅ ; dataset.ts `downloadAnalysisReport` → `GET /reports/{id}/pdf` ✅ | ⚠️ R1 trailing-slash |
| Profile update | SettingsPage → `updateProfile()` PATCH `/users/me` ✅ | ✅ |
| Profile picture upload | `uploadProfilePicture()` POST `/users/me/profile-picture` with **manual header** `"Content-Type": "multipart/form-data"` (auth.ts:262) → browser can't append boundary → FastAPI `UploadFile = File(None)` receives no file → 422/validation failure | ❌ REAL BUG (B5 CONFIRMED) |
| Settings → Change password | `changePassword()` POST `/users/me/change-password {current_password,new_password}` ✅ matches users.py:273 | ✅ |
| Notifications | No frontend chain exists at all. Badge is static. | ❌ FEATURE MISSING IN FRONTEND |
| Subscription → Checkout → Success | No frontend chain exists (pages absent). Backend endpoints exist but under **double prefix** (see §B1). | ❌ DEAD |
| Payment history | No frontend chain. | ❌ DEAD |
| Admin dashboard | Component exists but unrouted; if routed, stats fields would match current backend schema (see §B3 correction). | ❌ UNREACHABLE |

---

## 4. Stage 1 Defect Verification (B1–B6, JWT refresh)

### B1 — Payments double prefix: **CONFIRMED**
Evidence: `backend/app/api/api.py:78-82` mounts `payments.router` with `prefix="/payments"`, while `payments.py` declares routes as `@router.get("/plans")` … etc. Actual OpenAPI paths therefore are `/api/v1/payments/plans`, `/api/v1/payments/create-checkout`, `/api/v1/payments/webhook`, `/api/v1/payments/subscription`, `/api/v1/payments/cancel`, `/api/v1/payments/history`, `/api/v1/payments/success`.
Correction to Stage 1 wording: the *backend* URLs are single-prefixed and sane. The Stage-1-era frontend `payments.ts` that called `/payments/payments/...` **does not exist in this repo state**; there is currently **zero** frontend payment integration. Required fix for Stage 3 is therefore: (a) keep backend paths as-is, (b) CREATE the missing pricing/checkout/success/history frontend pages calling the exact paths above — do not invent different ones.

### B2 — AI Chat: **Stage 1 finding REJECTED / CORRECTED**
Backend chat endpoints DO exist: `backend/app/api/v1/endpoints/chat.py` implements `GET/POST /{dataset_id}/sessions`, `GET/DELETE /sessions/{session_id}`, `POST /{dataset_id}` (mounted at `/api/v1/chat`). Frontend `services/chat.ts` matches every method/path/body/response type. `AIChatPage.tsx` contains **no localStorage fallback** (grep for `localStorage` in AIChatPage = 0 hits; messages come from API responses only). The earlier claim of "missing ai.py / localStorage pretending persistence" does not hold in this repository state. Remaining gap: Ollama availability handling inside chat service should be exercised in tests (Phase 13 scope, not Stage 2).

### B3 — Admin stats shape: **CORRECTED**
Actual backend schema `app/schemas/admin.py:11-18` returns FLAT fields `total_users, active_users, total_datasets, total_analyses, total_reports, total_chat_messages, avg_quality_score`. `AdminDashboard.tsx` reads exactly `stats?.total_users`, `stats?.active_users`, `stats?.total_datasets`, `stats?.avg_quality_score` → **fields match**. The Stage-1 "nested vs flat mismatch" cannot be reproduced against this code state. The real defect here is that the page is **never routed** (§1 orphans) and uses `useState<any>` twice (TypeScript weakness, not runtime bug).

### B4 — Pagination param: **NOT REPRODUCIBLE in this state**
`dataset.py` list route accepts `page: int = Query(1)`, `page_size: int = Query(10, ge=1, le=100)` — i.e., backend's parameter IS named `page_size`. The only frontend list caller `getDatasets(params)` passes through a typed `DatasetQuery` object; no caller sends a bogus `limit`/`page_size=100` mismatch in this state (the old `admin.ts getDatasets(pageSize=100)` file doesn't exist). Verdict: contract currently consistent; re-verify after admin routing is added.

### B5 — Profile picture Content-Type: **CONFIRMED REAL BUG**
`services/auth.ts:247-265`: FormData + explicit `"Content-Type": "multipart/form-data"` (no boundary). Axios/browser must generate the boundary; overriding breaks it → backend `upload_profile_picture(file: Optional[UploadFile] = File(None))` will not parse the file. Fix: delete the manual header.

### B6 — Success-page `message` vs `detail`: **CANNOT VERIFY (file absent)**
No SuccessPage exists in this state. Generalized replacement finding: **LoginPage.tsx:91-92** reads `response.data.message` as a fallback although FastAPI always returns `detail` → harmless-but-dead branch (classify FALSE POSITIVE-ish/dead code). **ForgotPassword.tsx:38** surfaces `error.message` (axios generic) instead of backend `detail` → user sees "Request failed with status code 422" style text (REAL minor UX bug E2).

### JWT refresh: **NO refresh logic exists in this state**
`grep -rn "refresh" frontend/src` → zero hits in interceptors/services. Both `services/api.ts` and `lib/api.ts` respond to 401 by clearing `access_token` and hard-redirecting to `/login`. There is no `/auth/refresh` attempt anywhere, so the Stage-1 concern about a failing refresh path applies only to the (absent) newer code state. Documented for regression awareness in Stage 3.

---

## 5. Axios Instance Sprawl (new systemic finding S-C1)

Four separate axios instances coexist:
1. `src/services/api.ts` — baseURL env-or-fallback, timeout 30s, 401 → removes token+user, skips redirect on `/login`,`/register`,`/forgot-password`. Used by `services/auth.ts`, `context/AuthContext.tsx`, `pages/Dashboard/AdminDashboard.tsx`.
2. `src/lib/api.ts` — baseURL env-or-fallback, timeout 120s, 401 → removes token ONLY (keeps `user` key), redirects unless already on `/login`. Used by `services/chat.ts`, `dataset.ts`, `analysis.ts`, `dashboard.ts`, `report.ts`, `ReportButton.tsx`.
3. `src/lib/axios.ts` — baseURL = `import.meta.env.VITE_API_URL` **with NO fallback** (if `.env` missing → requests go to relative `/undefined`-style bad URLs / same-origin). Used by `ResetPasswordPage`.
4. `src/api/axios.ts` (+ `src/api/*.api.ts`) — **all four files are 0 bytes** (verified `wc -c` = 0). Empty scaffolding committed.

Consequences: inconsistent 401 cleanup (instance 2 leaks stale `user` in localStorage), inconsistent timeouts, three places to maintain auth headers. Stage 3 should consolidate to ONE instance (keep `services/api.ts` semantics + 120s override per-call where needed) and delete `src/api/` stubs.

---

## 6. Placeholder / Fake-Behavior Search (actual commands run)

```
grep -rniE "todo|fixme" frontend/src --include=*.ts --include=*.tsx        → 0 matches
grep -rniE "mock|dummy|fake|hardcod|sampledata|testdata|exampledata|staticdata" → 0 matches
grep -rniE "coming soon|not implemented|placeholder"                        → only HTML input placeholder attrs (false positives)
grep -rn "console.log"                                                      → 2 matches
grep -rn "alert\(|window.alert"                                             → 3 matches
grep -rn "setTimeout("                                                      → 3 matches
grep -rn "setInterval("                                                     → 0 matches
grep -rn "localStorage"                                                     → storage.ts(7), SettingsPage(6), api.ts(3), lib/api.ts(2), ThemeContext(2)
```

### Classification table (every meaningful match)

| ID | File:Line | Snippet | Classification | Notes / Required action |
|----|-----------|---------|----------------|--------------------------|
| D1 | UploadDatasetPage.tsx:149 | `console.log("Starting upload…", name, size)` | DEBUG CODE | Remove in Stage 3 |
| D2 | UploadDatasetPage.tsx:153 | `console.log("UPLOAD RESPONSE:", response)` | DEBUG CODE | Remove |
| A1 | components/analysis/ReportButton.tsx:61 | `alert("Failed to generate the report…")` | PRODUCTION BUG (wrong UX primitive; project has sonner via `lib/toast`) | Replace with `showError` |
| A2 | components/datasets/DatasetTable.tsx:188 | `alert("Failed to delete dataset.")` | PRODUCTION BUG | Replace with `showError` |
| A3 | components/datasets/DatasetTable.tsx:213 | `alert("Failed to rename dataset.")` | PRODUCTION BUG | Replace with `showError` |
| T1 | ReportsPage.tsx:89 | `setTimeout(() => revokeObjectURL(url), 60000)` | LEGITIMATE (blob lifetime for window.open preview) | Keep |
| T2 | UploadDatasetPage.tsx:161 | `setTimeout(() => navigate("/dashboard/datasets"), 1000)` | LEGITIMATE UI delay AFTER awaited API success | Keep (could use smaller delay; not fake backend) |
| T3 | hooks/useDatasets.ts:18 | `setTimeout(loadDatasets, 400)` keyed on `[search]` | LEGITIMATE debounce | Keep |
| F1 | TopNavbar.tsx:132-144 | Bell icon + hard-coded red dot span, no handler/fetch | FAKE/MOCK BEHAVIOR (notification badge pretends unread state) | Wire to `GET /notifications/unread-count` + dropdown (Phase 9 feature work — flagged, out of Stage 3 minimal scope decision) |
| M1 | SettingsPage.tsx:70-72,215-223 | `emailNotifications` / `datasetAlerts` / `weeklyReports` toggles persisted to localStorage only | LOCALSTORAGE PRETENDING PERSISTENCE (no backend settings API exists) | Requires product decision: add backend user-settings OR document as device-local preference |
| L1 | AuthContext.tsx ~229 | commented-out `await api.post("/auth/logout")` + catch that can never fire | DEAD CODE | Clean up |
| C1 | src/api/*.ts (4 files) | 0-byte committed modules | DEAD SCAFFOLDING | Delete or implement |
| K1 | 25 × `console.error/warn` | e.g. AuthContext:69, AIChatPage:143…, AdminDashboard:19 | MOSTLY LEGITIMATE error logging paired with user-facing handling | Keep; remove only where duplicated with toast suppression; none log tokens/passwords (spot-checked) |
| P1 | "placeholder=" attributes (~20 files) | HTML input placeholders | FALSE POSITIVE | Ignore |

### Hardcoded data scan
No hardcoded arrays representing datasets/notifications/payments/users/stats found in existing components (the only static content is legitimate marketing copy in `components/landing/*` incl. Pricing card prices which are display-only duplicates of backend plan config — flag: ensure they stay in sync with `payments.py` plans when checkout UI is built).

---

## 7. Error-Handling Findings

| ID | Location | Problem | Severity |
|----|----------|---------|----------|
| E1 | LoginPage.tsx:91-92 | Reads `data.message` fallback that backend never sends (FastAPI uses `detail`) — dead branch, masks nothing but confuses future edits | LOW |
| E2 | ForgotPassword.tsx:38 | Shows `error.message` (axios technical string) instead of extracting `error.response.data.detail` → raw technical error exposed to users | MED |
| E3 | AdminDashboard.tsx:18-20 | `catch { console.error }` then renders with `stats=null` → blank metrics silently; no retry, no visible error | MED (page unrouted today) |
| E4 | lib/api.ts 401 handler | Removes `access_token` but NOT `user` (services/api.ts removes both) → divergent stale-state behavior between instances | MED |
| E5 | AIChatPage.tsx:446-455 | Catches all chat errors into one generic sentence; loses 404-vs-503(Ollama down) distinction | LOW-MED |
| E6 | dataset.ts download helpers | Blob error bodies: if server returns JSON error with `responseType:'blob'`, `err.response.data` is a Blob — no code converts it back to readable `detail` | MED |
| E7 | useDatasets.ts:35 | `catch { setError("Failed to load datasets.") }` discards cause entirely (no console trace) | LOW |
| E8 | SettingsPage change-password flow | Relies on services/api.ts global 401 redirect; a wrong-current-password 401 from `/users/me/change-password` would **log the user out and redirect to /login** instead of showing "Current password incorrect" | HIGH — verify backend status code in Stage 3; likely needs 400 instead of 401 for wrong current password (backend-side check) |

---

## 8. Exact Files Requiring Changes (Stage 3 backlog)

Frontend: `services/auth.ts` (B5 header removal), `services/api.ts`+`lib/api.ts`+`lib/axios.ts` (consolidation S-C1, E4), `src/api/*` (delete C1), `pages/Auth/ForgotPassword.tsx` (E2), `pages/Auth/LoginPage.tsx` (E1), `components/analysis/ReportButton.tsx` (A1), `components/datasets/DatasetTable.tsx` (A2,A3), `pages/Dashboard/UploadDatasetPage.tsx` (D1,D2), `routes/AppRouter.tsx` (admin route + payment routes when built), `context/AuthContext.tsx` (L1), `components/dashboard/TopNavbar.tsx` (F1), `pages/Dashboard/SettingsPage.tsx` (M1 decision), `services/report.ts`/`dataset.ts` (R1/E6).
Backend (minimal, contract-driven only): possible change-password 401→400 semantics (E8), reports route trailing-slash normalization (R1).

## 9. Prioritized Fix List for Stage 3

1. **P0** B5 profile-picture multipart header (breaks a shipped feature).
2. **P0** E8 change-password 401 trap (locks users out mid-settings).
3. **P1** Axios instance consolidation + uniform 401 cleanup (S-C1/E4).
4. **P1** Alert→toast (A1-A3), debug log removal (D1-D2), error-detail extraction (E2/E6).
5. **P1** Reports trailing slash (R1) + delete dead `src/api` stubs (C1).
6. **P2** Route AdminDashboard behind AdminRoute guard; replace `any` types (B3 residual).
7. **P2** Wire notification bell to `/notifications/unread-count` (F1) — coordinate with Phase 9.
8. **P2** Build pricing→checkout→success→history pages against verified `/api/v1/payments/*` paths (B1) — coordinate with Phase 7/8 acceptance.
9. **P3** M1 settings persistence decision; E7/E5 error granularity; L1 dead code.

---

**Commands actually executed during Stage 2:** `cat`/`sed`/`head`/`wc -c` on AppRouter.tsx, ProtectedRoute.tsx, AdminRoute.tsx, main.tsx, services/{api,auth,chat,dataset,dashboard,report}.ts, lib/{api,axios}.ts, pages Auth/{ForgotPassword,ResetPasswordPage,LoginPage}, Dashboard/{AIChatPage,AdminDashboard,SettingsPage,UploadDatasetPage,ReportsPage}, hooks/useDatasets.ts, components TopNavbar/ReportButton/DatasetTable; `git status --short`, `git log --oneline`, `git ls-files`; `grep` inventories of axios/localStorage/console/alert/setTimeout/todo/mock/placeholder across `frontend/src`; backend route greps of `api/api.py`, `endpoints/{payments,chat,admin,notifications,dataset,analysis,auth,users,reports,cleaning,dashboard}.py`, `schemas/admin.py`; verification of reset URL construction in `auth.py`/`email.py` and `frontend/.env`.

STAGE 2 COMPLETE
