from web_mcp.search.base import VALID_CATEGORIES, SearchProvider, SearchResponse, SearchResult
from web_mcp.search.fallback import FallbackSearchProvider
from web_mcp.search.google import GoogleProvider
from web_mcp.search.provider_registry import close_search_provider, get_search_provider
from web_mcp.search.relevance import detect_query_intent, get_domain, rank_search_results
from web_mcp.search.searxng import SearxNGProvider

__all__ = [
    "VALID_CATEGORIES",
    "SearchProvider",
    "SearchResponse",
    "SearchResult",
    "SearxNGProvider",
    "GoogleProvider",
    "FallbackSearchProvider",
    "get_search_provider",
    "close_search_provider",
    "detect_query_intent",
    "get_domain",
    "rank_search_results",
]
