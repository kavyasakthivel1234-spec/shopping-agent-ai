/**
 * SearchBar.jsx
 * -------------
 * Controlled text-area + submit button for entering shopping queries.
 *
 * Props:
 *   query       {string}   - Current input value (controlled)
 *   onChange    {function} - Called with new value whenever the user types
 *   onSubmit    {function} - Called when the user clicks "Get Recommendations"
 *   isLoading   {boolean}  - Disables the form while a request is in-flight
 */

function SearchBar({ query, onChange, onSubmit, isLoading }) {
  /**
   * Handle form submission.
   * Prevents the default browser page reload and delegates to the parent.
   */
  function handleSubmit(e) {
    e.preventDefault();
    if (query.trim()) {
      onSubmit();
    }
  }

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <textarea
        className="search-bar__input"
        rows={3}
        placeholder="e.g. I need a smartphone under ₹20000 with a good camera and long battery life"
        value={query}
        onChange={(e) => onChange(e.target.value)}
        disabled={isLoading}
        aria-label="Shopping query"
      />
      <button
        className="search-bar__button"
        type="submit"
        disabled={isLoading || !query.trim()}
        aria-busy={isLoading}
      >
        {isLoading ? "Finding..." : "Get Recommendations"}
      </button>
    </form>
  );
}

export default SearchBar;
