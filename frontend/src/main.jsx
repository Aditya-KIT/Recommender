import React, { useState, useRef, useEffect } from "react";
import { createRoot } from "react-dom/client";
import { sendChat } from "./lib/api";
import "./style.css";

/* ─── Icons (inline SVG, no extra deps) ─────────────────────────────────────── */
const SendIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13" />
    <polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
);

const BotIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    <line x1="12" y1="3" x2="12" y2="7" />
    <circle cx="9" cy="16" r="1" fill="currentColor" />
    <circle cx="15" cy="16" r="1" fill="currentColor" />
  </svg>
);

const UserIcon = () => (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </svg>
);

const ExternalLinkIcon = () => (
  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
    <polyline points="15 3 21 3 21 9" />
    <line x1="10" y1="14" x2="21" y2="3" />
  </svg>
);

/* ─── Test type label map ────────────────────────────────────────────────────── */
const TYPE_LABEL = {
  K: "Knowledge",
  A: "Ability",
  P: "Personality",
  S: "Situational",
};

/* ─── Typing indicator ───────────────────────────────────────────────────────── */
function TypingIndicator() {
  return (
    <div className="typing">
      <div className="avatar bot">
        <BotIcon />
      </div>
      <div className="typing-bubble">
        <span className="dot-flashing" />
        <span className="dot-flashing" />
        <span className="dot-flashing" />
      </div>
    </div>
  );
}

/* ─── Single recommendation card ─────────────────────────────────────────────── */
function RecCard({ rec }) {
  const typeClass = `type-${rec.test_type}` || "type-K";
  const typeLabel = TYPE_LABEL[rec.test_type] || rec.test_type || "Test";

  return (
    <a
      className="rec-item"
      href={rec.url}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`${rec.name} - Open in SHL catalog`}
    >
      <div className="rec-item-top">
        <span className="rec-name">{rec.name}</span>
        <span className={`test-type-badge ${typeClass}`}>{typeLabel}</span>
      </div>
      <div className="rec-url-hint">
        <ExternalLinkIcon />
        View in SHL catalog
      </div>
    </a>
  );
}

/* ─── Legend ─────────────────────────────────────────────────────────────────── */
function Legend() {
  return (
    <div className="legend" aria-label="Test type legend">
      <p className="legend-title">Test Type Legend</p>
      <div className="legend-items">
        <div className="legend-item"><span className="legend-dot dot-K" />Knowledge (K)</div>
        <div className="legend-item"><span className="legend-dot dot-A" />Ability (A)</div>
        <div className="legend-item"><span className="legend-dot dot-P" />Personality (P)</div>
        <div className="legend-item"><span className="legend-dot dot-S" />Situational (S)</div>
      </div>
    </div>
  );
}

/* ─── Main App ───────────────────────────────────────────────────────────────── */
function App() {
  const INITIAL_MESSAGES = [
    {
      role: "assistant",
      content:
        "Hi! I'm your SHL Assessment Recommender. Tell me about the role you're hiring for — the job title, skills to evaluate, and seniority level — and I'll match it to the right SHL Individual Test Solutions.",
    },
  ];

  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [input, setInput] = useState("");
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to newest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setError("");
    const userMsg = { role: "user", content: text };

    // Only send role=user or role=assistant messages (skip the initial assistant greeting
    // that was never actually sent to the API). We filter system and convert all messages.
    const apiMessages = [
      ...messages.filter((m) => m.role === "user" || m.role === "assistant"),
      userMsg,
    ];

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const data = await sendChat(apiMessages);
      const assistantMsg = { role: "assistant", content: data.reply };
      setMessages((prev) => [...prev, assistantMsg]);
      setRecommendations(data.recommendations || []);
    } catch (err) {
      setError(
        "Could not reach the backend. Make sure the FastAPI server is running on http://localhost:8000."
      );
      // Remove the user message if the call failed so they can retry
      setMessages((prev) => prev.slice(0, -1));
      setInput(text);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  return (
    <div className="page">
      {/* ── Hero ── */}
      <header className="hero" role="banner">
        <div className="hero-badge" aria-label="Status: Active">
          <span className="dot" aria-hidden="true" />
          SHL Individual Test Solutions
        </div>
        <h1>Assessment Recommender</h1>
        <p className="hero-sub">
          Describe your hiring need and get a grounded shortlist from the official SHL catalog.
        </p>
      </header>

      {/* ── Main grid ── */}
      <main className="layout" aria-label="Main content">
        {/* ── Chat panel ── */}
        <section className="card chat-card" aria-label="Chat panel">
          <div className="messages-container" role="log" aria-live="polite" aria-label="Conversation">
            {messages.map((msg, i) => (
              <div key={i} className={`message ${msg.role}`} aria-label={`${msg.role} message`}>
                <div className={`avatar ${msg.role === "assistant" ? "bot" : "user-av"}`} aria-hidden="true">
                  {msg.role === "assistant" ? <BotIcon /> : <UserIcon />}
                </div>
                <div className="bubble">{msg.content}</div>
              </div>
            ))}
            {loading && <TypingIndicator />}
            <div ref={bottomRef} aria-hidden="true" />
          </div>

          {/* ── Input ── */}
          <form onSubmit={handleSubmit} aria-label="Chat input form">
            <div className="input-area">
              <input
                id="chat-input"
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="e.g. Hiring a mid-level Java developer who works with stakeholders…"
                disabled={loading}
                autoComplete="off"
                aria-label="Type your message"
              />
              <button
                type="submit"
                className="send-btn"
                disabled={!input.trim() || loading}
                aria-label="Send message"
              >
                <SendIcon />
              </button>
            </div>
          </form>

          {error && (
            <div className="error-banner" role="alert">
              ⚠️ {error}
            </div>
          )}
        </section>

        {/* ── Recommendations panel ── */}
        <aside className="card rec-card" aria-label="Recommendations panel">
          <div className="rec-card-header">
            <h2>Recommendations</h2>
            {recommendations.length > 0 && (
              <span className="rec-count-badge" aria-label={`${recommendations.length} recommendations`}>
                {recommendations.length} found
              </span>
            )}
          </div>

          {recommendations.length === 0 ? (
            <div className="rec-empty" aria-label="No recommendations yet">
              <div className="rec-empty-icon" aria-hidden="true">🎯</div>
              <p>
                No shortlist yet. The assistant may ask a clarification question
                to ensure the best match before recommending.
              </p>
            </div>
          ) : (
            <div className="rec-list" aria-label={`${recommendations.length} SHL assessment recommendations`}>
              {recommendations.map((rec, i) => (
                <RecCard key={rec.url || i} rec={rec} />
              ))}
            </div>
          )}

          <Legend />
        </aside>
      </main>

      {/* ── Footer ── */}
      <footer className="footer" aria-label="Footer">
        Data sourced from the SHL Individual Test Solutions catalog only. All URLs link directly to SHL.com.
      </footer>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
