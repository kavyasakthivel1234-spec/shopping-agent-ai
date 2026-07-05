/**
 * Signup.jsx
 * ----------
 * Signup page — premium dark-indigo / purple glassmorphism theme.
 * Direct registration: name + email + mobile + password. No OTP.
 *
 * Flow:
 *   1. User fills all fields
 *   2. Clicks "Create Account" → POST /api/auth/signup
 *   3. On success → auto-login via POST /api/auth/login → redirect to app
 *
 * Props:
 *   onSuccess {function} — called after successful signup + auto-login
 *   onGoLogin {function} — navigate to Login page
 */

import { useState } from "react";
import { useAuth }         from "../context/AuthContext";
import { signup, login }   from "../services/authService";
import "../auth.css";

/* ── SVG eye icons ────────────────────────────────────────────── */
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

const INITIAL = {
  name: "", email: "", mobile: "", password: "", confirmPassword: "",
};

export default function Signup({ onSuccess, onGoLogin }) {
  const { login: authLogin } = useAuth();

  const [form,          setForm]          = useState(INITIAL);
  const [showPassword,  setShowPassword]  = useState(false);
  const [showConfirm,   setShowConfirm]   = useState(false);
  const [isLoading,     setIsLoading]     = useState(false);
  const [error,         setError]         = useState("");

  function set(field) {
    return (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }));
  }

  function validate() {
    if (!form.name.trim() || form.name.trim().length < 2)
      return "Full name must be at least 2 characters.";
    if (!form.email.trim() || !form.email.includes("@"))
      return "Enter a valid email address.";
    if (!form.mobile.trim() || !/^\d{10,15}$/.test(form.mobile.trim()))
      return "Enter a valid mobile number (10–15 digits, digits only).";
    if (form.password.length < 6)
      return "Password must be at least 6 characters.";
    if (form.password !== form.confirmPassword)
      return "Passwords do not match.";
    return "";
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const err = validate();
    if (err) { setError(err); return; }

    setError("");
    setIsLoading(true);
    try {
      // 1 — Create account
      await signup({
        name:     form.name.trim(),
        email:    form.email.trim(),
        mobile:   form.mobile.trim(),
        password: form.password,
      });

      // 2 — Auto-login to obtain JWT
      const tokenData = await login({
        email:    form.email.trim(),
        password: form.password,
      });

      authLogin(tokenData.access_token, tokenData.user);
      if (onSuccess) onSuccess();
    } catch (e) {
      setError(e.message || "Signup failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="auth-page">

      {/* ── Glass card ──────────────────────────────────────── */}
      <div className="auth-card auth-card--wide">

        {/* Brand */}
        <div className="auth-card__brand">
          <div className="auth-card__logo">SA</div>
          <h1 className="auth-card__title">Shopping AI</h1>
          <p className="auth-card__subtitle">Create your account</p>
        </div>

        {/* Error banner */}
        {error && <div className="auth-error" role="alert">{error}</div>}

        <form className="auth-form" onSubmit={handleSubmit} noValidate>

          {/* Full Name */}
          <div className="auth-field">
            <label className="auth-field__label" htmlFor="su-name">Full Name</label>
            <input
              id="su-name"
              className="auth-field__input"
              type="text"
              placeholder="Kavya Sharma"
              value={form.name}
              onChange={set("name")}
              disabled={isLoading}
              autoComplete="name"
              aria-required="true"
            />
          </div>

          {/* Email */}
          <div className="auth-field">
            <label className="auth-field__label" htmlFor="su-email">Email Address</label>
            <input
              id="su-email"
              className="auth-field__input"
              type="email"
              placeholder="kavya@email.com"
              value={form.email}
              onChange={set("email")}
              disabled={isLoading}
              autoComplete="email"
              aria-required="true"
            />
          </div>

          {/* Mobile */}
          <div className="auth-field">
            <label className="auth-field__label" htmlFor="su-mobile">Mobile Number</label>
            <input
              id="su-mobile"
              className="auth-field__input"
              type="tel"
              placeholder="9876543210"
              value={form.mobile}
              onChange={set("mobile")}
              disabled={isLoading}
              autoComplete="tel"
              aria-required="true"
            />
          </div>

          {/* Password */}
          <div className="auth-field">
            <label className="auth-field__label" htmlFor="su-pw">Password</label>
            <div className="auth-field__password-wrap">
              <input
                id="su-pw"
                className="auth-field__input auth-field__input--password"
                type={showPassword ? "text" : "password"}
                placeholder="Minimum 6 characters"
                value={form.password}
                onChange={set("password")}
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
          </div>

          {/* Confirm Password */}
          <div className="auth-field">
            <label className="auth-field__label" htmlFor="su-confirm">Confirm Password</label>
            <div className="auth-field__password-wrap">
              <input
                id="su-confirm"
                className="auth-field__input auth-field__input--password"
                type={showConfirm ? "text" : "password"}
                placeholder="Re-enter your password"
                value={form.confirmPassword}
                onChange={set("confirmPassword")}
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

          {/* Submit */}
          <button
            type="submit"
            className="auth-btn auth-btn--primary"
            disabled={isLoading}
          >
            {isLoading ? <span className="auth-btn__spinner" /> : "Create Account"}
          </button>

        </form>

        {/* Switch to login */}
        <p className="auth-card__footer">
          Already have an account?{" "}
          <button className="auth-link" type="button" onClick={onGoLogin}>
            Sign in
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
