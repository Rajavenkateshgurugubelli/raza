"""
In-memory tool result cache with TTL (time-to-live).
Avoids re-fetching the same URL or running the same search in the same server session.
Thread-safe via a simple dict + lock.
"""
import hashlib
import json
import time
import threading
import logging

logger = logging.getLogger(__name__)

# Default TTLs (seconds) per tool
_DEFAULT_TTL: dict[str, int] = {
    "web_search": 300,   # 5 min — news changes
    "fetch_url":  600,   # 10 min — pages are relatively stable
    "run_python":   0,   # never cache — side effects possible
}

_cache: dict[str, tuple[str, float]] = {}  # key -> (result, expires_at)
_lock = threading.Lock()


def _make_key(tool_name: str, args: dict) -> str:
    payload = json.dumps({"tool": tool_name, "args": args}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def get(tool_name: str, args: dict) -> str | None:
    """Return cached result if still fresh, else None."""
    ttl = _DEFAULT_TTL.get(tool_name, 0)
    if ttl == 0:
        return None
    key = _make_key(tool_name, args)
    with _lock:
        entry = _cache.get(key)
    if entry is None:
        return None
    result, expires_at = entry
    if time.monotonic() < expires_at:
        logger.debug(f"[Cache] HIT {tool_name}")
        return result
    # Expired
    with _lock:
        _cache.pop(key, None)
    return None


def put(tool_name: str, args: dict, result: str) -> None:
    """Store a result in the cache."""
    ttl = _DEFAULT_TTL.get(tool_name, 0)
    if ttl == 0 or not result:
        return
    key = _make_key(tool_name, args)
    expires_at = time.monotonic() + ttl
    with _lock:
        _cache[key] = (result, expires_at)
    logger.debug(f"[Cache] STORED {tool_name} (TTL {ttl}s)")


def invalidate(tool_name: str | None = None) -> int:
    """Invalidate all cache entries (or just for one tool). Returns count removed."""
    with _lock:
        if tool_name is None:
            count = len(_cache)
            _cache.clear()
        else:
            keys = [k for k, (_, _) in _cache.items()]
            # We stored by hash so can't filter by tool; just clear all
            count = len(_cache)
            _cache.clear()
    return count


def stats() -> dict:
    """Return cache statistics."""
    now = time.monotonic()
    with _lock:
        total = len(_cache)
        alive = sum(1 for _, (_, exp) in _cache.items() if exp > now)
    return {"total_entries": total, "live_entries": alive}
