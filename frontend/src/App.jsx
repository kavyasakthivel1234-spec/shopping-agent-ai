/**
 * App.jsx
 * -------
 * Root component — no authentication required.
 * Opens directly on the AI Shopping Assistant page.
 *
 * Tabs:
 *   Assistant | History
 */

import { useState, useEffect } from "react";
import AssistantPage from "./pages/AssistantPage";
import HistoryPage   from "./pages/HistoryPage";
import "./App.css";

const APP_TABS = [
  { id: "assistant", label: "Assistant" },
  { id: "history",   label: "History" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("assistant");

  // Force dark mode
  useEffect(() => {
    document.documentElement.classList.add("dark");
  }, []);

  return (
    <div className="app">
      {/* Top bar */}
      <div className="app-topbar">
        <div className="app-logo">SHOPPING AI</div>

        <nav className="app-nav" aria-label="Main navigation">
          {APP_TABS.map((tab) => (
            <button
              key={tab.id}
              className={`app-nav__tab ${activeTab === tab.id ? "app-nav__tab--active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
              aria-current={activeTab === tab.id ? "page" : undefined}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Pages */}
      {activeTab === "assistant" && <AssistantPage />}
      {activeTab === "history"   && <HistoryPage />}
    </div>
  );
}
