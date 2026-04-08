import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

def web_search(query: str) -> str:
    """Searches the web using DuckDuckGo."""
    try:
        results = ""
        with DDGS() as ddgs:
            # Get up to 5 results
            for idx, r in enumerate(ddgs.text(query, max_results=5)):
                results += f"[{idx+1}] {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n\n"
        return results if results else "No results found."
    except Exception as e:
        return f"Error during search: {e}"

def fetch_url(url: str) -> str:
    """Fetches the text content of a URL."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text(separator=' ', strip=True)
        # Limit to 5000 characters to save context space
        return text[:5000] + ("..." if len(text) > 5000 else "")
    except Exception as e:
        return f"Error fetching URL: {e}"
