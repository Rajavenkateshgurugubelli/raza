from app.tools.web import web_search, fetch_url
from app.tools.python_repl import run_python
from app.tools.zettelkasten import save_note, search_notes
from app.tools.google_workspace import (
    gmail_list_recent,
    gmail_create_draft,
    calendar_upcoming,
    calendar_create_event,
)

# Tool Registry
tools_list = [
    {
        "name": "web_search",
        "description": "Searches the web for a given query to find facts, news, etc. Returns top 5 results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "fetch_url",
        "description": "Fetches the full text content of a given URL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch."
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "run_python",
        "description": "Executes Python code. Good for data manipulation, calculations, or writing ad-hoc scripts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute."
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "save_note",
        "description": "Saves a note to the Zettelkasten memory store.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the note."
                },
                "content": {
                    "type": "string",
                    "description": "Content of the note."
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tags associated with the note."
                }
            },
            "required": ["title", "content"]
        }
    },
    {
        "name": "search_notes",
        "description": "Searches through notes in the Zettelkasten by matching title, content, or tags.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "gmail_list_recent",
        "description": "List recent Gmail messages, optionally filtered by Gmail query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "string", "description": "How many emails to fetch (1-20)."},
                "query": {"type": "string", "description": "Optional Gmail search query."}
            },
            "required": []
        }
    },
    {
        "name": "gmail_create_draft",
        "description": "Create a Gmail draft email.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address."},
                "subject": {"type": "string", "description": "Email subject."},
                "body": {"type": "string", "description": "Email plain text body."}
            },
            "required": ["to", "subject", "body"]
        }
    },
    {
        "name": "calendar_upcoming",
        "description": "List upcoming Google Calendar events.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "string", "description": "How many upcoming events to fetch (1-20)."},
                "calendar_id": {"type": "string", "description": "Calendar ID (default: primary)."}
            },
            "required": []
        }
    },
    {
        "name": "calendar_create_event",
        "description": "Create an event in Google Calendar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Event title."},
                "start_iso": {"type": "string", "description": "Start datetime in ISO format."},
                "end_iso": {"type": "string", "description": "End datetime in ISO format."},
                "timezone_name": {"type": "string", "description": "Timezone, e.g., Asia/Kolkata."},
                "description": {"type": "string", "description": "Optional description."},
                "calendar_id": {"type": "string", "description": "Calendar ID (default: primary)."}
            },
            "required": ["summary", "start_iso", "end_iso"]
        }
    }
]


def get_tool_schemas():
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": tool["input_schema"],
        }
        for tool in tools_list
    ]


def execute_tool(tool_name: str, tool_args: dict):
    try:
        if tool_name == "web_search":
            query = tool_args.get("query")
            return web_search(query)
        elif tool_name == "fetch_url":
            url = tool_args.get("url")
            return fetch_url(url)
        elif tool_name == "run_python":
            return run_python(tool_args.get("code"))
        elif tool_name == "save_note":
            return save_note(tool_args.get("title"), tool_args.get("content"), tool_args.get("tags"))
        elif tool_name == "search_notes":
            return search_notes(tool_args.get("query"))
        elif tool_name == "gmail_list_recent":
            limit = int(tool_args.get("limit", 5) or 5)
            return gmail_list_recent(limit=limit, query=tool_args.get("query", ""))
        elif tool_name == "gmail_create_draft":
            return gmail_create_draft(
                to=tool_args.get("to", ""),
                subject=tool_args.get("subject", ""),
                body=tool_args.get("body", ""),
            )
        elif tool_name == "calendar_upcoming":
            limit = int(tool_args.get("limit", 5) or 5)
            return calendar_upcoming(
                limit=limit,
                calendar_id=tool_args.get("calendar_id", "primary"),
            )
        elif tool_name == "calendar_create_event":
            return calendar_create_event(
                summary=tool_args.get("summary", ""),
                start_iso=tool_args.get("start_iso", ""),
                end_iso=tool_args.get("end_iso", ""),
                timezone_name=tool_args.get("timezone_name", "UTC"),
                description=tool_args.get("description", ""),
                calendar_id=tool_args.get("calendar_id", "primary"),
            )
        else:
            return f"Tool {tool_name} not found."
    except Exception as exc:
        # Basic fallback chain for web research actions.
        if tool_name == "fetch_url":
            url = tool_args.get("url", "")
            return web_search(url)
        if tool_name == "web_search":
            query = tool_args.get("query", "")
            if isinstance(query, str) and query.startswith(("http://", "https://")):
                return fetch_url(query)
        return f"Tool {tool_name} failed: {exc}"
