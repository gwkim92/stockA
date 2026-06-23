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

    def test_remaining_readonly_requests_build_expected_paths_and_redact_headers(self) -> None:
        source = TossInvestSource()
        config = RuntimeConfig()
        requests = [
            source.build_request(
                "market_calendar_kr",
                {"access_token": "access-token-test", "date": "2026-06-23"},
                config=config,
                require_credentials=False,
            ),
            source.build_request(
                "market_calendar_us",
                {"access_token": "access-token-test"},
                config=config,
                require_credentials=False,
            ),
            source.build_request(
                "stock_warnings",
                {"access_token": "access-token-test", "symbol": "aapl"},
                config=config,
                require_credentials=False,
            ),
            source.build_request(
                "orderbook",
                {"access_token": "access-token-test", "symbol": "aapl"},
                config=config,
                require_credentials=False,
            ),
            source.build_request(
                "trades",
                {"access_token": "access-token-test", "symbol": "aapl", "count": "10"},
                config=config,
                require_credentials=False,
            ),
            source.build_request(
                "price_limits",
                {"access_token": "access-token-test", "symbol": "aapl"},
                config=config,
                require_credentials=False,
            ),
        ]

        urls = [request.url for request in requests]
        self.assertIn("/api/v1/market-calendar/KR?date=2026-06-23", urls[0])
        self.assertIn("/api/v1/market-calendar/US", urls[1])
        self.assertIn("/api/v1/stocks/AAPL/warnings", urls[2])
        self.assertIn("/api/v1/orderbook?symbol=AAPL", urls[3])
        self.assertIn("/api/v1/trades?symbol=AAPL&count=10", urls[4])
        self.assertIn("/api/v1/price-limits?symbol=AAPL", urls[5])
        dumped = json.dumps([sanitized_tossinvest_request_dict(request) for request in requests], sort_keys=True)
        self.assertNotIn("access-token-test", dumped)

    def test_order_history_requests_redact_account_header_and_order_detail_url(self) -> None:
        source = TossInvestSource()
        config = RuntimeConfig()
        orders_request = source.build_request(
            "orders",
            {
                "access_token": "access-token-test",
                "account_seq": "account-seq-secret-test",
                "status": "closed",
                "symbol": "aapl",
                "limit": "20",
            },
            config=config,
            require_credentials=False,
        )
        detail_request = source.build_request(
            "order_detail",
            {
                "access_token": "access-token-test",
                "account_seq": "account-seq-secret-test",
                "order_id": "order-secret-test-001",
            },
            config=config,
            require_credentials=False,
        )

        self.assertIn("/api/v1/orders?status=CLOSED&symbol=AAPL&limit=20", orders_request.url)
        self.assertIn("/api/v1/orders/order-secret-test-001", detail_request.url)
        sanitized = sanitized_tossinvest_request_dict(detail_request)
        dumped = json.dumps(
            [sanitized_tossinvest_request_dict(orders_request), sanitized],
            sort_keys=True,
        )
        self.assertNotIn("access-token-test", dumped)
        self.assertNotIn("account-seq-secret-test", dumped)
        self.assertNotIn("order-secret-test-001", dumped)
        self.assertEqual(sanitized["url"], "https://openapi.tossinvest.com/api/v1/orders/<redacted>")

    def test_readonly_request_validation_rejects_bad_status_and_counts(self) -> None:
        source = TossInvestSource()
        with self.assertRaisesRegex(ValueError, "status"):
            source.build_request(
                "orders",
                {
                    "access_token": "access-token-test",
                    "account_seq": "account-seq-secret-test",
                    "status": "all",
                },
                config=RuntimeConfig(),
                require_credentials=False,
            )
        with self.assertRaisesRegex(ValueError, "count"):
            source.build_request(
                "trades",
                {"access_token": "access-token-test", "symbol": "AAPL", "count": "51"},
                config=RuntimeConfig(),
                require_credentials=False,
            )


if __name__ == "__main__":
    unittest.main()
