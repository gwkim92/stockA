#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"

bash -n scripts/render_data_operations_env_template.sh
bash -n scripts/check_data_operations_runtime_env.sh
bash -n scripts/verify_data_operations_runtime_env_readiness.sh
"$PYTHON_BIN" -m compileall src tests >/dev/null

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_data_operations_env_readiness \
  tests.test_ingest_cli.IngestCliTests.test_data_operations_env_readiness_cli_prints_redacted_report \
  -v

TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/stockanalysis-data-ops-env.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT

TEMPLATE_ENV="$TMP_DIR/data-operations-template.env"
VALID_ENV="$TMP_DIR/data-operations-valid.env"
POSITIONS_CSV="$TMP_DIR/positions.csv"
MARKET_WATCHLIST_CSV="$TMP_DIR/market-watchlist.csv"
ARTIFACT_ROOT="$TMP_DIR/artifacts"
TEMPLATE_OUTPUT=$(scripts/render_data_operations_env_template.sh --output "$TEMPLATE_ENV")

if [ ! -f "$TEMPLATE_OUTPUT" ]; then
  echo "Unexpected template output path: $TEMPLATE_OUTPUT" >&2
  exit 1
fi

if scripts/render_data_operations_env_template.sh --output "$ROOT_DIR/.tmp-data-operations.env" >/tmp/stockanalysis-data-ops-render.err 2>&1; then
  echo "Renderer must refuse repo-inside output paths." >&2
  exit 1
fi
grep -q "inside repository" /tmp/stockanalysis-data-ops-render.err

if scripts/check_data_operations_runtime_env.sh --env-file "$TEMPLATE_ENV" >/tmp/stockanalysis-data-ops-template.out 2>&1; then
  echo "Unedited data operations env template must fail readiness." >&2
  exit 1
fi
grep -q "placeholder" /tmp/stockanalysis-data-ops-template.out

cat > "$POSITIONS_CSV" <<'CSV'
symbol,quantity
AAPL,10
CSV

cat > "$MARKET_WATCHLIST_CSV" <<'CSV'
symbol
AAPL
MSFT
CSV

cat > "$VALID_ENV" <<ENV
STOCKANALYSIS_DATABASE_URL="postgresql://runtime_user:runtime_pass@db.internal:5432/stockanalysis"
STOCKANALYSIS_FRED_API_KEY="fred-runtime-token-123"
STOCKANALYSIS_MARKET_PRICE_PROVIDER="twelve_data"
STOCKANALYSIS_TWELVE_DATA_API_KEY="twelve-runtime-token-123"
STOCKANALYSIS_MARKET_PRICE_WATCHLIST_CSV="$MARKET_WATCHLIST_CSV"
STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH="$TMP_DIR/market-ledger.json"
STOCKANALYSIS_ALPHA_VANTAGE_API_KEY="alpha-runtime-token-123"
STOCKANALYSIS_SEC_USER_AGENT="stockanalysis-test contact@operator.test"
STOCKANALYSIS_PORTFOLIO_POSITIONS_CSV="$POSITIONS_CSV"
STOCKANALYSIS_LLM_PROVIDER="openai"
OPENAI_API_KEY="openai-runtime-key-123456"
STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="$ARTIFACT_ROOT"
ENV
chmod 600 "$VALID_ENV"

VALID_OUTPUT="$TMP_DIR/readiness.json"
scripts/check_data_operations_runtime_env.sh --env-file "$VALID_ENV" > "$VALID_OUTPUT"
python3 - "$VALID_OUTPUT" <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
assert payload["report_name"] == "data_operations_runtime_env_readiness"
assert payload["runtime_env_readiness"] == "passed"
assert "database" in payload["validated_env_groups"]
assert "market_price_provider" in payload["validated_env_groups"]
assert "openai_or_llm_provider" in payload["validated_env_groups"]
text = json.dumps(payload)
for forbidden in [
    "postgresql://runtime_user:runtime_pass",
    "fred-runtime-token-123",
    "twelve-runtime-token-123",
    "alpha-runtime-token-123",
    "openai-runtime-key-123456",
    "contact@operator.test",
]:
    assert forbidden not in text, forbidden
PY

if scripts/check_data_operations_runtime_env.sh --env-file "$ROOT_DIR/README.md" >/tmp/stockanalysis-data-ops-readme.json 2>/tmp/stockanalysis-data-ops-readme.err; then
  echo "Checker must refuse repo-inside env files." >&2
  exit 1
fi
grep -q "inside repository" /tmp/stockanalysis-data-ops-readme.err

grep -q "data-operations-runtime-env-readiness" docs/project-execution-roadmap.md
grep -q "data-operations-runtime-env-readiness" docs/verification-plan.md
grep -q "docs/data-operations-runtime-env-readiness.md" README.md
grep -q "data-operations-runtime-smoke" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-activation-boundary" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-install-dry-run" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-alert-boundary" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-activation-runbook" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-operator-dry-run" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-activation-approval-gate" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-request" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-user-decision" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-final-preflight" docs/project-execution-roadmap.md
grep -q 'Current task: `local-live-mvp-runtime`' docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `local-live-mvp-runtime`' AGENTS.md

PYTHONPATH=/Users/woody/ai/agent-work-harness/src "$PYTHON_BIN" -m awh verify --repo "$ROOT_DIR" --task data-operations-runtime-env-readiness

echo "data operations runtime env readiness verification passed"
