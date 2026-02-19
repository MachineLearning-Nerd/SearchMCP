import random
from typing import Any, Final

import httpx
from bs4 import BeautifulSoup

from web_mcp.config import settings
from web_mcp.search.base import SearchProvider, SearchResult, SearchResponse
from web_mcp.utils.logger import get_logger

logger = get_logger()

USER_AGENTS: Final[list[str]] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

GOOGLE_SEARCH_URL: Final[str] = "https://www.google.com/search"
GOOGLE_TIMEOUT: int = 10  # Default timeout for Google requests


class GoogleProvider(SearchProvider):
    def __init__(self, timeout: int | None = None):
        self._timeout = httpx.Timeout(timeout or GOOGLE_TIMEOUT)
        self._available: bool | None = None

    @property
    def name(self) -> str:
        return "google"

    @property
    def is_available(self) -> bool:
        if self._available is None:
            return settings.FALLBACK_ENABLED
        return self._available

    def _get_headers(self) -> dict[str, str]:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def search(self, query: str, category: str = "general", limit: int = 5) -> SearchResponse:
        logger.info(
            f"Starting Google search for query: {query}", extra={"query": query, "limit": limit}
        )

        results = await self._scrape_google(query, limit)

        return SearchResponse(
            results=results,
            suggestions=[],
            provider=self.name,
            query=query,
        )

    async def _scrape_google(self, query: str, limit: int) -> list[SearchResult]:
        params = {"q": query, "num": str(limit + 2)}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    GOOGLE_SEARCH_URL,
                    params=params,
                    headers=self._get_headers(),
                    follow_redirects=True,
                )

                if response.status_code == 429:
                    logger.warning("Google rate limit hit (429)", extra={"query": query})
                    self._available = False
                    return []

                response.raise_for_status()
                return self._parse_results(response.text, limit)

        except httpx.ConnectError as e:
            logger.error(f"Connection error to Google: {e}", extra={"query": query})
            self._available = False
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Google: {e}", extra={"query": query})
            return []
        except Exception as e:
            logger.error(f"Unexpected error scraping Google: {e}", extra={"query": query})
            return []

    def _parse_results(self, html: str, limit: int) -> list[SearchResult]:
        results: list[SearchResult] = []

        try:
            soup = BeautifulSoup(html, "lxml")
            containers = soup.select("div.g")

            for container in containers[:limit]:
                result = self._extract_result(container)
                if result:
                    results.append(result)

            logger.info(f"Parsed {len(results)} results from Google")

        except Exception as e:
            logger.error(f"Error parsing Google results: {e}")

        return results

    def _extract_result(self, container: Any) -> SearchResult | None:
        try:
            title_elem = container.select_one("h3")
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True)

            link_elem = container.select_one("a[href]")
            if not link_elem:
                return None
            url = link_elem.get("href", "")
            if not url or not url.startswith("http"):
                return None

            description = ""
            desc_selectors = [
                "div[data-sncf]",
                "div.VwiC3b",
                "span.aCOpRe",
                "div.IsZvec",
            ]
            for selector in desc_selectors:
                desc_elem = container.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                    break

            return SearchResult(
                title=title,
                url=url,
                description=description,
                source="google",
            )

        except Exception as e:
            logger.debug(f"Error extracting result: {e}")
            return None

    async def get_suggestions(self, query: str) -> list[str]:
        return []
