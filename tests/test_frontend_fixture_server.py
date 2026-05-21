from __future__ import annotations

import json
import os
import threading
import unittest
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from stockanalysis.frontend.fixture_server import create_frontend_fixture_server


class FrontendFixtureServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = create_frontend_fixture_server(
            port=0,
            runtime_profile="local",
            auth_mode="disabled",
            allowed_origin="*",
        )
        host, port = cls.server.server_address
        cls.base_url = f"http://{host}:{port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def fetch_json(self, path: str) -> tuple[int, dict[str, Any]]:
        with urlopen(f"{self.base_url}{path}", timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def fetch_error_json(self, path: str, method: str = "GET") -> tuple[int, dict[str, Any]]:
        request = Request(f"{self.base_url}{path}", method=method)
        if method not in {"GET", "HEAD"}:
            request.data = b"{}"
        try:
            urlopen(request, timeout=5)
        except HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))
        raise AssertionError("request unexpectedly succeeded")

    def test_health_returns_contract_metadata(self) -> None:
        status, payload = self.fetch_json("/__health")
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["endpoint_count"], 17)
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["source_mode"], "fixture")
        self.assertEqual(payload["runtime"]["runtime_profile"], "local")
        self.assertFalse(payload["runtime"]["read_auth_required"])

    def test_endpoints_returns_fixture_index(self) -> None:
        status, payload = self.fetch_json("/__endpoints")
        self.assertEqual(status, 200)
        self.assertEqual(payload["source_mode"], "fixture")
        paths = {endpoint["path"] for endpoint in payload["data"]["endpoints"]}
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

    def test_known_api_path_returns_fixture_response(self) -> None:
        status, payload = self.fetch_json("/api/dashboard/today")
        self.assertEqual(status, 200)
        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["portfolio_name"], "Long Term Paper")
        self.assertEqual(payload["data"]["attention_summary"]["open_ticket_count"], 1)

    def test_known_query_path_returns_fixture_response(self) -> None:
        status, payload = self.fetch_json("/api/remediation-tickets?status=open")
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["tickets"][0]["symbol"], "BABA")
        self.assertEqual(payload["data"]["status_filter"], "open")

    def test_event_and_theme_paths_return_fixture_responses(self) -> None:
        status, events = self.fetch_json("/api/events?asOfDate=2024-11-01")
        self.assertEqual(status, 200)
        self.assertEqual(events["data"]["summary"]["event_count"], 2)
        self.assertEqual(events["data"]["events"][0]["ai_evidence_id"], "sec-event-aapl-10k-20240928")

        status, theme = self.fetch_json("/api/themes/ANNUAL_REPORTING?asOfDate=2024-11-01")
        self.assertEqual(status, 200)
        self.assertEqual(theme["data"]["theme_key"], "ANNUAL_REPORTING")
        self.assertEqual(theme["data"]["linked_instruments"][0]["symbol"], "AAPL")

    def test_performance_path_returns_fixture_response(self) -> None:
        status, payload = self.fetch_json(
            "/api/performance/Long%20Term%20Paper/outcomes?measurementEndDate=2024-12-02"
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["summary"]["measured_recommendation_count"], 1)
        self.assertEqual(payload["data"]["outcomes"][0]["recommendation_id"], "AAPL-2024-11-01")
        self.assertEqual(payload["data"]["coverage_exclusions"][0]["symbol"], "BABA")

    def test_paper_trading_preview_path_returns_fixture_response(self) -> None:
        status, payload = self.fetch_json("/api/paper-trading/preview")

        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["portfolio_name"], "Long Term Paper")
        self.assertEqual(payload["data"]["quality_summary"]["paper_action_count"], 2)
        self.assertEqual(payload["data"]["paper_actions"][0]["symbol"], "AAPL")
        self.assertEqual(payload["data"]["paper_actions"][0]["paper_action"], "paper_sell_to_zero")
        self.assertTrue(payload["data"]["paper_actions"][0]["requires_human_approval"])

    def test_trading_readiness_path_returns_fixture_response(self) -> None:
        status, payload = self.fetch_json("/api/trading/readiness")

        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["portfolio_name"], "Long Term Paper")
        self.assertEqual(payload["data"]["readiness_status"], "blocked")
        self.assertEqual(payload["data"]["audit_summary"]["submitted_to_broker_count"], 0)
        self.assertNotIn("secret_ref", json.dumps(payload))

    def test_unknown_path_returns_stable_404_json(self) -> None:
        status, payload = self.fetch_error_json("/api/not-found")
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"]["code"], "FrontendApiPathNotFound")
        self.assertEqual(payload["error"]["details"]["path"], "/api/not-found")

    def test_write_method_returns_stable_405_json(self) -> None:
        status, payload = self.fetch_error_json("/api/remediation-tickets/ticket/status", method="POST")
        self.assertEqual(status, 405)
        self.assertEqual(payload["error"]["code"], "MethodNotAllowed")
        self.assertEqual(payload["error"]["details"]["method"], "POST")


class FrontendFixtureServerSourceModeTests(unittest.TestCase):
    def fetch_json_from_server(
        self,
        *,
        source: str,
        path: str,
        headers: dict[str, str] | None = None,
        **server_kwargs: Any,
    ) -> tuple[int, dict[str, Any]]:
        server_kwargs.setdefault("runtime_profile", "local")
        server_kwargs.setdefault("auth_mode", "disabled")
        server_kwargs.setdefault("allowed_origin", "*")
        server = create_frontend_fixture_server(port=0, source=source, **server_kwargs)
        host, port = server.server_address
        base_url = f"http://{host}:{port}"
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            request = Request(f"{base_url}{path}", headers=headers or {})
            with urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def fetch_error_from_server(
        self,
        *,
        source: str,
        path: str,
        headers: dict[str, str] | None = None,
        **server_kwargs: Any,
    ) -> tuple[int, dict[str, Any]]:
        server_kwargs.setdefault("runtime_profile", "local")
        server_kwargs.setdefault("auth_mode", "disabled")
        server_kwargs.setdefault("allowed_origin", "*")
        server = create_frontend_fixture_server(port=0, source=source, **server_kwargs)
        host, port = server.server_address
        base_url = f"http://{host}:{port}"
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            try:
                request = Request(f"{base_url}{path}", headers=headers or {})
                urlopen(request, timeout=5)
            except HTTPError as exc:
                return exc.code, json.loads(exc.read().decode("utf-8"))
            raise AssertionError("request unexpectedly succeeded")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_auto_source_falls_back_to_fixture_without_live_config(self) -> None:
        with patch.dict(os.environ, {"STOCKANALYSIS_PSQL_COMMAND": ""}):
            status, health = self.fetch_json_from_server(source="auto", path="/__health")
            self.assertEqual(status, 200)
            self.assertEqual(health["source_mode"], "auto")

            status, payload = self.fetch_json_from_server(
                source="auto",
                path="/api/remediation-tickets?status=open",
            )

        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["tickets"][0]["symbol"], "BABA")

    def test_live_source_without_config_returns_stable_503_json(self) -> None:
        with patch.dict(os.environ, {"STOCKANALYSIS_PSQL_COMMAND": ""}):
            status, payload = self.fetch_error_from_server(
                source="live",
                path="/api/remediation-tickets?status=open",
            )

        self.assertEqual(status, 503)
        self.assertEqual(payload["error"]["code"], "FrontendLiveReadUnavailable")
        self.assertEqual(payload["error"]["details"]["source_mode"], "live")

    def test_invalid_source_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            create_frontend_fixture_server(port=0, source="invalid")

    def test_local_non_loopback_without_auth_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            create_frontend_fixture_server(host="0.0.0.0", port=0, source="fixture")

    def test_read_token_auth_protects_api_paths_but_not_health(self) -> None:
        with patch.dict(os.environ, {"STOCKANALYSIS_FRONTEND_API_READ_TOKEN": "fixture-secret"}):
            status, health = self.fetch_json_from_server(
                source="fixture",
                path="/__health",
                auth_mode="read-token",
            )
            self.assertEqual(status, 200)
            self.assertTrue(health["runtime"]["read_auth_required"])

            status, error_payload = self.fetch_error_from_server(
                source="fixture",
                path="/api/dashboard/today",
                auth_mode="read-token",
            )
            self.assertEqual(status, 401)
            self.assertEqual(error_payload["error"]["code"], "Unauthorized")

            status, payload = self.fetch_json_from_server(
                source="fixture",
                path="/api/dashboard/today",
                auth_mode="read-token",
                headers={"Authorization": "Bearer fixture-secret"},
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["portfolio_name"], "Long Term Paper")

    def test_production_profile_requires_boundary_guards(self) -> None:
        with patch.dict(
            os.environ,
            {
                "STOCKANALYSIS_FRONTEND_API_READ_TOKEN": "",
                "STOCKANALYSIS_PSQL_COMMAND": "",
            },
        ):
            with self.assertRaises(ValueError):
                create_frontend_fixture_server(
                    port=0,
                    source="fixture",
                    runtime_profile="production",
                )

    def test_production_profile_accepts_explicit_guarded_runtime(self) -> None:
        with patch.dict(
            os.environ,
            {
                "STOCKANALYSIS_FRONTEND_API_READ_TOKEN": "prod-secret",
                "STOCKANALYSIS_PSQL_COMMAND": "psql postgresql://example.invalid/db",
            },
        ):
            status, health = self.fetch_json_from_server(
                source="auto",
                path="/__health",
                runtime_profile="production",
                allowed_origin="https://cockpit.example",
                auth_mode="read-token",
            )

        self.assertEqual(status, 200)
        self.assertEqual(health["runtime"]["runtime_profile"], "production")
        self.assertEqual(health["runtime"]["source_mode"], "auto")
        self.assertEqual(health["runtime"]["allowed_origin"], "https://cockpit.example")
        self.assertTrue(health["runtime"]["read_auth_required"])


if __name__ == "__main__":
    unittest.main()
