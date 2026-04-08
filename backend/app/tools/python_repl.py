import io
import sys
import contextlib

def run_python(code: str) -> str:
    """Executes arbitrary Python code and returns the stdout output."""
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            # A dictionary to serve as the global and local scope
            exec_globals = {}
            exec(code, exec_globals)
        res = output.getvalue()
        return res if res else "Code executed successfully with no output."
    except Exception as e:
        return f"Error executing Python code: {e}"
