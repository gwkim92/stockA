#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

bash -n scripts/verify_project_execution_roadmap.sh
python3 -m compileall src tests >/dev/null

test -f docs/project-execution-roadmap.md
test -f docs/tasks/project-execution-roadmap/contract.md
test -f docs/tasks/project-execution-roadmap/plan.md
test -f docs/tasks/project-execution-roadmap/handoff.md
test -f docs/tasks/project-execution-roadmap/review.md

grep -q "Current State" docs/project-execution-roadmap.md
grep -q "Not Done" docs/project-execution-roadmap.md
grep -q "Execution Order" docs/project-execution-roadmap.md
grep -q "Live Read Completeness" docs/project-execution-roadmap.md
grep -q "API Runtime Boundary" docs/project-execution-roadmap.md
grep -q "Data Operations Loop" docs/project-execution-roadmap.md
grep -q "AI Runtime" docs/project-execution-roadmap.md
grep -q "Recommendation And Cycle Quality" docs/project-execution-roadmap.md
grep -q "Frontend Productization" docs/project-execution-roadmap.md
grep -q "frontend-live-read-expansion" docs/project-execution-roadmap.md
grep -q "새 프론트 기능보다 live read completeness를 먼저 진행한다" AGENTS.md
grep -q "docs/project-execution-roadmap.md" README.md
grep -q "verify_project_execution_roadmap.sh" docs/verification-plan.md

if grep -q "실거래 자동화는 별도 승인 전까지 범위 밖이다" AGENTS.md; then
  true
else
  echo "AGENTS.md must keep real-trading automation out of scope." >&2
  exit 1
fi

echo "project execution roadmap verification passed"
