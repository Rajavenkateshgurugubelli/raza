from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from ..agent.raza import raza_engine

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


@router.post("")
async def chat_endpoint(req: ChatRequest):
    async def event_stream():
        try:
            async for chunk in raza_engine.process_message(req.message, req.session_id):
                # Escape the chunk for SSE — newlines must be preserved within a data field
                safe_chunk = chunk.replace("\n", "⏎")
                yield f"data: {safe_chunk}\n\n"
        except Exception as e:
            yield f"data: ❌ Error: {str(e)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
