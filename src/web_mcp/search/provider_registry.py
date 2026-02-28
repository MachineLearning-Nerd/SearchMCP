from web_mcp.search.fallback import FallbackSearchProvider

_search_provider: FallbackSearchProvider | None = None


def get_search_provider() -> FallbackSearchProvider:
    global _search_provider
    if _search_provider is None:
        _search_provider = FallbackSearchProvider()
    return _search_provider


async def close_search_provider() -> None:
    global _search_provider
    if _search_provider is None:
        return
    await _search_provider.close()
    _search_provider = None
