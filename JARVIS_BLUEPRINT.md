# JARVIS-Style Assistant Blueprint

## Build Phases

1. Core brain: Claude model, persona prompt, context-window controls.
2. Memory: short-term window + long-term memory indexing and retrieval.
3. Tools/integrations: Gmail, Calendar, web, filesystem, code exec, browser automation.
4. Voice: wake word, STT, VAD, TTS, push-to-talk and always-on modes.
5. Proactive mode: daily briefings, alerts, schedules, job watcher.
6. UI/HUD: dashboard, live tool feed, memory viewer, mobile support.
7. Deployment: local-first, containerization, cloud option, secrets/logging/restart.

## Current Implementation Status

- [x] Core backend and frontend app are running.
- [x] Tool-calling loop with web/file/code/memory tools.
- [x] Persistent notes and chat history in SQLite.
- [x] Session memory compression (rolling summary + recent turns).
- [x] Provider abstraction (Gemini primary + Claude fallback).
- [x] Gmail and Calendar tool integrations (OAuth token-based).
- [x] Full Notes CRUD API with PATCH editing.
- [x] Session rename API and UI (double-click in sidebar).
- [x] System status panel (/api/system/status).
- [x] Note create/edit directly from Notes panel UI.
- [x] 9-tool registry: web_search, fetch_url, run_python, save_note, search_notes, gmail_list_recent, gmail_create_draft, calendar_upcoming, calendar_create_event.
- [x] Vector memory store (ChromaDB + all-MiniLM-L6-v2, hybrid semantic+keyword search).
- [x] Daily brief endpoint (GET /api/system/brief, SSE streaming).
- [x] File attachment upload in chat UI (📎 button, 50KB limit, 10+ file types).
- [x] Clean error messages for quota/auth/timeout failures.
- [x] Voice I/O pipeline: GET /api/voice/speak (edge-tts neural TTS), POST /api/voice/transcribe (faster-whisper STT), 🎤 mic button with pulsing recording UI, 🗣️ speak button on every agent message.
- [x] Proactive scheduler: APScheduler cron job, BRIEF_TIME env var, auto-saves brief as a note.
- [x] Tool result caching: TTL cache for web_search (5 min) and fetch_url (10 min).
- [x] Docker containerization: backend + frontend Dockerfiles, docker-compose with named volumes, healthcheck gating.
- [x] Settings UI panel (⚙️ Ctrl+,): edit model, memory, brief time, TTS voice in-browser; writes to backend/.env safely.
- [x] PWA support: Web App Manifest, Service Worker, installable on mobile, offline shell cache.
- [x] Cloud deployment configs: railway.toml (Railway) and fly.toml (Fly.io).
- [x] Nginx reverse proxy config for containerized production deployment.
- [ ] Wake word / always-on voice activation.
- [ ] Proactive push notifications (system tray alerts).

## API Surface (v2.3.0)

| Method | Path | Purpose |
|--------|------|---------|
| POST | /api/chat | SSE chat stream |
| GET | /api/memory/sessions | List sessions |
| GET/DELETE | /api/memory/sessions/{id} | Session ops |
| PUT | /api/memory/sessions/{id}/rename | Rename session |
| GET | /api/memory/notes/search | Search notes |
| GET/POST | /api/notes | List / create notes |
| GET/PATCH/DELETE | /api/notes/{id} | Note CRUD |
| GET | /api/system/status | Full system status |
| GET | /api/system/brief | Daily brief (SSE) |
| DELETE | /api/system/cache | Flush tool cache |
| POST | /api/voice/transcribe | Whisper STT |
| GET | /api/voice/speak | edge-tts TTS |
| GET | /api/voice/voices | List TTS voices |
| GET/PATCH | /api/settings | Read/write config |
| GET | /api/settings/fields | Editable field list |
| GET | /health | Health + cache + scheduler |

## Deployment Options

### Local (dev)
```
cd backend && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

### Docker (production)
```
docker-compose up --build -d
```

### Railway
```
railway up
```

### Fly.io
```
fly deploy
```

## Environment Variables (backend/.env)

| Variable | Default | Description |
|----------|---------|-------------|
| GOOGLE_API_KEY | (required) | Gemini API key |
| ANTHROPIC_API_KEY | (optional) | Claude fallback |
| MODEL_NAME | gemini-2.0-flash | Active model |
| PROVIDER_ORDER | gemini,anthropic | Failover order |
| BRIEF_TIME | (blank) | HH:MM for auto-brief |
| TTS_VOICE | en-US-GuyNeural | edge-tts voice |

## Next (Phase G — optional enhancements)
- Wake word detection (Porcupine or silero-VAD always-on mic).
- System tray integration via Tauri for native desktop experience.
- Multi-user support with session isolation.
- Plugin marketplace for custom tools.
