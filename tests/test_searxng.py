from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from web_mcp.search.searxng import SearxNGProvider


class TestSearxNGProvider:
    def test_provider_name(self):
        provider = SearxNGProvider(base_url="http://localhost:8080")
        assert provider.name == "searxng"

    def test_is_available_with_url(self):
        provider = SearxNGProvider(base_url="http://localhost:8080")
        assert provider.is_available is True

    def test_is_available_without_url(self):
        provider = SearxNGProvider(base_url="")
        assert provider.is_available is False

    def test_validate_category_valid(self):
        provider = SearxNGProvider(base_url="http://localhost:8080")
        assert provider._validate_category("general") == "general"
        assert provider._validate_category("images") == "images"
        assert provider._validate_category("news") == "news"

    def test_validate_category_invalid(self):
        provider = SearxNGProvider(base_url="http://localhost:8080")
        assert provider._validate_category("invalid") == "general"

    def test_parse_result(self):
        provider = SearxNGProvider(base_url="http://localhost:8080")
        item = {
            "title": "Test Title",
            "url": "https://example.com",
            "content": "Test content",
            "engine": "google",
        }
        result = provider._parse_result(item)
        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.description == "Test content"
        assert result.source == "google"

    def test_parse_response(self):
        provider = SearxNGProvider(base_url="http://localhost:8080")
        data = {
            "results": [
                {"title": "Test 1", "url": "https://example.com/1", "content": "Content 1"},
                {"title": "Test 2", "url": "https://example.com/2", "content": "Content 2"},
            ],
            "suggestions": ["suggestion1", "suggestion2"],
        }
        response = provider._parse_response(data, "test query")
        assert len(response.results) == 2
        assert len(response.suggestions) == 2
        assert response.query == "test query"
        assert response.provider == "searxng"

    def test_resolve_candidate_limit(self):
        provider = SearxNGProvider(base_url="http://localhost:8080")
        candidate_limit = provider._resolve_candidate_limit(5)
        assert candidate_limit >= 5

    @pytest.mark.asyncio
    async def test_search_connection_error(self):
        provider = SearxNGProvider(base_url="http://nonexistent:8080")

        with patch("httpx.AsyncClient.get", side_effect=Exception("Connection error")):
            response = await provider.search("test query")
            assert response.results == []
            assert response.provider == "searxng"

    @pytest.mark.asyncio
    async def test_search_applies_engine_profile_for_security_query(self):
        provider = SearxNGProvider(base_url="http://localhost:8080")

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"results": [], "suggestions": []}

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch.object(provider, "_get_client", return_value=mock_client):
            await provider.search("CVE-2026-26007 details", limit=5)

        _, kwargs = mock_client.get.call_args
        params = kwargs["params"]
        assert "engines" in params
        assert "brave" in params["engines"]

    @pytest.mark.asyncio
    async def test_get_suggestions_error(self):
        provider = SearxNGProvider(base_url="http://nonexistent:8080")

        with patch("httpx.AsyncClient.get", side_effect=Exception("Connection error")):
            suggestions = await provider.get_suggestions("test query")
            assert suggestions == []

    @pytest.mark.asyncio
    async def test_close(self):
        provider = SearxNGProvider(base_url="http://localhost:8080")
        await provider.close()
