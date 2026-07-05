/**
 * ResetPassword.jsx
 * -----------------
 * Reset password page — dark-indigo / purple glassmorphism theme.
 *
 * Flow:
 *   1. Reads the JWT token from the URL query string: ?token=<jwt>
 *   2. User enters new password + confirmation.
 *   3. Clicks "Reset Password" → POST /api/auth/reset-password.
 *   4. On success → navigates to Login after 2 seconds.
 *   5. On invalid/expired token → shows a clear error with a link to
 *      re-request a reset.
 *
 * Props:
 *   onGoLogin       {function} — navigate to Login page
 *   onGoForgot      {function} — navigate to Forgot Password page
 *   queryToken      {string}   — JWT token extracted from URL by App.jsx
 */

import { useState } from "react";
import { resetPassword } from "../services/authService";
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

export default function ResetPassword({ onGoLogin, onGoForgot, queryToken }) {
  const [password,     setPassword]     = useState("");
  const [confirmPw,    setConfirmPw]    = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm,  setShowConfirm]  = useState(false);
  const [isLoading,    setIsLoading]    = useState(false);
  const [success,      setSuccess]      = useState("");
  const [error,        setError]        = useState("");

  // Guard: no token in URL
  if (!queryToken) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <div className="auth-card__brand">
            <div className="auth-card__logo">SA</div>
            <h1 className="auth-card__title">Invalid Link</h1>
          </div>
          <div className="auth-error" role="alert">
            This password reset link is missing or invalid.
          </div>
          <p className="auth-card__footer">
            <button className="auth-link" type="button" onClick={onGoForgot}>
              Request a new reset link
            </button>
          </p>
        </div>
        <footer className="auth-page-footer">Kavya S &copy; 2026</footer>
      </div>
    );
  }

  function validate() {
    if (password.length < 8)  return "Password must be at least 8 characters.";
    if (password.length > 72) return "Password must be no more than 72 characters.";
    if (password !== confirmPw) return "Passwords do not match.";
    return "";
  }

  async function handleSubmit(e) {
    e.preventDefault();

    const err = validate();
    if (err) { setError(err); return; }

    setError("");
    setSuccess("");
    setIsLoading(true);

    console.log("[ResetPassword] Submitting reset with token:", queryToken.slice(0, 20) + "...");

    try {
      const data = await resetPassword(queryToken, password);
      console.log("[ResetPassword] API response:", data);
      setSuccess(
        data.message ||
        "Your password has been reset. Redirecting to sign in..."
      );
      // Redirect to login after 2 seconds
      setTimeout(() => onGoLogin(), 2000);
    } catch (e) {
      console.error("[ResetPassword] API error:", e.message);
      setError(e.message || "Reset failed. The link may have expired.");
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
          <h1 className="auth-card__title">Reset Password</h1>
          <p className="auth-card__subtitle">Enter your new password below</p>
        </div>

        {/* Banners */}
        {error   && <div className="auth-error"   role="alert">{error}</div>}
        {success && <div className="auth-success" role="status">{success}</div>}

        {!success && (
          <form className="auth-form" onSubmit={handleSubmit} noValidate>

            {/* New password */}
            <div className="auth-field">
              <label className="auth-field__label" htmlFor="rp-pw">New Password</label>
              <div className="auth-field__password-wrap">
                <input
                  id="rp-pw"
                  className="auth-field__input auth-field__input--password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Minimum 8 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isLoading}
                  autoComplete="new-password"
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
              <p className="auth-field__hint">8 to 72 characters</p>            </div>

            {/* Confirm password */}
            <div className="auth-field">
              <label className="auth-field__label" htmlFor="rp-confirm">Confirm Password</label>
              <div className="auth-field__password-wrap">
                <input
                  id="rp-confirm"
                  className="auth-field__input auth-field__input--password"
                  type={showConfirm ? "text" : "password"}
                  placeholder="Re-enter your new password"
                  value={confirmPw}
                  onChange={(e) => setConfirmPw(e.target.value)}
                  disabled={isLoading}
                  autoComplete="new-password"
                  aria-required="true"
                />
                <button
                  type="button"
                  className="auth-field__eye"
                  onClick={() => setShowConfirm((v) => !v)}
                  aria-label={showConfirm ? "Hide password" : "Show password"}
                >
                  {showConfirm ? <EyeOpen /> : <EyeClosed />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="auth-btn auth-btn--primary"
              disabled={isLoading}
            >
              {isLoading ? <span className="auth-btn__spinner" /> : "Reset Password"}
            </button>

          </form>
        )}

        {/* Expired token fallback */}
        {error && (
          <p className="auth-card__footer">
            Link expired?{" "}
            <button className="auth-link" type="button" onClick={onGoForgot}>
              Request a new one
            </button>
          </p>
        )}

        {!error && !success && (
          <p className="auth-card__footer">
            <button className="auth-link auth-link--muted" type="button" onClick={onGoLogin}>
              Back to Sign In
            </button>
          </p>
        )}

      </div>

      <footer className="auth-page-footer">
        Kavya S &copy; 2026
      </footer>

    </div>
  );
}
