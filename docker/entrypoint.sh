#!/bin/sh
set -e

# Entrypoint script for Web MCP Server

echo "Starting Web MCP Server..."

# Create log directories
mkdir -p /var/log/supervisor

# Set SearxNG secret if not provided
if [ -z "$SEARXNG_SECRET" ] || [ "$SEARXNG_SECRET" = "change_me_in_production" ]; then
    export SEARXNG_SECRET=$(/usr/local/searxng/.venv/bin/python -c "import secrets; print(secrets.token_hex(32))")
    echo "Generated SearxNG secret key"
fi

# Update settings with secret
if [ -f /etc/searxng/settings.yml ]; then
    sed -i "s/change_me_to_a_random_string_in_production/$SEARXNG_SECRET/g" /etc/searxng/settings.yml
fi

# Set environment variables for MCP server
export SEARXNG_URL=${SEARXNG_URL:-http://127.0.0.1:8080}
export LOG_LEVEL=${LOG_LEVEL:-INFO}
export FALLBACK_ENABLED=${FALLBACK_ENABLED:-true}

echo "Configuration:"
echo "  SEARXNG_URL: $SEARXNG_URL"
echo "  LOG_LEVEL: $LOG_LEVEL"
echo "  FALLBACK_ENABLED: $FALLBACK_ENABLED"

# Start supervisord
exec /usr/local/searxng/.venv/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
