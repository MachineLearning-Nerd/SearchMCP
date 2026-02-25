# Web MCP Server

A privacy-focused web search MCP (Model Context Protocol) server that provides web search and content extraction capabilities. Uses **SearxNG** as the primary search engine with **Google scraping** as a fallback.

## Features

- **Web Search** - Search the web with category filters (general, news, images, videos, science, files)
- **Content Extraction** - Extract readable content from URLs as markdown
- **Search Suggestions** - Get query suggestions for better searches
- **Privacy-Focused** - Uses SearxNG metasearch engine
- **Fallback Support** - Automatically falls back to Google scraping if SearxNG is unavailable
- **Rate Limiting** - Built-in rate limiting to prevent abuse
- **Docker Ready** - Single-container deployment with SearxNG included

## Tools Provided

| Tool | Description |
|------|-------------|
| `web_search` | Search the web with query, category, and limit options |
| `fetch_content` | Extract and convert webpage content to markdown |
| `get_suggestions` | Get search query suggestions |

## Installation

### Option 1: Docker (Recommended)

```bash
# Build the image
docker build -t web-mcp:latest .

# Run the container
docker run -i web-mcp:latest
```

### Option 2: Python Package

```bash
# Clone the repository
git clone https://github.com/your-org/web-mcp.git
cd web-mcp

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .

# Run the server
python -m web_mcp.server
```

### Option 3: With External SearxNG

If you have an existing SearxNG instance:

```bash
# Set the SearxNG URL
export SEARXNG_URL=http://your-searxng-instance:8080

# Run the MCP server
python -m web_mcp.server
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SEARXNG_URL` | `http://localhost:8080` | SearxNG server URL |
| `SEARXNG_TIMEOUT` | `10` | Request timeout in seconds |
| `FALLBACK_ENABLED` | `true` | Enable Google scraping fallback |
| `RATE_LIMIT_REQUESTS` | `30` | Max requests per period |
| `RATE_LIMIT_PERIOD` | `60` | Rate limit period in seconds |
| `MAX_CONTENT_LENGTH` | `10000` | Max characters in fetched content |
| `DEFAULT_SEARCH_LIMIT` | `5` | Default number of search results |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `JSON_LOGS` | `false` | Output logs in JSON format |

### Configuration File

Create a `.env` file in the project root:

```env
SEARXNG_URL=http://localhost:8080
SEARXNG_TIMEOUT=10
FALLBACK_ENABLED=true
RATE_LIMIT_REQUESTS=30
RATE_LIMIT_PERIOD=60
MAX_CONTENT_LENGTH=10000
DEFAULT_SEARCH_LIMIT=5
LOG_LEVEL=INFO
JSON_LOGS=false
```

## Usage with MCP Clients

### Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "web-mcp": {
      "command": "docker",
      "args": ["run", "-i", "web-mcp:latest"]
    }
  }
}
```

Or with Python:

```json
{
  "mcpServers": {
    "web-mcp": {
      "command": "python",
      "args": ["-m", "web_mcp.server"],
      "env": {
        "SEARXNG_URL": "http://localhost:8080"
      }
    }
  }
}
```

### Other MCP Clients

The server uses stdio transport, making it compatible with any MCP-compatible client.

## Tool Reference

### web_search

Search the web for information.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | The search query |
| `category` | string | No | Search category: `general`, `images`, `videos`, `news`, `science`, `files` |
| `limit` | number | No | Maximum results (default: 5, max: 10) |

**Example:**

```json
{
  "name": "web_search",
  "arguments": {
    "query": "Python async programming",
    "category": "general",
    "limit": 5
  }
}
```

**Response:**

```markdown
# Search Results for: Python async programming

*Provider: searxng | 5 results*

---

## 1. Async IO in Python: A Complete Guide
**URL:** https://realpython.com/async-io-python/

Complete guide to async programming in Python...

## 2. Python asyncio Documentation
**URL:** https://docs.python.org/3/library/asyncio.html

Official Python asyncio documentation...
```

### fetch_content

Extract readable content from a URL.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | The URL to fetch content from |
| `max_length` | number | No | Maximum content length (default: 10000) |

**Example:**

```json
{
  "name": "fetch_content",
  "arguments": {
    "url": "https://example.com/article",
    "max_length": 5000
  }
}
```

**Response:**

```markdown
# Article Title

> Brief description of the article

**Author:** John Doe
**Source:** example.com
**URL:** https://example.com/article

---

[Article content in markdown format...]
```

### get_suggestions

Get search query suggestions.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | The partial search query |

**Example:**

```json
{
  "name": "get_suggestions",
  "arguments": {
    "query": "python asyn"
  }
}
```

**Response:**

```markdown
# Suggestions for: python asyn

1. python async await
2. python asyncio tutorial
3. python async http requests
4. python async context manager
5. python asyncio vs threading
```

## Development

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src tests

# Run type checking
mypy src
```

### Project Structure

```
web-mcp/
├── src/web_mcp/
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── server.py           # MCP server entry point
│   ├── search/
│   │   ├── base.py         # Abstract search provider
│   │   ├── searxng.py      # SearxNG provider
│   │   ├── google.py       # Google scraping fallback
│   │   └── fallback.py     # Fallback logic
│   ├── tools/
│   │   ├── web_search.py   # web_search tool
│   │   ├── fetch_content.py # fetch_content tool
│   │   └── suggestions.py  # get_suggestions tool
│   └── utils/
│       ├── logger.py       # Structured logging
│       ├── rate_limiter.py # Rate limiting
│       └── content_extractor.py # Content extraction
├── tests/                  # Test suite
├── docker/                 # Docker configuration
│   ├── searxng/           # SearxNG settings
│   ├── supervisord.conf   # Process manager config
│   └── entrypoint.sh      # Container entrypoint
├── Dockerfile             # Multi-stage Docker build
├── pyproject.toml         # Python project config
└── requirements.txt       # Dependencies
```

## Troubleshooting

### Common Issues

**1. SearxNG Connection Refused**

```
Error: Failed to connect to SearxNG
```

- Ensure SearxNG is running: `curl http://localhost:8080/config`
- Check `SEARXNG_URL` environment variable
- If using Docker, ensure both services are running (check supervisord logs)

**2. Google Rate Limiting**

```
Error: Google rate limit hit (429)
```

- Reduce request frequency
- SearxNG should be used as primary; Google is fallback only
- Wait a few minutes before retrying

**3. Content Extraction Failed**

```
Error: Failed to extract content from page
```

- The page may use JavaScript rendering (not supported)
- The page may block automated requests
- Try with a different URL

**4. Import Errors**

```
ModuleNotFoundError: No module named 'web_mcp'
```

- Ensure you're in the virtual environment
- Install the package: `pip install -e .`
- Check `PYTHONPATH` includes `src/`

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python -m web_mcp.server
```

### Docker Debugging

```bash
# Run container interactively
docker run -it --entrypoint /bin/sh web-mcp:latest

# Check supervisord status
docker exec <container> /usr/local/searxng/.venv/bin/supervisorctl status

# View logs
docker logs <container>
```

## Security Considerations

- **SearxNG Secret**: Change `SEARXNG_SECRET` in production
- **Rate Limiting**: Configure `RATE_LIMIT_REQUESTS` to prevent abuse
- **Network**: Container exposes port 8080 (for debugging only)
- **User Permissions**: Container defaults to root-managed processes; harden users/permissions for production

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## Acknowledgments

- [SearxNG](https://github.com/searxng/searxng) - Privacy-respecting metasearch engine
- [MCP](https://modelcontextprotocol.io/) - Model Context Protocol
- [Trafilatura](https://github.com/adbar/trafilatura) - Web content extraction
