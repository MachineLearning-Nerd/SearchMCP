from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from web_mcp.config import settings
from web_mcp.search.base import SearchResponse
from web_mcp.search.provider_registry import get_search_provider
from web_mcp.utils.logger import get_logger

logger = get_logger("web_mcp")
MIN_LIMIT = 1
MAX_LIMIT = 10
VALID_CATEGORIES = {"general", "images", "videos", "news", "science", "files"}
DEFAULT_LIMIT = min(MAX_LIMIT, max(MIN_LIMIT, settings.DEFAULT_SEARCH_LIMIT))


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
        if self.error:
            return [
                {
                    "type": "text",
                    "text": f"Search failed for query '{self.query}': {self.error}",
                }
            ]

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
            title = _compact_text(str(result.get("title", "Untitled")), max_length=160)
            url = str(result.get("url", ""))
            description = _compact_text(str(result.get("description", "")), max_length=320)
            source = str(result.get("source", "")).strip()
            domain = _extract_domain(url)

            lines.append(f"## {i}. {title}\n")
            lines.append(f"**URL:** {url}\n")
            if source or domain:
                source_parts = [part for part in [source, domain] if part]
                lines.append(f"**Source:** {' | '.join(source_parts)}\n")
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


def _compact_text(value: str, max_length: int) -> str:
    compact = " ".join(value.split())
    if len(compact) <= max_length:
        return compact
    return f"{compact[: max_length - 3]}..."


def _extract_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc


def _normalize_query(query: str) -> str:
    if not isinstance(query, str):
        raise ValueError("query must be a non-empty string")
    normalized = " ".join(query.split())
    if not normalized:
        raise ValueError("query must be a non-empty string")
    return normalized


def _normalize_category(category: str) -> str:
    if not isinstance(category, str):
        valid = ", ".join(sorted(VALID_CATEGORIES))
        raise ValueError(f"category must be one of: {valid}")
    normalized = category.strip().lower()
    if normalized not in VALID_CATEGORIES:
        valid = ", ".join(sorted(VALID_CATEGORIES))
        raise ValueError(f"category must be one of: {valid}")
    return normalized


def _normalize_limit(limit: int | float | None) -> int:
    if limit is None:
        limit = DEFAULT_LIMIT

    if isinstance(limit, bool) or not isinstance(limit, (int, float)):
        raise ValueError(f"limit must be an integer between {MIN_LIMIT} and {MAX_LIMIT}")

    if isinstance(limit, float):
        if not limit.is_integer():
            raise ValueError(f"limit must be an integer between {MIN_LIMIT} and {MAX_LIMIT}")
        limit = int(limit)

    resolved = int(limit)
    if resolved < MIN_LIMIT or resolved > MAX_LIMIT:
        raise ValueError(f"limit must be between {MIN_LIMIT} and {MAX_LIMIT}")

    return resolved


async def web_search(
    query: str, category: str = "general", limit: int | float | None = None
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
    try:
        normalized_query = _normalize_query(query)
        normalized_category = _normalize_category(category)
        normalized_limit = _normalize_limit(limit)

        logger.info(
            "Performing web search",
            extra={
                "query": normalized_query,
                "category": normalized_category,
                "limit": normalized_limit,
            },
        )

        provider = get_search_provider()
        response: SearchResponse = await provider.search(
            normalized_query,
            normalized_category,
            normalized_limit,
        )

        results = [r.to_dict() for r in response.results]

        logger.info(
            "Search completed",
            extra={
                "query": normalized_query,
                "provider": response.provider,
                "results_count": len(results),
            },
        )

        return WebSearchResult(
            query=normalized_query,
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
            query=normalized_query if "normalized_query" in locals() else query,
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
                "type": "integer",
                "description": "Maximum number of results to return (default: 5)",
                "minimum": MIN_LIMIT,
                "maximum": MAX_LIMIT,
                "default": DEFAULT_LIMIT,
            },
        },
        "required": ["query"],
    },
}
