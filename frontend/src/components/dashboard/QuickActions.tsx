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
  },
  {
    title: "Datasets",
    icon: FolderOpen,
    href: "/dashboard/datasets",
  },
  {
    title: "Reports",
    icon: FileText,
    href: "/dashboard/reports",
  },
  {
    title: "AI Chat",
    icon: Bot,
    href: "/dashboard/ai-chat",
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
            className="group rounded-2xl border bg-card p-5 shadow-sm transition-all hover:-translate-y-1 hover:shadow-lg"
          >
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
              <Icon className="h-6 w-6 text-primary" />
            </div>

            <h3 className="font-semibold">
              {action.title}
            </h3>

            <p className="mt-1 text-sm text-muted-foreground">
              Open {action.title.toLowerCase()}
            </p>
          </Link>
        );
      })}
    </div>
  );
}