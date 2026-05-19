#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p logs

if ! lsof -i tcp:8765 -sTCP:LISTEN >/dev/null 2>&1; then
  nohup scripts/start-local.sh > logs/server.out.log 2> logs/server.err.log &
fi

open "http://127.0.0.1:8765/"
