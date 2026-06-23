from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.http import execute_request
from stockanalysis.ingest.macro.sql import sql_date, sql_literal, sql_numeric
from stockanalysis.ingest.market.price import MarketDailyPriceBarRecord, normalize_tossinvest_candles_payload
from stockanalysis.ingest.models import FetchResponse, HttpRequest
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.ingest.sources.tossinvest import TossInvestSource


TOSSINVEST_MARKET_DATA_PIPELINE_NAME = "tossinvest_market_data_sync"
TOSSINVEST_PROVIDER_COMPARISON_PIPELINE_NAME = "tossinvest_provider_comparison"
TOSSINVEST_PROVIDER_NAME = "tossinvest"
DEFAULT_TOSSINVEST_CANDLE_OUTPUTSIZE = "120"
DEFAULT_TOSSINVEST_MARKET_CODE = "US"
DEFAULT_TOSSINVEST_SCHEDULED_DAILY_OUTPUTSIZE = "30"
DEFAULT_TOSSINVEST_SCHEDULED_MAX_SYMBOLS_PER_RUN = 10
TOSSINVEST_COLLECTION_CADENCE = {
    "toss-reference-kr-daily": "Mon..Fri 08:30 Asia/Seoul",
    "toss-reference-us-daily": "Mon..Fri 08:45 America/New_York",
    "toss-candles-kr-daily": "Mon..Fri 16:10 Asia/Seoul",
    "toss-candles-us-shadow-daily": "Mon..Fri 18:20 America/New_York",
    "toss-priority-microdata-intraday": "Mon..Fri 09:40,12:30,15:55 per market calendar",
    "toss-live-account-readonly": "pre-open/midday/after-close on open market days",
}


@dataclass(frozen=True)
class TossInvestDailyCandle:
    symbol: str
    market_code: str
    currency_code: str
    bar: MarketDailyPriceBarRecord
    evidence: Mapping[str, Any]


@dataclass(frozen=True)
class TossInvestMarketCalendar:
    market_code: str
    calendar_date: date
    is_open: bool
    next_business_day: date | None
    evidence: Mapping[str, Any]


@dataclass(frozen=True)
class TossInvestStockWarning:
    symbol: str
    warning_status: str
    warning_count: int
    warning_types: tuple[str, ...]
    provider_error: str = ""
    evidence: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class TossInvestMarketMicrodata:
    symbol: str
    microdata_status: str
    currency_code: str | None
    best_bid_price: Decimal | None
    best_ask_price: Decimal | None
    latest_trade_price: Decimal | None
    latest_trade_timestamp: str | None
    trade_count: int
    upper_limit_price: Decimal | None
    lower_limit_price: Decimal | None
    orderbook: Mapping[str, Any]
    trades: Mapping[str, Any]
    price_limits: Mapping[str, Any]


@dataclass(frozen=True)
class TossInvestMarketDataResult:
    symbols: tuple[str, ...]
    market_code: str
    sync_mode: str
    as_of_date: date
    credentials_configured: bool
    calendars: tuple[TossInvestMarketCalendar, ...]
    candles: tuple[TossInvestDailyCandle, ...]
    warnings: tuple[TossInvestStockWarning, ...]
    microdata: tuple[TossInvestMarketMicrodata, ...]
    unresolved_symbol_count: int = 0
    provider_skip_reason: str = ""

    def report(self) -> dict[str, object]:
        candle_symbols = sorted({item.symbol for item in self.candles})
        warning_symbols = sorted({item.symbol for item in self.warnings})
        microdata_symbols = sorted({item.symbol for item in self.microdata})
        return {
            "report_name": TOSSINVEST_MARKET_DATA_PIPELINE_NAME,
            "status": "skipped_market_closed" if self.provider_skip_reason else "loaded",
            "provider": TOSSINVEST_PROVIDER_NAME,
            "sync_mode": self.sync_mode,
            "market_code": self.market_code,
            "as_of_date": self.as_of_date.isoformat(),
            "provider_skip_reason": self.provider_skip_reason,
            "credentials_configured": self.credentials_configured,
            "requested_symbol_count": len(self.symbols),
            "requested_symbols": list(self.symbols),
            "calendar_market_count": len(self.calendars),
            "candle_symbol_count": len(candle_symbols),
            "candle_bar_count": len(self.candles),
            "candle_symbols": candle_symbols,
            "stock_warning_symbol_count": len(warning_symbols),
            "stock_warning_symbols": warning_symbols,
            "market_microdata_symbol_count": len(microdata_symbols),
            "market_microdata_symbols": microdata_symbols,
            "unresolved_symbol_count": self.unresolved_symbol_count,
            "canonical_policy": "KR candles may update canonical daily_price_bar; US candles remain shadow evidence.",
            "provider_transition_policy": "US Toss canonical promotion requires provider comparison pass.",
            "collection_cadence": TOSSINVEST_COLLECTION_CADENCE,
            "submit_adapter_status": "disabled_stub",
            "order_submit_attempted": False,
            "submitted_to_broker": False,
            "broker_submit_allowed": False,
            "automatic_order_allowed": False,
            "order_boundary": "read_only_no_order",
            "secret_free": True,
        }


def run_tossinvest_market_data_sync(
    *,
    config: RuntimeConfig,
    symbols: list[str],
    market_code: str = DEFAULT_TOSSINVEST_MARKET_CODE,
    sync_mode: str = "daily_candles",
    as_of_date: date | None = None,
    fixture_json_path: str | None = None,
    outputsize: str = DEFAULT_TOSSINVEST_CANDLE_OUTPUTSIZE,
    max_symbols_per_run: int = 0,
    execute: bool = False,
    dry_run: bool = True,
    executor: PsqlCommandExecutor | None = None,
    request_executor: Callable[[HttpRequest], FetchResponse] = execute_request,
) -> dict[str, object]:
    normalized_symbols = tuple(_normalize_symbol(symbol) for symbol in symbols if str(symbol).strip())
    if not normalized_symbols:
        raise ValueError("At least one TossInvest market data symbol is required.")
    normalized_market = _normalize_market_code(market_code)
    resolved_date = as_of_date or date.today()
    candle_limit = _coerce_tossinvest_candle_outputsize(outputsize)
    selected_symbols, batch_metadata = _select_tossinvest_symbol_batch(
        normalized_symbols,
        max_symbols_per_run=max_symbols_per_run,
        as_of_date=resolved_date,
    )
    credentials_configured = _credentials_configured(config)
    if fixture_json_path is None and not credentials_configured:
        return _blocked_missing_credentials_report(
            symbols=selected_symbols,
            market_code=normalized_market,
            sync_mode=sync_mode,
            as_of_date=resolved_date,
            batch_metadata=batch_metadata,
        )

    payload = (
        json.loads(Path(fixture_json_path).read_text(encoding="utf-8"))
        if fixture_json_path
        else _fetch_live_market_data_payload(
            config=config,
            symbols=selected_symbols,
            market_code=normalized_market,
            sync_mode=sync_mode,
            outputsize=outputsize,
            request_executor=request_executor,
        )
    )
    result = normalize_tossinvest_market_data_payload(
        payload,
        symbols=selected_symbols,
        market_code=normalized_market,
        sync_mode=sync_mode,
        as_of_date=resolved_date,
        credentials_configured=credentials_configured,
        max_bars_per_symbol=candle_limit,
    )
    report = result.report()
    report.update(batch_metadata)
    report["requested_symbol_count_total"] = len(normalized_symbols)
    report["requested_symbols_total"] = list(normalized_symbols)
    report["selected_symbol_count"] = len(selected_symbols)
    report["selected_symbols"] = list(selected_symbols)
    report["candle_outputsize"] = str(outputsize)
    report["candle_max_bars_per_symbol"] = candle_limit
    report["dry_run"] = bool(dry_run or not execute)
    report["execute"] = bool(execute)

    if not execute:
        return report

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=TOSSINVEST_MARKET_DATA_PIPELINE_NAME,
        config_json=report,
    )
    try:
        write_payload = sql_executor.execute_scalar(
            render_tossinvest_market_data_upsert_sql(result, source_run_id=run_id)
        )
        write_result = json.loads(write_payload)
        report = {**report, "status": "succeeded", "run_id": run_id, "write_result": write_result}
        _mark_pipeline_run_succeeded(sql_executor, run_id, config_json=report)
    except Exception as exc:
        report = {**report, "status": "failed", "run_id": run_id, "error": str(exc)[:500]}
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc), config_json=report)
        raise
    return report


def normalize_tossinvest_market_data_payload(
    payload: Mapping[str, Any],
    *,
    symbols: tuple[str, ...],
    market_code: str,
    sync_mode: str,
    as_of_date: date,
    credentials_configured: bool,
    max_bars_per_symbol: int | None = None,
) -> TossInvestMarketDataResult:
    calendars = tuple(_normalize_market_calendar_items(payload, default_date=as_of_date))
    candles = tuple(
        _normalize_candles(
            payload,
            symbols=symbols,
            market_code=market_code,
            max_bars_per_symbol=max_bars_per_symbol,
        )
    )
    warnings = tuple(_normalize_warnings(payload, symbols=symbols))
    microdata = tuple(_normalize_microdata(payload, symbols=symbols))
    return TossInvestMarketDataResult(
        symbols=symbols,
        market_code=market_code,
        sync_mode=sync_mode,
        as_of_date=as_of_date,
        credentials_configured=credentials_configured,
        calendars=calendars,
        candles=candles,
        warnings=warnings,
        microdata=microdata,
        provider_skip_reason=str(payload.get("provider_skip_reason") or ""),
    )


def render_tossinvest_market_data_upsert_sql(
    result: TossInvestMarketDataResult,
    *,
    source_run_id: int,
) -> str:
    candle_values = _render_candle_values(result.candles, source_run_id=source_run_id)
    calendar_values = _render_calendar_values(result.calendars, source_run_id=source_run_id)
    warning_values = _render_warning_values(result.warnings, source_run_id=source_run_id)
    microdata_values = _render_microdata_values(result.microdata, source_run_id=source_run_id)
    statements = ["begin;"]
    if candle_values:
        statements.append(
            f"""with input_candles(
    symbol, market_code, currency_code, trade_date, open, high, low, close, adjusted_close, volume, source_run_id, evidence_json
) as (
    values
        {candle_values}
),
resolved as (
    select
        instrument.instrument_id,
        input_candles.*
    from input_candles
    left join ref.instrument instrument
      on instrument.is_active = true
     and upper(instrument.primary_symbol) = input_candles.symbol
)
insert into market.tossinvest_daily_candle_snapshot (
    instrument_id, symbol, market_code, currency_code, trade_date, open, high, low, close,
    adjusted_close, volume, source_run_id, evidence_json
)
select
    instrument_id, symbol, market_code, currency_code, trade_date, open, high, low, close,
    adjusted_close, volume, source_run_id, evidence_json
from resolved
on conflict (provider, symbol, trade_date) do update
set
    instrument_id = excluded.instrument_id,
    market_code = excluded.market_code,
    currency_code = excluded.currency_code,
    open = excluded.open,
    high = excluded.high,
    low = excluded.low,
    close = excluded.close,
    adjusted_close = excluded.adjusted_close,
    volume = excluded.volume,
    source_run_id = excluded.source_run_id,
    observed_at = now(),
    evidence_json = excluded.evidence_json;"""
        )
        statements.append(
            f"""with input_candles(
    symbol, market_code, currency_code, trade_date, open, high, low, close, adjusted_close, volume, source_run_id
) as (
    values
        {_render_canonical_candle_values(result.candles, source_run_id=source_run_id)}
),
resolved as (
    select
        instrument.instrument_id,
        input_candles.*
    from input_candles
    join ref.instrument instrument
      on instrument.is_active = true
     and upper(instrument.primary_symbol) = input_candles.symbol
    where input_candles.market_code = 'KR'
)
insert into market.daily_price_bar (
    instrument_id, trade_date, open, high, low, close, adjusted_close, volume,
    turnover_value, market_cap, source_run_id, provider
)
select
    instrument_id, trade_date, open, high, low, close, adjusted_close, volume,
    null::numeric, null::numeric, source_run_id, {sql_literal(TOSSINVEST_PROVIDER_NAME)}
from resolved
on conflict (instrument_id, trade_date) do update
set
    open = excluded.open,
    high = excluded.high,
    low = excluded.low,
    close = excluded.close,
    adjusted_close = excluded.adjusted_close,
    volume = excluded.volume,
    turnover_value = excluded.turnover_value,
    market_cap = excluded.market_cap,
    source_run_id = excluded.source_run_id,
    provider = excluded.provider;"""
        )
    if calendar_values:
        statements.append(
            f"""insert into market.tossinvest_market_calendar_snapshot (
    market_code, calendar_date, is_open, next_business_day, source_run_id, evidence_json
)
values
    {calendar_values}
on conflict (provider, market_code, calendar_date) do update
set
    is_open = excluded.is_open,
    next_business_day = excluded.next_business_day,
    source_run_id = excluded.source_run_id,
    observed_at = now(),
    evidence_json = excluded.evidence_json;"""
        )
    if warning_values:
        statements.append(
            f"""with input_warnings(symbol, warning_status, warning_count, warning_types, source_run_id, evidence_json) as (
    values
        {warning_values}
),
resolved as (
    select instrument.instrument_id, input_warnings.*
    from input_warnings
    left join ref.instrument instrument
      on instrument.is_active = true
     and upper(instrument.primary_symbol) = input_warnings.symbol
)
insert into market.tossinvest_stock_warning_snapshot (
    instrument_id, symbol, warning_status, warning_count, warning_types, source_run_id, evidence_json
)
select instrument_id, symbol, warning_status, warning_count, warning_types, source_run_id, evidence_json
from resolved;"""
        )
    if microdata_values:
        statements.append(
            f"""with input_microdata(
    symbol, microdata_status, currency_code, best_bid_price, best_ask_price, latest_trade_price,
    latest_trade_timestamp, trade_count, upper_limit_price, lower_limit_price,
    source_run_id, orderbook_json, trades_json, price_limits_json
) as (
    values
        {microdata_values}
),
resolved as (
    select instrument.instrument_id, input_microdata.*
    from input_microdata
    left join ref.instrument instrument
      on instrument.is_active = true
     and upper(instrument.primary_symbol) = input_microdata.symbol
)
insert into market.tossinvest_market_microdata_snapshot (
    instrument_id, symbol, microdata_status, currency_code, best_bid_price, best_ask_price,
    latest_trade_price, latest_trade_timestamp, trade_count, upper_limit_price, lower_limit_price,
    source_run_id, orderbook_json, trades_json, price_limits_json
)
select
    instrument_id, symbol, microdata_status, currency_code, best_bid_price, best_ask_price,
    latest_trade_price, latest_trade_timestamp, trade_count, upper_limit_price, lower_limit_price,
    source_run_id, orderbook_json, trades_json, price_limits_json
from resolved;"""
        )
    statements.append(
        """select json_build_object(
    'calendar_count', (select count(*) from market.tossinvest_market_calendar_snapshot where source_run_id = %s),
    'candle_bar_count', (select count(*) from market.tossinvest_daily_candle_snapshot where source_run_id = %s),
    'stock_warning_count', (select count(*) from market.tossinvest_stock_warning_snapshot where source_run_id = %s),
    'market_microdata_count', (select count(*) from market.tossinvest_market_microdata_snapshot where source_run_id = %s),
    'canonical_kr_candle_count', (
        select count(*)
        from market.daily_price_bar
        where source_run_id = %s
          and provider = 'tossinvest'
    )
)::text;"""
        % (source_run_id, source_run_id, source_run_id, source_run_id, source_run_id)
    )
    statements.append("commit;")
    return "\n\n".join(statements)


def run_tossinvest_provider_comparison(
    *,
    config: RuntimeConfig,
    symbols: list[str],
    comparison_date: date | None = None,
    lookback_days: int = 5,
    max_diff_bps: Decimal = Decimal("50"),
    max_symbols_per_run: int = 0,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    normalized_symbols = tuple(_normalize_symbol(symbol) for symbol in symbols if str(symbol).strip())
    if not normalized_symbols:
        raise ValueError("At least one TossInvest provider comparison symbol is required.")
    resolved_date = comparison_date or date.today()
    selected_symbols, batch_metadata = _select_tossinvest_symbol_batch(
        normalized_symbols,
        max_symbols_per_run=max_symbols_per_run,
        as_of_date=resolved_date,
    )
    report = {
        "report_name": TOSSINVEST_PROVIDER_COMPARISON_PIPELINE_NAME,
        "status": "not_executed" if not execute else "running",
        "provider": TOSSINVEST_PROVIDER_NAME,
        "symbols": list(selected_symbols),
        "symbol_count": len(selected_symbols),
        "requested_symbol_count_total": len(normalized_symbols),
        "requested_symbols_total": list(normalized_symbols),
        "selected_symbol_count": len(selected_symbols),
        "selected_symbols": list(selected_symbols),
        "comparison_date": resolved_date.isoformat(),
        "lookback_days": lookback_days,
        "max_diff_bps": str(max_diff_bps),
        "canonical_promotion_blocked": True,
        "broker_submit_allowed": False,
        "submitted_to_broker": False,
        "secret_free": True,
    }
    report.update(batch_metadata)
    if not execute:
        return report
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=TOSSINVEST_PROVIDER_COMPARISON_PIPELINE_NAME,
        config_json=report,
    )
    try:
        payload = sql_executor.execute_scalar(
            render_tossinvest_provider_comparison_sql(
                symbols=selected_symbols,
                comparison_date=resolved_date,
                lookback_days=lookback_days,
                max_diff_bps=max_diff_bps,
                source_run_id=run_id,
            )
        )
        write_result = json.loads(payload)
        report = {**report, "status": "succeeded", "run_id": run_id, "write_result": write_result}
        _mark_pipeline_run_succeeded(sql_executor, run_id, config_json=report)
    except Exception as exc:
        report = {**report, "status": "failed", "run_id": run_id, "error": str(exc)[:500]}
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc), config_json=report)
        raise
    return report


def render_tossinvest_provider_comparison_sql(
    *,
    symbols: tuple[str, ...],
    comparison_date: date,
    lookback_days: int,
    max_diff_bps: Decimal,
    source_run_id: int,
) -> str:
    symbol_values = ", ".join(f"({sql_literal(symbol)})" for symbol in symbols)
    return f"""with requested_symbols(symbol) as (
    values {symbol_values}
),
target_instruments as (
    select instrument.instrument_id, instrument.primary_symbol as symbol
    from ref.instrument instrument
    join requested_symbols requested on requested.symbol = upper(instrument.primary_symbol)
    where instrument.is_active = true
),
canonical as (
    select
        instrument.instrument_id,
        instrument.symbol,
        bar.trade_date,
        bar.close,
        coalesce(nullif(bar.provider, ''), 'unknown') as canonical_provider
    from target_instruments instrument
    join market.daily_price_bar bar on bar.instrument_id = instrument.instrument_id
    where bar.trade_date between {sql_date(comparison_date)} - {lookback_days} and {sql_date(comparison_date)}
),
toss as (
    select
        instrument.instrument_id,
        instrument.symbol,
        candle.trade_date,
        candle.close
    from target_instruments instrument
    join market.tossinvest_daily_candle_snapshot candle
      on candle.instrument_id = instrument.instrument_id
    where candle.trade_date between {sql_date(comparison_date)} - {lookback_days} and {sql_date(comparison_date)}
),
joined as (
    select
        coalesce(canonical.instrument_id, toss.instrument_id) as instrument_id,
        coalesce(canonical.symbol, toss.symbol) as symbol,
        coalesce(canonical.trade_date, toss.trade_date) as trade_date,
        canonical.close as canonical_close,
        toss.close as toss_close,
        canonical.canonical_provider
    from canonical
    full outer join toss
      on toss.instrument_id = canonical.instrument_id
     and toss.trade_date = canonical.trade_date
),
summary as (
    select
        instrument.instrument_id,
        instrument.symbol,
        max(joined.trade_date) filter (where joined.canonical_close is not null) as latest_canonical_trade_date,
        max(joined.trade_date) filter (where joined.toss_close is not null) as latest_compared_trade_date,
        count(*) filter (where joined.canonical_close is not null and joined.toss_close is not null)::integer
            as matched_bar_count,
        count(*) filter (where joined.canonical_close is null and joined.toss_close is not null)::integer
            as missing_canonical_count,
        count(*) filter (where joined.canonical_close is not null and joined.toss_close is null)::integer
            as missing_compared_count,
        max(abs((joined.toss_close - joined.canonical_close) / nullif(joined.canonical_close, 0)) * 10000)
            as max_close_diff_bps,
        percentile_cont(0.5) within group (
            order by abs((joined.toss_close - joined.canonical_close) / nullif(joined.canonical_close, 0)) * 10000
        ) as median_close_diff_bps,
        coalesce(max(joined.canonical_provider), 'unknown') as canonical_provider
    from target_instruments instrument
    left join joined on joined.instrument_id = instrument.instrument_id
    group by instrument.instrument_id, instrument.symbol
),
classified as (
    select
        *,
        case
            when matched_bar_count = 0 then 'missing'
            when missing_compared_count > 0 or missing_canonical_count > 0 then 'shadow_collecting'
            when coalesce(max_close_diff_bps, 0) <= {sql_numeric(max_diff_bps)} then 'candidate_ready'
            else 'conflict_review_required'
        end as status,
        case
            when matched_bar_count = 0 then 'no_overlapping_bars'
            when missing_compared_count > 0 then 'toss_missing_canonical_dates'
            when missing_canonical_count > 0 then 'canonical_missing_toss_dates'
            when coalesce(max_close_diff_bps, 0) <= {sql_numeric(max_diff_bps)} then 'within_diff_threshold'
            else 'close_diff_threshold_exceeded'
        end as reason
    from summary
),
upserted as (
    insert into market.tossinvest_provider_comparison_snapshot (
    instrument_id, symbol, comparison_date, canonical_provider, compared_provider,
    latest_canonical_trade_date, latest_compared_trade_date, matched_bar_count,
    missing_canonical_count, missing_compared_count, max_close_diff_bps,
    median_close_diff_bps, status, reason, source_run_id, evidence_json
)
select
    instrument_id,
    symbol,
    {sql_date(comparison_date)},
    canonical_provider,
    {sql_literal(TOSSINVEST_PROVIDER_NAME)},
    latest_canonical_trade_date,
    latest_compared_trade_date,
    matched_bar_count,
    missing_canonical_count,
    missing_compared_count,
    max_close_diff_bps,
    median_close_diff_bps,
    status,
    reason,
    {source_run_id},
    json_build_object('lookback_days', {lookback_days}, 'max_diff_bps', {sql_literal(str(max_diff_bps))})::jsonb
from classified
on conflict (provider, symbol, comparison_date) do update
set
    canonical_provider = excluded.canonical_provider,
    latest_canonical_trade_date = excluded.latest_canonical_trade_date,
    latest_compared_trade_date = excluded.latest_compared_trade_date,
    matched_bar_count = excluded.matched_bar_count,
    missing_canonical_count = excluded.missing_canonical_count,
    missing_compared_count = excluded.missing_compared_count,
    max_close_diff_bps = excluded.max_close_diff_bps,
    median_close_diff_bps = excluded.median_close_diff_bps,
    status = excluded.status,
    reason = excluded.reason,
    source_run_id = excluded.source_run_id,
    observed_at = now(),
    evidence_json = excluded.evidence_json
    returning symbol
)
select json_build_object(
    'comparison_count', (select count(*) from classified),
    'written_count', (select count(*) from upserted),
    'candidate_ready_count', (select count(*) from classified where status = 'candidate_ready'),
    'conflict_review_required_count', (select count(*) from classified where status = 'conflict_review_required'),
    'shadow_collecting_count', (select count(*) from classified where status = 'shadow_collecting'),
    'missing_count', (select count(*) from classified where status = 'missing')
)::text;"""


def _fetch_live_market_data_payload(
    *,
    config: RuntimeConfig,
    symbols: tuple[str, ...],
    market_code: str,
    sync_mode: str,
    outputsize: str,
    request_executor: Callable[[HttpRequest], FetchResponse],
) -> dict[str, Any]:
    source = TossInvestSource()
    token_response = request_executor(
        source.build_request("oauth_token", {}, config=config, require_credentials=True)
    ).as_json()
    access_token = str(token_response["access_token"])
    market_calendar_dataset = "market_calendar_kr" if market_code == "KR" else "market_calendar_us"
    market_calendar_payload = _fetch_optional_json(
        source,
        market_calendar_dataset,
        {"access_token": access_token},
        config=config,
        request_executor=request_executor,
    )
    payload: dict[str, Any] = {
        "market_calendars": {
            market_code: market_calendar_payload
        },
        "candles": {},
        "stock_warnings": {},
        "market_microdata": {"orderbooks": {}, "trades": {}, "price_limits": {}},
    }
    if sync_mode in {"daily_candles", "microdata", "all"} and _calendar_payload_is_open(market_calendar_payload) is False:
        payload["provider_skip_reason"] = "market_closed_by_toss_calendar"
        return payload
    for symbol in symbols:
        if sync_mode in {"daily_candles", "all"}:
            payload["candles"][symbol] = _fetch_optional_json(
                source,
                "candles",
                {
                    "access_token": access_token,
                    "symbol": symbol,
                    "interval": "1d",
                    "count": outputsize,
                    "adjusted": "true",
                },
                config=config,
                request_executor=request_executor,
            )
        if sync_mode in {"reference", "microdata", "all"}:
            payload["stock_warnings"][symbol] = _fetch_optional_json(
                source,
                "stock_warnings",
                {"access_token": access_token, "symbol": symbol},
                config=config,
                request_executor=request_executor,
            )
        if sync_mode in {"reference", "microdata", "all"}:
            payload["market_microdata"]["price_limits"][symbol] = _fetch_optional_json(
                source,
                "price_limits",
                {"access_token": access_token, "symbol": symbol},
                config=config,
                request_executor=request_executor,
            )
        if sync_mode in {"microdata", "all"}:
            payload["market_microdata"]["orderbooks"][symbol] = _fetch_optional_json(
                source,
                "orderbook",
                {"access_token": access_token, "symbol": symbol},
                config=config,
                request_executor=request_executor,
            )
            payload["market_microdata"]["trades"][symbol] = _fetch_optional_json(
                source,
                "trades",
                {"access_token": access_token, "symbol": symbol, "count": "20"},
                config=config,
                request_executor=request_executor,
            )
    return payload


def _normalize_candles(
    payload: Mapping[str, Any],
    *,
    symbols: tuple[str, ...],
    market_code: str,
    max_bars_per_symbol: int | None = None,
) -> list[TossInvestDailyCandle]:
    raw_candles = payload.get("candles")
    if not isinstance(raw_candles, Mapping):
        if len(symbols) == 1 and ("result" in payload or "candles" in _as_dict(payload.get("result"))):
            raw_candles = {symbols[0]: payload}
        else:
            return []
    candles: list[TossInvestDailyCandle] = []
    currency_code = "KRW" if market_code == "KR" else "USD"
    for symbol in symbols:
        symbol_payload = raw_candles.get(symbol) or raw_candles.get(symbol.lower())
        if not isinstance(symbol_payload, Mapping) or "error" in symbol_payload:
            continue
        normalized = normalize_tossinvest_candles_payload(symbol, dict(symbol_payload))
        source_bar_count = len(normalized.bars)
        selected_bars = normalized.bars[-max_bars_per_symbol:] if max_bars_per_symbol else normalized.bars
        compact_evidence = _build_compact_candle_evidence(
            symbol=symbol,
            market_code=market_code,
            source_bar_count=source_bar_count,
            stored_bar_count=len(selected_bars),
            max_bars_per_symbol=max_bars_per_symbol,
            source_payload=symbol_payload,
        )
        for bar in selected_bars:
            candles.append(
                TossInvestDailyCandle(
                    symbol=symbol,
                    market_code=market_code,
                    currency_code=currency_code,
                    bar=bar,
                    evidence=compact_evidence,
                )
            )
    return candles


def _build_compact_candle_evidence(
    *,
    symbol: str,
    market_code: str,
    source_bar_count: int,
    stored_bar_count: int,
    max_bars_per_symbol: int | None,
    source_payload: Mapping[str, Any],
) -> dict[str, Any]:
    unwrapped = _as_dict(_unwrap_result(source_payload))
    evidence: dict[str, Any] = {
        "provider": TOSSINVEST_PROVIDER_NAME,
        "symbol": symbol,
        "market_code": market_code,
        "source_bar_count": source_bar_count,
        "stored_bar_count": stored_bar_count,
        "max_bars_per_symbol": max_bars_per_symbol,
        "raw_candle_payload_stored": False,
        "evidence_policy": "compact_runtime_guard",
    }
    if unwrapped.get("nextBefore") or unwrapped.get("next_before"):
        evidence["next_before"] = str(unwrapped.get("nextBefore") or unwrapped.get("next_before"))
    if source_bar_count > stored_bar_count:
        evidence["trimmed_source_bar_count"] = source_bar_count - stored_bar_count
        evidence["trim_policy"] = f"latest_{stored_bar_count}_bars"
    return evidence


def _normalize_market_calendar_items(
    payload: Mapping[str, Any],
    *,
    default_date: date,
) -> list[TossInvestMarketCalendar]:
    raw_calendars = payload.get("market_calendars") or payload.get("market_calendar") or {}
    if not isinstance(raw_calendars, Mapping):
        return []
    calendars: list[TossInvestMarketCalendar] = []
    for market_code, raw_payload in raw_calendars.items():
        if not isinstance(raw_payload, Mapping) or "error" in raw_payload:
            continue
        unwrapped = _as_dict(_unwrap_result(raw_payload))
        today_payload = _as_dict(unwrapped.get("today"))
        next_business_day_payload = _as_dict(unwrapped.get("nextBusinessDay") or unwrapped.get("next_business_day"))
        date_text = _extract_calendar_date_text(
            unwrapped.get("date")
            or unwrapped.get("calendarDate")
            or unwrapped.get("businessDate")
            or today_payload.get("date")
            or default_date.isoformat()
        )
        next_text = _extract_calendar_date_text(
            next_business_day_payload.get("date")
            or unwrapped.get("nextBusinessDay")
            or unwrapped.get("next_business_day")
            or ""
        )
        calendars.append(
            TossInvestMarketCalendar(
                market_code=_normalize_market_code(str(market_code)),
                calendar_date=date.fromisoformat(date_text[:10]),
                is_open=bool(unwrapped.get("isOpen") or unwrapped.get("today_is_open") or unwrapped.get("open")),
                next_business_day=date.fromisoformat(next_text[:10]) if next_text else None,
                evidence=raw_payload,
            )
        )
    return calendars


def _extract_calendar_date_text(value: Any) -> str:
    if isinstance(value, Mapping):
        return _extract_calendar_date_text(value.get("date") or value.get("calendarDate") or value.get("businessDate") or "")
    return str(value or "").strip()


def _calendar_payload_is_open(payload: Mapping[str, Any]) -> bool | None:
    if "error" in payload:
        return None
    unwrapped = _as_dict(_unwrap_result(payload))
    for key in ("isOpen", "today_is_open", "open"):
        if key in unwrapped:
            return bool(unwrapped.get(key))
    return None


def _normalize_warnings(payload: Mapping[str, Any], *, symbols: tuple[str, ...]) -> list[TossInvestStockWarning]:
    raw_warnings = payload.get("stock_warnings") or {}
    if not isinstance(raw_warnings, Mapping):
        return []
    warnings: list[TossInvestStockWarning] = []
    for symbol in symbols:
        symbol_payload = raw_warnings.get(symbol) or raw_warnings.get(symbol.lower())
        if not isinstance(symbol_payload, Mapping):
            continue
        error = _as_dict(symbol_payload.get("error"))
        if error:
            warnings.append(
                TossInvestStockWarning(
                    symbol=symbol,
                    warning_status="provider_error",
                    warning_count=0,
                    warning_types=(),
                    provider_error=str(error.get("provider_error") or error.get("code") or "provider_error"),
                    evidence=symbol_payload,
                )
            )
            continue
        unwrapped = _unwrap_result(symbol_payload)
        warning_items = _as_list(_as_dict(unwrapped).get("warnings") if isinstance(unwrapped, Mapping) else unwrapped)
        warning_types: list[str] = []
        if warning_items:
            for item in warning_items:
                if isinstance(item, Mapping):
                    value = item.get("warningType") or item.get("warning_type") or item.get("type")
                    if value:
                        warning_types.append(str(value))
                elif item:
                    warning_types.append(str(item))
        if not warning_types:
            for value in _as_list(_as_dict(unwrapped).get("warningTypes")):
                if value:
                    warning_types.append(str(value))
        warnings.append(
            TossInvestStockWarning(
                symbol=symbol,
                warning_status="loaded",
                warning_count=len(warning_types),
                warning_types=tuple(sorted(set(warning_types))),
                evidence=symbol_payload,
            )
        )
    return warnings


def _normalize_microdata(payload: Mapping[str, Any], *, symbols: tuple[str, ...]) -> list[TossInvestMarketMicrodata]:
    raw_microdata = _as_dict(payload.get("market_microdata"))
    orderbooks = _as_dict(raw_microdata.get("orderbooks"))
    trades = _as_dict(raw_microdata.get("trades"))
    price_limits = _as_dict(raw_microdata.get("price_limits"))
    rows: list[TossInvestMarketMicrodata] = []
    for symbol in symbols:
        orderbook = _as_dict(orderbooks.get(symbol) or orderbooks.get(symbol.lower()))
        trade_payload = _as_dict(trades.get(symbol) or trades.get(symbol.lower()))
        limit_payload = _as_dict(price_limits.get(symbol) or price_limits.get(symbol.lower()))
        if not orderbook and not trade_payload and not limit_payload:
            continue
        orderbook_unwrapped = _as_dict(_unwrap_result(orderbook))
        trades_unwrapped = _unwrap_result(trade_payload)
        trade_items = _as_list(_as_dict(trades_unwrapped).get("trades") if isinstance(trades_unwrapped, Mapping) else trades_unwrapped)
        latest_trade = _as_dict(trade_items[0]) if trade_items else {}
        limit_unwrapped = _as_dict(_unwrap_result(limit_payload))
        rows.append(
            TossInvestMarketMicrodata(
                symbol=symbol,
                microdata_status="loaded",
                currency_code=_optional_upper(
                    orderbook_unwrapped.get("currency")
                    or latest_trade.get("currency")
                    or limit_unwrapped.get("currency")
                ),
                best_bid_price=_first_decimal(orderbook_unwrapped, ("bestBidPrice", "best_bid_price", "bidPrice")),
                best_ask_price=_first_decimal(orderbook_unwrapped, ("bestAskPrice", "best_ask_price", "askPrice")),
                latest_trade_price=_first_decimal(latest_trade, ("price", "tradePrice", "trade_price")),
                latest_trade_timestamp=_optional_text(
                    latest_trade.get("timestamp") or latest_trade.get("tradeTimestamp") or latest_trade.get("trade_at")
                ),
                trade_count=len(trade_items),
                upper_limit_price=_first_decimal(limit_unwrapped, ("upperLimitPrice", "upper_limit_price", "upper")),
                lower_limit_price=_first_decimal(limit_unwrapped, ("lowerLimitPrice", "lower_limit_price", "lower")),
                orderbook=orderbook,
                trades=trade_payload,
                price_limits=limit_payload,
            )
        )
    return rows


def _render_candle_values(candles: tuple[TossInvestDailyCandle, ...], *, source_run_id: int) -> str:
    return ",\n        ".join(
        "("
        f"{sql_literal(item.symbol)}, "
        f"{sql_literal(item.market_code)}, "
        f"{sql_literal(item.currency_code)}, "
        f"{sql_date(item.bar.trade_date)}, "
        f"{sql_numeric(item.bar.open)}, "
        f"{sql_numeric(item.bar.high)}, "
        f"{sql_numeric(item.bar.low)}, "
        f"{sql_numeric(item.bar.close)}, "
        f"{sql_numeric(item.bar.adjusted_close)}, "
        f"{item.bar.volume}, "
        f"{source_run_id}, "
        f"{_jsonb_literal(item.evidence)}"
        ")"
        for item in candles
    )


def _render_canonical_candle_values(candles: tuple[TossInvestDailyCandle, ...], *, source_run_id: int) -> str:
    return ",\n        ".join(
        "("
        f"{sql_literal(item.symbol)}, "
        f"{sql_literal(item.market_code)}, "
        f"{sql_literal(item.currency_code)}, "
        f"{sql_date(item.bar.trade_date)}, "
        f"{sql_numeric(item.bar.open)}, "
        f"{sql_numeric(item.bar.high)}, "
        f"{sql_numeric(item.bar.low)}, "
        f"{sql_numeric(item.bar.close)}, "
        f"{sql_numeric(item.bar.adjusted_close)}, "
        f"{item.bar.volume}, "
        f"{source_run_id}"
        ")"
        for item in candles
    )


def _render_calendar_values(calendars: tuple[TossInvestMarketCalendar, ...], *, source_run_id: int) -> str:
    return ",\n    ".join(
        "("
        f"{sql_literal(item.market_code)}, "
        f"{sql_date(item.calendar_date)}, "
        f"{sql_literal(item.is_open)}, "
        f"{sql_date(item.next_business_day) if item.next_business_day else 'null::date'}, "
        f"{source_run_id}, "
        f"{_jsonb_literal(item.evidence)}"
        ")"
        for item in calendars
    )


def _render_warning_values(warnings: tuple[TossInvestStockWarning, ...], *, source_run_id: int) -> str:
    return ",\n        ".join(
        "("
        f"{sql_literal(item.symbol)}, "
        f"{sql_literal(item.warning_status)}, "
        f"{item.warning_count}, "
        f"{_jsonb_literal(list(item.warning_types))}, "
        f"{source_run_id}, "
        f"{_jsonb_literal(item.evidence or {})}"
        ")"
        for item in warnings
    )


def _render_microdata_values(microdata: tuple[TossInvestMarketMicrodata, ...], *, source_run_id: int) -> str:
    return ",\n        ".join(
        "("
        f"{sql_literal(item.symbol)}, "
        f"{sql_literal(item.microdata_status)}, "
        f"{sql_literal(item.currency_code) if item.currency_code else 'null::text'}, "
        f"{_sql_numeric_or_null(item.best_bid_price)}, "
        f"{_sql_numeric_or_null(item.best_ask_price)}, "
        f"{_sql_numeric_or_null(item.latest_trade_price)}, "
        f"{sql_literal(item.latest_trade_timestamp) + '::timestamptz' if item.latest_trade_timestamp else 'null::timestamptz'}, "
        f"{item.trade_count}, "
        f"{_sql_numeric_or_null(item.upper_limit_price)}, "
        f"{_sql_numeric_or_null(item.lower_limit_price)}, "
        f"{source_run_id}, "
        f"{_jsonb_literal(item.orderbook)}, "
        f"{_jsonb_literal(item.trades)}, "
        f"{_jsonb_literal(item.price_limits)}"
        ")"
        for item in microdata
    )


def _create_pipeline_run(
    executor: PsqlCommandExecutor,
    *,
    pipeline_name: str,
    config_json: dict[str, object],
) -> int:
    payload = json.dumps(config_json, ensure_ascii=False, sort_keys=True)
    sql = f"""insert into ops.pipeline_run (
    run_kind,
    pipeline_name,
    status,
    config_json
)
values (
    'ingest',
    {sql_literal(pipeline_name)},
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
    truncated = error_summary.strip()[:2000] or "TossInvest market data sync failed"
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


def _fetch_optional_json(
    source: TossInvestSource,
    dataset_name: str,
    params: dict[str, str],
    *,
    config: RuntimeConfig,
    request_executor: Callable[[HttpRequest], FetchResponse],
) -> dict[str, Any]:
    try:
        return request_executor(
            source.build_request(dataset_name, params, config=config, require_credentials=True)
        ).as_json()
    except (HTTPError, URLError) as exc:
        status_code, provider_error, provider_description = _provider_error_details(exc)
        return {
            "error": {
                "dataset_name": dataset_name,
                "provider_http_status": status_code,
                "provider_error": provider_error,
                "provider_error_description": provider_description,
            }
        }


def _provider_error_details(exc: HTTPError | URLError) -> tuple[int | None, str, str]:
    if isinstance(exc, HTTPError):
        return exc.code, exc.reason or "http_error", _read_error_body(exc)
    return None, "url_error", str(exc.reason)


def _read_error_body(exc: HTTPError) -> str:
    try:
        return exc.read().decode("utf-8", errors="replace")[:500]
    except Exception:
        return ""


def _coerce_tossinvest_candle_outputsize(outputsize: str) -> int:
    text = str(outputsize or "").strip()
    if not text:
        raise ValueError("TossInvest candle outputsize must be an integer between 1 and 200.")
    try:
        count = int(text)
    except ValueError as exc:
        raise ValueError("TossInvest candle outputsize must be an integer between 1 and 200.") from exc
    if count < 1 or count > 200:
        raise ValueError("TossInvest candle outputsize must be between 1 and 200.")
    return count


def _select_tossinvest_symbol_batch(
    symbols: tuple[str, ...],
    *,
    max_symbols_per_run: int,
    as_of_date: date,
) -> tuple[tuple[str, ...], dict[str, object]]:
    max_symbols = int(max_symbols_per_run or 0)
    if max_symbols < 0:
        raise ValueError("TossInvest max_symbols_per_run must be zero or greater.")
    if max_symbols == 0 or max_symbols >= len(symbols):
        return symbols, {
            "symbol_batch_limited": False,
            "max_symbols_per_run": max_symbols,
            "symbol_batch_offset": 0,
        }

    offset = ((as_of_date.toordinal() - 1) * max_symbols) % len(symbols)
    selected = tuple(symbols[(offset + index) % len(symbols)] for index in range(max_symbols))
    return selected, {
        "symbol_batch_limited": True,
        "max_symbols_per_run": max_symbols,
        "symbol_batch_offset": offset,
        "symbol_batch_rotation_policy": "as_of_date_ordinal_x_max_symbols_mod_symbol_count",
    }


def _blocked_missing_credentials_report(
    *,
    symbols: tuple[str, ...],
    market_code: str,
    sync_mode: str,
    as_of_date: date,
    batch_metadata: Mapping[str, object] | None = None,
) -> dict[str, object]:
    report: dict[str, object] = {
        "report_name": TOSSINVEST_MARKET_DATA_PIPELINE_NAME,
        "status": "blocked_missing_credentials",
        "provider": TOSSINVEST_PROVIDER_NAME,
        "sync_mode": sync_mode,
        "market_code": market_code,
        "as_of_date": as_of_date.isoformat(),
        "requested_symbol_count": len(symbols),
        "requested_symbols": list(symbols),
        "credentials_configured": False,
        "missing_env_vars": [
            "STOCKANALYSIS_TOSSINVEST_CLIENT_ID",
            "STOCKANALYSIS_TOSSINVEST_CLIENT_SECRET",
        ],
        "operator_action": "configure_repo_outside_tossinvest_credentials",
        "collection_cadence": TOSSINVEST_COLLECTION_CADENCE,
        "submit_adapter_status": "disabled_stub",
        "order_submit_attempted": False,
        "broker_submit_allowed": False,
        "automatic_order_allowed": False,
        "submitted_to_broker": False,
        "order_boundary": "read_only_no_order",
        "secret_free": True,
    }
    if batch_metadata:
        report.update(batch_metadata)
    return report


def _credentials_configured(config: RuntimeConfig) -> bool:
    return bool(config.tossinvest_client_id and config.tossinvest_client_secret)


def _normalize_symbol(value: str) -> str:
    symbol = str(value).strip().upper()
    if not symbol:
        raise ValueError("TossInvest market data symbol must not be empty.")
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-")
    if any(char not in allowed for char in symbol):
        raise ValueError("TossInvest market data symbol may only contain letters, digits, '.', or '-'.")
    return symbol


def _normalize_market_code(value: str) -> str:
    market_code = value.strip().upper()
    if market_code not in {"KR", "US"}:
        raise ValueError("TossInvest market code must be KR or US.")
    return market_code


def _unwrap_result(payload: Any) -> Any:
    if isinstance(payload, Mapping) and "result" in payload:
        return payload["result"]
    return payload


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value is None:
        return []
    return [value]


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_upper(value: Any) -> str | None:
    text = _optional_text(value)
    return text.upper() if text else None


def _first_decimal(payload: Mapping[str, Any], keys: tuple[str, ...]) -> Decimal | None:
    for key in keys:
        if key in payload and payload[key] not in {None, ""}:
            return _to_decimal(payload[key])
    return None


def _to_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid TossInvest numeric value: {value}") from exc


def _sql_numeric_or_null(value: Decimal | None) -> str:
    return "null::numeric" if value is None else sql_numeric(value)


def _jsonb_literal(value: Any) -> str:
    return f"{sql_literal(json.dumps(value, ensure_ascii=False, sort_keys=True))}::jsonb"


def _format_timestamp(value: datetime | None = None) -> str:
    return (value or datetime.now(timezone.utc)).isoformat()
