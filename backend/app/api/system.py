from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ..core.config import get_settings
from ..memory.store import get_memory_stats
from ..tools.registry import tools_list
from ..agent.raza import current_provider_snapshot, generate_brief

router = APIRouter()


@router.get("/providers")
def get_provider_status():
    settings = get_settings()
    available = []
    if settings.google_api_key:
        available.append("gemini")
    if settings.anthropic_api_key:
        available.append("anthropic")

    order = [p.strip().lower() for p in settings.provider_order.split(",") if p.strip()]
    resolved_order = [p for p in order if p in available]
    for provider in available:
        if provider not in resolved_order:
            resolved_order.append(provider)

    return {
        "available": available,
        "provider_order": resolved_order,
        "default_provider": resolved_order[0] if resolved_order else None,
        "model_name": settings.model_name,
    }


@router.get("/status")
def get_full_status():
    """Return a comprehensive system status snapshot for the dashboard."""
    settings = get_settings()
    snapshot = current_provider_snapshot()
    stats = get_memory_stats()
    tool_names = [t["name"] for t in tools_list]

    return {
        "agent": settings.app_name,
        "version": "2.1.0",
        "provider": snapshot,
        "memory": stats,
        "tools": tool_names,
        "config": {
            "model_name": settings.model_name,
            "max_memory_messages": settings.max_memory_messages,
            "recent_context_messages": settings.recent_context_messages,
            "google_workspace": bool(settings.google_oauth_access_token),
            "vector_memory": True,
        },
    }


@router.get("/tools")
def list_tools():
    """Return the list of available tools with schemas."""
    return tools_list


@router.get("/brief")
async def daily_brief(session_id: str = "default"):
    """
    Stream an AI-generated daily briefing (notes summary + date context).
    Response is SSE — same format as /api/chat.
    """
    async def event_stream():
        try:
            async for chunk in generate_brief(session_id):
                safe_chunk = chunk.replace("\n", "⏎")
                yield f"data: {safe_chunk}\n\n"
        except Exception as e:
            yield f"data: ❌ Brief failed: {str(e)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
