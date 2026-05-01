from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

from stockanalysis.signal.portfolio_remediation_daily import run_portfolio_remediation_daily_automation


class FakeDailyExecutor:
    def __init__(self, scalar_results: list[str]) -> None:
        self.scalar_results = scalar_results
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        return self.scalar_results.pop(0)

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class PortfolioRemediationDailyTests(unittest.TestCase):
    def test_run_portfolio_remediation_daily_automation_returns_summary(self) -> None:
        executor = FakeDailyExecutor(["501"])
        review_summary = {
            "run_id": 601,
            "portfolio_review_id": 7001,
            "review_item_count": 2,
            "action_counts": {"monitor": 1, "needs_thesis_review": 1},
        }
        ticket_bootstrap_summary = {
            "report_name": "portfolio_remediation_ticket_bootstrap",
            "run_id": 602,
            "ticket_count": 1,
        }
        ticket_report = {
            "report_name": "portfolio_remediation_ticket_report",
            "ticket_count": 1,
            "status_counts": {"open": 1},
            "tickets": [{"symbol": "BABA", "status": "open"}],
        }

        with patch(
            "stockanalysis.signal.portfolio_remediation_daily.run_portfolio_review_bootstrap",
            return_value=review_summary,
        ) as review_mock:
            with patch(
                "stockanalysis.signal.portfolio_remediation_daily.run_portfolio_remediation_ticket_bootstrap",
                return_value=ticket_bootstrap_summary,
            ) as ticket_mock:
                with patch(
                    "stockanalysis.signal.portfolio_remediation_daily.load_portfolio_remediation_ticket_report",
                    return_value=ticket_report,
                ) as report_mock:
                    summary = run_portfolio_remediation_daily_automation(
                        config=type("Config", (), {})(),
                        portfolio_name="Long Term Paper",
                        as_of_date=date(2024, 11, 1),
                        strategy_name="long_term_core",
                        horizon_type="long_term",
                        universe_version="fixture-v1",
                        coverage_measurement_end_date=date(2024, 12, 2),
                        ticket_limit=5,
                        executor=executor,
                    )

        self.assertEqual(summary["report_name"], "portfolio_remediation_daily_automation")
        self.assertEqual(summary["run_id"], 501)
        self.assertEqual(summary["ticket_report"], ticket_report)
        self.assertEqual(
            [step["name"] for step in summary["steps"]],
            [
                "portfolio_review_bootstrap",
                "portfolio_remediation_ticket_bootstrap",
                "portfolio_remediation_ticket_report",
            ],
        )
        self.assertIn("portfolio_remediation_daily_automation", executor.scalar_sql[0])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])
        self.assertIs(review_mock.call_args.kwargs["executor"], executor)
        self.assertIs(ticket_mock.call_args.kwargs["executor"], executor)
        self.assertIs(report_mock.call_args.kwargs["executor"], executor)
        self.assertEqual(review_mock.call_args.kwargs["coverage_measurement_end_date"], date(2024, 12, 2))
        self.assertEqual(ticket_mock.call_args.kwargs["limit"], 5)
        self.assertEqual(report_mock.call_args.kwargs["status"], "open")

    def test_run_portfolio_remediation_daily_automation_rejects_non_positive_limit(self) -> None:
        with self.assertRaises(ValueError):
            run_portfolio_remediation_daily_automation(
                config=type("Config", (), {})(),
                portfolio_name="Long Term Paper",
                as_of_date=date(2024, 11, 1),
                strategy_name="long_term_core",
                horizon_type="long_term",
                universe_version="fixture-v1",
                ticket_limit=0,
                executor=FakeDailyExecutor([]),
            )

    def test_run_portfolio_remediation_daily_automation_marks_failed_when_step_fails(self) -> None:
        executor = FakeDailyExecutor(["502"])
        with patch(
            "stockanalysis.signal.portfolio_remediation_daily.run_portfolio_review_bootstrap",
            side_effect=ValueError("missing portfolio review candidates"),
        ):
            with self.assertRaises(ValueError):
                run_portfolio_remediation_daily_automation(
                    config=type("Config", (), {})(),
                    portfolio_name="Long Term Paper",
                    as_of_date=date(2024, 11, 1),
                    strategy_name="long_term_core",
                    horizon_type="long_term",
                    universe_version="fixture-v1",
                    executor=executor,
                )

        self.assertIn("status = 'failed'", executor.non_query_sql[0])
        self.assertIn("missing portfolio review candidates", executor.non_query_sql[0])


if __name__ == "__main__":
    unittest.main()
