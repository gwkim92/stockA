from __future__ import annotations

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.models import DatasetDefinition, HttpRequest

from .base import IngestSource


class FredSource(IngestSource):
    name = "fred"
    description = "FRED macroeconomic series and observations."
    documentation_url = "https://fred.stlouisfed.org/docs/api/fred/"

    def datasets(self) -> tuple[DatasetDefinition, ...]:
        return (
            DatasetDefinition(
                name="series",
                description="Series metadata lookup.",
                documentation_url="https://fred.stlouisfed.org/docs/api/fred/series.html",
                required_params=("series_id",),
                required_env_vars=("STOCKANALYSIS_FRED_API_KEY",),
            ),
            DatasetDefinition(
                name="series_observations",
                description="Observation values for a single FRED series.",
                documentation_url="https://fred.stlouisfed.org/docs/api/fred/series_observations.html",
                required_params=("series_id",),
                optional_params=("observation_start", "observation_end"),
                required_env_vars=("STOCKANALYSIS_FRED_API_KEY",),
            ),
            DatasetDefinition(
                name="series_search",
                description="Search FRED series by keyword.",
                documentation_url="https://fred.stlouisfed.org/docs/api/fred/series_search.html",
                required_params=("search_text",),
                required_env_vars=("STOCKANALYSIS_FRED_API_KEY",),
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
        api_key = config.resolve("STOCKANALYSIS_FRED_API_KEY", required=require_credentials)

        endpoint_map = {
            "series": "series",
            "series_observations": "series/observations",
            "series_search": "series/search",
        }
        endpoint = endpoint_map[dataset_name]
        query = {
            "api_key": api_key,
            "file_type": "json",
        }
        for key in dataset.required_params + dataset.optional_params:
            if key in params and params[key]:
                query[key] = params[key]

        url = self._build_url(f"https://api.stlouisfed.org/fred/{endpoint}", query)
        return HttpRequest(
            source_name=self.name,
            dataset_name=dataset_name,
            method="GET",
            url=url,
            headers={"Accept": "application/json"},
            timeout_seconds=float(params.get("timeout_seconds", "30")),
        )
