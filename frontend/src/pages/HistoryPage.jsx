/**
 * HistoryPage.jsx
 * ---------------
 * Persistent chat history — loaded from MongoDB.
 * Shows every assistant exchange the logged-in user has made,
 * newest first.  Survives page refresh and re-login.
 *
 * Each entry displays:
 *   - User query + timestamp
 *   - For shopping results: product cards (image, price, rating, brand, buy link)
 *   - For chat replies: the text message
 */

import { useState, useEffect } from "react";
import { getHistory, clearHistory, deleteHistoryEntry } from "../services/api";

// ─────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────

function formatDate(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString("en-IN", {
      day: "2-digit", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit", hour12: true,
    });
  } catch {
    return iso;
  }
}

function formatPrice(val) {
  if (!val && val !== 0) return null;
  return Number(val).toLocaleString("en-IN", {
    style: "currency", currency: "INR", maximumFractionDigits: 0,
  });
}

function StarRating({ rating }) {
  if (!rating) return null;
  const full  = Math.floor(rating);
  const half  = rating % 1 >= 0.5;
  const empty = 5 - full - (half ? 1 : 0);
  return (
    <span className="hist-card__stars">
      {"★".repeat(full)}{half ? "½" : ""}{"☆".repeat(empty)}
      <span className="hist-card__rating-num"> {rating}</span>
    </span>
  );
}

// ─────────────────────────────────────────────────────────
// Mini product card (used inside history entries)
// ─────────────────────────────────────────────────────────

function HistoryProductCard({ product, isTop }) {
  if (!product) return null;
  const img   = product.image || product.thumbnail;
  const price = formatPrice(product.price);
  const discount =
    product.old_price && product.price && product.old_price > product.price
      ? Math.round(((product.old_price - product.price) / product.old_price) * 100)
      : null;

  return (
    <div className={`hist-product${isTop ? " hist-product--top" : ""}`}>
      {isTop && <span className="hist-product__badge">Top Pick</span>}
      {discount && <span className="hist-product__discount">{discount}% off</span>}

      {img && (
        <div className="hist-product__img-wrap">
          <img
            src={img}
            alt={product.name}
            className="hist-product__img"
            loading="lazy"
            onError={(e) => { e.currentTarget.closest(".hist-product__img-wrap").style.display = "none"; }}
          />
        </div>
      )}

      <p className="hist-product__name">{product.name}</p>

      <div className="hist-product__price-row">
        {price
          ? <span className="hist-product__price">{price}</span>
          : <span className="hist-product__na">Price N/A</span>
        }
        {product.old_price && product.price && (
          <span className="hist-product__old-price">{formatPrice(product.old_price)}</span>
        )}
      </div>

      <div className="hist-product__rating-row">
        <StarRating rating={product.rating} />
        {product.reviews && (
          <span className="hist-product__reviews">
            ({Number(product.reviews).toLocaleString("en-IN")})
          </span>
        )}
      </div>

      {product.brand && (
        <p className="hist-product__meta">
          <span className="hist-product__meta-label">Brand:</span> {product.brand}
        </p>
      )}

      {product.seller && (
        <p className="hist-product__meta">
          <span className="hist-product__meta-label">Seller:</span> {product.seller}
        </p>
      )}

      {product.link && (
        <a
          href={product.link}
          target="_blank"
          rel="noopener noreferrer"
          className="hist-product__buy-btn"
        >
          Buy on Amazon
        </a>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// Single history entry
// ─────────────────────────────────────────────────────────

function HistoryEntry({ entry, onDelete }) {
  const { query, type, response, createdAt } = entry;
  const [expanded, setExpanded] = useState(false);

  // Shopping response
  const isShoping = type === "shopping";
  const topPick      = response?.top_pick;
  const alternatives = response?.alternatives || [];
  const filters      = response?.filters || {};
  const confidence   = response?.confidence;

  // Chat / comparison
  const chatMsg = response?.message || response?.chat_text;

  // Filter chips
  const chips = [];
  if (filters.product)                          chips.push({ label: filters.product,                        cls: "chip--category" });
  if (filters.brand)                            chips.push({ label: `Brand: ${filters.brand}`,              cls: "chip--brand" });
  if (filters.maxPrice)                         chips.push({ label: `Under ₹${Number(filters.maxPrice).toLocaleString("en-IN")}`, cls: "chip--budget" });
  if (filters.minRating)                        chips.push({ label: `★ ${filters.minRating}+`,              cls: "chip--rating" });
  if (filters.color)                            chips.push({ label: filters.color,                           cls: "chip--feature" });
  if (filters.ram)                              chips.push({ label: `RAM: ${filters.ram}`,                   cls: "chip--feature" });
  if (filters.storage)                          chips.push({ label: filters.storage,                         cls: "chip--feature" });

  const hasProducts = isShoping && (topPick || alternatives.length > 0);
  const showCount   = expanded ? alternatives.length : Math.min(2, alternatives.length);

  return (
    <li className="hist-entry">
      {/* Header row */}
      <div className="hist-entry__header">
        <div className="hist-entry__left">
          <span className="hist-entry__type-badge hist-entry__type-badge--shopping">
            {type === "shopping" ? "Product Search" : type === "comparison" ? "Comparison" : "Chat"}
          </span>
          <span className="hist-entry__time">{formatDate(createdAt)}</span>
        </div>
        <button
          className="hist-entry__delete-btn"
          onClick={() => onDelete(entry.id)}
          aria-label="Delete this entry"
        >
          ✕
        </button>
      </div>

      {/* User query */}
      <p className="hist-entry__query">
        <span className="hist-entry__query-label">You asked:</span>{" "}
        &ldquo;{query}&rdquo;
      </p>

      {/* Filter chips */}
      {chips.length > 0 && (
        <div className="hist-entry__chips chip-row">
          {chips.map((c, i) => (
            <span key={i} className={`chip ${c.cls}`}>{c.label}</span>
          ))}
          {confidence > 0 && (
            <span className="chip chip--confidence">
              {Math.round(confidence * 100)}% match
            </span>
          )}
        </div>
      )}

      {/* Chat message */}
      {!hasProducts && chatMsg && (
        <p className="hist-entry__chat-msg">{chatMsg}</p>
      )}

      {/* Products */}
      {hasProducts && (
        <div className="hist-entry__products">
          {topPick && (
            <HistoryProductCard product={topPick} isTop />
          )}

          {alternatives.length > 0 && (
            <>
              <p className="hist-entry__alt-label">
                Alternatives ({alternatives.length})
              </p>
              <div className="hist-products-grid">
                {alternatives.slice(0, showCount).map((p, i) => (
                  <HistoryProductCard key={p.id || i} product={p} />
                ))}
              </div>

              {alternatives.length > 2 && (
                <button
                  className="hist-entry__expand-btn"
                  onClick={() => setExpanded((v) => !v)}
                >
                  {expanded
                    ? "Show less"
                    : `Show ${alternatives.length - 2} more`}
                </button>
              )}
            </>
          )}
        </div>
      )}
    </li>
  );
}

// ─────────────────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────────────────

export default function HistoryPage() {
  const [history,   setHistory]   = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error,     setError]     = useState(null);

  useEffect(() => { load(); }, []);

  async function load() {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getHistory();
      setHistory(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleClearAll() {
    if (!window.confirm("Clear your entire search history?")) return;
    try {
      await clearHistory();
      setHistory([]);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(entryId) {
    try {
      await deleteHistoryEntry(entryId);
      setHistory((prev) => prev.filter((e) => e.id !== entryId));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <main className="history-page">
      <header className="history-page__header">
        <div>
          <h1 className="history-page__title">Search History</h1>
          <p className="history-page__subtitle">
            Your past AI-powered searches — persisted across sessions
          </p>
        </div>
        {history.length > 0 && (
          <button
            className="history-page__clear-btn"
            onClick={handleClearAll}
            aria-label="Clear all history"
          >
            Clear All
          </button>
        )}
      </header>

      {isLoading && (
        <p className="history-page__loading" role="status">
          Loading history...
        </p>
      )}

      {error && (
        <div className="history-page__error" role="alert">
          <strong>Error:</strong> {error}
        </div>
      )}

      {!isLoading && history.length === 0 && (
        <div className="history-page__empty">
          <p>No history yet.</p>
          <p>Use the Assistant to search for products — results will appear here.</p>
        </div>
      )}

      {history.length > 0 && (
        <ul className="history-list">
          {history.map((entry) => (
            <HistoryEntry
              key={entry.id}
              entry={entry}
              onDelete={handleDelete}
            />
          ))}
        </ul>
      )}
    </main>
  );
}
