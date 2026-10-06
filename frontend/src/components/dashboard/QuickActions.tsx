import {
  Bot,
  FileText,
  FolderOpen,
  Upload,
} from "lucide-react";
import { Link } from "react-router-dom";

const actions = [
  {
    title: "Upload Dataset",
    icon: Upload,
    href: "/dashboard/upload",
    accent: "from-indigo-500/20 to-violet-500/20",
  },
  {
    title: "Datasets",
    icon: FolderOpen,
    href: "/dashboard/datasets",
    accent: "from-cyan-500/20 to-blue-500/20",
  },
  {
    title: "Reports",
    icon: FileText,
    href: "/dashboard/reports",
    accent: "from-emerald-500/20 to-teal-500/20",
  },
  {
    title: "AI Chat",
    icon: Bot,
    href: "/dashboard/ai-chat",
    accent: "from-fuchsia-500/20 to-pink-500/20",
  },
];

export default function QuickActions() {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {actions.map((action) => {
        const Icon = action.icon;

        return (
          <Link
            key={action.title}
            to={action.href}
            className="group rounded-2xl border border-white/10 bg-slate-900/70 p-5 shadow-[0_18px_40px_rgba(15,23,42,0.25)] transition-all duration-200 hover:-translate-y-1 hover:border-indigo-400/40 hover:shadow-[0_24px_50px_rgba(99,102,241,0.18)]"
          >
            <div className={`mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${action.accent}`}>
              <Icon className="h-6 w-6 text-white" />
            </div>

            <h3 className="text-base font-semibold text-white">
              {action.title}
            </h3>

            <p className="mt-1 text-sm text-slate-400">
              Open {action.title.toLowerCase()}
            </p>
          </Link>
        );
      })}
    </div>
  );
}