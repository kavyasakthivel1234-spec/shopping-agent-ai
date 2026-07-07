/**
 * ChatAssistant.jsx
 * -----------------
 * Persistent chat interface for the AI Shopping Assistant.
 *
 * Persistence strategy — two layers:
 *
 *   1. sessionStorage  (primary, instant)
 *      Key: "sa_chat_messages"
 *      Written after every message update.
 *      Survives: tab switches, navigation between pages, F5 refresh.
 *      Cleared:  on page close (sessionStorage is tab-scoped).
 *
 *   2. MongoDB via PUT /api/chats/session  (backup, background)
 *      Written fire-and-forget after every AI response.
 *      History page reads these stored sessions independently.
 */

import { useState, useRef, useEffect, useCallback } from "react";
import ComparisonCard from "./ComparisonCard";
import { upsertSession } from "../services/api";

// ─────────────────────────────────────────────────────────
// sessionStorage key
// ─────────────────────────────────────────────────────────
const SESSION_KEY = "sa_chat_messages";

function loadFromSession() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveToSession(msgs) {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(msgs));
  } catch {
    // sessionStorage full or unavailable — silently skip
  }
}

// ─────────────────────────────────────────────────────────
// Markdown renderer (safe — HTML-escaped before parsing)
// ─────────────────────────────────────────────────────────
function renderMarkdown(text) {
  if (!text) return null;
  let html = text
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g,     "<em>$1</em>")
    .replace(/```(?:[a-z]+)?\n([\s\S]*?)\n```/gi, '<pre class="chat-code-block"><code>$1</code></pre>')
    .replace(/`([^`]+)`/g,  '<code class="chat-inline-code">$1</code>')
    .replace(/^###\s+(.+)$/gm, '<h3 class="chat-markdown-h3">$1</h3>')
    .replace(/^##\s+(.+)$/gm,  '<h2 class="chat-markdown-h2">$1</h2>')
    .replace(/^#\s+(.+)$/gm,   '<h1 class="chat-markdown-h1">$1</h1>')
    .replace(/^\s*[-*]\s+(.+)$/gm, '<li class="chat-markdown-li">$1</li>')
    .replace(/\n/g, "<br />");
  return <div dangerouslySetInnerHTML={{ __html: html }} className="chat-markdown-body" />;
}

// ─────────────────────────────────────────────────────────
// Price / rating helpers
// ─────────────────────────────────────────────────────────
function formatPrice(val) {
  if (val === null || val === undefined || val === 0) return null;
  return Number(val).toLocaleString("en-IN", {
    style: "currency", currency: "INR", maximumFractionDigits: 0,
  });
}

function StarRating({ rating }) {
  if (rating === null || rating === undefined)
    return <span className="product-card__na">Not Available</span>;
  const full  = Math.floor(rating);
  const half  = rating % 1 >= 0.5;
  const empty = 5 - full - (half ? 1 : 0);
  return (
    <span className="product-card__stars" aria-label={`${rating} out of 5 stars`}>
      {"★".repeat(full)}{half ? "½" : ""}{"☆".repeat(empty)}
      <span className="product-card__rating-num"> {rating}</span>
    </span>
  );
}

// ─────────────────────────────────────────────────────────
// Message bubbles
// ─────────────────────────────────────────────────────────
function UserBubble({ text }) {
  return (
    <div className="chat-message chat-message--user">
      <div className="chat-bubble chat-bubble--user">{text}</div>
      <div className="chat-avatar chat-avatar--user" aria-hidden="true">You</div>
    </div>
  );
}

function PlainTextBubble({ text }) {
  return (
    <div className="chat-message chat-message--ai">
      <div className="chat-avatar" aria-hidden="true">AI</div>
      <div className="chat-bubble chat-bubble--ai chat-bubble--plain">
        {renderMarkdown(text)}
      </div>
    </div>
  );
}

function ErrorBubble({ message }) {
  return (
    <div className="chat-message chat-message--ai">
      <div className="chat-avatar" aria-hidden="true">AI</div>
      <div className="chat-bubble chat-bubble--ai chat-bubble--error" role="alert">
        <strong>Error:</strong> {message}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// Filter chips — what Groq understood
// ─────────────────────────────────────────────────────────
function FilterChips({ filters, requirements }) {
  const chips = [];
  const product   = filters?.product   || requirements?.category;
  const brand     = filters?.brand;
  const maxPrice  = filters?.maxPrice  || requirements?.budget;
  const minRating = filters?.minRating;
  const color     = filters?.color;
  const size      = filters?.size;
  const storage   = filters?.storage;
  const ram       = filters?.ram;
  const features  = requirements?.features || [];

  if (product)      chips.push({ label: product,                                              cls: "chip--category" });
  if (brand)        chips.push({ label: `Brand: ${brand}`,                                    cls: "chip--brand"    });
  if (maxPrice > 0) chips.push({ label: `Under ₹${Number(maxPrice).toLocaleString("en-IN")}`, cls: "chip--budget"   });
  if (minRating)    chips.push({ label: `★ ${minRating}+`,                                    cls: "chip--rating"   });
  if (color)        chips.push({ label: color,                                                 cls: "chip--feature"  });
  if (size)         chips.push({ label: size,                                                  cls: "chip--feature"  });
  if (storage)      chips.push({ label: storage,                                               cls: "chip--feature"  });
  if (ram)          chips.push({ label: `RAM: ${ram}`,                                         cls: "chip--feature"  });
  features.forEach(f => chips.push({ label: f, cls: "chip--feature" }));

  if (!chips.length) return null;
  return (
    <div className="ai-card__requirements">
      <p className="ai-card__section-label">I understood:</p>
      <div className="chip-row">
        {chips.map((c, i) => (
          <span key={i} className={`chip ${c.cls}`}>{c.label}</span>
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// Full product card
// ─────────────────────────────────────────────────────────
function ProductCard({ product, isTopPick }) {
  if (!product) return null;

  const imgSrc   = product.image || product.thumbnail;
  const price    = formatPrice(product.price);
  const oldPrice = formatPrice(product.old_price);
  const discount =
    product.old_price && product.price && product.old_price > product.price
      ? Math.round(((product.old_price - product.price) / product.old_price) * 100)
      : null;

  return (
    <div className={`product-card${isTopPick ? " product-card--top" : ""}`}>
      {isTopPick && <div className="product-card__badge">Top Recommendation</div>}
      {discount   && <div className="product-card__discount-badge">{discount}% off</div>}

      {imgSrc ? (
        <div className="product-card__img-wrap">
          <img
            src={imgSrc} alt={product.name}
            className="product-card__img" loading="lazy"
            onError={(e) => { e.currentTarget.closest(".product-card__img-wrap").style.display = "none"; }}
          />
        </div>
      ) : (
        <div className="product-card__img-placeholder" aria-hidden="true">No Image</div>
      )}

      <p className="product-card__title">{product.name || product.title}</p>

      <div className="product-card__price-row">
        <span className="product-card__price">
          {price || <span className="product-card__na">Price Not Available</span>}
        </span>
        {oldPrice && <span className="product-card__old-price">{oldPrice}</span>}
      </div>

      <div className="product-card__rating-row">
        <StarRating rating={product.rating} />
        {product.reviews
          ? <span className="product-card__reviews">({Number(product.reviews).toLocaleString("en-IN")} reviews)</span>
          : <span className="product-card__na">(No reviews)</span>
        }
      </div>

      {product.bought_last_month && <p className="product-card__bought">{product.bought_last_month}</p>}

      <p className="product-card__meta">
        <span className="product-card__meta-label">Brand:</span>{" "}
        {product.brand || <span className="product-card__na">Not Available</span>}
      </p>
      <p className="product-card__meta">
        <span className="product-card__meta-label">Seller:</span>{" "}
        {product.seller || <span className="product-card__na">Not Available</span>}
      </p>
      <p className="product-card__meta">
        <span className="product-card__meta-label">Availability:</span>{" "}
        <span className={product.availability !== false ? "product-card__in-stock" : "product-card__out-stock"}>
          {product.availability !== false ? "In Stock" : "Out of Stock"}
        </span>
      </p>

      {product.delivery?.length > 0 && <p className="product-card__delivery">{product.delivery[0]}</p>}
      {product.offers?.length   > 0 && <p className="product-card__offer">{product.offers[0]}</p>}

      {product.link
        ? <a href={product.link} target="_blank" rel="noopener noreferrer" className="product-card__buy-btn">Buy on Amazon</a>
        : <span className="product-card__buy-btn product-card__buy-btn--disabled">Link Not Available</span>
      }
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// Review chips
// ─────────────────────────────────────────────────────────
function ReviewChips({ reviewSummary }) {
  if (!reviewSummary) return null;
  return (
    <div className="ai-card__reviews">
      <p className="ai-card__section-label">Based on {reviewSummary.review_count} reviews:</p>
      <div className="chip-row">
        {(reviewSummary.liked    || []).map((t, i) => <span key={`l${i}`} className="chip chip--liked">{t}</span>)}
        {(reviewSummary.disliked || []).map((t, i) => <span key={`d${i}`} className="chip chip--disliked">{t}</span>)}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// Pipeline trace
// ─────────────────────────────────────────────────────────
function PipelineTrace({ pipeline }) {
  if (!pipeline?.length) return null;
  return (
    <div className="ai-card__pipeline">
      <p className="ai-card__section-label">Pipeline:</p>
      <div className="pipeline-trace">
        {pipeline.map((a, i) => (
          <span key={a} className="pipeline-step">
            {a}{i < pipeline.length - 1 && <span className="pipeline-arrow"> → </span>}
          </span>
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// Shopping bubble
// ─────────────────────────────────────────────────────────
function ShoppingBubble({ data }) {
  const { requirements, top_pick, alternatives, review_summary, confidence, pipeline, filters } = data;
  return (
    <div className="chat-message chat-message--ai">
      <div className="chat-avatar" aria-hidden="true">AI</div>
      <div className="chat-bubble chat-bubble--ai">
        <FilterChips filters={filters} requirements={requirements} />

        {confidence > 0 && (
          <div className="ai-card__confidence">
            <span className="confidence-badge">Confidence: {Math.round(confidence * 100)}%</span>
          </div>
        )}

        {top_pick ? (
          <div className="ai-card__top-pick">
            <p className="ai-card__section-label">Top Pick</p>
            <ProductCard product={top_pick} isTopPick />
          </div>
        ) : (
          <p className="ai-card__no-results">No matching products found. Try a different search.</p>
        )}

        {alternatives?.length > 0 && (
          <div className="ai-card__alternatives">
            <p className="ai-card__section-label">Alternatives ({alternatives.length})</p>
            <div className="product-card-grid">
              {alternatives.slice(0, 3).map((p) => <ProductCard key={p.id} product={p} />)}
            </div>
            {alternatives.length > 3 && (
              <p className="ai-card__more">+{alternatives.length - 3} more</p>
            )}
          </div>
        )}

        {review_summary && <ReviewChips reviewSummary={review_summary} />}
        {pipeline        && <PipelineTrace pipeline={pipeline} />}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// Serialise a message array to MongoDB-safe format
// ─────────────────────────────────────────────────────────
function serialiseMessages(msgs) {
  return msgs
    .filter(m => m.type !== "error")   // don't persist error bubbles
    .map(m => ({
      id:   m.id,
      type: m.type,
      text: m.text || "",
      data: m.data || {},
    }));
}

// ─────────────────────────────────────────────────────────
// Main ChatAssistant component
// ─────────────────────────────────────────────────────────
export default function ChatAssistant() {
  // Initialise from sessionStorage so the chat survives tab switches and F5.
  const [messages,      setMessages]      = useState(() => loadFromSession());
  const [input,         setInput]         = useState("");
  const [isLoading,     setIsLoading]     = useState(false);
  const [currentStatus, setCurrentStatus] = useState("");

  const threadRef = useRef(null);

  // ── Auto-scroll whenever messages change ─────────────────
  useEffect(() => {
    if (threadRef.current)
      threadRef.current.scrollTop = threadRef.current.scrollHeight;
  }, [messages, isLoading]);

  // ── Persist to sessionStorage whenever messages change ───
  // This runs synchronously after every render so even a mid-render
  // crash won't lose the last message.
  useEffect(() => {
    saveToSession(messages);
  }, [messages]);

  // ── Persist to MongoDB (background, fire-and-forget) ─────
  // Called after every completed AI response so History works.
  const persistToMongo = useCallback(async (msgs) => {
    const payload = serialiseMessages(msgs);
    if (!payload.length) return;

    const firstUser = payload.find(m => m.type === "user");
    const title     = firstUser?.text?.slice(0, 60) || "Chat session";

    try {
      await upsertSession({ messages: payload, title });
    } catch (err) {
      // Non-fatal — sessionStorage already has the messages
      console.warn("[ChatAssistant] MongoDB persist failed (non-fatal):", err.message);
    }
  }, []);

  // ── Submit handler ────────────────────────────────────────
  async function handleSubmit(e) {
    e.preventDefault();
    const rawInput = input.trim();
    if (!rawInput || isLoading) return;

    const userMsgId = Date.now() + Math.random();
    const userMsg   = { id: userMsgId, type: "user", text: rawInput };

    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);
    setCurrentStatus("Analysing your request...");

    const controller = new AbortController();
    const timeout    = setTimeout(() => controller.abort(), 45_000);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || ""}/api/assistant`, {
        method:  "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body:   JSON.stringify({ query: rawInput }),
        signal: controller.signal,
      });

      clearTimeout(timeout);

      if (!response.ok) {
        let detail = response.statusText;
        try { const b = await response.json(); detail = b.detail || detail; } catch {}
        throw new Error(`Request failed (${response.status}): ${detail}`);
      }

      const data = await response.json();

      const aiMsgId = Date.now() + Math.random();
      let   aiMsg;

      if (data.type === "chat") {
        aiMsg = { id: aiMsgId, type: "ai-text", text: data.message };
      } else if (data.type === "shopping") {
        aiMsg = { id: aiMsgId, type: "ai-shopping", data: data.data };
      } else if (data.type === "comparison") {
        aiMsg = { id: aiMsgId, type: "ai-comparison", data: data.data };
      } else {
        aiMsg = { id: aiMsgId, type: "ai-text", text: JSON.stringify(data) };
      }

      setMessages(prev => {
        const next = [...prev, aiMsg];
        // Save to sessionStorage via the useEffect above, and also
        // fire background MongoDB persist for History.
        persistToMongo(next);
        return next;
      });

    } catch (err) {
      clearTimeout(timeout);
      console.error("[Assistant] Error:", err.message);

      const errorText = err.name === "AbortError"
        ? "Request timed out after 45 seconds. Please try again."
        : (err.message || "Something went wrong. Please try again.");

      setMessages(prev => [
        ...prev,
        { id: Date.now() + Math.random(), type: "error", text: errorText },
      ]);
    } finally {
      setIsLoading(false);
      setCurrentStatus("");
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) handleSubmit(e);
  }

  // ─────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────
  return (
    <div className="chat-assistant">
      {/* Header */}
      <header className="chat-header">
        <div className="chat-header__avatar" aria-hidden="true">AI</div>
        <div>
          <h2 className="chat-header__title">AI Shopping Assistant</h2>
          <p className="chat-header__subtitle">Groq AI · Llama 3.3 · Real Amazon Products</p>
        </div>
        <div className="chat-header__status">
          <span className="chat-header__status-dot" />
        </div>
      </header>

      {/* Thread */}
      <div className="chat-thread" ref={threadRef} aria-label="Conversation" aria-live="polite">
        {messages.length === 0 && !isLoading && (
          <div className="chat-thread__empty">
            <p className="chat-thread__empty-title">How can I help you today?</p>
            <p className="chat-thread__empty-hint">
              Try: <em>Samsung mobile under 20000 with 4+ stars</em>
            </p>
          </div>
        )}

        {messages.map((msg) => {
          if (msg.type === "user")          return <UserBubble      key={msg.id} text={msg.text} />;
          if (msg.type === "ai-text")       return <PlainTextBubble key={msg.id} text={msg.text} />;
          if (msg.type === "ai-shopping")   return <ShoppingBubble  key={msg.id} data={msg.data} />;
          if (msg.type === "ai-comparison") return (
            <div key={msg.id} className="chat-message chat-message--ai">
              <div className="chat-avatar" aria-hidden="true">AI</div>
              <div className="chat-bubble chat-bubble--ai">
                <ComparisonCard data={msg.data} onClose={() => {}} />
              </div>
            </div>
          );
          if (msg.type === "error") return <ErrorBubble key={msg.id} message={msg.text} />;
          return null;
        })}

        {isLoading && (
          <div className="chat-message chat-message--ai">
            <div className="chat-avatar" aria-hidden="true">AI</div>
            <div className="chat-bubble chat-bubble--ai chat-bubble--typing-wrap">
              {currentStatus && <span className="chat-status-text">{currentStatus}</span>}
              <div className="chat-bubble--typing" aria-label="AI is thinking">
                <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input bar */}
      <form className="chat-input-bar" onSubmit={handleSubmit}>
        <input
          className="chat-input-bar__field"
          type="text"
          placeholder="Describe what you're looking for... (e.g. Samsung phone under 20000 with 4+ stars)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          aria-label="Chat input"
          autoComplete="off"
        />
        <button
          className="chat-input-bar__send"
          type="submit"
          disabled={isLoading || !input.trim()}
          aria-label="Send"
        >
          {isLoading ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
}
