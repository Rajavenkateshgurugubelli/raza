from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import chat, memory, notes
from .memory.store import init_db
from .core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="R.A.Z.A. — Rapid Autonomous Zettelkasten Agent API",
    version="2.0.0",
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
    init_db()


app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(notes.router, prefix="/api/notes", tags=["notes"])


@app.get("/health")
def health():
    return {"status": "online", "agent": settings.app_name, "version": "2.0.0"}
