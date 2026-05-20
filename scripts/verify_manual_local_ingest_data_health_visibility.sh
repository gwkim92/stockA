#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

bash -n scripts/verify_manual_local_ingest_data_health_visibility.sh
python3 -m compileall src tests >/dev/null
PYTHONPATH=src python3 -m unittest \
  tests.test_manual_local_ingest_smoke \
  tests.test_data_operations_cli.DataOperationsCliTests.test_manual_local_ingest_smoke_preview_command_is_secret_free \
  tests.test_data_operations_cli.DataOperationsCliTests.test_manual_local_ingest_smoke_output_writes_repo_outside_summary \
  tests.test_data_operations_cli.DataOperationsCliTests.test_manual_local_ingest_smoke_output_rejects_repo_inside_path \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_data_health_response_includes_sanitized_manual_ingest_smoke \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_data_health_response_matches_frontend_contract_shape

RUNTIME_DIR=$(mktemp -d /private/tmp/stockanalysis-manual-visibility-verify.XXXXXX)
SUMMARY_PATH="$RUNTIME_DIR/manual-local-ingest-smoke.json"
mkdir -p "$RUNTIME_DIR/artifacts"
cat > "$RUNTIME_DIR/data-operations.env" <<EOF
STOCKANALYSIS_DATABASE_URL="postgresql://verify:hidden@localhost/stockanalysis"
STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="$RUNTIME_DIR/artifacts"
EOF
cat > "$RUNTIME_DIR/frontend-api.env" <<EOF
STOCKANALYSIS_DATABASE_URL="postgresql://verify:hidden@localhost/stockanalysis"
STOCKANALYSIS_MANUAL_LOCAL_INGEST_SMOKE_REPORT="$SUMMARY_PATH"
EOF

PYTHONPATH=src python3 -m stockanalysis.operations.cli manual-local-ingest-smoke \
  --runtime-root "$RUNTIME_DIR" \
  --job-id market-price-daily \
  --output "$SUMMARY_PATH" \
  >/dev/null

SUMMARY_PATH="$SUMMARY_PATH" PYTHONPATH=src python3 - <<'PY'
import json
import os
from pathlib import Path
from stockanalysis.operations.manual_local_ingest_smoke import load_manual_local_ingest_smoke_visibility_report

summary_path = Path(os.environ["SUMMARY_PATH"])
payload = json.loads(summary_path.read_text(encoding="utf-8"))
assert payload["report_name"] == "manual_local_ingest_smoke"
visibility = load_manual_local_ingest_smoke_visibility_report(report_path=summary_path, repo_root=Path.cwd())
assert visibility["status"] == "preview_not_executed"
assert visibility["planned_job_ids"] == ["market-price-daily"]
text = json.dumps(visibility, sort_keys=True)
assert "postgresql://" not in text
assert "hidden" not in text
print("manual local ingest data-health visibility verification passed")
PY
