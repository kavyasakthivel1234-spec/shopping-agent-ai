/**
 * AuthContext.jsx
 * ---------------
 * Global authentication state for the entire application.
 *
 * Provides:
 *   - user         : current user object | null
 *   - token        : JWT string | null
 *   - isLoading    : true while restoring session from localStorage
 *   - login(token, user)  : persist session + update state
 *   - logout()            : clear session + redirect to login
 *
 * localStorage keys:
 *   "sa_token"  — JWT access token
 *   "sa_user"   — JSON-stringified user object
 */

import { createContext, useContext, useState, useEffect } from "react";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user,      setUser]      = useState(null);
  const [token,     setToken]     = useState(null);
  const [isLoading, setIsLoading] = useState(true);  // restoring session

  // ── Restore session from localStorage on mount ─────────────────
  useEffect(() => {
    try {
      const savedToken = localStorage.getItem("sa_token");
      const savedUser  = localStorage.getItem("sa_user");
      if (savedToken && savedUser) {
        setToken(savedToken);
        setUser(JSON.parse(savedUser));
      }
    } catch {
      // Corrupted localStorage — start fresh
      localStorage.removeItem("sa_token");
      localStorage.removeItem("sa_user");
    } finally {
      setIsLoading(false);
    }
  }, []);

  /** Persist session after successful login or signup. */
  function login(newToken, newUser) {
    localStorage.setItem("sa_token", newToken);
    localStorage.setItem("sa_user", JSON.stringify(newUser));
    setToken(newToken);
    setUser(newUser);
  }

  /** Clear session and remove persisted data. */
  function logout() {
    localStorage.removeItem("sa_token");
    localStorage.removeItem("sa_user");
    localStorage.removeItem("sa_chats");
    localStorage.clear();
    sessionStorage.clear();   // clears sa_chat_messages → next login starts fresh
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

/** Hook — use inside any component that needs auth state. */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
