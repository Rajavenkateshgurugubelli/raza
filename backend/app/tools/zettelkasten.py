import os
import json
from datetime import datetime

MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "memory")

def ensure_memory_dir():
    if not os.path.exists(MEMORY_DIR):
        os.makedirs(MEMORY_DIR)

def save_note(title: str, content: str, tags: list[str] = None) -> str:
    """Saves a note to the Zettelkasten memory store."""
    ensure_memory_dir()
    
    # Create a safe filename
    filename = "".join(c for c in title if c.isalnum() or c in " -_").strip().replace(" ", "_").lower()
    if not filename:
        filename = "note_" + datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{filename}.json"
    
    filepath = os.path.join(MEMORY_DIR, filename)
    
    note_data = {
        "title": title,
        "content": content,
        "tags": tags or [],
        "created_at": datetime.now().isoformat()
    }
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(note_data, f, indent=4)
        return f"Successfully saved note '{title}' to memory."
    except Exception as e:
        return f"Failed to save note: {e}"

def search_notes(query: str) -> str:
    """Searches through notes in the Zettelkasten by matching title, content, or tags."""
    ensure_memory_dir()
    
    results = []
    query_lower = query.lower()
    
    for filename in os.listdir(MEMORY_DIR):
        if not filename.endswith(".json"):
            continue
            
        filepath = os.path.join(MEMORY_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                note = json.load(f)
                
            title = note.get("title", "")
            content = note.get("content", "")
            tags = note.get("tags", [])
            
            # Simple keyword search
            if (query_lower in title.lower() or 
                query_lower in content.lower() or 
                any(query_lower in str(tag).lower() for tag in tags)):
                
                results.append(f"Title: {title}\nTags: {', '.join(tags)}\nContent Snippet: {content[:100]}...\n")
                
        except Exception:
            continue
            
    if not results:
        return f"No notes found matching '{query}'."
        
    return "Found Notes:\n\n" + "\n".join(results)
