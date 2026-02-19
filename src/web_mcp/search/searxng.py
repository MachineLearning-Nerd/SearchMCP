from typing import Any

import httpx

from web_mcp.config import settings
from web_mcp.search.base import SearchProvider, SearchResponse, SearchResult
from web_mcp.utils.logger import get_logger


class SearxNGProvider(SearchProvider):
    VALID_CATEGORIES: set[str] = {"general", "images", "videos", "news", "science", "files"}

    def __init__(self, base_url: str | None = None, timeout: int | None = None):
        self._base_url = (base_url or settings.SEARXNG_URL).rstrip("/")
        self._timeout = timeout or settings.SEARXNG_TIMEOUT
        self._logger = get_logger("web_mcp")
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "searxng"

    @property
    def is_available(self) -> bool:
        return bool(self._base_url)

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _validate_category(self, category: str) -> str:
        if category not in self.VALID_CATEGORIES:
            self._logger.warning(
                f"Invalid category '{category}', falling back to 'general'",
                extra={"category": category, "valid_categories": list(self.VALID_CATEGORIES)},
            )
            return "general"
        return category

    def _parse_result(self, item: dict[str, Any]) -> SearchResult:
        return SearchResult(
            title=item.get("title", ""),
            url=item.get("url", ""),
            description=item.get("content", ""),
            source=item.get("engine", ""),
        )

    def _parse_response(self, data: dict[str, Any], query: str, limit: int = 0) -> SearchResponse:
        results_data = data.get("results", [])
        suggestions = data.get("suggestions", []) or data.get("corrections", [])

        if isinstance(suggestions, list):
            suggestions = [str(s) for s in suggestions if s]
        else:
            suggestions = []

        results = [self._parse_result(item) for item in results_data if item.get("url")]

        if limit > 0:
            results = results[:limit]

        return SearchResponse(
            results=results,
            suggestions=suggestions,
            provider=self.name,
            query=query,
        )

    async def search(self, query: str, category: str = "general", limit: int = 5) -> SearchResponse:
        category = self._validate_category(category)

        params: dict[str, Any] = {
            "format": "json",
            "q": query,
            "categories": category,
        }

        url = f"{self._base_url}/search"

        self._logger.debug(
            f"Searching SearxNG: {query}",
            extra={"url": url, "category": category, "limit": limit},
        )

        try:
            client = self._get_client()
            response = await client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if not isinstance(data, dict):
                self._logger.error(
                    "Invalid response format from SearxNG",
                    extra={"response_type": type(data).__name__},
                )
                return SearchResponse(
                    results=[],
                    suggestions=[],
                    provider=self.name,
                    query=query,
                )

            search_response = self._parse_response(data, query, limit)

            self._logger.info(
                f"SearxNG search completed: {len(search_response.results)} results",
                extra={
                    "query": query,
                    "category": category,
                    "results_count": len(search_response.results),
                },
            )

            return search_response

        except httpx.TimeoutException as e:
            self._logger.error(
                f"SearxNG request timed out: {e}",
                extra={"url": url, "timeout": self._timeout, "error": str(e)},
            )
            return SearchResponse(
                results=[],
                suggestions=[],
                provider=self.name,
                query=query,
            )

        except httpx.ConnectError as e:
            self._logger.error(
                f"Failed to connect to SearxNG: {e}",
                extra={"url": url, "error": str(e)},
            )
            return SearchResponse(
                results=[],
                suggestions=[],
                provider=self.name,
                query=query,
            )

        except httpx.HTTPStatusError as e:
            self._logger.error(
                f"SearxNG HTTP error: {e.response.status_code}",
                extra={"url": url, "status_code": e.response.status_code, "error": str(e)},
            )
            return SearchResponse(
                results=[],
                suggestions=[],
                provider=self.name,
                query=query,
            )

        except httpx.HTTPError as e:
            self._logger.error(
                f"SearxNG HTTP error: {e}",
                extra={"url": url, "error": str(e)},
            )
            return SearchResponse(
                results=[],
                suggestions=[],
                provider=self.name,
                query=query,
            )

        except (KeyError, TypeError, ValueError) as e:
            self._logger.error(
                f"Failed to parse SearxNG response: {e}",
                extra={"error": str(e)},
            )
            return SearchResponse(
                results=[],
                suggestions=[],
                provider=self.name,
                query=query,
            )

    async def get_suggestions(self, query: str) -> list[str]:
        params: dict[str, Any] = {
            "format": "json",
            "q": query,
        }

        url = f"{self._base_url}/search"

        self._logger.debug(f"Getting suggestions from SearxNG: {query}", extra={"url": url})

        try:
            client = self._get_client()
            response = await client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if not isinstance(data, dict):
                self._logger.error(
                    "Invalid response format from SearxNG",
                    extra={"response_type": type(data).__name__},
                )
                return []

            suggestions = data.get("suggestions", []) or data.get("corrections", [])

            if isinstance(suggestions, list):
                suggestions = [str(s) for s in suggestions if s]
            else:
                suggestions = []

            self._logger.debug(
                f"SearxNG suggestions: {len(suggestions)} found",
                extra={"query": query, "suggestions_count": len(suggestions)},
            )

            return suggestions

        except httpx.TimeoutException as e:
            self._logger.error(
                f"SearxNG suggestions request timed out: {e}",
                extra={"url": url, "timeout": self._timeout, "error": str(e)},
            )
            return []

        except httpx.ConnectError as e:
            self._logger.error(
                f"Failed to connect to SearxNG: {e}",
                extra={"url": url, "error": str(e)},
            )
            return []

        except httpx.HTTPStatusError as e:
            self._logger.error(
                f"SearxNG HTTP error: {e.response.status_code}",
                extra={"url": url, "status_code": e.response.status_code, "error": str(e)},
            )
            return []

        except httpx.HTTPError as e:
            self._logger.error(
                f"SearxNG HTTP error: {e}",
                extra={"url": url, "error": str(e)},
            )
            return []

        except (KeyError, TypeError, ValueError) as e:
            self._logger.error(
                f"Failed to parse SearxNG suggestions: {e}",
                extra={"error": str(e)},
            )
            return []
