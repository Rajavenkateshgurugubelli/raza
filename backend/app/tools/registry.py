from app.tools.web import web_search, fetch_url
from app.tools.python_repl import run_python
from app.tools.zettelkasten import save_note, search_notes

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
    }
]

def execute_tool(tool_name: str, tool_args: dict):
    if tool_name == "web_search":
        return web_search(tool_args.get("query"))
    elif tool_name == "fetch_url":
        return fetch_url(tool_args.get("url"))
    elif tool_name == "run_python":
        return run_python(tool_args.get("code"))
    elif tool_name == "save_note":
        return save_note(tool_args.get("title"), tool_args.get("content"), tool_args.get("tags"))
    elif tool_name == "search_notes":
        return search_notes(tool_args.get("query"))
    else:
        return f"Tool {tool_name} not found."
