from unittest.mock import AsyncMock, patch

import pytest

from web_mcp.search.base import SearchResponse, SearchResult
from web_mcp.search.fallback import FallbackSearchProvider


class TestFallbackSearchProvider:
    @pytest.mark.asyncio
    async def test_security_query_triggers_quality_fallback(self):
        provider = FallbackSearchProvider(fallback_enabled=True, min_quality_score=2.5)

        searxng_response = SearchResponse(
            results=[
                SearchResult(
                    title="word frequencies",
                    url="http://example.com/data.counts",
                    description="dictionary list",
                    source="google",
                )
            ],
            suggestions=[],
            provider="searxng",
            query="CVE-2026-26007 waiver",
        )
        google_response = SearchResponse(
            results=[
                SearchResult(
                    title="NVD - CVE-2026-26007",
                    url="https://nvd.nist.gov/vuln/detail/CVE-2026-26007",
                    description="Official record",
                    source="google",
                )
            ],
            suggestions=[],
            provider="google",
            query="CVE-2026-26007 waiver",
        )

        with (
            patch.object(provider._searxng, "search", AsyncMock(return_value=searxng_response)),
            patch.object(provider._google, "search", AsyncMock(return_value=google_response)),
        ):
            response = await provider.search("CVE-2026-26007 waiver", limit=3)

        assert response.provider in {"searxng+google", "google"}
        assert response.results
        assert response.results[0].url.startswith("https://nvd.nist.gov/vuln/detail/CVE-2026-26007")

    @pytest.mark.asyncio
    async def test_security_query_keeps_searxng_when_quality_is_high(self):
        provider = FallbackSearchProvider(fallback_enabled=True, min_quality_score=2.5)

        searxng_response = SearchResponse(
            results=[
                SearchResult(
                    title="NVD - CVE-2026-26007",
                    url="https://nvd.nist.gov/vuln/detail/CVE-2026-26007",
                    description="Official record",
                    source="brave",
                )
            ],
            suggestions=[],
            provider="searxng",
            query="CVE-2026-26007 waiver",
        )

        google_mock = AsyncMock()
        with (
            patch.object(provider._searxng, "search", AsyncMock(return_value=searxng_response)),
            patch.object(provider._google, "search", google_mock),
        ):
            response = await provider.search("CVE-2026-26007 waiver", limit=3)

        assert response.provider == "searxng"
        assert response.results
        google_mock.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_general_query_does_not_use_quality_trigger(self):
        provider = FallbackSearchProvider(fallback_enabled=True, min_quality_score=2.5)

        searxng_response = SearchResponse(
            results=[
                SearchResult(
                    title="noise item",
                    url="http://example.com/data.counts",
                    description="dictionary list",
                    source="google",
                )
            ],
            suggestions=[],
            provider="searxng",
            query="python asyncio",
        )

        google_mock = AsyncMock()
        with (
            patch.object(provider._searxng, "search", AsyncMock(return_value=searxng_response)),
            patch.object(provider._google, "search", google_mock),
        ):
            response = await provider.search("python asyncio", limit=3)

        assert response.provider == "searxng"
        assert response.results
        google_mock.assert_not_awaited()
