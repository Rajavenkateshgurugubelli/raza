"""
Persistent memory store using SQLite via SQLAlchemy.
Replaces the in-memory dict for chat history - survives server restarts.
"""
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import get_settings

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
    content = Column(Text, nullable=False)  # JSON-encoded for complex content
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


# ── CRUD helpers ──────────────────────────────────────────────────────────────

def get_history(session_id: str) -> list[dict]:
    """Return all messages for session as Anthropic-compatible dicts."""
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
        # Keep only the last N messages to avoid hitting context limits
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
