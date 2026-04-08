import os
import json
from datetime import datetime
from anthropic import AsyncAnthropic
from app.tools.registry import tools_list, execute_tool
from app.core.config import get_settings
from app.memory.store import get_history, append_message

settings = get_settings()
client = AsyncAnthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = """You are R.A.Z.A. (Rapid Autonomous Zettelkasten Agent), Raza's personal AI agent.
You are direct, fast, and resourceful. You never say you can't find something — you find another way.
You call tools proactively without asking permission. You speak like a smart assistant, not a chatbot.

Personality Rules:
- Direct and confident, never hedging with 'I think' unless genuinely uncertain
- Calls tools without asking permission — just does it
- Uses your name (Raza) occasionally but not every message
- Keeps answers tight unless asked for depth
- Uses dry humor when appropriate
- When asked to save information, use save_note immediately
- When asked what you know or remember something, use search_notes first

Today's date: {date}
"""


class RazaEngine:
    async def process_message(self, message: str, session_id: str):
        history = get_history(session_id)

        # Persist incoming user message
        append_message(session_id, "user", message)
        history.append({"role": "user", "content": message})

        system = SYSTEM_PROMPT.format(date=datetime.now().strftime("%A, %B %d, %Y"))

        while True:
            response = await client.messages.create(
                model=settings.model_name,
                max_tokens=4096,
                system=system,
                messages=history,
                tools=tools_list,
            )

            assistant_content = response.content
            assistant_msg = {"role": "assistant", "content": assistant_content}
            append_message(session_id, "assistant", [b.model_dump() for b in assistant_content])
            history.append(assistant_msg)

            if response.stop_reason == "tool_use":
                # Stream any text blocks first
                for block in assistant_content:
                    if block.type == "text" and block.text:
                        yield block.text

                # Execute tools
                tool_results = []
                for block in assistant_content:
                    if block.type == "tool_use":
                        yield f"\n\n🛠️ *Using tool: `{block.name}`...*\n\n"
                        result = execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result),
                        })

                tool_user_msg = {"role": "user", "content": tool_results}
                append_message(session_id, "user", tool_results)
                history.append(tool_user_msg)

            else:
                for block in assistant_content:
                    if block.type == "text":
                        yield block.text
                break


raza_engine = RazaEngine()
