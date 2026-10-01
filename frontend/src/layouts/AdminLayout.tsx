import { LogOut, ShieldCheck } from "lucide-react";
import { Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "@/hooks/useAuth";
import { getAdminLogoutDestination } from "@/context/adminAccess.js";
import ThemeToggle from "@/components/common/ThemeToggle";

export default function AdminLayout() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate(getAdminLogoutDestination(), { replace: true });
  }

  return (
    <div className="min-h-screen bg-background text-foreground transition-colors duration-200">
      <header className="flex min-h-16 flex-wrap items-center justify-between gap-3 border-b border-border bg-card px-3 py-3 text-card-foreground transition-colors duration-200 sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <ShieldCheck className="size-6 shrink-0 text-primary" />
          <div className="min-w-0">
            <p className="font-semibold text-foreground">InsightForge Admin</p>
            {user?.email && (
              <p className="max-w-[52vw] truncate text-xs text-muted-foreground sm:max-w-none">
                {user.email}
              </p>
            )}
          </div>
        </div>
        <div className="ml-auto flex shrink-0 items-center gap-1 sm:gap-2">
          <ThemeToggle />
          <button
            type="button"
            onClick={() => void handleLogout()}
            className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm font-medium text-foreground transition-colors duration-200 hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            <LogOut className="size-4" aria-hidden="true" />
            <span>Sign out</span>
          </button>
        </div>
      </header>
      <main className="min-w-0 p-3 transition-colors duration-200 sm:p-5 md:p-8">
        <Outlet />
      </main>
    </div>
  );
}
