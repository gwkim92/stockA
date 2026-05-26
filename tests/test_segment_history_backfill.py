from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.segment_history_backfill import (
    DEFAULT_SEGMENT_HISTORY_MODEL_NAME,
    run_segment_history_backfill,
)


class FakeSegmentHistoryExecutor:
    def __init__(self, *, run_id: int = 1071) -> None:
        self.run_id = run_id
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected SQL: {sql[:160]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class SegmentHistoryBackfillTests(unittest.TestCase):
    def test_dry_run_orchestrates_existing_backend_boundaries_without_parent_write(self) -> None:
        executor = FakeSegmentHistoryExecutor()
        with (
            patch("stockanalysis.operations.segment_history_backfill.run_financial_period_source_linkage") as linkage,
            patch("stockanalysis.operations.segment_history_backfill.run_reported_segment_footnote_parser") as parser,
            patch("stockanalysis.operations.segment_history_backfill.run_sum_of_parts_valuation") as sotp,
            patch("stockanalysis.operations.segment_history_backfill.run_valuation_snapshot") as valuation,
        ):
            linkage.return_value = {"report_name": "financial_period_source_linkage", "execute": False}
            parser.return_value = {
                "report_name": "reported_segment_footnote_parser",
                "execute": False,
                "preview": {"candidate_count": 3},
            }
            sotp.return_value = {"report_name": "sum_of_parts_valuation", "execute": False}
            valuation.return_value = {"report_name": "valuation_snapshot", "execute": False}

            report = run_segment_history_backfill(
                config=RuntimeConfig(psql_command="psql"),
                as_of_date=date(2026, 5, 26),
                statement_scope="annual",
                cik="320193",
                fallback_symbol="AAPL",
                max_filings=200,
                periods_per_instrument=4,
                execute=False,
                executor=executor,  # type: ignore[arg-type]
            )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["report_name"], "segment_history_backfill")
        self.assertEqual(report["model_name"], DEFAULT_SEGMENT_HISTORY_MODEL_NAME)
        self.assertEqual(report["periods_per_instrument"], 4)
        self.assertEqual(report["raw_fetch_limit"], 4)
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertFalse(report["automatic_order_allowed"])
        self.assertFalse(report["broker_submit_allowed"])
        self.assertEqual(report["order_boundary"], "read_only_no_order")
        self.assertEqual(executor.scalar_sql, [])
        parser.assert_called_once()
        self.assertEqual(parser.call_args.kwargs["periods_per_instrument"], 4)
        linkage.assert_called_once()
        self.assertEqual(linkage.call_args.kwargs["raw_fetch_limit"], 4)
        sotp.assert_called_once()
        valuation.assert_called_once()

    def test_execute_records_parent_pipeline_and_runs_children_in_execute_mode(self) -> None:
        executor = FakeSegmentHistoryExecutor(run_id=1072)
        with (
            patch("stockanalysis.operations.segment_history_backfill.run_financial_period_source_linkage") as linkage,
            patch("stockanalysis.operations.segment_history_backfill.run_reported_segment_footnote_parser") as parser,
            patch("stockanalysis.operations.segment_history_backfill.run_sum_of_parts_valuation") as sotp,
            patch("stockanalysis.operations.segment_history_backfill.run_valuation_snapshot") as valuation,
        ):
            linkage.return_value = {"report_name": "financial_period_source_linkage", "execute": True, "run_id": 1101}
            parser.return_value = {"report_name": "reported_segment_footnote_parser", "execute": True, "run_id": 1102}
            sotp.return_value = {"report_name": "sum_of_parts_valuation", "execute": True, "run_id": 1103}
            valuation.return_value = {"report_name": "valuation_snapshot", "execute": True, "run_id": 1104}

            report = run_segment_history_backfill(
                config=RuntimeConfig(psql_command="psql"),
                as_of_date=date(2026, 5, 26),
                statement_scope="annual",
                cik="320193",
                fallback_symbol="AAPL",
                raw_fetch_limit=2,
                periods_per_instrument=4,
                execute=True,
                executor=executor,  # type: ignore[arg-type]
            )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 1072)
        self.assertEqual(report["raw_fetch_limit"], 2)
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[0])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])
        self.assertTrue(linkage.call_args.kwargs["execute"])
        self.assertTrue(parser.call_args.kwargs["execute"])
        self.assertTrue(sotp.call_args.kwargs["execute"])
        self.assertTrue(valuation.call_args.kwargs["execute"])
        self.assertEqual(parser.call_args.kwargs["periods_per_instrument"], 4)
        self.assertEqual(linkage.call_args.kwargs["raw_fetch_limit"], 2)

    def test_rejects_invalid_history_period_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "periods_per_instrument must be greater than 0"):
            run_segment_history_backfill(
                config=RuntimeConfig(psql_command="psql"),
                as_of_date=date(2026, 5, 26),
                periods_per_instrument=0,
                execute=False,
                executor=FakeSegmentHistoryExecutor(),  # type: ignore[arg-type]
            )


if __name__ == "__main__":
    unittest.main()
