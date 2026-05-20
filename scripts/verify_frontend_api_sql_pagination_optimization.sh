#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"
cd "$ROOT_DIR"

bash -n scripts/verify_frontend_api_sql_pagination_optimization.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/frontend/pagination.py \
  src/stockanalysis/frontend/live_adapter.py \
  src/stockanalysis/signal/portfolio_remediation_ticket.py \
  src/stockanalysis/performance/coverage.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_frontend_pagination \
  tests.test_frontend_live_adapter \
  tests.test_portfolio_remediation_ticket \
  tests.test_portfolio_outcome_coverage_report \
  -v

grep -q "apply_frontend_sql_pagination" src/stockanalysis/frontend/pagination.py
grep -q "frontend_sql_page_window" src/stockanalysis/frontend/pagination.py
grep -q "apply_frontend_sql_pagination" src/stockanalysis/frontend/live_adapter.py
grep -q "cycle_page as" src/stockanalysis/frontend/live_adapter.py
grep -q "filtered_event_rows as" src/stockanalysis/frontend/live_adapter.py
grep -q "outcome_page as" src/stockanalysis/frontend/live_adapter.py
grep -q "selected_tickets as" src/stockanalysis/signal/portfolio_remediation_ticket.py
grep -q "offset {offset}" src/stockanalysis/signal/portfolio_remediation_ticket.py
grep -q "position_page as" src/stockanalysis/performance/coverage.py

test -f docs/frontend-api-sql-pagination-optimization.md
test -f docs/plans/2026-05-03-frontend-api-sql-pagination-optimization.md
test -f docs/tasks/frontend-api-sql-pagination-optimization/contract.md
test -f docs/tasks/frontend-api-sql-pagination-optimization/plan.md
test -f docs/tasks/frontend-api-sql-pagination-optimization/handoff.md
test -f docs/tasks/frontend-api-sql-pagination-optimization/review.md

grep -q "limit + 1" docs/frontend-api-sql-pagination-optimization.md
grep -q "offset cursor" docs/frontend-api-sql-pagination-optimization.md
grep -q "keyset" docs/frontend-api-sql-pagination-optimization.md
grep -q "frontend-api-local-collector-smoke" docs/project-execution-roadmap.md
grep -q "docs/frontend-api-local-collector-smoke.md" README.md
grep -q "frontend-api-alert-rules" docs/project-execution-roadmap.md
grep -q "docs/frontend-api-alert-rules.md" README.md
grep -q "data-operations-cadence-foundation" docs/project-execution-roadmap.md
grep -q "data-operations-artifact-runner" docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `data-operations-runtime-env-readiness`' AGENTS.md
grep -q "verify_frontend_api_sql_pagination_optimization.sh" docs/verification-plan.md
grep -q "docs/frontend-api-sql-pagination-optimization.md" README.md

echo "frontend API SQL pagination optimization verification passed"
