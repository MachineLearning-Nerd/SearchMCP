from web_mcp.search.base import SearchProvider, SearchResponse, SearchResult
from web_mcp.search.fallback import FallbackSearchProvider
from web_mcp.search.google import GoogleProvider
from web_mcp.search.relevance import detect_query_intent, rank_search_results
from web_mcp.search.searxng import SearxNGProvider

__all__ = [
    "SearchProvider",
    "SearchResponse",
    "SearchResult",
    "SearxNGProvider",
    "GoogleProvider",
    "FallbackSearchProvider",
    "detect_query_intent",
    "rank_search_results",
]
