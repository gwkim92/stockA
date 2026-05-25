from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.industry_competitive_positioning import (
    DEFAULT_METHODOLOGY,
    DEFAULT_MODEL_NAME,
    render_industry_competitive_positioning_preview_sql,
    render_industry_competitive_positioning_upsert_sql,
    run_industry_competitive_positioning,
)


class FakeIndustryCompetitiveExecutor:
    def __init__(self, *, run_id: int = 9901) -> None:
        self.run_id = run_id
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- industry competitive positioning preview"):
            return json.dumps(
                {
                    "as_of_date": "2026-05-25",
                    "model_name": DEFAULT_MODEL_NAME,
                    "methodology": DEFAULT_METHODOLOGY,
                    "min_metric_coverage": 3,
                    "candidate_instrument_count": 5,
                    "candidate_peer_group_count": 2,
                    "latest_peer_metric_count": 40,
                    "existing_position_count": 0,
                }
            )
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if sql.startswith("-- industry competitive positioning upsert"):
            return json.dumps(
                {
                    "as_of_date": "2026-05-25",
                    "source_run_id": self.run_id,
                    "methodology": DEFAULT_METHODOLOGY,
                    "position_count": 5,
                    "competitive_position_counts": {
                        "advantaged": 2,
                        "in_line": 2,
                        "insufficient_data": 1,
                    },
                    "recommendation_scoring_mutated": False,
                }
            )
        raise AssertionError(f"Unexpected scalar SQL: {sql[:160]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class IndustryCompetitivePositioningTests(unittest.TestCase):
    def test_migration_creates_competitive_position_table_without_scoring_mutation(self) -> None:
        sql = Path("db/migrations/0022_industry_competitive_positioning.sql").read_text(encoding="utf-8")

        self.assertIn("create table if not exists research.industry_competitive_position", sql)
        self.assertIn("pricing_power_score numeric(5,4)", sql)
        self.assertIn("capacity_cycle_risk_score numeric(5,4)", sql)
        self.assertIn("key_strengths_json jsonb", sql)
        self.assertIn("check (competitive_position in", sql)
        self.assertNotIn("signal.recommendation_score_component", sql)
        self.assertNotIn("submitted_to_broker", sql)

    def test_preview_sql_is_read_only_and_reports_peer_coverage(self) -> None:
        sql = render_industry_competitive_positioning_preview_sql(as_of_date=date(2026, 5, 25))
        lowered = sql.lower()

        self.assertIn("-- industry competitive positioning preview", sql)
        self.assertIn("ref.peer_group_member", sql)
        self.assertIn("market.peer_relative_snapshot", sql)
        self.assertIn("research.industry_competitive_position", sql)
        self.assertIn("'2026-05-25'::date", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_upsert_sql_scores_porter_style_proxies_without_recommendation_mutation(self) -> None:
        sql = render_industry_competitive_positioning_upsert_sql(
            as_of_date=date(2026, 5, 25),
            source_run_id=9901,
        )

        self.assertIn("-- industry competitive positioning upsert", sql)
        self.assertIn("insert into research.industry_competitive_position", sql)
        self.assertIn("pricing_power_score", sql)
        self.assertIn("profitability_score", sql)
        self.assertIn("financial_strength_score", sql)
        self.assertIn("capacity_cycle_risk_score", sql)
        self.assertIn("buyer_power_risk_score", sql)
        self.assertIn("new_entry_threat_risk_score", sql)
        self.assertIn("sector_membership as", sql)
        self.assertIn("recommendation_scoring_mutated', false", sql)
        self.assertNotIn("signal.recommendation_score_component", sql)
        self.assertIn("9901::bigint", sql)

    def test_run_dry_run_reads_preview_without_writes(self) -> None:
        executor = FakeIndustryCompetitiveExecutor()

        report = run_industry_competitive_positioning(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            execute=False,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["report_name"], "industry_competitive_positioning")
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertFalse(report["broker_submission_allowed"])
        self.assertEqual(executor.non_query_sql, [])
        self.assertEqual(len(executor.scalar_sql), 1)

    def test_run_execute_records_pipeline_and_upsert_summary(self) -> None:
        executor = FakeIndustryCompetitiveExecutor(run_id=9902)

        report = run_industry_competitive_positioning(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            execute=True,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9902)
        self.assertEqual(report["upsert"]["position_count"], 5)  # type: ignore[index]
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("-- industry competitive positioning upsert", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])


if __name__ == "__main__":
    unittest.main()
