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
- [ ] Provider abstraction (Claude + fallback providers).
- [ ] Vector memory store (Chroma/Qdrant semantic retrieval).
- [ ] MCP connectors (Gmail, Calendar, Notion/Obsidian).
- [ ] Voice I/O pipeline.
- [ ] Proactive jobs (morning brief, alerts, reports).
- [ ] Dashboard/HUD polish and mobile packaging.
- [ ] Docker and cloud deployment workflow.

## Immediate Next Build Targets

### Phase A (now)
- Stabilize Claude runtime path and env validation.
- Add memory APIs for summary inspect/edit.
- Add tool-call retry/fallback chain.

### Phase B
- Add vector memory backend (Chroma first).
- Add Gmail and Google Calendar integration layer.
- Add daily brief scheduled job.

### Phase C
- Add voice pipeline with Whisper + Silero VAD + TTS.
- Add proactive notifications and system tray flow.
