from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.benchmark_composition_import import (
    build_benchmark_composition_import_report,
    load_benchmark_composition_csv,
    render_benchmark_composition_upsert_sql,
    run_benchmark_composition_import,
)


class FakeBenchmarkCompositionExecutor:
    def __init__(self) -> None:
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []
        self.run_id = 981

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class BenchmarkCompositionImportTests(unittest.TestCase):
    def test_load_csv_validates_rows_and_normalizes_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "holdings.csv"
            path.write_text(
                "symbol,target_weight,name,rationale\n"
                "aapl,0.0700,Apple,provider row\n"
                "MSFT,0.0600,Microsoft,\n",
                encoding="utf-8",
            )

            rows = load_benchmark_composition_csv(path)

        self.assertEqual([row.symbol for row in rows], ["AAPL", "MSFT"])
        self.assertEqual(rows[0].target_weight, Decimal("0.0700"))
        self.assertEqual(rows[1].rationale, None)

    def test_load_csv_rejects_duplicate_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "holdings.csv"
            path.write_text("symbol,target_weight\nAAPL,0.07\nAAPL,0.08\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "duplicate symbol"):
                load_benchmark_composition_csv(path)

    def test_build_report_marks_partial_coverage_without_mutation_flags(self) -> None:
        rows = load_benchmark_composition_csv(_fixture_csv("AAPL,0.0700\nMSFT,0.0600\n"))

        report = build_benchmark_composition_import_report(
            benchmark_code="spy",
            source_type="operator_upload",
            source_name="operator-spy-2026-05-25",
            source_as_of_date=date(2026, 5, 25),
            valid_from=date(2026, 5, 25),
            rows=rows,
        )

        self.assertEqual(report["benchmark_code"], "SPY")
        self.assertEqual(report["coverage_status"], "partial_holdings_only")
        self.assertFalse(report["full_benchmark_drift_interpretation_allowed"])
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertFalse(report["automatic_order_allowed"])
        self.assertFalse(report["broker_submit_allowed"])

    def test_build_report_marks_full_enough_coverage(self) -> None:
        rows = load_benchmark_composition_csv(_fixture_csv("AAPL,0.5000\nMSFT,0.4700\n"))

        report = build_benchmark_composition_import_report(
            benchmark_code="SPY",
            source_type="provider_file",
            source_name="provider-spy-2026-05-25",
            source_as_of_date=date(2026, 5, 25),
            valid_from=date(2026, 5, 25),
            rows=rows,
        )

        self.assertEqual(report["coverage_status"], "full_enough_for_drift")
        self.assertTrue(report["full_benchmark_drift_interpretation_allowed"])
        self.assertEqual(report["target_weight_total"], "0.9700")

    def test_render_upsert_uses_reference_tables_and_no_weight_or_order_mutation(self) -> None:
        rows = load_benchmark_composition_csv(_fixture_csv("AAPL,0.0700\nMSFT,0.0600\n"))

        sql = render_benchmark_composition_upsert_sql(
            benchmark_code="SPY",
            source_type="operator_upload",
            source_name="operator-spy-2026-05-25",
            source_as_of_date=date(2026, 5, 25),
            valid_from=date(2026, 5, 25),
            rows=rows,
        )
        lowered = sql.lower()

        self.assertIn("-- benchmark composition upsert", sql)
        self.assertIn("insert into ref.benchmark_composition", lowered)
        self.assertIn("join ref.instrument", lowered)
        self.assertIn("on conflict", lowered)
        self.assertNotIn("signal.recommendation_score_component", lowered)
        self.assertNotIn("trading.order_intent", lowered)
        self.assertNotIn("update signal.", lowered)

    def test_run_execute_records_pipeline_and_upserts(self) -> None:
        executor = FakeBenchmarkCompositionExecutor()

        report = run_benchmark_composition_import(
            config=RuntimeConfig(psql_command="docker exec psql"),
            holdings_csv=_fixture_csv("AAPL,0.0700\nMSFT,0.0600\n"),
            benchmark_code="SPY",
            source_type="operator_upload",
            source_name="operator-spy-2026-05-25",
            source_as_of_date=date(2026, 5, 25),
            valid_from=date(2026, 5, 25),
            execute=True,
            executor=executor,
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 981)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[0])
        self.assertIn("insert into ref.benchmark_composition", executor.non_query_sql[0].lower())
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])


def _fixture_csv(rows: str) -> Path:
    path = Path(tempfile.mkdtemp()) / "holdings.csv"
    path.write_text("symbol,target_weight\n" + rows, encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
