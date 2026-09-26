# Authentication Repair

## Verified

| FEATURE | TEST | RESULT | NOTES |
|---|---|---|---|
| Registration | `tests/test_auth.py::TestRegister` | PASS | Covers successful registration, duplicate email, malformed email, missing fields, password policy, and bcrypt hashing. |
| Login | `tests/test_auth.py::TestLogin`; inactive-account regression test | PASS | Covers valid login, wrong password, unknown account, expired JWT, and rejection of inactive users. |
| Current-user/profile loading | `tests/test_auth.py::TestCurrentUser` | PASS | Verifies valid bearer authentication and rejects absent, malformed, expired, deleted-user, and inactive-user credentials. |
| JWT expiration and API 401 behavior | `tests/test_auth.py::TestCurrentUser`; `tests/test_auth_security.py` | PASS | API tests verify malformed, expired, wrong-signature, malformed-subject, and inactive-user tokens are rejected with 401. Frontend redirect behavior remains unverified in a browser. |
| Protected resources | `tests/test_auth.py::TestCurrentUser`; `tests/test_auth_security.py` | PASS | Anonymous requests fail authentication; another user's dataset is hidden with 404; a non-admin gets 403. |
| Change password | `tests/test_auth.py::TestChangePassword` | PASS | Exercises the authenticated password update, previous-password rejection, and new-password login. |
| Forgot password | `tests/test_auth.py::TestForgotPassword`; security regression tests | PASS | Email delivery is mocked. Known and unknown addresses have the same response; no reset token is returned; delivery failure does not expose token/error text in logs. |
| Reset password | `tests/test_auth.py::TestResetPassword` | PASS | Covers successful update, malformed, forged, expired, wrong-type, and unknown-account tokens, plus password login using the new password. |
| End-to-end API journey | `tests/test_auth.py::test_end_to_end_auth_journey` | PASS | TestClient flow covers registration, login, protected current-user access, password change, unauthenticated access, forgot/reset, and login with the reset password. This is an API-level journey, not a browser journey. |
| Full backend suite with strict deprecation filter | `pytest -q -W error::DeprecationWarning` | PASS | 42 passed. One Starlette TestClient deprecation warning remains; it is not a `DeprecationWarning` caught by this command's filter. |
| Full backend suite | `pytest -q` | PASS | 42 passed; the same Starlette TestClient deprecation warning is reported. |
| Frontend static validation | `npm run lint`; `npm run build` | PASS | Lint reports zero errors (three existing Fast Refresh warnings). Production build succeeds with a large-chunk advisory. |
| Python compilation | `python -m compileall app alembic` (from `backend`) | PASS | Backend application and Alembic modules compile. |

## Failed

| FEATURE | TEST | RESULT | NOTES |
|---|---|---|---|
| Reset-token one-time use | No token-consumption/revocation mechanism exists | NOT SUPPORTED | Reset tokens are signed, type-bound, and expire, but a valid token is reusable until expiry. No one-time guarantee is claimed. |
| Server-side logout/revocation | No logout endpoint or JWT revocation store exists | NOT SUPPORTED | Logout clears frontend authentication state only. A copied bearer token remains usable until it expires. |

## Requires external service

| FEATURE | TEST | RESULT | NOTES |
|---|---|---|---|
| Production password-reset email | SMTP delivery | NOT RUN | Tests replace the mail sender with a stub. A configured SMTP service is required to verify delivery end-to-end. |

## Requires manual browser testing

| FEATURE | TEST | RESULT | NOTES |
|---|---|---|---|
| Browser authentication journey | Real browser with responsive API | NOT RUN | Verify registration, logout, login, protected-page access, refresh/session restoration, logout, forgot/reset, and new-password login. The current pytest journey exercises the API only; no live PostgreSQL-backed API was available for browser execution. |
| Browser 401 behavior | Expired-session response in a browser | NOT RUN | Verify stale auth storage is cleared and a protected page redirects to login without redirect loops. Axios interceptor behavior is not a substitute for browser execution; no live API was available. |

## Changes made

- Reject inactive users during password authentication.
- Make forgot-password responses indistinguishable for known and unknown addresses and keep reset tokens out of API responses.
- Avoid logging mail exception text that may include reset URLs/tokens.
- Reject malformed reset-token subjects.
- Clear stale frontend user state when no auth token exists; do not log Axios request errors that may contain bearer credentials.
- Route newly registered users to the dashboard after the existing auto-login flow.
- Replace deprecated Pydantic class-based model config in admin response schemas and deprecated naive UTC timestamp callables in the user and dataset models.
