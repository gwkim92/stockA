from __future__ import annotations

from urllib.parse import urlencode

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.models import DatasetDefinition, HttpRequest
from stockanalysis.ingest.sources.base import IngestSource


TOSSINVEST_API_BASE_URL = "https://openapi.tossinvest.com"
TOSSINVEST_OPENAPI_DOC_URL = "https://openapi.tossinvest.com/openapi-docs/latest/openapi.json"


class TossInvestSource(IngestSource):
    name = "tossinvest"
    description = "Toss Securities Open API read-only account, market, and order-info datasets."
    documentation_url = TOSSINVEST_OPENAPI_DOC_URL

    def datasets(self) -> tuple[DatasetDefinition, ...]:
        return (
            DatasetDefinition(
                name="oauth_token",
                description="OAuth2 client-credentials access token endpoint.",
                documentation_url=TOSSINVEST_OPENAPI_DOC_URL,
                required_params=(),
                required_env_vars=(
                    "STOCKANALYSIS_TOSSINVEST_CLIENT_ID",
                    "STOCKANALYSIS_TOSSINVEST_CLIENT_SECRET",
                ),
                notes=("POST form body is intentionally omitted from HttpRequest.as_dict().",),
            ),
            DatasetDefinition(
                name="accounts",
                description="Read-only account list.",
                documentation_url=TOSSINVEST_OPENAPI_DOC_URL,
                required_params=("access_token",),
            ),
            DatasetDefinition(
                name="holdings",
                description="Read-only holdings and valuation summary.",
                documentation_url=TOSSINVEST_OPENAPI_DOC_URL,
                required_params=("access_token", "account_seq"),
                optional_params=("symbol",),
            ),
            DatasetDefinition(
                name="exchange_rate",
                description="KRW/USD exchange rate evidence.",
                documentation_url=TOSSINVEST_OPENAPI_DOC_URL,
                required_params=("access_token", "base_currency", "quote_currency"),
            ),
            DatasetDefinition(
                name="stocks",
                description="Stock reference information.",
                documentation_url=TOSSINVEST_OPENAPI_DOC_URL,
                required_params=("access_token", "symbols"),
            ),
            DatasetDefinition(
                name="prices",
                description="Current stock prices.",
                documentation_url=TOSSINVEST_OPENAPI_DOC_URL,
                required_params=("access_token", "symbols"),
            ),
            DatasetDefinition(
                name="buying_power",
                description="Read-only cash buying power by currency.",
                documentation_url=TOSSINVEST_OPENAPI_DOC_URL,
                required_params=("access_token", "account_seq", "currency"),
            ),
            DatasetDefinition(
                name="sellable_quantity",
                description="Read-only sellable quantity for a symbol.",
                documentation_url=TOSSINVEST_OPENAPI_DOC_URL,
                required_params=("access_token", "account_seq", "symbol"),
            ),
            DatasetDefinition(
                name="commissions",
                description="Read-only commission rates by market.",
                documentation_url=TOSSINVEST_OPENAPI_DOC_URL,
                required_params=("access_token", "account_seq"),
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
        if dataset_name == "oauth_token":
            client_id = config.resolve("STOCKANALYSIS_TOSSINVEST_CLIENT_ID", required=require_credentials)
            client_secret = config.resolve("STOCKANALYSIS_TOSSINVEST_CLIENT_SECRET", required=require_credentials)
            body = urlencode(
                {
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                }
            ).encode("utf-8")
            return HttpRequest(
                source_name=self.name,
                dataset_name=dataset_name,
                method="POST",
                url=f"{TOSSINVEST_API_BASE_URL}/oauth2/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                body=body,
            )

        access_token = params["access_token"]
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        account_seq = params.get("account_seq")
        if account_seq:
            headers["X-Tossinvest-Account"] = account_seq

        if dataset_name == "accounts":
            return self._get("/api/v1/accounts", headers=headers)
        if dataset_name == "holdings":
            query = {"symbol": params["symbol"]} if params.get("symbol") else {}
            return self._get("/api/v1/holdings", headers=headers, query=query, dataset_name=dataset_name)
        if dataset_name == "exchange_rate":
            return self._get(
                "/api/v1/exchange-rate",
                headers=headers,
                query={
                    "baseCurrency": params["base_currency"].upper(),
                    "quoteCurrency": params["quote_currency"].upper(),
                },
                dataset_name=dataset_name,
            )
        if dataset_name == "stocks":
            return self._get("/api/v1/stocks", headers=headers, query={"symbols": params["symbols"]}, dataset_name=dataset_name)
        if dataset_name == "prices":
            return self._get("/api/v1/prices", headers=headers, query={"symbols": params["symbols"]}, dataset_name=dataset_name)
        if dataset_name == "buying_power":
            return self._get(
                "/api/v1/buying-power",
                headers=headers,
                query={"currency": params["currency"].upper()},
                dataset_name=dataset_name,
            )
        if dataset_name == "sellable_quantity":
            return self._get(
                "/api/v1/sellable-quantity",
                headers=headers,
                query={"symbol": params["symbol"]},
                dataset_name=dataset_name,
            )
        if dataset_name == "commissions":
            return self._get("/api/v1/commissions", headers=headers, dataset_name=dataset_name)
        raise ValueError(f"Unsupported TossInvest dataset: {dataset_name}")

    def _get(
        self,
        path: str,
        *,
        headers: dict[str, str],
        query: dict[str, str] | None = None,
        dataset_name: str | None = None,
    ) -> HttpRequest:
        return HttpRequest(
            source_name=self.name,
            dataset_name=dataset_name or path.rsplit("/", 1)[-1].replace("-", "_"),
            method="GET",
            url=self._build_url(f"{TOSSINVEST_API_BASE_URL}{path}", query or {}),
            headers=headers,
        )


def sanitized_tossinvest_request_dict(request: HttpRequest) -> dict[str, object]:
    headers = {
        key: ("<redacted>" if key.lower() in {"authorization", "x-tossinvest-account"} else value)
        for key, value in request.headers.items()
    }
    return {
        "source_name": request.source_name,
        "dataset_name": request.dataset_name,
        "method": request.method,
        "url": request.url,
        "headers": headers,
        "body_length": len(request.body) if request.body is not None else 0,
        "timeout_seconds": request.timeout_seconds,
    }
