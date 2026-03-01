from unittest.mock import AsyncMock, patch

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
        from web_mcp.search.relevance import get_domain

        assert get_domain("https://example.com/page") == "example.com"
        assert get_domain("http://test.org") == "test.org"
        assert get_domain("invalid") == ""

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
        extractor = ContentExtractor(allow_private_network=True)

        with patch.object(extractor, "fetch", side_effect=Exception("Connection failed")):
            result = await extractor.extract("https://nonexistent.invalid")
            assert result.error != ""
            assert result.content == ""

    @pytest.mark.asyncio
    async def test_extract_successful(self):
        extractor = ContentExtractor(allow_private_network=True)

        mock_html = "<html><head><title>Test</title></head><body><p>Content</p></body></html>"
        mock_meta = {"content_type": "text/html"}

        with patch.object(extractor, "fetch", return_value=(mock_html, mock_meta)):
            with patch.object(
                extractor, "_html_to_markdown", return_value=("Content", {"title": "Test"})
            ):
                result = await extractor.extract("https://example.com")
                assert result.error == ""
                assert result.source == "example.com"

    @pytest.mark.asyncio
    async def test_validate_target_blocks_non_http_scheme(self):
        extractor = ContentExtractor(allow_private_network=False)
        with pytest.raises(ValueError, match="Only http and https URLs are allowed"):
            await extractor._validate_target("file:///tmp/test.txt")

    @pytest.mark.asyncio
    async def test_validate_target_blocks_localhost(self):
        extractor = ContentExtractor(allow_private_network=False)
        with pytest.raises(ValueError, match="local network addresses"):
            await extractor._validate_target("http://localhost/test")

    @pytest.mark.asyncio
    async def test_validate_target_blocks_private_ip_literal(self):
        extractor = ContentExtractor(allow_private_network=False)
        with pytest.raises(ValueError, match="private network addresses"):
            await extractor._validate_target("http://10.0.0.5/internal")

    @pytest.mark.asyncio
    async def test_validate_target_blocks_private_dns_resolution(self):
        extractor = ContentExtractor(allow_private_network=False)
        with patch.object(extractor, "_resolve_host_ips", AsyncMock(return_value={"127.0.0.1"})):
            with pytest.raises(ValueError, match="private network addresses"):
                await extractor._validate_target("http://example.com/test")

    @pytest.mark.asyncio
    async def test_validate_target_allows_public_dns_resolution(self):
        extractor = ContentExtractor(allow_private_network=False)
        with patch.object(
            extractor,
            "_resolve_host_ips",
            AsyncMock(return_value={"93.184.216.34"}),
        ):
            await extractor._validate_target("https://example.com")

    @pytest.mark.asyncio
    async def test_validate_target_allows_private_when_override_enabled(self):
        extractor = ContentExtractor(allow_private_network=True)
        await extractor._validate_target("http://localhost/test")

    @pytest.mark.asyncio
    async def test_extract_blocks_private_network_urls(self):
        extractor = ContentExtractor(allow_private_network=False)
        with patch.object(extractor, "fetch", AsyncMock()) as fetch_mock:
            result = await extractor.extract("http://localhost/internal")
            assert "Blocked URL target" in result.error
            fetch_mock.assert_not_awaited()
