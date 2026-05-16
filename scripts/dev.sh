#!/usr/bin/env bash
# Start backend (Flask on 127.0.0.1:8765) and frontend (Vite on 127.0.0.1:5173)
# Usage: bash scripts/dev.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

if [[ ! -f "$BACKEND/requirements.txt" ]]; then
  echo "backend not found at $BACKEND"; exit 1
fi
if [[ ! -f "$FRONTEND/package.json" ]]; then
  echo "frontend not found at $FRONTEND"; exit 1
fi

echo "[apc] starting backend (http://127.0.0.1:8765)"
( cd "$BACKEND" && python run.py ) &
BACKEND_PID=$!

sleep 2

echo "[apc] starting frontend (http://127.0.0.1:5173)"
( cd "$FRONTEND" && npm run dev ) &
FRONTEND_PID=$!

cleanup() {
  echo "[apc] shutting down..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

wait
