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
test -f "$WEB_DIR/src/app/ai-evidence/[evidenceId]/page.tsx"
test -f "$WEB_DIR/src/app/source-documents/[documentId]/page.tsx"
test -f "$WEB_DIR/src/app/events/page.tsx"
test -f "$WEB_DIR/src/app/themes/[themeKey]/page.tsx"
test -f "$WEB_DIR/src/app/performance/page.tsx"
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
    "/recommendations/AAPL-2024-11-01": ("Recommendation Dossier", "추천 검토서"),
    "/theses/AAPL-bootstrap-v1": ("Thesis evidence ledger", "투자 논리 상세"),
    "/portfolio/coverage": ("Portfolio coverage gate", "포트폴리오 커버리지 관문"),
    "/ai-evidence/sec-event-aapl-10k-20240928": ("AI Extraction Evidence", "AI 근거 상세", "뉴스 묶음 증거"),
    "/source-documents/aapl-2024-10k-20240928": ("Source Document Dossier", "원천 문서 검토서"),
    "/events": ("Event Evidence Map", "이벤트", "오늘 들어온 시장 뉴스와 원천 문서를 확인한다"),
    "/themes/ANNUAL_REPORTING": ("Annual reporting quality", "테마 화면은", "연간 보고"),
    "/performance": ("Performance outcome review", "성과 측정"),
}

for path, expected_terms in checks.items():
    with urlopen(f"{base_url}{path}", timeout=5) as response:
        body = response.read().decode("utf-8")
    assert response.status == 200, (path, response.status)
    assert any(term in body for term in expected_terms), (path, expected_terms)
PY

cd "$ROOT_DIR"
bash scripts/verify_frontend_fixture_server.sh

echo "frontend detail routes verification passed"
