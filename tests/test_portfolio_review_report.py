from __future__ import annotations

import json
import unittest

from stockanalysis.signal.portfolio_review_report import (
    load_portfolio_review_run_history,
    render_portfolio_review_run_history_sql,
)


class FakeReportExecutor:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.scalar_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        return json.dumps(self.payload)


class PortfolioReviewReportTests(unittest.TestCase):
    def test_load_portfolio_review_run_history_returns_payload(self) -> None:
        executor = FakeReportExecutor(
            {
                "report_name": "portfolio_review_run_history",
                "portfolio_name": "Long Term Paper",
                "review_count": 1,
                "risk_counts": {"watch": 1},
                "action_counts": {"monitor": 1, "needs_thesis_review": 1},
                "attention_item_count": 1,
                "reviews": [
                    {
                        "portfolio_review_id": 6001,
                        "risk_level": "watch",
                        "attention_items": [{"symbol": "BABA", "action": "needs_thesis_review"}],
                    }
                ],
            }
        )

        payload = load_portfolio_review_run_history(
            config=type("Config", (), {})(),
            portfolio_name="Long Term Paper",
            limit=5,
            executor=executor,
        )

        self.assertEqual(payload["report_name"], "portfolio_review_run_history")
        self.assertEqual(payload["portfolio_name"], "Long Term Paper")
        self.assertEqual(payload["attention_item_count"], 1)
        self.assertIn("limit 5", executor.scalar_sql[0])

    def test_load_portfolio_review_run_history_rejects_non_positive_limit(self) -> None:
        with self.assertRaises(ValueError):
            load_portfolio_review_run_history(
                config=type("Config", (), {})(),
                portfolio_name="Long Term Paper",
                limit=0,
                executor=FakeReportExecutor({}),
            )

    def test_render_portfolio_review_run_history_sql_adds_optional_filters(self) -> None:
        sql = render_portfolio_review_run_history_sql(
            portfolio_name="Long Term Paper",
            limit=10,
            review_source="deterministic_bootstrap",
            risk_level="watch",
            action="needs_thesis_review",
        )

        self.assertIn("portfolio.review", sql)
        self.assertIn("portfolio.review_item", sql)
        self.assertIn("ops.pipeline_run", sql)
        self.assertIn("portfolio.portfolio_name = 'Long Term Paper'", sql)
        self.assertIn("review.review_source = 'deterministic_bootstrap'", sql)
        self.assertIn("review.risk_level = 'watch'", sql)
        self.assertIn("item_filter.action = 'needs_thesis_review'", sql)
        self.assertIn("limit 10", sql)

