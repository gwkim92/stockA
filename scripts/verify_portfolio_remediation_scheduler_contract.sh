#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)

require_file() {
  local path="$1"
  if [ ! -f "$ROOT_DIR/$path" ]; then
    echo "Missing required file: $path" >&2
    exit 1
  fi
}

require_text() {
  local path="$1"
  local pattern="$2"
  if ! rg -q "$pattern" "$ROOT_DIR/$path"; then
    echo "Missing required pattern in $path: $pattern" >&2
    exit 1
  fi
}

require_absent_path() {
  local path="$1"
  if [ -e "$ROOT_DIR/$path" ]; then
    echo "Unexpected scheduler activation artifact exists: $path" >&2
    exit 1
  fi
}

require_file "docs/portfolio-remediation-scheduler-contract.md"
require_file "docs/tasks/portfolio-remediation-scheduler-contract/contract.md"
require_file "docs/tasks/portfolio-remediation-scheduler-contract/loop_contract.md"
require_file "docs/tasks/portfolio-remediation-scheduler-contract/handoff.md"
require_file "docs/tasks/portfolio-remediation-scheduler-contract/review.md"

require_text "docs/portfolio-remediation-scheduler-contract.md" "portfolio-remediation-daily-run"
require_text "docs/portfolio-remediation-scheduler-contract.md" "America/New_York"
require_text "docs/portfolio-remediation-scheduler-contract.md" "Artifact Policy"
require_text "docs/portfolio-remediation-scheduler-contract.md" "Alert Policy"
require_text "docs/portfolio-remediation-scheduler-contract.md" "Retry Policy"
require_text "docs/portfolio-remediation-scheduler-contract.md" "Rollback Policy"
require_text "docs/portfolio-remediation-scheduler-contract.md" "Activation Gate"
require_text "docs/portfolio-remediation-scheduler-contract.md" "scheduler activation은 이번 작업 범위 밖"

require_text "docs/tasks/portfolio-remediation-scheduler-contract/loop_contract.md" "Proposed Cadence"
require_text "docs/tasks/portfolio-remediation-scheduler-contract/loop_contract.md" "Artifact Policy"
require_text "docs/tasks/portfolio-remediation-scheduler-contract/loop_contract.md" "Alert Policy"
require_text "docs/tasks/portfolio-remediation-scheduler-contract/loop_contract.md" "Retry Policy"
require_text "docs/tasks/portfolio-remediation-scheduler-contract/loop_contract.md" "Rollback Policy"
require_text "docs/tasks/portfolio-remediation-scheduler-contract/loop_contract.md" "Activation Gate"

require_absent_path ".github/workflows/portfolio-remediation-scheduler.yml"
require_absent_path "cron/portfolio-remediation-daily.cron"
require_absent_path "launchd/com.stockanalysis.portfolio-remediation.plist"
require_file "scripts/install_portfolio_remediation_scheduler.sh"

echo "portfolio remediation scheduler contract verification passed"
