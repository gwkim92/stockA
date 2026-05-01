from __future__ import annotations

import json
import unittest

from stockanalysis.signal.portfolio_remediation_queue import (
    load_portfolio_remediation_queue,
    render_portfolio_remediation_queue_sql,
)


class FakeQueueExecutor:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.scalar_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        return json.dumps(self.payload)


class PortfolioRemediationQueueTests(unittest.TestCase):
    def test_load_portfolio_remediation_queue_returns_payload(self) -> None:
        executor = FakeQueueExecutor(
            {
                "report_name": "portfolio_remediation_queue",
                "portfolio_name": "Long Term Paper",
                "queue_item_count": 1,
                "remediation_type_counts": {"thesis_remediation": 1},
                "action_counts": {"needs_thesis_review": 1},
                "items": [
                    {
                        "symbol": "BABA",
                        "action": "needs_thesis_review",
                        "remediation_type": "thesis_remediation",
                    }
                ],
            }
        )

        payload = load_portfolio_remediation_queue(
            config=type("Config", (), {})(),
            portfolio_name="Long Term Paper",
            limit=5,
            executor=executor,
        )

        self.assertEqual(payload["report_name"], "portfolio_remediation_queue")
        self.assertEqual(payload["queue_item_count"], 1)
        self.assertIn("limit 5", executor.scalar_sql[0])

    def test_load_portfolio_remediation_queue_rejects_non_positive_limit(self) -> None:
        with self.assertRaises(ValueError):
            load_portfolio_remediation_queue(
                config=type("Config", (), {})(),
                portfolio_name="Long Term Paper",
                limit=0,
                executor=FakeQueueExecutor({}),
            )

    def test_render_portfolio_remediation_queue_sql_adds_optional_filters(self) -> None:
        sql = render_portfolio_remediation_queue_sql(
            portfolio_name="Long Term Paper",
            limit=10,
            review_source="deterministic_bootstrap",
            action="needs_thesis_review",
            remediation_type="thesis_remediation",
        )

        self.assertIn("portfolio.review_item", sql)
        self.assertIn("portfolio.portfolio_name = 'Long Term Paper'", sql)
        self.assertIn("review.review_source = 'deterministic_bootstrap'", sql)
        self.assertIn("item.action = 'needs_thesis_review'", sql)
        self.assertIn("remediation_type = 'thesis_remediation'", sql)
        self.assertIn("then 'thesis_remediation'", sql)
        self.assertIn("then 'performance_outcome_runner'", sql)
        self.assertIn("limit 10", sql)

