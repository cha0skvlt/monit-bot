#!/bin/sh
# Send a test message using BOT_TOKEN and CHAT_ID from .env or environment
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Load .env from current directory or script directory if variables not set
if [ -z "$BOT_TOKEN" ] || [ -z "$CHAT_ID" ]; then
    if [ -f ./.env ]; then
        set -a
        . ./.env
        set +a
    elif [ -f "$SCRIPT_DIR/.env" ]; then
        set -a
        . "$SCRIPT_DIR/.env"
        set +a
    fi
fi

if [ -z "$BOT_TOKEN" ] || [ -z "$CHAT_ID" ]; then
    echo "BOT_TOKEN or CHAT_ID not set"
    exit 1
fi

if [ -n "$SKIP_SEND" ]; then
    echo "DRY RUN: would send test message to $CHAT_ID"
    exit 0
fi

curl -fsS -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
    -d chat_id="$CHAT_ID" -d text="test" >/dev/null

echo "Test message sent"
