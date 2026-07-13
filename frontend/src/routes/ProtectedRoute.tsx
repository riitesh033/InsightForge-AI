import { Navigate } from "react-router-dom";

interface Props {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: Props) {
  const isAuthenticated = false;

  return isAuthenticated ? children : <Navigate to="/login" replace />;
}