/**
 * @param {{ is_superuser?: boolean } | null} user
 * @returns {"allowed" | "forbidden"}
 */
export function getAdminRouteAccess(user) {
  if (!user) {
    return "forbidden";
  }

  return user.is_superuser === true ? "allowed" : "forbidden";
}
