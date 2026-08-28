import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from mcp.server import MCPServer
import json
from openai import OpenAI

mcp = MCPServer("web_search_mcp")


SEARCH_BACKENDS = (
    "auto",
    "duckduckgo",
    "startpage",
    "yahoo",
)

@mcp.tool()
def web_search(
    query: str,
    max_results: int = 5
) -> dict:
    """Search the web and return up to ``max_results`` results."""

    errors = []

    for backend in SEARCH_BACKENDS:
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

@mcp.tool()
def read_webpage(
    url: str,
    max_chars: int = 10000
) -> dict:
    """读取网页正文内容"""

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=10
        )

        response.raise_for_status()

        # 暂时不处理 PDF
        content_type = response.headers.get("Content-Type", "")

        if "application/pdf" in content_type:
            return {
                "url": url,
                "error": "暂不支持PDF读取"
            }

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # 去掉无用内容
        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header"
        ]):
            tag.decompose()

        paragraphs = [
            p.get_text(" ", strip=True)
            for p in soup.find_all("p")
        ]

        text = "\n".join(
            p for p in paragraphs if p
        )

        return {
            "url": url,
            "content": text[:max_chars]
        }

    except Exception as e:
        return {
            "url": url,
            "error": str(e)
        }


if __name__ == "__main__":
    # Local MCP clients and Inspector connect over stdio by default.
    mcp.run()
