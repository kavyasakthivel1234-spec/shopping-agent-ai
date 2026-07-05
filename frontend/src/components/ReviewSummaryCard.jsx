/**
 * ReviewSummaryCard.jsx
 * ---------------------
 * Displays an AI-generated review summary (liked / disliked topics).
 * Fetches data lazily when the user clicks "View Reviews".
 *
 * Props:
 *   productId   {string} - e.g. "sp-001"
 *   productName {string} - shown in the accessible label
 */

import { useState } from "react";
import { getReviewSummary } from "../services/api";

function ReviewSummaryCard({ productId, productName }) {
  const [data, setData]           = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError]         = useState(null);
  const [isOpen, setIsOpen]       = useState(false);

  /**
   * Fetch review summary on first open; cache for subsequent toggles.
   */
  async function handleToggle() {
    if (!isOpen && !data && !isLoading) {
      setIsLoading(true);
      setError(null);
      try {
        const result = await getReviewSummary(productId);
        setData(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    }
    setIsOpen((prev) => !prev);
  }

  return (
    <div className="review-summary-card">
      <button
        className="review-summary-card__toggle"
        onClick={handleToggle}
        aria-expanded={isOpen}
        aria-controls={`reviews-${productId}`}
        aria-label={`View reviews for ${productName}`}
      >
        {isOpen ? "▲" : "▼"} Customer Reviews
      </button>

      {isOpen && (
        <div id={`reviews-${productId}`} className="review-summary-card__body">
          {isLoading && (
            <p className="review-summary-card__loading" role="status">
              ⏳ Summarising reviews…
            </p>
          )}

          {error && (
            <p className="review-summary-card__error" role="alert">
              {error}
            </p>
          )}

          {data && (
            <>
              <p className="review-summary-card__count">
                Based on {data.review_count} reviews
              </p>
              <div className="review-summary-card__columns">
                {/* Liked topics */}
                <div className="review-summary-card__column review-summary-card__column--liked">
                  <h4>👍 Liked</h4>
                  <ul>
                    {data.liked.map((topic, i) => (
                      <li key={i}>{topic}</li>
                    ))}
                  </ul>
                </div>

                {/* Disliked topics */}
                <div className="review-summary-card__column review-summary-card__column--disliked">
                  <h4>👎 Disliked</h4>
                  <ul>
                    {data.disliked.map((topic, i) => (
                      <li key={i}>{topic}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default ReviewSummaryCard;
