#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)

cd "$ROOT_DIR"

python3 -m compileall src tests >/dev/null
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m stockanalysis.ingest.cli list-sources
PYTHONPATH=src python3 -m stockanalysis.ingest.cli build-request sec submissions --param cik=0000320193 >/dev/null
PYTHONPATH=src python3 -m stockanalysis.ingest.cli build-request fred series_observations --param series_id=CPIAUCSL >/dev/null
