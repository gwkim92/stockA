#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"
ARTIFACT_ROOT=$(mktemp -d /tmp/stockanalysis-frontend-pagination.XXXXXX)
CLI_OUTPUT="$ARTIFACT_ROOT/events-page.json"

cleanup() {
  rm -rf "$ARTIFACT_ROOT"
}

trap cleanup EXIT

cd "$ROOT_DIR"

bash -n scripts/verify_frontend_api_pagination_conventions.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/frontend/pagination.py \
  src/stockanalysis/frontend/api_adapter.py \
  src/stockanalysis/frontend/live_adapter.py \
  src/stockanalysis/frontend/api_server.py \
  src/stockanalysis/frontend/fixture_server.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_frontend_pagination \
  tests.test_frontend_api_adapter \
  tests.test_frontend_live_adapter \
  tests.test_frontend_api_server \
  -v

PYTHONPATH=src "$PYTHON_BIN" -m stockanalysis.frontend.api_adapter get \
  --path "/api/events?asOfDate=2024-11-01&limit=1" > "$CLI_OUTPUT"

"$PYTHON_BIN" - "$CLI_OUTPUT" "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

cli_output, root_dir = sys.argv[1:]

payload = json.loads(Path(cli_output).read_text(encoding="utf-8"))
assert len(payload["data"]["events"]) == 1, payload
assert payload["pagination"]["limit"] == 1, payload
assert payload["pagination"]["has_more"] is True, payload
assert payload["pagination"]["next_cursor"], payload

collection_examples = {
    "docs/api/frontend/examples/remediation-tickets.json": "tickets",
    "docs/api/frontend/examples/cycle-state-list.json": "cycle_states",
    "docs/api/frontend/examples/event-list.json": "events",
    "docs/api/frontend/examples/portfolio-coverage.json": "positions",
    "docs/api/frontend/examples/performance-outcomes.json": "outcomes",
}

for relative_path, collection_key in collection_examples.items():
    example = json.loads((Path(root_dir) / relative_path).read_text(encoding="utf-8"))
    pagination = example["pagination"]
    items = example["data"][collection_key]
    assert pagination["limit"] == 50, example
    assert pagination["cursor"] is None, example
    assert pagination["next_cursor"] is None, example
    assert pagination["has_more"] is False, example
    assert pagination["item_count"] == len(items), example

types_text = (Path(root_dir) / "apps/web/src/lib/types.ts").read_text(encoding="utf-8")
assert "pagination?:" in types_text, types_text
assert "next_cursor: string | null" in types_text, types_text
PY

echo "frontend API pagination conventions verification passed"
