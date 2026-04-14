import { useState, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import PropTypes from 'prop-types';
import './index.css';

const API_BASE = 'http://127.0.0.1:8000';
const DEFAULT_SESSION = 'default';

const SUGGESTIONS = [
  { icon: '🔍', text: 'Search the web for latest AI news' },
  { icon: '📝', text: 'Save a note about quantum computing basics' },
  { icon: '🐍', text: 'Run Python: print fibonacci sequence to 20' },
  { icon: '🧠', text: 'What notes do you have saved?' },
  { icon: '📡', text: 'Fetch and summarize https://news.ycombinator.com' },
  { icon: '💡', text: 'What can you do?' },
];

function formatTime(date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function isToolEvent(text) {
  return text && text.startsWith('🛠️');
}

function decodeSSE(raw) {
  return raw.replace(/⏎/g, '\n');
}

// ── Typing Indicator ──────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div className="typing-dots">
      <span /><span /><span />
    </div>
  );
}

// ── Tool Event Card ───────────────────────────────────────────────────────────
function ToolCard({ content }) {
  // Extract tool name and args from "🛠️ **tool_name**(args)"
  const match = content.match(/🛠️\s+\*\*(.+?)\*\*\((.*)?\)$/s);
  const toolName = match?.[1] || 'tool';
  const args = match?.[2] || '';

  const toolIcons = {
    web_search: '🌐',
    fetch_url: '📡',
    run_python: '🐍',
    save_note: '📝',
    search_notes: '🔍',
  };
  const icon = toolIcons[toolName] || '⚙️';

  return (
    <div className="tool-card">
      <div className="tool-card-header">
        <span className="tool-card-icon">{icon}</span>
        <span className="tool-card-name">{toolName}</span>
        <span className="tool-card-badge">EXECUTING</span>
      </div>
      {args && <div className="tool-card-args">{args}</div>}
    </div>
  );
}
ToolCard.propTypes = {
  content: PropTypes.string.isRequired,
};

// ── Copy Button ───────────────────────────────────────────────────────────────
function CopyBtn({ text }) {
  const [copied, setCopied] = useState(false);
  function handleCopy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    });
  }
  return (
    <button className={`copy-btn ${copied ? 'copied' : ''}`} onClick={handleCopy} title="Copy">
      {copied ? '✓' : '⎘'}
    </button>
  );
}
CopyBtn.propTypes = {
  text: PropTypes.string.isRequired,
};

// ── Message Component ─────────────────────────────────────────────────────────
function Message({ msg }) {
  const isUser = msg.role === 'user';
  const isTool = isToolEvent(msg.content);

  if (isTool) return <ToolCard content={msg.content} />;

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
        <div className="msg-meta">
          {msg.time && <span className="msg-time">{formatTime(msg.time)}</span>}
          {!isUser && !msg.streaming && msg.content && <CopyBtn text={msg.content} />}
        </div>
      </div>
    </div>
  );
}
Message.propTypes = {
  msg: PropTypes.shape({
    role: PropTypes.string.isRequired,
    content: PropTypes.string.isRequired,
    streaming: PropTypes.bool,
    time: PropTypes.instanceOf(Date),
  }).isRequired,
};

// ── Note Item ─────────────────────────────────────────────────────────────────
function NoteItem({ note, onDelete }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="note-item">
      <div className="note-item-header" onClick={() => setExpanded(v => !v)}>
        <span className="note-item-title">{note.title}</span>
        <div className="note-item-actions">
          <button
            className="note-delete-btn"
            onClick={(e) => { e.stopPropagation(); onDelete(note.id); }}
            title="Delete note"
          >✕</button>
          <span className="note-item-chevron">{expanded ? '▲' : '▼'}</span>
        </div>
      </div>
      {note.tags?.length > 0 && (
        <div className="note-tags">
          {note.tags.map((t, i) => <span key={i} className="note-tag">#{t}</span>)}
        </div>
      )}
      {expanded && (
        <div className="note-item-content">{note.content}</div>
      )}
    </div>
  );
}
NoteItem.propTypes = {
  note: PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    content: PropTypes.string.isRequired,
    tags: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
  onDelete: PropTypes.func.isRequired,
};

// ── Notes Panel ───────────────────────────────────────────────────────────────
function NotesPanel({ visible, onClose }) {
  const [notes, setNotes] = useState([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchNotes = useCallback(async (q = '') => {
    setLoading(true);
    try {
      const url = q.trim()
        ? `${API_BASE}/api/notes?q=${encodeURIComponent(q)}`
        : `${API_BASE}/api/notes`;
      const res = await fetch(url);
      const data = await res.json();
      setNotes(Array.isArray(data) ? data : []);
    } catch { setNotes([]); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    if (visible) fetchNotes();
  }, [visible, fetchNotes]);

  useEffect(() => {
    if (!visible) return;
    const t = setTimeout(() => fetchNotes(query), 350);
    return () => clearTimeout(t);
  }, [query, visible, fetchNotes]);

  async function handleDelete(id) {
    try {
      await fetch(`${API_BASE}/api/notes/${id}`, { method: 'DELETE' });
      fetchNotes(query);
    } catch { /* ignore */ }
  }

  return (
    <div className={`notes-panel ${visible ? 'open' : ''}`}>
      <div className="notes-panel-header">
        <span>📒 Zettelkasten</span>
        <button className="notes-panel-close" onClick={onClose}>✕</button>
      </div>
      <div className="notes-panel-search">
        <input
          placeholder="🔍 Search notes…"
          value={query}
          onChange={e => setQuery(e.target.value)}
          className="notes-panel-input"
        />
      </div>
      <div className="notes-panel-body">
        {loading && <div className="notes-loading">Searching…</div>}
        {!loading && notes.length === 0 && (
          <div className="notes-empty">No notes yet. Ask R.A.Z.A. to save something.</div>
        )}
        {!loading && notes.map(n => (
          <NoteItem key={n.id} note={n} onDelete={handleDelete} />
        ))}
      </div>
    </div>
  );
}
NotesPanel.propTypes = {
  visible: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
};

// ── Sidebar ───────────────────────────────────────────────────────────────────
function Sidebar({ visible, sessions, activeSession, onSelectSession, onNewSession, onDeleteSession }) {
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
    </aside>
  );
}
Sidebar.propTypes = {
  visible: PropTypes.bool.isRequired,
  sessions: PropTypes.arrayOf(
    PropTypes.shape({
      session_id: PropTypes.string.isRequired,
      count: PropTypes.number.isRequired,
    }),
  ).isRequired,
  activeSession: PropTypes.string.isRequired,
  onSelectSession: PropTypes.func.isRequired,
  onNewSession: PropTypes.func.isRequired,
  onDeleteSession: PropTypes.func.isRequired,
};

// ── Offline Banner ────────────────────────────────────────────────────────────
function OfflineBanner() {
  return (
    <div className="offline-banner">
      ⚠️ Backend offline — start the server at <code>localhost:8000</code>
    </div>
  );
}

// ── Shortcuts Modal ───────────────────────────────────────────────────────────
function ShortcutsModal({ onClose }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <span>⌨️ Keyboard Shortcuts</span>
          <button onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <div className="shortcut-row"><kbd>Enter</kbd><span>Send message</span></div>
          <div className="shortcut-row"><kbd>Shift+Enter</kbd><span>New line</span></div>
          <div className="shortcut-row"><kbd>Ctrl+K</kbd><span>Clear chat</span></div>
          <div className="shortcut-row"><kbd>Ctrl+/</kbd><span>Toggle sidebar</span></div>
          <div className="shortcut-row"><kbd>Ctrl+N</kbd><span>New session</span></div>
          <div className="shortcut-row"><kbd>Ctrl+E</kbd><span>Export chat</span></div>
          <div className="shortcut-row"><kbd>Ctrl+Shift+N</kbd><span>Open notes</span></div>
          <div className="shortcut-row"><kbd>?</kbd><span>This panel</span></div>
        </div>
      </div>
    </div>
  );
}
ShortcutsModal.propTypes = {
  onClose: PropTypes.func.isRequired,
};

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(DEFAULT_SESSION);
  const [backendOnline, setBackendOnline] = useState(true);
  const [notesOpen, setNotesOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const [providerInfo, setProviderInfo] = useState(null);
  const chatEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => { scrollToBottom(); }, [messages, scrollToBottom]);
  useEffect(() => { checkHealth(); fetchSessions(); fetchProviders(); }, []);
  useEffect(() => { loadSessionHistory(activeSession); }, [activeSession]);

  // Global keyboard shortcuts
  useEffect(() => {
    function onKey(e) {
      if (e.key === '?' && !e.ctrlKey && !e.metaKey && document.activeElement.tagName !== 'TEXTAREA') {
        setShortcutsOpen(v => !v);
      }
      if ((e.ctrlKey || e.metaKey)) {
        if (e.key === '/') { e.preventDefault(); setSidebarOpen(v => !v); }
        if (e.key === 'k') { e.preventDefault(); setMessages([]); }
        if (e.key === 'n') { e.preventDefault(); handleNewSession(); }
        if (e.key === 'e') { e.preventDefault(); exportChat(); }
        if (e.key === 'N') { e.preventDefault(); setNotesOpen(v => !v); }
      }
      if (e.key === 'Escape') { setShortcutsOpen(false); setNotesOpen(false); }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages, activeSession]);

  async function checkHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) });
      setBackendOnline(res.ok);
    } catch {
      setBackendOnline(false);
    }
  }

  async function fetchProviders() {
    try {
      const res = await fetch(`${API_BASE}/api/system/providers`);
      const data = await res.json();
      setProviderInfo(data);
    } catch {
      setProviderInfo(null);
    }
  }

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
          content: `Online, Raza. Session: **${sessionId}**. What do you need?`,
          time: new Date(),
        }]);
      }
    } catch {
      setMessages([{
        role: 'agent',
        content: `I'm R.A.Z.A. Online and standing by. What do you need?`,
        time: new Date(),
      }]);
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
      if (sessionId === activeSession) setActiveSession(DEFAULT_SESSION);
    } catch { /* ignore */ }
  }

  function handleSuggestion(text) {
    setInput(text);
    textareaRef.current?.focus();
  }

  function exportChat() {
    if (messages.length === 0) return;
    const md = messages
      .filter(m => !isToolEvent(m.content))
      .map(m => `**${m.role === 'user' ? 'You' : 'R.A.Z.A.'}**\n${m.content}`)
      .join('\n\n---\n\n');
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `raza-chat-${activeSession}-${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const handleSend = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: trimmed, time: new Date() }]);
    setLoading(true);

    // Placeholder streaming agent bubble
    setMessages(prev => [...prev, { role: 'agent', content: '', streaming: true, time: new Date() }]);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, session_id: activeSession }),
      });

      setBackendOnline(true);

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

            if (isToolEvent(decoded)) {
              // Finalize current streaming bubble, insert tool card, open new bubble
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
      setBackendOnline(false);
      setMessages(prev => {
        const arr = [...prev];
        arr[arr.length - 1] = {
          role: 'agent',
          content: `❌ ${err.message}. Is the backend running?`,
          streaming: false,
          time: new Date(),
        };
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
      fetchProviders();
    }
  }, [input, loading, activeSession]);

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleInputChange(e) {
    setInput(e.target.value);
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = 'auto';
      ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
    }
  }

  const showEmpty = messages.length === 0;

  return (
    <div className="app-shell">
      {!backendOnline && <OfflineBanner />}
      {shortcutsOpen && <ShortcutsModal onClose={() => setShortcutsOpen(false)} />}
      <NotesPanel visible={notesOpen} onClose={() => setNotesOpen(false)} />

      <Sidebar
        visible={sidebarOpen}
        sessions={sessions}
        activeSession={activeSession}
        onSelectSession={setActiveSession}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
      />

      <div className="main-area">
        <header className="header">
          <button
            id="sidebar-toggle"
            className="header-icon-btn"
            onClick={() => setSidebarOpen(v => !v)}
            title="Toggle sidebar (Ctrl+/)"
          >☰</button>

          <div className="header-title">
            <h1>R.A.Z.A.</h1>
            <p>Rapid Autonomous Zettelkasten Agent</p>
            {providerInfo?.default_provider && (
              <div className="provider-chip">
                AI: {providerInfo.default_provider} · model: {providerInfo.model_name}
              </div>
            )}
          </div>

          <div className="header-actions">
            <button
              id="notes-toggle-btn"
              className="header-icon-btn"
              onClick={() => setNotesOpen(v => !v)}
              title="Notes (Ctrl+Shift+N)"
            >📒</button>
            <button
              id="export-btn"
              className="header-icon-btn"
              onClick={exportChat}
              title="Export chat (Ctrl+E)"
              disabled={messages.length === 0}
            >↓</button>
            <button
              id="shortcuts-btn"
              className="header-icon-btn"
              onClick={() => setShortcutsOpen(true)}
              title="Keyboard shortcuts (?)"
            >?</button>
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
            <div className={`status-dot ${loading ? 'thinking' : ''}`} title={loading ? 'Thinking…' : 'Online'} />
          </div>
        </header>

        <main className="chat-box" id="chat-box">
          {showEmpty ? (
            <div className="empty-state">
              <div className="empty-state-avatar">R</div>
              <h2>R.A.Z.A. is online.</h2>
              <p>Your autonomous AI agent with web search, Python REPL, and persistent Zettelkasten memory.</p>
              <div className="empty-suggestions">
                {SUGGESTIONS.map((s, i) => (
                  <button key={i} className="suggestion-chip" onClick={() => handleSuggestion(s.text)}>
                    <span>{s.icon}</span> {s.text}
                  </button>
                ))}
              </div>
              <div className="empty-shortcut-hint">Press <kbd>?</kbd> for keyboard shortcuts</div>
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
              {loading ? <span className="send-spinner" /> : '↗'}
            </button>
          </div>
          <div className="input-hint">
            Enter · send &nbsp;·&nbsp; Shift+Enter · newline &nbsp;·&nbsp; Ctrl+K · clear &nbsp;·&nbsp; ? · shortcuts
          </div>
        </div>
      </div>
    </div>
  );
}
