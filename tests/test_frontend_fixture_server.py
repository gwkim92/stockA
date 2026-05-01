from __future__ import annotations

import json
import threading
import unittest
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from stockanalysis.frontend.fixture_server import create_frontend_fixture_server


class FrontendFixtureServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = create_frontend_fixture_server(port=0)
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
        self.assertEqual(payload["endpoint_count"], 7)
        self.assertTrue(payload["read_only"])

    def test_endpoints_returns_fixture_index(self) -> None:
        status, payload = self.fetch_json("/__endpoints")
        self.assertEqual(status, 200)
        paths = {endpoint["path"] for endpoint in payload["data"]["endpoints"]}
        self.assertIn("/api/dashboard/today", paths)
        self.assertIn("/api/remediation-tickets?status=open", paths)

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


if __name__ == "__main__":
    unittest.main()
