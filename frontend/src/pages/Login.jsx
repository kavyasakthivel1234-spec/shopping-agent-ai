/**
 * Login.jsx
 * ---------
 * Login page — dark-indigo / purple glassmorphism theme.
 *
 * Fixed: "Forgot password?" button now calls onGoForgot prop
 *        so App.jsx can navigate to the ForgotPassword page.
 *
 * Props:
 *   onSuccess   {function} — called when login succeeds
 *   onGoSignup  {function} — navigate to Signup page
 *   onGoForgot  {function} — navigate to Forgot Password page  ← NEW
 */

import { useState } from "react";
import { useAuth }           from "../context/AuthContext";
import { login as apiLogin } from "../services/authService";
import "../auth.css";

function EyeOpen() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
      <circle cx="12" cy="12" r="3"/>
    </svg>
  );
}

function EyeClosed() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
      <line x1="1" y1="1" x2="23" y2="23"/>
    </svg>
  );
}

export default function Login({ onSuccess, onGoSignup, onGoForgot }) {
  const { login: authLogin } = useAuth();

  const [identifier,   setIdentifier]   = useState("");
  const [password,     setPassword]     = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe,   setRememberMe]   = useState(false);
  const [isLoading,    setIsLoading]    = useState(false);
  const [error,        setError]        = useState("");

  const isEmail = identifier.includes("@");

  function validate() {
    if (!identifier.trim()) return "Enter your email or mobile number.";
    if (!password.trim())   return "Enter your password.";
    return "";
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const err = validate();
    if (err) { setError(err); return; }

    setError("");
    setIsLoading(true);

    console.log("[Login] Attempting login for:", identifier.trim());

    try {
      const payload = isEmail
        ? { email:  identifier.trim(), password }
        : { mobile: identifier.trim(), password };

      const data = await apiLogin(payload);
      console.log("[Login] Success:", data.user?.email);
      authLogin(data.access_token, data.user);
      if (onSuccess) onSuccess();
    } catch (e) {
      console.error("[Login] Error:", e.message);
      setError(e.message || "Login failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">

        {/* Brand */}
        <div className="auth-card__brand">
          <div className="auth-card__logo">SA</div>
          <h1 className="auth-card__title">Shopping AI</h1>
          <p className="auth-card__subtitle">Sign in to your account</p>
        </div>

        {/* Error banner */}
        {error && <div className="auth-error" role="alert">{error}</div>}

        <form className="auth-form" onSubmit={handleSubmit} noValidate>

          {/* Identifier */}
          <div className="auth-field">
            <label className="auth-field__label" htmlFor="login-id">
              Email or Mobile Number
            </label>
            <input
              id="login-id"
              className="auth-field__input"
              type="text"
              placeholder="kavya@email.com or 9876543210"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              disabled={isLoading}
              autoComplete="username"
              aria-required="true"
            />
          </div>

          {/* Password */}
          <div className="auth-field">
            <label className="auth-field__label" htmlFor="login-pw">Password</label>
            <div className="auth-field__password-wrap">
              <input
                id="login-pw"
                className="auth-field__input auth-field__input--password"
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
                autoComplete="current-password"
                aria-required="true"
              />
              <button
                type="button"
                className="auth-field__eye"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOpen /> : <EyeClosed />}
              </button>
            </div>
          </div>

          {/* Remember me + Forgot password */}
          <div className="auth-form__row">
            <label className="auth-checkbox">
              <input
                type="checkbox"
                className="auth-checkbox__input"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
              />
              <span className="auth-checkbox__label">Remember me</span>
            </label>

            {/* ── FIX: wired onClick to onGoForgot prop ── */}
            <button
              type="button"
              className="auth-link auth-link--muted"
              onClick={() => {
                console.log("[Login] Navigating to Forgot Password");
                if (onGoForgot) onGoForgot();
              }}
            >
              Forgot password?
            </button>
          </div>

          {/* Submit */}
          <button
            type="submit"
            className="auth-btn auth-btn--primary"
            disabled={isLoading}
          >
            {isLoading ? <span className="auth-btn__spinner" /> : "Sign In"}
          </button>

        </form>

        {/* Switch to signup */}
        <p className="auth-card__footer">
          Don&apos;t have an account?{" "}
          <button className="auth-link" type="button" onClick={onGoSignup}>
            Create account
          </button>
        </p>

      </div>

      <footer className="auth-page-footer">Kavya S &copy; 2026</footer>
    </div>
  );
}
