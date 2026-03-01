from dataclasses import dataclass
from typing import Any

from web_mcp.config import settings
from web_mcp.utils.content_extractor import ContentExtractor, ExtractedContent
from web_mcp.utils.logger import get_logger
from web_mcp.utils.validation import normalize_int_param

logger = get_logger("web_mcp")
_content_extractor: ContentExtractor | None = None
MIN_CONTENT_LENGTH = 500
MAX_CONTENT_LENGTH = 20000
DEFAULT_CONTENT_LENGTH = min(MAX_CONTENT_LENGTH, max(MIN_CONTENT_LENGTH, settings.MAX_CONTENT_LENGTH))


@dataclass
class FetchContentResult:
    """Result of fetching content from a URL."""

    url: str
    title: str
    content: str
    description: str = ""
    author: str = ""
    source: str = ""
    content_type: str = ""
    truncated: bool = False
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "description": self.description,
            "author": self.author,
            "source": self.source,
            "content_type": self.content_type,
            "truncated": self.truncated,
            "error": self.error,
        }

    def to_mcp_response(self) -> list[dict[str, str]]:
        """Convert to MCP tool response format."""
        if self.error:
            return [
                {
                    "type": "text",
                    "text": f"Error fetching content from {self.url}: {self.error}",
                }
            ]

        result_text = f"# {self.title}\n\n"
        if self.description:
            result_text += f"> {self.description}\n\n"
        if self.author:
            result_text += f"**Author:** {self.author}\n\n"
        if self.source:
            result_text += f"**Source:** {self.source}\n\n"
        result_text += f"**URL:** {self.url}\n\n"
        result_text += "---\n\n"
        result_text += self.content

        if self.truncated:
            result_text += "\n\n*[Content truncated due to length limit]*"

        return [
            {
                "type": "text",
                "text": result_text,
            }
        ]


async def fetch_content(url: str, max_length: int | float | None = None) -> FetchContentResult:
    """
    Fetch and extract content from a URL.

    Args:
        url: The URL to fetch content from
        max_length: Maximum content length in characters (default from settings)

    Returns:
        FetchContentResult with extracted content
    """
    normalized_url = url
    try:
        normalized_url = _normalize_url(url)
        normalized_max_length = normalize_int_param(
            max_length, MIN_CONTENT_LENGTH, MAX_CONTENT_LENGTH, DEFAULT_CONTENT_LENGTH, "max_length"
        )

        logger.info(
            f"Fetching content from {normalized_url}",
            extra={"url": normalized_url, "max_length": normalized_max_length},
        )

        global _content_extractor
        if _content_extractor is None:
            _content_extractor = ContentExtractor()
        extracted: ExtractedContent = await _content_extractor.extract(
            normalized_url,
            max_length=normalized_max_length,
        )

        if extracted.error:
            logger.warning(
                f"Content extraction failed: {extracted.error}",
                extra={"url": normalized_url, "error": extracted.error},
            )
            return FetchContentResult(
                url=normalized_url,
                title="",
                content="",
                error=extracted.error,
            )

        logger.info(
            "Content extracted successfully",
            extra={
                "url": normalized_url,
                "title": extracted.title,
                "content_length": len(extracted.content),
                "truncated": extracted.truncated,
            },
        )

        return FetchContentResult(
            url=normalized_url,
            title=extracted.title,
            content=extracted.content,
            description=extracted.description or "",
            author=extracted.author or "",
            source=extracted.source or "",
            content_type=extracted.content_type or "",
            truncated=extracted.truncated,
        )

    except Exception as e:
        logger.error(f"Failed to fetch content: {e}", extra={"url": url, "error": str(e)})
        return FetchContentResult(
            url=normalized_url,
            title="",
            content="",
            error=str(e),
        )


def _normalize_url(url: str) -> str:
    if not isinstance(url, str):
        raise ValueError("url must be a non-empty string")
    normalized = url.strip()
    if not normalized:
        raise ValueError("url must be a non-empty string")
    return normalized


TOOL_SCHEMA = {
    "name": "fetch_content",
    "description": "Fetch and extract readable content from a URL. Returns content as markdown.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch content from",
            },
            "max_length": {
                "type": "integer",
                "description": "Maximum content length in characters (default: 10000)",
                "minimum": MIN_CONTENT_LENGTH,
                "maximum": MAX_CONTENT_LENGTH,
                "default": DEFAULT_CONTENT_LENGTH,
            },
        },
        "required": ["url"],
    },
}
