import {
  Bell,
  Menu,
  Search,
} from "lucide-react";

import ThemeToggle from "@/components/common/ThemeToggle";

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

        {/* Avatar */}
        <button
          className="
            flex
            h-10
            w-10
            items-center
            justify-center
            rounded-full
            bg-primary
            font-semibold
            text-primary-foreground
          "
        >
          R
        </button>

      </div>

    </header>
  );
}