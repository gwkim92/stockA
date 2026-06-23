from __future__ import annotations

import json
import unittest

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


if __name__ == "__main__":
    unittest.main()
