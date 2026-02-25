
from web_mcp.server import create_server


class TestServerCreation:
    def test_create_server(self):
        server = create_server()
        assert server is not None
        assert server.name == "web-mcp"


class TestToolHandlers:
    def test_web_search_handler_registered(self):
        from web_mcp.tools import TOOL_HANDLERS

        assert "web_search" in TOOL_HANDLERS
        assert callable(TOOL_HANDLERS["web_search"])

    def test_fetch_content_handler_registered(self):
        from web_mcp.tools import TOOL_HANDLERS

        assert "fetch_content" in TOOL_HANDLERS
        assert callable(TOOL_HANDLERS["fetch_content"])

    def test_get_suggestions_handler_registered(self):
        from web_mcp.tools import TOOL_HANDLERS

        assert "get_suggestions" in TOOL_HANDLERS
        assert callable(TOOL_HANDLERS["get_suggestions"])


class TestAllTools:
    def test_all_tools_count(self):
        from web_mcp.tools import ALL_TOOLS

        assert len(ALL_TOOLS) == 3

    def test_all_tools_have_required_fields(self):
        from web_mcp.tools import ALL_TOOLS

        for tool in ALL_TOOLS:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert "properties" in tool["inputSchema"]
            assert "required" in tool["inputSchema"]

    def test_tool_names_match_handlers(self):
        from web_mcp.tools import ALL_TOOLS, TOOL_HANDLERS

        tool_names = {tool["name"] for tool in ALL_TOOLS}
        handler_names = set(TOOL_HANDLERS.keys())
        assert tool_names == handler_names

    def test_web_search_schema(self):
        from web_mcp.tools import WEB_SEARCH_SCHEMA

        assert WEB_SEARCH_SCHEMA["name"] == "web_search"
        assert "query" in WEB_SEARCH_SCHEMA["inputSchema"]["required"]

    def test_fetch_content_schema(self):
        from web_mcp.tools import FETCH_CONTENT_SCHEMA

        assert FETCH_CONTENT_SCHEMA["name"] == "fetch_content"
        assert "url" in FETCH_CONTENT_SCHEMA["inputSchema"]["required"]

    def test_get_suggestions_schema(self):
        from web_mcp.tools import GET_SUGGESTIONS_SCHEMA

        assert GET_SUGGESTIONS_SCHEMA["name"] == "get_suggestions"
        assert "query" in GET_SUGGESTIONS_SCHEMA["inputSchema"]["required"]
