from __future__ import annotations

from urllib.parse import quote, urlencode

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
                name="market_calendar_kr",
                description="Korean market trading calendar and session hours.",
                documentation_url=TOSSINVEST_OPENAPI_DOC_URL,
                required_params=("access_token",),
                optional_params=("date",),
            ),
            DatasetDefinition(
                name="market_calendar_us",
                description="US market trading calendar and session hours in KST.",
                documentation_url=TOSSINVEST_OPENAPI_DOC_URL,
                required_params=("access_token",),
                optional_params=("date",),
            ),
            DatasetDefinition(
                name="stocks",
                description="Stock reference information.",
                documentation_url=TOSSINVEST_OPENAPI_DOC_URL,
                required_params=("access_token", "symbols"),
            ),
            DatasetDefinition(
                name="stock_warnings",
                description="Read-only stock warnings and active volatility interruption flags.",
                documentation_url=TOSSINVEST_OPENAPI_DOC_URL,
                required_params=("access_token", "symbol"),
            ),
            DatasetDefinition(
                name="prices",
                description="Current stock prices.",
                documentation_url=TOSSINVEST_OPENAPI_DOC_URL,
                required_params=("access_token", "symbols"),
            ),
            DatasetDefinition(
                name="orderbook",
                description="Read-only market depth snapshot.",
                documentation_url=TOSSINVEST_OPENAPI_DOC_URL,
                required_params=("access_token", "symbol"),
            ),
            DatasetDefinition(
                name="trades",
                description="Read-only recent same-day trades.",
                documentation_url=TOSSINVEST_OPENAPI_DOC_URL,
                required_params=("access_token", "symbol"),
                optional_params=("count",),
            ),
            DatasetDefinition(
                name="price_limits",
                description="Read-only daily upper/lower price limits.",
                documentation_url=TOSSINVEST_OPENAPI_DOC_URL,
                required_params=("access_token", "symbol"),
            ),
            DatasetDefinition(
                name="candles",
                description="Read-only OHLCV candles for 1-minute or daily bars.",
                documentation_url=TOSSINVEST_OPENAPI_DOC_URL,
                required_params=("access_token", "symbol", "interval"),
                optional_params=("count", "before", "adjusted"),
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
            DatasetDefinition(
                name="orders",
                description="Read-only order history list.",
                documentation_url=TOSSINVEST_OPENAPI_DOC_URL,
                required_params=("access_token", "account_seq", "status"),
                optional_params=("symbol", "from", "to", "cursor", "limit"),
            ),
            DatasetDefinition(
                name="order_detail",
                description="Read-only order detail.",
                documentation_url=TOSSINVEST_OPENAPI_DOC_URL,
                required_params=("access_token", "account_seq", "order_id"),
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
        if dataset_name == "market_calendar_kr":
            query = {"date": params["date"]} if params.get("date") else {}
            return self._get("/api/v1/market-calendar/KR", headers=headers, query=query, dataset_name=dataset_name)
        if dataset_name == "market_calendar_us":
            query = {"date": params["date"]} if params.get("date") else {}
            return self._get("/api/v1/market-calendar/US", headers=headers, query=query, dataset_name=dataset_name)
        if dataset_name == "stocks":
            return self._get("/api/v1/stocks", headers=headers, query={"symbols": params["symbols"]}, dataset_name=dataset_name)
        if dataset_name == "stock_warnings":
            symbol = _normalize_symbol(params["symbol"])
            return self._get(f"/api/v1/stocks/{quote(symbol, safe='')}/warnings", headers=headers, dataset_name=dataset_name)
        if dataset_name == "prices":
            return self._get("/api/v1/prices", headers=headers, query={"symbols": params["symbols"]}, dataset_name=dataset_name)
        if dataset_name == "orderbook":
            return self._get("/api/v1/orderbook", headers=headers, query={"symbol": _normalize_symbol(params["symbol"])}, dataset_name=dataset_name)
        if dataset_name == "trades":
            query = {"symbol": _normalize_symbol(params["symbol"])}
            if params.get("count"):
                count = int(params["count"])
                if count < 1 or count > 50:
                    raise ValueError("TossInvest trades count must be between 1 and 50")
                query["count"] = str(count)
            return self._get("/api/v1/trades", headers=headers, query=query, dataset_name=dataset_name)
        if dataset_name == "price_limits":
            return self._get("/api/v1/price-limits", headers=headers, query={"symbol": _normalize_symbol(params["symbol"])}, dataset_name=dataset_name)
        if dataset_name == "candles":
            interval = params["interval"].strip()
            if interval not in {"1m", "1d"}:
                raise ValueError("TossInvest candles interval must be one of: 1m, 1d")
            query = {
                "symbol": params["symbol"].strip().upper(),
                "interval": interval,
            }
            if params.get("count"):
                count = int(params["count"])
                if count < 1 or count > 200:
                    raise ValueError("TossInvest candles count must be between 1 and 200")
                query["count"] = str(count)
            if params.get("before"):
                query["before"] = params["before"]
            if params.get("adjusted"):
                adjusted = params["adjusted"].strip().lower()
                if adjusted not in {"true", "false"}:
                    raise ValueError("TossInvest candles adjusted must be true or false")
                query["adjusted"] = adjusted
            return self._get("/api/v1/candles", headers=headers, query=query, dataset_name=dataset_name)
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
        if dataset_name == "orders":
            status = params["status"].strip().upper()
            if status not in {"OPEN", "CLOSED"}:
                raise ValueError("TossInvest orders status must be OPEN or CLOSED")
            query = {"status": status}
            if params.get("symbol"):
                query["symbol"] = _normalize_symbol(params["symbol"])
            for name in ("from", "to", "cursor"):
                if params.get(name):
                    query[name] = params[name]
            if params.get("limit"):
                limit = int(params["limit"])
                if limit < 1 or limit > 100:
                    raise ValueError("TossInvest orders limit must be between 1 and 100")
                query["limit"] = str(limit)
            return self._get("/api/v1/orders", headers=headers, query=query, dataset_name=dataset_name)
        if dataset_name == "order_detail":
            order_id = params["order_id"].strip()
            if not order_id:
                raise ValueError("TossInvest order_detail order_id must not be empty")
            return self._get(f"/api/v1/orders/{quote(order_id, safe='')}", headers=headers, dataset_name=dataset_name)
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
        "url": _sanitize_tossinvest_url(request),
        "headers": headers,
        "body_length": len(request.body) if request.body is not None else 0,
        "timeout_seconds": request.timeout_seconds,
    }


def _sanitize_tossinvest_url(request: HttpRequest) -> str:
    if request.dataset_name != "order_detail":
        return request.url
    marker = "/api/v1/orders/"
    if marker not in request.url:
        return request.url
    prefix, suffix = request.url.split(marker, 1)
    query = ""
    if "?" in suffix:
        _, query = suffix.split("?", 1)
    sanitized = f"{prefix}{marker}<redacted>"
    return f"{sanitized}?{query}" if query else sanitized


def _normalize_symbol(value: str) -> str:
    symbol = value.strip().upper()
    if not symbol:
        raise ValueError("TossInvest symbol must not be empty")
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-")
    if any(char not in allowed for char in symbol):
        raise ValueError("TossInvest symbol may only contain letters, digits, '.', or '-'")
    return symbol
