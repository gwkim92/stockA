#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
TMP_SQL="${TMPDIR:-/tmp}/stockanalysis-macro-sync.sql"

cd "$ROOT_DIR"

python3 -m compileall src tests >/dev/null
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m stockanalysis.ingest.cli macro-default-series >/dev/null
PYTHONPATH=src python3 -m stockanalysis.ingest.cli macro-sync \
  --series-id CPIAUCSL \
  --series-json tests/fixtures/fred_series_CPIAUCSL.json \
  --observations-json tests/fixtures/fred_observations_CPIAUCSL.json \
  --sql-output "$TMP_SQL" >/dev/null

test -s "$TMP_SQL"
