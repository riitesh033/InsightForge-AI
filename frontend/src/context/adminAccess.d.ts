export function getAdminRouteAccess(
  auth: {
    loading: boolean;
    user: { is_superuser?: boolean } | null;
  }
): "loading" | "admin-login" | "forbidden" | "allowed";

export function getAdminLogoutDestination(): string;
