from unittest.mock import AsyncMock, patch

import pytest

from web_mcp.tools.suggestions import (
    TOOL_SCHEMA,
    SuggestionsResult,
    get_suggestions,
)


class TestSuggestionsResult:
    def test_create_result(self):
        result = SuggestionsResult(
            query="test query",
            suggestions=["suggestion1", "suggestion2"],
        )
        assert result.query == "test query"
        assert len(result.suggestions) == 2

    def test_to_dict(self):
        result = SuggestionsResult(
            query="test",
            suggestions=["suggestion1"],
        )
        d = result.to_dict()
        assert d["query"] == "test"
        assert d["suggestions"] == ["suggestion1"]
        assert d["error"] == ""

    def test_to_dict_with_error(self):
        result = SuggestionsResult(
            query="test",
            suggestions=[],
            error="Failed to get suggestions",
        )
        d = result.to_dict()
        assert d["error"] == "Failed to get suggestions"

    def test_to_mcp_response_with_error(self):
        result = SuggestionsResult(
            query="test",
            suggestions=[],
            error="Connection failed",
        )
        response = result.to_mcp_response()
        assert "Error" in response[0]["text"]
        assert "Connection failed" in response[0]["text"]

    def test_to_mcp_response_with_suggestions(self):
        result = SuggestionsResult(
            query="test query",
            suggestions=["suggestion1", "suggestion2"],
        )
        response = result.to_mcp_response()
        assert len(response) == 1
        assert response[0]["type"] == "text"
        assert "suggestion1" in response[0]["text"]
        assert "suggestion2" in response[0]["text"]

    def test_to_mcp_response_empty(self):
        result = SuggestionsResult(
            query="test",
            suggestions=[],
        )
        response = result.to_mcp_response()
        assert "No suggestions available" in response[0]["text"]


class TestGetSuggestions:
    @pytest.mark.asyncio
    async def test_get_suggestions_success(self):
        mock_provider = AsyncMock()
        mock_provider.get_suggestions.return_value = ["suggestion1", "suggestion2"]

        result = await get_suggestions("test query", provider=mock_provider)
        assert len(result.suggestions) == 2
        assert result.query == "test query"

    @pytest.mark.asyncio
    async def test_get_suggestions_empty(self):
        mock_provider = AsyncMock()
        mock_provider.get_suggestions.return_value = []

        result = await get_suggestions("test query", provider=mock_provider)
        assert result.suggestions == []

    @pytest.mark.asyncio
    async def test_get_suggestions_error(self):
        mock_provider = AsyncMock()
        mock_provider.get_suggestions.side_effect = Exception("Failed")

        result = await get_suggestions("test query", provider=mock_provider)
        assert result.suggestions == []
        assert result.error == "Failed"

    @pytest.mark.asyncio
    async def test_get_suggestions_uses_singleton(self):
        with patch("web_mcp.tools.suggestions.get_search_provider") as mock_get_provider:
            mock_instance = AsyncMock()
            mock_instance.get_suggestions.return_value = ["suggestion"]
            mock_get_provider.return_value = mock_instance

            result = await get_suggestions("test")
            assert isinstance(result, SuggestionsResult)
            assert result.suggestions == ["suggestion"]

    @pytest.mark.asyncio
    async def test_get_suggestions_rejects_empty_query(self):
        result = await get_suggestions("   ")
        assert result.suggestions == []
        assert result.error == "query must be a non-empty string"


class TestToolSchema:
    def test_tool_schema_has_required_fields(self):
        assert TOOL_SCHEMA["name"] == "get_suggestions"
        assert "query" in TOOL_SCHEMA["inputSchema"]["properties"]
        assert "query" in TOOL_SCHEMA["inputSchema"]["required"]
