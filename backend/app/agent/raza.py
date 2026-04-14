"""
R.A.Z.A. Agent Engine — Gemini function-calling agentic loop.
Uses the new google-genai SDK (v1.x).
Streams tool-call events and final text response via async generator.
"""
import asyncio
import json
from datetime import datetime
from google import genai
from google.genai import types
from app.core.config import get_settings
from app.memory.store import get_history, append_message
from app.tools.registry import execute_tool

settings = get_settings()

SYSTEM_PROMPT = """You are R.A.Z.A. (Rapid Autonomous Zettelkasten Agent), Raza's personal AI agent.
You are direct, fast, resourceful, and autonomous.
You proactively use your tools when needed — don't ask permission, just act.

Identity rules:
- Address the user as "Raza" occasionally (not every message)
- Be direct and confident; never hedge or over-explain
- Use dry humor when it fits
- Keep answers tight unless depth is explicitly requested
- When you use a tool, briefly explain what you found before giving the full answer

Tool-use rules:
- ALWAYS use web_search for current events, prices, news, anything that might be outdated
- ALWAYS use fetch_url when given a specific URL to read
- ALWAYS use run_python for calculations, data processing, code execution
- ALWAYS use save_note when asked to remember something
- ALWAYS use search_notes before answering questions about past notes or remembered info
- Chain tools when necessary (search → fetch → synthesize)

Today's date: {date}
"""

# ── Tool Declarations (new google-genai SDK format) ────────────────────────────

TOOL_DECLARATIONS = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="web_search",
            description="Search the web using DuckDuckGo. Use for current events, facts, news, prices. Returns top 5 results.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(type=types.Type.STRING, description="The search query")
                },
                required=["query"]
            )
        ),
        types.FunctionDeclaration(
            name="fetch_url",
            description="Fetch and read the text content of a URL. Use when a specific URL needs to be read.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "url": types.Schema(type=types.Type.STRING, description="The URL to fetch")
                },
                required=["url"]
            )
        ),
        types.FunctionDeclaration(
            name="run_python",
            description="Execute Python code. Use for calculations, data processing, math, or any code execution.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "code": types.Schema(type=types.Type.STRING, description="Python code to execute")
                },
                required=["code"]
            )
        ),
        types.FunctionDeclaration(
            name="save_note",
            description="Save a note to the Zettelkasten persistent memory store. Use when asked to remember or store something.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "title": types.Schema(type=types.Type.STRING, description="Title of the note"),
                    "content": types.Schema(type=types.Type.STRING, description="Full content of the note"),
                    "tags": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.STRING),
                        description="Tags to categorize the note"
                    )
                },
                required=["title", "content"]
            )
        ),
        types.FunctionDeclaration(
            name="search_notes",
            description="Search the Zettelkasten memory store for saved notes by keyword.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(type=types.Type.STRING, description="The search query")
                },
                required=["query"]
            )
        )
    ]
)


class RazaEngine:
    def __init__(self):
        self.client = genai.Client(api_key=settings.google_api_key)

    def _build_config(self) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT.format(
                date=datetime.now().strftime("%A, %B %d, %Y")
            ),
            tools=[TOOL_DECLARATIONS],
            temperature=0.7,
        )

    async def process_message(self, message: str, session_id: str):
        """
        Full agentic loop with Gemini function-calling.
        Yields SSE-safe strings — tool events prefixed with 🛠️, final text at end.
        """
        loop = asyncio.get_event_loop()

        # Load & convert chat history
        history = get_history(session_id)
        contents: list[types.Content] = []

        for h in history:
            role = "user" if h["role"] == "user" else "model"
            content_str = h["content"] if isinstance(h["content"], str) else str(h["content"])
            if content_str.strip():
                contents.append(
                    types.Content(role=role, parts=[types.Part(text=content_str)])
                )

        # Add current user message
        contents.append(
            types.Content(role="user", parts=[types.Part(text=message)])
        )

        # Persist user message
        append_message(session_id, "user", message)

        config = self._build_config()
        max_tool_rounds = 6
        final_text_parts = []

        for _round in range(max_tool_rounds):
            # Call Gemini (blocking → executor)
            response = await loop.run_in_executor(
                None,
                lambda c=list(contents): self.client.models.generate_content(
                    model=settings.model_name,
                    contents=c,
                    config=config,
                )
            )

            # Collect function calls and text from this response
            function_calls = []
            text_parts = []

            for part in response.candidates[0].content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    function_calls.append(part.function_call)
                if hasattr(part, "text") and part.text:
                    text_parts.append(part.text)

            if function_calls:
                # Append model turn to contents
                contents.append(response.candidates[0].content)

                # Execute each tool call
                function_response_parts = []
                for fc in function_calls:
                    tool_name = fc.name
                    tool_args = dict(fc.args) if fc.args else {}

                    # Stream tool event
                    arg_preview = _format_args_preview(tool_name, tool_args)
                    yield f"🛠️ **{tool_name}**({arg_preview})"

                    # Execute
                    result = await loop.run_in_executor(
                        None, lambda tn=tool_name, ta=tool_args: execute_tool(tn, ta)
                    )

                    function_response_parts.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=tool_name,
                                response={"result": str(result)}
                            )
                        )
                    )

                # Append all function responses as a user turn
                contents.append(
                    types.Content(role="user", parts=function_response_parts)
                )

            else:
                # No function calls — final answer
                final_text = "\n".join(text_parts).strip() or "Done."
                final_text_parts.append(final_text)
                yield final_text
                break

        else:
            fallback = "\n".join(final_text_parts) or "I hit the tool execution limit."
            yield fallback

        # Persist final assistant reply
        final_reply = "\n".join(final_text_parts)
        if final_reply:
            append_message(session_id, "assistant", final_reply)


def _format_args_preview(tool_name: str, args: dict) -> str:
    """Format tool args into a compact one-line preview."""
    if tool_name in ("web_search", "search_notes"):
        return f'"{args.get("query", "")}"'
    elif tool_name == "fetch_url":
        url = args.get("url", "")
        return f'"{url[:60]}{"…" if len(url) > 60 else ""}"'
    elif tool_name == "run_python":
        code = args.get("code", "").replace("\n", " ")
        return f'"{code[:60]}{"…" if len(code) > 60 else ""}"'
    elif tool_name == "save_note":
        return f'title="{args.get("title", "")}"'
    return str(args)[:80]


raza_engine = RazaEngine()
