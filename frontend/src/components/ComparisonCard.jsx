/**
 * ComparisonCard.jsx
 * ------------------
 * Displays an AI-generated side-by-side product comparison in a table.
 *
 * Props:
 *   data {object} - Full response from POST /api/compare:
 *     {
 *       product1:   { name, price, … },
 *       product2:   { name, price, … },
 *       comparison: {
 *         camera:  { product1, product2 },
 *         battery: { product1, product2 },
 *         price:   { product1, product2 },
 *         winner:  string,
 *         summary: string
 *       }
 *     }
 *   onClose {function} - Called when the user dismisses the card
 */

function ComparisonCard({ data, onClose }) {
  if (!data) return null;

  const { product1, product2, comparison } = data;

  // Table rows: [ label, comparison key ]
  const rows = [
    ["Camera",  "camera"],
    ["Battery", "battery"],
    ["Price",   "price"],
  ];

  return (
    <section className="comparison-card" aria-label="Product comparison">
      {/* Header */}
      <div className="comparison-card__header">
        <h2 className="comparison-card__title">Side-by-Side Comparison</h2>
        <button
          className="comparison-card__close"
          onClick={onClose}
          aria-label="Close comparison"
        >
          ✕
        </button>
      </div>

      {/* Comparison table */}
      <div className="comparison-card__table-wrapper">
        <table className="comparison-table">
          <thead>
            <tr>
              <th className="comparison-table__attr">Attribute</th>
              <th className="comparison-table__product">{product1.name}</th>
              <th className="comparison-table__product">{product2.name}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([label, key]) => (
              <tr key={key}>
                <td className="comparison-table__label">{label}</td>
                <td className="comparison-table__value">
                  {comparison[key]?.product1 ?? "—"}
                </td>
                <td className="comparison-table__value">
                  {comparison[key]?.product2 ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Winner banner */}
      {comparison.winner && (
        <div className="comparison-card__winner" aria-live="polite">
          <strong>Our Pick:</strong> {comparison.winner}
        </div>
      )}

      {/* AI summary */}
      {comparison.summary && (
        <p className="comparison-card__summary">{comparison.summary}</p>
      )}
    </section>
  );
}

export default ComparisonCard;
