import {
  Bell,
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
import { showSuccess } from "@/lib/toast";

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

    return `${import.meta.env.VITE_API_BASE_URL || "/api/v1"}${user.profile_picture}`;
  }

  async function handleLogout() {
    try {
      await logout();
      showSuccess("Logged out successfully.");
      navigate("/login");
    } catch (error) {
      navigate("/login");
    }
  }

  function handleMenuItemClick(callback: () => void) {
    setShowUserMenu(false);
    callback();
  }

  return (
    <header className="sticky top-0 z-30 flex h-20 items-center justify-between border-b border-border bg-card/95 px-6 backdrop-blur">

      {/* Left */}
      <div className="flex items-center gap-4">

        {/* Mobile Menu */}
        <button
          onClick={onMenuClick}
          className="rounded-lg p-2 transition hover:bg-accent lg:hidden"
        >
          <Menu size={22} />
        </button>

        <div>

          <h1 className="text-2xl font-bold text-foreground">
            {title}
          </h1>

          <p className="text-sm text-muted-foreground">
            {subtitle}
          </p>

        </div>

      </div>

      {/* Right */}
      <div className="flex items-center gap-4">

        {/* Search */}
        <div className="relative hidden md:block">

          <Search
            size={18}
            className="absolute left-3 top-3 text-muted-foreground"
          />

          <input
            placeholder="Search..."
            className="
              w-72
              rounded-lg
              border
              border-border
              bg-background
              py-2.5
              pl-10
              pr-4
              text-sm
              text-foreground
              placeholder:text-muted-foreground
              focus:border-primary
              focus:outline-none
            "
          />

        </div>

        {/* Theme */}
        <ThemeToggle />

        {/* Notifications */}
        <button
          className="
            relative
            rounded-lg
            p-2
            transition
            hover:bg-accent
          "
        >
          <Bell size={21} />

          <span
            className="
              absolute
              right-2
              top-2
              h-2
              w-2
              rounded-full
              bg-red-500
            "
          />
        </button>

        {/* Avatar with Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 rounded-full bg-primary/10 p-1 pr-3 transition hover:bg-primary/20"
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
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-primary-foreground">
                {user?.full_name?.[0]?.toUpperCase() || "U"}
              </div>
            )}
            <span className="hidden text-sm font-medium text-foreground lg:block">
              {user?.full_name || "User"}
            </span>
          </button>

          {/* Dropdown Menu */}
          {showUserMenu && (
            <>
              {/* Backdrop */}
              <div
                className="fixed inset-0 z-40"
                onClick={() => setShowUserMenu(false)}
              />

              {/* Menu */}
              <div className="absolute right-0 top-full mt-2 w-56 rounded-xl border border-border bg-card py-2 shadow-lg z-50">
                
                {/* User Info */}
                <div className="border-b border-border px-4 pb-3">
                  <p className="truncate text-sm font-semibold text-foreground">
                    {user?.full_name}
                  </p>
                  <p className="truncate text-xs text-muted-foreground">
                    {user?.email}
                  </p>
                </div>

                {/* Menu Items */}
                <div className="py-2">
                  <button
                    onClick={() => handleMenuItemClick(() => navigate("/dashboard/settings"))}
                    className="flex w-full items-center gap-3 px-4 py-2 text-left text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  >
                    <UserIcon size={16} />
                    Profile
                  </button>

                  <button
                    onClick={() => handleMenuItemClick(() => navigate("/dashboard/settings"))}
                    className="flex w-full items-center gap-3 px-4 py-2 text-left text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  >
                    <Settings size={16} />
                    Settings
                  </button>

                  <button
                    onClick={() => handleMenuItemClick(() => navigate("/pricing"))}
                    className="flex w-full items-center gap-3 px-4 py-2 text-left text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  >
                    <CreditCard size={16} />
                    Plan & Billing
                  </button>
                </div>

                {/* Logout */}
                <div className="border-t border-border pt-2">
                  <button
                    onClick={() => handleMenuItemClick(handleLogout)}
                    className="flex w-full items-center gap-3 px-4 py-2 text-left text-sm text-destructive hover:bg-destructive/10"
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