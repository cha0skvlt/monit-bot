#!/bin/sh
# Send a test message using BOT_TOKEN and CHAT_ID from the environment
set -e

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
