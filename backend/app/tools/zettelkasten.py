"""
Zettelkasten tool — SQLite-backed with hybrid semantic + keyword search.
Semantic results (ChromaDB) are ranked first; keyword hits fill gaps.
"""
from app.memory.store import save_note_to_db, search_notes_in_db, list_notes, get_note_by_id
from app.memory import vector_store as vs
from app.core.config import get_settings


def save_note(title: str, content: str, tags: list[str] = None) -> str:
    """Saves a note to the Zettelkasten (SQLite + vector index)."""
    try:
        note = save_note_to_db(title, content, tags)
        tag_str = ", ".join(note["tags"]) if note["tags"] else "none"
        return f"✅ Note saved: **{title}** (id={note['id']}, tags: {tag_str})"
    except Exception as e:
        return f"❌ Failed to save note: {e}"


def search_notes(query: str) -> str:
    """
    Hybrid search: semantic similarity (ChromaDB) + keyword fallback (SQLite).
    Returns top results merged and deduplicated.
    """
    try:
        settings = get_settings()
        seen_ids: set[int] = set()
        result_notes: list[dict] = []

        # 1. Semantic search via ChromaDB
        semantic_hits = vs.search(query, n_results=6, db_path=settings.chroma_db_path)
        if semantic_hits:
            for hit in semantic_hits:
                note = get_note_by_id(hit["note_id"])
                if note and note["id"] not in seen_ids:
                    note["_score"] = 1.0 - hit["distance"]  # convert distance → similarity
                    note["_source"] = "semantic"
                    result_notes.append(note)
                    seen_ids.add(note["id"])

        # 2. Keyword fallback — fill up to 8 total results
        if len(result_notes) < 8:
            keyword_hits = search_notes_in_db(query)
            for note in keyword_hits:
                if note["id"] not in seen_ids:
                    note["_score"] = None
                    note["_source"] = "keyword"
                    result_notes.append(note)
                    seen_ids.add(note["id"])
                    if len(result_notes) >= 8:
                        break

        if not result_notes:
            return f"No notes found matching '{query}'."

        out = f"Found {len(result_notes)} note(s):\n\n"
        for note in result_notes:
            tags = ", ".join(note["tags"]) if note["tags"] else "none"
            snippet = note["content"][:150].replace("\n", " ")
            src = "🔮" if note.get("_source") == "semantic" else "🔑"
            score_txt = f" · {note['_score']:.0%} match" if note.get("_score") is not None else ""
            out += f"{src} **{note['title']}** (id={note['id']}, tags: {tags}){score_txt}\n{snippet}…\n\n"

        return out.strip()

    except Exception as e:
        return f"❌ Error searching notes: {e}"
