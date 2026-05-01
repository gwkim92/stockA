#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
ARTIFACT_ROOT=$(mktemp -d /tmp/stockanalysis-frontend-live-read-adapter.XXXXXX)

cleanup() {
  rm -rf "$ARTIFACT_ROOT"
}

trap cleanup EXIT

cd "$ROOT_DIR"

bash -n scripts/verify_frontend_live_read_adapter.sh
python3 -m compileall src tests >/dev/null
PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v
PYTHONPATH=src python3 -m unittest tests.test_frontend_api_adapter -v
bash scripts/verify_frontend_api_adapter.sh

env -u STOCKANALYSIS_PSQL_COMMAND PYTHONPATH=src python3 -m stockanalysis.frontend.api_adapter \
  get --source auto --path "/api/remediation-tickets?status=open" > "$ARTIFACT_ROOT/auto-fallback.json"

python3 - "$ARTIFACT_ROOT/auto-fallback.json" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)

assert payload["contract_version"] == "frontend-api-v0.1", payload
assert payload["data"]["tickets"][0]["symbol"] == "BABA", payload
PY

if env -u STOCKANALYSIS_PSQL_COMMAND PYTHONPATH=src python3 -m stockanalysis.frontend.api_adapter \
  get --source live --path "/api/remediation-tickets?status=open" > "$ARTIFACT_ROOT/live-missing-config.json"; then
  echo "live frontend read unexpectedly succeeded without STOCKANALYSIS_PSQL_COMMAND" >&2
  exit 1
fi

python3 - "$ARTIFACT_ROOT/live-missing-config.json" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)

assert payload["error"]["code"] == "FrontendLiveReadUnavailable", payload
PY

if [ -e app ]; then
  echo "root-level app scaffold should not exist; use apps/web instead" >&2
  exit 1
fi

echo "frontend live read adapter verification passed"
