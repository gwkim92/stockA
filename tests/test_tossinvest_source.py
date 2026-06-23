from __future__ import annotations

import json
import unittest
from urllib.parse import parse_qs, urlparse

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.sources.tossinvest import TossInvestSource, sanitized_tossinvest_request_dict


class TossInvestSourceTests(unittest.TestCase):
    def test_oauth_request_dict_is_secret_free(self) -> None:
        source = TossInvestSource()
        request = source.build_request(
            "oauth_token",
            {},
            config=RuntimeConfig(
                tossinvest_client_id="client-id-test",
                tossinvest_client_secret="client-secret-test",
            ),
            require_credentials=True,
        )

        self.assertEqual(request.method, "POST")
        self.assertEqual(request.url, "https://openapi.tossinvest.com/oauth2/token")
        self.assertIn(b"client-secret-test", request.body or b"")
        dumped = json.dumps(request.as_dict(), sort_keys=True)
        self.assertNotIn("client-secret-test", dumped)
        self.assertNotIn("client-id-test", dumped)
        self.assertEqual(request.as_dict()["body_length"], len(request.body or b""))

    def test_account_request_sanitizer_redacts_token_and_account_header(self) -> None:
        source = TossInvestSource()
        request = source.build_request(
            "holdings",
            {
                "access_token": "access-token-test",
                "account_seq": "account-seq-secret-test",
            },
            config=RuntimeConfig(),
            require_credentials=False,
        )

        sanitized = sanitized_tossinvest_request_dict(request)
        dumped = json.dumps(sanitized, sort_keys=True)
        self.assertNotIn("access-token-test", dumped)
        self.assertNotIn("account-seq-secret-test", dumped)
        self.assertEqual(sanitized["headers"]["Authorization"], "<redacted>")
        self.assertEqual(sanitized["headers"]["X-Tossinvest-Account"], "<redacted>")
        self.assertEqual(request.as_dict()["headers"]["Authorization"], "<redacted>")

    def test_candles_request_supports_daily_chart_params_and_redacts_token(self) -> None:
        source = TossInvestSource()
        request = source.build_request(
            "candles",
            {
                "access_token": "access-token-test",
                "symbol": "aapl",
                "interval": "1d",
                "count": "200",
                "before": "2026-03-25T09:00:00+09:00",
                "adjusted": "true",
            },
            config=RuntimeConfig(),
            require_credentials=False,
        )

        parsed = urlparse(request.url)
        query = parse_qs(parsed.query)
        self.assertEqual(request.method, "GET")
        self.assertEqual(parsed.path, "/api/v1/candles")
        self.assertEqual(query["symbol"], ["AAPL"])
        self.assertEqual(query["interval"], ["1d"])
        self.assertEqual(query["count"], ["200"])
        self.assertEqual(query["adjusted"], ["true"])
        self.assertEqual(query["before"], ["2026-03-25T09:00:00+09:00"])
        dumped = json.dumps(sanitized_tossinvest_request_dict(request), sort_keys=True)
        self.assertNotIn("access-token-test", dumped)
        self.assertEqual(request.as_dict()["headers"]["Authorization"], "<redacted>")

    def test_candles_request_rejects_unsupported_interval(self) -> None:
        source = TossInvestSource()
        with self.assertRaisesRegex(ValueError, "interval"):
            source.build_request(
                "candles",
                {
                    "access_token": "access-token-test",
                    "symbol": "AAPL",
                    "interval": "5m",
                },
                config=RuntimeConfig(),
                require_credentials=False,
            )


if __name__ == "__main__":
    unittest.main()
