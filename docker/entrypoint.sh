#!/bin/sh
set -e

# Entrypoint script for Web MCP Server

echo "Starting Web MCP Server..." >&2

# Create log directories
mkdir -p /var/log/supervisor

# Set SearxNG secret if not provided
if [ -z "$SEARXNG_SECRET" ] || [ "$SEARXNG_SECRET" = "change_me_in_production" ]; then
    export SEARXNG_SECRET=$(/usr/local/searxng/.venv/bin/python -c "import secrets; print(secrets.token_hex(32))")
    echo "Generated SearxNG secret key" >&2
fi

# Update settings with secret
if [ -f /etc/searxng/settings.yml ]; then
    sed -i "s/change_me_to_a_random_string_in_production/$SEARXNG_SECRET/g" /etc/searxng/settings.yml
fi

# Set environment variables for MCP server
export SEARXNG_URL=${SEARXNG_URL:-http://127.0.0.1:8080}
export LOG_LEVEL=${LOG_LEVEL:-INFO}
export FALLBACK_ENABLED=${FALLBACK_ENABLED:-true}
export MCP_STDIO_MODE=${MCP_STDIO_MODE:-true}

echo "Configuration:" >&2
echo "  SEARXNG_URL: $SEARXNG_URL" >&2
echo "  LOG_LEVEL: $LOG_LEVEL" >&2
echo "  FALLBACK_ENABLED: $FALLBACK_ENABLED" >&2
echo "  MCP_STDIO_MODE: $MCP_STDIO_MODE" >&2

if [ "$MCP_STDIO_MODE" = "true" ]; then
    echo "Starting SearxNG in background for MCP stdio mode..." >&2
    searxng_boot_log="/var/log/supervisor/searxng-mcp-stdio.log"
    (
        cd /usr/local/searxng
        SEARXNG_SETTINGS_PATH="/etc/searxng/settings.yml" /usr/local/searxng/entrypoint.sh
    ) >>"$searxng_boot_log" 2>&1 &
    searxng_pid=$!

    cleanup() {
        if kill -0 "$searxng_pid" 2>/dev/null; then
            kill "$searxng_pid" 2>/dev/null || true
            wait "$searxng_pid" 2>/dev/null || true
        fi
    }
    trap cleanup EXIT INT TERM

    echo "Waiting for SearxNG readiness..." >&2
    ready=0
    i=0
    while [ "$i" -lt 120 ]; do
        if ! kill -0 "$searxng_pid" 2>/dev/null; then
            echo "SearxNG process exited during startup. Last logs:" >&2
            tail -n 50 "$searxng_boot_log" >&2 || true
            exit 1
        fi

        if /usr/local/searxng/.venv/bin/python -c "import httpx; r = httpx.get('http://127.0.0.1:8080/config', timeout=1.5); raise SystemExit(0 if r.status_code == 200 else 1)" >/dev/null 2>&1; then
            ready=1
            break
        fi
        i=$((i + 1))
        sleep 1
    done

    if [ "$ready" -ne 1 ]; then
        echo "SearxNG failed to become ready in MCP stdio mode" >&2
        exit 1
    fi

    echo "Starting MCP server (stdio)..." >&2
    /usr/local/searxng/.venv/bin/python -m web_mcp.server
    status=$?
    cleanup
    exit "$status"
fi

# Fallback process-manager mode
exec /usr/local/searxng/.venv/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
