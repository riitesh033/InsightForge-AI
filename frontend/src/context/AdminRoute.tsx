import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { AuthContext } from './AuthContext';
import { getAdminRouteAccess } from './adminAccess.js';

export const AdminRoute: React.FC = () => {
  const authContext = React.useContext(AuthContext);

  if (!authContext) {
    return <Navigate to="/dashboard" replace />;
  }

  const routeAccess = getAdminRouteAccess(authContext);
  if (routeAccess === "loading") {
    return <div className="flex min-h-screen items-center justify-center">Loading...</div>;
  }
  if (routeAccess === "admin-login") {
    return <Navigate to="/admin/login" replace />;
  }
  if (routeAccess === "forbidden") {
    return <Navigate to="/forbidden" replace />;
  }

  return <Outlet />;
};