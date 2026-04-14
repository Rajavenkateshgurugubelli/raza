"""
R.A.Z.A. Agent Engine — Google-first tool-calling loop with memory compression.
Streams tool-call events and final text response via async generator.
"""
import asyncio
from datetime import datetime
from anthropic import Anthropic
from google import genai
from google.genai import types
from app.core.config import get_settings
from app.memory.store import (
    get_history,
    append_message,
    get_session_summary,
    rollup_session_memory,
)
from app.tools.registry import execute_tool, get_tool_schemas

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

class RazaEngine:
    def __init__(self):
        self.clients = {}
        if settings.google_api_key:
            self.clients["gemini"] = genai.Client(api_key=settings.google_api_key)
        if settings.anthropic_api_key:
            self.clients["anthropic"] = Anthropic(api_key=settings.anthropic_api_key)

    async def process_message(self, message: str, session_id: str):
        """
        Full agentic loop with multi-provider tool-calling.
        Yields SSE-safe strings — tool events prefixed with 🛠️, final text at end.
        """
        loop = asyncio.get_event_loop()
        system_text = SYSTEM_PROMPT.format(date=datetime.now().strftime("%A, %B %d, %Y"))

        # Load compressed context summary + recent messages only
        rollup_session_memory(session_id, keep_last=settings.recent_context_messages)
        memory_summary = get_session_summary(session_id)
        history = get_history(session_id)
        recent = history[-settings.recent_context_messages :]
        messages = []

        if memory_summary:
            system_text = (
                f"{system_text}\n\nConversation memory summary:\n{memory_summary}\n"
                "Treat this as historical context; prioritize recent turns when conflicting."
            )

        for h in recent:
            role = "assistant" if h["role"] == "assistant" else "user"
            content_str = h["content"] if isinstance(h["content"], str) else str(h["content"])
            if content_str.strip():
                messages.append({"role": role, "content": content_str})

        # Add current user message
        messages.append({"role": "user", "content": message})

        # Persist user message
        append_message(session_id, "user", message)

        max_tool_rounds = 6
        final_reply = ""

        provider_order = _provider_order()
        if not provider_order:
            final_reply = "No AI provider key configured. Set GOOGLE_API_KEY in backend/.env."
            yield final_reply
            append_message(session_id, "assistant", final_reply)
            return

        last_error = ""
        for provider in provider_order:
            try:
                if provider == "gemini":
                    async for chunk in self._process_with_gemini(
                        loop=loop,
                        message=message,
                        messages=messages,
                        system_text=system_text,
                        max_tool_rounds=max_tool_rounds,
                    ):
                        final_reply = chunk
                        yield chunk
                else:
                    async for chunk in self._process_with_anthropic(
                        loop=loop,
                        messages=messages,
                        system_text=system_text,
                        max_tool_rounds=max_tool_rounds,
                    ):
                        final_reply = chunk
                        yield chunk
                break
            except Exception as exc:
                last_error = str(exc)
                if not _should_try_next_provider(last_error):
                    raise
                continue
        else:
            final_reply = f"All providers unavailable. Last error: {last_error}"
            yield final_reply

        # Persist final assistant reply
        if final_reply:
            append_message(session_id, "assistant", final_reply)
            rollup_session_memory(session_id, keep_last=settings.recent_context_messages)

    async def _process_with_anthropic(
        self,
        loop,
        messages: list[dict],
        system_text: str,
        max_tool_rounds: int,
    ):
        for _round in range(max_tool_rounds):
            response = await loop.run_in_executor(
                None,
                lambda m=list(messages): self.clients["anthropic"].messages.create(
                    model=_resolve_model_name("anthropic"),
                    max_tokens=1200,
                    temperature=0.6,
                    system=system_text,
                    messages=m,
                    tools=get_tool_schemas(),
                ),
            )

            tool_calls = []
            text_parts = []
            for part in response.content:
                if getattr(part, "type", "") == "tool_use":
                    tool_calls.append(part)
                if getattr(part, "type", "") == "text":
                    text_parts.append(part.text)

            if tool_calls:
                assistant_blocks = []
                for part in response.content:
                    if getattr(part, "type", "") == "text":
                        assistant_blocks.append({"type": "text", "text": part.text})
                    elif getattr(part, "type", "") == "tool_use":
                        assistant_blocks.append(
                            {"type": "tool_use", "id": part.id, "name": part.name, "input": part.input}
                        )
                messages.append({"role": "assistant", "content": assistant_blocks})

                tool_results = []
                for tc in tool_calls:
                    tool_name = tc.name
                    tool_args = dict(tc.input) if tc.input else {}
                    yield f"🛠️ **{tool_name}**({_format_args_preview(tool_name, tool_args)})"
                    result = await loop.run_in_executor(
                        None, lambda n=tool_name, a=tool_args: execute_tool(n, a)
                    )
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": tc.id, "content": str(result)}
                    )
                messages.append({"role": "user", "content": tool_results})
            else:
                yield "\n".join(text_parts).strip() or "Done."
                return

        yield "I hit the tool execution limit."

    async def _process_with_gemini(
        self,
        loop,
        message: str,
        messages: list[dict],
        system_text: str,
        max_tool_rounds: int,
    ):
        """
        Gemini fallback path for environments still configured with GOOGLE_API_KEY.
        """
        contents: list[types.Content] = []
        for msg in messages[:-1]:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append(types.Content(role=role, parts=[types.Part(text=str(msg["content"]))]))
        contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

        config = types.GenerateContentConfig(
            system_instruction=system_text,
            tools=[_build_gemini_tools()],
            temperature=0.6,
        )

        for _ in range(max_tool_rounds):
            response = await loop.run_in_executor(
                None,
                lambda c=list(contents): self.clients["gemini"].models.generate_content(
                    model=_resolve_model_name("gemini"),
                    contents=c,
                    config=config,
                ),
            )

            function_calls = []
            text_parts = []
            for part in response.candidates[0].content.parts:
                if getattr(part, "function_call", None):
                    function_calls.append(part.function_call)
                if getattr(part, "text", None):
                    text_parts.append(part.text)

            if function_calls:
                contents.append(response.candidates[0].content)
                function_response_parts = []
                for fc in function_calls:
                    tool_name = fc.name
                    tool_args = dict(fc.args) if fc.args else {}
                    yield f"🛠️ **{tool_name}**({_format_args_preview(tool_name, tool_args)})"
                    result = await loop.run_in_executor(
                        None, lambda n=tool_name, a=tool_args: execute_tool(n, a)
                    )
                    function_response_parts.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=tool_name,
                                response={"result": str(result)},
                            )
                        )
                    )
                contents.append(types.Content(role="user", parts=function_response_parts))
            else:
                yield "\n".join(text_parts).strip() or "Done."
                return

        yield "I hit the tool execution limit."


def _provider_order() -> list[str]:
    configured = [
        p.strip().lower()
        for p in (settings.provider_order or "gemini,anthropic").split(",")
        if p.strip()
    ]
    available = []
    for provider in configured:
        if provider == "gemini" and settings.google_api_key:
            available.append("gemini")
        elif provider == "anthropic" and settings.anthropic_api_key:
            available.append("anthropic")
    # Ensure fallback providers are still included if available but omitted.
    if settings.google_api_key and "gemini" not in available:
        available.append("gemini")
    if settings.anthropic_api_key and "anthropic" not in available:
        available.append("anthropic")
    return available


def _should_try_next_provider(error_text: str) -> bool:
    lowered = (error_text or "").lower()
    retry_markers = [
        "resource_exhausted",
        "quota",
        "rate limit",
        "authentication",
        "auth",
        "api key",
        "timeout",
        "temporarily unavailable",
        "service unavailable",
    ]
    return any(marker in lowered for marker in retry_markers)


def _build_gemini_tools() -> types.Tool:
    declarations = []
    for tool in get_tool_schemas():
        props = {}
        required = tool["input_schema"].get("required", [])
        for key, value in tool["input_schema"].get("properties", {}).items():
            t = value.get("type", "string")
            if t == "array":
                props[key] = types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(type=types.Type.STRING),
                    description=value.get("description", ""),
                )
            else:
                props[key] = types.Schema(
                    type=types.Type.STRING,
                    description=value.get("description", ""),
                )
        declarations.append(
            types.FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties=props,
                    required=required,
                ),
            )
        )
    return types.Tool(function_declarations=declarations)


def _resolve_model_name(provider: str) -> str:
    configured = (settings.model_name or "").strip()
    if provider == "gemini":
        return configured if configured.startswith("gemini") else "gemini-2.0-flash"
    return configured if configured.startswith("claude") else "claude-sonnet-4-20250514"


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
