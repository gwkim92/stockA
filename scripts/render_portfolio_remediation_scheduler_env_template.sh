#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
OUTPUT_PATH=""
FORCE="false"

usage() {
  cat <<'USAGE'
Usage:
  scripts/render_portfolio_remediation_scheduler_env_template.sh --output PATH [--force]

Renders a scheduler env template to a repo-outside path.
USAGE
}

absolute_path() {
  python3 - "$1" <<'PY'
import os
import sys

print(os.path.abspath(sys.argv[1]))
PY
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --output)
      if [ "$#" -lt 2 ]; then
        echo "--output requires a path." >&2
        exit 2
      fi
      OUTPUT_PATH="$2"
      shift 2
      ;;
    --force)
      FORCE="true"
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$OUTPUT_PATH" ]; then
  echo "Missing required --output PATH." >&2
  exit 1
fi

ABS_ROOT=$(absolute_path "$ROOT_DIR")
ABS_OUTPUT=$(absolute_path "$OUTPUT_PATH")

case "$ABS_OUTPUT" in
  "$ABS_ROOT"|"$ABS_ROOT"/*)
    echo "Refusing to render scheduler env template inside repository: $ABS_OUTPUT" >&2
    exit 1
    ;;
esac

if [ -e "$ABS_OUTPUT" ] && [ "$FORCE" != "true" ]; then
  echo "Output already exists. Use --force to overwrite: $ABS_OUTPUT" >&2
  exit 1
fi

mkdir -p "$(dirname "$ABS_OUTPUT")"

cat > "$ABS_OUTPUT" <<'ENV'
# Portfolio remediation scheduler env.
# This file is sourced as shell by scheduler smoke/install scripts.
# Keep it outside the repository and do not commit credentials.

STOCKANALYSIS_PSQL_COMMAND="psql postgresql://USER:PASSWORD@HOST:5432/stockanalysis"

PORTFOLIO_REMEDIATION_AS_OF_DATE="YYYY-MM-DD"
PORTFOLIO_REMEDIATION_UNIVERSE_VERSION="CHANGE_ME_UNIVERSE_VERSION"
PORTFOLIO_REMEDIATION_COVERAGE_MEASUREMENT_END_DATE="YYYY-MM-DD"

PORTFOLIO_REMEDIATION_PORTFOLIO_NAME="Long Term Paper"
PORTFOLIO_REMEDIATION_STRATEGY_NAME="long_term_core"
PORTFOLIO_REMEDIATION_HORIZON_TYPE="long_term"
PORTFOLIO_REMEDIATION_TICKET_LIMIT="50"
PORTFOLIO_REMEDIATION_TICKET_STATUS="open"
PORTFOLIO_REMEDIATION_ARTIFACT_ROOT="/absolute/path/to/portfolio-remediation-scheduler-artifacts"

# Optional scheduler control.
# Leave RUN_DATE empty to use current America/New_York date.
# SKIP_DATES accepts comma and/or whitespace separated ISO dates.
PORTFOLIO_REMEDIATION_RUN_DATE=""
PORTFOLIO_REMEDIATION_SKIP_DATES=""
PORTFOLIO_REMEDIATION_SKIP_REASON="configured_market_holiday"
ENV

chmod 600 "$ABS_OUTPUT"
echo "$ABS_OUTPUT"
