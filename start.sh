#!/bin/sh
set -e

python - <<'EOF'
import core
core.init_db()
EOF

if [ -n "$SKIP_BOT" ]; then
    exit 0
fi

exec python /app/bot.py
