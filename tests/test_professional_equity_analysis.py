from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.professional_equity_analysis import (
    DEFAULT_MODEL_NAME,
    STANDARD_FINANCIAL_METRICS,
    render_financial_metric_normalization_preview_sql,
    render_financial_metric_normalization_upsert_sql,
    run_financial_metric_normalization,
)


class FakeFinancialMetricExecutor:
    def __init__(self, *, run_id: int = 9501) -> None:
        self.run_id = run_id
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- financial metric normalization preview"):
            return json.dumps(
                {
                    "as_of_date": "2026-05-25",
                    "model_name": DEFAULT_MODEL_NAME,
                    "standard_metric_codes": list(STANDARD_FINANCIAL_METRICS),
                    "source_period_count": 2,
                    "source_instrument_count": 1,
                    "latest_source_period_end": "2025-12-31",
                    "source_metric_codes": ["net_income", "revenue"],
                    "existing_normalized_count": 0,
                    "existing_computed_count": 0,
                }
            )
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if sql.startswith("-- financial metric normalization upsert"):
            return json.dumps(
                {
                    "as_of_date": "2026-05-25",
                    "source_run_id": self.run_id,
                    "summary": {
                        "upserted_count": 20,
                        "computed_count": 3,
                        "unavailable_count": 15,
                        "insufficient_history_count": 2,
                    },
                    "metric_counts": {"net_margin": 2, "revenue_growth_yoy": 2},
                    "status_counts": {"computed": 3, "unavailable": 15, "insufficient_history": 2},
                }
            )
        raise AssertionError(f"Unexpected scalar SQL: {sql[:160]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class ProfessionalEquityAnalysisTests(unittest.TestCase):
    def test_migration_creates_professional_analysis_tables_without_scoring_weight_change(self) -> None:
        sql = Path("db/migrations/0021_professional_equity_analysis.sql").read_text(encoding="utf-8")

        self.assertIn("create table if not exists market.financial_metric_normalized", sql)
        self.assertIn("create table if not exists ref.peer_group", sql)
        self.assertIn("create table if not exists market.peer_relative_snapshot", sql)
        self.assertIn("create table if not exists market.valuation_snapshot", sql)
        self.assertIn("create table if not exists research.equity_research_artifact", sql)
        self.assertNotIn("update signal.recommendation_score_component", sql.lower())
        self.assertNotIn("insert into signal.recommendation_score_component", sql.lower())

    def test_preview_sql_is_read_only_and_reports_standard_metrics(self) -> None:
        sql = render_financial_metric_normalization_preview_sql(as_of_date=date(2026, 5, 25), limit=10)
        lowered = sql.lower()

        self.assertIn("-- financial metric normalization preview", sql)
        self.assertIn("'2026-05-25'::date", sql)
        self.assertIn("market.financial_statement_period", sql)
        self.assertIn("market.financial_metric_normalized", sql)
        self.assertIn("revenue_growth_yoy", sql)
        self.assertIn("limit 10", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_upsert_sql_computes_ratios_and_preserves_missing_data_status(self) -> None:
        sql = render_financial_metric_normalization_upsert_sql(
            as_of_date=date(2026, 5, 25),
            source_run_id=9501,
            limit=10,
        )

        self.assertIn("-- financial metric normalization upsert", sql)
        self.assertIn("insert into market.financial_metric_normalized", sql)
        self.assertIn("on conflict (instrument_id, as_of_date, statement_scope, period_end, metric_code)", sql)
        self.assertIn("revenue_growth_yoy", sql)
        self.assertIn("gross_margin", sql)
        self.assertIn("free_cash_flow_margin", sql)
        self.assertIn("cash_flow_quality", sql)
        self.assertIn("left join lateral", sql)
        self.assertIn("limit 1", sql)
        self.assertIn("insufficient_history", sql)
        self.assertIn("unavailable", sql)
        self.assertIn("9501::bigint", sql)

    def test_run_dry_run_reads_preview_without_writes(self) -> None:
        executor = FakeFinancialMetricExecutor()

        report = run_financial_metric_normalization(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            limit=5,
            execute=False,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["report_name"], "financial_metric_normalization")
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertEqual(executor.non_query_sql, [])
        self.assertEqual(len(executor.scalar_sql), 1)

    def test_run_execute_records_pipeline_and_upsert_summary(self) -> None:
        executor = FakeFinancialMetricExecutor(run_id=9502)

        report = run_financial_metric_normalization(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            limit=5,
            execute=True,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9502)
        self.assertEqual(report["upsert"]["summary"]["upserted_count"], 20)  # type: ignore[index]
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("-- financial metric normalization upsert", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])


if __name__ == "__main__":
    unittest.main()
