from __future__ import annotations

import json
import unittest
from datetime import date, datetime, timezone

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.portfolio_attribution import (
    render_portfolio_attribution_window_lookup_sql,
    resolve_portfolio_attribution_window,
    run_portfolio_attribution_monthly,
)


class FakePortfolioAttributionExecutor:
    def __init__(self, *, has_window: bool = True, run_id: int = 9201) -> None:
        self.has_window = has_window
        self.run_id = run_id
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- portfolio attribution candidate window lookup"):
            if not self.has_window:
                return "{}"
            return json.dumps(
                {
                    "portfolio_name": "Long Term Paper",
                    "snapshot_date": "2026-05-22",
                    "measurement_end_date": "2026-05-22",
                    "covered_position_count": 1,
                    "covered_weight": "0.1583",
                }
            )
        if sql.startswith("-- portfolio attribution candidate lookup"):
            return json.dumps(
                [
                    {
                        "portfolio_id": 3001,
                        "portfolio_name": "Long Term Paper",
                        "snapshot_date": "2026-05-22",
                        "measurement_start_date": "2026-05-22",
                        "measurement_end_date": "2026-05-22",
                        "instrument_id": 501,
                        "primary_symbol": "NVDA",
                        "position_weight": "0.1583",
                        "linked_thesis_id": 7001,
                        "thesis_title": "NVDA cycle thesis",
                        "primary_node_id": 401,
                        "node_code": "AI_SEMICONDUCTOR_CYCLE",
                        "node_name": "AI Semiconductor Cycle",
                        "recommendation_id": 9001,
                        "absolute_return_pct": "0.010000",
                        "benchmark_return_pct": "0.004000",
                        "alpha_pct": "0.006000",
                        "success_grade": "pass",
                    }
                ]
            )
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if "insert into performance.attribution_run" in sql:
            return json.dumps(
                {
                    "attribution_run_id": 6101,
                    "deleted_component_count": 0,
                    "component_count": 3,
                }
            )
        raise AssertionError(f"Unexpected scalar SQL: {sql[:120]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class OperationsPortfolioAttributionTests(unittest.TestCase):
    def test_render_window_lookup_uses_snapshot_and_thesis_outcomes(self) -> None:
        sql = render_portfolio_attribution_window_lookup_sql(
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
        )

        self.assertIn("portfolio.position_snapshot", sql)
        self.assertIn("performance.thesis_outcome", sql)
        self.assertIn("outcome.measurement_start_date = position.snapshot_date", sql)
        self.assertIn("2026-05-27", sql)

    def test_resolve_portfolio_attribution_window(self) -> None:
        window = resolve_portfolio_attribution_window(
            config=RuntimeConfig(psql_command="psql"),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
            executor=FakePortfolioAttributionExecutor(),  # type: ignore[arg-type]
        )

        self.assertIsNotNone(window)
        self.assertEqual(window.snapshot_date, date(2026, 5, 22))
        self.assertEqual(window.measurement_end_date, date(2026, 5, 22))
        self.assertEqual(window.covered_position_count, 1)
        self.assertEqual(str(window.covered_weight), "0.1583")

    def test_run_monthly_preview_selects_window_without_writes(self) -> None:
        executor = FakePortfolioAttributionExecutor()

        report = run_portfolio_attribution_monthly(
            config=RuntimeConfig(psql_command="psql"),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
            execute=False,
            executor=executor,  # type: ignore[arg-type]
            generated_at=datetime(2026, 5, 27, tzinfo=timezone.utc),
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["selected_window"]["snapshot_date"], "2026-05-22")
        self.assertEqual(len(executor.scalar_sql), 1)
        self.assertEqual(executor.non_query_sql, [])

    def test_run_monthly_execute_runs_existing_attribution_bootstrap(self) -> None:
        executor = FakePortfolioAttributionExecutor(run_id=9202)

        report = run_portfolio_attribution_monthly(
            config=RuntimeConfig(psql_command="psql"),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
            execute=True,
            executor=executor,  # type: ignore[arg-type]
            generated_at=datetime(2026, 5, 27, tzinfo=timezone.utc),
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9202)
        self.assertEqual(report["attribution_run_id"], 6101)
        self.assertEqual(report["candidate_count"], 1)
        self.assertEqual(report["component_count"], 3)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[2])
        self.assertIn("insert into performance.attribution_run", executor.scalar_sql[3])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])

    def test_run_monthly_execute_records_noop_pipeline_when_no_window_exists(self) -> None:
        executor = FakePortfolioAttributionExecutor(has_window=False, run_id=9203)

        report = run_portfolio_attribution_monthly(
            config=RuntimeConfig(psql_command="psql"),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
            execute=True,
            executor=executor,  # type: ignore[arg-type]
            generated_at=datetime(2026, 5, 27, tzinfo=timezone.utc),
        )

        self.assertEqual(report["status"], "completed_no_eligible_window")
        self.assertEqual(report["run_id"], 9203)
        self.assertIsNone(report["selected_window"])
        self.assertEqual(len(executor.scalar_sql), 2)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("no_eligible_attribution_window", executor.scalar_sql[1])
        self.assertEqual(len(executor.non_query_sql), 1)
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])


if __name__ == "__main__":
    unittest.main()

