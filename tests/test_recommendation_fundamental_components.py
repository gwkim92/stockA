from __future__ import annotations

import json
import unittest
from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.recommendation_fundamental_components import (
    DEFAULT_MODEL_NAME,
    FUNDAMENTAL_COMPONENTS,
    render_recommendation_fundamental_components_preview_sql,
    render_recommendation_fundamental_components_upsert_sql,
    run_recommendation_fundamental_components,
)


class FakeRecommendationFundamentalExecutor:
    def __init__(self, *, run_id: int = 9801) -> None:
        self.run_id = run_id
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- recommendation fundamental components preview"):
            return json.dumps(
                {
                    "as_of_date": "2026-05-25",
                    "selected_batch_id": 7101,
                    "selected_batch_as_of_date": "2026-05-25",
                    "market_code": "US",
                    "strategy_name": "long_term_core",
                    "horizon_type": "long_term",
                    "model_name": DEFAULT_MODEL_NAME,
                    "component_names": list(FUNDAMENTAL_COMPONENTS),
                    "active_recommendation_count": 5,
                    "financial_coverage_count": 5,
                    "peer_coverage_count": 5,
                    "valuation_coverage_count": 5,
                    "linked_thesis_count": 2,
                    "existing_fundamental_component_count": 0,
                }
            )
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if sql.startswith("-- recommendation fundamental components upsert"):
            return json.dumps(
                {
                    "as_of_date": "2026-05-25",
                    "source_run_id": self.run_id,
                    "selected_batch_id": 7101,
                    "selected_batch_as_of_date": "2026-05-25",
                    "active_recommendation_count": 5,
                    "component_count": 25,
                    "component_counts": {
                        "balance_sheet_risk_penalty": 5,
                        "fundamental_quality_score": 5,
                        "peer_relative_score": 5,
                        "thesis_consistency_score": 5,
                        "valuation_margin_score": 5,
                    },
                    "non_zero_weight_count": 0,
                    "recommendation_total_score_mutated": False,
                }
            )
        raise AssertionError(f"Unexpected scalar SQL: {sql[:160]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class RecommendationFundamentalComponentsTests(unittest.TestCase):
    def test_preview_sql_is_read_only_and_reports_coverage(self) -> None:
        sql = render_recommendation_fundamental_components_preview_sql(as_of_date=date(2026, 5, 25))
        lowered = sql.lower()

        self.assertIn("-- recommendation fundamental components preview", sql)
        self.assertIn("signal.recommendation_batch", sql)
        self.assertIn("market.financial_metric_normalized", sql)
        self.assertIn("market.peer_relative_snapshot", sql)
        self.assertIn("market.valuation_snapshot", sql)
        self.assertIn("normalized.as_of_date <= '2026-05-25'::date", sql)
        self.assertIn("snapshot.as_of_date <= '2026-05-25'::date", sql)
        self.assertIn("valuation.as_of_date <= '2026-05-25'::date", sql)
        self.assertIn("existing_fundamental_component_count", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_upsert_sql_adds_zero_weight_components_without_mutating_totals(self) -> None:
        sql = render_recommendation_fundamental_components_upsert_sql(
            as_of_date=date(2026, 5, 25),
            source_run_id=9801,
        )

        self.assertIn("-- recommendation fundamental components upsert", sql)
        self.assertIn("insert into signal.recommendation_score_component", sql)
        self.assertIn("'fundamental_quality_score'", sql)
        self.assertIn("'valuation_margin_score'", sql)
        self.assertIn("'peer_relative_score'", sql)
        self.assertIn("'balance_sheet_risk_penalty'", sql)
        self.assertIn("'thesis_consistency_score'", sql)
        self.assertIn("0.0000::numeric as component_weight", sql)
        self.assertIn("'recommendation_total_score_mutated', false", sql)
        self.assertNotIn("update signal.recommendation recommendation", sql.lower())
        self.assertNotIn("set total_score", sql.lower())
        self.assertIn("'source_run_id', 9801", sql)

    def test_run_dry_run_reads_preview_without_writes(self) -> None:
        executor = FakeRecommendationFundamentalExecutor()

        report = run_recommendation_fundamental_components(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            execute=False,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["report_name"], "recommendation_fundamental_components")
        self.assertFalse(report["recommendation_total_score_mutated"])
        self.assertFalse(report["recommendation_weight_mutated"])
        self.assertEqual(executor.non_query_sql, [])
        self.assertEqual(len(executor.scalar_sql), 1)

    def test_run_execute_records_pipeline_and_upsert_summary(self) -> None:
        executor = FakeRecommendationFundamentalExecutor(run_id=9802)

        report = run_recommendation_fundamental_components(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            execute=True,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9802)
        self.assertEqual(report["upsert"]["component_count"], 25)  # type: ignore[index]
        self.assertEqual(report["upsert"]["non_zero_weight_count"], 0)  # type: ignore[index]
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("-- recommendation fundamental components upsert", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])


if __name__ == "__main__":
    unittest.main()
