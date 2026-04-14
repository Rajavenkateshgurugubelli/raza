import json
from datetime import datetime, timezone
import requests
from app.core.config import get_settings


def _auth_headers() -> dict | None:
    settings = get_settings()
    token = getattr(settings, "google_oauth_access_token", "") or ""
    if not token:
        return None
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def gmail_list_recent(limit: int = 5, query: str = "") -> str:
    headers = _auth_headers()
    if not headers:
        return "Gmail unavailable: set GOOGLE_OAUTH_ACCESS_TOKEN in backend/.env."
    try:
        params = {"maxResults": max(1, min(limit, 20))}
        if query:
            params["q"] = query
        resp = requests.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            headers=headers,
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        messages = data.get("messages", [])
        if not messages:
            return "No Gmail messages found."

        lines = []
        for idx, item in enumerate(messages[:limit], start=1):
            msg_id = item.get("id", "")
            detail = requests.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
                headers=headers,
                params={"format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]},
                timeout=15,
            )
            detail.raise_for_status()
            payload = detail.json().get("payload", {})
            headers_arr = payload.get("headers", [])
            lookup = {h.get("name"): h.get("value") for h in headers_arr}
            lines.append(
                f"[{idx}] From: {lookup.get('From', 'Unknown')} | "
                f"Subject: {lookup.get('Subject', '(no subject)')} | "
                f"Date: {lookup.get('Date', 'Unknown')}"
            )
        return "\n".join(lines)
    except Exception as exc:
        return f"Gmail list failed: {exc}"


def gmail_create_draft(to: str, subject: str, body: str) -> str:
    headers = _auth_headers()
    if not headers:
        return "Gmail unavailable: set GOOGLE_OAUTH_ACCESS_TOKEN in backend/.env."
    try:
        import base64

        raw = (
            f"To: {to}\r\n"
            f"Subject: {subject}\r\n"
            "Content-Type: text/plain; charset=utf-8\r\n\r\n"
            f"{body}"
        )
        encoded = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")
        resp = requests.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/drafts",
            headers=headers,
            data=json.dumps({"message": {"raw": encoded}}),
            timeout=15,
        )
        resp.raise_for_status()
        draft = resp.json()
        draft_id = draft.get("id", "unknown")
        return f"Draft created successfully (id={draft_id})."
    except Exception as exc:
        return f"Gmail draft failed: {exc}"


def calendar_upcoming(limit: int = 5, calendar_id: str = "primary") -> str:
    headers = _auth_headers()
    if not headers:
        return "Calendar unavailable: set GOOGLE_OAUTH_ACCESS_TOKEN in backend/.env."
    try:
        now = datetime.now(timezone.utc).isoformat()
        resp = requests.get(
            f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
            headers=headers,
            params={
                "singleEvents": "true",
                "orderBy": "startTime",
                "timeMin": now,
                "maxResults": max(1, min(limit, 20)),
            },
            timeout=15,
        )
        resp.raise_for_status()
        events = resp.json().get("items", [])
        if not events:
            return "No upcoming calendar events."
        lines = []
        for idx, event in enumerate(events, start=1):
            start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
            lines.append(f"[{idx}] {event.get('summary', '(no title)')} @ {start}")
        return "\n".join(lines)
    except Exception as exc:
        return f"Calendar lookup failed: {exc}"


def calendar_create_event(
    summary: str,
    start_iso: str,
    end_iso: str,
    timezone_name: str = "UTC",
    description: str = "",
    calendar_id: str = "primary",
) -> str:
    headers = _auth_headers()
    if not headers:
        return "Calendar unavailable: set GOOGLE_OAUTH_ACCESS_TOKEN in backend/.env."
    try:
        payload = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_iso, "timeZone": timezone_name},
            "end": {"dateTime": end_iso, "timeZone": timezone_name},
        }
        resp = requests.post(
            f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
            headers=headers,
            data=json.dumps(payload),
            timeout=15,
        )
        resp.raise_for_status()
        event = resp.json()
        return f"Calendar event created: {event.get('htmlLink', '(no link)')}"
    except Exception as exc:
        return f"Calendar create failed: {exc}"
