from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
from ..agent.raza import raza_engine

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

@router.post("")
async def chat_endpoint(req: ChatRequest):
    async def event_stream():
        async for chunk in raza_engine.process_message(req.message, req.session_id):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    try:
        return StreamingResponse(event_stream(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
