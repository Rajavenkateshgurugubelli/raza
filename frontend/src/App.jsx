import { useState, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import './index.css';

const API_BASE = 'http://localhost:8000';
const DEFAULT_SESSION = 'default';

const SUGGESTIONS = [
  '🔍 Search the web for latest AI research',
  '📝 Save a note about quantum computing',
  '🐍 Run a Python calculation',
  '🧠 What do you remember about me?',
  '📡 Fetch and summarize a URL',
];

function formatTime(date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function isToolLine(text) {
  return text && text.includes('🛠️');
}

// Restore newlines encoded as ⏎ from SSE
function decodeSSE(raw) {
  return raw.replace(/⏎/g, '\n');
}

function TypingDots() {
  return (
    <div className="typing-dots">
      <span /><span /><span />
    </div>
  );
}

function Message({ msg }) {
  const isUser = msg.role === 'user';
  const isTool = isToolLine(msg.content);

  if (isTool) {
    return (
      <div className="message agent" style={{ maxWidth: 600 }}>
        <div className="msg-avatar agent-av">R</div>
        <div className="tool-msg">
          <div className="tool-dot" />
          {msg.content}
        </div>
      </div>
    );
  }

  return (
    <div className={`message ${msg.role}`}>
      {!isUser && <div className="msg-avatar agent-av">R</div>}
      {isUser && <div className="msg-avatar user-av">U</div>}
      <div className="msg-bubble">
        <div className="msg-content">
          {msg.streaming ? (
            msg.content ? <ReactMarkdown>{msg.content}</ReactMarkdown> : <TypingDots />
          ) : (
            <ReactMarkdown>{msg.content}</ReactMarkdown>
          )}
        </div>
        {msg.time && <div className="msg-time">{formatTime(msg.time)}</div>}
      </div>
    </div>
  );
}

function Sidebar({ visible, sessions, activeSession, onSelectSession, onNewSession, onDeleteSession, notesQuery, onNotesQuery, notesResults }) {
  return (
    <aside className={`sidebar ${visible ? '' : 'collapsed'}`}>
      <div className="sidebar-logo">
        <div className="sidebar-logo-avatar">R</div>
        <div>
          <div className="sidebar-logo-text">R.A.Z.A.</div>
          <div className="sidebar-logo-sub">Zettelkasten Agent</div>
        </div>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-section-label">Conversations</div>
        <button id="new-session-btn" className="sidebar-new-btn" onClick={onNewSession}>
          <span>＋</span> New Session
        </button>
      </div>

      <div className="sessions-list">
        {sessions.length === 0 && (
          <div style={{ fontSize: 11, color: 'var(--text-muted)', padding: '4px' }}>No sessions yet</div>
        )}
        {sessions.map(s => (
          <div
            key={s.session_id}
            id={`session-${s.session_id}`}
            className={`session-item ${s.session_id === activeSession ? 'active' : ''}`}
            onClick={() => onSelectSession(s.session_id)}
          >
            <span className="session-item-icon">💬</span>
            <span className="session-item-name">{s.session_id}</span>
            <span className="session-item-count">{s.count}</span>
            <button
              className="session-delete-btn"
              onClick={(e) => { e.stopPropagation(); onDeleteSession(s.session_id); }}
              title="Delete session"
            >✕</button>
          </div>
        ))}
      </div>

      <div className="sidebar-notes-search">
        <div className="sidebar-section-label" style={{ paddingBottom: 6 }}>Memory Search</div>
        <input
          id="notes-search"
          className="notes-search-input"
          placeholder="🔍 Search notes..."
          value={notesQuery}
          onChange={e => onNotesQuery(e.target.value)}
        />
      </div>
      {notesResults && (
        <div className="notes-results">
          <div className="note-result-item">{notesResults}</div>
        </div>
      )}
    </aside>
  );
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(DEFAULT_SESSION);
  const [notesQuery, setNotesQuery] = useState('');
  const [notesResults, setNotesResults] = useState('');
  const chatEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => { scrollToBottom(); }, [messages, scrollToBottom]);

  // Load sessions on mount
  useEffect(() => {
    fetchSessions();
  }, []);

  // Load history when session changes
  useEffect(() => {
    loadSessionHistory(activeSession);
  }, [activeSession]);

  // Notes search debounce
  useEffect(() => {
    if (!notesQuery.trim()) { setNotesResults(''); return; }
    const t = setTimeout(() => searchNotes(notesQuery), 400);
    return () => clearTimeout(t);
  }, [notesQuery]);

  async function fetchSessions() {
    try {
      const res = await fetch(`${API_BASE}/api/memory/sessions`);
      const data = await res.json();
      setSessions(data);
    } catch { /* backend not yet running */ }
  }

  async function loadSessionHistory(sessionId) {
    setMessages([]);
    try {
      const res = await fetch(`${API_BASE}/api/memory/sessions/${sessionId}`);
      const history = await res.json();
      if (Array.isArray(history) && history.length > 0) {
        const loaded = history
          .filter(m => typeof m.content === 'string')
          .map(m => ({
            role: m.role === 'assistant' ? 'agent' : m.role,
            content: m.content,
            time: new Date(),
          }));
        setMessages(loaded);
      } else {
        setMessages([{
          role: 'agent',
          content: `Online and ready, Raza. Session: **${sessionId}**`,
          time: new Date(),
        }]);
      }
    } catch {
      setMessages([{
        role: 'agent',
        content: `I am R.A.Z.A. Online and ready. What do you need, Raza?`,
        time: new Date(),
      }]);
    }
  }

  async function searchNotes(q) {
    try {
      const res = await fetch(`${API_BASE}/api/memory/notes/search?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      setNotesResults(data.results || 'No notes found.');
    } catch {
      setNotesResults('Could not reach backend.');
    }
  }

  function handleNewSession() {
    const newId = `session-${Date.now()}`;
    setActiveSession(newId);
    fetchSessions();
  }

  async function handleDeleteSession(sessionId) {
    try {
      await fetch(`${API_BASE}/api/memory/sessions/${sessionId}`, { method: 'DELETE' });
      fetchSessions();
      if (sessionId === activeSession) {
        setActiveSession(DEFAULT_SESSION);
      }
    } catch { /* ignore */ }
  }

  function handleSuggestion(text) {
    setInput(text.replace(/^[^\s]+\s/, '')); // strip emoji prefix
    textareaRef.current?.focus();
  }

  const handleSend = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: trimmed, time: new Date() }]);
    setLoading(true);

    // Placeholder agent message
    setMessages(prev => [...prev, { role: 'agent', content: '', streaming: true, time: new Date() }]);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, session_id: activeSession }),
      });

      if (!res.body) throw new Error('No readable stream');

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let done = false;
      let buffer = '';

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split('\n\n');
          buffer = parts.pop() ?? '';

          for (const part of parts) {
            if (!part.startsWith('data: ')) continue;
            const data = part.substring(6);
            if (data === '[DONE]') { done = true; break; }

            const decoded = decodeSSE(data);
            if (isToolLine(decoded)) {
              // Finalize current streaming bubble, add tool msg, open new bubble
              setMessages(prev => {
                const arr = [...prev];
                arr[arr.length - 1] = { ...arr[arr.length - 1], streaming: false };
                return [
                  ...arr,
                  { role: 'agent', content: decoded, time: new Date() },
                  { role: 'agent', content: '', streaming: true, time: new Date() },
                ];
              });
            } else {
              setMessages(prev => {
                const arr = [...prev];
                const last = arr[arr.length - 1];
                arr[arr.length - 1] = { ...last, content: last.content + decoded, streaming: true };
                return arr;
              });
            }
          }
        }
      }
    } catch (err) {
      setMessages(prev => {
        const arr = [...prev];
        arr[arr.length - 1] = { role: 'agent', content: `❌ Error: ${err.message}`, streaming: false, time: new Date() };
        return arr;
      });
    } finally {
      setLoading(false);
      setMessages(prev => {
        const arr = [...prev];
        if (arr.length > 0) arr[arr.length - 1] = { ...arr[arr.length - 1], streaming: false };
        return arr;
      });
      fetchSessions();
    }
  }, [input, loading, activeSession]);

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  // Auto-resize textarea
  function handleInputChange(e) {
    setInput(e.target.value);
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = 'auto';
      ta.style.height = `${Math.min(ta.scrollHeight, 140)}px`;
    }
  }

  const showEmpty = messages.length === 0;

  return (
    <div className="app-shell">
      <Sidebar
        visible={sidebarOpen}
        sessions={sessions}
        activeSession={activeSession}
        onSelectSession={setActiveSession}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        notesQuery={notesQuery}
        onNotesQuery={setNotesQuery}
        notesResults={notesResults}
      />

      <div className="main-area">
        <header className="header">
          <button
            id="sidebar-toggle"
            className="header-toggle-btn"
            onClick={() => setSidebarOpen(v => !v)}
            title="Toggle sidebar"
          >☰</button>
          <div className="header-title">
            <h1>R.A.Z.A.</h1>
            <p>Rapid Autonomous Zettelkasten Agent</p>
          </div>
          <select
            id="session-selector"
            className="header-session-select"
            value={activeSession}
            onChange={e => setActiveSession(e.target.value)}
          >
            <option value="default">default</option>
            {sessions.filter(s => s.session_id !== 'default').map(s => (
              <option key={s.session_id} value={s.session_id}>{s.session_id}</option>
            ))}
            {!sessions.find(s => s.session_id === activeSession) && activeSession !== 'default' && (
              <option value={activeSession}>{activeSession}</option>
            )}
          </select>
          <div className={`status-dot ${loading ? 'thinking' : ''}`} title={loading ? 'Thinking...' : 'Online'} />
        </header>

        <main className="chat-box" id="chat-box">
          {showEmpty ? (
            <div className="empty-state">
              <div className="empty-state-avatar">R</div>
              <h2>R.A.Z.A. is online.</h2>
              <p>Your personal AI agent with persistent memory, web search, and a Python REPL. Command it directly.</p>
              <div className="empty-suggestions">
                {SUGGESTIONS.map((s, i) => (
                  <button key={i} className="suggestion-chip" onClick={() => handleSuggestion(s)}>{s}</button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, i) => <Message key={i} msg={msg} />)
          )}
          <div ref={chatEndRef} />
        </main>

        <div className="input-area">
          <div className="input-wrapper">
            <textarea
              id="chat-input"
              ref={textareaRef}
              className="input-textarea"
              rows={1}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Command R.A.Z.A.… (Shift+Enter for newline)"
              disabled={loading}
            />
            <button
              id="send-btn"
              className="send-btn"
              onClick={handleSend}
              disabled={loading || !input.trim()}
              title="Send (Enter)"
            >
              ↗
            </button>
          </div>
          <div className="input-hint">Enter to send · Shift+Enter for new line · R.A.Z.A. remembers across sessions</div>
        </div>
      </div>
    </div>
  );
}
