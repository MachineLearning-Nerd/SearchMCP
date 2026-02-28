# Web MCP Server Docker image
# Single container: SearxNG + MCP server

FROM searxng/searxng:2026.2.27-8e9ed5f9b

LABEL maintainer="SearchMCP Team"
LABEL description="Web MCP Server with SearxNG - Privacy-focused web search"
LABEL version="0.1.0"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SEARXNG_URL=http://127.0.0.1:8080 \
    SEARXNG_SECRET=change_me_in_production \
    LOG_LEVEL=INFO \
    FALLBACK_ENABLED=true

RUN mkdir -p /var/log/supervisor /var/run /app /etc/supervisor/conf.d \
    && /usr/local/searxng/.venv/bin/python -m ensurepip \
    && /usr/local/searxng/.venv/bin/python -m pip install --no-cache-dir \
        mcp>=1.0.0 \
        httpx>=0.27.0 \
        beautifulsoup4>=4.12.0 \
        lxml>=5.0.0 \
        trafilatura>=1.8.0 \
        pydantic>=2.0.0 \
        pydantic-settings>=2.0.0 \
        typing-extensions>=4.9.0 \
        supervisor>=4.2.0

COPY docker/searxng/settings.yml /etc/searxng/settings.yml
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/entrypoint.sh /entrypoint.sh
COPY src/web_mcp /app/web_mcp
COPY pyproject.toml /app/pyproject.toml

RUN chmod +x /entrypoint.sh

WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /usr/local/searxng/.venv/bin/python -c "import pathlib, httpx; r = httpx.get('http://127.0.0.1:8080/config', timeout=5); mcp_alive = any('web_mcp.server' in p.read_text(errors='ignore') for p in pathlib.Path('/proc').glob('[0-9]*/cmdline')); raise SystemExit(0 if r.status_code == 200 and mcp_alive else 1)"

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
