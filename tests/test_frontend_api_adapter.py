from __future__ import annotations

import io
import json
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from stockanalysis.frontend.api_adapter import (
    FrontendApiAdapterError,
    list_frontend_endpoints,
    main,
    resolve_frontend_response,
)


class FrontendApiAdapterTests(unittest.TestCase):
    def test_list_frontend_endpoints_loads_contract_index(self) -> None:
        endpoints = list_frontend_endpoints()
        paths = {endpoint.path for endpoint in endpoints}
        self.assertEqual(len(endpoints), 17)
        self.assertIn("/api/dashboard/today", paths)
        self.assertIn("/api/remediation-tickets?status=open", paths)
        self.assertIn("/api/stocks", paths)
        self.assertIn("/api/stocks/AAPL", paths)
        self.assertIn("/api/paper-trading/preview", paths)
        self.assertIn("/api/trading/readiness", paths)
        self.assertIn("/api/ai-evidence/sec-event-aapl-10k-20240928", paths)
        self.assertIn("/api/source-documents/aapl-2024-10k-20240928", paths)
        self.assertIn("/api/events?asOfDate=2024-11-01", paths)
        self.assertIn("/api/themes/ANNUAL_REPORTING?asOfDate=2024-11-01", paths)
        self.assertIn("/api/performance/Long%20Term%20Paper/outcomes?measurementEndDate=2024-12-02", paths)

    def test_resolve_frontend_response_returns_linked_example(self) -> None:
        payload = resolve_frontend_response("/api/dashboard/today")
        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["attention_summary"]["open_ticket_count"], 1)
        self.assertEqual(payload["links"]["remediation_tickets"], "/api/remediation-tickets?status=open")

    def test_resolve_frontend_response_returns_event_theme_examples(self) -> None:
        events = resolve_frontend_response("/api/events?asOfDate=2024-11-01")
        theme = resolve_frontend_response("/api/themes/ANNUAL_REPORTING?asOfDate=2024-11-01")
        self.assertEqual(events["data"]["summary"]["event_count"], 2)
        self.assertEqual(events["data"]["events"][0]["theme_key"], "ANNUAL_REPORTING")
        self.assertEqual(events["pagination"]["limit"], 50)
        self.assertEqual(events["pagination"]["item_count"], 2)
        self.assertEqual(events["data"]["events"][0]["related_events"][0]["relation_type"], "same_source_document")
        self.assertEqual(theme["data"]["theme_key"], "ANNUAL_REPORTING")
        self.assertEqual(theme["data"]["supporting_events"][0]["event_id"], "sec-event-aapl-10k-20240928")

    def test_resolve_frontend_response_returns_stock_examples(self) -> None:
        stocks = resolve_frontend_response("/api/stocks")
        detail = resolve_frontend_response("/api/stocks/AAPL")

        self.assertEqual(stocks["data"]["stock_count"], 2)
        self.assertEqual(stocks["data"]["stocks"][0]["symbol"], "AAPL")
        self.assertEqual(stocks["data"]["stocks"][0]["latest_price"]["trade_date"], "2026-05-18")
        self.assertEqual(stocks["pagination"]["limit"], 50)
        self.assertEqual(detail["data"]["symbol"], "AAPL")
        self.assertEqual(detail["data"]["price_bars"][-1]["close"], 300.23)

    def test_resolve_frontend_response_returns_paper_trading_preview_example(self) -> None:
        payload = resolve_frontend_response("/api/paper-trading/preview")

        self.assertEqual(payload["data"]["portfolio_name"], "Long Term Paper")
        self.assertEqual(payload["data"]["quality_summary"]["position_recommendation_conflict_count"], 1)
        self.assertEqual(payload["data"]["paper_actions"][0]["symbol"], "AAPL")
        self.assertEqual(payload["data"]["paper_actions"][0]["paper_action"], "paper_sell_to_zero")
        self.assertTrue(payload["data"]["paper_actions"][0]["requires_human_approval"])
        self.assertEqual(payload["pagination"]["limit"], 50)

    def test_resolve_frontend_response_returns_trading_readiness_example(self) -> None:
        payload = resolve_frontend_response("/api/trading/readiness")

        self.assertEqual(payload["data"]["portfolio_name"], "Long Term Paper")
        self.assertEqual(payload["data"]["readiness_status"], "blocked")
        self.assertEqual(payload["data"]["broker_boundary"]["status"], "missing")
        self.assertTrue(payload["data"]["kill_switches"][0]["is_engaged"])
        self.assertEqual(payload["data"]["audit_summary"]["submitted_to_broker_count"], 0)
        self.assertNotIn("secret_ref", json.dumps(payload))

    def test_resolve_frontend_response_applies_limit_to_fixture_collection(self) -> None:
        events = resolve_frontend_response("/api/events?asOfDate=2024-11-01&limit=1")

        self.assertEqual(len(events["data"]["events"]), 1)
        self.assertEqual(events["pagination"]["limit"], 1)
        self.assertTrue(events["pagination"]["has_more"])
        self.assertIsNotNone(events["pagination"]["next_cursor"])

    def test_resolve_frontend_response_rejects_pagination_on_detail_path(self) -> None:
        with self.assertRaises(FrontendApiAdapterError) as ctx:
            resolve_frontend_response("/api/dashboard/today?limit=1")

        self.assertEqual(ctx.exception.code, "FrontendPaginationInvalid")

    def test_resolve_frontend_response_returns_performance_example(self) -> None:
        performance = resolve_frontend_response(
            "/api/performance/Long%20Term%20Paper/outcomes?measurementEndDate=2024-12-02"
        )
        self.assertEqual(performance["data"]["summary"]["measured_recommendation_count"], 1)
        self.assertEqual(performance["data"]["outcomes"][0]["recommendation_id"], "AAPL-2024-11-01")
        self.assertEqual(performance["data"]["coverage_exclusions"][0]["symbol"], "BABA")

    def test_resolve_frontend_response_rejects_unknown_path(self) -> None:
        with self.assertRaises(FrontendApiAdapterError):
            resolve_frontend_response("/api/unknown")

    def test_cli_list_prints_endpoint_index(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["list"])
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(len(payload["endpoints"]), 17)

    def test_cli_get_prints_response_payload(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["get", "--path", "/api/remediation-tickets?status=open"])
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["data"]["tickets"][0]["symbol"], "BABA")

    def test_cli_get_auto_source_falls_back_to_fixture_without_live_config(self) -> None:
        stdout = io.StringIO()
        with patch.dict(os.environ, {"STOCKANALYSIS_PSQL_COMMAND": ""}), redirect_stdout(stdout):
            exit_code = main(["get", "--source", "auto", "--path", "/api/remediation-tickets?status=open"])
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["data"]["tickets"][0]["symbol"], "BABA")

    def test_cli_get_live_source_without_config_prints_stable_error(self) -> None:
        stdout = io.StringIO()
        with patch.dict(os.environ, {"STOCKANALYSIS_PSQL_COMMAND": ""}), redirect_stdout(stdout):
            exit_code = main(["get", "--source", "live", "--path", "/api/remediation-tickets?status=open"])
        self.assertEqual(exit_code, 1)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["error"]["code"], "FrontendLiveReadUnavailable")

    def test_cli_get_unknown_path_prints_stable_error(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["get", "--path", "/api/unknown"])
        self.assertEqual(exit_code, 1)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["error"]["code"], "FrontendApiPathNotFound")

    def test_cli_get_invalid_pagination_prints_stable_error(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["get", "--path", "/api/events?asOfDate=2024-11-01&limit=0"])
        self.assertEqual(exit_code, 1)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["error"]["code"], "FrontendPaginationInvalid")


if __name__ == "__main__":
    unittest.main()
