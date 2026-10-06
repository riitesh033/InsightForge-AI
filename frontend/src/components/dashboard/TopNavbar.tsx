import {
  Menu,
  Search,
  User as UserIcon,
  Settings,
  CreditCard,
  LogOut,
} from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import ThemeToggle from "@/components/common/ThemeToggle";
import { useAuth } from "@/hooks/useAuth";
import { getApiAssetUrl } from "@/lib/api";
import { showSuccess } from "@/lib/toast";
import NotificationMenu from "@/components/dashboard/NotificationMenu";

interface TopNavbarProps {
  title?: string;
  subtitle?: string;
  onMenuClick?: () => void;
}

export default function TopNavbar({
  title = "Dashboard",
  subtitle = "Welcome to InsightForge AI",
  onMenuClick,
}: TopNavbarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showUserMenu, setShowUserMenu] = useState(false);

  // Get profile picture URL
  function getProfilePictureUrl() {
    if (!user?.profile_picture) return null;

    if (user.profile_picture.startsWith("builtin:")) {
      const avatarId = user.profile_picture.replace("builtin:", "");
      return `/avatars/${avatarId}.svg`;
    }

    return getApiAssetUrl(user.profile_picture);
  }

  async function handleLogout() {
    await logout();
    showSuccess("Logged out successfully.");
    navigate("/login");
  }

  function handleMenuItemClick(callback: () => void) {
    setShowUserMenu(false);
    callback();
  }

  return (
    <header className="sticky top-0 z-30 flex h-20 items-center justify-between border-b border-slate-200 bg-white/90 px-3 backdrop-blur-xl transition-colors duration-300 dark:border-white/10 dark:bg-slate-950/80 sm:px-4 md:px-6">
      <div className="flex min-w-0 items-center gap-2 sm:gap-4">
        <button
          type="button"
          aria-label="Open navigation menu"
          onClick={onMenuClick}
          className="rounded-xl border border-slate-200 bg-slate-50 p-2 text-slate-700 transition hover:border-indigo-400/40 hover:text-indigo-700 dark:border-white/10 dark:bg-slate-900/80 dark:text-slate-200 dark:hover:text-white lg:hidden"
        >
          <Menu size={20} />
        </button>

        <div className="min-w-0">
          <h1 className="truncate text-lg font-semibold text-slate-900 dark:text-white sm:text-2xl">
            {title}
          </h1>
          <p className="hidden truncate text-sm text-slate-500 dark:text-slate-400 sm:block">
            {subtitle}
          </p>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-2 sm:gap-3 md:gap-4">
        <div className="relative hidden md:block">
          <Search
            size={17}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
          />

          <input
            placeholder="Search..."
            className="w-32 rounded-xl border border-slate-200 bg-white py-2.5 pl-10 pr-4 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-400/60 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 dark:border-white/10 dark:bg-slate-900/70 dark:text-white dark:placeholder:text-slate-400 sm:w-40 lg:w-48 xl:w-72"
          />
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-1.5 text-slate-700 dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-200">
          <ThemeToggle />
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-1.5 text-slate-700 dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-200">
          <NotificationMenu />
        </div>

        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 p-1 pr-3 transition hover:border-indigo-400/40 hover:bg-slate-100 dark:border-white/10 dark:bg-slate-900/70 dark:hover:bg-slate-900"
          >
            {getProfilePictureUrl() ? (
              <img
                src={getProfilePictureUrl()!}
                alt={user?.full_name?.[0]?.toUpperCase() || "U"}
                className="h-9 w-9 rounded-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = "/avatars/avatar_01.svg";
                }}
              />
            ) : (
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-500 text-sm font-semibold text-white">
                {user?.full_name?.[0]?.toUpperCase() || "U"}
              </div>
            )}
            <span className="hidden text-sm font-medium text-slate-800 dark:text-slate-100 lg:block">
              {user?.full_name || "User"}
            </span>
          </button>

          {showUserMenu && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setShowUserMenu(false)}
              />

              <div className="absolute right-0 top-full z-50 mt-2 w-56 rounded-2xl border border-slate-200 bg-white py-2 shadow-2xl shadow-slate-950/20 backdrop-blur-xl dark:border-white/10 dark:bg-slate-900/95 dark:shadow-slate-950/80">
                <div className="border-b border-slate-200 px-4 pb-3 pt-2 dark:border-white/10">
                  <p className="truncate text-sm font-semibold text-slate-900 dark:text-white">
                    {user?.full_name}
                  </p>
                  <p className="truncate text-xs text-slate-500 dark:text-slate-400">
                    {user?.email}
                  </p>
                </div>

                <div className="py-2">
                  <button
                    onClick={() => handleMenuItemClick(() => navigate("/dashboard/settings"))}
                    className="flex w-full items-center gap-3 px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-white/5 dark:hover:text-white"
                  >
                    <UserIcon size={16} />
                    Profile
                  </button>

                  <button
                    onClick={() => handleMenuItemClick(() => navigate("/dashboard/settings"))}
                    className="flex w-full items-center gap-3 px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-white/5 dark:hover:text-white"
                  >
                    <Settings size={16} />
                    Settings
                  </button>

                  <button
                    onClick={() =>
                      handleMenuItemClick(() => navigate("/dashboard/billing"))
                    }
                    className="flex w-full items-center gap-3 px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-white/5 dark:hover:text-white"
                  >
                    <CreditCard size={16} />
                    Plan & Billing
                  </button>
                </div>

                <div className="border-t border-slate-200 pt-2 dark:border-white/10">
                  <button
                    onClick={() => handleMenuItemClick(handleLogout)}
                    className="flex w-full items-center gap-3 px-4 py-2 text-left text-sm text-red-300 hover:bg-red-500/10"
                  >
                    <LogOut size={16} />
                    Logout
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}