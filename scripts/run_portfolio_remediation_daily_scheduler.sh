#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
MODE="${1:-run}"

if [ "$MODE" != "run" ] && [ "$MODE" != "--preflight-only" ]; then
  echo "Usage: $0 [--preflight-only]" >&2
  exit 2
fi

require_env() {
  local name="$1"
  if [ -z "${!name:-}" ]; then
    echo "Missing required environment variable: $name" >&2
    exit 1
  fi
}

require_command() {
  local name="$1"
  if ! command -v "$name" >/dev/null 2>&1; then
    echo "Missing required command: $name" >&2
    exit 1
  fi
}

require_env "STOCKANALYSIS_PSQL_COMMAND"
require_env "PORTFOLIO_REMEDIATION_AS_OF_DATE"
require_env "PORTFOLIO_REMEDIATION_UNIVERSE_VERSION"
require_env "PORTFOLIO_REMEDIATION_COVERAGE_MEASUREMENT_END_DATE"
require_command "python3"

PORTFOLIO_NAME="${PORTFOLIO_REMEDIATION_PORTFOLIO_NAME:-Long Term Paper}"
STRATEGY_NAME="${PORTFOLIO_REMEDIATION_STRATEGY_NAME:-long_term_core}"
HORIZON_TYPE="${PORTFOLIO_REMEDIATION_HORIZON_TYPE:-long_term}"
TICKET_LIMIT="${PORTFOLIO_REMEDIATION_TICKET_LIMIT:-50}"
TICKET_STATUS="${PORTFOLIO_REMEDIATION_TICKET_STATUS:-open}"
ARTIFACT_ROOT="${PORTFOLIO_REMEDIATION_ARTIFACT_ROOT:-$ROOT_DIR/artifacts/portfolio-remediation-scheduler}"
RUN_DATE="${PORTFOLIO_REMEDIATION_RUN_DATE:-$(TZ=America/New_York date +%Y-%m-%d)}"
SKIP_DATES_RAW="${PORTFOLIO_REMEDIATION_SKIP_DATES:-}"
SKIP_REASON="${PORTFOLIO_REMEDIATION_SKIP_REASON:-configured_market_holiday}"

mkdir -p "$ARTIFACT_ROOT"
if [ ! -w "$ARTIFACT_ROOT" ]; then
  echo "Artifact root is not writable: $ARTIFACT_ROOT" >&2
  exit 1
fi

case "$TICKET_LIMIT" in
  ""|*[!0-9]*)
    echo "PORTFOLIO_REMEDIATION_TICKET_LIMIT must be a positive integer." >&2
    exit 1
    ;;
esac

if [ "$TICKET_LIMIT" -le 0 ]; then
  echo "PORTFOLIO_REMEDIATION_TICKET_LIMIT must be greater than 0." >&2
  exit 1
fi

SKIP_DATES=$(python3 - "$RUN_DATE" "$SKIP_DATES_RAW" <<'PY'
import datetime as dt
import sys

run_date, raw_skip_dates = sys.argv[1:]

try:
    dt.date.fromisoformat(run_date)
except ValueError as exc:
    raise SystemExit("PORTFOLIO_REMEDIATION_RUN_DATE must be ISO date YYYY-MM-DD.") from exc

skip_dates = raw_skip_dates.replace(",", " ").split()
for skip_date in skip_dates:
    try:
        dt.date.fromisoformat(skip_date)
    except ValueError as exc:
        raise SystemExit("PORTFOLIO_REMEDIATION_SKIP_DATES must contain only ISO dates YYYY-MM-DD.") from exc

print(" ".join(skip_dates))
PY
)

WOULD_SKIP="false"
for skip_date in $SKIP_DATES; do
  if [ "$skip_date" = "$RUN_DATE" ]; then
    WOULD_SKIP="true"
    break
  fi
done

RUN_STAMP=$(date -u +"%Y%m%dT%H%M%SZ")
JSON_PATH="$ARTIFACT_ROOT/${PORTFOLIO_REMEDIATION_AS_OF_DATE}-${RUN_STAMP}-portfolio-remediation-daily.json"
STDERR_PATH="$ARTIFACT_ROOT/${PORTFOLIO_REMEDIATION_AS_OF_DATE}-${RUN_STAMP}-portfolio-remediation-daily.stderr.log"

if [ "$MODE" = "--preflight-only" ]; then
  python3 - "$ARTIFACT_ROOT" "$JSON_PATH" "$STDERR_PATH" "$RUN_DATE" "$SKIP_DATES" "$WOULD_SKIP" "$SKIP_REASON" <<'PY'
import json
import sys

skip_dates = sys.argv[5].split()
print(
    json.dumps(
        {
            "preflight": "passed",
            "artifact_root": sys.argv[1],
            "json_path": sys.argv[2],
            "stderr_path": sys.argv[3],
            "run_date": sys.argv[4],
            "skip_dates": skip_dates,
            "would_skip": sys.argv[6] == "true",
            "skip_reason": sys.argv[7],
        },
        ensure_ascii=False,
        indent=2,
    )
)
PY
  exit 0
fi

if [ "$WOULD_SKIP" = "true" ]; then
  printf 'scheduler skipped for run_date=%s reason=%s\n' "$RUN_DATE" "$SKIP_REASON" > "$STDERR_PATH"
  python3 - "$JSON_PATH" "$RUN_DATE" "$SKIP_DATES" "$SKIP_REASON" "$PORTFOLIO_REMEDIATION_AS_OF_DATE" "$PORTFOLIO_NAME" "$STRATEGY_NAME" "$HORIZON_TYPE" "$PORTFOLIO_REMEDIATION_UNIVERSE_VERSION" "$PORTFOLIO_REMEDIATION_COVERAGE_MEASUREMENT_END_DATE" <<'PY'
import json
import sys

(
    json_path,
    run_date,
    skip_dates_raw,
    skip_reason,
    as_of_date,
    portfolio_name,
    strategy_name,
    horizon_type,
    universe_version,
    coverage_measurement_end_date,
) = sys.argv[1:]

with open(json_path, "w", encoding="utf-8") as handle:
    json.dump(
        {
            "report_name": "portfolio_remediation_scheduler_skip",
            "status": "skipped",
            "skip_type": "configured_skip_date",
            "skip_reason": skip_reason,
            "run_date": run_date,
            "skip_dates": skip_dates_raw.split(),
            "as_of_date": as_of_date,
            "portfolio_name": portfolio_name,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "universe_version": universe_version,
            "coverage_measurement_end_date": coverage_measurement_end_date,
        },
        handle,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    handle.write("\n")
PY
  echo "$JSON_PATH"
  exit 0
fi

cd "$ROOT_DIR"

set +e
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-remediation-daily-run \
  --portfolio-name "$PORTFOLIO_NAME" \
  --as-of-date "$PORTFOLIO_REMEDIATION_AS_OF_DATE" \
  --strategy-name "$STRATEGY_NAME" \
  --horizon-type "$HORIZON_TYPE" \
  --universe-version "$PORTFOLIO_REMEDIATION_UNIVERSE_VERSION" \
  --coverage-measurement-end-date "$PORTFOLIO_REMEDIATION_COVERAGE_MEASUREMENT_END_DATE" \
  --ticket-limit "$TICKET_LIMIT" \
  --ticket-status "$TICKET_STATUS" > "$JSON_PATH" 2> "$STDERR_PATH"
exit_code=$?
set -e

if [ "$exit_code" -ne 0 ]; then
  echo "portfolio-remediation-daily-run failed with exit code $exit_code" >&2
  echo "stdout artifact: $JSON_PATH" >&2
  echo "stderr artifact: $STDERR_PATH" >&2
  exit "$exit_code"
fi

python3 - "$JSON_PATH" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)

if payload.get("report_name") != "portfolio_remediation_daily_automation":
    raise SystemExit(f"Unexpected report_name: {payload.get('report_name')!r}")
if not payload.get("run_id"):
    raise SystemExit("Missing top-level run_id in scheduler output.")
PY

echo "$JSON_PATH"
