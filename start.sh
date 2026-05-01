#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"

API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"
UI_HOST="${UI_HOST:-127.0.0.1}"
UI_PORT="${UI_PORT:-3000}"

API_URL="http://$API_HOST:$API_PORT"
UI_URL="http://$UI_HOST:$UI_PORT"

API_PID=""
UI_PID=""

cleanup() {
  if [[ -n "$UI_PID" ]] && kill -0 "$UI_PID" 2>/dev/null; then
    kill "$UI_PID" 2>/dev/null || true
  fi

  if [[ -n "$API_PID" ]] && kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID" 2>/dev/null || true
  fi
}

wait_for_url() {
  local url="$1"
  local attempts="${2:-60}"

  for ((attempt = 1; attempt <= attempts; attempt += 1)); do
    if command -v curl >/dev/null 2>&1; then
      if curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then
        return 0
      fi
    else
      if python3 - "$url" >/dev/null 2>&1 <<'PY'
import sys
from urllib.request import urlopen

with urlopen(sys.argv[1], timeout=2):
    pass
PY
      then
        return 0
      fi
    fi

    sleep 1
  done

  return 1
}

open_browser() {
  local url="$1"

  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url" >/dev/null 2>&1 &
  elif command -v gio >/dev/null 2>&1; then
    gio open "$url" >/dev/null 2>&1 &
  elif command -v open >/dev/null 2>&1; then
    open "$url" >/dev/null 2>&1 &
  else
    printf 'Open %s in your browser.\n' "$url"
  fi
}

if [[ ! -d "$FRONTEND_DIR" ]]; then
  printf 'Frontend directory not found: %s\n' "$FRONTEND_DIR" >&2
  exit 1
fi

if [[ -x "$ROOT_DIR/.venv/bin/uvicorn" ]]; then
  API_CMD=("$ROOT_DIR/.venv/bin/uvicorn" "main:app" "--host" "$API_HOST" "--port" "$API_PORT" "--reload")
elif command -v uv >/dev/null 2>&1; then
  API_CMD=("uv" "run" "uvicorn" "main:app" "--host" "$API_HOST" "--port" "$API_PORT" "--reload")
else
  printf 'Could not find .venv/bin/uvicorn or uv. Run uv sync first.\n' >&2
  exit 1
fi

trap cleanup EXIT INT TERM

printf 'Starting FastAPI at %s\n' "$API_URL"
(
  cd "$ROOT_DIR"
  "${API_CMD[@]}"
) &
API_PID="$!"

printf 'Starting Next.js UI at %s\n' "$UI_URL"
(
  cd "$FRONTEND_DIR"
  NEXT_PUBLIC_API_BASE_URL="$API_URL" npm run dev -- --hostname "$UI_HOST" --port "$UI_PORT"
) &
UI_PID="$!"

printf 'Waiting for UI to be ready...\n'
if wait_for_url "$UI_URL" 90; then
  open_browser "$UI_URL"
  printf 'Opened %s\n' "$UI_URL"
else
  printf 'UI did not become ready at %s before the timeout.\n' "$UI_URL" >&2
fi

printf 'Press Ctrl+C to stop FastAPI and Next.js.\n'
wait -n "$API_PID" "$UI_PID"
