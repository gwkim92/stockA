from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

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

    def summary(self) -> dict[str, object]:
        first_date = self.bars[0].trade_date.isoformat() if self.bars else None
        last_date = self.bars[-1].trade_date.isoformat() if self.bars else None
        return {
            "symbol": self.symbol,
            "bar_count": len(self.bars),
            "oldest_trade_date": first_date,
            "latest_trade_date": last_date,
        }


@dataclass(frozen=True)
class _ResolvedInstrument:
    instrument_id: int
    primary_symbol: str
    instrument_name: str


def load_market_price_sync_result(
    symbol: str,
    *,
    config: RuntimeConfig,
    prices_json_path: str | None = None,
    outputsize: str | None = None,
) -> MarketPriceSyncResult:
    payload = _load_prices_payload(
        symbol,
        config=config,
        json_path=prices_json_path,
        outputsize=outputsize,
    )
    return normalize_daily_adjusted_payload(symbol, payload)


def normalize_daily_adjusted_payload(symbol: str, payload: dict[str, Any]) -> MarketPriceSyncResult:
    series = payload.get("Time Series (Daily)")
    if not isinstance(series, dict) or not series:
        raise ValueError(f"Alpha Vantage daily_adjusted payload for `{symbol}` does not contain `Time Series (Daily)`")

    bars: list[MarketDailyPriceBarRecord] = []
    for trade_date_text, raw_item in series.items():
        try:
            bars.append(
                MarketDailyPriceBarRecord(
                    trade_date=date.fromisoformat(str(trade_date_text)),
                    open=_as_decimal(raw_item["1. open"]),
                    high=_as_decimal(raw_item["2. high"]),
                    low=_as_decimal(raw_item["3. low"]),
                    close=_as_decimal(raw_item["4. close"]),
                    adjusted_close=_as_decimal(raw_item["5. adjusted close"]),
                    volume=int(str(raw_item["6. volume"])),
                )
            )
        except (KeyError, ValueError, InvalidOperation) as exc:
            raise ValueError(f"Invalid daily price row for `{symbol}` on `{trade_date_text}`") from exc

    bars.sort(key=lambda record: record.trade_date)
    return MarketPriceSyncResult(symbol=symbol.upper(), bars=tuple(bars))


def run_market_price_upsert(
    symbol: str,
    *,
    config: RuntimeConfig,
    prices_json_path: str | None = None,
    outputsize: str | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    result = load_market_price_sync_result(
        symbol,
        config=config,
        prices_json_path=prices_json_path,
        outputsize=outputsize,
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
            "instrument_id": instrument.instrument_id,
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
    return summary


def run_market_price_batch_upsert(
    symbols: list[str],
    *,
    config: RuntimeConfig,
    fixtures_dir: str | None = None,
    outputsize: str | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    if not symbols:
        raise ValueError("At least one --symbol is required.")

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    requested_symbols = tuple(symbol.upper() for symbol in symbols)
    results: list[dict[str, object]] = []
    succeeded = 0
    failed = 0
    total_bars = 0

    for symbol in requested_symbols:
        prices_json_path = _resolve_fixture_path(symbol, fixtures_dir)
        try:
            summary = run_market_price_upsert(
                symbol,
                config=config,
                prices_json_path=prices_json_path,
                outputsize=outputsize,
                executor=sql_executor,
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
        "succeeded_symbol_count": succeeded,
        "failed_symbol_count": failed,
        "total_bar_count": total_bars,
        "results": results,
    }


def resolve_instrument_for_symbol(
    symbol: str,
    *,
    executor: PsqlCommandExecutor,
) -> _ResolvedInstrument:
    try:
        payload_text = executor.execute_scalar(render_instrument_lookup_by_symbol_sql(symbol))
    except PsqlExecutionError as exc:
        raise ValueError(f"No canonical instrument found for symbol `{symbol}`.") from exc
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
    source_run_id
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
    source_run_id = excluded.source_run_id;"""


def _render_daily_price_value_tuple(
    record: MarketDailyPriceBarRecord,
    *,
    instrument_id: int,
    run_literal: str,
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
        f"{run_literal})"
    )


def _load_prices_payload(
    symbol: str,
    *,
    config: RuntimeConfig,
    json_path: str | None,
    outputsize: str | None,
) -> dict[str, Any]:
    if json_path:
        return json.loads(Path(json_path).read_text(encoding="utf-8"))
    alpha_vantage = get_source("alpha_vantage")
    params = {"symbol": symbol}
    if outputsize:
        params["outputsize"] = outputsize
    request = alpha_vantage.build_request(
        "daily_adjusted",
        params,
        config=config,
        require_credentials=True,
    )
    return execute_request(request).as_json()


def _as_decimal(value: object) -> Decimal:
    return Decimal(str(value))


def _resolve_fixture_path(symbol: str, fixtures_dir: str | None) -> str | None:
    if not fixtures_dir:
        return None
    base_dir = Path(fixtures_dir)
    fixture_path = base_dir / f"alpha_vantage_daily_adjusted_{symbol.upper()}.json"
    if not fixture_path.exists():
        raise FileNotFoundError(f"Missing fixture file: {fixture_path}")
    return str(fixture_path)


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
