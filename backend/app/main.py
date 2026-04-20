from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import chat, memory, notes, system, voice, settings
from .memory.store import init_db, list_notes
from .memory import vector_store as vs
from .scheduler import start_scheduler, stop_scheduler
from .core.config import get_settings

settings_obj = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    init_db()
    all_notes = list_notes()
    if all_notes:
        vs.sync_all(all_notes, db_path=settings_obj.chroma_db_path)
    start_scheduler()

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────────
    stop_scheduler()


app = FastAPI(
    title=settings_obj.app_name,
    description="R.A.Z.A. — Rapid Autonomous Zettelkasten Agent API",
    version="2.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(notes.router, prefix="/api/notes", tags=["notes"])
app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(voice.router, prefix="/api/voice", tags=["voice"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])


@app.get("/health")
def health():
    from .scheduler import get_scheduler_info
    from .tools.cache import stats as cache_stats
    return {
        "status": "online",
        "agent": settings_obj.app_name,
        "version": "2.3.0",
        "scheduler": get_scheduler_info(),
        "cache": cache_stats(),
    }

