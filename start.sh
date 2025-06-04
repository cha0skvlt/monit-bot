#!/bin/sh
set -e

STATUS_FILE=${STATUS_FILE:-/app/status.json}

if [ ! -s "$STATUS_FILE" ]; then
    echo '{}' > "$STATUS_FILE"
fi

if [ -n "$SKIP_BOT" ]; then
    exit 0
fi

exec python /app/bot.py
