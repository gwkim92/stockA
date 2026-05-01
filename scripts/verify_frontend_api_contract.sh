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

require_absent_path() {
  local path="$1"
  if [ -e "$ROOT_DIR/$path" ]; then
    echo "Unexpected root-level frontend scaffold path: $path" >&2
    exit 1
  fi
}

require_file "docs/frontend-api-contract.md"
require_file "docs/api/frontend/contract-index.json"
require_file "docs/api/frontend/examples/daily-cockpit.json"
require_file "docs/api/frontend/examples/remediation-tickets.json"
require_file "docs/api/frontend/examples/data-health.json"
require_file "docs/api/frontend/examples/cycle-state-list.json"
require_file "docs/api/frontend/examples/recommendation-detail.json"
require_file "docs/api/frontend/examples/thesis-detail.json"
require_file "docs/api/frontend/examples/portfolio-coverage.json"
require_file "docs/tasks/frontend-api-contract-foundation/contract.md"
require_file "docs/tasks/frontend-api-contract-foundation/plan.md"
require_file "docs/tasks/frontend-api-contract-foundation/handoff.md"
require_file "docs/tasks/frontend-api-contract-foundation/review.md"

require_text "docs/frontend-api-contract.md" "frontend-api-v0.1"
require_text "docs/frontend-api-contract.md" "DailyCockpitResponse"
require_text "docs/frontend-api-contract.md" "RemediationTicketsResponse"
require_text "docs/frontend-api-contract.md" "DataHealthResponse"
require_text "docs/frontend-api-contract.md" "CycleStateListResponse"
require_text "docs/frontend-api-contract.md" "RecommendationDetailResponse"
require_text "docs/frontend-api-contract.md" "ThesisDetailResponse"
require_text "docs/frontend-api-contract.md" "PortfolioCoverageResponse"
require_text "docs/frontend-api-contract.md" "Initial frontend release is read-only"
require_text "docs/frontend-api-contract.md" "system of record: Python/Postgres pipeline"

python3 - "$ROOT_DIR" <<'PY'
import json
import os
import sys

root_dir = sys.argv[1]
index_path = os.path.join(root_dir, "docs/api/frontend/contract-index.json")

with open(index_path, "r", encoding="utf-8") as handle:
    index = json.load(handle)

assert index["contract_version"] == "frontend-api-v0.1", index
assert index["status"] == "draft", index
endpoints = index["endpoints"]
assert len(endpoints) == 7, endpoints

expected_dtos = {
    "DailyCockpitResponse",
    "RemediationTicketsResponse",
    "DataHealthResponse",
    "CycleStateListResponse",
    "RecommendationDetailResponse",
    "ThesisDetailResponse",
    "PortfolioCoverageResponse",
}
assert {endpoint["response_dto"] for endpoint in endpoints} == expected_dtos, endpoints

for endpoint in endpoints:
    assert endpoint["method"] == "GET", endpoint
    assert endpoint["path"].startswith("/api/"), endpoint
    example_path = os.path.join(root_dir, endpoint["example"])
    assert os.path.isfile(example_path), endpoint
    with open(example_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    assert payload["contract_version"] == index["contract_version"], payload
    assert payload["generated_at"].endswith("Z"), payload
    assert isinstance(payload["data"], dict) and payload["data"], payload
    assert isinstance(payload["links"], dict), payload

examples = {
    "daily": "docs/api/frontend/examples/daily-cockpit.json",
    "tickets": "docs/api/frontend/examples/remediation-tickets.json",
    "health": "docs/api/frontend/examples/data-health.json",
    "cycles": "docs/api/frontend/examples/cycle-state-list.json",
    "recommendation": "docs/api/frontend/examples/recommendation-detail.json",
    "thesis": "docs/api/frontend/examples/thesis-detail.json",
    "coverage": "docs/api/frontend/examples/portfolio-coverage.json",
}

loaded = {}
for key, relative_path in examples.items():
    with open(os.path.join(root_dir, relative_path), "r", encoding="utf-8") as handle:
        loaded[key] = json.load(handle)["data"]

assert loaded["daily"]["attention_summary"]["open_ticket_count"] == 1, loaded["daily"]
assert loaded["tickets"]["tickets"][0]["symbol"] == "BABA", loaded["tickets"]
assert "actual_runtime_db_smoke" in loaded["health"]["open_gates"], loaded["health"]
assert loaded["cycles"]["cycle_states"][0]["theme_key"] == "ANNUAL_REPORTING", loaded["cycles"]
assert loaded["recommendation"]["linked_thesis_id"] == "AAPL-bootstrap-v1", loaded["recommendation"]
assert loaded["thesis"]["status"] == "active", loaded["thesis"]
assert loaded["coverage"]["summary"]["missing_thesis_count"] == 1, loaded["coverage"]
PY

require_absent_path "app"

echo "frontend API contract verification passed"
