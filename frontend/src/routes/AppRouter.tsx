import { Routes, Route, Navigate } from "react-router-dom";

import LandingLayout from "@/layouts/LandingLayout";
import AuthLayout from "@/layouts/AuthLayout";
import DashboardLayout from "@/layouts/DashBoardLayout";

import LandingPage from "@/pages/Landing/LandingPage";

import LoginPage from "@/pages/Auth/LoginPage";
import RegisterPage from "@/pages/Auth/RegisterPage";
import ForgotPasswordPage from "@/pages/Auth/ForgotPassword";

import DashboardPage from "@/pages/Dashboard/DashBoardPage";
import UploadDatasetPage from "@/pages/Dashboard/UploadDatasetPage";
import DatasetsPage from "@/pages/Dashboard/DatasetsPage";
import ReportsPage from "@/pages/Dashboard/ReportsPage";
import AIChatPage from "@/pages/Dashboard/AIChatPage";
import SettingsPage from "@/pages/Dashboard/SettingsPage";

import ProtectedRoute from "./ProtectedRoute";

export default function AppRouter() {
  return (
    <Routes>

      {/* Landing */}
      <Route element={<LandingLayout />}>
        <Route index element={<LandingPage />} />
      </Route>

      {/* Authentication */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/forgot-password"
          element={<ForgotPasswordPage />}
        />
      </Route>

      {/* Dashboard */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />

        <Route
          path="upload"
          element={<UploadDatasetPage />}
        />

        <Route
          path="datasets"
          element={<DatasetsPage />}
        />

        <Route
          path="reports"
          element={<ReportsPage />}
        />

        <Route
          path="ai-chat"
          element={<AIChatPage />}
        />

        <Route
          path="settings"
          element={<SettingsPage />}
        />
      </Route>

      {/* Live Demo */}
      <Route
        path="/demo"
        element={<Navigate to="/" replace />}
      />

      {/* 404 */}
      <Route
        path="*"
        element={<Navigate to="/" replace />}
      />

    </Routes>
  );
}