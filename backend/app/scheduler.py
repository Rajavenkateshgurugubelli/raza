"""
Proactive scheduler for R.A.Z.A.
Uses APScheduler (already installed) to run background jobs.

Configured via environment variables:
  BRIEF_TIME=08:00   — HH:MM to auto-fire the daily brief (leave blank to disable)
  BRIEF_SESSION=default — session_id to store the auto-brief in
"""
import asyncio
import logging
from datetime import datetime, date as date_type

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.config import get_settings

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None
_last_brief_date: date_type | None = None   # prevent double-firing on same day


async def _fire_brief():
    """Run the daily brief and save it as a note."""
    global _last_brief_date
    today = datetime.now().date()
    if _last_brief_date == today:
        logger.info("[Scheduler] Brief already fired today — skipping.")
        return

    logger.info("[Scheduler] Firing proactive morning brief…")
    _last_brief_date = today

    try:
        from app.agent.raza import generate_brief
        from app.memory.store import save_note_to_db

        settings = get_settings()
        session_id = getattr(settings, "brief_session", "default")

        chunks = []
        async for chunk in generate_brief(session_id):
            chunks.append(chunk)

        brief_text = "".join(chunks).strip()
        if brief_text:
            title = f"Daily Brief — {today.strftime('%A, %B %d %Y')}"
            save_note_to_db(title, brief_text, tags=["brief", "auto", today.strftime("%Y-%m")])
            logger.info(f"[Scheduler] Brief saved as note: '{title}'")
    except Exception as e:
        logger.error(f"[Scheduler] Brief job failed: {e}")


def start_scheduler() -> AsyncIOScheduler | None:
    """
    Start the APScheduler if BRIEF_TIME is configured.
    Returns the scheduler or None if disabled.
    """
    global _scheduler
    settings = get_settings()
    brief_time = getattr(settings, "brief_time", "") or ""

    if not brief_time.strip():
        logger.info("[Scheduler] BRIEF_TIME not set — proactive brief disabled.")
        return None

    try:
        hour_str, minute_str = brief_time.strip().split(":")
        hour, minute = int(hour_str), int(minute_str)
    except ValueError:
        logger.warning(f"[Scheduler] Invalid BRIEF_TIME '{brief_time}' — must be HH:MM. Scheduler disabled.")
        return None

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _fire_brief,
        trigger="cron",
        hour=hour,
        minute=minute,
        id="daily_brief",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(f"[Scheduler] Daily brief scheduled at {hour:02d}:{minute:02d} every day.")
    return _scheduler


def stop_scheduler():
    """Stop the scheduler gracefully."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("[Scheduler] Stopped.")


def get_scheduler_info() -> dict:
    """Return scheduler status for the system status dashboard."""
    settings = get_settings()
    brief_time = getattr(settings, "brief_time", "") or ""
    return {
        "enabled": bool(_scheduler and _scheduler.running),
        "brief_time": brief_time or None,
        "last_brief_date": str(_last_brief_date) if _last_brief_date else None,
        "jobs": [j.id for j in (_scheduler.get_jobs() if _scheduler else [])],
    }
