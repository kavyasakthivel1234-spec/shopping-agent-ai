/**
 * api.js
 * ------
 * Centralised API communication layer — Phase 4.
 *
 * All HTTP calls go through this module — components never use fetch directly.
 *
 * In development : Vite proxies /api/* → http://localhost:8000
 * In production  : requests go to VITE_API_URL (baked in at build time)
 */

// Base URL: empty string in dev (proxy handles it), set in production builds
const API_BASE = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL
  : "";

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------

/**
 * Generic fetch wrapper that throws a descriptive Error on non-2xx responses.
 * @param {string} path   - e.g. "/api/recommend"
 * @param {RequestInit} options
 * @returns {Promise<any>} Parsed JSON body
 */
async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const token = localStorage.getItem("sa_token");
  
  const headers = { 
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
    console.debug(`[api] ${options.method || "GET"} ${path} — token: ${token.slice(0, 20)}...`);
  } else {
    console.debug(`[api] ${options.method || "GET"} ${path} — NO TOKEN`);
  }

  const response = await fetch(url, {
    ...options,
    headers,
    redirect: "follow",
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const errorText = await response.text();
      console.error(`[api] Backend error response:`, errorText);
      try {
        const body = JSON.parse(errorText);
        detail = body.detail || errorText || detail;
      } catch {
        detail = errorText || detail;
      }
    } catch { /* couldn't read body */ }

    // Auto-logout on 401 — stale or mismatched token
    if (response.status === 401) {
      console.warn(`[api] 401 on ${path} — clearing stale session. User must log in again.`);
      localStorage.removeItem("sa_token");
      localStorage.removeItem("sa_user");
      // Reload the page — AuthProvider will see no token and show login
      window.location.reload();
      return;   // prevent the error from propagating during reload
    }

    throw new Error(`Request failed (${response.status}): ${detail}`);
  }

  return response.json();
}

// ---------------------------------------------------------------------------
// Phase 1 — Recommendations
// ---------------------------------------------------------------------------
export async function getRecommendations(query) {
  return request("/api/recommend", { method: "POST", body: JSON.stringify({ query }) });
}

// ---------------------------------------------------------------------------
// Phase 2 — Pros & Cons
// ---------------------------------------------------------------------------
export async function getProsAndCons(productId) {
  return request(`/api/pros-cons/${productId}`);
}

// ---------------------------------------------------------------------------
// Phase 2 — Comparison
// ---------------------------------------------------------------------------
export async function compareProducts(product1Id, product2Id) {
  return request("/api/compare", {
    method: "POST",
    body: JSON.stringify({ product1_id: product1Id, product2_id: product2Id }),
  });
}

// ---------------------------------------------------------------------------
// Phase 2 — Review Summary
// ---------------------------------------------------------------------------
export async function getReviewSummary(productId) {
  return request(`/api/reviews/${productId}/summary`);
}

// ---------------------------------------------------------------------------
// Phase 3 — Multi-agent Assistant
// ---------------------------------------------------------------------------
export async function runAssistant(query) {
  return request("/api/assistant", { method: "POST", body: JSON.stringify({ query }) });
}

// ---------------------------------------------------------------------------
// History  (MongoDB, JWT-protected)
// ---------------------------------------------------------------------------
export async function getHistory() {
  return request("/api/history");
}

export async function clearHistory() {
  return request("/api/history", { method: "DELETE" });
}

export async function deleteHistoryEntry(entryId) {
  return request(`/api/history/${entryId}`, { method: "DELETE" });
}

// ── Chat session  ───────────────────────────────────────────────

/**
 * PUT /api/chats/session  — upsert (create or update) the current session.
 * Called after every assistant response to persist the conversation.
 * No IDs needed — backend finds the session by userId automatically.
 */
export async function upsertSession(chatData) {
  return request("/api/chats/session", {
    method: "PUT",
    body:   JSON.stringify(chatData),
  });
}
