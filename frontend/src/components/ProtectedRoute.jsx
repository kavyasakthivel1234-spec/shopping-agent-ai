/**
 * ProtectedRoute.jsx
 * ------------------
 * Renders children if the user is authenticated.
 * Redirects to the login view (sets activeTab="login") if not.
 *
 * Props:
 *   children  {ReactNode}
 *   onRedirect {function}  — called with "login" when auth is missing
 */

import { useEffect } from "react";
import { useAuth }   from "../context/AuthContext";

function ProtectedRoute({ children, onRedirect }) {
  const { user, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !user && onRedirect) {
      onRedirect("login");
    }
  }, [user, isLoading, onRedirect]);

  // While restoring session from localStorage — show nothing
  if (isLoading) {
    return (
      <div className="auth-loading" aria-live="polite">
        <div className="auth-loading__spinner" />
      </div>
    );
  }

  // Not authenticated
  if (!user) return null;

  return children;
}

export default ProtectedRoute;
