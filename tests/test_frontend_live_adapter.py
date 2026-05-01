from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone

from stockanalysis.frontend.live_adapter import (
    FrontendLiveUnavailableError,
    FrontendLiveUnsupportedPathError,
    resolve_live_frontend_response,
)


class FakeLiveExecutor:
    def __init__(self) -> None:
        self.scalar_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- frontend dashboard state lookup"):
            return json.dumps(
                {
                    "portfolio_name": "Long Term Paper",
                    "as_of_date": "2024-11-01",
                    "daily_automation": "succeeded",
                    "latest_run_id": 9101,
                    "failed_pipeline_count": 0,
                    "open_ticket_count": 1,
                    "critical_blind_spot_count": 1,
                    "missing_thesis_count": 1,
                    "missing_outcome_count": 0,
                    "top_actions": [
                        {
                            "symbol": "BABA",
                            "action": "needs_thesis_review",
                            "reason": "coverage status missing_thesis",
                            "suggested_runner": "thesis_or_position_link_review",
                            "risk_level": "high",
                        }
                    ],
                    "latest_metrics": {
                        "covered_weight": "0.0500",
                        "missing_thesis_weight": "0.0300",
                        "cash_weight": "0.9200",
                        "weight_coverage_ratio": "0.6250",
                    },
                }
            )
        if sql.startswith("-- frontend data health state lookup"):
            return json.dumps(
                {
                    "overall_status": "attention_required",
                    "as_of_date": "2024-11-01",
                    "pipeline_runs": [
                        {
                            "pipeline_name": "portfolio_remediation_daily_automation",
                            "latest_status": "succeeded",
                            "latest_run_id": 9101,
                            "finished_at": "2024-11-01T23:30:00+00:00",
                        }
                    ],
                    "latest_artifact_root": "",
                    "freshness": [
                        {
                            "dataset": "market.daily_price_bar",
                            "status": "observed",
                            "latest_observation_date": "2024-12-02",
                        },
                        {
                            "dataset": "portfolio.position_snapshot",
                            "status": "observed",
                            "latest_observation_date": "2024-11-01",
                        },
                    ],
                    "open_gates": [
                        "production_api_server",
                        "auth_rbac",
                        "alert_destination",
                        "actual_db_backed_frontend_live_smoke",
                    ],
                }
            )
        if sql.startswith("-- portfolio remediation ticket report"):
            return json.dumps(
                {
                    "report_name": "portfolio_remediation_ticket_report",
                    "portfolio_name": "Long Term Paper",
                    "limit": 50,
                    "status_filter": "open",
                    "ticket_count": 1,
                    "status_counts": {"open": 1},
                    "remediation_type_counts": {"thesis_remediation": 1},
                    "action_counts": {"needs_thesis_review": 1},
                    "tickets": [
                        {
                            "remediation_ticket_id": 42,
                            "portfolio_review_id": 6001,
                            "instrument_id": 502,
                            "portfolio_name": "Long Term Paper",
                            "review_date": "2024-11-01",
                            "review_source": "coverage_gate",
                            "symbol": "BABA",
                            "action": "needs_thesis_review",
                            "remediation_type": "thesis_remediation",
                            "suggested_runner": "thesis_or_position_link_review",
                            "suggested_next_step": "Create or link an active thesis before the next portfolio review.",
                            "status": "open",
                            "priority": 1,
                            "risk_level": "high",
                            "health_score": "0.0000",
                            "current_weight": "0.0300",
                            "recommended_weight": None,
                            "reason": "coverage status missing_thesis",
                            "source_run_id": 9101,
                            "source_run_status": "succeeded",
                            "opened_at": "2024-11-01T23:30:00+00:00",
                            "updated_at": "2024-11-01T23:30:00+00:00",
                            "last_seen_at": "2024-11-01T23:30:00+00:00",
                            "resolved_at": None,
                        }
                    ],
                }
            )
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
                        "primary_symbol": "BABA",
                        "market_value": "298.50",
                        "position_weight": "0.0300",
                        "linked_thesis_id": None,
                        "thesis_title": None,
                        "outcome_id": None,
                        "outcome_status": None,
                        "success_grade": None,
                        "coverage_status": "missing_thesis",
                    },
                ]
            )
        raise AssertionError(f"Unexpected SQL: {sql}")


class FrontendLiveAdapterTests(unittest.TestCase):
    def test_live_dashboard_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/dashboard/today",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["generated_at"], "2026-05-01T00:00:00Z")
        self.assertEqual(payload["data"]["as_of_date"], "2024-11-01")
        self.assertEqual(payload["data"]["run_status"]["daily_automation"], "succeeded")
        self.assertEqual(payload["data"]["run_status"]["latest_run_id"], "pipeline-run-9101")
        self.assertEqual(payload["data"]["run_status"]["scheduler"], "not_installed")
        self.assertFalse(payload["data"]["run_status"]["holiday_skip"]["would_skip_today"])
        self.assertEqual(payload["data"]["attention_summary"]["open_ticket_count"], 1)
        self.assertEqual(payload["data"]["attention_summary"]["critical_blind_spot_count"], 1)
        self.assertEqual(payload["data"]["top_actions"][0]["rank"], 1)
        self.assertEqual(payload["data"]["top_actions"][0]["symbol"], "BABA")
        self.assertEqual(payload["data"]["top_actions"][0]["action"], "needs_thesis_review")
        self.assertEqual(payload["data"]["latest_metrics"]["covered_weight"], 0.05)
        self.assertEqual(payload["data"]["latest_metrics"]["missing_thesis_weight"], 0.03)
        self.assertEqual(payload["data"]["latest_metrics"]["cash_weight"], 0.92)
        self.assertEqual(payload["data"]["latest_metrics"]["weight_coverage_ratio"], 0.625)
        self.assertEqual(
            payload["links"]["portfolio_coverage"],
            "/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01",
        )

    def test_live_data_health_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/data-health",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["generated_at"], "2026-05-01T00:00:00Z")
        self.assertEqual(payload["data"]["overall_status"], "attention_required")
        self.assertEqual(payload["data"]["as_of_date"], "2024-11-01")
        self.assertEqual(payload["data"]["pipeline_runs"][0]["latest_run_id"], "pipeline-run-9101")
        self.assertEqual(payload["data"]["pipeline_runs"][0]["finished_at"], "2024-11-01T23:30:00Z")
        self.assertEqual(payload["data"]["scheduler"]["install_status"], "not_installed")
        self.assertEqual(
            payload["data"]["scheduler"]["runtime_env_readiness"],
            "template_rendered_placeholder_pending",
        )
        self.assertEqual(payload["data"]["freshness"][0]["dataset"], "market.daily_price_bar")
        self.assertEqual(payload["data"]["freshness"][0]["latest_observation_date"], "2024-12-02")
        self.assertIn("auth_rbac", payload["data"]["open_gates"])
        self.assertEqual(payload["links"]["dashboard"], "/api/dashboard/today")

    def test_live_remediation_tickets_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/remediation-tickets?status=open",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["generated_at"], "2026-05-01T00:00:00Z")
        self.assertEqual(payload["data"]["portfolio_name"], "Long Term Paper")
        self.assertEqual(payload["data"]["ticket_count"], 1)
        self.assertEqual(
            payload["data"]["status_counts"],
            {"open": 1, "in_progress": 0, "resolved": 0, "ignored": 0},
        )
        ticket = payload["data"]["tickets"][0]
        self.assertEqual(ticket["ticket_id"], "remediation-ticket-42")
        self.assertEqual(ticket["instrument_id"], "instrument-502")
        self.assertEqual(ticket["symbol"], "BABA")
        self.assertEqual(ticket["source_run_id"], "pipeline-run-9101")
        self.assertEqual(ticket["created_at"], "2024-11-01T23:30:00Z")
        self.assertEqual(
            payload["links"]["portfolio_coverage"],
            "/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01",
        )

    def test_live_portfolio_coverage_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["coverage_measurement_end_date"], "2024-12-02")
        self.assertEqual(payload["data"]["summary"]["position_count"], 2)
        self.assertEqual(payload["data"]["summary"]["covered_position_count"], 1)
        self.assertEqual(payload["data"]["summary"]["missing_thesis_count"], 1)
        self.assertEqual(payload["data"]["summary"]["covered_weight"], 0.05)
        self.assertEqual(payload["data"]["summary"]["missing_thesis_weight"], 0.03)
        self.assertEqual(payload["data"]["summary"]["cash_weight"], 0.92)
        self.assertEqual(payload["data"]["summary"]["weight_coverage_ratio"], 0.625)
        self.assertEqual(payload["data"]["positions"][0]["active_thesis_id"], "thesis-7001")
        self.assertEqual(payload["data"]["positions"][0]["outcome_status"], "measured")
        self.assertEqual(payload["data"]["positions"][1]["action"], "needs_thesis_review")
        self.assertEqual(payload["data"]["attribution_readiness"]["blocking_reasons"], ["missing_thesis:BABA"])

    def test_live_portfolio_coverage_allows_explicit_measurement_end_date(self) -> None:
        executor = FakeLiveExecutor()
        resolve_live_frontend_response(
            "/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01&measurementEndDate=2024-12-02",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=executor,
        )
        self.assertIn("2024-12-02", executor.scalar_sql[-1])

    def test_live_adapter_rejects_unsupported_path(self) -> None:
        with self.assertRaises(FrontendLiveUnsupportedPathError):
            resolve_live_frontend_response(
                "/api/events?asOfDate=2024-11-01",
                config=type("Config", (), {"psql_command": "psql"})(),
                executor=FakeLiveExecutor(),
            )

    def test_live_adapter_requires_psql_command_without_injected_executor(self) -> None:
        with self.assertRaises(FrontendLiveUnavailableError):
            resolve_live_frontend_response(
                "/api/remediation-tickets?status=open",
                config=type("Config", (), {"psql_command": None})(),
            )


if __name__ == "__main__":
    unittest.main()
