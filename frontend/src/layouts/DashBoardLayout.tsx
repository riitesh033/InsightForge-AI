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

    <div className="flex min-h-screen bg-background">


      {/* Desktop Sidebar */}
      <div className="hidden lg:block">

        <Sidebar />

      </div>



      {/* Mobile Sidebar */}
      <MobileSidebar

        open={mobileOpen}

        onClose={() =>
          setMobileOpen(false)
        }

      />



      {/* Main Content */}
      <div className="flex flex-1 flex-col">


        <TopNavbar

          title={title}

          subtitle={subtitle}

          onMenuClick={() =>
            setMobileOpen(true)
          }

        />



        <main
          className="
            flex-1
            overflow-y-auto
            bg-background
            p-6
          "
        >

          <Outlet />

        </main>


      </div>


    </div>

  );

}