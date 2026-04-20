"""
ChromaDB vector store for semantic note retrieval.
Uses sentence-transformers (all-MiniLM-L6-v2) for local embeddings — no API key required.
Persists the index to disk alongside the SQLite DB.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Lazy imports so the backend starts even if chromadb has issues
_chroma_client = None
_collection = None
_embed_fn = None


def _get_embed_fn():
    global _embed_fn
    if _embed_fn is None:
        try:
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
            _embed_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        except Exception as e:
            logger.warning(f"[VectorStore] Could not load embedding function: {e}")
            _embed_fn = None
    return _embed_fn


def _get_collection(db_path: str = "chroma_db"):
    global _chroma_client, _collection
    if _collection is not None:
        return _collection
    try:
        import chromadb
        Path(db_path).mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=db_path)
        embed_fn = _get_embed_fn()
        _collection = _chroma_client.get_or_create_collection(
            name="raza_notes",
            embedding_function=embed_fn,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"[VectorStore] Collection ready — {_collection.count()} notes indexed.")
        return _collection
    except Exception as e:
        logger.warning(f"[VectorStore] ChromaDB unavailable: {e}")
        return None


def upsert_note(note_id: int, title: str, content: str, tags: list[str] | None = None, db_path: str = "chroma_db"):
    """Embed and upsert a note into the vector index."""
    col = _get_collection(db_path)
    if col is None:
        return
    try:
        tag_str = " ".join(tags or [])
        document = f"{title}\n{tag_str}\n{content}".strip()
        col.upsert(
            ids=[str(note_id)],
            documents=[document],
            metadatas=[{"note_id": note_id, "title": title}],
        )
    except Exception as e:
        logger.warning(f"[VectorStore] upsert_note({note_id}) failed: {e}")


def delete_note(note_id: int, db_path: str = "chroma_db"):
    """Remove a note from the vector index."""
    col = _get_collection(db_path)
    if col is None:
        return
    try:
        col.delete(ids=[str(note_id)])
    except Exception as e:
        logger.warning(f"[VectorStore] delete_note({note_id}) failed: {e}")


def search(query: str, n_results: int = 8, db_path: str = "chroma_db") -> list[dict]:
    """
    Semantic similarity search. Returns list of dicts:
      { 'note_id': int, 'title': str, 'distance': float }
    Distance is cosine distance (lower = more similar).
    Returns [] if vector store unavailable or empty.
    """
    col = _get_collection(db_path)
    if col is None or col.count() == 0:
        return []
    try:
        results = col.query(
            query_texts=[query],
            n_results=min(n_results, col.count()),
            include=["metadatas", "distances"],
        )
        hits = []
        for meta, dist in zip(results["metadatas"][0], results["distances"][0]):
            hits.append({
                "note_id": meta["note_id"],
                "title": meta.get("title", ""),
                "distance": dist,
            })
        return hits
    except Exception as e:
        logger.warning(f"[VectorStore] search failed: {e}")
        return []


def sync_all(notes: list[dict], db_path: str = "chroma_db"):
    """
    Rebuild the vector index from a list of note dicts (from SQLite).
    Each note dict must have: id, title, content, tags (list[str]).
    Idempotent — safe to call on every startup.
    """
    if not notes:
        return
    col = _get_collection(db_path)
    if col is None:
        return
    try:
        ids, docs, metas = [], [], []
        for note in notes:
            tag_str = " ".join(note.get("tags") or [])
            document = f"{note['title']}\n{tag_str}\n{note['content']}".strip()
            ids.append(str(note["id"]))
            docs.append(document)
            metas.append({"note_id": note["id"], "title": note["title"]})
        col.upsert(ids=ids, documents=docs, metadatas=metas)
        logger.info(f"[VectorStore] Synced {len(notes)} notes into Chroma.")
    except Exception as e:
        logger.warning(f"[VectorStore] sync_all failed: {e}")
