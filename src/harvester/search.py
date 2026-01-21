from mcp.server.fastmcp import FastMCP
from duckduckgo_search import DDGS
import time

mcp = FastMCP("WebSearcher")

@mcp.tool()
def search_duckduckgo(query: str) -> str:
    """Searches the web for real-time information and returns snippets."""
    max_retries = 3
    retry_delay = 2 # seconds
    
    for attempt in range(max_retries):
        try:
            results_list = []
            with DDGS() as ddgs:
                # We limit to 5 results to keep the AI from getting overwhelmed
                results = ddgs.text(query, max_results=5)
                if results:
                    for r in results:
                        results_list.append(f"Title: {r['title']}\nSnippet: {r['body']}\nURL: {r['href']}\n")
                    return "\n---\n".join(results_list)
                else:
                    return "No results found for your query."
                    
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return f"Error after {max_retries} attempts: {str(e)}"
    
    return "Search failed unexpectedly."

if __name__ == "__main__":
    mcp.run()