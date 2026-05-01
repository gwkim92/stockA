from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

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
        self.assertEqual(len(endpoints), 7)
        self.assertIn("/api/dashboard/today", paths)
        self.assertIn("/api/remediation-tickets?status=open", paths)

    def test_resolve_frontend_response_returns_linked_example(self) -> None:
        payload = resolve_frontend_response("/api/dashboard/today")
        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["attention_summary"]["open_ticket_count"], 1)
        self.assertEqual(payload["links"]["remediation_tickets"], "/api/remediation-tickets?status=open")

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
        self.assertEqual(len(payload["endpoints"]), 7)

    def test_cli_get_prints_response_payload(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["get", "--path", "/api/remediation-tickets?status=open"])
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["data"]["tickets"][0]["symbol"], "BABA")

    def test_cli_get_unknown_path_prints_stable_error(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["get", "--path", "/api/unknown"])
        self.assertEqual(exit_code, 1)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["error"]["code"], "FrontendApiPathNotFound")


if __name__ == "__main__":
    unittest.main()
