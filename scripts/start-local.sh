#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

export DATABASE_PATH="${DATABASE_PATH:-$(pwd)/data/citizens.sqlite}"
export APP_USERNAME="${APP_USERNAME:-admin}"
export APP_PASSWORD="${APP_PASSWORD:-change-this-password}"
export APP_SECRET="${APP_SECRET:-local-dev-secret}"
export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-8765}"

exec /usr/bin/python3 server.py
