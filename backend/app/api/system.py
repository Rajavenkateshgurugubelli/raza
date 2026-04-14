from fastapi import APIRouter
from ..core.config import get_settings

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

