from unittest.mock import AsyncMock, patch

import pytest

from web_mcp.tools.fetch_content import (
    MAX_CONTENT_LENGTH,
    MIN_CONTENT_LENGTH,
    TOOL_SCHEMA,
    FetchContentResult,
    fetch_content,
)


class TestFetchContentResult:
    def test_create_result(self):
        result = FetchContentResult(
            url="https://example.com",
            title="Test Title",
            content="Test content",
            description="Description",
            author="Author",
            source="example.com",
            truncated=True,
        )
        assert result.url == "https://example.com"
        assert result.truncated is True

    def test_to_dict(self):
        result = FetchContentResult(
            url="https://example.com",
            title="Test",
            content="Content",
        )
        d = result.to_dict()
        assert d["url"] == "https://example.com"
        assert d["title"] == "Test"
        assert d["truncated"] is False

    def test_to_mcp_response_success(self):
        result = FetchContentResult(
            url="https://example.com",
            title="Test Title",
            content="Test content",
            source="example.com",
        )
        response = result.to_mcp_response()
        assert len(response) == 1
        assert response[0]["type"] == "text"
        assert "Test Title" in response[0]["text"]
        assert "Test content" in response[0]["text"]

    def test_to_mcp_response_error(self):
        result = FetchContentResult(
            url="https://example.com",
            title="",
            content="",
            error="Connection failed",
        )
        response = result.to_mcp_response()
        assert "Error" in response[0]["text"]
        assert "Connection failed" in response[0]["text"]

    def test_to_mcp_response_with_truncation(self):
        result = FetchContentResult(
            url="https://example.com",
            title="Test",
            content="Content",
            truncated=True,
        )
        response = result.to_mcp_response()
        assert "truncated" in response[0]["text"].lower()


class TestFetchContent:
    @pytest.mark.asyncio
    async def test_fetch_content_success(self):
        from web_mcp.utils.content_extractor import ContentExtractor, ExtractedContent

        mock_extracted = ExtractedContent(
            url="https://example.com",
            title="Test Title",
            content="Test content",
            description="Description",
            author="Author",
            source="example.com",
            content_type="text/html",
            truncated=False,
        )

        extractor = ContentExtractor()
        with patch.object(extractor, "extract", new=AsyncMock(return_value=mock_extracted)):
            with patch("web_mcp.tools.fetch_content._content_extractor", extractor):
                result = await fetch_content("https://example.com")
                assert result.error == ""
                assert result.title == "Test Title"

    @pytest.mark.asyncio
    async def test_fetch_content_error(self):
        from web_mcp.utils.content_extractor import ContentExtractor, ExtractedContent

        mock_extracted = ExtractedContent(
            url="https://example.com",
            title="",
            content="",
            error="Failed to extract",
        )

        extractor = ContentExtractor()
        with patch.object(extractor, "extract", new=AsyncMock(return_value=mock_extracted)):
            with patch("web_mcp.tools.fetch_content._content_extractor", extractor):
                result = await fetch_content("https://example.com")
                assert result.error == "Failed to extract"

    @pytest.mark.asyncio
    async def test_fetch_content_rejects_empty_url(self):
        result = await fetch_content("   ")
        assert result.error == "url must be a non-empty string"

    @pytest.mark.asyncio
    async def test_fetch_content_rejects_non_integer_max_length(self):
        result = await fetch_content("https://example.com", max_length=1000.5)
        assert "max_length must be an integer" in result.error


class TestToolSchema:
    def test_tool_schema_has_required_fields(self):
        assert TOOL_SCHEMA["name"] == "fetch_content"
        assert "url" in TOOL_SCHEMA["inputSchema"]["properties"]
        assert "max_length" in TOOL_SCHEMA["inputSchema"]["properties"]
        assert "url" in TOOL_SCHEMA["inputSchema"]["required"]

    def test_max_length_schema_is_integer_with_bounds(self):
        max_length_prop = TOOL_SCHEMA["inputSchema"]["properties"]["max_length"]
        assert max_length_prop["type"] == "integer"
        assert max_length_prop["minimum"] == MIN_CONTENT_LENGTH
        assert max_length_prop["maximum"] == MAX_CONTENT_LENGTH
