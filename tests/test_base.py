
from web_mcp.search.base import SearchResponse, SearchResult


class TestSearchResult:
    def test_create_search_result(self):
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            description="Test description",
            source="test",
        )
        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.description == "Test description"
        assert result.source == "test"

    def test_search_result_defaults(self):
        result = SearchResult(title="Test", url="https://example.com")
        assert result.description == ""
        assert result.source == ""

    def test_search_result_to_dict(self):
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            description="Test description",
            source="test",
        )
        d = result.to_dict()
        assert d["title"] == "Test Title"
        assert d["url"] == "https://example.com"
        assert d["description"] == "Test description"
        assert d["source"] == "test"


class TestSearchResponse:
    def test_create_search_response(self):
        results = [
            SearchResult(title="Test 1", url="https://example.com/1"),
            SearchResult(title="Test 2", url="https://example.com/2"),
        ]
        response = SearchResponse(
            results=results,
            suggestions=["suggestion1", "suggestion2"],
            provider="test",
            query="test query",
        )
        assert len(response.results) == 2
        assert len(response.suggestions) == 2
        assert response.provider == "test"
        assert response.query == "test query"
        assert response.total == 2

    def test_search_response_defaults(self):
        response = SearchResponse(
            results=[],
            provider="test",
            query="test",
        )
        assert response.suggestions == []
        assert response.total == 0

    def test_search_response_total_is_property(self):
        results = [
            SearchResult(title="Test 1", url="https://example.com/1"),
        ]
        response = SearchResponse(
            results=results,
            provider="test",
            query="test",
        )
        assert response.total == 1

        response.results.append(SearchResult(title="Test 2", url="https://example.com/2"))
        assert response.total == 2

    def test_search_response_to_dict(self):
        results = [
            SearchResult(title="Test 1", url="https://example.com/1"),
        ]
        response = SearchResponse(
            results=results,
            suggestions=["suggestion1"],
            provider="test",
            query="test query",
        )
        d = response.to_dict()
        assert d["provider"] == "test"
        assert d["query"] == "test query"
        assert d["total"] == 1
        assert len(d["results"]) == 1
        assert d["suggestions"] == ["suggestion1"]
