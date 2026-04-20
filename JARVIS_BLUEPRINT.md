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
- [ ] Voice I/O pipeline (Whisper + Silero VAD + TTS).
- [ ] Proactive jobs (morning brief automation, alerts, reports).
- [ ] Desktop wrapper (Electron/Tauri).
- [ ] Docker and cloud deployment workflow.

## Immediate Next Build Targets

### Phase E (next)
- Add voice pipeline: Whisper STT (local via `faster-whisper`) + TTS (via `edge-tts`).
- Add proactive scheduler: auto-run daily brief at startup if configured time passes.
- Add tool result caching: avoid re-fetching same URLs in same session.

### Phase F
- Docker containerization with auto-restart and volume mounts.
- Cloud deployment option (Railway, Fly.io, etc.).
