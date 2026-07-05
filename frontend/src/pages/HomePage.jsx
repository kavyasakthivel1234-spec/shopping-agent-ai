/**
 * HomePage.jsx
 * ------------
 * The main page of the AI Shopping Assistant — Phase 2.
 *
 * State managed here:
 *   - query        : current search input
 *   - isLoading    : true while the /api/recommend request is in-flight
 *   - error        : error message if the request failed
 *   - requirements : structured requirements extracted by Gemini
 *   - topPick      : highest-scoring product (Phase 2 shape)
 *   - alternatives : remaining scored products (Phase 2 shape)
 *
 * All child components receive only the props they need; no prop-drilling
 * beyond one level.
 */

import { useState } from "react";
import { getRecommendations } from "../services/api";
import SearchBar from "../components/SearchBar";
import RequirementsCard from "../components/RequirementsCard";
import RecommendationList from "../components/RecommendationList";

function HomePage() {
  const [query,        setQuery]        = useState("");
  const [isLoading,    setIsLoading]    = useState(false);
  const [error,        setError]        = useState(null);
  const [requirements, setRequirements] = useState(null);
  const [topPick,      setTopPick]      = useState(null);
  const [alternatives, setAlternatives] = useState([]);

  /**
   * Submit the query to the backend.
   * Resets all previous results before the new request.
   */
  async function handleSearch() {
    setError(null);
    setRequirements(null);
    setTopPick(null);
    setAlternatives([]);
    setIsLoading(true);

    try {
      const data = await getRecommendations(query);
      setRequirements(data.requirements);
      setTopPick(data.top_pick);
      setAlternatives(data.alternatives);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  const hasResults = topPick || (alternatives && alternatives.length > 0);

  return (
    <main className="home-page">
      {/* ── Header ────────────────────────────────────────────────── */}
      <header className="home-page__header">
        <h1 className="home-page__title">AI Shopping Assistant</h1>
        <p className="home-page__subtitle">
          Describe what you're looking for and we'll find the best matches for you.
        </p>
      </header>

      {/* ── Search bar ────────────────────────────────────────────── */}
      <section className="home-page__search">
        <SearchBar
          query={query}
          onChange={setQuery}
          onSubmit={handleSearch}
          isLoading={isLoading}
        />
      </section>

      {/* ── Loading indicator ─────────────────────────────────────── */}
      {isLoading && (
        <p className="home-page__loading" role="status" aria-live="polite">
          Analysing your query with AI...
        </p>
      )}

      {/* ── Error ─────────────────────────────────────────────────── */}
      {error && (
        <div className="home-page__error" role="alert">
          <strong>Something went wrong:</strong> {error}
        </div>
      )}

      {/* ── Results ───────────────────────────────────────────────── */}
      {!isLoading && requirements && (
        <>
          {/* What Gemini extracted */}
          <RequirementsCard requirements={requirements} />

          {/* Product recommendations */}
          {hasResults ? (
            <RecommendationList
              topPick={topPick}
              alternatives={alternatives}
            />
          ) : (
            <p className="home-page__no-results">
              No products matched your requirements. Try a different query or a higher budget.
            </p>
          )}
        </>
      )}
    </main>
  );
}

export default HomePage;
