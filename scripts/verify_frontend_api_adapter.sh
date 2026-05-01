#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
ARTIFACT_ROOT=$(mktemp -d /tmp/stockanalysis-frontend-api-adapter.XXXXXX)

cleanup() {
  rm -rf "$ARTIFACT_ROOT"
}

trap cleanup EXIT

cd "$ROOT_DIR"

bash -n scripts/verify_frontend_api_adapter.sh
python3 -m compileall src tests >/dev/null
PYTHONPATH=src python3 -m unittest tests.test_frontend_api_adapter -v
bash scripts/verify_frontend_api_contract.sh

PYTHONPATH=src python3 -m stockanalysis.frontend.api_adapter list > "$ARTIFACT_ROOT/list.json"
PYTHONPATH=src python3 -m stockanalysis.frontend.api_adapter get --path "/api/dashboard/today" > "$ARTIFACT_ROOT/dashboard.json"

python3 - "$ARTIFACT_ROOT/list.json" "$ARTIFACT_ROOT/dashboard.json" <<'PY'
import json
import sys

list_path, dashboard_path = sys.argv[1:]

with open(list_path, "r", encoding="utf-8") as handle:
    endpoint_payload = json.load(handle)
with open(dashboard_path, "r", encoding="utf-8") as handle:
    dashboard_payload = json.load(handle)

assert endpoint_payload["contract_version"] == "frontend-api-v0.1", endpoint_payload
assert len(endpoint_payload["endpoints"]) == 11, endpoint_payload
assert dashboard_payload["data"]["portfolio_name"] == "Long Term Paper", dashboard_payload
assert dashboard_payload["data"]["attention_summary"]["open_ticket_count"] == 1, dashboard_payload
PY

if PYTHONPATH=src python3 -m stockanalysis.frontend.api_adapter get --path "/api/not-found" > "$ARTIFACT_ROOT/error.json"; then
  echo "unknown frontend API path unexpectedly succeeded" >&2
  exit 1
fi

python3 - "$ARTIFACT_ROOT/error.json" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)

assert payload["error"]["code"] == "FrontendApiPathNotFound", payload
PY

if [ -e app ]; then
  echo "root-level app scaffold should not exist; use apps/web instead" >&2
  exit 1
fi

echo "frontend API adapter verification passed"
