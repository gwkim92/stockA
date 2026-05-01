from __future__ import annotations

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.models import DatasetDefinition, HttpRequest

from .base import IngestSource


class AlphaVantageSource(IngestSource):
    name = "alpha_vantage"
    description = "Bootstrap market data and fundamentals from Alpha Vantage."
    documentation_url = "https://www.alphavantage.co/documentation/"

    def datasets(self) -> tuple[DatasetDefinition, ...]:
        return (
            DatasetDefinition(
                name="daily_adjusted",
                description="Daily adjusted OHLCV series with split/dividend history.",
                documentation_url=self.documentation_url,
                required_params=("symbol",),
                optional_params=("outputsize", "datatype"),
                required_env_vars=("STOCKANALYSIS_ALPHA_VANTAGE_API_KEY",),
                notes=("Alpha Vantage free key currently allows up to 25 requests per day.",),
            ),
            DatasetDefinition(
                name="income_statement",
                description="Income statement fundamentals for a symbol.",
                documentation_url=self.documentation_url,
                required_params=("symbol",),
                required_env_vars=("STOCKANALYSIS_ALPHA_VANTAGE_API_KEY",),
            ),
            DatasetDefinition(
                name="earnings",
                description="Reported earnings history for a symbol.",
                documentation_url=self.documentation_url,
                required_params=("symbol",),
                required_env_vars=("STOCKANALYSIS_ALPHA_VANTAGE_API_KEY",),
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
        api_key = config.resolve("STOCKANALYSIS_ALPHA_VANTAGE_API_KEY", required=require_credentials)

        function_map = {
            "daily_adjusted": "TIME_SERIES_DAILY_ADJUSTED",
            "income_statement": "INCOME_STATEMENT",
            "earnings": "EARNINGS",
        }
        query = {
            "function": function_map[dataset_name],
            "apikey": api_key,
            "symbol": params["symbol"],
        }
        if dataset_name == "daily_adjusted":
            query["outputsize"] = params.get("outputsize", "compact")
            query["datatype"] = params.get("datatype", "json")

        url = self._build_url("https://www.alphavantage.co/query", query)
        return HttpRequest(
            source_name=self.name,
            dataset_name=dataset_name,
            method="GET",
            url=url,
            headers={"Accept": "application/json"},
            timeout_seconds=float(params.get("timeout_seconds", "30")),
        )
