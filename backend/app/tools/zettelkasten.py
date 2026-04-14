"""
Zettelkasten tool — now backed by SQLite via the shared memory store.
"""
from app.memory.store import save_note_to_db, search_notes_in_db


def save_note(title: str, content: str, tags: list[str] = None) -> str:
    """Saves a note to the Zettelkasten (SQLite) memory store."""
    try:
        note = save_note_to_db(title, content, tags)
        tag_str = ", ".join(note["tags"]) if note["tags"] else "none"
        return f"✅ Note saved: **{title}** (id={note['id']}, tags: {tag_str})"
    except Exception as e:
        return f"❌ Failed to save note: {e}"


def search_notes(query: str) -> str:
    """Searches Zettelkasten notes by title, content, or tags."""
    try:
        results = search_notes_in_db(query)
        if not results:
            return f"No notes found matching '{query}'."
        out = f"Found {len(results)} note(s):\n\n"
        for note in results:
            tags = ", ".join(note["tags"]) if note["tags"] else "none"
            snippet = note["content"][:120].replace("\n", " ")
            out += f"📝 **{note['title']}** (id={note['id']}, tags: {tags})\n{snippet}...\n\n"
        return out.strip()
    except Exception as e:
        return f"❌ Error searching notes: {e}"
