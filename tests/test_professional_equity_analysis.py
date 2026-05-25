from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.professional_equity_analysis import (
    DEFAULT_MODEL_NAME,
    DEFAULT_PEER_RELATIVE_MODEL_NAME,
    DEFAULT_VALUATION_MODEL_NAME,
    STANDARD_FINANCIAL_METRICS,
    VALUATION_METHODS,
    render_financial_metric_normalization_preview_sql,
    render_financial_metric_normalization_upsert_sql,
    render_peer_relative_analysis_preview_sql,
    render_peer_relative_analysis_upsert_sql,
    render_valuation_snapshot_preview_sql,
    render_valuation_snapshot_upsert_sql,
    run_financial_metric_normalization,
    run_peer_relative_analysis,
    run_valuation_snapshot,
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
        if sql.startswith("-- peer relative analysis preview"):
            return json.dumps(
                {
                    "as_of_date": "2026-05-25",
                    "model_name": DEFAULT_PEER_RELATIVE_MODEL_NAME,
                    "statement_scope": "annual",
                    "min_peer_count": 2,
                    "standard_metric_codes": list(STANDARD_FINANCIAL_METRICS),
                    "coverage_instrument_count": 3,
                    "latest_metric_count": 18,
                    "classification_peer_group_count": 1,
                    "existing_peer_group_count": 0,
                    "fallback_group_code": "US_CORE_FINANCIAL_DISCLOSURE",
                }
            )
        if sql.startswith("-- peer relative analysis upsert"):
            return json.dumps(
                {
                    "as_of_date": "2026-05-25",
                    "source_run_id": self.run_id,
                    "statement_scope": "annual",
                    "min_peer_count": 2,
                    "peer_group_count": 2,
                    "peer_member_count": 6,
                    "snapshot_count": 60,
                    "metric_counts": {"net_margin": 6},
                    "relative_signal_counts": {
                        "above_peer": 10,
                        "below_peer": 10,
                        "near_peer": 20,
                        "insufficient_data": 20,
                    },
                }
            )
        if sql.startswith("-- valuation snapshot preview"):
            return json.dumps(
                {
                    "as_of_date": "2026-05-25",
                    "model_name": DEFAULT_VALUATION_MODEL_NAME,
                    "statement_scope": "annual",
                    "methods": list(VALUATION_METHODS),
                    "price_coverage_count": 3,
                    "raw_financial_input_count": 3,
                    "normalized_input_count": 3,
                    "peer_context_count": 3,
                    "valuation_context_count": 3,
                    "dcf_lite_eligible_count": 2,
                    "existing_valuation_count": 0,
                }
            )
        if sql.startswith("-- valuation snapshot upsert"):
            return json.dumps(
                {
                    "as_of_date": "2026-05-25",
                    "source_run_id": self.run_id,
                    "statement_scope": "annual",
                    "snapshot_count": 8,
                    "method_counts": {
                        "dcf_lite": 2,
                        "relative_multiple": 3,
                        "scenario_range": 3,
                    },
                    "confidence_summary": {"min": 0.25, "avg": 0.4, "max": 0.5},
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
        self.assertIn("free_cash_flow_to_net_income", sql)
        self.assertIn("accrual_ratio", sql)
        self.assertIn("capex_intensity", sql)
        self.assertIn("liabilities_to_assets", sql)
        self.assertIn("(period.net_income - period.operating_cash_flow)", sql)
        self.assertIn("(period.operating_cash_flow - abs(period.capital_expenditure))", sql)
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

    def test_peer_relative_preview_sql_is_read_only_and_uses_classification_and_fallback_groups(self) -> None:
        sql = render_peer_relative_analysis_preview_sql(
            as_of_date=date(2026, 5, 25),
            statement_scope="annual",
            min_peer_count=2,
        )
        lowered = sql.lower()

        self.assertIn("-- peer relative analysis preview", sql)
        self.assertIn("market.financial_metric_normalized", sql)
        self.assertIn("ref.instrument_classification_membership", sql)
        self.assertIn("classification_peer_groups as", sql)
        self.assertIn("US_CORE_FINANCIAL_DISCLOSURE", sql)
        self.assertIn("normalized.statement_scope = 'annual'", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_peer_relative_upsert_sql_builds_groups_members_and_snapshots(self) -> None:
        sql = render_peer_relative_analysis_upsert_sql(
            as_of_date=date(2026, 5, 25),
            source_run_id=9601,
            statement_scope="annual",
            min_peer_count=2,
        )

        self.assertIn("-- peer relative analysis upsert", sql)
        self.assertIn("insert into ref.peer_group", sql)
        self.assertIn("insert into ref.peer_group_member", sql)
        self.assertIn("insert into market.peer_relative_snapshot", sql)
        self.assertIn("percentile_cont(0.5)", sql)
        self.assertIn("percent_rank()", sql)
        self.assertIn("insufficient_data", sql)
        self.assertNotIn("signal.recommendation_score_component", sql)
        self.assertIn("9601::bigint", sql)

    def test_run_peer_relative_analysis_dry_run_reads_preview_without_writes(self) -> None:
        executor = FakeFinancialMetricExecutor()

        report = run_peer_relative_analysis(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            statement_scope="annual",
            min_peer_count=2,
            execute=False,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["report_name"], "peer_relative_analysis")
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertEqual(executor.non_query_sql, [])
        self.assertEqual(len(executor.scalar_sql), 1)

    def test_run_peer_relative_analysis_execute_records_pipeline_and_upsert_summary(self) -> None:
        executor = FakeFinancialMetricExecutor(run_id=9602)

        report = run_peer_relative_analysis(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            statement_scope="annual",
            min_peer_count=2,
            execute=True,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9602)
        self.assertEqual(report["upsert"]["peer_group_count"], 2)  # type: ignore[index]
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("-- peer relative analysis upsert", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])

    def test_valuation_snapshot_preview_sql_is_read_only_and_reports_missing_dcf_coverage(self) -> None:
        sql = render_valuation_snapshot_preview_sql(as_of_date=date(2026, 5, 25), statement_scope="annual")
        lowered = sql.lower()

        self.assertIn("-- valuation snapshot preview", sql)
        self.assertIn("market.daily_price_bar", sql)
        self.assertIn("market.financial_metric_value", sql)
        self.assertIn("shares_outstanding", sql)
        self.assertIn("valuation_context_count", sql)
        self.assertIn("dcf_lite_eligible_count", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_valuation_snapshot_upsert_sql_creates_three_methods_without_recommendation_mutation(self) -> None:
        sql = render_valuation_snapshot_upsert_sql(
            as_of_date=date(2026, 5, 25),
            source_run_id=9701,
            statement_scope="annual",
        )

        self.assertIn("-- valuation snapshot upsert", sql)
        self.assertIn("insert into market.valuation_snapshot", sql)
        self.assertIn("'relative_multiple' as method", sql)
        self.assertIn("'scenario_range' as method", sql)
        self.assertIn("'dcf_lite' as method", sql)
        self.assertIn("shares_outstanding", sql)
        self.assertIn("free_cash_flow", sql)
        self.assertIn("recommendation_scoring_mutated", sql)
        self.assertNotIn("signal.recommendation_score_component", sql)
        self.assertIn("9701::bigint", sql)

    def test_run_valuation_snapshot_dry_run_reads_preview_without_writes(self) -> None:
        executor = FakeFinancialMetricExecutor()

        report = run_valuation_snapshot(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            statement_scope="annual",
            execute=False,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["report_name"], "valuation_snapshot")
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertEqual(executor.non_query_sql, [])
        self.assertEqual(len(executor.scalar_sql), 1)

    def test_run_valuation_snapshot_execute_records_pipeline_and_upsert_summary(self) -> None:
        executor = FakeFinancialMetricExecutor(run_id=9702)

        report = run_valuation_snapshot(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            statement_scope="annual",
            execute=True,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9702)
        self.assertEqual(report["upsert"]["method_counts"]["relative_multiple"], 3)  # type: ignore[index]
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("-- valuation snapshot upsert", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])


if __name__ == "__main__":
    unittest.main()
