from dataclasses import dataclass
from urllib.parse import urlparse
import httpx
import trafilatura
from typing import Any

from web_mcp.utils.logger import get_logger

logger = get_logger("web_mcp")


@dataclass
class ExtractedContent:
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


class ContentExtractor:
    DEFAULT_TIMEOUT = 10
    DEFAULT_MAX_LENGTH = 10000
    USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(self, timeout: int = DEFAULT_TIMEOUT, max_length: int = DEFAULT_MAX_LENGTH):
        self.timeout = timeout
        self.max_length = max_length

    async def extract(self, url: str, max_length: int | None = None) -> ExtractedContent:
        max_len = max_length if max_length is not None else self.max_length
        domain = self._extract_domain(url)

        try:
            html, fetch_meta = await self.fetch(url)
            content_type = fetch_meta.get("content_type", "")

            markdown, meta = self._html_to_markdown(html, url)

            if not markdown:
                return ExtractedContent(
                    url=url,
                    title="",
                    content="",
                    source=domain,
                    content_type=content_type,
                    error="Failed to extract content from page",
                )

            truncated_content, was_truncated = self._truncate(markdown, max_len)

            return ExtractedContent(
                url=url,
                title=meta.get("title", ""),
                content=truncated_content,
                description=meta.get("description", ""),
                author=meta.get("author", ""),
                source=domain,
                content_type=content_type,
                truncated=was_truncated,
            )

        except httpx.TimeoutException:
            logger.error(f"Timeout fetching URL: {url}")
            return ExtractedContent(
                url=url,
                title="",
                content="",
                source=domain,
                error=f"Request timed out after {self.timeout} seconds",
            )
        except httpx.ConnectError as e:
            logger.error(f"Connection error for URL {url}: {e}")
            return ExtractedContent(
                url=url,
                title="",
                content="",
                source=domain,
                error=f"Failed to connect: {str(e)}",
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for URL {url}: {e}")
            return ExtractedContent(
                url=url,
                title="",
                content="",
                source=domain,
                error=f"HTTP error {e.response.status_code}",
            )
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return ExtractedContent(
                url=url,
                title="",
                content="",
                source=domain,
                error=f"Extraction failed: {str(e)}",
            )

    async def fetch(self, url: str) -> tuple[str, dict[str, Any]]:
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            html = response.text

            meta: dict[str, Any] = {
                "content_type": content_type,
                "status_code": response.status_code,
                "final_url": str(response.url),
            }

            return html, meta

    def _html_to_markdown(self, html: str, url: str) -> tuple[str, dict[str, str]]:
        """Convert HTML to markdown using trafilatura.

        Note: We use the already-fetched HTML instead of calling trafilatura.fetch_url()
        to avoid making redundant HTTP requests.
        """
        try:
            content = trafilatura.extract(
                html,
                include_comments=False,
                favor_precision=True,
                include_links=True,
                output_format="markdown",
                url=url,
                with_metadata=True,
            )

            metadata = trafilatura.extract_metadata(html, default_url=url)

            meta: dict[str, str] = {
                "title": metadata.title if metadata else "",
                "description": metadata.description if metadata else "",
                "author": metadata.author if metadata else "",
            }

            return content or "", meta

        except Exception as e:
            logger.warning(f"Trafilatura extraction failed for {url}: {e}")
            return "", {}

    def _truncate(self, content: str, max_length: int) -> tuple[str, bool]:
        """Truncate content to max_length, preserving word boundaries. Returns (content, was_truncated)."""
        if len(content) <= max_length:
            return content, False

        truncated = content[:max_length]
        last_space = truncated.rfind(" ")
        last_newline = truncated.rfind("\n")
        cut_point = max(last_space, last_newline)

        if cut_point > max_length * 0.8:
            truncated = truncated[:cut_point]

        return truncated.rstrip() + "\n\n[Content truncated...]", True

    def _extract_domain(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            return parsed.netloc or ""
        except Exception:
            return ""
