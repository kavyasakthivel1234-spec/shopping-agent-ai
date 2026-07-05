/**
 * App.jsx
 * -------
 * Root component — handles all auth views and the main app.
 *
 * Auth view states (no React Router — pure state machine):
 *   "login"           → Login page
 *   "signup"          → Signup page
 *   "forgot-password" → ForgotPassword page
 *   "reset-password"  → ResetPassword page  (reads ?token= from URL)
 *
 * On app load, checks window.location for /reset-password?token=...
 * so email reset links work even when the app is restarted.
 */

import { useState, useEffect } from "react";
import { useAuth }        from "./context/AuthContext";
import AssistantPage      from "./pages/AssistantPage";
import HistoryPage        from "./pages/HistoryPage";
import Login              from "./pages/Login";
import Signup             from "./pages/Signup";
import ForgotPassword     from "./pages/ForgotPassword";
import ResetPassword      from "./pages/ResetPassword";
import ProtectedRoute     from "./components/ProtectedRoute";
import "./App.css";

const APP_TABS = [
  { id: "assistant", label: "Assistant" },
  { id: "history",   label: "History" },
];

// ---------------------------------------------------------------------------
// Helper — read ?token= from the URL query string
// ---------------------------------------------------------------------------
function getResetTokenFromURL() {
  const params = new URLSearchParams(window.location.search);
  return params.get("token") || "";
}

// ---------------------------------------------------------------------------
// Helper — detect if the URL path looks like /reset-password
// ---------------------------------------------------------------------------
function isResetPasswordPath() {
  return window.location.pathname.includes("reset-password");
}

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------
export default function App() {
  const { user, logout, isLoading } = useAuth();

  const [activeTab, setActiveTab] = useState("assistant");

  // Determine initial auth view from URL so reset links work
  const [authView, setAuthView] = useState(() => {
    if (isResetPasswordPath() && getResetTokenFromURL()) {
      return "reset-password";
    }
    return "login";
  });

  // Token read once at mount — stored in state so it survives view switches
  const [resetToken] = useState(() => getResetTokenFromURL());

  // Force dark class on <html>
  useEffect(() => {
    document.documentElement.classList.add("dark");
  }, []);

  // ── Full-screen loading spinner while session is being restored ───
  if (isLoading) {
    return (
      <div className="auth-loading">
        <div className="auth-loading__spinner" />
      </div>
    );
  }

  // ── Unauthenticated views ─────────────────────────────────────────
  if (!user) {
    return (
      <div className="app">
        {authView === "login" && (
          <Login
            onSuccess={() => { setActiveTab("assistant"); }}
            onGoSignup={() => setAuthView("signup")}
            onGoForgot={() => setAuthView("forgot-password")}
          />
        )}

        {authView === "signup" && (
          <Signup
            onSuccess={() => { setActiveTab("assistant"); }}
            onGoLogin={() => setAuthView("login")}
          />
        )}

        {authView === "forgot-password" && (
          <ForgotPassword
            onGoLogin={() => setAuthView("login")}
          />
        )}

        {authView === "reset-password" && (
          <ResetPassword
            queryToken={resetToken}
            onGoLogin={() => setAuthView("login")}
            onGoForgot={() => setAuthView("forgot-password")}
          />
        )}
      </div>
    );
  }

  // ── Authenticated app ─────────────────────────────────────────────
  return (
    <div className="app">
      {/* Top bar */}
      <div className="app-topbar">
        <div className="app-logo">SHOPPING AI</div>

        <nav className="app-nav" aria-label="Main navigation">
          {APP_TABS.map((tab) => (
            <button
              key={tab.id}
              className={`app-nav__tab ${activeTab === tab.id ? "app-nav__tab--active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
              aria-current={activeTab === tab.id ? "page" : undefined}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        <div className="app-user">
          <span className="app-user__name">{user.name}</span>
          <button
            className="app-nav__tab app-user__logout"
            onClick={logout}
            aria-label="Sign out"
          >
            Sign out
          </button>
        </div>
      </div>

      {/* Protected pages */}
      <ProtectedRoute onRedirect={() => setAuthView("login")}>
        {activeTab === "assistant" && <AssistantPage />}
        {activeTab === "history"   && <HistoryPage />}
      </ProtectedRoute>
    </div>
  );
}
