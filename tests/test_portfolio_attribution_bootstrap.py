from __future__ import annotations

import json
import unittest
from datetime import date
from decimal import Decimal

from stockanalysis.performance.attribution import (
    PortfolioAttributionCandidate,
    build_portfolio_attribution,
    load_portfolio_attribution_candidates,
    render_portfolio_attribution_candidate_lookup_sql,
    render_portfolio_attribution_upsert_sql,
    run_portfolio_attribution_bootstrap,
)


class FakeExecutor:
    def __init__(self, *, run_id: int = 8201, fail_on_upsert: bool = False) -> None:
        self.run_id = run_id
        self.fail_on_upsert = fail_on_upsert
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- portfolio attribution candidate lookup"):
            return json.dumps(
                [
                    {
                        "portfolio_id": 3001,
                        "portfolio_name": "Long Term Paper",
                        "snapshot_date": "2024-11-01",
                        "measurement_start_date": "2024-11-01",
                        "measurement_end_date": "2024-12-02",
                        "instrument_id": 501,
                        "primary_symbol": "AAPL",
                        "position_weight": "0.0500",
                        "linked_thesis_id": 7001,
                        "thesis_title": "AAPL watch thesis via Annual Reporting",
                        "primary_node_id": 401,
                        "node_code": "ANNUAL_REPORTING",
                        "node_name": "Annual Reporting",
                        "recommendation_id": 9001,
                        "absolute_return_pct": "0.100000",
                        "benchmark_return_pct": "0.040000",
                        "alpha_pct": "0.060000",
                        "success_grade": "pass",
                    }
                ]
            )
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if "insert into performance.attribution_run" in sql:
            if self.fail_on_upsert:
                raise RuntimeError("boom")
            return json.dumps(
                {
                    "attribution_run_id": 6101,
                    "deleted_component_count": 0,
                    "component_count": 3,
                }
            )
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class EmptyExecutor:
    def execute_scalar(self, sql: str) -> str:
        return "[]"


class PortfolioAttributionBootstrapTests(unittest.TestCase):
    def test_render_portfolio_attribution_candidate_lookup_sql(self) -> None:
        sql = render_portfolio_attribution_candidate_lookup_sql(
            portfolio_name="Long Term Paper",
            snapshot_date=date(2024, 11, 1),
            measurement_end_date=date(2024, 12, 2),
            methodology="position_weighted_alpha_v1",
        )
        self.assertIn("portfolio.position_snapshot", sql)
        self.assertIn("performance.thesis_outcome", sql)
        self.assertIn("signal.investment_thesis", sql)
        self.assertIn("ref.classification_node", sql)
        self.assertIn("2024-12-02", sql)
        self.assertIn("position_weighted_alpha_v1", sql)

    def test_load_portfolio_attribution_candidates(self) -> None:
        rows = load_portfolio_attribution_candidates(
            config=type("Config", (), {})(),
            portfolio_name="Long Term Paper",
            snapshot_date=date(2024, 11, 1),
            measurement_end_date=date(2024, 12, 2),
            executor=FakeExecutor(),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].primary_symbol, "AAPL")
        self.assertEqual(rows[0].position_weight, Decimal("0.0500"))
        self.assertEqual(rows[0].alpha_pct, Decimal("0.060000"))

    def test_load_portfolio_attribution_candidates_fails_when_empty(self) -> None:
        with self.assertRaises(ValueError):
            load_portfolio_attribution_candidates(
                config=type("Config", (), {})(),
                portfolio_name="Long Term Paper",
                snapshot_date=date(2024, 11, 1),
                measurement_end_date=date(2024, 12, 2),
                executor=EmptyExecutor(),
            )

    def test_load_portfolio_attribution_candidates_rejects_end_before_snapshot(self) -> None:
        with self.assertRaises(ValueError):
            load_portfolio_attribution_candidates(
                config=type("Config", (), {})(),
                portfolio_name="Long Term Paper",
                snapshot_date=date(2024, 11, 1),
                measurement_end_date=date(2024, 10, 31),
                executor=EmptyExecutor(),
            )

    def test_build_portfolio_attribution_components(self) -> None:
        header, component_rows = build_portfolio_attribution((_candidate(),))
        self.assertEqual(header.portfolio_name, "Long Term Paper")
        self.assertEqual(len(component_rows), 3)

        components = {(row.component_type, row.component_key): row for row in component_rows}
        security = components[("security_selection", "AAPL")]
        self.assertEqual(security.weight, Decimal("0.0500"))
        self.assertEqual(security.return_pct, Decimal("0.100000"))
        self.assertEqual(security.benchmark_return_pct, Decimal("0.040000"))
        self.assertEqual(security.alpha_pct, Decimal("0.060000"))
        self.assertEqual(security.contribution_bps, Decimal("30.0000"))

        theme = components[("theme_exposure", "ANNUAL_REPORTING")]
        self.assertEqual(theme.weight, Decimal("0.0500"))
        self.assertEqual(theme.alpha_pct, Decimal("0.060000"))
        self.assertEqual(theme.contribution_bps, Decimal("30.0000"))

        cash = components[("cash_timing", "CASH")]
        self.assertEqual(cash.weight, Decimal("0.9500"))
        self.assertEqual(cash.contribution_bps, Decimal("0.0000"))

    def test_render_portfolio_attribution_upsert_sql(self) -> None:
        header, component_rows = build_portfolio_attribution((_candidate(),))
        sql = render_portfolio_attribution_upsert_sql(header, component_rows, source_run_id=82)
        self.assertIn("insert into performance.attribution_run", sql)
        self.assertIn("insert into performance.attribution_component", sql)
        self.assertIn("on conflict (portfolio_id, snapshot_date, measurement_end_date, methodology) do update", sql)
        self.assertIn("'security_selection'::text", sql)
        self.assertIn("'theme_exposure'::text", sql)
        self.assertIn("'cash_timing'::text", sql)
        self.assertIn("30.0000::numeric", sql)
        self.assertIn("82::bigint", sql)

    def test_run_portfolio_attribution_bootstrap_records_pipeline_run_and_summary(self) -> None:
        executor = FakeExecutor(run_id=8202)
        summary = run_portfolio_attribution_bootstrap(
            config=type("Config", (), {})(),
            portfolio_name="Long Term Paper",
            snapshot_date=date(2024, 11, 1),
            measurement_end_date=date(2024, 12, 2),
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 8202)
        self.assertEqual(summary["attribution_run_id"], 6101)
        self.assertEqual(summary["candidate_count"], 1)
        self.assertEqual(summary["component_count"], 3)
        self.assertEqual(summary["component_type_counts"], {"security_selection": 1, "theme_exposure": 1, "cash_timing": 1})
        self.assertEqual(
            summary["contribution_bps_by_type"],
            {"security_selection": "30.0000", "theme_exposure": "30.0000", "cash_timing": "0.0000"},
        )
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("insert into performance.attribution_run", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])

    def test_run_portfolio_attribution_bootstrap_marks_pipeline_run_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=8203, fail_on_upsert=True)
        with self.assertRaises(RuntimeError):
            run_portfolio_attribution_bootstrap(
                config=type("Config", (), {})(),
                portfolio_name="Long Term Paper",
                snapshot_date=date(2024, 11, 1),
                measurement_end_date=date(2024, 12, 2),
                executor=executor,
            )
        self.assertIn("status = 'failed'", executor.non_query_sql[-1])


def _candidate() -> PortfolioAttributionCandidate:
    return PortfolioAttributionCandidate(
        portfolio_id=3001,
        portfolio_name="Long Term Paper",
        snapshot_date=date(2024, 11, 1),
        measurement_start_date=date(2024, 11, 1),
        measurement_end_date=date(2024, 12, 2),
        instrument_id=501,
        primary_symbol="AAPL",
        position_weight=Decimal("0.0500"),
        linked_thesis_id=7001,
        thesis_title="AAPL watch thesis via Annual Reporting",
        primary_node_id=401,
        node_code="ANNUAL_REPORTING",
        node_name="Annual Reporting",
        recommendation_id=9001,
        absolute_return_pct=Decimal("0.100000"),
        benchmark_return_pct=Decimal("0.040000"),
        alpha_pct=Decimal("0.060000"),
        success_grade="pass",
    )
