from __future__ import annotations

import json
import unittest

from stockanalysis.ingest.macro.report import load_macro_run_history


class FakeReportExecutor:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.scalar_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        return json.dumps(self.payload)


class MacroReportTests(unittest.TestCase):
    def test_load_macro_run_history_returns_payload(self) -> None:
        executor = FakeReportExecutor(
            {
                "pipeline_name": "macro_upsert",
                "run_count": 1,
                "status_counts": {"succeeded": 1},
                "runs": [{"run_id": 55, "series_id": "CPIAUCSL"}],
            }
        )

        payload = load_macro_run_history(
            config=type("Config", (), {})(),
            executor=executor,
            limit=5,
        )

        self.assertEqual(payload["pipeline_name"], "macro_upsert")
        self.assertEqual(payload["run_count"], 1)
        self.assertIn("limit 5", executor.scalar_sql[0])

    def test_load_macro_run_history_adds_status_filter(self) -> None:
        executor = FakeReportExecutor(
            {
                "pipeline_name": "macro_upsert",
                "run_count": 0,
                "status_counts": {},
                "runs": [],
            }
        )

        payload = load_macro_run_history(
            config=type("Config", (), {})(),
            executor=executor,
            limit=10,
            status="failed",
        )

        self.assertEqual(payload["run_count"], 0)
        self.assertIn("status = 'failed'", executor.scalar_sql[0])

    def test_load_macro_run_history_rejects_non_positive_limit(self) -> None:
        with self.assertRaises(ValueError):
            load_macro_run_history(
                config=type("Config", (), {})(),
                executor=FakeReportExecutor({"pipeline_name": "macro_upsert", "run_count": 0, "status_counts": {}, "runs": []}),
                limit=0,
            )
