from web_mcp.tools.fetch_content import (
    FetchContentResult,
    fetch_content,
    TOOL_SCHEMA as FETCH_CONTENT_SCHEMA,
)
from web_mcp.tools.web_search import (
    WebSearchResult,
    web_search,
    TOOL_SCHEMA as WEB_SEARCH_SCHEMA,
)
from web_mcp.tools.suggestions import (
    SuggestionsResult,
    get_suggestions,
    TOOL_SCHEMA as GET_SUGGESTIONS_SCHEMA,
)

__all__ = [
    "FetchContentResult",
    "fetch_content",
    "FETCH_CONTENT_SCHEMA",
    "WebSearchResult",
    "web_search",
    "WEB_SEARCH_SCHEMA",
    "SuggestionsResult",
    "get_suggestions",
    "GET_SUGGESTIONS_SCHEMA",
]

ALL_TOOLS = [
    WEB_SEARCH_SCHEMA,
    FETCH_CONTENT_SCHEMA,
    GET_SUGGESTIONS_SCHEMA,
]

TOOL_HANDLERS = {
    "web_search": web_search,
    "fetch_content": fetch_content,
    "get_suggestions": get_suggestions,
}
