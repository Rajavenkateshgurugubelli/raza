# R.A.Z.A. — Rapid Autonomous Zettelkasten Agent

A Jarvis-style personal AI assistant with full tool-calling, persistent Zettelkasten memory, and a polished React UI.

## Quick Start

```powershell
# From the raza/ directory:
.\start.ps1
```

Or manually:

```powershell
# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

Then open **http://localhost:5173**

## Configuration

Copy `.env.example` to `backend/.env` and fill in your keys:

```env
# Required (pick at least one)
GOOGLE_API_KEY=your-gemini-api-key

# Optional
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_OAUTH_ACCESS_TOKEN=your-oauth-token   # for Gmail & Calendar
MODEL_NAME=gemini-2.0-flash
PROVIDER_ORDER=gemini,anthropic              # fallback order
MEMORY_DB_PATH=raza_memory.db
MAX_MEMORY_MESSAGES=50
RECENT_CONTEXT_MESSAGES=20
```

## Features

### 🧠 Agent Loop
- Multi-provider: Gemini 2.0 Flash (primary) + Claude Sonnet (fallback)
- Automatic provider failover on quota/auth errors
- Up to 6 tool-call rounds per response
- Rolling session memory with compression

### 🛠️ Tools (9 total)
| Tool | Description |
|------|-------------|
| `web_search` | DuckDuckGo search, top 5 results |
| `fetch_url` | Fetch and extract text from any URL |
| `run_python` | Execute Python code with stdout capture |
| `save_note` | Save to Zettelkasten (SQLite) |
| `search_notes` | Full-text search across all notes |
| `gmail_list_recent` | List recent Gmail messages |
| `gmail_create_draft` | Create Gmail drafts |
| `calendar_upcoming` | List upcoming Google Calendar events |
| `calendar_create_event` | Create calendar events |

### 📒 Zettelkasten (Notes)
- Persistent SQLite storage
- Create, view, edit, delete notes from the sidebar panel
- Search by title, content, or tags
- CRUD API at `/api/notes`

### 💬 Chat UI
- Real-time SSE streaming with token-by-token display
- Tool-call visualization cards with animated EXECUTING badge
- Multiple named sessions with persistent history
- Double-click session name to rename
- Export chat as Markdown (Ctrl+E)
- ReactMarkdown with full code block rendering

### ⚡ System Status Panel
- Live provider/model info
- Memory statistics (notes, sessions, messages)
- Full tool list
- Configuration snapshot

## Keyboard Shortcuts

| Shortcut | Action |
|---------|--------|
| `Enter` | Send message |
| `Shift+Enter` | New line |
| `Ctrl+K` | Clear chat |
| `Ctrl+/` | Toggle sidebar |
| `Ctrl+N` | New session |
| `Ctrl+E` | Export chat |
| `Ctrl+Shift+N` | Open notes |
| `Ctrl+Shift+S` | System status |
| `?` | Keyboard shortcuts |
| `Esc` | Close panels |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat` | Stream chat response (SSE) |
| GET | `/api/notes` | List / search notes |
| POST | `/api/notes` | Create note |
| GET | `/api/notes/{id}` | Get note by ID |
| PATCH | `/api/notes/{id}` | Edit note |
| DELETE | `/api/notes/{id}` | Delete note |
| GET | `/api/memory/sessions` | List sessions |
| GET | `/api/memory/sessions/{id}` | Session history |
| DELETE | `/api/memory/sessions/{id}` | Clear session |
| PUT | `/api/memory/sessions/{id}/rename` | Rename session |
| GET | `/api/system/status` | Full system status |
| GET | `/api/system/providers` | Provider info |
| GET | `/api/system/tools` | Tool schemas |
| GET | `/health` | Health check |

## Architecture

```
raza/
├── backend/
│   └── app/
│       ├── agent/raza.py        # Core agentic loop (Gemini + Claude)
│       ├── api/                 # FastAPI routers
│       ├── memory/store.py      # SQLite ORM (chat + notes + summaries)
│       ├── tools/               # Tool implementations
│       └── core/config.py       # Pydantic settings
└── frontend/
    └── src/
        ├── App.jsx              # Main React app
        └── index.css            # Design system + all styles
```

## Roadmap

- [ ] Vector memory (Chroma/Qdrant semantic retrieval)  
- [ ] Voice I/O (Whisper STT + TTS output)  
- [ ] Proactive mode (daily briefings, scheduled tasks)  
- [ ] Electron or Tauri desktop wrapper  
- [ ] Docker deployment with auto-restart  
