import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import Sidebar from "@/components/dashboard/Sidebar";
import MobileSidebar from "@/components/dashboard/MobileSidebar";
import TopNavbar from "@/components/dashboard/TopNavbar";


export default function DashboardLayout() {

  const [mobileOpen, setMobileOpen] = useState(false);

  const location = useLocation();


  const pageTitles: Record<string, string> = {

    "/dashboard": "Dashboard",

    "/dashboard/upload": "Upload Dataset",

    "/dashboard/datasets": "Datasets",

    "/dashboard/reports": "Reports",

    "/dashboard/ai-chat": "AI Chat",

    "/dashboard/billing": "Plan & Billing",

    "/dashboard/subscription": "Subscription",

    "/dashboard/payment-history": "Payment History",

    "/dashboard/student-verification": "Student Pro Verification",

    "/dashboard/settings": "Settings",

  };


  const pageSubtitles: Record<string, string> = {

    "/dashboard": "Welcome to InsightForge AI",

    "/dashboard/upload":
      "Upload CSV or Excel datasets for AI analysis.",

    "/dashboard/datasets":
      "Manage your uploaded datasets.",

    "/dashboard/reports":
      "View AI-generated reports.",

    "/dashboard/ai-chat":
      "Interact with your AI Data Analyst.",

    "/dashboard/billing":
      "Choose or change your membership plan.",

    "/dashboard/subscription":
      "View your current membership and its status.",

    "/dashboard/payment-history":
      "Review payments recorded for your account.",

    "/dashboard/student-verification":
      "Apply for student Pro access and track your verification status.",

    "/dashboard/settings":
      "Manage your account settings.",

  };


  let title =
    pageTitles[location.pathname];


  let subtitle =
    pageSubtitles[location.pathname];


  // Dynamic Analysis page
  if (
    location.pathname.startsWith(
      "/dashboard/analysis/"
    )
  ) {

    title = "Dataset Analysis";

    subtitle =
      "AI powered data quality report";

  }


  title =
    title ?? "Dashboard";


  subtitle =
    subtitle ??
    "Welcome to InsightForge AI";


  return (
    <div className="dashboard-shell flex min-h-screen">
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      <MobileSidebar
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <TopNavbar
          title={title}
          subtitle={subtitle}
          onMenuClick={() => setMobileOpen(true)}
        />

        <main className="min-w-0 flex-1 overflow-y-auto bg-background p-3 text-foreground transition-colors duration-300 sm:p-4 md:p-6 lg:p-8">
          <div className="mx-auto w-full max-w-7xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}