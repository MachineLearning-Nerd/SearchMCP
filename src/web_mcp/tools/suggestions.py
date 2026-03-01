from dataclasses import dataclass
from typing import Any

from web_mcp.search.base import SearchProvider
from web_mcp.search.provider_registry import get_search_provider
from web_mcp.utils.logger import get_logger
from web_mcp.utils.validation import normalize_query

logger = get_logger("web_mcp")


@dataclass
class SuggestionsResult:
    """Result of getting search suggestions."""

    query: str
    suggestions: list[str]
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "suggestions": self.suggestions,
            "error": self.error,
        }

    def to_mcp_response(self) -> list[dict[str, str]]:
        """Convert to MCP tool response format."""
        if self.error:
            return [
                {
                    "type": "text",
                    "text": f"Error getting suggestions for '{self.query}': {self.error}",
                }
            ]

        if not self.suggestions:
            return [
                {
                    "type": "text",
                    "text": f"No suggestions available for query: {self.query}",
                }
            ]

        result_text = f"# Suggestions for: {self.query}\n\n"
        for i, suggestion in enumerate(self.suggestions, 1):
            result_text += f"{i}. {suggestion}\n"

        return [
            {
                "type": "text",
                "text": result_text,
            }
        ]


async def get_suggestions(
    query: str, provider: SearchProvider | None = None
) -> SuggestionsResult:
    """
    Get search suggestions for a query.

    Args:
        query: The partial search query
        provider: Optional FallbackSearchProvider instance (uses singleton if not provided)

    Returns:
        SuggestionsResult with suggested queries
    """
    normalized_query = query
    try:
        normalized_query = normalize_query(query)

        logger.info(
            f"Getting suggestions for query: {normalized_query}",
            extra={"query": normalized_query},
        )

        if provider is None:
            provider = get_search_provider()

        suggestions = await provider.get_suggestions(normalized_query)

        logger.info(
            f"Retrieved {len(suggestions)} suggestions",
            extra={"query": normalized_query, "suggestions_count": len(suggestions)},
        )

        return SuggestionsResult(
            query=normalized_query,
            suggestions=suggestions,
        )

    except Exception as e:
        logger.error(
            f"Failed to get suggestions: {e}",
            extra={"query": query, "error": str(e)},
        )
        return SuggestionsResult(
            query=normalized_query,
            suggestions=[],
            error=str(e),
        )


TOOL_SCHEMA = {
    "name": "get_suggestions",
    "description": "Get search query suggestions. Useful for autocomplete or query refinement.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The partial search query to get suggestions for",
            },
        },
        "required": ["query"],
    },
}
