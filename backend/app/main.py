from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import chat, memory, notes, system
from .memory.store import init_db, list_notes
from .memory import vector_store as vs
from .core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="R.A.Z.A. — Rapid Autonomous Zettelkasten Agent API",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    # Init relational DB
    init_db()
    # Rebuild vector index from all existing notes (idempotent)
    all_notes = list_notes()
    if all_notes:
        vs.sync_all(all_notes, db_path=settings.chroma_db_path)


app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(notes.router, prefix="/api/notes", tags=["notes"])
app.include_router(system.router, prefix="/api/system", tags=["system"])


@app.get("/health")
def health():
    return {"status": "online", "agent": settings.app_name, "version": "2.1.0"}
