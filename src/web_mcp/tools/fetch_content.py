from dataclasses import dataclass
from typing import Any

from web_mcp.config import settings
from web_mcp.utils.content_extractor import ContentExtractor, ExtractedContent
from web_mcp.utils.logger import get_logger

logger = get_logger("web_mcp")


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

    def to_mcp_response(self) -> list[dict]:
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


async def fetch_content(url: str, max_length: int | None = None) -> FetchContentResult:
    """
    Fetch and extract content from a URL.

    Args:
        url: The URL to fetch content from
        max_length: Maximum content length in characters (default from settings)

    Returns:
        FetchContentResult with extracted content
    """
    if max_length is None:
        max_length = settings.MAX_CONTENT_LENGTH

    logger.info(f"Fetching content from {url}", extra={"url": url, "max_length": max_length})

    try:
        extractor = ContentExtractor()
        extracted: ExtractedContent = await extractor.extract(url, max_length=max_length)

        if extracted.error:
            logger.warning(
                f"Content extraction failed: {extracted.error}",
                extra={"url": url, "error": extracted.error},
            )
            return FetchContentResult(
                url=url,
                title="",
                content="",
                error=extracted.error,
            )

        logger.info(
            f"Content extracted successfully",
            extra={
                "url": url,
                "title": extracted.title,
                "content_length": len(extracted.content),
                "truncated": extracted.truncated,
            },
        )

        return FetchContentResult(
            url=url,
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
            url=url,
            title="",
            content="",
            error=str(e),
        )


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
                "type": "number",
                "description": "Maximum content length in characters (default: 10000)",
            },
        },
        "required": ["url"],
    },
}
