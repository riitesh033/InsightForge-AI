import React, { useEffect, useState } from 'react';
import api from "@/lib/api";
import { Users, Database, FileText, Activity, CheckCircle2, GraduationCap } from 'lucide-react';
import { Link } from "react-router-dom";

interface AdminDashboardStats {
  total_users: number;
  active_users: number;
  total_datasets: number;
  total_analyses: number;
  total_reports: number;
  total_chat_messages: number;
  avg_quality_score: number;
}

interface SystemHealth {
  backend_status: string;
  database_status: string;
  ai_service_status: string;
  storage_usage_mb: number;
}

export const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<AdminDashboardStats | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAdminData = async () => {
      try {
        const [statsRes, healthRes] = await Promise.all([
          api.get('/admin/dashboard'),
          api.get('/admin/system-health')
        ]);
        setStats(statsRes.data);
        setHealth(healthRes.data);
      } catch (err) {
        console.error("Failed to load admin stats", err);
      } finally {
        setLoading(false);
      }
    };
    fetchAdminData();
  }, []);

  if (loading) return <div role="status" className="p-4 text-muted-foreground sm:p-8">Loading System Metrics...</div>;

  return (
    <div className="mx-auto min-w-0 max-w-7xl space-y-6 p-3 transition-colors duration-200 sm:space-y-8 sm:p-5 md:p-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground sm:text-3xl">Admin Control Center</h1>
        <p className="mt-1 text-muted-foreground">Platform overview and system health metrics</p>
      </div>
      <Link
        to="/admin/student-verifications"
        className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-primary px-4 py-3 font-semibold text-primary-foreground transition-colors duration-200 hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
      >
        <GraduationCap className="size-5" />
        Review student verification applications
      </Link>

      {/* Metrics Grid */}
      <div className="grid min-w-0 grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4 sm:gap-6">
        <div className="flex min-w-0 items-center justify-between gap-3 rounded-xl border border-border bg-card p-4 text-card-foreground shadow-sm transition-colors duration-200 sm:p-6">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Total Users</p>
            <h3 className="mt-1 text-2xl font-bold text-foreground">{stats?.total_users}</h3>
            <span className="text-xs font-medium text-emerald-700 dark:text-emerald-300">{stats?.active_users} Active</span>
          </div>
          <Users className="size-10 shrink-0 rounded-lg bg-primary/10 p-2 text-primary" />
        </div>

        <div className="flex min-w-0 items-center justify-between gap-3 rounded-xl border border-border bg-card p-4 text-card-foreground shadow-sm transition-colors duration-200 sm:p-6">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Datasets Managed</p>
            <h3 className="mt-1 text-2xl font-bold text-foreground">{stats?.total_datasets}</h3>
          </div>
          <Database className="size-10 shrink-0 rounded-lg bg-sky-500/10 p-2 text-sky-700 dark:text-sky-300" />
        </div>

        <div className="flex min-w-0 items-center justify-between gap-3 rounded-xl border border-border bg-card p-4 text-card-foreground shadow-sm transition-colors duration-200 sm:p-6">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Avg Quality Score</p>
            <h3 className="mt-1 text-2xl font-bold text-foreground">{stats?.avg_quality_score} / 100</h3>
          </div>
          <Activity className="size-10 shrink-0 rounded-lg bg-emerald-500/10 p-2 text-emerald-700 dark:text-emerald-300" />
        </div>

        <div className="flex min-w-0 items-center justify-between gap-3 rounded-xl border border-border bg-card p-4 text-card-foreground shadow-sm transition-colors duration-200 sm:p-6">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Reports Generated</p>
            <h3 className="mt-1 text-2xl font-bold text-foreground">{stats?.total_reports}</h3>
          </div>
          <FileText className="size-10 shrink-0 rounded-lg bg-purple-500/10 p-2 text-purple-700 dark:text-purple-300" />
        </div>
      </div>

      {/* System Health Module */}
      <div className="rounded-xl border border-border bg-card p-4 text-card-foreground shadow-sm transition-colors duration-200 sm:p-6">
        <h2 className="mb-4 text-xl font-bold text-foreground">System Health & Infrastructure</h2>
        <div className="grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4 sm:gap-4">
          <div className="min-w-0 rounded-lg border border-border bg-background p-4 transition-colors duration-200">
            <span className="text-xs font-semibold uppercase text-muted-foreground">Backend API</span>
            <div className="flex items-center space-x-2 mt-2">
              <CheckCircle2 className="size-5 shrink-0 text-emerald-600 dark:text-emerald-300" />
              <span className="break-words font-semibold text-foreground">{health?.backend_status}</span>
            </div>
          </div>
          <div className="min-w-0 rounded-lg border border-border bg-background p-4 transition-colors duration-200">
            <span className="text-xs font-semibold uppercase text-muted-foreground">Database Connection</span>
            <div className="flex items-center space-x-2 mt-2">
              <CheckCircle2 className="size-5 shrink-0 text-emerald-600 dark:text-emerald-300" />
              <span className="break-words font-semibold text-foreground">{health?.database_status}</span>
            </div>
          </div>
          <div className="min-w-0 rounded-lg border border-border bg-background p-4 transition-colors duration-200">
            <span className="text-xs font-semibold uppercase text-muted-foreground">AI Integration Engine</span>
            <div className="flex items-center space-x-2 mt-2">
              <Activity className="size-5 shrink-0 text-primary" />
              <span className="break-words font-semibold text-foreground">{health?.ai_service_status}</span>
            </div>
          </div>
          <div className="min-w-0 rounded-lg border border-border bg-background p-4 transition-colors duration-200">
            <span className="text-xs font-semibold uppercase text-muted-foreground">Storage Usage</span>
            <div className="flex items-center space-x-2 mt-2">
              <span className="text-lg font-bold text-foreground">{health?.storage_usage_mb} MB</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};