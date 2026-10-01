/**
 * @param {{ loading: boolean, user: { is_superuser?: boolean } | null }} auth
 * @returns {"loading" | "admin-login" | "forbidden" | "allowed"}
 */
export function getAdminRouteAccess({ loading, user }) {
  if (loading) {
    return "loading";
  }
  if (!user) {
    return "admin-login";
  }

  return user.is_superuser === true ? "allowed" : "forbidden";
}

export function getAdminLogoutDestination() {
  return "/admin/login";
}
