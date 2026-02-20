from dataclasses import dataclass
from typing import Any

from web_mcp.search.fallback import FallbackSearchProvider
from web_mcp.utils.logger import get_logger

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

    def to_mcp_response(self) -> list[dict]:
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


_suggestions_provider: FallbackSearchProvider | None = None


def _get_provider() -> FallbackSearchProvider:
    """Get or create a singleton FallbackSearchProvider instance."""
    global _suggestions_provider
    if _suggestions_provider is None:
        _suggestions_provider = FallbackSearchProvider()
    return _suggestions_provider


async def get_suggestions(
    query: str, provider: FallbackSearchProvider | None = None
) -> SuggestionsResult:
    """
    Get search suggestions for a query.

    Args:
        query: The partial search query
        provider: Optional FallbackSearchProvider instance (uses singleton if not provided)

    Returns:
        SuggestionsResult with suggested queries
    """
    logger.info(f"Getting suggestions for query: {query}", extra={"query": query})

    if provider is None:
        provider = _get_provider()

    try:
        suggestions = await provider.get_suggestions(query)

        logger.info(
            f"Retrieved {len(suggestions)} suggestions",
            extra={"query": query, "suggestions_count": len(suggestions)},
        )

        return SuggestionsResult(
            query=query,
            suggestions=suggestions,
        )

    except Exception as e:
        logger.error(
            f"Failed to get suggestions: {e}",
            extra={"query": query, "error": str(e)},
        )
        return SuggestionsResult(
            query=query,
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
