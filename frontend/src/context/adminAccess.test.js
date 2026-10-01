import assert from "node:assert/strict";
import test from "node:test";

import {
  getAdminLogoutDestination,
  getAdminRouteAccess,
} from "./adminAccess.js";

test("admin route redirects unauthenticated users to admin login", () => {
  assert.equal(
    getAdminRouteAccess({ loading: false, user: null }),
    "admin-login"
  );
});

test("admin route allows superusers and denies normal users", () => {
  assert.equal(
    getAdminRouteAccess({
      loading: false,
      user: { id: 10, is_superuser: true },
    }),
    "allowed"
  );
  assert.equal(
    getAdminRouteAccess({
      loading: false,
      user: { id: 11, is_superuser: false },
    }),
    "forbidden"
  );
  assert.equal(
    getAdminRouteAccess({
      loading: false,
      user: { id: 12 },
    }),
    "forbidden"
  );
});

test("admin route waits for server-backed session restoration", () => {
  assert.equal(
    getAdminRouteAccess({ loading: true, user: null }),
    "loading"
  );
});

test("admin logout returns to the dedicated login route", () => {
  assert.equal(getAdminLogoutDestination(), "/admin/login");
});

test("admin logout clears the shared application token and user storage", async () => {
  const { clearAuthSession } = await import("../utils/authSession.js");
  const removedKeys = [];
  clearAuthSession({
    removeItem: (key) => removedKeys.push(key),
  });
  assert.deepEqual(removedKeys, ["access_token", "user"]);
});
