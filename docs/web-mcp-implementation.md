# Web Search MCP Server - Implementation Plan

## Overview

A dedicated web search MCP server that combines **SearxNG** (privacy-focused metasearch) with **Google scraping fallback** in a single Docker container. No API keys required.

## Current Delivery Status (MVP)

- Core MCP functionality is implemented and validated (`web_search`, `fetch_content`, `get_suggestions`)
- Primary/fallback search flow is implemented (SearxNG first, Google fallback)
- Docker image builds and starts both SearxNG + MCP processes
- stdio is the active MCP transport for this release
- Deferred post-MVP items: SSE transport, formal performance report, formal security review

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Docker Container                        │
│  ┌─────────────────┐      ┌─────────────────────────┐  │
│  │   Supervisord   │──────│   Process Manager        │  │
│  └────────┬────────┘      └───────────┬─────────────┘  │
│           │                           │                 │
│           ▼                           ▼                 │
│  ┌─────────────────┐      ┌─────────────────────────┐  │
│  │    SearxNG      │◄────►│     Web MCP Server      │  │
│  │  (Port 8080)    │      │   (stdio/SSE transport) │  │
│  └─────────────────┘      └───────────┬─────────────┘  │
│                                       │                 │
│                                       ▼                 │
│                          ┌─────────────────────────┐   │
│                          │   Google Scraping       │   │
│                          │   (Fallback Provider)   │   │
│                          └─────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| MCP Server | Python 3.11+ with `mcp` SDK |
| HTTP Client | `httpx` (async) |
| HTML Parsing | `beautifulsoup4` + `lxml` |
| Content Extraction | `trafilatura` |
| Metasearch Engine | SearxNG |
| Process Manager | Supervisord |
| Containerization | Docker (multi-stage) |

---

## Tools Provided

| Tool | Description | Parameters |
|------|-------------|------------|
| `web_search` | Search the web | `query`, `category`, `limit` |
| `fetch_content` | Extract markdown from URLs | `url`, `max_length` |
| `get_suggestions` | Get query suggestions | `query` |

---

## Search Flow

```
┌─────────────┐
│ User Query  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Try SearxNG    │
│  (localhost)    │
└────┬───────┬────┘
     │       │
  OK │       │ Error/Timeout
     │       │
     ▼       ▼
┌────────┐  ┌─────────────────┐
│ Return │  │ Google Scraping │
│ Results│  │    Fallback     │
└────────┘  └────────┬────────┘
                     │
                     ▼
               ┌────────────┐
               │   Return   │
               │   Results  │
               └────────────┘
```

---

## Project Structure

```
SearchMCP/
├── src/
│   └── web_mcp/
│       ├── __init__.py
│       ├── server.py              # MCP server entry point
│       ├── config.py              # Configuration management
│       ├── search/
│       │   ├── __init__.py
│       │   ├── base.py            # Abstract SearchProvider class
│       │   ├── searxng.py         # SearxNG implementation
│       │   └── google.py          # Google scraping implementation
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── web_search.py      # web_search tool
│       │   ├── fetch_content.py   # fetch_content tool
│       │   └── suggestions.py     # get_suggestions tool
│       └── utils/
│           ├── __init__.py
│           ├── content_extractor.py  # HTML to markdown
│           └── rate_limiter.py       # Request rate limiting
├── docker/
│   ├── searxng/
│   │   └── settings.yml           # SearxNG configuration
│   └── entrypoint.sh              # Stdio startup and readiness checks
├── tests/
│   ├── __init__.py
│   ├── test_searxng.py
│   ├── test_google.py
│   └── test_tools.py
├── Dockerfile                     # Multi-stage build
├── pyproject.toml                 # Python project config
├── requirements.txt               # Dependencies
├── .env.example                   # Environment variables template
└── README.md                      # Usage documentation
```

---

# Implementation Phases

## Phase 1: Project Foundation
**Goal**: Set up project structure and core dependencies

| Task ID | Task | Description | Deliverable |
|---------|------|-------------|-------------|
| 1.1 | Initialize project | Create directory structure, pyproject.toml | Project skeleton |
| 1.2 | Configure dependencies | Create requirements.txt with mcp, httpx, beautifulsoup4, trafilatura, lxml | requirements.txt |
| 1.3 | Create config module | Environment variable handling, default values | src/web_mcp/config.py |
| 1.4 | Setup logging | Structured logging for debugging | Logging configuration |
| 1.5 | Create base abstractions | Abstract SearchProvider class | src/web_mcp/search/base.py |

---

## Phase 2: Search Providers
**Goal**: Implement SearxNG and Google scraping providers

| Task ID | Task | Description | Deliverable |
|---------|------|-------------|-------------|
| 2.1 | SearxNG client | HTTP client for SearxNG JSON API | src/web_mcp/search/searxng.py |
| 2.2 | Parse SearxNG response | Extract title, url, content from JSON | Response parser |
| 2.3 | SearxNG category support | Handle categories (general, news, images, etc.) | Category filtering |
| 2.4 | SearxNG error handling | Timeout, connection errors, retry logic | Error handling |
| 2.5 | Google scraping client | Fetch Google search results page | src/web_mcp/search/google.py |
| 2.6 | Parse Google HTML | Extract results using BeautifulSoup | HTML parser |
| 2.7 | User-Agent rotation | Rotate user agents to avoid blocks | UA management |
| 2.8 | Rate limiter | Prevent excessive requests | src/web_mcp/utils/rate_limiter.py |
| 2.9 | Provider fallback logic | Switch to Google when SearxNG fails | Fallback mechanism |
| 2.10 | Unit tests for providers | Test both search providers | tests/test_searxng.py, tests/test_google.py |

---

## Phase 3: Content Extraction
**Goal**: Implement URL content fetching and markdown conversion

| Task ID | Task | Description | Deliverable |
|---------|------|-------------|-------------|
| 3.1 | Fetch URL content | Download webpage content with httpx | URL fetcher |
| 3.2 | HTML to markdown | Convert HTML to clean markdown using trafilatura | src/web_mcp/utils/content_extractor.py |
| 3.3 | Handle encoding | Detect and handle various character encodings | Encoding handler |
| 3.4 | Handle errors | 404, timeout, SSL errors | Error handling |
| 3.5 | Content truncation | Limit output length for LLM consumption | Max length parameter |
| 3.6 | Metadata extraction | Extract title, description, author | Metadata parser |
| 3.7 | Unit tests | Test content extraction | tests/test_extractor.py |

---

## Phase 4: MCP Tools
**Goal**: Implement the three MCP tools

| Task ID | Task | Description | Deliverable |
|---------|------|-------------|-------------|
| 4.1 | web_search tool | Search tool with query, category, limit | src/web_mcp/tools/web_search.py |
| 4.2 | Tool input schema | Define JSON schema for parameters | Input validation |
| 4.3 | Tool response format | Structure response for MCP protocol | Output formatting |
| 4.4 | fetch_content tool | URL to markdown extraction tool | src/web_mcp/tools/fetch_content.py |
| 4.5 | get_suggestions tool | Query suggestions from SearxNG | src/web_mcp/tools/suggestions.py |
| 4.6 | Tool registration | Register all tools with MCP server | Tool registry |
| 4.7 | Unit tests for tools | Test each tool independently | tests/test_tools.py |

---

## Phase 5: MCP Server
**Goal**: Create the MCP server that exposes all tools

| Task ID | Task | Description | Deliverable |
|---------|------|-------------|-------------|
| 5.1 | Server initialization | Create MCP server instance | src/web_mcp/server.py |
| 5.2 | Register tools | Connect tools to server | Tool registration |
| 5.3 | stdio transport | Support standard input/output | Transport layer |
| 5.4 | SSE transport | Support Server-Sent Events (optional) | SSE handler |
| 5.5 | Error handling | Graceful error responses | Error middleware |
| 5.6 | Graceful shutdown | Handle SIGTERM, SIGINT | Signal handlers |
| 5.7 | Integration tests | Test full server functionality | tests/test_server.py |

---

## Phase 6: Docker Setup
**Goal**: Create single-container deployment with SearxNG + MCP

| Task ID | Task | Description | Deliverable |
|---------|------|-------------|-------------|
| 6.1 | SearxNG configuration | settings.yml with JSON format enabled | docker/searxng/settings.yml |
| 6.2 | Entrypoint startup script | Start SearxNG in background, then MCP server in foreground | docker/entrypoint.sh |
| 6.3 | Multi-stage Dockerfile | Build SearxNG stage, combine with Python | Dockerfile |
| 6.4 | .dockerignore | Exclude unnecessary files | .dockerignore |
| 6.5 | Environment setup | Configure SEARXNG_URL internally | Environment variables |
| 6.6 | Health checks | Container health monitoring | HEALTHCHECK directive |
| 6.7 | Volume mounts | Persist SearxNG data | Volume configuration |
| 6.8 | Build optimization | Minimize image size, layer caching | Build optimization |
| 6.9 | Test Docker build | Verify container builds and runs | Build verification |

---

## Phase 7: Documentation & Polish
**Goal**: Complete documentation and final testing

| Task ID | Task | Description | Deliverable |
|---------|------|-------------|-------------|
| 7.1 | README.md | Installation, usage, configuration docs | README.md |
| 7.2 | .env.example | Document all environment variables | .env.example |
| 7.3 | Usage examples | Example queries and responses | Examples section |
| 7.4 | Troubleshooting guide | Common issues and solutions | Troubleshooting section |
| 7.5 | API documentation | Document tool parameters and responses | API docs |
| 7.6 | End-to-end testing | Full integration test suite | E2E tests |
| 7.7 | Performance testing | Benchmark search performance | Performance report |
| 7.8 | Security review | Check for vulnerabilities | Security checklist |

---

## Phase Dependencies

```
Phase 1 (Foundation)
    │
    ├──► Phase 2 (Search Providers)
    │         │
    │         └──► Phase 3 (Content Extraction)
    │                   │
    └──► Phase 4 (MCP Tools) ◄─────────┘
              │
              └──► Phase 5 (MCP Server)
                        │
                        └──► Phase 6 (Docker)
                                  │
                                  └──► Phase 7 (Documentation)
```

---

## Estimated Effort

| Phase | Tasks | Est. Time |
|-------|-------|-----------|
| Phase 1: Foundation | 5 | 1-2 hours |
| Phase 2: Search Providers | 10 | 3-4 hours |
| Phase 3: Content Extraction | 7 | 2-3 hours |
| Phase 4: MCP Tools | 7 | 2-3 hours |
| Phase 5: MCP Server | 7 | 2-3 hours |
| Phase 6: Docker Setup | 9 | 3-4 hours |
| Phase 7: Documentation | 8 | 2-3 hours |
| **Total** | **53** | **15-22 hours** |

---

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SEARXNG_URL` | `http://localhost:8080` | SearxNG server URL |
| `SEARXNG_TIMEOUT` | `10` | Request timeout (seconds) |
| `FALLBACK_ENABLED` | `true` | Enable Google scraping fallback |
| `RATE_LIMIT_REQUESTS` | `30` | Max requests per minute |
| `RATE_LIMIT_PERIOD` | `60` | Rate limit period (seconds) |
| `MAX_CONTENT_LENGTH` | `10000` | Max characters in fetched content |
| `DEFAULT_SEARCH_LIMIT` | `5` | Default number of search results |
| `LOG_LEVEL` | `INFO` | Logging level |

### SearxNG Categories

| Category | Description |
|----------|-------------|
| `general` | Default web search |
| `images` | Image search |
| `videos` | Video search |
| `news` | News articles |
| `science` | Academic/scientific |
| `files` | File search |

---

## Success Criteria

### MVP Criteria (Current)

- [x] All 3 MCP tools functional (`web_search`, `fetch_content`, `get_suggestions`)
- [x] SearxNG as primary search with Google fallback
- [x] Single Docker container deployment
- [x] Rate limiting implemented
- [x] Baseline error handling implemented
- [x] Unit test suite passing locally
- [x] Documentation updated for current scope
- [x] stdio transport works for MCP clients

### Post-MVP Criteria (Deferred)

- [ ] SSE transport support
- [ ] End-to-end scenario suite and report
- [ ] Performance benchmark report
- [ ] Security review checklist/report

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Google blocks scraping | User-Agent rotation, rate limiting, SearxNG primary |
| SearxNG unavailable | Google scraping fallback |
| Large content sizes | Truncation with max_length parameter |
| Encoding issues | Auto-detect with chardet fallback |
| Docker image size | Multi-stage build, minimal base image |

---

## Next Steps

1. Implement SSE transport support when needed by target clients
2. Add end-to-end MCP client scenarios (including Claude Desktop profile)
3. Produce formal performance benchmark and security review artifacts
