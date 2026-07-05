/**
 * RequirementsCard.jsx
 * --------------------
 * Displays the structured requirements that Gemini extracted from the
 * user's natural-language query.
 *
 * Props:
 *   requirements {object} - { category, budget, features[] }
 */

function RequirementsCard({ requirements }) {
  if (!requirements) return null;

  const { category, budget, features } = requirements;

  return (
    <section className="requirements-card" aria-label="Extracted requirements">
      <h2 className="requirements-card__title">What we understood</h2>
      <ul className="requirements-card__list">
        <li>
          <span className="requirements-card__label">Category:</span>{" "}
          <span className="requirements-card__value">{category || "—"}</span>
        </li>
        <li>
          <span className="requirements-card__label">Budget:</span>{" "}
          <span className="requirements-card__value">
            {budget > 0 ? `₹${budget.toLocaleString("en-IN")}` : "Not specified"}
          </span>
        </li>
        <li>
          <span className="requirements-card__label">Features:</span>{" "}
          <span className="requirements-card__value">
            {features && features.length > 0 ? features.join(", ") : "None"}
          </span>
        </li>
      </ul>
    </section>
  );
}

export default RequirementsCard;
