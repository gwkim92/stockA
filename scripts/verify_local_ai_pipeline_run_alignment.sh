#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

bash -n scripts/verify_local_ai_pipeline_run_alignment.sh
python3 -m compileall src/stockanalysis/ingest/news src/stockanalysis/operations/cli.py tests/test_news_rss_cluster_evidence.py tests/test_data_operations_cli.py >/dev/null
PYTHONPATH=src python3 -m unittest \
  tests.test_news_rss_cluster_evidence \
  tests.test_data_operations_cli.DataOperationsCliTests.test_news_rss_cluster_evidence_run_command_passes_env_and_limits

PYTHONPATH=src python3 - <<'PY'
from datetime import date
from stockanalysis.ingest.news.cluster_evidence import run_news_rss_cluster_evidence


class Executor:
    def __init__(self) -> None:
        self.scalar_sql = []
        self.non_query_sql = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "from event.event e" in sql:
            return "[]"
        return "1"

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


executor = Executor()
summary = run_news_rss_cluster_evidence(
    config=object(),
    as_of_date=date(2026, 5, 20),
    pipeline_name="event_intelligence_llm_extract",
    executor=executor,
)
assert summary["pipeline_name"] == "event_intelligence_llm_extract"
assert summary["status"] == "completed"
print("local AI pipeline run alignment verification passed")
PY
