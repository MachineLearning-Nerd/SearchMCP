import pytest
from unittest.mock import patch, MagicMock

from web_mcp.search.google import GoogleProvider, USER_AGENTS
from web_mcp.search.base import SearchResponse


class TestGoogleProvider:
    def test_provider_name(self):
        provider = GoogleProvider()
        assert provider.name == "google"

    def test_is_available_default(self):
        provider = GoogleProvider()
        assert provider.is_available is True

    def test_get_headers_contains_user_agent(self):
        provider = GoogleProvider()
        headers = provider._get_headers()
        assert "User-Agent" in headers
        assert any(ua in headers["User-Agent"] for ua in USER_AGENTS)

    def test_parse_results_empty(self):
        provider = GoogleProvider()
        html = "<html><body></body></html>"
        results = provider._parse_results(html, 5)
        assert results == []

    def test_parse_results_with_data(self):
        provider = GoogleProvider()
        html = """
        <html>
            <body>
                <div class="g">
                    <h3>Test Title</h3>
                    <a href="https://example.com">Link</a>
                    <div class="VwiC3b">Test description</div>
                </div>
            </body>
        </html>
        """
        results = provider._parse_results(html, 5)
        assert len(results) == 1
        assert results[0].title == "Test Title"
        assert results[0].url == "https://example.com"
        assert results[0].description == "Test description"

    def test_parse_results_excludes_invalid_urls(self):
        provider = GoogleProvider()
        html = """
        <html>
            <body>
                <div class="g">
                    <h3>Test Title</h3>
                    <a href="/search?q=test">Link</a>
                </div>
            </body>
        </html>
        """
        results = provider._parse_results(html, 5)
        assert len(results) == 0

    def test_extract_result_no_title(self):
        provider = GoogleProvider()
        container = MagicMock()
        container.select_one.return_value = None
        result = provider._extract_result(container)
        assert result is None

    @pytest.mark.asyncio
    async def test_search_returns_response(self):
        provider = GoogleProvider()

        with patch.object(provider, "_scrape_google", return_value=[]):
            response = await provider.search("test query")
            assert isinstance(response, SearchResponse)
            assert response.provider == "google"
            assert response.query == "test query"

    @pytest.mark.asyncio
    async def test_get_suggestions_returns_empty(self):
        provider = GoogleProvider()
        suggestions = await provider.get_suggestions("test query")
        assert suggestions == []
