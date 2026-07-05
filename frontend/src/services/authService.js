/**
 * authService.js
 * --------------
 * Fetch wrappers for all authentication API calls.
 *
 * URL strategy:
 *   Development : API_BASE = ""  → relative paths → Vite proxy → http://localhost:8000
 *   Production  : API_BASE = VITE_API_URL
 *
 * Do NOT set VITE_API_URL in .env.local during local development —
 * leave it unset so Vite's proxy handles routing automatically.
 */

const API_BASE = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace(/\/$/, "")
  : "";

/**
 * Generic fetch helper that extracts FastAPI error details from response body.
 */
async function authRequest(path, options = {}) {
  const url = `${API_BASE}${path}`;

  console.log(`[authService] ${options.method || "GET"} ${url}`);

  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const body = await response.json().catch(() => ({}));

  if (!response.ok) {
    let message = response.statusText;
    if (typeof body.detail === "string") {
      message = body.detail;
    } else if (Array.isArray(body.detail)) {
      message = body.detail.map((e) => e.msg || String(e)).join(", ");
    }
    console.error(`[authService] Error ${response.status}:`, message);
    throw new Error(message);
  }

  return body;
}

// ---------------------------------------------------------------------------
// Signup
// ---------------------------------------------------------------------------
export async function signup(data) {
  return authRequest("/api/auth/signup", {
    method: "POST",
    body:   JSON.stringify(data),
  });
}

// ---------------------------------------------------------------------------
// Login — email or mobile + password
// ---------------------------------------------------------------------------
export async function login(data) {
  return authRequest("/api/auth/login", {
    method: "POST",
    body:   JSON.stringify(data),
  });
}

// ---------------------------------------------------------------------------
// Profile (protected)
// ---------------------------------------------------------------------------
export async function getProfile(token) {
  return authRequest("/api/auth/profile", {
    headers: {
      "Content-Type":  "application/json",
      "Authorization": `Bearer ${token}`,
    },
  });
}

// ---------------------------------------------------------------------------
// Forgot password — request a reset email
// ---------------------------------------------------------------------------

/**
 * POST /api/auth/forgot-password
 *
 * Always returns a generic message (no email enumeration).
 * In development, the backend prints the reset link to the terminal.
 *
 * @param {string} email — registered email address
 * @returns {Promise<{ message: string }>}
 */
export async function forgotPassword(email) {
  return authRequest("/api/auth/forgot-password", {
    method: "POST",
    body:   JSON.stringify({ email }),
  });
}

// ---------------------------------------------------------------------------
// Reset password — set a new password using the JWT token
// ---------------------------------------------------------------------------

/**
 * POST /api/auth/reset-password
 *
 * @param {string} token    — JWT from the reset email link (?token=...)
 * @param {string} password — new password (8–72 characters)
 * @returns {Promise<{ message: string }>}
 */
export async function resetPassword(token, password) {
  return authRequest("/api/auth/reset-password", {
    method: "POST",
    body:   JSON.stringify({ token, password }),
  });
}
