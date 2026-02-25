#!/usr/bin/env python3
"""Manual smoke test for Web MCP tools."""

from __future__ import annotations

import argparse
import asyncio
import os
import re
from urllib.parse import urlparse

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run manual Web MCP tool checks")
    parser.add_argument(
        "--searxng-url",
        default=os.environ.get("SEARXNG_URL", "http://127.0.0.1:18080"),
        help="SearxNG base URL",
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
        help="URL for fetch_content (defaults to first web_search result)",
    )
    parser.add_argument("--limit", type=int, default=3, help="Result limit for web_search")
    parser.add_argument(
        "--max-length",
        type=int,
        default=800,
        help="Max length for fetch_content",
    )
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip SearxNG /config reachability check",
    )
    return parser.parse_args()


def preflight(searxng_url: str) -> None:
    config_url = f"{searxng_url.rstrip('/')}/config"
    try:
        response = httpx.get(config_url, timeout=5.0)
        response.raise_for_status()
        print(f"SearxNG check: OK ({response.status_code})")
    except Exception as exc:
        print(f"SearxNG check: FAILED ({exc})")


def shorten(value: str, limit: int) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."


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


def extract_cve_ids(text: str) -> list[str]:
    return re.findall(r"CVE-\d{4}-\d{4,}", text, flags=re.IGNORECASE)


def collect_content_url_candidates(
    explicit_url: str | None,
    search_query: str,
    search_results: list[dict[str, object]],
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

    cve_ids = extract_cve_ids(search_query)
    for cve_id in cve_ids:
        preferred.append(f"https://nvd.nist.gov/vuln/detail/{cve_id.upper()}")

    for item in search_results:
        url = str(item.get("url", "")).strip()
        if not url:
            continue

        parsed = urlparse(url)
        path = parsed.path.lower()
        if path.endswith(skip_suffixes):
            fallback.append(url)
            continue

        preferred.append(url)

    candidates = preferred + fallback
    if not candidates:
        candidates.append("http://example.com")
    return candidates


async def run_checks(args: argparse.Namespace) -> None:
    from web_mcp.tools.fetch_content import fetch_content
    from web_mcp.tools.suggestions import get_suggestions
    from web_mcp.tools.web_search import web_search

    search_result = await web_search(args.query, limit=args.limit)
    print(
        "web_search:",
        search_result.provider,
        search_result.total,
        "error=",
        search_result.error,
    )
    print("web_search output:")
    if search_result.results:
        for idx, item in enumerate(search_result.results, start=1):
            title = shorten(str(item.get("title", "")), 100)
            url = str(item.get("url", ""))
            description = shorten(str(item.get("description", "")), 180)
            print(f"  {idx}. {title}")
            print(f"     {url}")
            if description:
                print(f"     {description}")
    else:
        print("  (no results)")

    suggestions_result = await get_suggestions(args.suggest_query)
    print(
        "get_suggestions:",
        len(suggestions_result.suggestions),
        "error=",
        suggestions_result.error,
    )
    print("get_suggestions output:")
    if suggestions_result.suggestions:
        for idx, suggestion in enumerate(suggestions_result.suggestions, start=1):
            print(f"  {idx}. {suggestion}")
    else:
        print("  (no suggestions)")

    content_result = None
    selected_url = ""
    content_candidates = collect_content_url_candidates(
        args.content_url,
        args.query,
        search_result.results,
    )
    for candidate_url in content_candidates:
        selected_url = candidate_url
        candidate_result = await fetch_content(candidate_url, max_length=args.max_length)
        content_result = candidate_result
        if not candidate_result.error:
            break

    if content_result is None:
        raise RuntimeError("No content candidate URL available")

    print(
        "fetch_content:",
        bool(content_result.title),
        len(content_result.content),
        "error=",
        content_result.error,
    )
    print("fetch_content output:")
    print(f"  requested url: {selected_url}")
    if content_result.error:
        print(f"  error: {content_result.error}")
        return

    print(f"  title: {content_result.title or '(empty)'}")
    print(f"  source: {content_result.source or '(empty)'}")
    print(f"  url: {content_result.url}")
    print(f"  content preview: {shorten(content_result.content, 500)}")


def main() -> None:
    args = parse_args()
    resolve_queries(args)
    os.environ["SEARXNG_URL"] = args.searxng_url

    from web_mcp.config import settings

    print(f"SEARXNG_URL={settings.SEARXNG_URL}")
    print(f"web_search query={args.query}")
    print(f"suggestions query={args.suggest_query}")
    if not args.skip_preflight:
        preflight(settings.SEARXNG_URL)
    asyncio.run(run_checks(args))


if __name__ == "__main__":
    main()
