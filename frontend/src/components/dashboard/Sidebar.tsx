import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Upload,
  Database,
  FileText,
  MessageSquare,
  Settings,
  LogOut,
  BarChart3,
  CreditCard,
  BadgeCheck,
  ReceiptText,
  GraduationCap,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

import { useAuth } from "@/hooks/useAuth";
import { showSuccess } from "@/lib/toast";

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
    name: "Plan & Billing",
    href: "/dashboard/billing",
    icon: CreditCard,
  },
  {
    name: "Subscription",
    href: "/dashboard/subscription",
    icon: BadgeCheck,
  },
  {
    name: "Payment History",
    href: "/dashboard/payment-history",
    icon: ReceiptText,
  },
  {
    name: "Student Pro Verification",
    href: "/dashboard/student-verification",
    icon: GraduationCap,
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
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);

  async function handleLogout() {
    await logout();
    showSuccess("Logged out successfully.");
    navigate("/login");
  }

  return (
    <aside
      className={`flex h-full flex-col border-r border-white/10 bg-slate-950/80 backdrop-blur-xl transition-all duration-300 ${
        collapsed ? "w-24" : "w-72"
      }`}
    >
      <Link
        to="/"
        aria-label="InsightForge AI home"
        onClick={onNavigate}
        className={`flex items-center border-b border-white/10 px-4 py-5 transition-colors hover:bg-white/5 ${
          collapsed ? "justify-center px-3" : "gap-3 px-5"
        }`}
      >
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 text-white shadow-lg shadow-indigo-500/30">
          <BarChart3 size={20} />
        </div>

        {!collapsed && (
          <div className="min-w-0">
            <h1 className="truncate text-base font-semibold text-white">
              InsightForge AI
            </h1>
            <p className="truncate text-[11px] text-slate-400">
              Your AI Data Analyst
            </p>
          </div>
        )}
      </Link>

      <nav className="flex-1 space-y-1.5 p-3">
        {navigation.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.href}
              to={item.href}
              end={item.href === "/dashboard"}
              onClick={onNavigate}
              className={({ isActive }) =>
                `flex items-center rounded-xl px-3 py-2.5 transition-all duration-200 ${
                  collapsed ? "justify-center" : "gap-3"
                } ${
                  isActive
                    ? "bg-gradient-to-r from-indigo-500/80 to-violet-500/80 text-white shadow-lg shadow-indigo-500/20"
                    : "text-slate-300 hover:bg-white/5 hover:text-white"
                }`
              }
            >
              <Icon size={18} />
              {!collapsed && <span className="text-sm font-medium">{item.name}</span>}
            </NavLink>
          );
        })}
      </nav>

      <div className="space-y-2 border-t border-white/10 p-3">
        <button
          type="button"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          onClick={() => setCollapsed((value) => !value)}
          className={`flex w-full items-center rounded-xl border border-white/10 bg-slate-900/60 px-3 py-2.5 text-sm text-slate-300 transition hover:border-indigo-400/40 hover:text-white ${
            collapsed ? "justify-center" : "gap-3"
          }`}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          {!collapsed && <span>Collapse</span>}
        </button>

        <button
          type="button"
          onClick={handleLogout}
          className={`flex w-full items-center rounded-xl px-3 py-2.5 text-sm text-slate-300 transition hover:bg-red-500/10 hover:text-red-200 ${
            collapsed ? "justify-center" : "gap-3"
          }`}
        >
          <LogOut size={18} />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  );
}