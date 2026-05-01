from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor

_WEIGHT_QUANTIZER = Decimal("0.0001")
_COVERAGE_STATUSES = ("covered", "missing_outcome", "missing_thesis", "missing_weight")


@dataclass(frozen=True)
class PortfolioOutcomeCoverageRow:
    portfolio_id: int
    portfolio_name: str
    snapshot_date: date
    measurement_end_date: date
    instrument_id: int
    primary_symbol: str
    market_value: Decimal
    position_weight: Decimal | None
    linked_thesis_id: int | None
    thesis_title: str | None
    outcome_id: int | None
    outcome_status: str | None
    success_grade: str | None
    coverage_status: str


def load_portfolio_outcome_coverage_rows(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    snapshot_date: date,
    measurement_end_date: date,
    executor: PsqlCommandExecutor | None = None,
) -> tuple[PortfolioOutcomeCoverageRow, ...]:
    if measurement_end_date < snapshot_date:
        raise ValueError("measurement_end_date must be greater than or equal to snapshot_date.")

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload_text = sql_executor.execute_scalar(
        render_portfolio_outcome_coverage_lookup_sql(
            portfolio_name=portfolio_name,
            snapshot_date=snapshot_date,
            measurement_end_date=measurement_end_date,
        )
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Portfolio outcome coverage lookup did not return a JSON array.")

    rows: list[PortfolioOutcomeCoverageRow] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Portfolio outcome coverage lookup returned a non-object row.")
        rows.append(
            PortfolioOutcomeCoverageRow(
                portfolio_id=int(item["portfolio_id"]),
                portfolio_name=str(item["portfolio_name"]),
                snapshot_date=date.fromisoformat(str(item["snapshot_date"])),
                measurement_end_date=date.fromisoformat(str(item["measurement_end_date"])),
                instrument_id=int(item["instrument_id"]),
                primary_symbol=str(item["primary_symbol"]).upper(),
                market_value=Decimal(str(item["market_value"])),
                position_weight=_optional_decimal(item.get("position_weight")),
                linked_thesis_id=int(item["linked_thesis_id"]) if item.get("linked_thesis_id") is not None else None,
                thesis_title=str(item["thesis_title"]) if item.get("thesis_title") is not None else None,
                outcome_id=int(item["outcome_id"]) if item.get("outcome_id") is not None else None,
                outcome_status=str(item["outcome_status"]) if item.get("outcome_status") is not None else None,
                success_grade=str(item["success_grade"]) if item.get("success_grade") is not None else None,
                coverage_status=str(item["coverage_status"]),
            )
        )

    if not rows:
        raise ValueError("No portfolio positions matched the requested coverage report identity.")
    return tuple(rows)


def render_portfolio_outcome_coverage_lookup_sql(
    *,
    portfolio_name: str,
    snapshot_date: date,
    measurement_end_date: date,
) -> str:
    return f"""-- portfolio outcome coverage lookup
with selected_portfolio as (
    select portfolio_id, portfolio_name
    from portfolio.portfolio
    where portfolio_name = {sql_literal(portfolio_name)}
    limit 1
),
position_rows as (
    select
        portfolio.portfolio_id,
        portfolio.portfolio_name,
        position.instrument_id,
        instrument.primary_symbol,
        position.market_value,
        position.weight as position_weight,
        position.linked_thesis_id
    from selected_portfolio portfolio
    join portfolio.position_snapshot position on position.portfolio_id = portfolio.portfolio_id
    join ref.instrument instrument on instrument.instrument_id = position.instrument_id
    where position.snapshot_date = {sql_date(snapshot_date)}
      and position.quantity <> 0
),
coverage_rows as (
    select
        position.portfolio_id,
        position.portfolio_name,
        {sql_date(snapshot_date)} as snapshot_date,
        {sql_date(measurement_end_date)} as measurement_end_date,
        position.instrument_id,
        position.primary_symbol,
        position.market_value,
        position.position_weight,
        position.linked_thesis_id,
        thesis.title as thesis_title,
        outcome.outcome_id,
        outcome.status as outcome_status,
        outcome.success_grade,
        case
            when position.linked_thesis_id is null then 'missing_thesis'
            when position.position_weight is null then 'missing_weight'
            when outcome.outcome_id is null then 'missing_outcome'
            else 'covered'
        end as coverage_status
    from position_rows position
    left join signal.investment_thesis thesis on thesis.thesis_id = position.linked_thesis_id
    left join performance.thesis_outcome outcome
      on outcome.thesis_id = position.linked_thesis_id
     and outcome.measurement_start_date = {sql_date(snapshot_date)}
     and outcome.measurement_end_date = {sql_date(measurement_end_date)}
)
select coalesce(
    json_agg(
        json_build_object(
            'portfolio_id', portfolio_id,
            'portfolio_name', portfolio_name,
            'snapshot_date', snapshot_date,
            'measurement_end_date', measurement_end_date,
            'instrument_id', instrument_id,
            'primary_symbol', primary_symbol,
            'market_value', market_value,
            'position_weight', position_weight,
            'linked_thesis_id', linked_thesis_id,
            'thesis_title', thesis_title,
            'outcome_id', outcome_id,
            'outcome_status', outcome_status,
            'success_grade', success_grade,
            'coverage_status', coverage_status
        )
        order by coverage_status, primary_symbol
    ),
    '[]'::json
)::text
from coverage_rows;"""


def build_portfolio_outcome_coverage_report(rows: tuple[PortfolioOutcomeCoverageRow, ...]) -> dict[str, object]:
    if not rows:
        raise ValueError("At least one portfolio outcome coverage row is required.")

    portfolio_id = rows[0].portfolio_id
    portfolio_name = rows[0].portfolio_name
    snapshot_date = rows[0].snapshot_date
    measurement_end_date = rows[0].measurement_end_date
    if any(row.portfolio_id != portfolio_id for row in rows):
        raise ValueError("Portfolio outcome coverage rows must belong to one portfolio.")
    if any(row.snapshot_date != snapshot_date for row in rows):
        raise ValueError("Portfolio outcome coverage rows must share one snapshot_date.")
    if any(row.measurement_end_date != measurement_end_date for row in rows):
        raise ValueError("Portfolio outcome coverage rows must share one measurement_end_date.")

    status_counts = {status: 0 for status in _COVERAGE_STATUSES}
    weight_by_status = {status: Decimal("0") for status in _COVERAGE_STATUSES}
    total_weight = Decimal("0")
    has_missing_weight_value = False
    for row in rows:
        if row.coverage_status not in status_counts:
            raise ValueError(f"Unsupported coverage status: {row.coverage_status}")
        status_counts[row.coverage_status] += 1
        if row.position_weight is None:
            has_missing_weight_value = True
            continue
        weight = _quantize_weight(row.position_weight)
        weight_by_status[row.coverage_status] += weight
        total_weight += weight

    covered_count = status_counts["covered"]
    covered_weight = weight_by_status["covered"]
    cash_weight = None if has_missing_weight_value else _quantize_weight(max(Decimal("0"), Decimal("1") - total_weight))

    return {
        "portfolio_id": portfolio_id,
        "portfolio_name": portfolio_name,
        "snapshot_date": snapshot_date.isoformat(),
        "measurement_end_date": measurement_end_date.isoformat(),
        "position_count": len(rows),
        "status_counts": status_counts,
        "weight_by_status": {status: str(_quantize_weight(weight)) for status, weight in weight_by_status.items()},
        "total_position_weight": str(_quantize_weight(total_weight)),
        "covered_weight": str(_quantize_weight(covered_weight)),
        "cash_weight": str(cash_weight) if cash_weight is not None else None,
        "coverage_ratio_by_count": str(_ratio(Decimal(covered_count), Decimal(len(rows)))),
        "coverage_ratio_by_weight": str(_ratio(covered_weight, total_weight)) if total_weight > 0 else None,
        "positions": [_render_position(row) for row in rows],
    }


def load_portfolio_outcome_coverage_report(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    snapshot_date: date,
    measurement_end_date: date,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    rows = load_portfolio_outcome_coverage_rows(
        config=config,
        portfolio_name=portfolio_name,
        snapshot_date=snapshot_date,
        measurement_end_date=measurement_end_date,
        executor=executor,
    )
    return build_portfolio_outcome_coverage_report(rows)


def _render_position(row: PortfolioOutcomeCoverageRow) -> dict[str, object]:
    return {
        "symbol": row.primary_symbol,
        "instrument_id": row.instrument_id,
        "coverage_status": row.coverage_status,
        "weight": str(_quantize_weight(row.position_weight)) if row.position_weight is not None else None,
        "market_value": str(row.market_value),
        "linked_thesis_id": row.linked_thesis_id,
        "thesis_title": row.thesis_title,
        "outcome_id": row.outcome_id,
        "outcome_status": row.outcome_status,
        "success_grade": row.success_grade,
    }


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _quantize_weight(value: Decimal) -> Decimal:
    return value.quantize(_WEIGHT_QUANTIZER, rounding=ROUND_HALF_UP)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == 0:
        return Decimal("0.0000")
    return (numerator / denominator).quantize(_WEIGHT_QUANTIZER, rounding=ROUND_HALF_UP)
