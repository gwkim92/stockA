from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal, sql_numeric
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)

_DEFAULT_METHODOLOGY = "position_weighted_alpha_v1"
_WEIGHT_QUANTIZER = Decimal("0.0001")
_RETURN_QUANTIZER = Decimal("0.000001")
_BPS_QUANTIZER = Decimal("0.0001")


@dataclass(frozen=True)
class PortfolioAttributionCandidate:
    portfolio_id: int
    portfolio_name: str
    snapshot_date: date
    measurement_start_date: date
    measurement_end_date: date
    instrument_id: int
    primary_symbol: str
    position_weight: Decimal
    linked_thesis_id: int
    thesis_title: str | None
    primary_node_id: int | None
    node_code: str | None
    node_name: str | None
    recommendation_id: int | None
    absolute_return_pct: Decimal
    benchmark_return_pct: Decimal | None
    alpha_pct: Decimal | None
    success_grade: str


@dataclass(frozen=True)
class PortfolioAttributionHeader:
    portfolio_id: int
    portfolio_name: str
    snapshot_date: date
    measurement_start_date: date
    measurement_end_date: date
    methodology: str


@dataclass(frozen=True)
class PortfolioAttributionComponentRow:
    component_type: str
    component_key: str
    instrument_id: int | None
    thesis_id: int | None
    recommendation_id: int | None
    weight: Decimal | None
    return_pct: Decimal | None
    benchmark_return_pct: Decimal | None
    alpha_pct: Decimal | None
    contribution_bps: Decimal
    summary: str


def load_portfolio_attribution_candidates(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    snapshot_date: date,
    measurement_end_date: date,
    methodology: str = _DEFAULT_METHODOLOGY,
    executor: PsqlCommandExecutor | None = None,
) -> tuple[PortfolioAttributionCandidate, ...]:
    if measurement_end_date < snapshot_date:
        raise ValueError("measurement_end_date must be greater than or equal to snapshot_date.")

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload_text = sql_executor.execute_scalar(
        render_portfolio_attribution_candidate_lookup_sql(
            portfolio_name=portfolio_name,
            snapshot_date=snapshot_date,
            measurement_end_date=measurement_end_date,
            methodology=methodology,
        )
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Portfolio attribution candidate lookup did not return a JSON array.")

    candidates: list[PortfolioAttributionCandidate] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Portfolio attribution candidate lookup returned a non-object row.")
        candidates.append(
            PortfolioAttributionCandidate(
                portfolio_id=int(item["portfolio_id"]),
                portfolio_name=str(item["portfolio_name"]),
                snapshot_date=date.fromisoformat(str(item["snapshot_date"])),
                measurement_start_date=date.fromisoformat(str(item["measurement_start_date"])),
                measurement_end_date=date.fromisoformat(str(item["measurement_end_date"])),
                instrument_id=int(item["instrument_id"]),
                primary_symbol=str(item["primary_symbol"]).upper(),
                position_weight=Decimal(str(item["position_weight"])),
                linked_thesis_id=int(item["linked_thesis_id"]),
                thesis_title=str(item["thesis_title"]) if item.get("thesis_title") is not None else None,
                primary_node_id=int(item["primary_node_id"]) if item.get("primary_node_id") is not None else None,
                node_code=str(item["node_code"]) if item.get("node_code") is not None else None,
                node_name=str(item["node_name"]) if item.get("node_name") is not None else None,
                recommendation_id=int(item["recommendation_id"]) if item.get("recommendation_id") is not None else None,
                absolute_return_pct=Decimal(str(item["absolute_return_pct"])),
                benchmark_return_pct=_optional_decimal(item.get("benchmark_return_pct")),
                alpha_pct=_optional_decimal(item.get("alpha_pct")),
                success_grade=str(item["success_grade"]),
            )
        )

    if not candidates:
        raise ValueError("No portfolio attribution candidates matched the requested portfolio snapshot and outcome.")
    return tuple(candidates)


def render_portfolio_attribution_candidate_lookup_sql(
    *,
    portfolio_name: str,
    snapshot_date: date,
    measurement_end_date: date,
    methodology: str,
) -> str:
    return f"""-- portfolio attribution candidate lookup
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
        position.weight as position_weight,
        position.linked_thesis_id
    from selected_portfolio portfolio
    join portfolio.position_snapshot position on position.portfolio_id = portfolio.portfolio_id
    join ref.instrument instrument on instrument.instrument_id = position.instrument_id
    where position.snapshot_date = {sql_date(snapshot_date)}
      and position.quantity <> 0
      and position.weight is not null
      and position.linked_thesis_id is not null
),
candidate_rows as (
    select
        position.portfolio_id,
        position.portfolio_name,
        {sql_date(snapshot_date)} as snapshot_date,
        outcome.measurement_start_date,
        outcome.measurement_end_date,
        position.instrument_id,
        position.primary_symbol,
        position.position_weight,
        position.linked_thesis_id,
        thesis.title as thesis_title,
        thesis.primary_node_id,
        node.code as node_code,
        node.name as node_name,
        outcome.recommendation_id,
        outcome.absolute_return_pct,
        outcome.benchmark_return_pct,
        outcome.alpha_pct,
        outcome.success_grade
    from position_rows position
    join performance.thesis_outcome outcome
      on outcome.thesis_id = position.linked_thesis_id
     and outcome.measurement_start_date = {sql_date(snapshot_date)}
     and outcome.measurement_end_date = {sql_date(measurement_end_date)}
    join signal.investment_thesis thesis on thesis.thesis_id = position.linked_thesis_id
    left join ref.classification_node node on node.node_id = thesis.primary_node_id
)
select coalesce(
    json_agg(
        json_build_object(
            'portfolio_id', portfolio_id,
            'portfolio_name', portfolio_name,
            'snapshot_date', snapshot_date,
            'measurement_start_date', measurement_start_date,
            'measurement_end_date', measurement_end_date,
            'instrument_id', instrument_id,
            'primary_symbol', primary_symbol,
            'position_weight', position_weight,
            'linked_thesis_id', linked_thesis_id,
            'thesis_title', thesis_title,
            'primary_node_id', primary_node_id,
            'node_code', node_code,
            'node_name', node_name,
            'recommendation_id', recommendation_id,
            'absolute_return_pct', absolute_return_pct,
            'benchmark_return_pct', benchmark_return_pct,
            'alpha_pct', alpha_pct,
            'success_grade', success_grade,
            'methodology', {sql_literal(methodology)}
        )
        order by primary_symbol
    ),
    '[]'::json
)::text
from candidate_rows;"""


def build_portfolio_attribution(
    candidates: tuple[PortfolioAttributionCandidate, ...],
    *,
    methodology: str = _DEFAULT_METHODOLOGY,
) -> tuple[PortfolioAttributionHeader, tuple[PortfolioAttributionComponentRow, ...]]:
    if not candidates:
        raise ValueError("At least one portfolio attribution candidate is required.")
    if methodology != _DEFAULT_METHODOLOGY:
        raise ValueError(f"Unsupported portfolio attribution methodology: {methodology}")

    portfolio_id = candidates[0].portfolio_id
    portfolio_name = candidates[0].portfolio_name
    snapshot_date = candidates[0].snapshot_date
    measurement_start_date = candidates[0].measurement_start_date
    measurement_end_date = candidates[0].measurement_end_date
    if any(candidate.portfolio_id != portfolio_id for candidate in candidates):
        raise ValueError("Portfolio attribution candidates must belong to one portfolio.")
    if any(candidate.snapshot_date != snapshot_date for candidate in candidates):
        raise ValueError("Portfolio attribution candidates must share one snapshot_date.")
    if any(candidate.measurement_end_date != measurement_end_date for candidate in candidates):
        raise ValueError("Portfolio attribution candidates must share one measurement_end_date.")

    component_rows: list[PortfolioAttributionComponentRow] = []
    for candidate in candidates:
        contribution_bps = _position_contribution_bps(candidate)
        metric_name = "alpha" if candidate.alpha_pct is not None else "absolute return"
        component_rows.append(
            PortfolioAttributionComponentRow(
                component_type="security_selection",
                component_key=candidate.primary_symbol,
                instrument_id=candidate.instrument_id,
                thesis_id=candidate.linked_thesis_id,
                recommendation_id=candidate.recommendation_id,
                weight=_quantize_weight(candidate.position_weight),
                return_pct=_quantize_return(candidate.absolute_return_pct),
                benchmark_return_pct=_quantize_return_optional(candidate.benchmark_return_pct),
                alpha_pct=_quantize_return_optional(candidate.alpha_pct),
                contribution_bps=contribution_bps,
                summary=(
                    f"{candidate.primary_symbol} {metric_name} contribution "
                    f"{contribution_bps} bps from weight {_quantize_weight(candidate.position_weight)}."
                ),
            )
        )

    component_rows.extend(_build_theme_components(candidates))
    component_rows.append(_build_cash_component(candidates))

    header = PortfolioAttributionHeader(
        portfolio_id=portfolio_id,
        portfolio_name=portfolio_name,
        snapshot_date=snapshot_date,
        measurement_start_date=measurement_start_date,
        measurement_end_date=measurement_end_date,
        methodology=methodology,
    )
    return header, tuple(component_rows)


def render_portfolio_attribution_upsert_sql(
    header: PortfolioAttributionHeader,
    component_rows: tuple[PortfolioAttributionComponentRow, ...],
    *,
    source_run_id: int,
) -> str:
    if not component_rows:
        raise ValueError("At least one portfolio attribution component row is required.")
    value_rows = ",\n        ".join(_render_component_value_tuple(row) for row in component_rows)
    return f"""begin;

with upsert_run as (
    insert into performance.attribution_run (
        portfolio_id,
        snapshot_date,
        measurement_start_date,
        measurement_end_date,
        methodology,
        source_run_id
    )
    values (
        {header.portfolio_id}::bigint,
        {sql_date(header.snapshot_date)},
        {sql_date(header.measurement_start_date)},
        {sql_date(header.measurement_end_date)},
        {_sql_text(header.methodology)},
        {source_run_id}::bigint
    )
    on conflict (portfolio_id, snapshot_date, measurement_end_date, methodology) do update
    set
        measurement_start_date = excluded.measurement_start_date,
        source_run_id = excluded.source_run_id
    returning attribution_run_id
),
delete_existing_components as (
    delete from performance.attribution_component
    where attribution_run_id = (select attribution_run_id from upsert_run)
    returning attribution_component_id
),
source_components (
    component_type,
    component_key,
    instrument_id,
    thesis_id,
    recommendation_id,
    weight,
    return_pct,
    benchmark_return_pct,
    alpha_pct,
    contribution_bps,
    summary
) as (
    values
        {value_rows}
),
insert_components as (
    insert into performance.attribution_component (
        attribution_run_id,
        component_type,
        component_key,
        instrument_id,
        thesis_id,
        recommendation_id,
        weight,
        return_pct,
        benchmark_return_pct,
        alpha_pct,
        contribution_bps,
        summary
    )
    select
        upsert_run.attribution_run_id,
        source_components.component_type,
        source_components.component_key,
        source_components.instrument_id,
        source_components.thesis_id,
        source_components.recommendation_id,
        source_components.weight,
        source_components.return_pct,
        source_components.benchmark_return_pct,
        source_components.alpha_pct,
        source_components.contribution_bps,
        source_components.summary
    from upsert_run
    join source_components on true
    returning attribution_component_id
)
select json_build_object(
    'attribution_run_id', (select attribution_run_id from upsert_run),
    'deleted_component_count', (select count(*) from delete_existing_components),
    'component_count', (select count(*) from insert_components)
)::text;

commit;
"""


def run_portfolio_attribution_bootstrap(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    snapshot_date: date,
    measurement_end_date: date,
    methodology: str = _DEFAULT_METHODOLOGY,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    candidates = load_portfolio_attribution_candidates(
        config=config,
        portfolio_name=portfolio_name,
        snapshot_date=snapshot_date,
        measurement_end_date=measurement_end_date,
        methodology=methodology,
        executor=sql_executor,
    )
    header, component_rows = build_portfolio_attribution(candidates, methodology=methodology)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="portfolio_attribution_bootstrap",
        config_json={
            "portfolio_name": portfolio_name,
            "snapshot_date": snapshot_date.isoformat(),
            "measurement_end_date": measurement_end_date.isoformat(),
            "methodology": methodology,
            "candidate_count": len(candidates),
            "component_count": len(component_rows),
        },
    )
    try:
        result = json.loads(
            sql_executor.execute_scalar(
                render_portfolio_attribution_upsert_sql(header, component_rows, source_run_id=run_id)
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return {
        "run_id": run_id,
        "attribution_run_id": int(result["attribution_run_id"]),
        "portfolio_id": header.portfolio_id,
        "portfolio_name": header.portfolio_name,
        "snapshot_date": header.snapshot_date.isoformat(),
        "measurement_start_date": header.measurement_start_date.isoformat(),
        "measurement_end_date": header.measurement_end_date.isoformat(),
        "methodology": header.methodology,
        "candidate_count": len(candidates),
        "component_count": int(result["component_count"]),
        "component_type_counts": _component_type_counts(component_rows),
        "contribution_bps_by_type": _contribution_bps_by_type(component_rows),
        "symbol_preview": [candidate.primary_symbol for candidate in candidates[:10]],
    }


def _build_theme_components(
    candidates: tuple[PortfolioAttributionCandidate, ...],
) -> tuple[PortfolioAttributionComponentRow, ...]:
    grouped: dict[str, list[PortfolioAttributionCandidate]] = {}
    for candidate in candidates:
        key = candidate.node_code or "UNCLASSIFIED"
        grouped.setdefault(key, []).append(candidate)

    rows: list[PortfolioAttributionComponentRow] = []
    for key, group in sorted(grouped.items()):
        weight = sum((candidate.position_weight for candidate in group), Decimal("0"))
        contribution_bps = _quantize_bps(sum((_position_contribution_bps(candidate) for candidate in group), Decimal("0")))
        rows.append(
            PortfolioAttributionComponentRow(
                component_type="theme_exposure",
                component_key=key,
                instrument_id=None,
                thesis_id=None,
                recommendation_id=None,
                weight=_quantize_weight(weight),
                return_pct=_weighted_average_return(group, "absolute_return_pct"),
                benchmark_return_pct=_weighted_average_return(group, "benchmark_return_pct"),
                alpha_pct=_weighted_average_return(group, "alpha_pct"),
                contribution_bps=contribution_bps,
                summary=f"{key} theme exposure contribution {contribution_bps} bps across {len(group)} positions.",
            )
        )
    return tuple(rows)


def _build_cash_component(
    candidates: tuple[PortfolioAttributionCandidate, ...],
) -> PortfolioAttributionComponentRow:
    invested_weight = sum((candidate.position_weight for candidate in candidates), Decimal("0"))
    cash_weight = _quantize_weight(max(Decimal("0"), Decimal("1") - invested_weight))
    return PortfolioAttributionComponentRow(
        component_type="cash_timing",
        component_key="CASH",
        instrument_id=None,
        thesis_id=None,
        recommendation_id=None,
        weight=cash_weight,
        return_pct=None,
        benchmark_return_pct=None,
        alpha_pct=None,
        contribution_bps=Decimal("0.0000"),
        summary=f"Uninvested cash weight {cash_weight} is tracked with zero attribution in v1.",
    )


def _position_contribution_bps(candidate: PortfolioAttributionCandidate) -> Decimal:
    performance_metric = candidate.alpha_pct if candidate.alpha_pct is not None else candidate.absolute_return_pct
    return _quantize_bps(candidate.position_weight * performance_metric * Decimal("10000"))


def _weighted_average_return(candidates: list[PortfolioAttributionCandidate], field_name: str) -> Decimal | None:
    weighted_total = Decimal("0")
    weight_total = Decimal("0")
    for candidate in candidates:
        value = getattr(candidate, field_name)
        if value is None:
            continue
        weighted_total += candidate.position_weight * value
        weight_total += candidate.position_weight
    if weight_total == 0:
        return None
    return _quantize_return(weighted_total / weight_total)


def _component_type_counts(component_rows: tuple[PortfolioAttributionComponentRow, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in component_rows:
        counts[row.component_type] = counts.get(row.component_type, 0) + 1
    return counts


def _contribution_bps_by_type(component_rows: tuple[PortfolioAttributionComponentRow, ...]) -> dict[str, str]:
    contributions: dict[str, Decimal] = {}
    for row in component_rows:
        contributions[row.component_type] = contributions.get(row.component_type, Decimal("0")) + row.contribution_bps
    return {component_type: str(_quantize_bps(contribution)) for component_type, contribution in contributions.items()}


def _render_component_value_tuple(row: PortfolioAttributionComponentRow) -> str:
    return "(" + ", ".join(
        (
            _sql_text(row.component_type),
            _sql_text(row.component_key),
            _sql_bigint_or_null(row.instrument_id),
            _sql_bigint_or_null(row.thesis_id),
            _sql_bigint_or_null(row.recommendation_id),
            _sql_numeric_or_null(row.weight),
            _sql_numeric_or_null(row.return_pct),
            _sql_numeric_or_null(row.benchmark_return_pct),
            _sql_numeric_or_null(row.alpha_pct),
            sql_numeric(row.contribution_bps),
            _sql_text(row.summary),
        )
    ) + ")"


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _quantize_weight(value: Decimal) -> Decimal:
    return value.quantize(_WEIGHT_QUANTIZER, rounding=ROUND_HALF_UP)


def _quantize_return(value: Decimal) -> Decimal:
    return value.quantize(_RETURN_QUANTIZER, rounding=ROUND_HALF_UP)


def _quantize_return_optional(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return _quantize_return(value)


def _quantize_bps(value: Decimal) -> Decimal:
    return value.quantize(_BPS_QUANTIZER, rounding=ROUND_HALF_UP)


def _sql_bigint_or_null(value: int | None) -> str:
    if value is None:
        return "null::bigint"
    return f"{value}::bigint"


def _sql_numeric_or_null(value: Decimal | None) -> str:
    if value is None:
        return "null::numeric"
    return sql_numeric(value)


def _sql_text(value: str) -> str:
    return f"{sql_literal(value)}::text"
