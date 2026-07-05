/**
 * ProductCard.jsx
 * ---------------
 * Full product card — supports both real Amazon (SerpAPI) and local data.
 *
 * Real products show:  thumbnail image, rating, review count, Buy Now button
 * Local products show: source badge, Compare, Save (no image/reviews)
 */

import ProsConsCard      from "./ProsConsCard";
import ReviewSummaryCard from "./ReviewSummaryCard";

/* ── Star rating display ──────────────────────────────────────── */
function StarRating({ rating }) {
  if (!rating || rating <= 0) return null;
  const full  = Math.floor(rating);
  const half  = rating - full >= 0.5;
  const empty = 5 - full - (half ? 1 : 0);

  return (
    <div className="product-card__stars" aria-label={`Rating: ${rating} out of 5`}>
      {"★".repeat(full)}
      {half ? "½" : ""}
      {"☆".repeat(empty)}
      <span className="product-card__rating-num">{rating.toFixed(1)}</span>
    </div>
  );
}

/* ── Data source badge — green = real Amazon, red = mock ──────── */
function DataSourceBadge({ dataMode, sourceType }) {
  const isReal = dataMode === "amazon" || sourceType === "Real";
  return (
    <div
      className={`product-card__data-badge ${isReal ? "product-card__data-badge--real" : "product-card__data-badge--mock"}`}
      aria-label={isReal ? "Real Amazon product" : "Mock/local product data"}
    >
      <span className="product-card__data-dot" />
      {isReal ? "Real Amazon Product" : "Mock Product"}
    </div>
  );
}

export default function ProductCard({ product, rank, isTopPick, isSelectedForCompare, onSelectCompare }) {
  const {
    id, name, price, camera, battery, score,
    source      = "Local",
    source_type = "Local",
    data_mode   = "mock",
    brand       = "",
    rating      = 0,
    reviews     = 0,
    link        = "",
    thumbnail   = "",
    availability = true,
  } = product;

  const isReal = data_mode === "amazon" || source_type === "Real";

  return (
    <article
      className={`product-card${isTopPick ? " product-card--top-pick" : ""}${isSelectedForCompare ? " product-card--selected" : ""}`}
      aria-label={`${isTopPick ? "Top pick: " : ""}Product ${rank}: ${name}`}
    >
      {/* Top-pick badge */}
      {isTopPick && (
        <div className="product-card__top-badge">Top Pick</div>
      )}

      <div className="product-card__main">

        {/* Thumbnail — only shown for real SerpAPI products */}
        {isReal && thumbnail && (
          <div className="product-card__image-wrap">
            <img
              src={thumbnail}
              alt={name}
              className="product-card__image"
              loading="lazy"
              onError={(e) => { e.currentTarget.style.display = "none"; }}
            />
          </div>
        )}

        {/* Rank (hidden when image is shown) */}
        {!isReal && (
          <div className="product-card__rank" aria-hidden="true">#{rank}</div>
        )}

        {/* Core info */}
        <div className="product-card__body">
          {/* Brand (when available) */}
          {brand && (
            <p className="product-card__brand">{brand}</p>
          )}

          <h3 className="product-card__name">{name}</h3>

          <p className="product-card__price">
            {price > 0
              ? price.toLocaleString("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 })
              : "Price not available"}
          </p>

          {/* Rating + review count */}
          {rating > 0 && (
            <div className="product-card__rating-row">
              <StarRating rating={rating} />
              {reviews > 0 && (
                <span className="product-card__reviews">
                  ({reviews.toLocaleString("en-IN")} reviews)
                </span>
              )}
            </div>
          )}

          {/* Specs */}
          <ul className="product-card__specs">
            {camera && camera !== "N/A" && (
              <li><span className="product-card__spec-label">Camera</span>{camera}</li>
            )}
            {battery && battery !== "N/A" && (
              <li><span className="product-card__spec-label">Battery</span>{battery}</li>
            )}
          </ul>

          {/* Availability */}
          {isReal && !availability && (
            <p className="product-card__unavailable">Currently unavailable</p>
          )}

          {/* Data source badge — always visible */}
          <DataSourceBadge dataMode={data_mode} sourceType={source_type} />
        </div>

        {/* Right-side actions */}
        <div className="product-card__actions">
          {score > 0 && (
            <div className="product-card__score">Score {score}</div>
          )}

          {/* Buy Now — only for real products with a link */}
          {isReal && link && (
            <a
              href={link}
              target="_blank"
              rel="noopener noreferrer"
              className="product-card__buy-btn"
              aria-label={`Buy ${name} on Amazon`}
            >
              Buy on Amazon
            </a>
          )}

          {/* Compare */}
          <button
            className={`product-card__compare-btn${isSelectedForCompare ? " product-card__compare-btn--active" : ""}`}
            onClick={() => onSelectCompare(product)}
            aria-pressed={isSelectedForCompare}
          >
            {isSelectedForCompare ? "Selected" : "Compare"}
          </button>
        </div>
      </div>

      {/* Lazy accordions */}
      <div className="product-card__accordions">
        <ProsConsCard      productId={id} productName={name} />
        <ReviewSummaryCard productId={id} productName={name} />
      </div>
    </article>
  );
}
