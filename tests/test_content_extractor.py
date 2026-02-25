from unittest.mock import patch

import pytest

from web_mcp.utils.content_extractor import ContentExtractor, ExtractedContent


class TestExtractedContent:
    def test_create_extracted_content(self):
        content = ExtractedContent(
            url="https://example.com",
            title="Test Title",
            content="Test content",
            description="Test description",
            author="Test Author",
            source="example.com",
            content_type="text/html",
            truncated=True,
        )
        assert content.url == "https://example.com"
        assert content.title == "Test Title"
        assert content.content == "Test content"
        assert content.truncated is True

    def test_extracted_content_defaults(self):
        content = ExtractedContent(
            url="https://example.com",
            title="Test",
            content="Content",
        )
        assert content.description == ""
        assert content.author == ""
        assert content.truncated is False
        assert content.error == ""

    def test_extracted_content_to_dict(self):
        content = ExtractedContent(
            url="https://example.com",
            title="Test Title",
            content="Test content",
            description="Description",
            truncated=True,
        )
        d = content.to_dict()
        assert d["url"] == "https://example.com"
        assert d["title"] == "Test Title"
        assert d["content"] == "Test content"
        assert d["truncated"] is True


class TestContentExtractor:
    def test_extract_domain(self):
        extractor = ContentExtractor()
        assert extractor._extract_domain("https://example.com/page") == "example.com"
        assert extractor._extract_domain("http://test.org") == "test.org"
        assert extractor._extract_domain("invalid") == ""

    def test_truncate_no_truncation_needed(self):
        extractor = ContentExtractor()
        content = "Short content"
        result, truncated = extractor._truncate(content, 100)
        assert result == content
        assert truncated is False

    def test_truncate_with_truncation(self):
        extractor = ContentExtractor()
        content = "This is a long piece of content that needs to be truncated"
        result, truncated = extractor._truncate(content, 20)
        assert len(result) <= 50  # Allow some buffer for truncation message
        assert truncated is True
        assert "[Content truncated...]" in result

    def test_truncate_preserves_word_boundary(self):
        extractor = ContentExtractor()
        content = "This is a sentence with words"
        result, truncated = extractor._truncate(content, 15)
        assert truncated is True
        assert not result.rstrip().endswith("sente")  # Should not cut mid-word

    @pytest.mark.asyncio
    async def test_extract_connection_error(self):
        extractor = ContentExtractor()

        with patch.object(extractor, "fetch", side_effect=Exception("Connection failed")):
            result = await extractor.extract("https://nonexistent.invalid")
            assert result.error != ""
            assert result.content == ""

    @pytest.mark.asyncio
    async def test_extract_successful(self):
        extractor = ContentExtractor()

        mock_html = "<html><head><title>Test</title></head><body><p>Content</p></body></html>"
        mock_meta = {"content_type": "text/html"}

        with patch.object(extractor, "fetch", return_value=(mock_html, mock_meta)):
            with patch.object(
                extractor, "_html_to_markdown", return_value=("Content", {"title": "Test"})
            ):
                result = await extractor.extract("https://example.com")
                assert result.error == ""
                assert result.source == "example.com"
