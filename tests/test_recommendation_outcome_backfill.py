from __future__ import annotations

import json
import unittest
from datetime import date

from stockanalysis.operations.recommendation_outcome_backfill import run_recommendation_outcome_backfill


class FakeBackfillExecutor:
    def __init__(self, *, empty: bool = False, run_id: int = 9100) -> None:
        self.empty = empty
        self._next_run_id = run_id
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- performance outcome schedule candidate lookup"):
            if self.empty:
                return "[]"
            return json.dumps(
                [
                    {
                        "batch_id": 3001,
                        "as_of_date": "2026-04-20",
                        "market_code": "US",
                        "strategy_name": "long_term_core",
                        "horizon_type": "long_term",
                        "universe_version": "fixture-v2",
                        "horizon_day": 30,
                        "measurement_end_date": "2026-05-20",
                        "active_recommendation_count": 2,
                        "existing_outcome_count": 1,
                    }
                ]
            )
        if sql.startswith("-- performance outcome candidate lookup"):
            return json.dumps(
                [
                    {
                        "batch_id": 3001,
                        "recommendation_id": 91001,
                        "thesis_id": 71001,
                        "instrument_id": 501,
                        "primary_symbol": "SPY",
                        "recommendation_score": "0.4200",
                        "recommendation_bucket": "watch",
                        "recommendation_action": "watch",
                        "thesis_title": "SPY macro thesis",
                        "thesis_status": "active",
                        "benchmark_code": "SPY",
                        "measurement_start_date": "2026-04-20",
                        "measurement_end_date": "2026-05-20",
                        "entry_price": "500.000000",
                        "exit_price": "510.000000",
                        "min_price": "495.000000",
                        "benchmark_entry_price": "500.000000",
                        "benchmark_exit_price": "510.000000",
                    }
                ]
            )
        if "insert into ops.pipeline_run" in sql:
            run_id = self._next_run_id
            self._next_run_id += 1
            return str(run_id)
        if "insert into performance.recommendation_outcome" in sql:
            return json.dumps(
                {
                    "recommendation_outcome_count": 1,
                    "thesis_outcome_count": 1,
                }
            )
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class RecommendationOutcomeBackfillTests(unittest.TestCase):
    def test_preview_reports_due_candidates_without_writes(self) -> None:
        executor = FakeBackfillExecutor()
        report = run_recommendation_outcome_backfill(
            config=type("Config", (), {})(),
            due_on_date=date(2026, 5, 24),
            horizon_days=(30,),
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v2",
            execute=False,
            executor=executor,
        )

        self.assertEqual(report["report_name"], "recommendation_outcome_backfill")
        self.assertEqual(report["mode"], "preview")
        self.assertEqual(report["status"], "preview_candidates_available")
        self.assertEqual(report["candidate_count"], 1)
        self.assertEqual(report["missing_outcome_count"], 1)
        self.assertFalse(report["writes_enabled"])
        self.assertEqual(len(executor.scalar_sql), 1)
        self.assertEqual(executor.non_query_sql, [])

    def test_execute_runs_price_based_schedule_bootstrap(self) -> None:
        executor = FakeBackfillExecutor(run_id=9200)
        report = run_recommendation_outcome_backfill(
            config=type("Config", (), {})(),
            due_on_date=date(2026, 5, 24),
            horizon_days=(30,),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v2",
            execute=True,
            executor=executor,
        )

        self.assertEqual(report["mode"], "execute")
        self.assertEqual(report["status"], "executed")
        self.assertEqual(report["run_id"], 9200)
        self.assertEqual(report["succeeded_candidate_count"], 1)
        self.assertEqual(report["recommendation_outcome_count"], 1)
        self.assertEqual(report["thesis_outcome_count"], 1)
        self.assertEqual(report["label_counts"], {"inline": 1})
        self.assertIn("performance_outcome_schedule_bootstrap", executor.scalar_sql[2])
        self.assertIn("insert into performance.recommendation_outcome", executor.scalar_sql[-1])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])

    def test_empty_preview_reports_no_due_candidates(self) -> None:
        report = run_recommendation_outcome_backfill(
            config=type("Config", (), {})(),
            due_on_date=date(2026, 5, 24),
            horizon_days=(30,),
            execute=False,
            executor=FakeBackfillExecutor(empty=True),
        )

        self.assertEqual(report["status"], "preview_no_due_candidates")
        self.assertEqual(report["candidate_count"], 0)
        self.assertEqual(report["candidate_preview"], [])


if __name__ == "__main__":
    unittest.main()
