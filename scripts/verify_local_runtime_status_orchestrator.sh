#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

bash -n scripts/verify_local_runtime_status_orchestrator.sh
python3 -m compileall src tests >/dev/null
PYTHONPATH=src python3 -m unittest \
  tests.test_local_runtime_status_orchestrator \
  tests.test_data_operations_cli.DataOperationsCliTests.test_local_runtime_status_command_prints_secret_free_report
PYTHONPATH=src python3 -m stockanalysis.operations.cli local-runtime-status --skip-http-probes >/dev/null

echo "local runtime status orchestrator verification passed"
