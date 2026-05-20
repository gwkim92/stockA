from __future__ import annotations

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.models import DatasetDefinition, HttpRequest

from .base import IngestSource


class TwelveDataSource(IngestSource):
    name = "twelve_data"
    description = "No-cost pilot market data source for daily OHLCV series."
    documentation_url = "https://twelvedata.com/docs"

    def datasets(self) -> tuple[DatasetDefinition, ...]:
        return (
            DatasetDefinition(
                name="time_series_daily",
                description="Daily OHLCV time series from Twelve Data /time_series.",
                documentation_url=self.documentation_url,
                required_params=("symbol",),
                optional_params=("outputsize", "start_date", "end_date"),
                required_env_vars=("STOCKANALYSIS_TWELVE_DATA_API_KEY",),
                notes=(
                    "Twelve Data Basic/Free plan documents 800 API credits per day.",
                    "Daily prices are split-adjusted by provider documentation; dividends need separate handling.",
                ),
            ),
        )

    def build_request(
        self,
        dataset_name: str,
        params: dict[str, str],
        *,
        config: RuntimeConfig,
        require_credentials: bool,
    ) -> HttpRequest:
        dataset = self._dataset(dataset_name)
        self._validate_required(dataset, params)
        api_key = config.resolve("STOCKANALYSIS_TWELVE_DATA_API_KEY", required=require_credentials)

        if dataset_name != "time_series_daily":
            raise ValueError(f"Unsupported Twelve Data dataset: {dataset_name}")

        query = {
            "symbol": params["symbol"].upper(),
            "interval": "1day",
            "apikey": api_key,
        }
        for optional_name in ("outputsize", "start_date", "end_date"):
            if params.get(optional_name):
                query[optional_name] = params[optional_name]

        return HttpRequest(
            source_name=self.name,
            dataset_name=dataset_name,
            method="GET",
            url=self._build_url("https://api.twelvedata.com/time_series", query),
            headers={"Accept": "application/json"},
            timeout_seconds=float(params.get("timeout_seconds", "30")),
        )
