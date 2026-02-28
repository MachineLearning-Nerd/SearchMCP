#!/usr/bin/env python3
"""MCP stdio smoke test for Web MCP container."""

from __future__ import annotations

import argparse
import asyncio
import re
from collections.abc import Iterable

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import CallToolResult

REQUIRED_TOOLS = {"web_search", "fetch_content", "get_suggestions"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MCP smoke checks against containerized server")
    parser.add_argument(
        "--docker-command",
        default="docker",
        help="Container runtime command",
    )
    parser.add_argument(
        "--image",
        default="web-mcp:latest",
        help="Container image for MCP server",
    )
    parser.add_argument(
        "--query",
        default=None,
        help="Query for web_search (defaults to --suggest-query if provided)",
    )
    parser.add_argument(
        "--suggest-query",
        default=None,
        help="Query prefix for get_suggestions (defaults to --query if provided)",
    )
    parser.add_argument(
        "--content-url",
        default=None,
        help="URL for fetch_content (defaults to first URL found in web_search output)",
    )
    parser.add_argument("--limit", type=int, default=3, help="Result limit for web_search")
    parser.add_argument("--max-length", type=int, default=800, help="Max length for fetch_content")
    return parser.parse_args()


def resolve_queries(args: argparse.Namespace) -> None:
    default_search_query = "python asyncio"
    default_suggest_query = "python asyn"

    if args.query and not args.suggest_query:
        args.suggest_query = args.query
    elif args.suggest_query and not args.query:
        args.query = args.suggest_query
    elif not args.query and not args.suggest_query:
        args.query = default_search_query
        args.suggest_query = default_suggest_query


def shorten(value: str, limit: int) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."


def extract_text_blocks(result: CallToolResult) -> list[str]:
    blocks: list[str] = []
    for item in result.content:
        text = getattr(item, "text", None)
        if isinstance(text, str) and text.strip():
            blocks.append(text)
    return blocks


def extract_urls(text: str) -> list[str]:
    urls = re.findall(r"https?://[^\s)\]>]+", text)
    seen: set[str] = set()
    ordered: list[str] = []
    for url in urls:
        normalized = url.rstrip(".,;)")
        if normalized not in seen:
            seen.add(normalized)
            ordered.append(normalized)
    return ordered


def extract_cve_ids(text: str) -> list[str]:
    return re.findall(r"CVE-\d{4}-\d{4,}", text, flags=re.IGNORECASE)


def collect_content_url_candidates(
    explicit_url: str | None,
    search_query: str,
    search_output_text: str,
) -> list[str]:
    if explicit_url:
        return [explicit_url]

    skip_suffixes = (
        ".txt",
        ".csv",
        ".tsv",
        ".log",
        ".json",
        ".xml",
        ".counts",
        ".vocab",
    )

    preferred: list[str] = []
    fallback: list[str] = []

    for cve_id in extract_cve_ids(search_query):
        preferred.append(f"https://nvd.nist.gov/vuln/detail/{cve_id.upper()}")

    for url in extract_urls(search_output_text):
        lowered = url.lower()
        if lowered.endswith(skip_suffixes):
            fallback.append(url)
        else:
            preferred.append(url)

    candidates = preferred + fallback
    if not candidates:
        candidates.append("https://example.com")
    return candidates


def print_tool_result(name: str, result: CallToolResult, text_blocks: Iterable[str]) -> None:
    blocks = list(text_blocks)
    print(f"{name}: isError={result.isError} content_items={len(result.content)}")
    print(f"{name} output:")
    if not blocks:
        print("  (no text content)")
        return
    for idx, block in enumerate(blocks, start=1):
        preview = shorten(block, 1200)
        print(f"  --- block {idx} ---")
        for line in preview.splitlines():
            print(f"  {line}")


async def run_checks(args: argparse.Namespace) -> None:
    server_parameters = StdioServerParameters(
        command=args.docker_command,
        args=["run", "--rm", "-i", args.image],
    )

    print(f"Starting MCP server via: {args.docker_command} run --rm -i {args.image}")

    async with stdio_client(server_parameters) as streams:
        async with ClientSession(*streams) as session:
            init = await session.initialize()
            print(
                "Initialized MCP session:",
                f"server={init.serverInfo.name}",
                f"version={init.serverInfo.version}",
            )

            tools_result = await session.list_tools()
            available_tools = {tool.name for tool in tools_result.tools}
            print("Available tools:", ", ".join(sorted(available_tools)))

            missing = REQUIRED_TOOLS - available_tools
            if missing:
                raise RuntimeError(f"Missing expected tools: {', '.join(sorted(missing))}")

            web_result = await session.call_tool(
                "web_search",
                {
                    "query": args.query,
                    "limit": args.limit,
                },
            )
            web_text_blocks = extract_text_blocks(web_result)
            print_tool_result("web_search", web_result, web_text_blocks)
            if web_result.isError:
                raise RuntimeError("web_search returned error")

            suggestions_result = await session.call_tool(
                "get_suggestions",
                {
                    "query": args.suggest_query,
                },
            )
            suggestions_text_blocks = extract_text_blocks(suggestions_result)
            print_tool_result("get_suggestions", suggestions_result, suggestions_text_blocks)
            if suggestions_result.isError:
                raise RuntimeError("get_suggestions returned error")

            content_result: CallToolResult | None = None
            selected_url = ""
            search_text = "\n".join(web_text_blocks)
            candidates = collect_content_url_candidates(args.content_url, args.query, search_text)

            for candidate_url in candidates:
                selected_url = candidate_url
                candidate_result = await session.call_tool(
                    "fetch_content",
                    {
                        "url": candidate_url,
                        "max_length": args.max_length,
                    },
                )
                content_result = candidate_result
                if not candidate_result.isError:
                    break

            if content_result is None:
                raise RuntimeError("No content candidate URL available")

            print(f"fetch_content requested url: {selected_url}")
            content_text_blocks = extract_text_blocks(content_result)
            print_tool_result("fetch_content", content_result, content_text_blocks)
            if content_result.isError:
                raise RuntimeError("fetch_content returned error for all candidates")


def main() -> None:
    args = parse_args()
    resolve_queries(args)
    print(f"web_search query={args.query}")
    print(f"suggestions query={args.suggest_query}")
    asyncio.run(run_checks(args))


if __name__ == "__main__":
    main()
