import { Routes, Route, Navigate } from "react-router-dom";

import LandingLayout from "@/layouts/LandingLayout";
import AuthLayout from "@/layouts/AuthLayout";
import DashboardLayout from "@/layouts/DashBoardLayout";

import LandingPage from "@/pages/Landing/LandingPage";

import LoginPage from "@/pages/Auth/LoginPage";
import RegisterPage from "@/pages/Auth/RegisterPage";
import ForgotPasswordPage from "@/pages/Auth/ForgotPassword";

import DashboardPage from "@/pages/Dashboard/DashboardPage";
import UploadDatasetPage from "@/pages/Dashboard/UploadDatasetPage";
import DatasetsPage from "@/pages/Dashboard/DatasetsPage";
import AnalysisPage from "@/pages/Dashboard/AnalysisPage";
import ReportsPage from "@/pages/Dashboard/ReportsPage";
import AIChatPage from "@/pages/Dashboard/AIChatPage";
import SettingsPage from "@/pages/Dashboard/SettingsPage";

import NotFoundPage from "@/pages/Error/NotFoundPage";

import ProtectedRoute from "./ProtectedRoute";


export default function AppRouter() {
  return (
    <Routes>

      {/* =========================
          Landing Pages
      ========================== */}
      <Route element={<LandingLayout />}>
        <Route
          path="/"
          element={<LandingPage />}
        />
      </Route>


      {/* =========================
          Authentication
      ========================== */}
      <Route element={<AuthLayout />}>

        <Route
          path="/login"
          element={<LoginPage />}
        />

        <Route
          path="/register"
          element={<RegisterPage />}
        />

        <Route
          path="/forgot-password"
          element={<ForgotPasswordPage />}
        />

      </Route>


      {/* =========================
          Dashboard
      ========================== */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >

        {/* /dashboard */}
        <Route
          index
          element={<DashboardPage />}
        />


        {/* /dashboard/upload */}
        <Route
          path="upload"
          element={<UploadDatasetPage />}
        />


        {/* /dashboard/datasets */}
        <Route
          path="datasets"
          element={<DatasetsPage />}
        />


        {/* /dashboard/analysis/:datasetId */}
        <Route
          path="analysis/:datasetId"
          element={<AnalysisPage />}
        />


        {/* /dashboard/reports */}
        <Route
          path="reports"
          element={<ReportsPage />}
        />


        {/* /dashboard/ai-chat */}
        <Route
          path="ai-chat"
          element={<AIChatPage />}
        />


        {/* /dashboard/settings */}
        <Route
          path="settings"
          element={<SettingsPage />}
        />

      </Route>


      {/* =========================
          Demo Redirect
      ========================== */}
      <Route
        path="/demo"
        element={
          <Navigate
            to="/"
            replace
          />
        }
      />


      {/* =========================
          404 Page
      ========================== */}
      <Route
        path="*"
        element={<NotFoundPage />}
      />

    </Routes>
  );
}