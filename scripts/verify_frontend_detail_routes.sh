#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
WEB_DIR="$ROOT_DIR/apps/web"
ARTIFACT_ROOT=$(mktemp -d /tmp/stockanalysis-frontend-detail-routes.XXXXXX)
FIXTURE_PID=""
WEB_PID=""

free_port() {
  python3 - <<'PY'
import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
}

wait_for_url() {
  local url="$1"
  python3 - "$url" <<'PY'
import sys
import time
from urllib.request import urlopen

url = sys.argv[1]
last_error = None
for _ in range(80):
    try:
        with urlopen(url, timeout=2) as response:
            if 200 <= response.status < 500:
                raise SystemExit(0)
    except Exception as exc:
        last_error = exc
    time.sleep(0.25)
raise SystemExit(f"Timed out waiting for {url}: {last_error}")
PY
}

cleanup() {
  if [ -n "$WEB_PID" ]; then
    kill "$WEB_PID" >/dev/null 2>&1 || true
    wait "$WEB_PID" >/dev/null 2>&1 || true
  fi
  if [ -n "$FIXTURE_PID" ]; then
    kill "$FIXTURE_PID" >/dev/null 2>&1 || true
    wait "$FIXTURE_PID" >/dev/null 2>&1 || true
  fi
  rm -rf "$WEB_DIR/.next" "$WEB_DIR/tsconfig.tsbuildinfo"
  rm -rf "$ARTIFACT_ROOT"
}

trap cleanup EXIT

cd "$ROOT_DIR"

bash -n scripts/verify_frontend_detail_routes.sh
test -f "$WEB_DIR/src/app/recommendations/[recommendationId]/page.tsx"
test -f "$WEB_DIR/src/app/theses/[thesisId]/page.tsx"
test -f "$WEB_DIR/src/app/portfolio/coverage/page.tsx"
test -f "$WEB_DIR/src/lib/frontend-api.ts"
test -f "$WEB_DIR/src/lib/types.ts"

FIXTURE_PORT=$(free_port)
WEB_PORT=$(free_port)
FIXTURE_BASE_URL="http://127.0.0.1:$FIXTURE_PORT"
WEB_BASE_URL="http://127.0.0.1:$WEB_PORT"

PYTHONPATH=src python3 -m stockanalysis.frontend.fixture_server \
  --host 127.0.0.1 \
  --port "$FIXTURE_PORT" \
  > "$ARTIFACT_ROOT/fixture-server.json" \
  2> "$ARTIFACT_ROOT/fixture-server.err" &
FIXTURE_PID=$!

wait_for_url "$FIXTURE_BASE_URL/__health"

cd "$WEB_DIR"
npm install --no-audit --fund=false
npm run typecheck
STOCKANALYSIS_FRONTEND_API_BASE_URL="$FIXTURE_BASE_URL" npm run build
STOCKANALYSIS_FRONTEND_API_BASE_URL="$FIXTURE_BASE_URL" npm run start -- -p "$WEB_PORT" \
  > "$ARTIFACT_ROOT/web-server.log" \
  2> "$ARTIFACT_ROOT/web-server.err" &
WEB_PID=$!

wait_for_url "$WEB_BASE_URL"

python3 - "$WEB_BASE_URL" <<'PY'
import sys
from urllib.request import urlopen

base_url = sys.argv[1]
checks = {
    "/recommendations/AAPL-2024-11-01": "recommendation dossier",
    "/theses/AAPL-bootstrap-v1": "Thesis evidence ledger",
    "/portfolio/coverage": "Portfolio coverage gate",
}

for path, expected in checks.items():
    with urlopen(f"{base_url}{path}", timeout=5) as response:
        body = response.read().decode("utf-8")
    assert response.status == 200, (path, response.status)
    assert expected in body, (path, expected)
PY

cd "$ROOT_DIR"
bash scripts/verify_frontend_fixture_server.sh

echo "frontend detail routes verification passed"
