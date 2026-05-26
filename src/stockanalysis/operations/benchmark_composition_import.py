from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal, sql_numeric
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_PIPELINE_NAME = "benchmark_composition_import"
DEFAULT_MIN_FULL_COVERAGE_WEIGHT = Decimal("0.9500")
SUPPORTED_SOURCE_TYPES = ("operator_upload", "provider_file")
REQUIRED_COLUMNS = ("symbol", "target_weight")


@dataclass(frozen=True)
class BenchmarkCompositionRow:
    symbol: str
    target_weight: Decimal
    name: str | None = None
    rationale: str | None = None


def load_benchmark_composition_csv(path: str | Path) -> tuple[BenchmarkCompositionRow, ...]:
    rows: list[BenchmarkCompositionRow] = []
    seen_symbols: set[str] = set()
    with Path(path).expanduser().resolve().open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing:
            raise ValueError(f"benchmark holdings CSV missing required columns: {', '.join(missing)}")
        for line_number, raw_row in enumerate(reader, start=2):
            symbol = str(raw_row.get("symbol") or "").strip().upper()
            if not symbol:
                raise ValueError(f"benchmark holdings CSV row {line_number} has empty symbol")
            if symbol in seen_symbols:
                raise ValueError(f"benchmark holdings CSV contains duplicate symbol: {symbol}")
            target_weight = _parse_weight(raw_row.get("target_weight"), line_number=line_number, symbol=symbol)
            seen_symbols.add(symbol)
            rows.append(
                BenchmarkCompositionRow(
                    symbol=symbol,
                    target_weight=target_weight,
                    name=_optional_text(raw_row.get("name")),
                    rationale=_optional_text(raw_row.get("rationale")),
                )
            )
    if not rows:
        raise ValueError("benchmark holdings CSV has no rows")
    return tuple(rows)


def build_benchmark_composition_import_report(
    *,
    benchmark_code: str,
    source_type: str,
    source_name: str,
    source_as_of_date: date,
    valid_from: date,
    rows: tuple[BenchmarkCompositionRow, ...],
    execute: bool = False,
    min_full_coverage_weight: Decimal = DEFAULT_MIN_FULL_COVERAGE_WEIGHT,
) -> dict[str, object]:
    normalized_benchmark_code = benchmark_code.strip().upper()
    if not normalized_benchmark_code:
        raise ValueError("benchmark_code is required")
    if source_type not in SUPPORTED_SOURCE_TYPES:
        raise ValueError(f"source_type must be one of: {', '.join(SUPPORTED_SOURCE_TYPES)}")
    if not source_name.strip():
        raise ValueError("source_name is required")
    if min_full_coverage_weight <= 0 or min_full_coverage_weight > 1:
        raise ValueError("min_full_coverage_weight must be greater than 0 and less than or equal to 1")

    total_weight = sum((row.target_weight for row in rows), Decimal("0"))
    coverage_status = "full_enough_for_drift" if total_weight >= min_full_coverage_weight else "partial_holdings_only"
    return {
        "report_name": DEFAULT_PIPELINE_NAME,
        "status": "planned" if not execute else "running",
        "execute": execute,
        "benchmark_code": normalized_benchmark_code,
        "source_type": source_type,
        "source_name": source_name.strip(),
        "source_as_of_date": source_as_of_date.isoformat(),
        "valid_from": valid_from.isoformat(),
        "component_count": len(rows),
        "target_weight_total": _decimal_text(total_weight),
        "min_full_coverage_weight": _decimal_text(min_full_coverage_weight),
        "coverage_status": coverage_status,
        "full_benchmark_drift_interpretation_allowed": coverage_status == "full_enough_for_drift",
        "recommendation_scoring_mutated": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "top_components": [
            {
                "symbol": row.symbol,
                "target_weight": _decimal_text(row.target_weight),
            }
            for row in sorted(rows, key=lambda item: item.target_weight, reverse=True)[:10]
        ],
        "warnings": _warnings_for_coverage(coverage_status),
    }


def render_benchmark_composition_upsert_sql(
    *,
    benchmark_code: str,
    source_type: str,
    source_name: str,
    source_as_of_date: date,
    valid_from: date,
    rows: tuple[BenchmarkCompositionRow, ...],
    create_missing_instruments: bool = False,
) -> str:
    if not rows:
        raise ValueError("rows are required")
    values = ",\n        ".join(
        "("
        f"{sql_literal(row.symbol)}, "
        f"{sql_literal(_canonical_symbol(row.symbol))}, "
        f"{sql_literal(row.name or row.symbol)}, "
        f"{sql_numeric(row.target_weight)}, "
        f"{sql_literal(row.rationale or _default_rationale(source_type=source_type, source_name=source_name))}"
        ")"
        for row in rows
    )
    missing_instrument_ctes = ""
    guard_missing_cte = """guard_missing as (
    select case
        when exists(select 1 from missing_rows)
        then 1 / 0
        else 1
    end as ok
),
all_resolved_rows as (
    select symbol, instrument_id, target_weight, rationale
    from resolved_rows
)"""
    guard_join = "cross join guard_missing"
    if create_missing_instruments:
        missing_instrument_ctes = """
inserted_issuers as (
    insert into ref.issuer (
        legal_name,
        display_name,
        country_code,
        issuer_type
    )
    select
        missing.name,
        missing.name,
        'US',
        'company'
    from missing_rows missing
    where missing.symbol <> '-'
      and missing.symbol !~ '^[0-9]'
    returning issuer_id, display_name
),
inserted_instruments as (
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
        issuer.issuer_id,
        exchange.exchange_id,
        'US',
        missing.canonical_symbol,
        'listed_security',
        'USD',
        missing.name,
        true
    from missing_rows missing
    join inserted_issuers issuer on issuer.display_name = missing.name
    join ref.exchange exchange on exchange.mic_code = 'XNYS'
    where missing.symbol <> '-'
      and missing.symbol !~ '^[0-9]'
    on conflict (exchange_id, primary_symbol) do update
    set
        name = excluded.name,
        is_active = true
    returning instrument_id, primary_symbol
),
all_resolved_rows as (
    select symbol, instrument_id, target_weight, rationale
    from resolved_rows
    union all
    select
        missing.symbol,
        instrument.instrument_id,
        missing.target_weight,
        missing.rationale
    from missing_rows missing
    join inserted_instruments instrument on instrument.primary_symbol = missing.canonical_symbol
)"""
        guard_missing_cte = missing_instrument_ctes
        guard_join = ""
    return f"""-- benchmark composition upsert
with input_rows(symbol, canonical_symbol, name, target_weight, rationale) as (
    values
        {values}
),
resolved_rows as (
    select distinct on (input_rows.symbol)
        input_rows.symbol,
        instrument.instrument_id,
        input_rows.target_weight,
        input_rows.rationale
    from input_rows
    join ref.instrument instrument
      on upper(instrument.primary_symbol) in (input_rows.symbol, input_rows.canonical_symbol)
     and instrument.is_active
    order by
        input_rows.symbol,
        case when upper(instrument.primary_symbol) = input_rows.symbol then 0 else 1 end,
        instrument.instrument_id
),
missing_rows as (
    select
        input_rows.symbol,
        input_rows.canonical_symbol,
        input_rows.name,
        input_rows.target_weight,
        input_rows.rationale
    from input_rows
    left join resolved_rows resolved on resolved.symbol = input_rows.symbol
    where resolved.instrument_id is null
),
{guard_missing_cte}
insert into ref.benchmark_composition (
    benchmark_code,
    component_instrument_id,
    target_weight,
    source_type,
    source_name,
    source_as_of_date,
    valid_from,
    valid_to,
    confidence,
    rationale
)
select
    {sql_literal(benchmark_code.strip().upper())},
    resolved.instrument_id,
    resolved.target_weight,
    {sql_literal(source_type)},
    {sql_literal(source_name.strip())},
    {sql_date(source_as_of_date)},
    {sql_date(valid_from)},
    null::date,
    0.8500::numeric,
    resolved.rationale
from all_resolved_rows resolved
{guard_join}
on conflict (
    benchmark_code,
    component_instrument_id,
    source_type,
    source_name,
    source_as_of_date,
    valid_from
) do update
set
    target_weight = excluded.target_weight,
    valid_to = excluded.valid_to,
    confidence = excluded.confidence,
    rationale = excluded.rationale,
    updated_at = now();"""


def run_benchmark_composition_import(
    *,
    config: RuntimeConfig,
    holdings_csv: str | Path,
    benchmark_code: str,
    source_type: str,
    source_name: str,
    source_as_of_date: date,
    valid_from: date,
    execute: bool = False,
    min_full_coverage_weight: Decimal = DEFAULT_MIN_FULL_COVERAGE_WEIGHT,
    create_missing_instruments: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    rows = load_benchmark_composition_csv(holdings_csv)
    return run_benchmark_composition_import_rows(
        config=config,
        benchmark_code=benchmark_code,
        source_type=source_type,
        source_name=source_name,
        source_as_of_date=source_as_of_date,
        valid_from=valid_from,
        rows=rows,
        execute=execute,
        min_full_coverage_weight=min_full_coverage_weight,
        create_missing_instruments=create_missing_instruments,
        executor=executor,
    )


def run_benchmark_composition_import_rows(
    *,
    config: RuntimeConfig,
    benchmark_code: str,
    source_type: str,
    source_name: str,
    source_as_of_date: date,
    valid_from: date,
    rows: tuple[BenchmarkCompositionRow, ...],
    execute: bool = False,
    min_full_coverage_weight: Decimal = DEFAULT_MIN_FULL_COVERAGE_WEIGHT,
    create_missing_instruments: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    report = build_benchmark_composition_import_report(
        benchmark_code=benchmark_code,
        source_type=source_type,
        source_name=source_name,
        source_as_of_date=source_as_of_date,
        valid_from=valid_from,
        rows=rows,
        execute=execute,
        min_full_coverage_weight=min_full_coverage_weight,
    )
    if not execute:
        return {**report, "create_missing_instruments": create_missing_instruments}

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "benchmark_code": report["benchmark_code"],
            "source_type": source_type,
            "source_name": source_name,
            "source_as_of_date": source_as_of_date.isoformat(),
            "valid_from": valid_from.isoformat(),
            "component_count": report["component_count"],
            "coverage_status": report["coverage_status"],
            "create_missing_instruments": create_missing_instruments,
        },
    )
    try:
        sql_executor.execute_non_query(
            render_benchmark_composition_upsert_sql(
                benchmark_code=benchmark_code,
                source_type=source_type,
                source_name=source_name,
                source_as_of_date=source_as_of_date,
                valid_from=valid_from,
                rows=rows,
                create_missing_instruments=create_missing_instruments,
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise
    return {**report, "status": "completed", "run_id": run_id, "create_missing_instruments": create_missing_instruments}


def _parse_weight(value: object, *, line_number: int, symbol: str) -> Decimal:
    try:
        weight = Decimal(str(value).strip())
    except (AttributeError, InvalidOperation):
        raise ValueError(f"benchmark holdings CSV row {line_number} has invalid target_weight for {symbol}") from None
    if weight < 0 or weight > 1:
        raise ValueError(f"benchmark holdings CSV row {line_number} target_weight for {symbol} must be between 0 and 1")
    return weight


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _canonical_symbol(symbol: str) -> str:
    return symbol.strip().upper().replace(".", "-")


def _warnings_for_coverage(status: str) -> list[dict[str, object]]:
    if status == "full_enough_for_drift":
        return []
    return [
        {
            "code": "benchmark_composition_partial",
            "message": "구성비 합계가 full drift 해석 기준보다 낮아 partial holdings로만 사용한다.",
        }
    ]


def _default_rationale(*, source_type: str, source_name: str) -> str:
    return f"Benchmark holding imported from {source_type}:{source_name}."
