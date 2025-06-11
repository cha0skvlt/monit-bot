#!/bin/bash
set -e

if ! command -v docker >/dev/null; then
  echo "Docker is not installed" >&2
  exit 1
fi

echo "🚀 Deploying commit $(git rev-parse --short HEAD)"

echo "📦 Stashing local changes (если есть)..."
git stash push -m "autodeploy changes" || true

echo "⬇️ Pulling latest code from GitHub..."
git pull origin master

echo "🔄 Restoring stashed changes..."
git stash pop || true

echo "🧹 Stopping old containers..."
docker compose down

echo "🗑️ Cleaning up unused Docker data..."
docker system prune -f

echo "🔨 Building and starting new containers..."
docker compose up -d --build

echo "✅ Deploy complete."
