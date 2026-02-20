import pytest
from unittest.mock import AsyncMock, patch

from web_mcp.tools.fetch_content import FetchContentResult, fetch_content, TOOL_SCHEMA


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
        from web_mcp.utils.content_extractor import ExtractedContent

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

        with patch("web_mcp.tools.fetch_content.ContentExtractor") as MockExtractor:
            instance = MockExtractor.return_value
            instance.extract = AsyncMock(return_value=mock_extracted)

            result = await fetch_content("https://example.com")
            assert result.error == ""
            assert result.title == "Test Title"

    @pytest.mark.asyncio
    async def test_fetch_content_error(self):
        from web_mcp.utils.content_extractor import ExtractedContent

        mock_extracted = ExtractedContent(
            url="https://example.com",
            title="",
            content="",
            error="Failed to extract",
        )

        with patch("web_mcp.tools.fetch_content.ContentExtractor") as MockExtractor:
            instance = MockExtractor.return_value
            instance.extract = AsyncMock(return_value=mock_extracted)

            result = await fetch_content("https://example.com")
            assert result.error == "Failed to extract"


class TestToolSchema:
    def test_tool_schema_has_required_fields(self):
        assert TOOL_SCHEMA["name"] == "fetch_content"
        assert "url" in TOOL_SCHEMA["inputSchema"]["properties"]
        assert "max_length" in TOOL_SCHEMA["inputSchema"]["properties"]
        assert "url" in TOOL_SCHEMA["inputSchema"]["required"]
