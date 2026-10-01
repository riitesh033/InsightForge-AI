import { LogOut, ShieldCheck } from "lucide-react";
import { Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "@/hooks/useAuth";
import { getAdminLogoutDestination } from "@/context/adminAccess.js";

export default function AdminLayout() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate(getAdminLogoutDestination(), { replace: true });
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="flex min-h-16 flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 py-3 sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <ShieldCheck className="size-6 shrink-0 text-indigo-600" />
          <div className="min-w-0">
            <p className="font-semibold text-slate-900">InsightForge Admin</p>
            {user?.email && (
              <p className="max-w-[70vw] truncate text-xs text-slate-500">
                {user.email}
              </p>
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={() => void handleLogout()}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
        >
          <LogOut className="size-4" />
          Sign out
        </button>
      </header>
      <main className="min-w-0 p-3 sm:p-5 md:p-8">
        <Outlet />
      </main>
    </div>
  );
}
