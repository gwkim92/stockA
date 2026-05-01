from __future__ import annotations

import unittest
from unittest.mock import patch

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.registry import get_source, list_sources


class IngestSourceTests(unittest.TestCase):
    def test_registry_lists_expected_sources(self) -> None:
        names = [source.name for source in list_sources()]
        self.assertEqual(names, ["alpha_vantage", "fred", "sec"])

    def test_sec_companyfacts_request(self) -> None:
        source = get_source("sec")
        config = RuntimeConfig(
            sec_user_agent="stockanalysis-test contact@example.com",
            fred_api_key=None,
            alpha_vantage_api_key=None,
        )
        request = source.build_request(
            "companyfacts",
            {"cik": "320193"},
            config=config,
            require_credentials=True,
        )
        self.assertEqual(
            request.url,
            "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json",
        )

    def test_fred_series_observations_request(self) -> None:
        source = get_source("fred")
        with patch.dict("os.environ", {"STOCKANALYSIS_FRED_API_KEY": "fred-demo-key"}, clear=False):
            config = RuntimeConfig.from_env()
        request = source.build_request(
            "series_observations",
            {"series_id": "DGS10", "observation_start": "2024-01-01"},
            config=config,
            require_credentials=True,
        )
        self.assertIn("series/observations", request.url)
        self.assertIn("series_id=DGS10", request.url)
        self.assertIn("observation_start=2024-01-01", request.url)
        self.assertIn("api_key=fred-demo-key", request.url)

    def test_alpha_vantage_request_defaults(self) -> None:
        source = get_source("alpha_vantage")
        config = RuntimeConfig(
            sec_user_agent=None,
            fred_api_key=None,
            alpha_vantage_api_key="alpha-demo-key",
        )
        request = source.build_request(
            "daily_adjusted",
            {"symbol": "MSFT"},
            config=config,
            require_credentials=True,
        )
        self.assertIn("function=TIME_SERIES_DAILY_ADJUSTED", request.url)
        self.assertIn("symbol=MSFT", request.url)
        self.assertIn("outputsize=compact", request.url)
        self.assertIn("apikey=alpha-demo-key", request.url)
