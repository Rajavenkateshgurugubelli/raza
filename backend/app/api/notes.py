from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..memory.store import save_note_to_db, search_notes_in_db, list_notes, delete_note, get_note_by_id

router = APIRouter()


class NoteCreate(BaseModel):
    title: str
    content: str
    tags: Optional[list[str]] = []


@router.get("")
def get_notes(q: Optional[str] = None):
    """List all notes, or search if q is provided."""
    if q:
        return search_notes_in_db(q)
    return list_notes()


@router.post("", status_code=201)
def create_note(body: NoteCreate):
    """Create a new note."""
    return save_note_to_db(body.title, body.content, body.tags)


@router.get("/{note_id}")
def get_note(note_id: int):
    note = get_note_by_id(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.delete("/{note_id}")
def remove_note(note_id: int):
    """Delete a note by ID."""
    success = delete_note(note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"status": "deleted", "id": note_id}
