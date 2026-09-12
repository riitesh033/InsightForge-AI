import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { AuthContext } from './AuthContext';

export const AdminRoute: React.FC = () => {
  const authContext = React.useContext(AuthContext);

  if (!authContext) {
    return <Navigate to="/dashboard" replace />;
  }

  const { user, loading } = authContext;

  if (loading) return <div>Loading...</div>;
  if (!user || !user.is_superuser) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
};