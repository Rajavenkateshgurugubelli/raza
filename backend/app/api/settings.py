"""
Settings API — read and update non-sensitive backend configuration.
Reads/writes backend/.env in place so changes survive server restarts.

Sensitive keys (API keys, OAuth tokens) are READ-ONLY via this API — 
they must be set directly in the .env file for security.

PATCH /api/settings           — update one or more config fields
GET  /api/settings            — return current public config
"""
import re
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Body
from ..core.config import get_settings

router = APIRouter()

# Fields that are safe to expose and edit via the UI
EDITABLE_FIELDS = {
    "model_name":               "Model name (e.g. gemini-2.0-flash, claude-sonnet-4-…)",
    "provider_order":           "Comma-separated provider priority (gemini,anthropic)",
    "app_name":                 "Display name of the agent",
    "max_memory_messages":      "Max messages before compression (integer)",
    "recent_context_messages":  "Recent messages kept in context window (integer)",
    "brief_time":               "Daily brief time as HH:MM (blank = disabled)",
    "brief_session":            "Session to save auto-brief into",
    "tts_voice":                "edge-tts neural voice name",
}

# Always redacted in responses
SENSITIVE_KEYS = {"google_api_key", "anthropic_api_key", "google_oauth_access_token"}


def _find_env_file() -> Path:
    """Locate the backend .env file regardless of CWD."""
    candidates = [
        Path(".env"),
        Path(__file__).parents[3] / ".env",  # backend/.env when run from backend/
    ]
    for p in candidates:
        if p.exists():
            return p
    # If none found, create one next to this config file's grandparent
    default = Path(__file__).parents[3] / ".env"
    default.touch()
    return default


def _read_env_file(path: Path) -> dict[str, str]:
    """Parse a .env file into a dict (skips comments and blank lines)."""
    env = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            # Strip surrounding quotes
            val = val.strip().strip('"').strip("'")
            env[key.strip()] = val
    return env


def _write_env_file(path: Path, env: dict[str, str]) -> None:
    """Write env dict back to file preserving comments."""
    existing_lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    already_written: set[str] = set()
    new_lines = []

    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue
        if "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in env:
                new_lines.append(f'{key}="{env[key]}"')
                already_written.add(key)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # Append any new keys not already in the file
    for key, val in env.items():
        if key not in already_written:
            new_lines.append(f'{key}="{val}"')

    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


@router.get("")
def get_config():
    """Return current config values (sensitive keys redacted)."""
    settings = get_settings()
    data = settings.model_dump()
    return {
        k: ("***" if k in SENSITIVE_KEYS else v)
        for k, v in data.items()
    }


@router.get("/fields")
def get_editable_fields():
    """Return metadata about which fields can be edited via UI."""
    return EDITABLE_FIELDS


@router.patch("")
def update_config(updates: dict = Body(...)):
    """
    Update one or more editable config fields.
    Changes are written to backend/.env and take effect on next server restart
    (or immediately for fields read dynamically).
    Sensitive keys (API keys) cannot be changed via this endpoint.
    """
    if not updates:
        raise HTTPException(400, "No fields provided.")

    # Reject sensitive keys
    sensitive_attempted = [k for k in updates if k in SENSITIVE_KEYS]
    if sensitive_attempted:
        raise HTTPException(
            403,
            f"Security: {sensitive_attempted} must be set directly in backend/.env, not via the API."
        )

    # Reject unknown keys
    unknown = [k for k in updates if k not in EDITABLE_FIELDS]
    if unknown:
        raise HTTPException(400, f"Unknown or non-editable fields: {unknown}. Allowed: {list(EDITABLE_FIELDS)}")

    env_path = _find_env_file()
    env = _read_env_file(env_path)

    # Apply updates
    for key, val in updates.items():
        env[key] = str(val)

    _write_env_file(env_path, env)

    # Bust the lru_cache so next call reads fresh values
    get_settings.cache_clear()

    return {"updated": list(updates.keys()), "env_file": str(env_path)}
