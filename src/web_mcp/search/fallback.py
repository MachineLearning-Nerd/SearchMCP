from web_mcp.config import settings
from web_mcp.search.base import SearchProvider, SearchResponse
from web_mcp.search.google import GOOGLE_TIMEOUT, GoogleProvider
from web_mcp.search.searxng import SearxNGProvider
from web_mcp.utils.logger import get_logger
from web_mcp.utils.rate_limiter import RateLimiter


class FallbackSearchProvider(SearchProvider):
    def __init__(
        self,
        searxng_url: str | None = None,
        fallback_enabled: bool | None = None,
        rate_limiter: RateLimiter | None = None,
    ):
        self._searxng = SearxNGProvider(base_url=searxng_url)
        self._google = GoogleProvider(timeout=GOOGLE_TIMEOUT)
        self._fallback_enabled = (
            fallback_enabled if fallback_enabled is not None else settings.FALLBACK_ENABLED
        )
        self._rate_limiter = rate_limiter or RateLimiter()
        self._logger = get_logger("web_mcp")

    @property
    def name(self) -> str:
        return "fallback"

    @property
    def is_available(self) -> bool:
        return self._searxng.is_available or (self._fallback_enabled and self._google.is_available)

    async def search(self, query: str, category: str = "general", limit: int = 5) -> SearchResponse:
        await self._rate_limiter.acquire()

        if not self._searxng.is_available and not self._fallback_enabled:
            self._logger.warning("No search providers available")
            return SearchResponse(
                results=[],
                suggestions=[],
                provider=self.name,
                query=query,
            )

        response = await self._searxng.search(query, category, limit)

        if response.results:
            self._logger.info(
                f"SearxNG returned {len(response.results)} results",
                extra={"query": query, "provider": "searxng"},
            )
            return response

        if not self._fallback_enabled:
            self._logger.info(
                "SearxNG returned no results, fallback disabled",
                extra={"query": query},
            )
            return response

        self._logger.info(
            "SearxNG returned no results, falling back to Google",
            extra={"query": query, "provider": "google"},
        )

        return await self._google.search(query, category, limit)

    async def get_suggestions(self, query: str) -> list[str]:
        await self._rate_limiter.acquire()

        suggestions = await self._searxng.get_suggestions(query)

        if suggestions:
            return suggestions

        if self._fallback_enabled:
            return await self._google.get_suggestions(query)

        return []

    async def close(self) -> None:
        await self._searxng.close()
