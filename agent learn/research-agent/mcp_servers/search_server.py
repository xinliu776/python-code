from ddgs import DDGS
from mcp.server import MCPServer

mcp = MCPServer("web-search")


@mcp.tool()
@mcp.tool()
@mcp.tool()
def web_search(
    query: str,
    max_results: int = 5
) -> dict:

    backends = [
        "bing",
        "google",
        "duckduckgo"
    ]

    errors = []

    for backend in backends:
        try:
            results = DDGS(timeout=10).text(
                query=query,
                max_results=max_results,
                backend=backend
            )

            results = list(results or [])

            if results:
                return {
                    "results": results,
                    "count": len(results),
                    "backend": backend
                }

        except Exception as e:
            errors.append(
                f"{backend}: {str(e)}"
            )

    return {
        "results": [],
        "count": 0,
        "error": errors or ["No results found"]
    }