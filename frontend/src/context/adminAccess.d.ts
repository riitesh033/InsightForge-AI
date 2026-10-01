export function getAdminRouteAccess(
  user: { is_superuser?: boolean } | null
): "allowed" | "forbidden";
