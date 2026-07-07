/**
 * api.js
 * ------
 * Centralised API communication layer.
 * Authentication removed — all requests are public.
 *
 * Development:  Vite proxy forwards /api/* → http://localhost:8000
 * Production:   requests go to VITE_API_URL
 */

const API_BASE = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace(/\/$/, "")
  : "";

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;

  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
    redirect: "follow",
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const text = await response.text();
      try {
        const body = JSON.parse(text);
        detail = body.detail || text || detail;
      } catch {
        detail = text || detail;
      }
    } catch { /* couldn't read body */ }
    throw new Error(`Request failed (${response.status}): ${detail}`);
  }

  return response.json();
}

// ---------------------------------------------------------------------------
// Recommendations
// ---------------------------------------------------------------------------
export async function getRecommendations(query) {
  return request("/api/recommend", { method: "POST", body: JSON.stringify({ query }) });
}

// ---------------------------------------------------------------------------
// Pros & Cons
// ---------------------------------------------------------------------------
export async function getProsAndCons(productId) {
  return request(`/api/pros-cons/${productId}`);
}

// ---------------------------------------------------------------------------
// Comparison
// ---------------------------------------------------------------------------
export async function compareProducts(product1Id, product2Id) {
  return request("/api/compare", {
    method: "POST",
    body: JSON.stringify({ product1_id: product1Id, product2_id: product2Id }),
  });
}

// ---------------------------------------------------------------------------
// Review Summary
// ---------------------------------------------------------------------------
export async function getReviewSummary(productId) {
  return request(`/api/reviews/${productId}/summary`);
}

// ---------------------------------------------------------------------------
// Multi-agent Assistant
// ---------------------------------------------------------------------------
export async function runAssistant(query) {
  return request("/api/assistant", { method: "POST", body: JSON.stringify({ query }) });
}

// ---------------------------------------------------------------------------
// History (public, no auth)
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

// ---------------------------------------------------------------------------
// Chat session persistence (public, no auth)
// ---------------------------------------------------------------------------
export async function upsertSession(chatData) {
  return request("/api/chats/session", {
    method: "PUT",
    body:   JSON.stringify(chatData),
  });
}
