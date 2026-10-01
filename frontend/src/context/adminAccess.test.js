import assert from "node:assert/strict";
import test from "node:test";

import { getAdminRouteAccess } from "./adminAccess.js";

test("allows the admin route only for an authenticated superuser", () => {
  assert.equal(
    getAdminRouteAccess({ id: 10, is_superuser: true }),
    "allowed"
  );
  assert.equal(
    getAdminRouteAccess({ id: 11, is_superuser: false }),
    "forbidden"
  );
  assert.equal(
    getAdminRouteAccess({ id: 12 }),
    "forbidden"
  );
  assert.equal(getAdminRouteAccess(null), "forbidden");
});
