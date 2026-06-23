from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.http import execute_request
from stockanalysis.ingest.macro.sql import sql_date, sql_literal, sql_numeric
from stockanalysis.ingest.models import FetchResponse, HttpRequest
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.ingest.sources.tossinvest import TossInvestSource


DEFAULT_TOSSINVEST_PORTFOLIO_NAME = "Toss Real Readonly"
DEFAULT_TOSSINVEST_BASE_CURRENCY = "KRW"
TOSSINVEST_READONLY_PIPELINE_NAME = "tossinvest_readonly_sync"
TOSSINVEST_PROVIDER_NAME = "tossinvest"
READ_ONLY_ORDER_BOUNDARY = "read_only_no_order"
DISABLED_SUBMIT_ADAPTER_STATUS = "disabled_stub"

_MONEY_QUANTIZER = Decimal("0.01")
_PRICE_QUANTIZER = Decimal("0.000001")
_WEIGHT_QUANTIZER = Decimal("0.0001")
_FX_QUANTIZER = Decimal("0.00000001")


@dataclass(frozen=True)
class TossInvestFxRate:
    base_currency: str
    quote_currency: str
    rate: Decimal
    mid_rate: Decimal | None
    basis_point: Decimal | None
    valid_from: str
    valid_until: str | None
    rate_change_type: str | None

    @property
    def conversion_rate(self) -> Decimal:
        return self.mid_rate if self.mid_rate is not None else self.rate


@dataclass(frozen=True)
class TossInvestHolding:
    symbol: str
    name: str
    market_country: str
    exchange_mic_code: str | None
    instrument_type: str
    native_currency: str
    quantity: Decimal
    market_price_native: Decimal
    market_value_native: Decimal
    cost_basis_native: Decimal | None
    unrealized_pnl_native: Decimal | None
    fx_rate_to_base: Decimal
    market_price_base: Decimal
    market_value_base: Decimal
    cost_basis_base: Decimal | None
    unrealized_pnl_base: Decimal | None
    conversion_note: str


@dataclass(frozen=True)
class TossInvestReadonlySyncResult:
    portfolio_name: str
    base_currency: str
    snapshot_date: date
    account_selection_status: str
    selected_account_seq_configured: bool
    credentials_configured: bool
    fx_rate: TossInvestFxRate | None
    holdings: tuple[TossInvestHolding, ...]
    unresolved_exchange_mappings: tuple[dict[str, str], ...]
    buying_power: tuple[dict[str, str], ...]
    sellable_quantities: tuple[dict[str, str], ...]
    commissions: tuple[dict[str, str], ...]

    def report(self) -> dict[str, object]:
        total_market_value = sum((holding.market_value_base for holding in self.holdings), Decimal("0"))
        currencies = sorted({holding.native_currency for holding in self.holdings})
        return {
            "report_name": "tossinvest_readonly_sync",
            "provider": TOSSINVEST_PROVIDER_NAME,
            "portfolio_name": self.portfolio_name,
            "base_currency": self.base_currency,
            "snapshot_date": self.snapshot_date.isoformat(),
            "status": "loaded",
            "credentials_configured": self.credentials_configured,
            "account_selection_status": self.account_selection_status,
            "selected_account_seq_configured": self.selected_account_seq_configured,
            "holding_count": len(self.holdings),
            "currency_summary": {
                "native_currencies": currencies,
                "base_market_value": _decimal_text(_quantize_money(total_market_value)),
            },
            "fx_rate": _fx_report(self.fx_rate),
            "unresolved_exchange_mappings": list(self.unresolved_exchange_mappings),
            "unresolved_exchange_mapping_count": len(self.unresolved_exchange_mappings),
            "buying_power": list(self.buying_power),
            "sellable_quantities": list(self.sellable_quantities),
            "sellable_quantity_count": len(self.sellable_quantities),
            "commission_summary": list(self.commissions),
            "submit_adapter_status": DISABLED_SUBMIT_ADAPTER_STATUS,
            "broker_submit_allowed": False,
            "automatic_order_allowed": False,
            "order_boundary": READ_ONLY_ORDER_BOUNDARY,
            "order_submit_attempted": False,
            "submitted_to_broker": False,
            "secret_free": True,
        }


def run_tossinvest_readonly_sync(
    *,
    config: RuntimeConfig,
    portfolio_name: str = DEFAULT_TOSSINVEST_PORTFOLIO_NAME,
    base_currency: str = DEFAULT_TOSSINVEST_BASE_CURRENCY,
    as_of_date: date | None = None,
    fixture_json_path: str | None = None,
    execute: bool = False,
    dry_run: bool = False,
    executor: PsqlCommandExecutor | None = None,
    request_executor: Callable[[HttpRequest], FetchResponse] = execute_request,
) -> dict[str, object]:
    if execute and dry_run:
        raise ValueError("Use either --execute or --dry-run, not both.")
    snapshot_date = as_of_date or date.today()
    normalized_base_currency = base_currency.upper()

    if fixture_json_path:
        payload = _load_fixture_payload(fixture_json_path)
        result = normalize_tossinvest_readonly_payload(
            payload,
            portfolio_name=portfolio_name,
            base_currency=normalized_base_currency,
            snapshot_date=snapshot_date,
            credentials_configured=_credentials_configured(config),
            selected_account_seq=config.tossinvest_account_seq,
        )
    else:
        if not _credentials_configured(config):
            report = _missing_credentials_report(
                portfolio_name=portfolio_name,
                base_currency=normalized_base_currency,
                snapshot_date=snapshot_date,
                selected_account_seq_configured=config.tossinvest_account_seq is not None,
            )
            if execute:
                report["status"] = "blocked_missing_credentials"
            return report
        try:
            payload = _fetch_live_payload(
                config=config,
                base_currency=normalized_base_currency,
                request_executor=request_executor,
            )
        except (HTTPError, URLError) as exc:
            report = _provider_access_error_report(
                portfolio_name=portfolio_name,
                base_currency=normalized_base_currency,
                snapshot_date=snapshot_date,
                selected_account_seq_configured=config.tossinvest_account_seq is not None,
                error=exc,
                execute=execute,
            )
            if execute:
                sql_executor = executor or PsqlCommandExecutor.from_config(config)
                run_id = _create_pipeline_run(sql_executor, config_json=report)
                report["run_id"] = run_id
                _mark_pipeline_run_failed(
                    sql_executor,
                    run_id,
                    _provider_access_error_summary(report),
                    config_json=report,
                )
            return report
        result = normalize_tossinvest_readonly_payload(
            payload,
            portfolio_name=portfolio_name,
            base_currency=normalized_base_currency,
            snapshot_date=snapshot_date,
            credentials_configured=True,
            selected_account_seq=config.tossinvest_account_seq,
        )

    report = result.report()
    report["mode"] = "execute" if execute else "dry_run"
    report["dry_run"] = not execute
    if not execute:
        return report

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(sql_executor, config_json=report)
    try:
        write_payload = json.loads(
            sql_executor.execute_scalar(render_tossinvest_readonly_sync_upsert_sql(result, source_run_id=run_id))
        )
        report["run_id"] = run_id
        report["write_result"] = write_payload
        report["status"] = "succeeded"
        _mark_pipeline_run_succeeded(sql_executor, run_id, config_json=report)
        return report
    except Exception as exc:
        failed_report = dict(report)
        failed_report["run_id"] = run_id
        failed_report["status"] = "failed"
        failed_report["error_code"] = "tossinvest_readonly_sync_failed"
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc), config_json=failed_report)
        raise


def normalize_tossinvest_readonly_payload(
    payload: Mapping[str, Any],
    *,
    portfolio_name: str,
    base_currency: str,
    snapshot_date: date,
    credentials_configured: bool,
    selected_account_seq: str | None,
) -> TossInvestReadonlySyncResult:
    normalized_base_currency = base_currency.upper()
    accounts = _as_list(_unwrap_result(payload.get("accounts")))
    account_selection_status = _account_selection_status(accounts, selected_account_seq)
    selected_account_seq_configured = selected_account_seq is not None
    stocks_by_symbol = _records_by_symbol(_unwrap_result(payload.get("stocks")))
    prices_by_symbol = _records_by_symbol(_unwrap_result(payload.get("prices")))
    fx_rate = _normalize_fx_rate(_unwrap_result(payload.get("exchange_rate")))
    raw_holdings = _holding_items(_unwrap_result(payload.get("holdings")))
    unresolved: list[dict[str, str]] = []
    holdings: list[TossInvestHolding] = []
    for raw_holding in raw_holdings:
        holding = _normalize_holding(
            raw_holding,
            stock_info=stocks_by_symbol.get(_symbol(raw_holding)),
            price_info=prices_by_symbol.get(_symbol(raw_holding)),
            base_currency=normalized_base_currency,
            fx_rate=fx_rate,
        )
        if holding.exchange_mic_code is None:
            unresolved.append(
                {
                    "symbol": holding.symbol,
                    "market_country": holding.market_country,
                    "reason": "unsupported_or_missing_exchange_mapping",
                }
            )
        holdings.append(holding)

    return TossInvestReadonlySyncResult(
        portfolio_name=portfolio_name,
        base_currency=normalized_base_currency,
        snapshot_date=snapshot_date,
        account_selection_status=account_selection_status,
        selected_account_seq_configured=selected_account_seq_configured,
        credentials_configured=credentials_configured,
        fx_rate=fx_rate,
        holdings=tuple(holdings),
        unresolved_exchange_mappings=tuple(unresolved),
        buying_power=tuple(_normalize_buying_power(payload.get("buying_power"))),
        sellable_quantities=tuple(_normalize_sellable_quantities(payload.get("sellable_quantities"))),
        commissions=tuple(_normalize_commissions(payload.get("commissions"))),
    )


def render_tossinvest_readonly_sync_upsert_sql(
    result: TossInvestReadonlySyncResult,
    *,
    source_run_id: int,
) -> str:
    if not result.holdings:
        raise ValueError("TossInvest readonly sync requires at least one holding to write.")
    fx_rows = _render_fx_value_row(result.fx_rate, source_run_id=source_run_id)
    holding_rows = ",\n        ".join(_render_holding_value_tuple(holding) for holding in result.holdings)
    return f"""begin;

insert into ref.market (
    market_code,
    name,
    country_code,
    currency_code,
    timezone,
    is_active
)
values
    ('KR', 'Korea Equities', 'KR', 'KRW', 'Asia/Seoul', true)
on conflict (market_code) do update
set
    name = excluded.name,
    country_code = excluded.country_code,
    currency_code = excluded.currency_code,
    timezone = excluded.timezone,
    is_active = excluded.is_active;

insert into ref.exchange (
    market_code,
    mic_code,
    name,
    timezone,
    is_primary
)
values
    ('KR', 'XKRX', 'Korea Exchange', 'Asia/Seoul', true)
on conflict (mic_code) do update
set
    market_code = excluded.market_code,
    name = excluded.name,
    timezone = excluded.timezone,
    is_primary = excluded.is_primary;

with source_holdings (
    symbol,
    instrument_name,
    market_country,
    exchange_mic_code,
    instrument_type,
    native_currency_code,
    quantity,
    cost_basis,
    market_price,
    market_value,
    weight,
    unrealized_pnl,
    cost_basis_native,
    market_price_native,
    market_value_native,
    unrealized_pnl_native,
    fx_rate_to_base,
    currency_conversion_note
) as (
    values
        {holding_rows}
),
fx_input (
    provider,
    base_currency,
    quote_currency,
    valid_from,
    valid_until,
    rate,
    mid_rate,
    basis_point,
    rate_change_type,
    evidence_json,
    source_run_id
) as (
    values
        {fx_rows}
),
upsert_fx as (
    insert into market.fx_rate_snapshot (
        provider,
        base_currency,
        quote_currency,
        valid_from,
        valid_until,
        rate,
        mid_rate,
        basis_point,
        rate_change_type,
        evidence_json,
        source_run_id
    )
    select
        provider,
        base_currency,
        quote_currency,
        valid_from,
        valid_until,
        rate,
        mid_rate,
        basis_point,
        rate_change_type,
        evidence_json,
        source_run_id
    from fx_input
    where base_currency is not null
    on conflict (provider, base_currency, quote_currency, valid_from)
    where valid_from is not null
    do update
    set
        valid_until = excluded.valid_until,
        rate = excluded.rate,
        mid_rate = excluded.mid_rate,
        basis_point = excluded.basis_point,
        rate_change_type = excluded.rate_change_type,
        evidence_json = excluded.evidence_json,
        source_run_id = excluded.source_run_id
    returning fx_rate_snapshot_id, base_currency, quote_currency
),
issuer_source as (
    select distinct
        instrument_name as legal_name,
        instrument_name as display_name,
        market_country as country_code,
        case when instrument_type in ('etf', 'fund') then 'fund' else 'corporate' end as issuer_type
    from source_holdings
    where exchange_mic_code is not null
),
inserted_issuer as (
    insert into ref.issuer (
        legal_name,
        display_name,
        country_code,
        issuer_type
    )
    select
        source.legal_name,
        source.display_name,
        source.country_code,
        source.issuer_type
    from issuer_source source
    where not exists (
        select 1
        from ref.issuer existing
        where existing.legal_name = source.legal_name
          and existing.country_code = source.country_code
          and existing.issuer_type = source.issuer_type
    )
    returning issuer_id, legal_name, country_code, issuer_type
),
resolved_issuer as (
    select issuer_id, legal_name, country_code, issuer_type
    from inserted_issuer
    union all
    select
        issuer_id,
        legal_name,
        country_code,
        issuer_type
    from (
        select distinct on (existing.legal_name, existing.country_code, existing.issuer_type)
            existing.issuer_id,
            existing.legal_name,
            existing.country_code,
            existing.issuer_type
        from ref.issuer existing
        join issuer_source source
          on source.legal_name = existing.legal_name
         and source.country_code = existing.country_code
         and source.issuer_type = existing.issuer_type
        order by existing.legal_name, existing.country_code, existing.issuer_type, existing.issuer_id
    ) existing_issuer
),
instrument_source as (
    select distinct
        source.symbol,
        source.instrument_name,
        source.market_country,
        source.exchange_mic_code,
        source.instrument_type,
        source.native_currency_code,
        issuer.issuer_id,
        exchange.exchange_id
    from source_holdings source
    join ref.exchange exchange on exchange.mic_code = source.exchange_mic_code
    join resolved_issuer issuer
      on issuer.legal_name = source.instrument_name
     and issuer.country_code = source.market_country
),
upsert_instrument as (
    insert into ref.instrument (
        issuer_id,
        exchange_id,
        market_code,
        primary_symbol,
        instrument_type,
        currency_code,
        name,
        is_active
    )
    select
        issuer_id,
        exchange_id,
        market_country,
        symbol,
        instrument_type,
        native_currency_code,
        instrument_name,
        true
    from instrument_source
    on conflict (exchange_id, primary_symbol) do update
    set
        issuer_id = excluded.issuer_id,
        market_code = excluded.market_code,
        instrument_type = excluded.instrument_type,
        currency_code = excluded.currency_code,
        name = excluded.name,
        is_active = excluded.is_active
    returning instrument_id, primary_symbol
),
upsert_portfolio as (
    insert into portfolio.portfolio (
        portfolio_name,
        base_currency,
        market_code,
        strategy_name,
        is_paper
    )
    values (
        {sql_literal(result.portfolio_name)},
        {sql_literal(result.base_currency)},
        'KR',
        'tossinvest_readonly',
        false
    )
    on conflict (portfolio_name) do update
    set
        base_currency = excluded.base_currency,
        market_code = excluded.market_code,
        strategy_name = excluded.strategy_name,
        is_paper = excluded.is_paper
    returning portfolio_id
),
resolved_rows as (
    select distinct on (source.symbol)
        portfolio.portfolio_id,
        instrument.instrument_id,
        source.*,
        case
            when source.native_currency_code = {sql_literal(result.base_currency)} then null::bigint
            when source.native_currency_code = fx.base_currency and fx.quote_currency = {sql_literal(result.base_currency)}
                then fx.fx_rate_snapshot_id
            else null::bigint
        end as fx_rate_snapshot_id
    from source_holdings source
    join ref.instrument instrument
      on instrument.is_active = true
     and lower(instrument.primary_symbol) = lower(source.symbol)
    join upsert_portfolio portfolio on true
    left join upsert_fx fx on fx.base_currency = source.native_currency_code and fx.quote_currency = {sql_literal(result.base_currency)}
    order by source.symbol, instrument.instrument_id
),
upsert_positions as (
    insert into portfolio.position_snapshot (
        portfolio_id,
        instrument_id,
        snapshot_date,
        quantity,
        cost_basis,
        market_price,
        market_value,
        weight,
        unrealized_pnl,
        linked_thesis_id,
        source_run_id,
        native_currency_code,
        market_price_native,
        market_value_native,
        cost_basis_native,
        unrealized_pnl_native,
        fx_rate_to_base,
        fx_rate_snapshot_id,
        currency_conversion_note
    )
    select
        portfolio_id,
        instrument_id,
        {sql_date(result.snapshot_date)},
        quantity,
        cost_basis,
        market_price,
        market_value,
        weight,
        unrealized_pnl,
        null::bigint,
        {source_run_id}::bigint,
        native_currency_code,
        market_price_native,
        market_value_native,
        cost_basis_native,
        unrealized_pnl_native,
        fx_rate_to_base,
        fx_rate_snapshot_id,
        currency_conversion_note
    from resolved_rows
    on conflict (portfolio_id, instrument_id, snapshot_date) do update
    set
        quantity = excluded.quantity,
        cost_basis = excluded.cost_basis,
        market_price = excluded.market_price,
        market_value = excluded.market_value,
        weight = excluded.weight,
        unrealized_pnl = excluded.unrealized_pnl,
        linked_thesis_id = excluded.linked_thesis_id,
        source_run_id = excluded.source_run_id,
        native_currency_code = excluded.native_currency_code,
        market_price_native = excluded.market_price_native,
        market_value_native = excluded.market_value_native,
        cost_basis_native = excluded.cost_basis_native,
        unrealized_pnl_native = excluded.unrealized_pnl_native,
        fx_rate_to_base = excluded.fx_rate_to_base,
        fx_rate_snapshot_id = excluded.fx_rate_snapshot_id,
        currency_conversion_note = excluded.currency_conversion_note
    returning instrument_id, fx_rate_snapshot_id
)
select json_build_object(
    'portfolio_id', (select portfolio_id from upsert_portfolio),
    'source_position_count', (select count(*) from source_holdings),
    'resolved_position_count', (select count(*) from resolved_rows),
    'position_count', (select count(*) from upsert_positions),
    'fx_rate_snapshot_id', (select fx_rate_snapshot_id from upsert_fx limit 1),
    'fx_linked_position_count', (select count(*) from upsert_positions where fx_rate_snapshot_id is not null)
)::text;

commit;
"""


def _fetch_live_payload(
    *,
    config: RuntimeConfig,
    base_currency: str,
    request_executor: Callable[[HttpRequest], FetchResponse],
) -> dict[str, Any]:
    source = TossInvestSource()
    token_response = request_executor(
        source.build_request("oauth_token", {}, config=config, require_credentials=True)
    ).as_json()
    access_token = str(token_response["access_token"])
    accounts = request_executor(
        source.build_request("accounts", {"access_token": access_token}, config=config, require_credentials=True)
    ).as_json()
    account_items = _as_list(_unwrap_result(accounts))
    selected_account_seq = config.tossinvest_account_seq or (
        str(account_items[0].get("accountSeq")) if account_items and isinstance(account_items[0], dict) else ""
    )
    common = {"access_token": access_token, "account_seq": selected_account_seq}
    holdings = request_executor(
        source.build_request("holdings", common, config=config, require_credentials=True)
    ).as_json()
    symbols = ",".join(item["symbol"] for item in _holding_items(_unwrap_result(holdings)) if item.get("symbol"))
    stocks = (
        request_executor(source.build_request("stocks", {"access_token": access_token, "symbols": symbols}, config=config, require_credentials=True)).as_json()
        if symbols
        else {"result": []}
    )
    prices = (
        request_executor(source.build_request("prices", {"access_token": access_token, "symbols": symbols}, config=config, require_credentials=True)).as_json()
        if symbols
        else {"result": []}
    )
    exchange_rate = request_executor(
        source.build_request(
            "exchange_rate",
            {"access_token": access_token, "base_currency": "USD", "quote_currency": base_currency},
            config=config,
            require_credentials=True,
        )
    ).as_json()
    buying_power = [
        request_executor(
            source.build_request(
                "buying_power",
                {**common, "currency": currency},
                config=config,
                require_credentials=True,
            )
        ).as_json()
        for currency in sorted({"KRW", "USD", base_currency})
    ]
    sellable_quantities = [
        request_executor(
            source.build_request(
                "sellable_quantity",
                {**common, "symbol": item["symbol"]},
                config=config,
                require_credentials=True,
            )
        ).as_json()
        for item in _holding_items(_unwrap_result(holdings))
        if item.get("symbol")
    ]
    commissions = request_executor(
        source.build_request("commissions", common, config=config, require_credentials=True)
    ).as_json()
    return {
        "accounts": accounts,
        "holdings": holdings,
        "exchange_rate": exchange_rate,
        "stocks": stocks,
        "prices": prices,
        "buying_power": buying_power,
        "sellable_quantities": sellable_quantities,
        "commissions": commissions,
    }


def _load_fixture_payload(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("TossInvest fixture JSON must contain an object.")
    return payload


def _credentials_configured(config: RuntimeConfig) -> bool:
    return bool(config.tossinvest_client_id and config.tossinvest_client_secret)


def _missing_credentials_report(
    *,
    portfolio_name: str,
    base_currency: str,
    snapshot_date: date,
    selected_account_seq_configured: bool,
) -> dict[str, object]:
    return {
        "report_name": "tossinvest_readonly_sync",
        "provider": TOSSINVEST_PROVIDER_NAME,
        "portfolio_name": portfolio_name,
        "base_currency": base_currency,
        "snapshot_date": snapshot_date.isoformat(),
        "status": "missing_credentials",
        "credentials_configured": False,
        "missing_env_vars": [
            "STOCKANALYSIS_TOSSINVEST_CLIENT_ID",
            "STOCKANALYSIS_TOSSINVEST_CLIENT_SECRET",
        ],
        "selected_account_seq_configured": selected_account_seq_configured,
        "submit_adapter_status": DISABLED_SUBMIT_ADAPTER_STATUS,
        "broker_submit_allowed": False,
        "automatic_order_allowed": False,
        "order_boundary": READ_ONLY_ORDER_BOUNDARY,
        "order_submit_attempted": False,
        "submitted_to_broker": False,
        "secret_free": True,
    }


def _provider_access_error_report(
    *,
    portfolio_name: str,
    base_currency: str,
    snapshot_date: date,
    selected_account_seq_configured: bool,
    error: HTTPError | URLError,
    execute: bool,
) -> dict[str, object]:
    status_code, provider_error, provider_description = _provider_error_details(error)
    config_gap = "ip_address_not_allowed" if provider_description == "IP address not allowed" else "provider_access_error"
    return {
        "report_name": "tossinvest_readonly_sync",
        "provider": TOSSINVEST_PROVIDER_NAME,
        "portfolio_name": portfolio_name,
        "base_currency": base_currency,
        "snapshot_date": snapshot_date.isoformat(),
        "status": "blocked_provider_access",
        "credentials_configured": True,
        "selected_account_seq_configured": selected_account_seq_configured,
        "provider_http_status": status_code,
        "provider_error": provider_error,
        "provider_error_description": provider_description,
        "config_gap": config_gap,
        "operator_action": "allowlist_runtime_egress_ip_for_tossinvest_openapi",
        "submit_adapter_status": DISABLED_SUBMIT_ADAPTER_STATUS,
        "broker_submit_allowed": False,
        "automatic_order_allowed": False,
        "order_boundary": READ_ONLY_ORDER_BOUNDARY,
        "order_submit_attempted": False,
        "submitted_to_broker": False,
        "secret_free": True,
        "mode": "execute" if execute else "dry_run",
        "dry_run": not execute,
    }


def _provider_error_details(error: HTTPError | URLError) -> tuple[int | None, str, str]:
    if isinstance(error, HTTPError):
        body = error.read().decode("utf-8", errors="replace")[:2000]
        provider_error = ""
        description = ""
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {}
        if isinstance(parsed, dict):
            provider_error = str(parsed.get("error") or "")
            raw_description = str(parsed.get("error_description") or parsed.get("message") or "")
            if raw_description.lower() == "ip address not allowed":
                description = "IP address not allowed"
        return error.code, provider_error or f"http_{error.code}", description
    return None, "url_error", ""


def _provider_access_error_summary(report: Mapping[str, object]) -> str:
    status = report.get("provider_http_status")
    config_gap = report.get("config_gap")
    return f"TossInvest readonly sync blocked before write: {config_gap} http_status={status}"


def _unwrap_result(value: Any) -> Any:
    if isinstance(value, dict) and "result" in value:
        return value["result"]
    return value


def _as_list(value: Any) -> list[dict[str, Any]]:
    value = _unwrap_result(value)
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ("items", "holdings", "stocks", "accounts", "commissions", "prices"):
            nested = value.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
    return []


def _holding_items(value: Any) -> list[dict[str, Any]]:
    value = _unwrap_result(value)
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ("items", "holdings", "stocks", "assets"):
            nested = value.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
    return []


def _records_by_symbol(value: Any) -> dict[str, dict[str, Any]]:
    return {
        _symbol(item): item
        for item in _as_list(value)
        if _symbol(item)
    }


def _symbol(item: Mapping[str, Any] | None) -> str:
    if not item:
        return ""
    return str(item.get("symbol") or item.get("ticker") or item.get("stockCode") or "").upper()


def _account_selection_status(accounts: list[dict[str, Any]], selected_account_seq: str | None) -> str:
    if selected_account_seq:
        return "configured_account_seq"
    if accounts:
        return "first_account_selected"
    return "no_account_available"


def _normalize_fx_rate(value: Any) -> TossInvestFxRate | None:
    value = _unwrap_result(value)
    if not isinstance(value, dict) or not value:
        return None
    base_currency = str(value.get("baseCurrency") or value.get("base_currency") or "USD").upper()
    quote_currency = str(value.get("quoteCurrency") or value.get("quote_currency") or "KRW").upper()
    valid_from = str(
        value.get("validFrom")
        or value.get("valid_from")
        or datetime.now(timezone.utc).isoformat()
    )
    return TossInvestFxRate(
        base_currency=base_currency,
        quote_currency=quote_currency,
        rate=_decimal(value.get("rate")),
        mid_rate=_optional_decimal(value.get("midRate") or value.get("mid_rate")),
        basis_point=_optional_decimal(value.get("basisPoint") or value.get("basis_point")),
        valid_from=valid_from,
        valid_until=str(value.get("validUntil") or value.get("valid_until")) if value.get("validUntil") or value.get("valid_until") else None,
        rate_change_type=str(value.get("rateChangeType") or value.get("rate_change_type")) if value.get("rateChangeType") or value.get("rate_change_type") else None,
    )


def _normalize_holding(
    raw: Mapping[str, Any],
    *,
    stock_info: Mapping[str, Any] | None,
    price_info: Mapping[str, Any] | None,
    base_currency: str,
    fx_rate: TossInvestFxRate | None,
) -> TossInvestHolding:
    symbol = _symbol(raw)
    if not symbol:
        raise ValueError("TossInvest holding is missing symbol.")
    native_currency = str(
        raw.get("currency")
        or (stock_info or {}).get("currency")
        or (price_info or {}).get("currency")
        or ("KRW" if symbol.isdigit() else "USD")
    ).upper()
    market_country = str(
        raw.get("marketCountry")
        or raw.get("market_country")
        or (stock_info or {}).get("marketCountry")
        or (stock_info or {}).get("market_country")
        or ("KR" if native_currency == "KRW" else "US")
    ).upper()
    exchange_mic_code = _resolve_exchange_mic_code(raw, stock_info=stock_info, market_country=market_country, symbol=symbol)
    quantity = _decimal(raw.get("quantity") or raw.get("heldQuantity") or raw.get("holdingQuantity"))
    market_price_native = _first_decimal(
        raw,
        ("lastPrice", "currentPrice", "marketPrice", "price"),
        fallback=_first_decimal(price_info or {}, ("price", "lastPrice", "currentPrice"), fallback=None),
    )
    if market_price_native is None:
        raise ValueError(f"TossInvest holding {symbol} is missing market price.")
    cost_basis_native = _first_decimal(raw, ("averagePurchasePrice", "averagePrice", "costBasis"), fallback=None)
    market_value_native = _amount_decimal(raw.get("marketValue"), native_currency)
    if market_value_native is None:
        market_value_native = quantity * market_price_native
    unrealized_pnl_native = _amount_decimal(raw.get("profitLoss") or raw.get("unrealizedProfitLoss"), native_currency)
    fx_rate_to_base, conversion_note = _conversion_rate(native_currency, base_currency=base_currency, fx_rate=fx_rate)
    market_price_base = market_price_native * fx_rate_to_base
    market_value_base = market_value_native * fx_rate_to_base
    cost_basis_base = cost_basis_native * fx_rate_to_base if cost_basis_native is not None else None
    unrealized_pnl_base = unrealized_pnl_native * fx_rate_to_base if unrealized_pnl_native is not None else None
    return TossInvestHolding(
        symbol=symbol,
        name=str(raw.get("name") or raw.get("stockName") or (stock_info or {}).get("name") or symbol),
        market_country=market_country,
        exchange_mic_code=exchange_mic_code,
        instrument_type=_instrument_type(raw, stock_info),
        native_currency=native_currency,
        quantity=quantity,
        market_price_native=_quantize_price(market_price_native),
        market_value_native=_quantize_money(market_value_native),
        cost_basis_native=_quantize_price(cost_basis_native) if cost_basis_native is not None else None,
        unrealized_pnl_native=_quantize_money(unrealized_pnl_native) if unrealized_pnl_native is not None else None,
        fx_rate_to_base=_quantize_fx(fx_rate_to_base),
        market_price_base=_quantize_price(market_price_base),
        market_value_base=_quantize_money(market_value_base),
        cost_basis_base=_quantize_price(cost_basis_base) if cost_basis_base is not None else None,
        unrealized_pnl_base=_quantize_money(unrealized_pnl_base) if unrealized_pnl_base is not None else None,
        conversion_note=conversion_note,
    )


def _conversion_rate(native_currency: str, *, base_currency: str, fx_rate: TossInvestFxRate | None) -> tuple[Decimal, str]:
    if native_currency == base_currency:
        return Decimal("1"), "native_equals_base_currency"
    if fx_rate is None:
        raise ValueError(f"Missing FX rate for {native_currency}/{base_currency} conversion.")
    if fx_rate.base_currency == native_currency and fx_rate.quote_currency == base_currency:
        return fx_rate.conversion_rate, "tossinvest_mid_rate" if fx_rate.mid_rate is not None else "tossinvest_rate_fallback"
    if fx_rate.base_currency == base_currency and fx_rate.quote_currency == native_currency:
        return Decimal("1") / fx_rate.conversion_rate, "tossinvest_inverse_mid_rate" if fx_rate.mid_rate is not None else "tossinvest_inverse_rate_fallback"
    raise ValueError(f"Unsupported FX pair {fx_rate.base_currency}/{fx_rate.quote_currency} for {native_currency}/{base_currency}.")


def _resolve_exchange_mic_code(
    raw: Mapping[str, Any],
    *,
    stock_info: Mapping[str, Any] | None,
    market_country: str,
    symbol: str,
) -> str | None:
    direct = raw.get("micCode") or raw.get("mic_code") or (stock_info or {}).get("micCode") or (stock_info or {}).get("mic_code")
    if direct:
        return str(direct).upper()
    market_text = str(
        raw.get("market")
        or raw.get("exchange")
        or (stock_info or {}).get("market")
        or (stock_info or {}).get("exchange")
        or ""
    ).upper()
    mapping = {
        "NASDAQ": "XNAS",
        "NAS": "XNAS",
        "NYSE": "XNYS",
        "NYS": "XNYS",
        "NYSE_ARCA": "ARCX",
        "AMEX": "ARCX",
        "KRX": "XKRX",
        "KOSPI": "XKRX",
        "KOSDAQ": "XKRX",
        "NXT": "XKRX",
    }
    if market_text in mapping:
        return mapping[market_text]
    if market_country == "KR" and symbol.isdigit():
        return "XKRX"
    return None


def _instrument_type(raw: Mapping[str, Any], stock_info: Mapping[str, Any] | None) -> str:
    raw_type = str(
        raw.get("securityType")
        or raw.get("instrumentType")
        or (stock_info or {}).get("securityType")
        or (stock_info or {}).get("instrumentType")
        or "stock"
    ).lower()
    if "etf" in raw_type or "fund" in raw_type:
        return "etf"
    return "equity"


def _normalize_buying_power(value: Any) -> list[dict[str, str]]:
    rows = [item for envelope in value for item in _record_list(envelope)] if isinstance(value, list) else _record_list(value)
    normalized = []
    for row in rows:
        currency = str(row.get("currency") or "").upper()
        amount = _first_decimal(row, ("cashBuyingPower", "buyingPower", "amount"), fallback=None)
        if currency and amount is not None:
            normalized.append({"currency": currency, "cash_buying_power": _decimal_text(_quantize_money(amount))})
    return normalized


def _normalize_sellable_quantities(value: Any) -> list[dict[str, str]]:
    rows = [item for envelope in value for item in _record_list(envelope)] if isinstance(value, list) else _record_list(value)
    normalized = []
    for row in rows:
        symbol = _symbol(row)
        quantity = _first_decimal(row, ("sellableQuantity", "quantity"), fallback=None)
        if symbol and quantity is not None:
            normalized.append({"symbol": symbol, "sellable_quantity": _decimal_text(quantity)})
    return normalized


def _normalize_commissions(value: Any) -> list[dict[str, str]]:
    normalized = []
    rows = [item for envelope in value for item in _record_list(envelope)] if isinstance(value, list) else _record_list(value)
    for row in rows:
        market_country = str(row.get("marketCountry") or row.get("market_country") or "").upper()
        commission_rate = _optional_decimal(row.get("commissionRate") or row.get("commission_rate"))
        if market_country and commission_rate is not None:
            normalized.append(
                {
                    "market_country": market_country,
                    "commission_rate": _decimal_text(commission_rate),
                    "valid_from": str(row.get("validFrom") or row.get("valid_from") or ""),
                    "valid_until": str(row.get("validUntil") or row.get("valid_until") or ""),
                }
            )
    return normalized


def _record_list(value: Any) -> list[dict[str, Any]]:
    value = _unwrap_result(value)
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ("items", "holdings", "stocks", "accounts", "commissions", "prices"):
            nested = value.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
        return [value]
    return []


def _amount_decimal(value: Any, currency: str) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, (str, int, float, Decimal)):
        return _decimal(value)
    if isinstance(value, dict):
        amount = value.get("amount")
        if isinstance(amount, dict):
            raw = amount.get(currency.lower()) or amount.get(currency.upper()) or amount.get(currency)
            return _optional_decimal(raw)
        if amount is not None and not isinstance(amount, dict):
            return _decimal(amount)
        raw = value.get(currency.lower()) or value.get(currency.upper()) or value.get(currency)
        return _optional_decimal(raw)
    return None


def _first_decimal(mapping: Mapping[str, Any], keys: tuple[str, ...], *, fallback: Decimal | None) -> Decimal | None:
    for key in keys:
        if key in mapping and mapping[key] is not None and str(mapping[key]) != "":
            return _decimal(mapping[key])
    return fallback


def _decimal(value: Any) -> Decimal:
    if value is None or str(value) == "":
        raise ValueError("Decimal value is required.")
    return Decimal(str(value).replace(",", ""))


def _optional_decimal(value: Any) -> Decimal | None:
    if value is None or str(value) == "":
        return None
    return _decimal(value)


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(_MONEY_QUANTIZER, rounding=ROUND_HALF_UP)


def _quantize_price(value: Decimal) -> Decimal:
    return value.quantize(_PRICE_QUANTIZER, rounding=ROUND_HALF_UP)


def _quantize_weight(value: Decimal) -> Decimal:
    return value.quantize(_WEIGHT_QUANTIZER, rounding=ROUND_HALF_UP)


def _quantize_fx(value: Decimal) -> Decimal:
    return value.quantize(_FX_QUANTIZER, rounding=ROUND_HALF_UP)


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _fx_report(fx_rate: TossInvestFxRate | None) -> dict[str, object] | None:
    if fx_rate is None:
        return None
    return {
        "provider": TOSSINVEST_PROVIDER_NAME,
        "base_currency": fx_rate.base_currency,
        "quote_currency": fx_rate.quote_currency,
        "rate": _decimal_text(fx_rate.rate),
        "mid_rate": _decimal_text(fx_rate.mid_rate) if fx_rate.mid_rate is not None else None,
        "conversion_rate": _decimal_text(fx_rate.conversion_rate),
        "conversion_rate_source": "midRate" if fx_rate.mid_rate is not None else "rate",
        "valid_from": fx_rate.valid_from,
        "valid_until": fx_rate.valid_until,
    }


def _render_fx_value_row(fx_rate: TossInvestFxRate | None, *, source_run_id: int) -> str:
    if fx_rate is None:
        return "(null::text, null::text, null::text, null::timestamptz, null::timestamptz, null::numeric, null::numeric, null::numeric, null::text, '{}'::jsonb, null::bigint)"
    evidence = json.dumps(
        {
            "provider": TOSSINVEST_PROVIDER_NAME,
            "conversion_rate_source": "midRate" if fx_rate.mid_rate is not None else "rate",
            "valid_from": fx_rate.valid_from,
            "valid_until": fx_rate.valid_until,
        },
        sort_keys=True,
    )
    return "(" + ", ".join(
        (
            sql_literal(TOSSINVEST_PROVIDER_NAME),
            sql_literal(fx_rate.base_currency),
            sql_literal(fx_rate.quote_currency),
            f"{sql_literal(fx_rate.valid_from)}::timestamptz",
            f"{sql_literal(fx_rate.valid_until)}::timestamptz" if fx_rate.valid_until else "null::timestamptz",
            sql_numeric(fx_rate.rate),
            _sql_numeric_or_null(fx_rate.mid_rate),
            _sql_numeric_or_null(fx_rate.basis_point),
            sql_literal(fx_rate.rate_change_type),
            f"{sql_literal(evidence)}::jsonb",
            f"{source_run_id}::bigint",
        )
    ) + ")"


def _render_holding_value_tuple(holding: TossInvestHolding) -> str:
    return "(" + ", ".join(
        (
            sql_literal(holding.symbol),
            sql_literal(holding.name),
            sql_literal(holding.market_country),
            sql_literal(holding.exchange_mic_code),
            sql_literal(holding.instrument_type),
            sql_literal(holding.native_currency),
            sql_numeric(holding.quantity),
            _sql_numeric_or_null(holding.cost_basis_base),
            sql_numeric(holding.market_price_base),
            sql_numeric(holding.market_value_base),
            "null::numeric",
            _sql_numeric_or_null(holding.unrealized_pnl_base),
            _sql_numeric_or_null(holding.cost_basis_native),
            sql_numeric(holding.market_price_native),
            sql_numeric(holding.market_value_native),
            _sql_numeric_or_null(holding.unrealized_pnl_native),
            sql_numeric(holding.fx_rate_to_base),
            sql_literal(holding.conversion_note),
        )
    ) + ")"


def _sql_numeric_or_null(value: Decimal | None) -> str:
    if value is None:
        return "null::numeric"
    return sql_numeric(value)


def _create_pipeline_run(executor: PsqlCommandExecutor, *, config_json: dict[str, object]) -> int:
    payload = json.dumps(config_json, ensure_ascii=False, sort_keys=True)
    sql = f"""insert into ops.pipeline_run (
    run_kind,
    pipeline_name,
    status,
    config_json
)
values (
    'ingest',
    {sql_literal(TOSSINVEST_READONLY_PIPELINE_NAME)},
    'running',
    {sql_literal(payload)}::jsonb
)
returning run_id;"""
    return int(executor.execute_scalar(sql))


def _mark_pipeline_run_succeeded(
    executor: PsqlCommandExecutor,
    run_id: int,
    *,
    config_json: dict[str, object],
) -> None:
    payload = json.dumps(config_json, ensure_ascii=False, sort_keys=True)
    executor.execute_non_query(
        f"""update ops.pipeline_run
set
    status = 'succeeded',
    ended_at = now(),
    error_summary = null,
    config_json = {sql_literal(payload)}::jsonb
where run_id = {run_id};"""
    )


def _mark_pipeline_run_failed(
    executor: PsqlCommandExecutor,
    run_id: int,
    error_summary: str,
    *,
    config_json: dict[str, object],
) -> None:
    payload = json.dumps(config_json, ensure_ascii=False, sort_keys=True)
    truncated = error_summary.strip()[:2000] or "TossInvest readonly sync failed"
    try:
        executor.execute_non_query(
            f"""update ops.pipeline_run
set
    status = 'failed',
    ended_at = now(),
    error_summary = {sql_literal(truncated)},
    config_json = {sql_literal(payload)}::jsonb
where run_id = {run_id};"""
        )
    except Exception:
        return
