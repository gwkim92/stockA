from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.http import execute_request
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor, PsqlExecutionError
from stockanalysis.ingest.registry import get_source


@dataclass(frozen=True)
class MarketDailyPriceBarRecord:
    trade_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adjusted_close: Decimal
    volume: int


@dataclass(frozen=True)
class MarketPriceSyncResult:
    symbol: str
    bars: tuple[MarketDailyPriceBarRecord, ...]
    price_adjustment_mode: str = "adjusted"
    provider: str = "alpha_vantage"

    def summary(self) -> dict[str, object]:
        first_date = self.bars[0].trade_date.isoformat() if self.bars else None
        last_date = self.bars[-1].trade_date.isoformat() if self.bars else None
        return {
            "symbol": self.symbol,
            "provider": self.provider,
            "bar_count": len(self.bars),
            "oldest_trade_date": first_date,
            "latest_trade_date": last_date,
            "price_adjustment_mode": self.price_adjustment_mode,
        }


@dataclass(frozen=True)
class _ResolvedInstrument:
    instrument_id: int
    primary_symbol: str
    instrument_name: str


@dataclass(frozen=True)
class _MarketPriceProviderContext:
    tossinvest_access_token: str | None = None
    auth_request_count: int = 0


def load_market_price_sync_result(
    symbol: str,
    *,
    config: RuntimeConfig,
    prices_json_path: str | None = None,
    outputsize: str | None = None,
    provider: str | None = None,
    provider_context: _MarketPriceProviderContext | None = None,
) -> MarketPriceSyncResult:
    resolved_provider = resolve_market_price_provider(provider)
    payload = _load_prices_payload(
        symbol,
        config=config,
        json_path=prices_json_path,
        outputsize=outputsize,
        provider=resolved_provider,
        provider_context=provider_context,
    )
    return normalize_market_price_payload(symbol, payload, provider=resolved_provider)


def normalize_market_price_payload(
    symbol: str,
    payload: dict[str, Any],
    *,
    provider: str,
) -> MarketPriceSyncResult:
    if provider == "twelve_data":
        return normalize_twelve_data_time_series_payload(symbol, payload)
    if provider == "alpha_vantage":
        return normalize_daily_adjusted_payload(symbol, payload)
    if provider == "tossinvest":
        return normalize_tossinvest_candles_payload(symbol, payload)
    raise ValueError(f"Unsupported market price provider `{provider}`.")


def normalize_daily_adjusted_payload(symbol: str, payload: dict[str, Any]) -> MarketPriceSyncResult:
    series = payload.get("Time Series (Daily)")
    if not isinstance(series, dict) or not series:
        raise ValueError(f"Alpha Vantage daily_adjusted payload for `{symbol}` does not contain `Time Series (Daily)`")

    bars: list[MarketDailyPriceBarRecord] = []
    price_adjustment_mode = "adjusted"
    for trade_date_text, raw_item in series.items():
        try:
            close = _as_decimal(raw_item["4. close"])
            if "5. adjusted close" in raw_item:
                adjusted_close = _as_decimal(raw_item["5. adjusted close"])
                volume = int(str(raw_item["6. volume"]))
            else:
                price_adjustment_mode = "unadjusted_fallback"
                adjusted_close = close
                volume = int(str(raw_item["5. volume"]))
            bars.append(
                MarketDailyPriceBarRecord(
                    trade_date=date.fromisoformat(str(trade_date_text)),
                    open=_as_decimal(raw_item["1. open"]),
                    high=_as_decimal(raw_item["2. high"]),
                    low=_as_decimal(raw_item["3. low"]),
                    close=close,
                    adjusted_close=adjusted_close,
                    volume=volume,
                )
            )
        except (KeyError, ValueError, InvalidOperation) as exc:
            raise ValueError(f"Invalid daily price row for `{symbol}` on `{trade_date_text}`") from exc

    bars.sort(key=lambda record: record.trade_date)
    return MarketPriceSyncResult(
        symbol=symbol.upper(),
        bars=tuple(bars),
        price_adjustment_mode=price_adjustment_mode,
        provider="alpha_vantage",
    )


def normalize_twelve_data_time_series_payload(symbol: str, payload: dict[str, Any]) -> MarketPriceSyncResult:
    status = str(payload.get("status", "")).strip().lower()
    if status and status != "ok":
        message = str(payload.get("message") or payload.get("code") or "unknown Twelve Data error")
        raise ValueError(f"Twelve Data time_series payload for `{symbol}` returned status `{status}`: {message}")
    values = payload.get("values")
    if not isinstance(values, list) or not values:
        raise ValueError(f"Twelve Data time_series payload for `{symbol}` does not contain `values`.")

    bars: list[MarketDailyPriceBarRecord] = []
    for raw_item in values:
        if not isinstance(raw_item, dict):
            raise ValueError(f"Twelve Data time_series payload for `{symbol}` contains a non-object value.")
        trade_date_text = str(raw_item.get("datetime", "")).strip()
        try:
            close = _as_decimal(raw_item["close"])
            bars.append(
                MarketDailyPriceBarRecord(
                    trade_date=date.fromisoformat(trade_date_text),
                    open=_as_decimal(raw_item["open"]),
                    high=_as_decimal(raw_item["high"]),
                    low=_as_decimal(raw_item["low"]),
                    close=close,
                    adjusted_close=close,
                    volume=int(str(raw_item.get("volume", "0") or "0")),
                )
            )
        except (KeyError, ValueError, InvalidOperation) as exc:
            raise ValueError(f"Invalid Twelve Data daily price row for `{symbol}` on `{trade_date_text}`") from exc

    bars.sort(key=lambda record: record.trade_date)
    return MarketPriceSyncResult(
        symbol=symbol.upper(),
        bars=tuple(bars),
        price_adjustment_mode="split_adjusted_provider",
        provider="twelve_data",
    )


def normalize_tossinvest_candles_payload(symbol: str, payload: dict[str, Any]) -> MarketPriceSyncResult:
    error = payload.get("error")
    if isinstance(error, dict):
        code = str(error.get("code") or "unknown")
        message = str(error.get("message") or "unknown TossInvest error")
        raise ValueError(f"TossInvest candles payload for `{symbol}` returned error `{code}`: {message}")

    result = payload.get("result")
    if not isinstance(result, dict):
        result = payload
    candles = result.get("candles") if isinstance(result, dict) else None
    if not isinstance(candles, list) or not candles:
        raise ValueError(f"TossInvest candles payload for `{symbol}` does not contain `result.candles`.")

    bars: list[MarketDailyPriceBarRecord] = []
    for raw_item in candles:
        if not isinstance(raw_item, dict):
            raise ValueError(f"TossInvest candles payload for `{symbol}` contains a non-object candle.")
        timestamp_text = str(raw_item.get("timestamp", "")).strip()
        try:
            close = _as_decimal(raw_item["closePrice"])
            bars.append(
                MarketDailyPriceBarRecord(
                    trade_date=_parse_iso_trade_date(timestamp_text),
                    open=_as_decimal(raw_item["openPrice"]),
                    high=_as_decimal(raw_item["highPrice"]),
                    low=_as_decimal(raw_item["lowPrice"]),
                    close=close,
                    adjusted_close=close,
                    volume=int(str(raw_item.get("volume", "0") or "0")),
                )
            )
        except (KeyError, ValueError, InvalidOperation) as exc:
            raise ValueError(f"Invalid TossInvest daily candle row for `{symbol}` at `{timestamp_text}`") from exc

    bars.sort(key=lambda record: record.trade_date)
    return MarketPriceSyncResult(
        symbol=symbol.upper(),
        bars=tuple(bars),
        price_adjustment_mode="adjusted_provider",
        provider="tossinvest",
    )


def run_market_price_upsert(
    symbol: str,
    *,
    config: RuntimeConfig,
    prices_json_path: str | None = None,
    outputsize: str | None = None,
    provider: str | None = None,
    executor: PsqlCommandExecutor | None = None,
    provider_context: _MarketPriceProviderContext | None = None,
) -> dict[str, object]:
    resolved_provider = resolve_market_price_provider(provider)
    resolved_context = provider_context
    if prices_json_path is None and resolved_context is None:
        resolved_context = _build_market_price_provider_context(resolved_provider, config=config)
    result = load_market_price_sync_result(
        symbol,
        config=config,
        prices_json_path=prices_json_path,
        outputsize=outputsize,
        provider=resolved_provider,
        provider_context=resolved_context,
    )
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    instrument = resolve_instrument_for_symbol(result.symbol, executor=sql_executor)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="market_price_upsert",
        config_json={
            "symbol": result.symbol,
            "prices_fixture_path": prices_json_path,
            "outputsize": outputsize,
            "provider": resolved_provider,
            "instrument_id": instrument.instrument_id,
            "price_adjustment_mode": result.price_adjustment_mode,
        },
    )
    try:
        sql_executor.execute_non_query(
            render_market_price_upsert_sql(
                result,
                instrument_id=instrument.instrument_id,
                source_run_id=run_id,
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    summary = result.summary()
    summary["run_id"] = run_id
    summary["instrument_id"] = instrument.instrument_id
    summary["instrument_symbol"] = instrument.primary_symbol
    summary["provider_auth_request_count"] = resolved_context.auth_request_count if resolved_context else 0
    return summary


def run_market_price_batch_upsert(
    symbols: list[str],
    *,
    config: RuntimeConfig,
    fixtures_dir: str | None = None,
    outputsize: str | None = None,
    provider: str | None = None,
    throttle_seconds: float = 0.0,
    max_requests_per_run: int | None = 25,
    skip_if_fresh: bool = False,
    freshness_date: date | None = None,
    executor: PsqlCommandExecutor | None = None,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    resolved_provider = resolve_market_price_provider(provider)
    if not symbols:
        raise ValueError("At least one --symbol is required.")
    if throttle_seconds < 0:
        raise ValueError("throttle_seconds must be greater than or equal to 0.")
    if max_requests_per_run is not None and max_requests_per_run < 0:
        raise ValueError("max_requests_per_run must be greater than or equal to 0.")

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    requested_symbols = tuple(symbol.upper() for symbol in symbols)
    results: list[dict[str, object]] = []
    succeeded = 0
    failed = 0
    skipped = 0
    total_bars = 0
    provider_request_count = 0
    throttle_sleep_count = 0
    resolved_freshness_date = freshness_date or date.today()
    provider_context: _MarketPriceProviderContext | None = None
    provider_auth_request_count = 0

    for symbol in requested_symbols:
        if skip_if_fresh:
            latest_trade_date = load_latest_market_price_trade_date(symbol, executor=sql_executor)
            if latest_trade_date is not None and latest_trade_date >= resolved_freshness_date:
                skipped += 1
                results.append(
                    {
                        "symbol": symbol,
                        "status": "skipped",
                        "reason": "fresh_price_data_exists",
                        "latest_trade_date": latest_trade_date.isoformat(),
                        "freshness_date": resolved_freshness_date.isoformat(),
                    }
                )
                continue

        prices_json_path = _resolve_fixture_path(symbol, fixtures_dir, provider=resolved_provider)
        uses_provider_request = prices_json_path is None
        if (
            uses_provider_request
            and max_requests_per_run is not None
            and provider_request_count >= max_requests_per_run
        ):
            skipped += 1
            results.append(
                {
                    "symbol": symbol,
                    "status": "skipped",
                    "reason": "request_budget_exhausted",
                    "request_budget": max_requests_per_run,
                }
            )
            continue
        if uses_provider_request:
            if provider_context is None:
                provider_context = _build_market_price_provider_context(resolved_provider, config=config)
                provider_auth_request_count += provider_context.auth_request_count
            if provider_request_count > 0 and throttle_seconds > 0:
                sleeper(throttle_seconds)
                throttle_sleep_count += 1
            provider_request_count += 1
        try:
            summary = run_market_price_upsert(
                symbol,
                config=config,
                prices_json_path=prices_json_path,
                outputsize=outputsize,
                provider=resolved_provider,
                executor=sql_executor,
                provider_context=provider_context if uses_provider_request else None,
            )
        except Exception as exc:
            failed += 1
            results.append(
                {
                    "symbol": symbol,
                    "status": "failed",
                    "error": str(exc),
                }
            )
            continue

        succeeded += 1
        total_bars += int(summary["bar_count"])
        results.append(
            {
                "symbol": symbol,
                "status": "succeeded",
                **summary,
            }
        )

    return {
        "requested_symbol_count": len(requested_symbols),
        "provider": resolved_provider,
        "succeeded_symbol_count": succeeded,
        "failed_symbol_count": failed,
        "skipped_symbol_count": skipped,
        "total_bar_count": total_bars,
        "provider_request_count": provider_request_count,
        "provider_auth_request_count": provider_auth_request_count,
        "max_requests_per_run": max_requests_per_run,
        "throttle_seconds": throttle_seconds,
        "throttle_sleep_count": throttle_sleep_count,
        "skip_if_fresh": skip_if_fresh,
        "freshness_date": resolved_freshness_date.isoformat() if skip_if_fresh else None,
        "results": results,
    }


def load_latest_market_price_trade_date(
    symbol: str,
    *,
    executor: PsqlCommandExecutor,
) -> date | None:
    try:
        value = executor.execute_scalar(render_latest_market_price_trade_date_sql(symbol))
    except PsqlExecutionError as exc:
        if str(exc) == "psql returned no rows for scalar query":
            return None
        raise
    cleaned = value.strip()
    if not cleaned:
        return None
    return date.fromisoformat(cleaned)


def render_latest_market_price_trade_date_sql(symbol: str) -> str:
    return f"""select max(b.trade_date)::text
from ref.instrument i
join market.daily_price_bar b on b.instrument_id = i.instrument_id
where i.is_active = true
  and lower(i.primary_symbol) = lower({sql_literal(symbol)});"""


def resolve_instrument_for_symbol(
    symbol: str,
    *,
    executor: PsqlCommandExecutor,
) -> _ResolvedInstrument:
    try:
        payload_text = executor.execute_scalar(render_instrument_lookup_by_symbol_sql(symbol))
    except PsqlExecutionError as exc:
        if str(exc) == "psql returned no rows for scalar query":
            raise ValueError(f"No canonical instrument found for symbol `{symbol}`.") from exc
        raise
    payload = json.loads(payload_text)
    return _ResolvedInstrument(
        instrument_id=int(payload["instrument_id"]),
        primary_symbol=str(payload["primary_symbol"]),
        instrument_name=str(payload["instrument_name"]),
    )


def render_instrument_lookup_by_symbol_sql(symbol: str) -> str:
    return f"""select json_build_object(
    'instrument_id', i.instrument_id,
    'primary_symbol', i.primary_symbol,
    'instrument_name', i.name
)::text
from ref.instrument i
where i.is_active = true
  and lower(i.primary_symbol) = lower({sql_literal(symbol)})
order by i.instrument_id
limit 1;"""


def render_market_price_upsert_sql(
    result: MarketPriceSyncResult,
    *,
    instrument_id: int,
    source_run_id: int | None = None,
) -> str:
    run_literal = "null::bigint" if source_run_id is None else f"{source_run_id}::bigint"
    value_rows = ",\n    ".join(
        _render_daily_price_value_tuple(
            record,
            instrument_id=instrument_id,
            run_literal=run_literal,
            provider=result.provider,
        )
        for record in result.bars
    )
    return f"""insert into market.daily_price_bar (
    instrument_id,
    trade_date,
    open,
    high,
    low,
    close,
    adjusted_close,
    volume,
    turnover_value,
    market_cap,
    source_run_id,
    provider
)
values
    {value_rows}
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


def _render_daily_price_value_tuple(
    record: MarketDailyPriceBarRecord,
    *,
    instrument_id: int,
    run_literal: str,
    provider: str,
) -> str:
    return (
        f"({instrument_id}, "
        f"{sql_literal(record.trade_date.isoformat())}::date, "
        f"{record.open}::numeric, "
        f"{record.high}::numeric, "
        f"{record.low}::numeric, "
        f"{record.close}::numeric, "
        f"{record.adjusted_close}::numeric, "
        f"{record.volume}, "
        f"null::numeric, "
        f"null::numeric, "
        f"{run_literal}, "
        f"{sql_literal(provider)})"
    )


def _load_prices_payload(
    symbol: str,
    *,
    config: RuntimeConfig,
    json_path: str | None,
    outputsize: str | None,
    provider: str,
    provider_context: _MarketPriceProviderContext | None = None,
) -> dict[str, Any]:
    if json_path:
        return json.loads(Path(json_path).read_text(encoding="utf-8"))
    if provider == "tossinvest":
        context = provider_context or _build_market_price_provider_context(provider, config=config)
        if not context.tossinvest_access_token:
            raise ValueError("TossInvest market price provider did not receive an access token.")
        tossinvest = get_source("tossinvest")
        request = tossinvest.build_request(
            "candles",
            {
                "access_token": context.tossinvest_access_token,
                "symbol": symbol,
                "interval": "1d",
                "count": _resolve_tossinvest_candle_count(outputsize),
                "adjusted": "true",
            },
            config=config,
            require_credentials=True,
        )
        return execute_request(request).as_json()
    if provider == "twelve_data":
        twelve_data = get_source("twelve_data")
        params = {"symbol": symbol}
        if outputsize:
            params["outputsize"] = outputsize
        request = twelve_data.build_request(
            "time_series_daily",
            params,
            config=config,
            require_credentials=True,
        )
        return execute_request(request).as_json()
    alpha_vantage = get_source("alpha_vantage")
    params = {"symbol": symbol}
    if outputsize:
        params["outputsize"] = outputsize
    if _alpha_vantage_price_mode() == "adjusted":
        request = alpha_vantage.build_request(
            "daily_adjusted",
            params,
            config=config,
            require_credentials=True,
        )
        payload = execute_request(request).as_json()
        if _is_premium_daily_adjusted_response(payload):
            fallback_request = alpha_vantage.build_request(
                "daily",
                params,
                config=config,
                require_credentials=True,
            )
            return execute_request(fallback_request).as_json()
        return payload
    request = alpha_vantage.build_request(
        "daily",
        params,
        config=config,
        require_credentials=True,
    )
    return execute_request(request).as_json()


def _as_decimal(value: object) -> Decimal:
    return Decimal(str(value))


def _parse_iso_trade_date(value: str) -> date:
    cleaned = value.strip()
    if len(cleaned) < 10:
        raise ValueError("TossInvest candle timestamp must include an ISO date.")
    return date.fromisoformat(cleaned[:10])


def _resolve_fixture_path(symbol: str, fixtures_dir: str | None, *, provider: str) -> str | None:
    if not fixtures_dir:
        return None
    base_dir = Path(fixtures_dir)
    if provider == "tossinvest":
        fixture_path = base_dir / f"tossinvest_candles_1d_{symbol.upper()}.json"
        if fixture_path.exists():
            return str(fixture_path)
        raise FileNotFoundError(f"Missing fixture file: {fixture_path}")
    if provider == "twelve_data":
        fixture_path = base_dir / f"twelve_data_time_series_daily_{symbol.upper()}.json"
        if fixture_path.exists():
            return str(fixture_path)
        raise FileNotFoundError(f"Missing fixture file: {fixture_path}")
    fixture_path = base_dir / f"alpha_vantage_daily_adjusted_{symbol.upper()}.json"
    if fixture_path.exists():
        return str(fixture_path)
    daily_fixture_path = base_dir / f"alpha_vantage_daily_{symbol.upper()}.json"
    if daily_fixture_path.exists():
        return str(daily_fixture_path)
    raise FileNotFoundError(f"Missing fixture file: {fixture_path}")


def _is_premium_daily_adjusted_response(payload: dict[str, Any]) -> bool:
    information = str(payload.get("Information", ""))
    return "premium endpoint" in information.lower()


def _alpha_vantage_price_mode() -> str:
    value = os.getenv("STOCKANALYSIS_ALPHA_VANTAGE_PRICE_MODE", "daily").strip().lower()
    if value in {"adjusted", "daily_adjusted", "premium"}:
        return "adjusted"
    return "daily"


def resolve_market_price_provider(provider: str | None) -> str:
    value = (provider or os.getenv("STOCKANALYSIS_MARKET_PRICE_PROVIDER", "alpha_vantage")).strip().lower()
    if value in {"alpha_vantage", "alphavantage", "av"}:
        return "alpha_vantage"
    if value in {"twelve_data", "twelvedata", "12data"}:
        return "twelve_data"
    if value in {"tossinvest", "toss_invest", "toss"}:
        return "tossinvest"
    raise ValueError(f"Unsupported market price provider `{provider or value}`.")


def _resolve_market_price_provider(provider: str | None) -> str:
    return resolve_market_price_provider(provider)


def _build_market_price_provider_context(provider: str, *, config: RuntimeConfig) -> _MarketPriceProviderContext:
    if provider != "tossinvest":
        return _MarketPriceProviderContext()
    tossinvest = get_source("tossinvest")
    request = tossinvest.build_request(
        "oauth_token",
        {},
        config=config,
        require_credentials=True,
    )
    payload = execute_request(request).as_json()
    access_token = str(payload.get("access_token") or "").strip()
    if not access_token:
        raise ValueError("TossInvest OAuth response did not include access_token.")
    return _MarketPriceProviderContext(tossinvest_access_token=access_token, auth_request_count=1)


def _resolve_tossinvest_candle_count(outputsize: str | None) -> str:
    if outputsize is None or not outputsize.strip():
        return "200"
    normalized = outputsize.strip().lower()
    if normalized == "compact":
        return "100"
    if normalized == "full":
        return "200"
    try:
        count = int(normalized)
    except ValueError as exc:
        raise ValueError("TossInvest candle outputsize must be compact, full, or an integer between 1 and 200.") from exc
    if count < 1 or count > 200:
        raise ValueError("TossInvest candle outputsize must be between 1 and 200.")
    return str(count)


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


def _mark_pipeline_run_succeeded(executor: PsqlCommandExecutor, run_id: int) -> None:
    executor.execute_non_query(
        f"""update ops.pipeline_run
set
    status = 'succeeded',
    ended_at = now(),
    error_summary = null
where run_id = {run_id};"""
    )


def _mark_pipeline_run_failed(executor: PsqlCommandExecutor, run_id: int, error_summary: str) -> None:
    truncated = error_summary.strip()[:2000] or "market price upsert failed"
    try:
        executor.execute_non_query(
            f"""update ops.pipeline_run
set
    status = 'failed',
    ended_at = now(),
    error_summary = {sql_literal(truncated)}
where run_id = {run_id};"""
        )
    except Exception:
        return
