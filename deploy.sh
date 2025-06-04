#!/bin/bash
set -e

echo "📦 Stashing local changes (если есть)..."
git stash push -m "autodeploy changes" || true

echo "⬇️ Pulling latest code from GitHub..."
git pull origin master

echo "🔄 Restoring stashed changes..."
git stash pop || true

echo "🧹 Stopping old containers..."
docker compose down

echo "🔨 Building and starting new containers..."
docker compose up -d --build

echo "✅ Deploy complete."
