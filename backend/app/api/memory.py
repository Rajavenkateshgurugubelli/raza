from fastapi import APIRouter
from pydantic import BaseModel
from ..memory.store import (
    list_sessions,
    get_history,
    clear_session,
    get_session_summary,
    upsert_session_summary,
)
from ..tools.zettelkasten import search_notes

router = APIRouter()


class SessionSummaryUpdate(BaseModel):
    summary: str


@router.get("/sessions")
def get_sessions():
    return list_sessions()


@router.get("/sessions/{session_id}")
def get_session_history(session_id: str):
    return get_history(session_id)


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    clear_session(session_id)
    return {"status": "cleared", "session_id": session_id}


@router.get("/sessions/{session_id}/summary")
def read_session_summary(session_id: str):
    return {"session_id": session_id, "summary": get_session_summary(session_id)}


@router.put("/sessions/{session_id}/summary")
def update_session_summary(session_id: str, body: SessionSummaryUpdate):
    upsert_session_summary(session_id, body.summary)
    return {"status": "updated", "session_id": session_id}


@router.get("/notes/search")
def search_memory_notes(q: str):
    return {"results": search_notes(q)}
