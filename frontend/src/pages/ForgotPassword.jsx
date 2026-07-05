/**
 * ForgotPassword.jsx
 * ------------------
 * Forgot password page — dark-indigo / purple glassmorphism theme.
 *
 * Flow:
 *   1. User enters their registered email.
 *   2. Clicks "Send Reset Link" → POST /api/auth/forgot-password.
 *   3. Success banner shown regardless of whether the email exists
 *      (prevents email enumeration).
 *   4. Backend prints the reset link to the terminal for development.
 *
 * Props:
 *   onGoLogin {function} — navigate back to the Login page
 */

import { useState } from "react";
import { forgotPassword } from "../services/authService";
import "../auth.css";

export default function ForgotPassword({ onGoLogin }) {
  const [email,     setEmail]     = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [success,   setSuccess]   = useState("");
  const [error,     setError]     = useState("");

  function validate() {
    if (!email.trim()) return "Please enter your email address.";
    if (!email.includes("@") || !email.includes("."))
      return "Please enter a valid email address.";
    return "";
  }

  async function handleSubmit(e) {
    e.preventDefault();

    const err = validate();
    if (err) { setError(err); return; }

    setError("");
    setSuccess("");
    setIsLoading(true);

    console.log("[ForgotPassword] Submitting forgot-password for:", email.trim());

    try {
      const data = await forgotPassword(email.trim());
      console.log("[ForgotPassword] API response:", data);

      // Always show the generic security message from the backend
      setSuccess(
        data.message ||
        "If an account with that email exists, a password reset link has been sent."
      );
      setEmail(""); // clear the input after success
    } catch (e) {
      console.error("[ForgotPassword] API error:", e.message);
      setError(e.message || "Something went wrong. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="auth-page">

      {/* ── Glass card ──────────────────────────────────────── */}
      <div className="auth-card">

        {/* Brand */}
        <div className="auth-card__brand">
          <div className="auth-card__logo">SA</div>
          <h1 className="auth-card__title">Forgot Password</h1>
          <p className="auth-card__subtitle">
            Enter your email and we will send you a reset link
          </p>
        </div>

        {/* Banners */}
        {error   && <div className="auth-error"   role="alert">{error}</div>}
        {success && <div className="auth-success" role="status">{success}</div>}

        {/* Only show the form before success */}
        {!success && (
          <form className="auth-form" onSubmit={handleSubmit} noValidate>

            <div className="auth-field">
              <label className="auth-field__label" htmlFor="fp-email">
                Email Address
              </label>
              <input
                id="fp-email"
                className="auth-field__input"
                type="email"
                placeholder="kavya@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
                autoComplete="email"
                autoFocus
                aria-required="true"
              />
            </div>

            <button
              type="submit"
              className="auth-btn auth-btn--primary"
              disabled={isLoading}
            >
              {isLoading
                ? <span className="auth-btn__spinner" />
                : "Send Reset Link"
              }
            </button>

          </form>
        )}

        {/* Back to login */}
        <p className="auth-card__footer">
          Remember your password?{" "}
          <button className="auth-link" type="button" onClick={onGoLogin}>
            Back to Sign In
          </button>
        </p>

      </div>

      {/* ── Page footer ─────────────────────────────────────── */}
      <footer className="auth-page-footer">
        Kavya S &copy; 2026
      </footer>

    </div>
  );
}
