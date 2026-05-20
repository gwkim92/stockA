#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

bash -n scripts/verify_manual_local_ingest_smoke.sh
python3 -m compileall src tests >/dev/null
PYTHONPATH=src python3 -m unittest \
  tests.test_manual_local_ingest_smoke \
  tests.test_data_operations_cli.DataOperationsCliTests.test_manual_local_ingest_smoke_preview_command_is_secret_free

RUNTIME_DIR=$(mktemp -d /private/tmp/stockanalysis-manual-smoke-verify.XXXXXX)
mkdir -p "$RUNTIME_DIR/artifacts"
cat > "$RUNTIME_DIR/data-operations.env" <<EOF
STOCKANALYSIS_DATABASE_URL="postgresql://verify:hidden@localhost/stockanalysis"
STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="$RUNTIME_DIR/artifacts"
EOF
cat > "$RUNTIME_DIR/frontend-api.env" <<EOF
STOCKANALYSIS_DATABASE_URL="postgresql://verify:hidden@localhost/stockanalysis"
EOF
PYTHONPATH=src python3 -m stockanalysis.operations.cli manual-local-ingest-smoke \
  --runtime-root "$RUNTIME_DIR" \
  --job-id market-price-daily \
  >/dev/null

echo "manual local ingest smoke verification passed"
