/**
 * AssistantPage.jsx
 * -----------------
 * Page wrapper for the Phase 3 chat-style AI assistant.
 *
 * Renders the ChatAssistant component inside a centred page layout.
 * Navigation between this page and HomePage is handled in App.jsx.
 */

import ChatAssistant from "../components/ChatAssistant";

function AssistantPage() {
  return (
    <main className="assistant-page">
      <ChatAssistant />
    </main>
  );
}

export default AssistantPage;
