# Frontend API and Routing Repair

## API client dependency map

### Before consolidation

| API implementation | Files importing it | Observed behavior |
|---|---|---|
| `frontend/src/lib/api.ts` | `services/dataset.ts`, `services/analysis.ts`, `services/dashboard.ts`, `services/chat.ts`, `services/report.ts`, `components/analysis/ReportButton.tsx` | 120-second timeout, development base URL fallback, token interceptor; response 401 cleared only the access token and redirected unconditionally except on `/login`. |
| `frontend/src/services/api.ts` | `context/AuthContext.tsx`, `services/auth.ts`, `pages/Dashboard/AdminDashboard.tsx` | 30-second timeout, token and cached-user cleanup, excluded some public auth pages from redirect. |
| `frontend/src/lib/axios.ts` | `pages/Auth/ResetPasswordPage.tsx` | No base URL fallback; reset request used a relative URL on the bare Axios instance. |
| `frontend/src/api/` | No implementation or imports found. | No API client to migrate. |

### After consolidation

`frontend/src/lib/api.ts` is the sole Axios instance. It reads `VITE_API_URL`, trims trailing slashes, falls back to `http://localhost:8000/api/v1` in development and `/api/v1` in production when the variable is omitted, and has a 120-second timeout for dataset processing and report downloads. It attaches the current `access_token` on each request and handles non-authentication 401 responses centrally by clearing auth storage and returning an existing session to `/login`. Login/register/forgot/reset 401 responses stay on their public page.

The client sets `Accept` but does not force a request content type. Axios/the browser can therefore set the multipart boundary for `FormData`; JSON and URL-encoded requests continue to specify or infer their own format. Blob responses remain requested by the download callers. `getApiAssetUrl` resolves backend-hosted profile images against the configured API origin. `getApiErrorMessage` and `getApiErrorDetails` centralize typed error inspection without creating another client.

All API callers now use the canonical client: AuthContext, all frontend API services, report download button, admin dashboard, reset-password page, payment-success page, and profile-image/error helpers.

Removed `frontend/src/services/api.ts` and `frontend/src/lib/axios.ts` after migrating their importers and confirming no remaining source imports. A source search confirms only `frontend/src/lib/api.ts` contains `axios.create`.

Copy `frontend/.env.example` to `.env` for local development. Production should set `VITE_API_URL` to the backend API base (including `/api/v1`) when frontend and backend are on different origins; the same-origin `/api/v1` fallback assumes the production host proxies that path. This variable is a public API URL, not a secret.

## Route audit

| Route | Page | Access |
|---|---|---|
| `/` | Landing page | Public |
| `/login` | Login | Public |
| `/register` | Register | Public |
| `/forgot-password` | Forgot password | Public |
| `/reset-password?token=...` | Reset password; reads `token` query parameter | Public |
| `/dashboard` | Dashboard | Authenticated |
| `/dashboard/upload` | Dataset upload | Authenticated |
| `/dashboard/datasets` | Dataset list | Authenticated |
| `/dashboard/analysis/:datasetId` | Analysis; `datasetId` is parsed as a positive safe integer before API use | Authenticated |
| `/dashboard/reports` | Reports | Authenticated |
| `/dashboard/ai-chat/:datasetId?` and `/dashboard/ai-chat` | Dataset chat; an optional ID is validated and matched against the user's datasets | Authenticated |
| `/dashboard/billing` | Plan catalog and Stripe Checkout entry point | Authenticated |
| `/dashboard/subscription` | Current subscription and supported cancellation action | Authenticated |
| `/dashboard/payment-history` | User-scoped payment history | Authenticated |
| `/dashboard/settings` | Settings | Authenticated |
| `/admin` | Admin dashboard | Authenticated and requires `is_superuser`; unauthorized users go to `/forbidden` |
| `/payment-success?session_id=...` | Displays webhook-confirmed payment state; browser redirect does not activate a subscription | Authenticated |
| `/payment-cancelled` | Checkout-canceled message; no subscription is activated | Authenticated |
| `/forbidden`, `/403` | Forbidden page | Public |
| `/server-error`, `/500` | Server-error page | Public |
| `/pricing` | Redirect to `/#pricing` | Public |
| `/demo` | Redirect to `/` | Public |
| `*` | Not-found page | Public |

Dashboard, payment-success, and payment-cancelled routes remain wrapped by `ProtectedRoute`; admin routes add the `AdminRoute` check. The payment flow and latest build validation are documented in [PAYMENT_REPAIR.md](./PAYMENT_REPAIR.md). The Vite production preview was tested by direct navigation to dashboard subpaths, admin, auth, error, pricing, payment-success, and an unknown path. The SPA fallback served the built application on refresh/direct requests. In production, the web server must likewise rewrite application paths to `index.html`.

## Frontend-to-backend API contract audit

All paths below are relative to the canonical base URL `/api/v1`. Method, URL and payloads were compared to the corresponding FastAPI endpoints.

| Frontend caller | Method and path | Contract result |
|---|---|---|
| Auth service | `POST /auth/login` (URL-encoded username/password), `POST /auth/register` (JSON), `POST /auth/forgot-password` (JSON), `POST /auth/reset-password` (JSON) | Match existing auth routes. |
| Auth service / AuthContext | `GET /users/me`, `PATCH /users/me`, `POST /users/me/change-password`, `POST /users/me/profile-picture` (multipart `file`), `POST /users/me/avatar` (`avatar_id` query), `DELETE /users/me/profile-picture`, `DELETE /users/me` | Match user routes and methods. |
| Dataset service | `GET /datasets` (page/search/sort query), `POST /datasets/upload` (multipart `file`), `PATCH /datasets/{id}` (JSON `original_filename`), `DELETE /datasets/{id}`, `GET /datasets/{id}/download` | Match dataset routes. Removed the unsupported `format` query from downloads; original downloads use the server's attachment filename when exposed and a file-type-aware fallback otherwise. |
| Analysis service | `GET /analysis/{datasetId}` | Match analysis response route. Route ID is validated before this call. |
| Report button | `GET /analysis/{datasetId}/report` with `responseType: "blob"` | Match the existing analysis PDF route. |
| Report service | `GET /reports`, `GET /reports/{datasetId}/pdf` with `responseType: "blob"` | Match report list and PDF routes. |
| Cleaning service | `POST /cleaning/{datasetId}/preview`, `POST /cleaning/{datasetId}/apply`, `GET /cleaning/{datasetId}/download` with `responseType: "blob"` | Match cleaning routes. Removed the unsupported `format` query; the selector now permits the cleaned output extension produced by the backend (CSV stays CSV; XLS/XLSX produce XLSX). |
| Dashboard service | `GET /dashboard` | Match dashboard router path. |
| Chat service | `GET /chat/{datasetId}/sessions`, `POST /chat/{datasetId}/sessions`, `GET /chat/sessions/{sessionId}`, `DELETE /chat/sessions/{sessionId}`, `POST /chat/{datasetId}` with JSON message/session ID | Match chat route methods and payloads. |
| Admin dashboard | `GET /admin/dashboard`, `GET /admin/system-health` | Match admin routes; both remain behind the client-side admin guard and server-side admin dependency. |
| Public pricing and dashboard billing | `GET /payments/plans`; authenticated `POST /payments/create-checkout?plan_type=...` | Matches the plans and checkout routes; pricing and billing share the same API-backed plan catalog. Plan loading times out after 15 seconds with a retry action; checkout sends the plan in the query string and redirects to Stripe's returned hosted URL. Paid-plan selections resume after login/registration. |
| Payment-success page | `GET /payments/success?session_id=...` | Matches the backend route. It is read-only and polls for webhook-confirmed subscription state. |
| Subscription page | `GET /payments/subscription`, `POST /payments/cancel` | Matches current-subscription and cancellation-request routes. Local subscription state updates after Stripe's webhook. |
| Payment history page | `GET /payments/history` | Matches the user-scoped payment-history route. |
| Stripe webhook | `POST /payments/webhook` | Server-to-server only; not called by frontend code. Signature/idempotency processing is documented in [PAYMENT_REPAIR.md](./PAYMENT_REPAIR.md). |

The payment router prefix is applied once by the backend API aggregator; the frontend uses `/payments/...`, not a duplicated prefix. The Stripe cancellation return now uses `/payment-cancelled` rather than `/pricing`.

The cleaning backend does not accept a requested output-format query and emits the cleaned file using its existing source-format behavior. The frontend no longer sends a format parameter it cannot honor and prevents selecting an output format the backend will not produce. It does not add server-side conversion behavior.

## Validation

Executed from `frontend`:

```powershell
npm run build
npm run lint
```

- `npm run build`: passed (`tsc -b` and Vite production build).
- `npm run lint`: passed with **0 errors**. Three existing Fast Refresh warnings remain in the UI button module and Auth/Theme contexts.
- Vite emitted its existing warning that the main minified JavaScript chunk exceeds 500 kB; this does not fail the build.
- Production preview direct-navigation smoke checks returned HTTP 200 for auth/dashboard/admin/payment/error paths and unknown paths. Browser checks confirmed an unauthenticated `/admin` request redirects to `/login`, `/forbidden` renders the 403 page, `/server-error` renders the 500 page, and an unknown path renders the 404 page.
