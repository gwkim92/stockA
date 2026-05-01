from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.http import execute_request
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.ingest.registry import get_source

_DEFAULT_REQUESTED_EXCHANGES = ("Nasdaq", "NYSE")
_SUPPORTED_EXCHANGE_TO_MIC = {
    "nasdaq": ("Nasdaq", "XNAS"),
    "nyse": ("NYSE", "XNYS"),
}


@dataclass(frozen=True)
class MarketUniverseRecord:
    cik: str
    company_name: str
    symbol: str
    exchange_name: str | None


@dataclass(frozen=True)
class SelectedMarketUniverseRecord:
    cik: str
    company_name: str
    symbol: str
    exchange_name: str
    mic_code: str


@dataclass(frozen=True)
class MarketUniverseSelection:
    requested_exchanges: tuple[str, ...]
    records: tuple[SelectedMarketUniverseRecord, ...]
    skipped_unsupported_exchange_count: int
    skipped_missing_exchange_count: int

    def summary(
        self,
        *,
        total_record_count: int,
        run_id: int | None = None,
    ) -> dict[str, object]:
        exchange_counts = Counter(record.exchange_name for record in self.records)
        payload: dict[str, object] = {
            "total_record_count": total_record_count,
            "selected_record_count": len(self.records),
            "selected_company_count": len({record.company_name for record in self.records}),
            "requested_exchanges": list(self.requested_exchanges),
            "skipped_unsupported_exchange_count": self.skipped_unsupported_exchange_count,
            "skipped_missing_exchange_count": self.skipped_missing_exchange_count,
            "selected_exchange_counts": dict(sorted(exchange_counts.items())),
            "selected_symbol_preview": [record.symbol for record in self.records[:10]],
        }
        if run_id is not None:
            payload["run_id"] = run_id
        return payload


def load_market_universe_records(
    *,
    config: RuntimeConfig,
    company_tickers_json_path: str | None = None,
) -> tuple[MarketUniverseRecord, ...]:
    payload = _load_company_tickers_payload(
        config=config,
        json_path=company_tickers_json_path,
    )
    return normalize_company_tickers_exchange_payload(payload)


def normalize_company_tickers_exchange_payload(payload: dict[str, Any]) -> tuple[MarketUniverseRecord, ...]:
    fields = payload.get("fields")
    if not isinstance(fields, list):
        raise ValueError("SEC company_tickers_exchange payload does not contain `fields`.")
    field_index = {str(name): index for index, name in enumerate(fields)}
    required_fields = ("cik", "name", "ticker", "exchange")
    missing = [name for name in required_fields if name not in field_index]
    if missing:
        raise ValueError(
            "SEC company_tickers_exchange payload is missing required fields: "
            + ", ".join(sorted(missing))
        )

    data = payload.get("data")
    if not isinstance(data, list):
        raise ValueError("SEC company_tickers_exchange payload does not contain `data`.")

    records: list[MarketUniverseRecord] = []
    for raw_row in data:
        if not isinstance(raw_row, (list, tuple)):
            raise ValueError("SEC company_tickers_exchange payload contains a non-row entry.")
        company_name = _clean_text(_value_at(raw_row, field_index["name"]))
        symbol = _clean_text(_value_at(raw_row, field_index["ticker"]))
        if not company_name or not symbol:
            continue
        exchange_name = _clean_text(_value_at(raw_row, field_index["exchange"]))
        cik_value = _clean_text(_value_at(raw_row, field_index["cik"])) or "0"
        records.append(
            MarketUniverseRecord(
                cik=cik_value.zfill(10),
                company_name=company_name,
                symbol=symbol.upper(),
                exchange_name=exchange_name,
            )
        )

    return tuple(records)


def select_market_universe_records(
    records: tuple[MarketUniverseRecord, ...],
    *,
    exchanges: list[str] | None = None,
    limit: int | None = None,
) -> MarketUniverseSelection:
    requested = _resolve_requested_exchanges(exchanges)
    requested_lookup = {name.lower() for name in requested}

    if limit is not None and limit <= 0:
        raise ValueError("limit must be greater than 0")

    selected: list[SelectedMarketUniverseRecord] = []
    skipped_unsupported = 0
    skipped_missing_exchange = 0
    seen_symbols: set[tuple[str, str]] = set()

    for record in records:
        normalized_exchange = _normalize_exchange_name(record.exchange_name)
        if normalized_exchange is None:
            skipped_missing_exchange += 1
            continue
        supported = _SUPPORTED_EXCHANGE_TO_MIC.get(normalized_exchange)
        if supported is None:
            skipped_unsupported += 1
            continue
        display_exchange, mic_code = supported
        if normalized_exchange not in requested_lookup:
            continue
        dedupe_key = (record.symbol, mic_code)
        if dedupe_key in seen_symbols:
            continue
        seen_symbols.add(dedupe_key)
        selected.append(
            SelectedMarketUniverseRecord(
                cik=record.cik,
                company_name=record.company_name,
                symbol=record.symbol,
                exchange_name=display_exchange,
                mic_code=mic_code,
            )
        )
        if limit is not None and len(selected) >= limit:
            break

    if not selected:
        raise ValueError("No supported company tickers matched the requested exchange filters.")

    return MarketUniverseSelection(
        requested_exchanges=requested,
        records=tuple(selected),
        skipped_unsupported_exchange_count=skipped_unsupported,
        skipped_missing_exchange_count=skipped_missing_exchange,
    )


def render_market_universe_bootstrap_sql(records: tuple[SelectedMarketUniverseRecord, ...]) -> str:
    if not records:
        raise ValueError("At least one selected market universe record is required.")

    value_rows = ",\n        ".join(
        _render_market_universe_value_tuple(record)
        for record in records
    )
    return f"""with source_rows (
    cik,
    legal_name,
    display_name,
    primary_symbol,
    sec_exchange_name,
    mic_code
) as (
    values
        {value_rows}
)
insert into ref.issuer (
    legal_name,
    display_name,
    country_code,
    issuer_type
)
select distinct
    sr.legal_name,
    sr.display_name,
    'US',
    'listed_entity'
from source_rows sr
left join ref.issuer iss
  on lower(iss.legal_name) = lower(sr.legal_name)
 and iss.country_code = 'US'
 and iss.issuer_type = 'listed_entity'
where iss.issuer_id is null;

with source_rows (
    cik,
    legal_name,
    display_name,
    primary_symbol,
    sec_exchange_name,
    mic_code
) as (
    values
        {value_rows}
)
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
    iss.issuer_id,
    ex.exchange_id,
    'US',
    sr.primary_symbol,
    'listed_security',
    'USD',
    sr.display_name,
    true
from source_rows sr
join ref.exchange ex
  on ex.mic_code = sr.mic_code
join ref.issuer iss
  on lower(iss.legal_name) = lower(sr.legal_name)
 and iss.country_code = 'US'
 and iss.issuer_type = 'listed_entity'
on conflict (exchange_id, primary_symbol) do update
set
    issuer_id = excluded.issuer_id,
    market_code = excluded.market_code,
    instrument_type = excluded.instrument_type,
    currency_code = excluded.currency_code,
    name = excluded.name,
    is_active = excluded.is_active,
    delisted_at = null;"""


def run_market_universe_bootstrap(
    *,
    config: RuntimeConfig,
    company_tickers_json_path: str | None = None,
    exchanges: list[str] | None = None,
    limit: int | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    records = load_market_universe_records(
        config=config,
        company_tickers_json_path=company_tickers_json_path,
    )
    selection = select_market_universe_records(
        records,
        exchanges=exchanges,
        limit=limit,
    )

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="market_universe_bootstrap",
        config_json={
            "company_tickers_fixture_path": company_tickers_json_path,
            "requested_exchanges": list(selection.requested_exchanges),
            "limit": limit,
            "selected_record_count": len(selection.records),
        },
    )
    try:
        sql_executor.execute_non_query(render_market_universe_bootstrap_sql(selection.records))
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return selection.summary(total_record_count=len(records), run_id=run_id)


def _load_company_tickers_payload(
    *,
    config: RuntimeConfig,
    json_path: str | None,
) -> dict[str, Any]:
    if json_path:
        return json.loads(Path(json_path).read_text(encoding="utf-8"))
    sec = get_source("sec")
    request = sec.build_request(
        "company_tickers_exchange",
        {},
        config=config,
        require_credentials=True,
    )
    return execute_request(request).as_json()


def _value_at(row: list[Any] | tuple[Any, ...], index: int) -> Any:
    if index >= len(row):
        return None
    return row[index]


def _clean_text(raw_value: object) -> str | None:
    if raw_value is None:
        return None
    value = str(raw_value).strip()
    return value or None


def _resolve_requested_exchanges(exchanges: list[str] | None) -> tuple[str, ...]:
    requested = exchanges or list(_DEFAULT_REQUESTED_EXCHANGES)
    resolved: list[str] = []
    seen: set[str] = set()
    for exchange_name in requested:
        normalized = _normalize_exchange_name(exchange_name)
        if normalized is None:
            raise ValueError("Requested exchange names must not be empty.")
        supported = _SUPPORTED_EXCHANGE_TO_MIC.get(normalized)
        if supported is None:
            raise ValueError(f"Unsupported requested exchange `{exchange_name}`.")
        display_name, _ = supported
        if normalized in seen:
            continue
        seen.add(normalized)
        resolved.append(display_name)
    return tuple(resolved)


def _normalize_exchange_name(exchange_name: str | None) -> str | None:
    if exchange_name is None:
        return None
    cleaned = exchange_name.strip().lower()
    return cleaned or None


def _render_market_universe_value_tuple(record: SelectedMarketUniverseRecord) -> str:
    return "(" + ", ".join(
        (
            sql_literal(record.cik),
            sql_literal(record.company_name),
            sql_literal(record.company_name),
            sql_literal(record.symbol),
            sql_literal(record.exchange_name),
            sql_literal(record.mic_code),
        )
    ) + ")"


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
    truncated = error_summary.strip()[:2000] or "market universe bootstrap failed"
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
