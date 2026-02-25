from dataclasses import dataclass
from typing import Any

from web_mcp.config import settings
from web_mcp.search.base import SearchResponse
from web_mcp.search.fallback import FallbackSearchProvider
from web_mcp.utils.logger import get_logger

logger = get_logger("web_mcp")


@dataclass
class WebSearchResult:
    """Result of a web search."""

    query: str
    results: list[dict[str, Any]]
    suggestions: list[str]
    provider: str
    total: int
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "results": self.results,
            "suggestions": self.suggestions,
            "provider": self.provider,
            "total": self.total,
            "error": self.error,
        }

    def to_mcp_response(self) -> list[dict[str, str]]:
        """Convert to MCP tool response format."""
        if not self.results:
            return [
                {
                    "type": "text",
                    "text": f"No results found for query: {self.query}",
                }
            ]

        lines = [f"# Search Results for: {self.query}\n"]
        lines.append(f"*Provider: {self.provider} | {self.total} results*\n")
        lines.append("---\n")

        for i, result in enumerate(self.results, 1):
            title = result.get("title", "Untitled")
            url = result.get("url", "")
            description = result.get("description", "")

            lines.append(f"## {i}. {title}\n")
            lines.append(f"**URL:** {url}\n")
            if description:
                lines.append(f"\n{description}\n")
            lines.append("\n")

        if self.suggestions:
            lines.append("---\n")
            lines.append("### Related searches\n")
            for suggestion in self.suggestions[:5]:
                lines.append(f"- {suggestion}")
            lines.append("")

        return [
            {
                "type": "text",
                "text": "\n".join(lines),
            }
        ]


_search_provider: FallbackSearchProvider | None = None


def _get_provider() -> FallbackSearchProvider:
    global _search_provider
    if _search_provider is None:
        _search_provider = FallbackSearchProvider()
    return _search_provider


async def web_search(
    query: str, category: str = "general", limit: int | None = None
) -> WebSearchResult:
    """
    Search the web for information.

    Args:
        query: The search query
        category: Search category (general, images, videos, news, science, files)
        limit: Maximum number of results (default from settings)

    Returns:
        WebSearchResult with search results
    """
    if limit is None:
        limit = settings.DEFAULT_SEARCH_LIMIT

    logger.info(
        "Performing web search",
        extra={"query": query, "category": category, "limit": limit},
    )

    try:
        provider = _get_provider()
        response: SearchResponse = await provider.search(query, category, limit)

        results = [r.to_dict() for r in response.results]

        logger.info(
            "Search completed",
            extra={
                "query": query,
                "provider": response.provider,
                "results_count": len(results),
            },
        )

        return WebSearchResult(
            query=query,
            results=results,
            suggestions=response.suggestions,
            provider=response.provider,
            total=len(results),
        )

    except Exception as e:
        logger.error(
            f"Search failed: {e}",
            extra={"query": query, "error": str(e)},
        )
        return WebSearchResult(
            query=query,
            results=[],
            suggestions=[],
            provider="error",
            total=0,
            error=str(e),
        )


TOOL_SCHEMA = {
    "name": "web_search",
    "description": "Search the web for information. Returns relevant search results with titles, URLs, and descriptions.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query",
            },
            "category": {
                "type": "string",
                "description": "Search category: general (default), images, videos, news, science, files",
                "enum": ["general", "images", "videos", "news", "science", "files"],
            },
            "limit": {
                "type": "number",
                "description": "Maximum number of results to return (default: 5)",
            },
        },
        "required": ["query"],
    },
}
