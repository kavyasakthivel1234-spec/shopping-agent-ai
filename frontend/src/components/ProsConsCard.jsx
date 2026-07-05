/**
 * ProsConsCard.jsx
 * ----------------
 * Displays AI-generated pros and cons for a product.
 * Fetches data lazily when the user clicks "View Pros & Cons".
 *
 * Props:
 *   productId   {string} - e.g. "sp-001"
 *   productName {string} - Display name shown in the heading
 */

import { useState } from "react";
import { getProsAndCons } from "../services/api";

function ProsConsCard({ productId, productName }) {
  const [data, setData]           = useState(null);   // { pros[], cons[] }
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError]         = useState(null);
  const [isOpen, setIsOpen]       = useState(false);  // accordion toggle

  /**
   * Fetch pros & cons from the API on first open; subsequent toggles
   * reuse the cached data without re-fetching.
   */
  async function handleToggle() {
    if (!isOpen && !data && !isLoading) {
      setIsLoading(true);
      setError(null);
      try {
        const result = await getProsAndCons(productId);
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
    <div className="pros-cons-card">
      {/* Accordion toggle button */}
      <button
        className="pros-cons-card__toggle"
        onClick={handleToggle}
        aria-expanded={isOpen}
        aria-controls={`pros-cons-${productId}`}
      >
        {isOpen ? "▲" : "▼"} Pros &amp; Cons
      </button>

      {/* Expanded content */}
      {isOpen && (
        <div id={`pros-cons-${productId}`} className="pros-cons-card__body">
          {/* Loading */}
          {isLoading && (
            <p className="pros-cons-card__loading" role="status">
              ⏳ Generating AI analysis…
            </p>
          )}

          {/* Error */}
          {error && (
            <p className="pros-cons-card__error" role="alert">
              {error}
            </p>
          )}

          {/* Content */}
          {data && (
            <div className="pros-cons-card__columns">
              {/* Pros column */}
              <div className="pros-cons-card__column pros-cons-card__column--pros">
                <h4 className="pros-cons-card__column-title">✅ Pros</h4>
                <ul>
                  {data.pros.map((pro, i) => (
                    <li key={i}>{pro}</li>
                  ))}
                </ul>
              </div>

              {/* Cons column */}
              <div className="pros-cons-card__column pros-cons-card__column--cons">
                <h4 className="pros-cons-card__column-title">❌ Cons</h4>
                <ul>
                  {data.cons.map((con, i) => (
                    <li key={i}>{con}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ProsConsCard;
