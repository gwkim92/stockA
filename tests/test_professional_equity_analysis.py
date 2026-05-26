from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.professional_equity_analysis import (
    DEFAULT_MODEL_NAME,
    DEFAULT_FINANCIAL_FORECAST_MODEL_NAME,
    DEFAULT_PEER_RELATIVE_MODEL_NAME,
    DEFAULT_REPORTED_SEGMENT_MODEL_NAME,
    DEFAULT_SEGMENT_FOOTNOTE_MODEL_NAME,
    DEFAULT_SOTP_MODEL_NAME,
    DEFAULT_VALUATION_MODEL_NAME,
    FINANCIAL_FORECAST_SCENARIOS,
    REPORTED_SEGMENT_METRIC_CODES,
    SEGMENT_FOOTNOTE_EVIDENCE_TYPES,
    SOTP_COMPONENT_TYPES,
    STANDARD_FINANCIAL_METRICS,
    VALUATION_METHODS,
    extract_reported_segment_metrics_from_html,
    render_financial_forecast_inputs_preview_sql,
    render_financial_forecast_inputs_upsert_sql,
    render_financial_metric_normalization_preview_sql,
    render_financial_metric_normalization_upsert_sql,
    render_peer_relative_analysis_preview_sql,
    render_peer_relative_analysis_upsert_sql,
    render_reported_segment_footnote_candidates_sql,
    render_reported_segment_footnote_metric_upsert_sql,
    render_segment_footnote_evidence_preview_sql,
    render_segment_footnote_evidence_upsert_sql,
    render_sum_of_parts_valuation_preview_sql,
    render_sum_of_parts_valuation_upsert_sql,
    render_valuation_snapshot_preview_sql,
    render_valuation_snapshot_upsert_sql,
    run_financial_forecast_inputs,
    run_financial_metric_normalization,
    run_peer_relative_analysis,
    run_reported_segment_footnote_parser,
    run_segment_footnote_evidence,
    run_sum_of_parts_valuation,
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
                    "sum_of_parts_component_count": 6,
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
                        "sum_of_parts": 3,
                    },
                    "confidence_summary": {"min": 0.25, "avg": 0.4, "max": 0.5},
                }
            )
        if sql.startswith("-- financial forecast inputs preview"):
            return json.dumps(
                {
                    "as_of_date": "2026-05-25",
                    "model_name": DEFAULT_FINANCIAL_FORECAST_MODEL_NAME,
                    "statement_scope": "annual",
                    "scenario_keys": list(FINANCIAL_FORECAST_SCENARIOS),
                    "forecast_years": 5,
                    "raw_input_count": 3,
                    "normalized_input_count": 3,
                    "forecast_context_count": 3,
                    "existing_forecast_row_count": 0,
                }
            )
        if sql.startswith("-- financial forecast inputs upsert"):
            return json.dumps(
                {
                    "as_of_date": "2026-05-25",
                    "source_run_id": self.run_id,
                    "statement_scope": "annual",
                    "forecast_row_count": 45,
                    "scenario_counts": {"bear": 15, "base": 15, "bull": 15},
                    "max_forecast_year": 5,
                    "confidence_summary": {"min": 0.25, "avg": 0.4, "max": 0.55},
                }
            )
        if sql.startswith("-- reported segment footnote candidates"):
            return json.dumps(
                [
                    {
                        "instrument_id": 1,
                        "primary_symbol": "AAPL",
                        "period_end": "2024-09-28",
                        "source_document_id": 101,
                        "source_document_title": "Apple Inc. 10-K",
                        "raw_storage_uri": Path("tests/fixtures/sec_filing_segment_footnote_sample.html")
                        .resolve()
                        .as_uri(),
                        "source_document_url": "https://www.sec.gov/example/aapl-10k.htm",
                    }
                ]
            )
        if sql.startswith("-- reported segment footnote metric upsert"):
            return json.dumps(
                {
                    "as_of_date": "2026-05-25",
                    "source_run_id": self.run_id,
                    "statement_scope": "annual",
                    "reported_segment_metric_count": 4,
                    "parsed_instrument_count": 1,
                    "removed_gap_count": 1,
                    "metric_code_counts": {
                        "segment_operating_income": 2,
                        "segment_revenue": 2,
                    },
                    "recommendation_scoring_mutated": False,
                }
            )
        if sql.startswith("-- segment footnote evidence preview"):
            return json.dumps(
                {
                    "as_of_date": "2026-05-25",
                    "model_name": DEFAULT_SEGMENT_FOOTNOTE_MODEL_NAME,
                    "statement_scope": "annual",
                    "evidence_types": list(SEGMENT_FOOTNOTE_EVIDENCE_TYPES),
                    "source_period_count": 3,
                    "source_document_count": 2,
                    "consolidated_metric_count": 9,
                    "reported_segment_instrument_count": 0,
                    "segment_data_gap_candidate_count": 3,
                    "existing_evidence_count": 0,
                }
            )
        if sql.startswith("-- segment footnote evidence upsert"):
            return json.dumps(
                {
                    "as_of_date": "2026-05-25",
                    "source_run_id": self.run_id,
                    "statement_scope": "annual",
                    "evidence_row_count": 15,
                    "evidence_type_counts": {
                        "consolidated_metric": 9,
                        "filing_anchor": 3,
                        "segment_data_gap": 3,
                    },
                    "confidence_summary": {"min": 0.65, "avg": 0.71, "max": 0.8},
                    "recommendation_scoring_mutated": False,
                }
            )
        if sql.startswith("-- sum of parts valuation preview"):
            return json.dumps(
                {
                    "as_of_date": "2026-05-25",
                    "model_name": DEFAULT_SOTP_MODEL_NAME,
                    "statement_scope": "annual",
                    "component_types": list(SOTP_COMPONENT_TYPES),
                    "price_coverage_count": 3,
                    "raw_input_count": 3,
                    "forecast_input_count": 3,
                    "segment_footnote_evidence_count": 15,
                    "sotp_context_count": 3,
                    "existing_component_count": 0,
                }
            )
        if sql.startswith("-- sum of parts valuation upsert"):
            return json.dumps(
                {
                    "as_of_date": "2026-05-25",
                    "source_run_id": self.run_id,
                    "statement_scope": "annual",
                    "component_row_count": 9,
                    "component_type_counts": {
                        "operating_business": 3,
                        "balance_sheet_adjustment": 3,
                        "risk_reserve": 3,
                    },
                    "confidence_summary": {"min": 0.35, "avg": 0.43, "max": 0.5},
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

    def test_financial_forecast_input_migration_creates_read_only_evidence_table(self) -> None:
        sql = Path("db/migrations/0024_financial_forecast_inputs.sql").read_text(encoding="utf-8")

        self.assertIn("create table if not exists market.financial_forecast_input", sql)
        self.assertIn("scenario_key text not null", sql)
        self.assertIn("forecast_year integer not null", sql)
        self.assertIn("revenue_growth_rate numeric", sql)
        self.assertIn("free_cash_flow_margin numeric", sql)
        self.assertIn("capex_intensity numeric", sql)
        self.assertIn("free_cash_flow numeric", sql)
        self.assertIn("unique (instrument_id, as_of_date, statement_scope, scenario_key, forecast_year)", sql)
        self.assertIn("check (scenario_key in ('bear', 'base', 'bull'))", sql)
        self.assertNotIn("signal.recommendation_score_component", sql.lower())

    def test_sum_of_parts_migration_creates_component_table_and_method(self) -> None:
        sql = Path("db/migrations/0025_sum_of_parts_valuation.sql").read_text(encoding="utf-8")

        self.assertIn("create table if not exists market.sum_of_parts_component", sql)
        self.assertIn("component_key text not null", sql)
        self.assertIn("component_type text not null", sql)
        self.assertIn("fair_value_base numeric", sql)
        self.assertIn("unique (instrument_id, as_of_date, statement_scope, component_key)", sql)
        self.assertIn("check (component_type in ('operating_business', 'balance_sheet_adjustment', 'risk_reserve'))", sql)
        self.assertIn("drop constraint if exists valuation_snapshot_method_check", sql)
        self.assertIn("'sum_of_parts'", sql)
        self.assertNotIn("signal.recommendation_score_component", sql.lower())

    def test_segment_footnote_migration_creates_read_only_evidence_table(self) -> None:
        sql = Path("db/migrations/0026_segment_footnote_evidence.sql").read_text(encoding="utf-8")

        self.assertIn("create table if not exists research.segment_footnote_evidence", sql)
        self.assertIn("source_document_id bigint references ingest.source_document", sql)
        self.assertIn("evidence_type text not null", sql)
        self.assertIn("metric_code text not null", sql)
        self.assertIn("segment_data_gap", sql)
        self.assertIn("reported_segment_metric", sql)
        self.assertIn("unique (", sql)
        self.assertNotIn("signal.recommendation_score_component", sql.lower())

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

    def test_financial_forecast_inputs_preview_sql_is_read_only(self) -> None:
        sql = render_financial_forecast_inputs_preview_sql(as_of_date=date(2026, 5, 25), statement_scope="annual")
        lowered = sql.lower()

        self.assertIn("-- financial forecast inputs preview", sql)
        self.assertIn("market.financial_statement_period", sql)
        self.assertIn("market.financial_metric_normalized", sql)
        self.assertIn("market.financial_forecast_input", sql)
        self.assertIn("forecast_context_count", sql)
        self.assertIn("existing_forecast_row_count", sql)
        self.assertIn('"bear"', sql)
        self.assertIn('"base"', sql)
        self.assertIn('"bull"', sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_financial_forecast_inputs_upsert_sql_creates_scenarios_without_recommendation_mutation(self) -> None:
        sql = render_financial_forecast_inputs_upsert_sql(
            as_of_date=date(2026, 5, 25),
            source_run_id=9651,
            statement_scope="annual",
        )

        self.assertIn("-- financial forecast inputs upsert", sql)
        self.assertIn("insert into market.financial_forecast_input", sql)
        self.assertIn("scenario_adjustments as", sql)
        self.assertIn("generate_series(1, 5)", sql)
        self.assertIn("revenue_growth_rate", sql)
        self.assertIn("operating_margin", sql)
        self.assertIn("free_cash_flow_margin", sql)
        self.assertIn("capex_intensity", sql)
        self.assertIn("recommendation_scoring_mutated", sql)
        self.assertNotIn("signal.recommendation_score_component", sql)
        self.assertIn("9651::bigint", sql)

    def test_reported_segment_footnote_candidates_sql_is_read_only(self) -> None:
        sql = render_reported_segment_footnote_candidates_sql(
            as_of_date=date(2026, 5, 25),
            statement_scope="annual",
            limit=10,
        )
        lowered = sql.lower()

        self.assertIn("-- reported segment footnote candidates", sql)
        self.assertIn("market.financial_statement_period", sql)
        self.assertIn("ingest.source_document", sql)
        self.assertIn("raw_storage_uri", sql)
        self.assertIn("statement_metric_priority", sql)
        self.assertIn("metric_code in ('revenue', 'operating_income', 'net_income')", sql)
        self.assertIn("limit 10", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_extract_reported_segment_metrics_from_html_parses_segment_table(self) -> None:
        html = Path("tests/fixtures/sec_filing_segment_footnote_sample.html").read_text(encoding="utf-8")

        rows = extract_reported_segment_metrics_from_html(
            html,
            instrument_id=1,
            primary_symbol="AAPL",
            as_of_date=date(2026, 5, 25),
            statement_scope="annual",
            period_end=date(2024, 9, 28),
            source_document_id=101,
            source_document_title="Apple Inc. 10-K",
            source_document_url="https://www.sec.gov/example/aapl-10k.htm",
        )

        self.assertEqual(len(rows), 4)
        self.assertEqual({row.segment_label for row in rows}, {"Products", "Services"})
        self.assertEqual({row.metric_code for row in rows}, {"segment_revenue", "segment_operating_income"})
        self.assertTrue(all(row.metric_unit == "USD_millions_as_reported" for row in rows))
        self.assertTrue(all(row.assumptions_json["recommendation_scoring_mutated"] is False for row in rows))

    def test_extract_reported_segment_metrics_from_html_parses_transposed_segment_table(self) -> None:
        html = Path("tests/fixtures/sec_filing_aapl_transposed_segment_sample.html").read_text(encoding="utf-8")

        rows = extract_reported_segment_metrics_from_html(
            html,
            instrument_id=1,
            primary_symbol="AAPL",
            as_of_date=date(2026, 5, 26),
            statement_scope="annual",
            period_end=date(2025, 9, 27),
            source_document_id=1493,
            source_document_title="Apple Inc. 2025 10-K",
            source_document_url="https://www.sec.gov/example/aapl-20250927.htm",
        )

        self.assertEqual(len(rows), 10)
        self.assertEqual(
            {row.segment_label for row in rows},
            {"Americas", "Europe", "Greater China", "Japan", "Rest of Asia Pacific"},
        )
        self.assertNotIn("Corporate", {row.segment_label for row in rows})
        self.assertNotIn("Total", {row.segment_label for row in rows})
        self.assertEqual({row.metric_code for row in rows}, {"segment_revenue", "segment_operating_income"})
        values = {(row.segment_label, row.metric_code): row.metric_value for row in rows}
        self.assertEqual(str(values[("Americas", "segment_revenue")]), "178353")
        self.assertEqual(str(values[("Americas", "segment_operating_income")]), "72480")
        self.assertEqual(str(values[("Rest of Asia Pacific", "segment_revenue")]), "33696")
        self.assertTrue(all(row.metric_unit in {"USD_as_reported", "USD_millions_as_reported"} for row in rows))
        self.assertTrue(all(row.assumptions_json["parser_layout"] == "transposed_segment_metric_rows" for row in rows))
        self.assertTrue(all(row.assumptions_json["recommendation_scoring_mutated"] is False for row in rows))

    def test_reported_segment_footnote_metric_upsert_sql_removes_obsolete_gap_rows(self) -> None:
        html = Path("tests/fixtures/sec_filing_segment_footnote_sample.html").read_text(encoding="utf-8")
        rows = extract_reported_segment_metrics_from_html(
            html,
            instrument_id=1,
            primary_symbol="AAPL",
            as_of_date=date(2026, 5, 25),
            statement_scope="annual",
            period_end=date(2024, 9, 28),
            source_document_id=101,
        )
        sql = render_reported_segment_footnote_metric_upsert_sql(
            rows,
            as_of_date=date(2026, 5, 25),
            source_run_id=9654,
            statement_scope="annual",
        )

        self.assertIn("-- reported segment footnote metric upsert", sql)
        self.assertIn("insert into research.segment_footnote_evidence", sql)
        self.assertIn("'reported_segment_metric'::text", sql)
        self.assertIn("segment_revenue", sql)
        self.assertIn("segment_operating_income", sql)
        self.assertIn("delete from research.segment_footnote_evidence gap", sql.lower())
        self.assertIn("removed_stale_reported_metrics", sql)
        self.assertIn("removed_stale_metric_count", sql)
        self.assertIn("segment_data_gap", sql)
        self.assertIn("recommendation_scoring_mutated", sql)
        self.assertNotIn("signal.recommendation_score_component", sql)
        self.assertIn("9654::bigint", sql)

    def test_segment_footnote_evidence_preview_sql_is_read_only(self) -> None:
        sql = render_segment_footnote_evidence_preview_sql(as_of_date=date(2026, 5, 25), statement_scope="annual")
        lowered = sql.lower()

        self.assertIn("-- segment footnote evidence preview", sql)
        self.assertIn("market.financial_statement_period", sql)
        self.assertIn("market.financial_metric_value", sql)
        self.assertIn("research.segment_footnote_evidence", sql)
        self.assertIn("segment_data_gap_candidate_count", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_segment_footnote_evidence_upsert_sql_creates_evidence_without_recommendation_mutation(self) -> None:
        sql = render_segment_footnote_evidence_upsert_sql(
            as_of_date=date(2026, 5, 25),
            source_run_id=9656,
            statement_scope="annual",
        )

        self.assertIn("-- segment footnote evidence upsert", sql)
        self.assertIn("insert into research.segment_footnote_evidence", sql)
        self.assertIn("filing_anchor", sql)
        self.assertIn("consolidated_metric", sql)
        self.assertIn("segment_data_gap", sql)
        self.assertIn("market.financial_statement_period.source_document_id", sql)
        self.assertIn("recommendation_scoring_mutated", sql)
        self.assertNotIn("signal.recommendation_score_component", sql)
        self.assertIn("9656::bigint", sql)

    def test_sum_of_parts_valuation_preview_sql_is_read_only(self) -> None:
        sql = render_sum_of_parts_valuation_preview_sql(as_of_date=date(2026, 5, 25), statement_scope="annual")
        lowered = sql.lower()

        self.assertIn("-- sum of parts valuation preview", sql)
        self.assertIn("market.daily_price_bar", sql)
        self.assertIn("market.financial_metric_value", sql)
        self.assertIn("market.financial_forecast_input", sql)
        self.assertIn("market.sum_of_parts_component", sql)
        self.assertIn("research.segment_footnote_evidence", sql)
        self.assertIn("segment_footnote_evidence_count", sql)
        self.assertIn("sotp_context_count", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_sum_of_parts_valuation_upsert_sql_creates_components_without_recommendation_mutation(self) -> None:
        sql = render_sum_of_parts_valuation_upsert_sql(
            as_of_date=date(2026, 5, 25),
            source_run_id=9661,
            statement_scope="annual",
        )

        self.assertIn("-- sum of parts valuation upsert", sql)
        self.assertIn("insert into market.sum_of_parts_component", sql)
        self.assertIn("operating_business_fcf", sql)
        self.assertIn("balance_sheet_adjustment", sql)
        self.assertIn("segment_data_gap_reserve", sql)
        self.assertIn("terminal_base_free_cash_flow", sql)
        self.assertIn("forecast_or_latest_fcf_multiple", sql)
        self.assertIn("book_equity_partial_credit", sql)
        self.assertIn("segment_data_gap_reserve", sql)
        self.assertIn("segment_footnote_evidence_source", sql)
        self.assertIn("research.segment_footnote_evidence", sql)
        self.assertNotIn("signal.recommendation_score_component", sql)
        self.assertIn("9661::bigint", sql)

    def test_valuation_snapshot_upsert_sql_creates_methods_without_recommendation_mutation(self) -> None:
        sql = render_valuation_snapshot_upsert_sql(
            as_of_date=date(2026, 5, 25),
            source_run_id=9701,
            statement_scope="annual",
        )

        self.assertIn("-- valuation snapshot upsert", sql)
        self.assertIn("insert into market.valuation_snapshot", sql)
        self.assertIn("market.financial_forecast_input", sql)
        self.assertIn("forecast_inputs as", sql)
        self.assertIn("'forecast_input_source'", sql)
        self.assertIn("'forecast_scenarios'", sql)
        self.assertIn("'forecast_row_count'", sql)
        self.assertIn("base_forecast_free_cash_flow", sql)
        self.assertIn("'relative_multiple' as method", sql)
        self.assertIn("'scenario_range' as method", sql)
        self.assertIn("'dcf_lite' as method", sql)
        self.assertIn("'sum_of_parts' as method", sql)
        self.assertIn("market.sum_of_parts_component", sql)
        self.assertIn("'sotp_component_source'", sql)
        self.assertIn("'segment_footnote_evidence_source'", sql)
        self.assertIn("'segment_evidence_count'", sql)
        self.assertIn("'sotp_components'", sql)
        self.assertIn("shares_outstanding", sql)
        self.assertIn("free_cash_flow", sql)
        self.assertIn("'model_family', 'relative_valuation'", sql)
        self.assertIn("'model_family', 'scenario_range'", sql)
        self.assertIn("'model_family', 'intrinsic_dcf_lite'", sql)
        self.assertIn("'model_family', 'sum_of_parts'", sql)
        self.assertIn("'forecast_years', 5", sql)
        self.assertIn("'sensitivity_basis', 'growth_rate, discount_rate, terminal_growth_rate'", sql)
        self.assertIn(
            "'key_variables', json_build_array('fcf_per_share', 'growth_rate', 'discount_rate', 'terminal_growth_rate', 'forecast_scenarios')",
            sql,
        )
        self.assertIn("'data_quality', json_build_object", sql)
        self.assertIn("'limitations', json_build_array", sql)
        self.assertIn("상세 매출·마진·CAPEX forecast", sql)
        self.assertIn("보수·기준·낙관 case", sql)
        self.assertIn("recommendation_scoring_mutated", sql)
        self.assertNotIn("signal.recommendation_score_component", sql)
        self.assertIn("9701::bigint", sql)

    def test_run_financial_forecast_inputs_dry_run_reads_preview_without_writes(self) -> None:
        executor = FakeFinancialMetricExecutor()

        report = run_financial_forecast_inputs(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            statement_scope="annual",
            execute=False,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["report_name"], "financial_forecast_inputs")
        self.assertEqual(report["scenario_keys"], list(FINANCIAL_FORECAST_SCENARIOS))
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertEqual(executor.non_query_sql, [])
        self.assertEqual(len(executor.scalar_sql), 1)

    def test_run_financial_forecast_inputs_execute_records_pipeline_and_upsert_summary(self) -> None:
        executor = FakeFinancialMetricExecutor(run_id=9652)

        report = run_financial_forecast_inputs(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            statement_scope="annual",
            execute=True,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9652)
        self.assertEqual(report["upsert"]["forecast_row_count"], 45)  # type: ignore[index]
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("-- financial forecast inputs upsert", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])

    def test_run_reported_segment_footnote_parser_dry_run_parses_without_writes(self) -> None:
        executor = FakeFinancialMetricExecutor()

        report = run_reported_segment_footnote_parser(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            statement_scope="annual",
            execute=False,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["report_name"], "reported_segment_footnote_parser")
        self.assertEqual(report["supported_metric_codes"], list(REPORTED_SEGMENT_METRIC_CODES))
        self.assertEqual(report["preview"]["parsed_metric_count"], 4)  # type: ignore[index]
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertEqual(executor.non_query_sql, [])
        self.assertEqual(len(executor.scalar_sql), 1)

    def test_run_reported_segment_footnote_parser_execute_records_pipeline_and_upsert_summary(self) -> None:
        executor = FakeFinancialMetricExecutor(run_id=9655)

        report = run_reported_segment_footnote_parser(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            statement_scope="annual",
            execute=True,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9655)
        self.assertEqual(report["upsert"]["reported_segment_metric_count"], 4)  # type: ignore[index]
        self.assertFalse(report["upsert"]["recommendation_scoring_mutated"])  # type: ignore[index]
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("-- reported segment footnote metric upsert", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])

    def test_run_segment_footnote_evidence_dry_run_reads_preview_without_writes(self) -> None:
        executor = FakeFinancialMetricExecutor()

        report = run_segment_footnote_evidence(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            statement_scope="annual",
            execute=False,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["report_name"], "segment_footnote_evidence")
        self.assertEqual(report["evidence_types"], list(SEGMENT_FOOTNOTE_EVIDENCE_TYPES))
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertEqual(executor.non_query_sql, [])
        self.assertEqual(len(executor.scalar_sql), 1)

    def test_run_segment_footnote_evidence_execute_records_pipeline_and_upsert_summary(self) -> None:
        executor = FakeFinancialMetricExecutor(run_id=9657)

        report = run_segment_footnote_evidence(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            statement_scope="annual",
            execute=True,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9657)
        self.assertEqual(report["upsert"]["evidence_row_count"], 15)  # type: ignore[index]
        self.assertFalse(report["upsert"]["recommendation_scoring_mutated"])  # type: ignore[index]
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("-- segment footnote evidence upsert", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])

    def test_run_sum_of_parts_valuation_dry_run_reads_preview_without_writes(self) -> None:
        executor = FakeFinancialMetricExecutor()

        report = run_sum_of_parts_valuation(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            statement_scope="annual",
            execute=False,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["report_name"], "sum_of_parts_valuation")
        self.assertEqual(report["component_types"], list(SOTP_COMPONENT_TYPES))
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertEqual(executor.non_query_sql, [])
        self.assertEqual(len(executor.scalar_sql), 1)

    def test_run_sum_of_parts_valuation_execute_records_pipeline_and_upsert_summary(self) -> None:
        executor = FakeFinancialMetricExecutor(run_id=9662)

        report = run_sum_of_parts_valuation(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            statement_scope="annual",
            execute=True,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9662)
        self.assertEqual(report["upsert"]["component_row_count"], 9)  # type: ignore[index]
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("-- sum of parts valuation upsert", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])

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
