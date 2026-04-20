from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..memory.store import (
    list_sessions,
    get_history,
    clear_session,
    get_session_summary,
    upsert_session_summary,
    rename_session,
)
from ..tools.zettelkasten import search_notes

router = APIRouter()


class SessionSummaryUpdate(BaseModel):
    summary: str


class SessionRename(BaseModel):
    new_id: str


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


@router.put("/sessions/{session_id}/rename")
def rename_session_endpoint(session_id: str, body: SessionRename):
    """Rename a session (moves all messages to new session_id)."""
    if not body.new_id or body.new_id == session_id:
        raise HTTPException(status_code=400, detail="new_id must be different and non-empty")
    result = rename_session(session_id, body.new_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "renamed", "old_id": session_id, "new_id": body.new_id}


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
