import argparse
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from mcp.types import CallToolResult, TextContent


@pytest.fixture(scope="module")
def smoke_module() -> ModuleType:
    script_path = Path(__file__).resolve().parents[1] / "test.py"
    spec = importlib.util.spec_from_file_location("smoke_test_script", script_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resolve_queries_defaults(smoke_module: ModuleType) -> None:
    args = argparse.Namespace(query=None, suggest_query=None)
    smoke_module.resolve_queries(args)

    assert args.query == smoke_module.DEFAULT_SEARCH_QUERY
    assert args.suggest_query == smoke_module.DEFAULT_SUGGEST_QUERY


def test_resolve_queries_reuses_query(smoke_module: ModuleType) -> None:
    args = argparse.Namespace(query="security query", suggest_query=None)
    smoke_module.resolve_queries(args)

    assert args.query == "security query"
    assert args.suggest_query == "security query"


def test_resolve_queries_reuses_suggest_query(smoke_module: ModuleType) -> None:
    args = argparse.Namespace(query=None, suggest_query="partial query")
    smoke_module.resolve_queries(args)

    assert args.query == "partial query"
    assert args.suggest_query == "partial query"


def test_first_url_from_blocks_returns_first_url(smoke_module: ModuleType) -> None:
    blocks = [
        "No url here",
        "Top result: https://example.com/path, and more text",
        "https://second.example.com",
    ]
    url = smoke_module.first_url_from_blocks(blocks)

    assert url == "https://example.com/path"


def test_first_url_from_blocks_returns_none_when_missing(smoke_module: ModuleType) -> None:
    assert smoke_module.first_url_from_blocks(["no links", "still none"]) is None


def test_content_url_candidates_prefers_explicit_url(smoke_module: ModuleType) -> None:
    candidates = smoke_module.content_url_candidates(
        "https://custom.example",
        ["https://ignored.example"],
    )
    assert candidates == ["https://custom.example"]


def test_content_url_candidates_includes_fallback(smoke_module: ModuleType) -> None:
    candidates = smoke_module.content_url_candidates(
        None,
        ["Primary https://primary.example/path"],
    )
    assert candidates == ["https://primary.example/path", smoke_module.FALLBACK_CONTENT_URL]


def test_content_url_candidates_uses_fallback_when_missing(smoke_module: ModuleType) -> None:
    candidates = smoke_module.content_url_candidates(None, ["no link here"])
    assert candidates == [smoke_module.FALLBACK_CONTENT_URL]


def test_extract_text_blocks_filters_blank_text(smoke_module: ModuleType) -> None:
    result = CallToolResult(
        content=[
            TextContent(type="text", text="  "),
            TextContent(type="text", text="real text"),
        ],
        isError=False,
    )

    blocks = smoke_module.extract_text_blocks(result)
    assert blocks == ["real text"]
