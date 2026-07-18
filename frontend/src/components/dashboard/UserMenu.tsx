import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Upload,
  Database,
  FileText,
  MessageSquare,
  Settings,
  LogOut,
  BarChart3,
} from "lucide-react";

const navigation = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Upload Dataset",
    href: "/dashboard/upload",
    icon: Upload,
  },
  {
    name: "Datasets",
    href: "/dashboard/datasets",
    icon: Database,
  },
  {
    name: "Reports",
    href: "/dashboard/reports",
    icon: FileText,
  },
  {
    name: "AI Chat",
    href: "/dashboard/ai-chat",
    icon: MessageSquare,
  },
  {
    name: "Settings",
    href: "/dashboard/settings",
    icon: Settings,
  },
];

interface SidebarProps {
  onNavigate?: () => void;
}

export default function Sidebar({ onNavigate }: SidebarProps) {
  return (
    <aside className="flex h-full w-72 flex-col border-r border-border bg-card">

      {/* Logo */}
      <div className="flex h-20 items-center gap-3 border-b border-border px-6">

        <div className="rounded-lg bg-primary p-2 text-primary-foreground">
          <BarChart3 size={22} />
        </div>

        <div>
          <h1 className="font-bold text-foreground">
            InsightForge AI
          </h1>

          <p className="text-xs text-muted-foreground">
            Your AI Data Analyst
          </p>
        </div>

      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-2 p-5">

        {navigation.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.href}
              to={item.href}
              end={item.href === "/dashboard"}
              onClick={onNavigate}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-4 py-3 transition-all duration-200 ${
                  isActive
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                }`
              }
            >
              <Icon size={20} />
              <span>{item.name}</span>
            </NavLink>
          );
        })}

      </nav>

      {/* Footer */}
      <div className="border-t border-border p-5">

        <button
          className="
            flex
            w-full
            items-center
            gap-3
            rounded-lg
            px-4
            py-3
            text-muted-foreground
            transition-all
            duration-200
            hover:bg-destructive
            hover:text-white
          "
        >
          <LogOut size={20} />
          Logout
        </button>

      </div>

    </aside>
  );
}