from unittest.mock import AsyncMock, patch

import pytest

from web_mcp.search.base import SearchResponse, SearchResult
from web_mcp.tools.web_search import (
    TOOL_SCHEMA,
    WebSearchResult,
    web_search,
)


class TestWebSearchResult:
    def test_create_result(self):
        result = WebSearchResult(
            query="test query",
            results=[
                {"title": "Test 1", "url": "https://example.com/1"},
                {"title": "Test 2", "url": "https://example.com/2"},
            ],
            suggestions=["suggestion1"],
            provider="searxng",
            total=2,
        )
        assert result.query == "test query"
        assert len(result.results) == 2
        assert result.total == 2

    def test_to_dict(self):
        result = WebSearchResult(
            query="test",
            results=[{"title": "Test", "url": "https://example.com"}],
            suggestions=[],
            provider="google",
            total=1,
        )
        d = result.to_dict()
        assert d["query"] == "test"
        assert d["provider"] == "google"
        assert d["total"] == 1
        assert d["error"] == ""

    def test_to_dict_with_error(self):
        result = WebSearchResult(
            query="test",
            results=[],
            suggestions=[],
            provider="error",
            total=0,
            error="Search failed",
        )
        d = result.to_dict()
        assert d["error"] == "Search failed"

    def test_to_mcp_response_with_results(self):
        result = WebSearchResult(
            query="test query",
            results=[
                {"title": "Test Title", "url": "https://example.com", "description": "Test desc"}
            ],
            suggestions=["related search"],
            provider="searxng",
            total=1,
        )
        response = result.to_mcp_response()
        assert len(response) == 1
        assert response[0]["type"] == "text"
        assert "Test Title" in response[0]["text"]
        assert "https://example.com" in response[0]["text"]
        assert "related search" in response[0]["text"]

    def test_to_mcp_response_empty(self):
        result = WebSearchResult(
            query="test",
            results=[],
            suggestions=[],
            provider="none",
            total=0,
        )
        response = result.to_mcp_response()
        assert "No results found" in response[0]["text"]


class TestWebSearch:
    @pytest.mark.asyncio
    async def test_web_search_success(self):
        mock_response = SearchResponse(
            results=[SearchResult(title="Test", url="https://example.com", description="Desc")],
            suggestions=["related"],
            provider="searxng",
            query="test",
        )

        with patch("web_mcp.tools.web_search._get_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.search.return_value = mock_response
            mock_get_provider.return_value = mock_provider

            result = await web_search("test query")
            assert result.error == ""
            assert result.total >= 0

    @pytest.mark.asyncio
    async def test_web_search_with_category(self):
        mock_response = SearchResponse(
            results=[],
            suggestions=[],
            provider="searxng",
            query="test",
        )

        with patch("web_mcp.tools.web_search._get_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.search.return_value = mock_response
            mock_get_provider.return_value = mock_provider

            result = await web_search("test", category="news")
            assert isinstance(result, WebSearchResult)

    @pytest.mark.asyncio
    async def test_web_search_error_handling(self):
        with patch("web_mcp.tools.web_search._get_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.search.side_effect = Exception("Search failed")
            mock_get_provider.return_value = mock_provider

            result = await web_search("test")
            assert result.provider == "error"
            assert result.results == []
            assert result.error == "Search failed"


class TestToolSchema:
    def test_tool_schema_has_required_fields(self):
        assert TOOL_SCHEMA["name"] == "web_search"
        assert "query" in TOOL_SCHEMA["inputSchema"]["properties"]
        assert "category" in TOOL_SCHEMA["inputSchema"]["properties"]
        assert "limit" in TOOL_SCHEMA["inputSchema"]["properties"]
        assert "query" in TOOL_SCHEMA["inputSchema"]["required"]

    def test_category_enum(self):
        category_prop = TOOL_SCHEMA["inputSchema"]["properties"]["category"]
        assert "enum" in category_prop
        assert "general" in category_prop["enum"]
        assert "news" in category_prop["enum"]
