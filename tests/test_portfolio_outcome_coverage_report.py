from __future__ import annotations

import json
import unittest
from datetime import date
from decimal import Decimal

from stockanalysis.performance.coverage import (
    PortfolioOutcomeCoverageRow,
    build_portfolio_outcome_coverage_report,
    load_portfolio_outcome_coverage_report,
    load_portfolio_outcome_coverage_rows,
    render_portfolio_outcome_coverage_lookup_sql,
    render_portfolio_outcome_coverage_report_sql,
)


class FakeExecutor:
    def __init__(self) -> None:
        self.scalar_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- portfolio outcome coverage lookup"):
            return json.dumps(
                [
                    {
                        "portfolio_id": 3001,
                        "portfolio_name": "Long Term Paper",
                        "snapshot_date": "2024-11-01",
                        "measurement_end_date": "2024-12-02",
                        "instrument_id": 501,
                        "primary_symbol": "AAPL",
                        "market_value": "2229.10",
                        "position_weight": "0.0500",
                        "linked_thesis_id": 7001,
                        "thesis_title": "AAPL watch thesis via Annual Reporting",
                        "outcome_id": 8101,
                        "outcome_status": "working",
                        "success_grade": "pass",
                        "coverage_status": "covered",
                    },
                    {
                        "portfolio_id": 3001,
                        "portfolio_name": "Long Term Paper",
                        "snapshot_date": "2024-11-01",
                        "measurement_end_date": "2024-12-02",
                        "instrument_id": 502,
                        "primary_symbol": "MSFT",
                        "market_value": "900.00",
                        "position_weight": "0.0300",
                        "linked_thesis_id": 7002,
                        "thesis_title": "MSFT thesis",
                        "outcome_id": None,
                        "outcome_status": None,
                        "success_grade": None,
                        "coverage_status": "missing_outcome",
                    },
                    {
                        "portfolio_id": 3001,
                        "portfolio_name": "Long Term Paper",
                        "snapshot_date": "2024-11-01",
                        "measurement_end_date": "2024-12-02",
                        "instrument_id": 503,
                        "primary_symbol": "BABA",
                        "market_value": "298.50",
                        "position_weight": "0.0200",
                        "linked_thesis_id": None,
                        "thesis_title": None,
                        "outcome_id": None,
                        "outcome_status": None,
                        "success_grade": None,
                        "coverage_status": "missing_thesis",
                    },
                ]
            )
        if sql.startswith("-- portfolio outcome coverage report"):
            return json.dumps(
                {
                    "portfolio_id": 3001,
                    "portfolio_name": "Long Term Paper",
                    "snapshot_date": "2024-11-01",
                    "measurement_end_date": "2024-12-02",
                    "position_count": 3,
                    "status_counts": {
                        "covered": 1,
                        "missing_outcome": 1,
                        "missing_thesis": 1,
                        "missing_weight": 0,
                    },
                    "weight_by_status": {
                        "covered": "0.0500",
                        "missing_outcome": "0.0300",
                        "missing_thesis": "0.0200",
                        "missing_weight": "0.0000",
                    },
                    "cash_weight": "0.9000",
                    "coverage_ratio_by_weight": "0.5000",
                    "positions": [{"symbol": "MSFT", "coverage_status": "missing_outcome"}],
                }
            )
        raise AssertionError(f"Unexpected scalar SQL: {sql}")


class EmptyExecutor:
    def execute_scalar(self, sql: str) -> str:
        return "[]"


class PortfolioOutcomeCoverageReportTests(unittest.TestCase):
    def test_render_portfolio_outcome_coverage_lookup_sql(self) -> None:
        sql = render_portfolio_outcome_coverage_lookup_sql(
            portfolio_name="Long Term Paper",
            snapshot_date=date(2024, 11, 1),
            measurement_end_date=date(2024, 12, 2),
        )
        self.assertIn("portfolio.position_snapshot", sql)
        self.assertIn("performance.thesis_outcome", sql)
        self.assertIn("signal.investment_thesis", sql)
        self.assertIn("missing_outcome", sql)
        self.assertIn("missing_thesis", sql)
        self.assertIn("missing_weight", sql)

    def test_render_portfolio_outcome_coverage_report_sql_pages_positions_only(self) -> None:
        sql = render_portfolio_outcome_coverage_report_sql(
            portfolio_name="Long Term Paper",
            snapshot_date=date(2024, 11, 1),
            measurement_end_date=date(2024, 12, 2),
            position_limit=2,
            position_offset=1,
        )

        self.assertIn("-- portfolio outcome coverage report", sql)
        self.assertIn("coverage_summary as", sql)
        self.assertIn("position_page as", sql)
        self.assertIn("limit 2", sql)
        self.assertIn("offset 1", sql)

    def test_load_portfolio_outcome_coverage_rows(self) -> None:
        rows = load_portfolio_outcome_coverage_rows(
            config=type("Config", (), {})(),
            portfolio_name="Long Term Paper",
            snapshot_date=date(2024, 11, 1),
            measurement_end_date=date(2024, 12, 2),
            executor=FakeExecutor(),
        )
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0].primary_symbol, "AAPL")
        self.assertEqual(rows[0].coverage_status, "covered")
        self.assertEqual(rows[1].coverage_status, "missing_outcome")
        self.assertEqual(rows[2].coverage_status, "missing_thesis")

    def test_load_portfolio_outcome_coverage_rows_fails_when_empty(self) -> None:
        with self.assertRaises(ValueError):
            load_portfolio_outcome_coverage_rows(
                config=type("Config", (), {})(),
                portfolio_name="Long Term Paper",
                snapshot_date=date(2024, 11, 1),
                measurement_end_date=date(2024, 12, 2),
                executor=EmptyExecutor(),
            )

    def test_load_portfolio_outcome_coverage_rows_rejects_end_before_snapshot(self) -> None:
        with self.assertRaises(ValueError):
            load_portfolio_outcome_coverage_rows(
                config=type("Config", (), {})(),
                portfolio_name="Long Term Paper",
                snapshot_date=date(2024, 11, 1),
                measurement_end_date=date(2024, 10, 31),
                executor=EmptyExecutor(),
            )

    def test_build_portfolio_outcome_coverage_report(self) -> None:
        report = build_portfolio_outcome_coverage_report((_covered_row(), _missing_outcome_row(), _missing_thesis_row()))
        self.assertEqual(report["portfolio_name"], "Long Term Paper")
        self.assertEqual(report["position_count"], 3)
        self.assertEqual(
            report["status_counts"],
            {"covered": 1, "missing_outcome": 1, "missing_thesis": 1, "missing_weight": 0},
        )
        self.assertEqual(
            report["weight_by_status"],
            {"covered": "0.0500", "missing_outcome": "0.0300", "missing_thesis": "0.0200", "missing_weight": "0.0000"},
        )
        self.assertEqual(report["total_position_weight"], "0.1000")
        self.assertEqual(report["covered_weight"], "0.0500")
        self.assertEqual(report["cash_weight"], "0.9000")
        self.assertEqual(report["coverage_ratio_by_count"], "0.3333")
        self.assertEqual(report["coverage_ratio_by_weight"], "0.5000")

    def test_build_portfolio_outcome_coverage_report_nulls_cash_when_weight_missing(self) -> None:
        report = build_portfolio_outcome_coverage_report((_covered_row(), _missing_weight_row()))
        self.assertEqual(report["status_counts"]["missing_weight"], 1)
        self.assertEqual(report["cash_weight"], None)
        self.assertEqual(report["weight_by_status"]["missing_weight"], "0.0000")

    def test_load_portfolio_outcome_coverage_report_returns_summary(self) -> None:
        report = load_portfolio_outcome_coverage_report(
            config=type("Config", (), {})(),
            portfolio_name="Long Term Paper",
            snapshot_date=date(2024, 11, 1),
            measurement_end_date=date(2024, 12, 2),
            executor=FakeExecutor(),
        )
        self.assertEqual(report["position_count"], 3)
        self.assertEqual(report["status_counts"]["covered"], 1)

    def test_load_portfolio_outcome_coverage_report_supports_position_window(self) -> None:
        executor = FakeExecutor()

        report = load_portfolio_outcome_coverage_report(
            config=type("Config", (), {})(),
            portfolio_name="Long Term Paper",
            snapshot_date=date(2024, 11, 1),
            measurement_end_date=date(2024, 12, 2),
            position_limit=2,
            position_offset=1,
            executor=executor,
        )

        self.assertEqual(report["position_count"], 3)
        self.assertEqual(len(report["positions"]), 1)
        self.assertIn("limit 2", executor.scalar_sql[-1])
        self.assertIn("offset 1", executor.scalar_sql[-1])


def _covered_row() -> PortfolioOutcomeCoverageRow:
    return PortfolioOutcomeCoverageRow(
        portfolio_id=3001,
        portfolio_name="Long Term Paper",
        snapshot_date=date(2024, 11, 1),
        measurement_end_date=date(2024, 12, 2),
        instrument_id=501,
        primary_symbol="AAPL",
        market_value=Decimal("2229.10"),
        position_weight=Decimal("0.0500"),
        linked_thesis_id=7001,
        thesis_title="AAPL watch thesis via Annual Reporting",
        outcome_id=8101,
        outcome_status="working",
        success_grade="pass",
        coverage_status="covered",
    )


def _missing_outcome_row() -> PortfolioOutcomeCoverageRow:
    return PortfolioOutcomeCoverageRow(
        portfolio_id=3001,
        portfolio_name="Long Term Paper",
        snapshot_date=date(2024, 11, 1),
        measurement_end_date=date(2024, 12, 2),
        instrument_id=502,
        primary_symbol="MSFT",
        market_value=Decimal("900.00"),
        position_weight=Decimal("0.0300"),
        linked_thesis_id=7002,
        thesis_title="MSFT thesis",
        outcome_id=None,
        outcome_status=None,
        success_grade=None,
        coverage_status="missing_outcome",
    )


def _missing_thesis_row() -> PortfolioOutcomeCoverageRow:
    return PortfolioOutcomeCoverageRow(
        portfolio_id=3001,
        portfolio_name="Long Term Paper",
        snapshot_date=date(2024, 11, 1),
        measurement_end_date=date(2024, 12, 2),
        instrument_id=503,
        primary_symbol="BABA",
        market_value=Decimal("298.50"),
        position_weight=Decimal("0.0200"),
        linked_thesis_id=None,
        thesis_title=None,
        outcome_id=None,
        outcome_status=None,
        success_grade=None,
        coverage_status="missing_thesis",
    )


def _missing_weight_row() -> PortfolioOutcomeCoverageRow:
    return PortfolioOutcomeCoverageRow(
        portfolio_id=3001,
        portfolio_name="Long Term Paper",
        snapshot_date=date(2024, 11, 1),
        measurement_end_date=date(2024, 12, 2),
        instrument_id=504,
        primary_symbol="NVDA",
        market_value=Decimal("1000.00"),
        position_weight=None,
        linked_thesis_id=7004,
        thesis_title="NVDA thesis",
        outcome_id=None,
        outcome_status=None,
        success_grade=None,
        coverage_status="missing_weight",
    )
