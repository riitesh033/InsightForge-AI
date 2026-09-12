import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import { Users, Database, FileText, Activity, ShieldAlert, CheckCircle2 } from 'lucide-react';

export const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
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

  if (loading) return <div className="p-8">Loading System Metrics...</div>;

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Admin Control Center</h1>
        <p className="text-gray-500 mt-1">Platform overview and system health metrics</p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">Total Users</p>
            <h3 className="text-2xl font-bold text-gray-900 mt-1">{stats?.total_users}</h3>
            <span className="text-xs text-green-600 font-medium">{stats?.active_users} Active</span>
          </div>
          <Users className="w-10 h-10 text-indigo-500 bg-indigo-50 p-2 rounded-lg" />
        </div>

        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">Datasets Managed</p>
            <h3 className="text-2xl font-bold text-gray-900 mt-1">{stats?.total_datasets}</h3>
          </div>
          <Database className="w-10 h-10 text-blue-500 bg-blue-50 p-2 rounded-lg" />
        </div>

        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">Avg Quality Score</p>
            <h3 className="text-2xl font-bold text-gray-900 mt-1">{stats?.avg_quality_score} / 100</h3>
          </div>
          <Activity className="w-10 h-10 text-emerald-500 bg-emerald-50 p-2 rounded-lg" />
        </div>

        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">Reports Generated</p>
            <h3 className="text-2xl font-bold text-gray-900 mt-1">{stats?.total_reports}</h3>
          </div>
          <FileText className="w-10 h-10 text-purple-500 bg-purple-50 p-2 rounded-lg" />
        </div>
      </div>

      {/* System Health Module */}
      <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
        <h2 className="text-xl font-bold text-gray-900 mb-4">System Health & Infrastructure</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-lg bg-gray-50 border border-gray-100">
            <span className="text-xs text-gray-500 uppercase font-semibold">Backend API</span>
            <div className="flex items-center space-x-2 mt-2">
              <CheckCircle2 className="w-5 h-5 text-green-500" />
              <span className="font-semibold text-gray-800">{health?.backend_status}</span>
            </div>
          </div>
          <div className="p-4 rounded-lg bg-gray-50 border border-gray-100">
            <span className="text-xs text-gray-500 uppercase font-semibold">Database Connection</span>
            <div className="flex items-center space-x-2 mt-2">
              <CheckCircle2 className="w-5 h-5 text-green-500" />
              <span className="font-semibold text-gray-800">{health?.database_status}</span>
            </div>
          </div>
          <div className="p-4 rounded-lg bg-gray-50 border border-gray-100">
            <span className="text-xs text-gray-500 uppercase font-semibold">AI Integration Engine</span>
            <div className="flex items-center space-x-2 mt-2">
              <Activity className="w-5 h-5 text-indigo-500" />
              <span className="font-semibold text-gray-800">{health?.ai_service_status}</span>
            </div>
          </div>
          <div className="p-4 rounded-lg bg-gray-50 border border-gray-100">
            <span className="text-xs text-gray-500 uppercase font-semibold">Storage Usage</span>
            <div className="flex items-center space-x-2 mt-2">
              <span className="text-lg font-bold text-gray-800">{health?.storage_usage_mb} MB</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};