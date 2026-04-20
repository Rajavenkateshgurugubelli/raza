"""
Persistent memory store using SQLite via SQLAlchemy.
Handles both chat history (ChatMessage) and Zettelkasten notes (Note).
"""
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import get_settings
from app.memory import vector_store as vs

settings = get_settings()
DATABASE_URL = f"sqlite:///{settings.memory_db_path}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True, nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(Text, default="[]")  # JSON-encoded list
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SessionSummary(Base):
    __tablename__ = "session_summaries"
    session_id = Column(String(100), primary_key=True, index=True)
    summary = Column(Text, nullable=False, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


# ── CHAT HISTORY CRUD ─────────────────────────────────────────────────────────

def get_history(session_id: str) -> list[dict]:
    """Return all messages for session as Gemini-compatible dicts."""
    db = SessionLocal()
    try:
        rows = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id)
            .all()
        )
        messages = []
        for row in rows:
            try:
                content = json.loads(row.content)
            except Exception:
                content = row.content
            messages.append({"role": row.role, "content": content})
        max_msgs = get_settings().max_memory_messages
        return messages[-max_msgs:] if len(messages) > max_msgs else messages
    finally:
        db.close()


def append_message(session_id: str, role: str, content):
    """Persist a single message."""
    db = SessionLocal()
    try:
        msg = ChatMessage(
            session_id=session_id,
            role=role,
            content=json.dumps(content) if not isinstance(content, str) else content,
        )
        db.add(msg)
        db.commit()
    finally:
        db.close()


def clear_session(session_id: str):
    """Wipe all messages for a session."""
    db = SessionLocal()
    try:
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        db.commit()
    finally:
        db.close()


def list_sessions() -> list[dict]:
    """List unique sessions with message count."""
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                "SELECT session_id, COUNT(*) as count, MAX(created_at) as last_active "
                "FROM chat_messages GROUP BY session_id ORDER BY last_active DESC"
            )
        ).fetchall()
        return [{"session_id": r[0], "count": r[1], "last_active": r[2]} for r in rows]
    finally:
        db.close()


def rename_session(old_id: str, new_id: str) -> bool:
    """Rename a session by updating session_id on all messages and summary."""
    db = SessionLocal()
    try:
        updated = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == old_id)
            .update({"session_id": new_id})
        )
        if updated == 0:
            return False
        # Also rename summary if exists
        summary_row = db.query(SessionSummary).filter(SessionSummary.session_id == old_id).first()
        if summary_row:
            summary_row.session_id = new_id
        db.commit()
        return True
    finally:
        db.close()


# ── NOTES CRUD ────────────────────────────────────────────────────────────────

def save_note_to_db(title: str, content: str, tags: list[str] = None) -> dict:
    """Save a new note, returns the created note dict."""
    db = SessionLocal()
    try:
        note = Note(
            title=title,
            content=content,
            tags=json.dumps(tags or []),
        )
        db.add(note)
        db.commit()
        db.refresh(note)
        result = _note_to_dict(note)
        # Sync to vector index (fire-and-forget)
        vs.upsert_note(result["id"], title, content, tags or [], settings.chroma_db_path)
        return result
    finally:
        db.close()


def search_notes_in_db(query: str) -> list[dict]:
    """Full text search across title, content, and tags."""
    db = SessionLocal()
    try:
        q = f"%{query.lower()}%"
        rows = (
            db.query(Note)
            .filter(
                (Note.title.ilike(q)) |
                (Note.content.ilike(q)) |
                (Note.tags.ilike(q))
            )
            .order_by(Note.created_at.desc())
            .all()
        )
        return [_note_to_dict(r) for r in rows]
    finally:
        db.close()


def list_notes() -> list[dict]:
    """List all notes, newest first."""
    db = SessionLocal()
    try:
        rows = db.query(Note).order_by(Note.created_at.desc()).all()
        return [_note_to_dict(r) for r in rows]
    finally:
        db.close()


def delete_note(note_id: int) -> bool:
    """Delete a note by id. Returns True if deleted."""
    db = SessionLocal()
    try:
        row = db.query(Note).filter(Note.id == note_id).first()
        if not row:
            return False
        db.delete(row)
        db.commit()
        # Remove from vector index
        vs.delete_note(note_id, settings.chroma_db_path)
        return True
    finally:
        db.close()


def get_note_by_id(note_id: int) -> dict | None:
    db = SessionLocal()
    try:
        row = db.query(Note).filter(Note.id == note_id).first()
        return _note_to_dict(row) if row else None
    finally:
        db.close()


def update_note_in_db(note_id: int, title: str = None, content: str = None, tags: list[str] = None) -> dict | None:
    """Partially update a note's fields. Returns updated note dict or None."""
    db = SessionLocal()
    try:
        row = db.query(Note).filter(Note.id == note_id).first()
        if not row:
            return None
        if title is not None:
            row.title = title
        if content is not None:
            row.content = content
        if tags is not None:
            row.tags = json.dumps(tags)
        row.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(row)
        result = _note_to_dict(row)
        # Re-sync updated note in vector index
        vs.upsert_note(
            result["id"], result["title"], result["content"],
            result["tags"], settings.chroma_db_path
        )
        return result
    finally:
        db.close()


def get_memory_stats() -> dict:
    """Return aggregate statistics about stored data."""
    db = SessionLocal()
    try:
        note_count = db.query(Note).count()
        session_count = db.execute(text("SELECT COUNT(DISTINCT session_id) FROM chat_messages")).scalar() or 0
        message_count = db.query(ChatMessage).count()
        return {
            "notes": note_count,
            "sessions": session_count,
            "messages": message_count,
        }
    finally:
        db.close()


def _note_to_dict(note: Note) -> dict:
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "tags": json.loads(note.tags) if note.tags else [],
        "created_at": note.created_at.isoformat() if note.created_at else None,
        "updated_at": note.updated_at.isoformat() if note.updated_at else None,
    }


def get_session_summary(session_id: str) -> str:
    db = SessionLocal()
    try:
        row = db.query(SessionSummary).filter(SessionSummary.session_id == session_id).first()
        return row.summary if row else ""
    finally:
        db.close()


def upsert_session_summary(session_id: str, summary: str):
    db = SessionLocal()
    try:
        row = db.query(SessionSummary).filter(SessionSummary.session_id == session_id).first()
        if row:
            row.summary = summary
        else:
            row = SessionSummary(session_id=session_id, summary=summary)
            db.add(row)
        db.commit()
    finally:
        db.close()


def rollup_session_memory(session_id: str, keep_last: int = 20, max_chars: int = 4000):
    """
    Build/update a compact session summary from older messages.
    Keeps recent turns in raw form and summarizes older content.
    """
    db = SessionLocal()
    try:
        rows = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id)
            .all()
        )
        if len(rows) <= keep_last:
            return

        older = rows[:-keep_last]
        snippets = []
        for row in older[-30:]:
            text_value = row.content
            if len(text_value) > 240:
                text_value = f"{text_value[:240]}..."
            snippets.append(f"{row.role}: {text_value}")

        current = get_session_summary(session_id)
        merged = "\n".join([current, *snippets]).strip()
        if len(merged) > max_chars:
            merged = merged[-max_chars:]

        upsert_session_summary(session_id, merged)
    finally:
        db.close()
