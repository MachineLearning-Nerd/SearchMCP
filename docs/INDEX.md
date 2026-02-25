# SearchMCP Documentation

## Overview

**SearchMCP** is a web search MCP (Model Context Protocol) server that provides:

- **Web Search** via SearxNG (privacy-focused metasearch)
- **Google Scraping Fallback** when SearxNG is unavailable
- **Content Extraction** - URL to markdown conversion
- **Search Suggestions** - Query auto-complete

All packaged in a **single Docker container** with no API keys required.

---

## Quick Start

```bash
# Build and run
docker build -t web-mcp .
docker run -i web-mcp
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [README.md](../README.md) | Full documentation |
| [Implementation Plan](./web-mcp-implementation.md) | Development plan with phases |

---

## MCP Tools

| Tool | Description |
|------|-------------|
| `web_search` | Search the web with category filters |
| `fetch_content` | Extract markdown from URLs |
| `get_suggestions` | Get search query suggestions |

---

## Project Status

| Phase | Status |
|-------|--------|
| Phase 1: Project Foundation | ✅ Complete |
| Phase 2: Search Providers | ✅ Complete |
| Phase 3: Content Extraction | ✅ Complete |
| Phase 4: MCP Tools | ✅ Complete |
| Phase 5: MCP Server | ✅ Complete |
| Phase 6: Docker Setup | ✅ Complete |
| Phase 7: Documentation | 🟨 MVP Complete (deferred backlog) |

### Deferred Backlog (Post-MVP)

- SSE transport support (stdio remains the active transport)
- End-to-end scenario suite beyond unit/integration coverage
- Formal performance benchmark report
- Formal security checklist/review report

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
│  │  (Port 8080)    │      │   (stdio transport)     │  │
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

## Configuration

See [.env.example](../.env.example) for all configuration options.

Key settings:
- `SEARXNG_URL` - SearxNG server URL
- `FALLBACK_ENABLED` - Enable Google fallback
- `LOG_LEVEL` - Logging verbosity
