from __future__ import annotations

import json
import unittest

from stockanalysis.signal.portfolio_remediation_ticket import (
    load_portfolio_remediation_ticket_report,
    render_portfolio_remediation_ticket_bootstrap_sql,
    render_portfolio_remediation_ticket_report_sql,
    render_portfolio_remediation_ticket_update_sql,
    run_portfolio_remediation_ticket_bootstrap,
    run_portfolio_remediation_ticket_update,
)


class FakeTicketExecutor:
    def __init__(self, scalar_results: list[str]) -> None:
        self.scalar_results = scalar_results
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        return self.scalar_results.pop(0)

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class PortfolioRemediationTicketTests(unittest.TestCase):
    def test_run_portfolio_remediation_ticket_update_returns_summary(self) -> None:
        executor = FakeTicketExecutor(
            [
                "91",
                json.dumps(
                    {
                        "report_name": "portfolio_remediation_ticket_update",
                        "portfolio_name": "Long Term Paper",
                        "ticket_id": 7001,
                        "status": "resolved",
                        "updated_count": 1,
                        "ticket": {
                            "remediation_ticket_id": 7001,
                            "symbol": "BABA",
                            "status": "resolved",
                            "resolved_at": "2026-04-29T12:00:00+09:00",
                        },
                    }
                ),
            ]
        )

        summary = run_portfolio_remediation_ticket_update(
            config=type("Config", (), {})(),
            portfolio_name="Long Term Paper",
            ticket_id=7001,
            status="resolved",
            executor=executor,
        )

        self.assertEqual(summary["run_id"], 91)
        self.assertEqual(summary["report_name"], "portfolio_remediation_ticket_update")
        self.assertEqual(summary["updated_count"], 1)
        self.assertIn("portfolio_remediation_ticket_update", executor.scalar_sql[0])
        self.assertIn("portfolio remediation ticket status update", executor.scalar_sql[1])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])

    def test_run_portfolio_remediation_ticket_update_rejects_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            run_portfolio_remediation_ticket_update(
                config=type("Config", (), {})(),
                portfolio_name="Long Term Paper",
                ticket_id=0,
                status="resolved",
                executor=FakeTicketExecutor([]),
            )
        with self.assertRaises(ValueError):
            run_portfolio_remediation_ticket_update(
                config=type("Config", (), {})(),
                portfolio_name="Long Term Paper",
                ticket_id=7001,
                status="done",
                executor=FakeTicketExecutor([]),
            )

    def test_run_portfolio_remediation_ticket_update_fails_when_ticket_missing(self) -> None:
        executor = FakeTicketExecutor(
            [
                "92",
                json.dumps(
                    {
                        "report_name": "portfolio_remediation_ticket_update",
                        "portfolio_name": "Long Term Paper",
                        "ticket_id": 9999,
                        "status": "resolved",
                        "updated_count": 0,
                        "ticket": None,
                    }
                ),
            ]
        )

        with self.assertRaises(ValueError):
            run_portfolio_remediation_ticket_update(
                config=type("Config", (), {})(),
                portfolio_name="Long Term Paper",
                ticket_id=9999,
                status="resolved",
                executor=executor,
            )

        self.assertIn("status = 'failed'", executor.non_query_sql[0])

    def test_render_portfolio_remediation_ticket_update_sql_sets_resolved_at_by_status(self) -> None:
        resolved_sql = render_portfolio_remediation_ticket_update_sql(
            portfolio_name="Long Term Paper",
            ticket_id=7001,
            status="resolved",
        )
        open_sql = render_portfolio_remediation_ticket_update_sql(
            portfolio_name="Long Term Paper",
            ticket_id=7001,
            status="open",
        )

        self.assertIn("update portfolio.remediation_ticket", resolved_sql)
        self.assertIn("portfolio.portfolio_name = 'Long Term Paper'", resolved_sql)
        self.assertIn("ticket.remediation_ticket_id = 7001", resolved_sql)
        self.assertIn("status = 'resolved'", resolved_sql)
        self.assertIn("resolved_at = now()", resolved_sql)
        self.assertIn("'report_name', 'portfolio_remediation_ticket_update'", resolved_sql)
        self.assertIn("resolved_at = null::timestamptz", open_sql)

    def test_load_portfolio_remediation_ticket_report_returns_payload(self) -> None:
        executor = FakeTicketExecutor(
            [
                json.dumps(
                    {
                        "report_name": "portfolio_remediation_ticket_report",
                        "portfolio_name": "Long Term Paper",
                        "ticket_count": 1,
                        "status_counts": {"open": 1},
                        "remediation_type_counts": {"thesis_remediation": 1},
                        "action_counts": {"needs_thesis_review": 1},
                        "tickets": [{"symbol": "BABA", "status": "open"}],
                    }
                )
            ]
        )

        payload = load_portfolio_remediation_ticket_report(
            config=type("Config", (), {})(),
            portfolio_name="Long Term Paper",
            limit=5,
            executor=executor,
        )

        self.assertEqual(payload["report_name"], "portfolio_remediation_ticket_report")
        self.assertEqual(payload["ticket_count"], 1)
        self.assertIn("portfolio.remediation_ticket", executor.scalar_sql[0])
        self.assertIn("ticket.status = 'open'", executor.scalar_sql[0])
        self.assertIn("limit 5", executor.scalar_sql[0])
        self.assertIn("offset 0", executor.scalar_sql[0])

    def test_load_portfolio_remediation_ticket_report_all_status_removes_status_filter(self) -> None:
        executor = FakeTicketExecutor(
            [
                json.dumps(
                    {
                        "report_name": "portfolio_remediation_ticket_report",
                        "ticket_count": 0,
                        "tickets": [],
                    }
                )
            ]
        )

        load_portfolio_remediation_ticket_report(
            config=type("Config", (), {})(),
            portfolio_name="Long Term Paper",
            status="all",
            executor=executor,
        )

        self.assertNotIn("ticket.status =", executor.scalar_sql[0])
        self.assertIn("'status_filter', null", executor.scalar_sql[0])

    def test_load_portfolio_remediation_ticket_report_rejects_non_positive_limit(self) -> None:
        with self.assertRaises(ValueError):
            load_portfolio_remediation_ticket_report(
                config=type("Config", (), {})(),
                portfolio_name="Long Term Paper",
                limit=0,
                executor=FakeTicketExecutor([]),
            )

    def test_load_portfolio_remediation_ticket_report_rejects_negative_offset(self) -> None:
        with self.assertRaises(ValueError):
            load_portfolio_remediation_ticket_report(
                config=type("Config", (), {})(),
                portfolio_name="Long Term Paper",
                limit=5,
                offset=-1,
                executor=FakeTicketExecutor([]),
            )

    def test_render_portfolio_remediation_ticket_report_sql_adds_optional_filters(self) -> None:
        sql = render_portfolio_remediation_ticket_report_sql(
            portfolio_name="Long Term Paper",
            limit=10,
            status="in_progress",
            action="needs_thesis_review",
            remediation_type="thesis_remediation",
            suggested_runner="thesis_or_position_link_review",
        )

        self.assertIn("portfolio.remediation_ticket", sql)
        self.assertIn("portfolio.portfolio_name = 'Long Term Paper'", sql)
        self.assertIn("ticket.status = 'in_progress'", sql)
        self.assertIn("ticket.action = 'needs_thesis_review'", sql)
        self.assertIn("ticket.remediation_type = 'thesis_remediation'", sql)
        self.assertIn("ticket.suggested_runner = 'thesis_or_position_link_review'", sql)
        self.assertIn("'report_name', 'portfolio_remediation_ticket_report'", sql)
        self.assertIn("'source_run_status', source_run_status", sql)
        self.assertIn("limit 10", sql)
        self.assertIn("offset 0", sql)

    def test_render_portfolio_remediation_ticket_report_sql_adds_offset(self) -> None:
        sql = render_portfolio_remediation_ticket_report_sql(
            portfolio_name="Long Term Paper",
            limit=5,
            offset=3,
            status="open",
        )

        self.assertIn("filtered_tickets as", sql)
        self.assertIn("selected_tickets as", sql)
        self.assertIn("'ticket_count', (select count(*) from filtered_tickets)", sql)
        self.assertIn("limit 5", sql)
        self.assertIn("offset 3", sql)

    def test_run_portfolio_remediation_ticket_bootstrap_returns_summary(self) -> None:
        executor = FakeTicketExecutor(
            [
                "77",
                json.dumps(
                    {
                        "report_name": "portfolio_remediation_ticket_bootstrap",
                        "portfolio_name": "Long Term Paper",
                        "ticket_count": 1,
                        "remediation_type_counts": {"thesis_remediation": 1},
                        "action_counts": {"needs_thesis_review": 1},
                        "tickets": [
                            {
                                "symbol": "BABA",
                                "status": "open",
                                "remediation_type": "thesis_remediation",
                            }
                        ],
                    }
                ),
            ]
        )

        summary = run_portfolio_remediation_ticket_bootstrap(
            config=type("Config", (), {})(),
            portfolio_name="Long Term Paper",
            limit=5,
            executor=executor,
        )

        self.assertEqual(summary["run_id"], 77)
        self.assertEqual(summary["report_name"], "portfolio_remediation_ticket_bootstrap")
        self.assertEqual(summary["ticket_count"], 1)
        self.assertIn("portfolio_remediation_ticket_bootstrap", executor.scalar_sql[0])
        self.assertIn("insert into portfolio.remediation_ticket", executor.scalar_sql[1])
        self.assertIn("limit 5", executor.scalar_sql[1])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])

    def test_run_portfolio_remediation_ticket_bootstrap_rejects_non_positive_limit(self) -> None:
        with self.assertRaises(ValueError):
            run_portfolio_remediation_ticket_bootstrap(
                config=type("Config", (), {})(),
                portfolio_name="Long Term Paper",
                limit=0,
                executor=FakeTicketExecutor([]),
            )

    def test_render_portfolio_remediation_ticket_bootstrap_sql_adds_optional_filters(self) -> None:
        sql = render_portfolio_remediation_ticket_bootstrap_sql(
            portfolio_name="Long Term Paper",
            limit=10,
            source_run_id=88,
            review_source="deterministic_bootstrap",
            action="needs_thesis_review",
            remediation_type="thesis_remediation",
        )

        self.assertIn("portfolio.review_item", sql)
        self.assertIn("insert into portfolio.remediation_ticket", sql)
        self.assertIn("portfolio.portfolio_name = 'Long Term Paper'", sql)
        self.assertIn("review.review_source = 'deterministic_bootstrap'", sql)
        self.assertIn("item.action = 'needs_thesis_review'", sql)
        self.assertIn("remediation_type = 'thesis_remediation'", sql)
        self.assertIn("on conflict (portfolio_review_id, instrument_id, action, remediation_type)", sql)
        self.assertIn("source_run_id = excluded.source_run_id", sql)
        self.assertIn("88::bigint", sql)
        self.assertIn("limit 10", sql)


if __name__ == "__main__":
    unittest.main()
