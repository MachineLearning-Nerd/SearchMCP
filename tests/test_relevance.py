from web_mcp.search.base import SearchResult
from web_mcp.search.relevance import (
    QUERY_INTENT_GENERAL,
    QUERY_INTENT_SECURITY,
    detect_query_intent,
    is_low_quality,
    rank_search_results,
    select_engines_for_query,
)


class TestQueryIntent:
    def test_detect_query_intent_security_from_cve(self):
        query = "Should we take waiver for CVE-2026-26007?"
        assert detect_query_intent(query) == QUERY_INTENT_SECURITY

    def test_detect_query_intent_general(self):
        assert detect_query_intent("python asyncio tutorial") == QUERY_INTENT_GENERAL


class TestEngineSelection:
    def test_select_engines_for_security_query(self):
        engines = select_engines_for_query(
            query="CVE-2026-26007 details",
            mode="auto",
            security_engines_raw="brave,bing,duckduckgo",
            general_engines_raw="",
        )
        assert engines == ["brave", "bing", "duckduckgo"]

    def test_select_engines_off_mode(self):
        engines = select_engines_for_query(
            query="CVE-2026-26007 details",
            mode="off",
            security_engines_raw="brave,bing,duckduckgo",
            general_engines_raw="wikipedia",
        )
        assert engines is None


class TestRanking:
    def test_rank_search_results_prioritizes_security_authority(self):
        query = "CVE-2026-26007 waiver justification"
        results = [
            SearchResult(
                title="word frequencies",
                url="http://example.com/data.counts",
                description="dictionary list",
                source="google",
            ),
            SearchResult(
                title="NVD - CVE-2026-26007",
                url="https://nvd.nist.gov/vuln/detail/CVE-2026-26007",
                description="Official CVE detail",
                source="brave",
            ),
            SearchResult(
                title="NVD duplicate",
                url="https://nvd.nist.gov/vuln/detail/CVE-2026-26007#fragment",
                description="duplicate item",
                source="bing",
            ),
        ]

        outcome = rank_search_results(query=query, results=results, limit=5)

        assert outcome.results[0].url.startswith("https://nvd.nist.gov/vuln/detail/CVE-2026-26007")
        assert len(outcome.results) == 2
        assert outcome.quality_score > 2.5

    def test_is_low_quality_for_noise_only_results(self):
        query = "CVE-2026-26007 waiver justification"
        results = [
            SearchResult(
                title="word frequencies",
                url="http://example.com/data.counts",
                description="dictionary list",
                source="google",
            )
        ]

        outcome = rank_search_results(query=query, results=results, limit=5)
        assert is_low_quality(outcome, min_quality_score=2.5)
