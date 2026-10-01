import { Routes, Route, Navigate } from "react-router-dom";

import LandingLayout from "@/layouts/LandingLayout";
import AuthLayout from "@/layouts/AuthLayout";
import DashboardLayout from "@/layouts/DashBoardLayout";
import { AdminRoute } from "@/context/AdminRoute";

import LandingPage from "@/pages/Landing/LandingPage";

import LoginPage from "@/pages/Auth/LoginPage";
import RegisterPage from "@/pages/Auth/RegisterPage";
import ForgotPasswordPage from "@/pages/Auth/ForgotPassword";
import ResetPasswordPage from "@/pages/Auth/ResetPasswordPage";
import GoogleCallbackPage from "@/pages/Auth/GoogleCallbackPage";
import AdminLoginPage from "@/pages/Auth/AdminLoginPage";

import DashboardPage from "@/pages/Dashboard/DashBoardPage";
import UploadDatasetPage from "@/pages/Dashboard/UploadDatasetPage";
import DatasetsPage from "@/pages/Dashboard/DatasetsPage";
import AnalysisPage from "@/pages/Dashboard/AnalysisPage";
import ReportsPage from "@/pages/Dashboard/ReportsPage";
import AIChatPage from "@/pages/Dashboard/AIChatPage";
import SettingsPage from "@/pages/Dashboard/SettingsPage";
import BillingPage from "@/pages/Dashboard/BillingPage";
import SubscriptionPage from "@/pages/Dashboard/SubscriptionPage";
import PaymentHistoryPage from "@/pages/Dashboard/PaymentHistoryPage";
import { AdminDashboard } from "@/pages/Dashboard/AdminDashboard";
import StudentVerificationPage from "@/pages/Dashboard/StudentVerificationPage";
import AdminStudentVerificationPage from "@/pages/Dashboard/AdminStudentVerificationPage";
import AdminLayout from "@/layouts/AdminLayout";

import NotFoundPage from "@/pages/Error/NotFoundPage";
import ForbiddenPage from "@/pages/Error/ForbiddenPage";
import ServerErrorPage from "@/pages/Error/ServerErrorPage";
import PaymentSuccessPage from "@/pages/PaymentSuccessPage";
import PaymentCancelledPage from "@/pages/PaymentCancelledPage";

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

        <Route path="/reset-password" 
        element={<ResetPasswordPage />} />
        <Route path="/auth/google/callback" element={<GoogleCallbackPage />} />

      </Route>

      <Route element={<AuthLayout />}>
        <Route path="/admin/login" element={<AdminLoginPage />} />
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
          path="ai-chat/:datasetId?"
          element={<AIChatPage />}
        />

        <Route
          path="billing"
          element={<BillingPage />}
        />

        <Route
          path="subscription"
          element={<SubscriptionPage />}
        />

        <Route
          path="payment-history"
          element={<PaymentHistoryPage />}
        />

        <Route
          path="student-verification"
          element={<StudentVerificationPage />}
        />


        {/* /dashboard/settings */}
        <Route
          path="settings"
          element={<SettingsPage />}
        />

      </Route>

      <Route
        path="/admin"
        element={
          <AdminRoute />
        }
      >
        <Route element={<AdminLayout />}>
          <Route index element={<AdminDashboard />} />
          <Route
            path="student-verifications"
            element={<AdminStudentVerificationPage />}
          />
        </Route>
      </Route>

      <Route
        path="/payment-success"
        element={
          <ProtectedRoute>
            <PaymentSuccessPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/payment-cancelled"
        element={
          <ProtectedRoute>
            <PaymentCancelledPage />
          </ProtectedRoute>
        }
      />

      <Route path="/forbidden" element={<ForbiddenPage />} />
      <Route path="/403" element={<ForbiddenPage />} />
      <Route path="/server-error" element={<ServerErrorPage />} />
      <Route path="/500" element={<ServerErrorPage />} />
      <Route
        path="/pricing"
        element={<Navigate to="/#pricing" replace />}
      />

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