from web_mcp.search.fallback import FallbackSearchProvider

# Singleton pattern: we reuse one provider instance across all requests so that
# its internal HTTP client connections and rate limiter state are shared.
# Use get_search_provider() instead of creating FallbackSearchProvider() directly.
_search_provider: FallbackSearchProvider | None = None


def get_search_provider() -> FallbackSearchProvider:
    """Return the shared search provider, creating it on first call (lazy init)."""
    global _search_provider
    if _search_provider is None:
        _search_provider = FallbackSearchProvider()
    return _search_provider


async def close_search_provider() -> None:
    """Shut down the shared provider and release its HTTP connections."""
    global _search_provider
    if _search_provider is None:
        return
    await _search_provider.close()
    _search_provider = None
