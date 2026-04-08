from fastapi import APIRouter
from ..memory.store import list_sessions, get_history, clear_session
from ..tools.zettelkasten import search_notes

router = APIRouter()


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


@router.get("/notes/search")
def search_memory_notes(q: str):
    return {"results": search_notes(q)}
