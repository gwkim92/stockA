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
    echo "Missing required text in $path: $pattern" >&2
    exit 1
  fi
}

require_file "docs/frontend-architecture.md"
require_file "docs/tasks/frontend-architecture-foundation/contract.md"
require_file "docs/tasks/frontend-architecture-foundation/plan.md"
require_file "docs/tasks/frontend-architecture-foundation/handoff.md"
require_file "docs/tasks/frontend-architecture-foundation/review.md"
require_file "apps/web/package.json"
require_file "apps/web/src/app/page.tsx"
require_file "apps/web/src/lib/frontend-api.ts"

require_text "docs/frontend-architecture.md" "apps/web"
require_text "docs/frontend-architecture.md" "investment cockpit"
require_text "docs/frontend-architecture.md" "Route Map"
require_text "docs/frontend-architecture.md" "Data Boundary"
require_text "docs/frontend-architecture.md" "AI Boundary"
require_text "docs/frontend-architecture.md" "Security Boundary"
require_text "docs/frontend-architecture.md" "Implementation Phases"
require_text "docs/frontend-architecture.md" "Phase 2: frontend scaffold"
require_text "docs/frontend-architecture.md" "LLM은 frontend에서 추천을 직접 결정하지 않는다"
require_text "docs/frontend-architecture.md" "Python/Postgres pipeline"

echo "frontend architecture verification passed"
