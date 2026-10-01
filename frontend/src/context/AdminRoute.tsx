import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { AuthContext } from './AuthContext';
import { getAdminRouteAccess } from './adminAccess.js';

export const AdminRoute: React.FC = () => {
  const authContext = React.useContext(AuthContext);

  if (!authContext) {
    return <Navigate to="/dashboard" replace />;
  }

  const { user, loading } = authContext;

  if (loading) return <div>Loading...</div>;
  if (getAdminRouteAccess(user) !== "allowed") {
    return <Navigate to="/forbidden" replace />;
  }

  return <Outlet />;
};