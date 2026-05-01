from __future__ import annotations

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.models import DatasetDefinition, HttpRequest

from .base import IngestSource


class SecSource(IngestSource):
    name = "sec"
    description = "SEC EDGAR filings and XBRL company facts from data.sec.gov."
    documentation_url = "https://www.sec.gov/search-filings/edgar-application-programming-interfaces"

    def datasets(self) -> tuple[DatasetDefinition, ...]:
        return (
            DatasetDefinition(
                name="submissions",
                description="Current filing history for a filer by 10-digit CIK.",
                documentation_url=self.documentation_url,
                required_params=("cik",),
                required_env_vars=("STOCKANALYSIS_SEC_USER_AGENT",),
                notes=("SEC fair access guideline: no more than 10 requests per second.",),
            ),
            DatasetDefinition(
                name="companyfacts",
                description="Aggregated XBRL company facts by 10-digit CIK.",
                documentation_url=self.documentation_url,
                required_params=("cik",),
                required_env_vars=("STOCKANALYSIS_SEC_USER_AGENT",),
                notes=("No API key required, but identified User-Agent is required for automation.",),
            ),
            DatasetDefinition(
                name="company_tickers_exchange",
                description="Current company ticker and exchange associations for listed SEC filers.",
                documentation_url="https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data",
                required_params=(),
                required_env_vars=("STOCKANALYSIS_SEC_USER_AGENT",),
                notes=("SEC file currently exposes fields [cik, name, ticker, exchange].",),
            ),
            DatasetDefinition(
                name="companyconcept",
                description="Single XBRL concept for a filer by taxonomy/tag.",
                documentation_url=self.documentation_url,
                required_params=("cik", "taxonomy", "concept"),
                required_env_vars=("STOCKANALYSIS_SEC_USER_AGENT",),
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
        cik = params["cik"].zfill(10)
        user_agent = config.resolve("STOCKANALYSIS_SEC_USER_AGENT", required=require_credentials)
        headers = {
            "Accept": "application/json",
            "User-Agent": user_agent,
        }

        if dataset_name == "submissions":
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        elif dataset_name == "companyfacts":
            url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        elif dataset_name == "company_tickers_exchange":
            url = "https://www.sec.gov/files/company_tickers_exchange.json"
        elif dataset_name == "companyconcept":
            taxonomy = params["taxonomy"]
            concept = params["concept"]
            url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/{taxonomy}/{concept}.json"
        else:
            raise ValueError(f"Unsupported SEC dataset: {dataset_name}")

        return HttpRequest(
            source_name=self.name,
            dataset_name=dataset_name,
            method="GET",
            url=url,
            headers=headers,
            timeout_seconds=float(params.get("timeout_seconds", "30")),
        )
