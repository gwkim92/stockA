from __future__ import annotations

import unittest
from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.correlation_analysis import (
    ASSET_CORRELATION_PIPELINE_NAME,
    parse_lookback_days,
    render_asset_correlation_snapshot_upsert_sql,
    run_correlation_analysis,
)


class CorrelationAnalysisTest(unittest.TestCase):
    def test_parse_lookback_days_accepts_repeated_and_csv_values(self) -> None:
        self.assertEqual(parse_lookback_days(["20,60", "120"]), (20, 60, 120))

    def test_parse_lookback_days_rejects_tiny_windows(self) -> None:
        with self.assertRaises(ValueError):
            parse_lookback_days(["5"])

    def test_snapshot_sql_uses_returns_and_no_causal_claim_policy(self) -> None:
        sql = render_asset_correlation_snapshot_upsert_sql(
            as_of_date=date(2026, 6, 14),
            lookback_days=(20, 60, 120),
            source_run_id=77,
        )

        self.assertIn("market.daily_price_bar", sql)
        self.assertIn("market.market_indicator_observation", sql)
        self.assertIn("corr(primary_return, comparison_return)", sql)
        self.assertIn("covar_samp(primary_return, comparison_return)", sql)
        self.assertIn("signal.asset_correlation_snapshot", sql)
        self.assertIn("delete from signal.asset_correlation_snapshot", sql)
        self.assertIn("co_movement_only_not_causality", sql)
        self.assertIn("'causal_claim', false", sql)
        self.assertIn("lower(comparison_asset.indicator_code) = lower(primary_asset.display_name)", sql)
        self.assertIn("equivalent_indicator.asset_type = 'indicator'", sql)
        self.assertIn("on conflict (as_of_date, lookback_days, primary_asset_key, comparison_asset_key)", sql)

    def test_run_correlation_analysis_records_guardrails(self) -> None:
        executor = _FakeCorrelationExecutor()

        report = run_correlation_analysis(
            config=RuntimeConfig(psql_command="psql postgresql://example/db"),
            as_of_date=date(2026, 6, 14),
            lookback_days=(20, 60),
            execute=True,
            executor=executor,
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 42)
        self.assertEqual(report["summary"]["snapshot_count"], 12)
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertFalse(report["automatic_weight_change_allowed"])
        self.assertFalse(report["broker_submit_allowed"])
        self.assertEqual(report["order_boundary"], "read_only_no_order")
        self.assertTrue(any(ASSET_CORRELATION_PIPELINE_NAME in sql for sql in executor.scalar_sql))
        self.assertTrue(any("signal.asset_correlation_snapshot" in sql for sql in executor.non_query_sql))


class _FakeCorrelationExecutor:
    def __init__(self) -> None:
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "returning run_id" in sql:
            return "42"
        return (
            '{"snapshot_count":12,"primary_asset_count":4,'
            '"comparison_asset_count":8,"strong_relationship_count":2}'
        )

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


if __name__ == "__main__":
    unittest.main()
