/**
 * RecommendationList.jsx
 * ----------------------
 * Renders the full list of recommended products using the Phase 2 shape:
 *   - top_pick    : single top recommendation, prominently displayed
 *   - alternatives: remaining options
 *
 * Manages compare-slot state: when the user presses Compare on two products,
 * triggers the API call and surfaces the ComparisonCard.
 *
 * Props:
 *   topPick      {object|null} - Highest-scoring product
 *   alternatives {Array}       - Remaining scored products
 */

import { useState } from "react";
import ProductCard from "./ProductCard";
import ComparisonCard from "./ComparisonCard";
import { compareProducts } from "../services/api";

function RecommendationList({ topPick, alternatives }) {
  // ── Comparison state ──────────────────────────────────────────────
  // Up to two products can be selected; when both are chosen the API is called.
  const [compareSlots, setCompareSlots]       = useState([]);   // [product, …]
  const [comparisonData, setComparisonData]   = useState(null);
  const [isComparing, setIsComparing]         = useState(false);
  const [compareError, setCompareError]       = useState(null);

  // Guard: nothing to render
  if (!topPick && (!alternatives || alternatives.length === 0)) return null;

  const allProducts = topPick
    ? [topPick, ...(alternatives || [])]
    : alternatives || [];

  /**
   * Toggle a product in/out of the compare slots.
   * When both slots are filled, automatically trigger the comparison.
   */
  async function handleSelectCompare(product) {
    // If already selected → deselect
    if (compareSlots.some((p) => p.id === product.id)) {
      setCompareSlots((prev) => prev.filter((p) => p.id !== product.id));
      setComparisonData(null);
      return;
    }

    // If both slots already full, replace the second one
    const newSlots = compareSlots.length >= 2
      ? [compareSlots[0], product]
      : [...compareSlots, product];

    setCompareSlots(newSlots);

    // Trigger comparison once both slots are filled
    if (newSlots.length === 2) {
      setIsComparing(true);
      setCompareError(null);
      setComparisonData(null);
      try {
        const result = await compareProducts(newSlots[0].id, newSlots[1].id);
        setComparisonData(result);
      } catch (err) {
        setCompareError(err.message);
      } finally {
        setIsComparing(false);
      }
    }
  }

  /** Dismiss the comparison panel and clear slots. */
  function handleCloseComparison() {
    setComparisonData(null);
    setCompareSlots([]);
    setCompareError(null);
  }

  return (
    <section aria-label="Recommended products">

      {/* ── Compare hint ─────────────────────────────────────────── */}
      <div className="compare-hint" aria-live="polite">
        {compareSlots.length === 0 && (
          <p>Press <strong>Compare</strong> on any two products to compare them side-by-side.</p>
        )}
        {compareSlots.length === 1 && (
          <p><strong>{compareSlots[0].name}</strong> selected — pick one more to compare.</p>
        )}
        {compareSlots.length === 2 && (
          <p>Comparing <strong>{compareSlots[0].name}</strong> vs <strong>{compareSlots[1].name}</strong>...</p>
        )}
      </div>

      {/* ── Comparing spinner ────────────────────────────────────── */}
      {isComparing && (
        <p className="compare-loading" role="status" aria-live="polite">
          Running AI comparison...
        </p>
      )}

      {/* ── Compare error ────────────────────────────────────────── */}
      {compareError && (
        <div className="compare-error" role="alert">
          <strong>Comparison failed:</strong> {compareError}
        </div>
      )}

      {/* ── Comparison table ─────────────────────────────────────── */}
      {comparisonData && (
        <ComparisonCard data={comparisonData} onClose={handleCloseComparison} />
      )}

      {/* ── Top pick ─────────────────────────────────────────────── */}
      {topPick && (
        <div className="recommendation-section">
          <h2 className="recommendation-section__title">Top Recommendation</h2>
          <ul className="recommendation-list__items">
            <li>
              <ProductCard
                product={topPick}
                rank={1}
                isTopPick={true}
                isSelectedForCompare={compareSlots.some((p) => p.id === topPick.id)}
                onSelectCompare={handleSelectCompare}
              />
            </li>
          </ul>
        </div>
      )}

      {/* ── Alternatives ─────────────────────────────────────────── */}
      {alternatives && alternatives.length > 0 && (
        <div className="recommendation-section">
          <h2 className="recommendation-section__title">Alternatives</h2>
          <ul className="recommendation-list__items">
            {alternatives.map((product, index) => (
              <li key={product.id}>
                <ProductCard
                  product={product}
                  rank={index + 2}
                  isTopPick={false}
                  isSelectedForCompare={compareSlots.some((p) => p.id === product.id)}
                  onSelectCompare={handleSelectCompare}
                />
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Empty state ──────────────────────────────────────────── */}
      {allProducts.length === 0 && (
        <p className="recommendation-list__empty">
          No products found matching your requirements. Try adjusting your budget or features.
        </p>
      )}
    </section>
  );
}

export default RecommendationList;
