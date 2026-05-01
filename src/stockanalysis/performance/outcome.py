from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal, sql_numeric
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)

_DEFAULT_MARKET_CODE = "US"
_DEFAULT_OUTCOME_VERSION = "bootstrap-v1"
_DEFAULT_SCHEDULE_HORIZON_DAYS = (30, 90, 180, 365)
_DECIMAL_QUANTIZER = Decimal("0.000001")


@dataclass(frozen=True)
class PerformanceOutcomeCandidate:
    batch_id: int
    recommendation_id: int
    thesis_id: int | None
    instrument_id: int
    primary_symbol: str
    recommendation_score: Decimal
    recommendation_bucket: str
    recommendation_action: str
    thesis_title: str | None
    thesis_status: str | None
    benchmark_code: str | None
    measurement_start_date: date
    measurement_end_date: date
    entry_price: Decimal
    exit_price: Decimal
    min_price: Decimal
    benchmark_entry_price: Decimal | None
    benchmark_exit_price: Decimal | None


@dataclass(frozen=True)
class RecommendationOutcomeRow:
    recommendation_id: int
    thesis_id: int | None
    primary_symbol: str
    measurement_start_date: date
    measurement_end_date: date
    horizon_days: int
    entry_price: Decimal
    exit_price: Decimal
    absolute_return_pct: Decimal
    benchmark_code: str | None
    benchmark_return_pct: Decimal | None
    alpha_pct: Decimal | None
    max_drawdown_pct: Decimal
    outcome_label: str


@dataclass(frozen=True)
class ThesisOutcomeRow:
    thesis_id: int
    recommendation_id: int
    primary_symbol: str
    measurement_start_date: date
    measurement_end_date: date
    holding_days: int
    status: str
    absolute_return_pct: Decimal
    benchmark_code: str | None
    benchmark_return_pct: Decimal | None
    alpha_pct: Decimal | None
    success_grade: str
    summary: str


@dataclass(frozen=True)
class PerformanceOutcomeScheduleCandidate:
    batch_id: int
    as_of_date: date
    market_code: str
    strategy_name: str
    horizon_type: str
    universe_version: str
    horizon_day: int
    measurement_end_date: date
    active_recommendation_count: int
    existing_outcome_count: int


def load_performance_outcome_candidates(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    measurement_end_date: date,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    market_code: str = _DEFAULT_MARKET_CODE,
    executor: PsqlCommandExecutor | None = None,
) -> tuple[PerformanceOutcomeCandidate, ...]:
    if measurement_end_date < as_of_date:
        raise ValueError("measurement_end_date must be greater than or equal to as_of_date.")
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload_text = sql_executor.execute_scalar(
        render_performance_outcome_candidate_lookup_sql(
            as_of_date=as_of_date,
            measurement_end_date=measurement_end_date,
            market_code=market_code,
            strategy_name=strategy_name,
            horizon_type=horizon_type,
            universe_version=universe_version,
        )
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Performance outcome candidate lookup did not return a JSON array.")

    candidates: list[PerformanceOutcomeCandidate] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Performance outcome candidate lookup returned a non-object row.")
        candidates.append(
            PerformanceOutcomeCandidate(
                batch_id=int(item["batch_id"]),
                recommendation_id=int(item["recommendation_id"]),
                thesis_id=int(item["thesis_id"]) if item.get("thesis_id") is not None else None,
                instrument_id=int(item["instrument_id"]),
                primary_symbol=str(item["primary_symbol"]).upper(),
                recommendation_score=Decimal(str(item["recommendation_score"])),
                recommendation_bucket=str(item["recommendation_bucket"]),
                recommendation_action=str(item["recommendation_action"]),
                thesis_title=str(item["thesis_title"]) if item.get("thesis_title") is not None else None,
                thesis_status=str(item["thesis_status"]) if item.get("thesis_status") is not None else None,
                benchmark_code=str(item["benchmark_code"]) if item.get("benchmark_code") is not None else None,
                measurement_start_date=date.fromisoformat(str(item["measurement_start_date"])),
                measurement_end_date=date.fromisoformat(str(item["measurement_end_date"])),
                entry_price=Decimal(str(item["entry_price"])),
                exit_price=Decimal(str(item["exit_price"])),
                min_price=Decimal(str(item["min_price"])),
                benchmark_entry_price=_optional_decimal(item.get("benchmark_entry_price")),
                benchmark_exit_price=_optional_decimal(item.get("benchmark_exit_price")),
            )
        )

    if not candidates:
        raise ValueError("No performance outcome candidates matched the requested recommendation batch identity.")
    return tuple(candidates)


def load_performance_outcome_schedule_candidates(
    *,
    config: RuntimeConfig,
    due_on_date: date,
    horizon_days: tuple[int, ...] = (),
    market_code: str | None = None,
    strategy_name: str | None = None,
    horizon_type: str | None = None,
    universe_version: str | None = None,
    limit: int | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> tuple[PerformanceOutcomeScheduleCandidate, ...]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload_text = sql_executor.execute_scalar(
        render_performance_outcome_schedule_candidate_lookup_sql(
            due_on_date=due_on_date,
            horizon_days=horizon_days,
            market_code=market_code,
            strategy_name=strategy_name,
            horizon_type=horizon_type,
            universe_version=universe_version,
            limit=limit,
        )
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Performance outcome schedule candidate lookup did not return a JSON array.")

    candidates: list[PerformanceOutcomeScheduleCandidate] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Performance outcome schedule candidate lookup returned a non-object row.")
        candidates.append(
            PerformanceOutcomeScheduleCandidate(
                batch_id=int(item["batch_id"]),
                as_of_date=date.fromisoformat(str(item["as_of_date"])),
                market_code=str(item["market_code"]),
                strategy_name=str(item["strategy_name"]),
                horizon_type=str(item["horizon_type"]),
                universe_version=str(item["universe_version"]),
                horizon_day=int(item["horizon_day"]),
                measurement_end_date=date.fromisoformat(str(item["measurement_end_date"])),
                active_recommendation_count=int(item["active_recommendation_count"]),
                existing_outcome_count=int(item["existing_outcome_count"]),
            )
        )

    return tuple(candidates)


def render_performance_outcome_candidate_lookup_sql(
    *,
    as_of_date: date,
    measurement_end_date: date,
    market_code: str,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
) -> str:
    return f"""-- performance outcome candidate lookup
with selected_batch as (
    select batch_id, as_of_date
    from signal.recommendation_batch
    where as_of_date = {sql_date(as_of_date)}
      and market_code = {sql_literal(market_code)}
      and strategy_name = {sql_literal(strategy_name)}
      and horizon_type = {sql_literal(horizon_type)}
      and universe_version = {sql_literal(universe_version)}
    order by batch_id desc
    limit 1
),
recommendation_rows as (
    select
        batch.batch_id,
        batch.as_of_date,
        recommendation.recommendation_id,
        recommendation.thesis_id,
        recommendation.instrument_id,
        instrument.primary_symbol,
        recommendation.total_score as recommendation_score,
        recommendation.bucket as recommendation_bucket,
        recommendation.action as recommendation_action,
        thesis.title as thesis_title,
        thesis.status as thesis_status,
        thesis.benchmark_code
    from selected_batch batch
    join signal.recommendation recommendation on recommendation.batch_id = batch.batch_id
    join ref.instrument instrument on instrument.instrument_id = recommendation.instrument_id
    left join signal.investment_thesis thesis on thesis.thesis_id = recommendation.thesis_id
    where recommendation.status = 'active'
),
candidate_rows as (
    select
        recommendation.batch_id,
        recommendation.recommendation_id,
        recommendation.thesis_id,
        recommendation.instrument_id,
        recommendation.primary_symbol,
        recommendation.recommendation_score,
        recommendation.recommendation_bucket,
        recommendation.recommendation_action,
        recommendation.thesis_title,
        recommendation.thesis_status,
        recommendation.benchmark_code,
        entry_price.trade_date as measurement_start_date,
        exit_price.trade_date as measurement_end_date,
        entry_price.adjusted_close as entry_price,
        exit_price.adjusted_close as exit_price,
        min_price.min_adjusted_close as min_price,
        benchmark_entry.adjusted_close as benchmark_entry_price,
        benchmark_exit.adjusted_close as benchmark_exit_price
    from recommendation_rows recommendation
    join lateral (
        select trade_date, adjusted_close
        from market.daily_price_bar
        where instrument_id = recommendation.instrument_id
          and trade_date <= recommendation.as_of_date
        order by trade_date desc
        limit 1
    ) entry_price on true
    join lateral (
        select trade_date, adjusted_close
        from market.daily_price_bar
        where instrument_id = recommendation.instrument_id
          and trade_date <= {sql_date(measurement_end_date)}
          and trade_date >= entry_price.trade_date
        order by trade_date desc
        limit 1
    ) exit_price on true
    join lateral (
        select min(adjusted_close) as min_adjusted_close
        from market.daily_price_bar
        where instrument_id = recommendation.instrument_id
          and trade_date >= entry_price.trade_date
          and trade_date <= exit_price.trade_date
    ) min_price on true
    left join ref.instrument benchmark_instrument
      on benchmark_instrument.is_active = true
     and lower(benchmark_instrument.primary_symbol) = lower(recommendation.benchmark_code)
    left join lateral (
        select adjusted_close
        from market.daily_price_bar
        where instrument_id = benchmark_instrument.instrument_id
          and trade_date <= entry_price.trade_date
        order by trade_date desc
        limit 1
    ) benchmark_entry on true
    left join lateral (
        select adjusted_close
        from market.daily_price_bar
        where instrument_id = benchmark_instrument.instrument_id
          and trade_date <= exit_price.trade_date
        order by trade_date desc
        limit 1
    ) benchmark_exit on true
)
select coalesce(
    json_agg(
        json_build_object(
            'batch_id', batch_id,
            'recommendation_id', recommendation_id,
            'thesis_id', thesis_id,
            'instrument_id', instrument_id,
            'primary_symbol', primary_symbol,
            'recommendation_score', recommendation_score,
            'recommendation_bucket', recommendation_bucket,
            'recommendation_action', recommendation_action,
            'thesis_title', thesis_title,
            'thesis_status', thesis_status,
            'benchmark_code', benchmark_code,
            'measurement_start_date', measurement_start_date,
            'measurement_end_date', measurement_end_date,
            'entry_price', entry_price,
            'exit_price', exit_price,
            'min_price', min_price,
            'benchmark_entry_price', benchmark_entry_price,
            'benchmark_exit_price', benchmark_exit_price
        )
        order by primary_symbol
    ),
    '[]'::json
)::text
from candidate_rows;"""


def render_performance_outcome_schedule_candidate_lookup_sql(
    *,
    due_on_date: date,
    horizon_days: tuple[int, ...] = (),
    market_code: str | None = None,
    strategy_name: str | None = None,
    horizon_type: str | None = None,
    universe_version: str | None = None,
    limit: int | None = None,
) -> str:
    resolved_horizon_days = resolve_performance_schedule_horizon_days(horizon_days)
    if limit is not None and limit <= 0:
        raise ValueError("limit must be greater than zero.")
    horizon_value_rows = ",\n        ".join(f"({horizon_day}::integer)" for horizon_day in resolved_horizon_days)
    filter_conditions = _render_schedule_batch_filters(
        market_code=market_code,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        universe_version=universe_version,
    )
    limit_clause = "" if limit is None else f"\n    limit {limit}"
    return f"""-- performance outcome schedule candidate lookup
with horizon_days(horizon_day) as (
    values
        {horizon_value_rows}
),
selected_batches as (
    select
        batch_id,
        as_of_date,
        market_code,
        strategy_name,
        horizon_type,
        universe_version
    from signal.recommendation_batch
    where as_of_date <= {sql_date(due_on_date)}
      and universe_version is not null
      {filter_conditions}
),
batch_horizons as (
    select
        batch.batch_id,
        batch.as_of_date,
        batch.market_code,
        batch.strategy_name,
        batch.horizon_type,
        batch.universe_version,
        horizon.horizon_day,
        (batch.as_of_date + horizon.horizon_day) as measurement_end_date
    from selected_batches batch
    join horizon_days horizon on true
    where (batch.as_of_date + horizon.horizon_day) <= {sql_date(due_on_date)}
),
outcome_status as (
    select
        batch_horizons.batch_id,
        batch_horizons.as_of_date,
        batch_horizons.market_code,
        batch_horizons.strategy_name,
        batch_horizons.horizon_type,
        batch_horizons.universe_version,
        batch_horizons.horizon_day,
        batch_horizons.measurement_end_date,
        count(recommendation.recommendation_id)::integer as active_recommendation_count,
        count(outcome.outcome_id)::integer as existing_outcome_count
    from batch_horizons
    join signal.recommendation recommendation
      on recommendation.batch_id = batch_horizons.batch_id
     and recommendation.status = 'active'
    left join performance.recommendation_outcome outcome
      on outcome.recommendation_id = recommendation.recommendation_id
     and outcome.measurement_end_date = batch_horizons.measurement_end_date
    group by
        batch_horizons.batch_id,
        batch_horizons.as_of_date,
        batch_horizons.market_code,
        batch_horizons.strategy_name,
        batch_horizons.horizon_type,
        batch_horizons.universe_version,
        batch_horizons.horizon_day,
        batch_horizons.measurement_end_date
),
candidate_rows as (
    select *
    from outcome_status
    where existing_outcome_count < active_recommendation_count
    order by as_of_date, horizon_day, batch_id
    {limit_clause}
)
select coalesce(
    json_agg(
        json_build_object(
            'batch_id', batch_id,
            'as_of_date', as_of_date,
            'market_code', market_code,
            'strategy_name', strategy_name,
            'horizon_type', horizon_type,
            'universe_version', universe_version,
            'horizon_day', horizon_day,
            'measurement_end_date', measurement_end_date,
            'active_recommendation_count', active_recommendation_count,
            'existing_outcome_count', existing_outcome_count
        )
        order by as_of_date, horizon_day, batch_id
    ),
    '[]'::json
)::text
from candidate_rows;"""


def build_performance_outcome_rows(
    candidates: tuple[PerformanceOutcomeCandidate, ...],
) -> tuple[tuple[RecommendationOutcomeRow, ...], tuple[ThesisOutcomeRow, ...]]:
    if not candidates:
        raise ValueError("At least one performance outcome candidate is required.")

    recommendation_rows: list[RecommendationOutcomeRow] = []
    thesis_rows_by_id: dict[int, ThesisOutcomeRow] = {}
    for candidate in candidates:
        absolute_return = _return_pct(candidate.entry_price, candidate.exit_price)
        benchmark_return = None
        if candidate.benchmark_entry_price is not None and candidate.benchmark_exit_price is not None:
            benchmark_return = _return_pct(candidate.benchmark_entry_price, candidate.benchmark_exit_price)
        alpha = _quantize(absolute_return - benchmark_return) if benchmark_return is not None else None
        max_drawdown = _return_pct(candidate.entry_price, candidate.min_price)
        outcome_label = _outcome_label(absolute_return=absolute_return, alpha_pct=alpha)
        horizon_days = (candidate.measurement_end_date - candidate.measurement_start_date).days
        recommendation_rows.append(
            RecommendationOutcomeRow(
                recommendation_id=candidate.recommendation_id,
                thesis_id=candidate.thesis_id,
                primary_symbol=candidate.primary_symbol,
                measurement_start_date=candidate.measurement_start_date,
                measurement_end_date=candidate.measurement_end_date,
                horizon_days=horizon_days,
                entry_price=candidate.entry_price,
                exit_price=candidate.exit_price,
                absolute_return_pct=absolute_return,
                benchmark_code=candidate.benchmark_code,
                benchmark_return_pct=benchmark_return,
                alpha_pct=alpha,
                max_drawdown_pct=max_drawdown,
                outcome_label=outcome_label,
            )
        )
        if candidate.thesis_id is not None:
            thesis_rows_by_id.setdefault(
                candidate.thesis_id,
                ThesisOutcomeRow(
                    thesis_id=candidate.thesis_id,
                    recommendation_id=candidate.recommendation_id,
                    primary_symbol=candidate.primary_symbol,
                    measurement_start_date=candidate.measurement_start_date,
                    measurement_end_date=candidate.measurement_end_date,
                    holding_days=horizon_days,
                    status=_thesis_outcome_status(outcome_label),
                    absolute_return_pct=absolute_return,
                    benchmark_code=candidate.benchmark_code,
                    benchmark_return_pct=benchmark_return,
                    alpha_pct=alpha,
                    success_grade=_success_grade(absolute_return),
                    summary=_thesis_summary(candidate, absolute_return=absolute_return, outcome_label=outcome_label),
                ),
            )

    return tuple(recommendation_rows), tuple(thesis_rows_by_id.values())


def render_performance_outcome_upsert_sql(
    recommendation_rows: tuple[RecommendationOutcomeRow, ...],
    thesis_rows: tuple[ThesisOutcomeRow, ...],
    *,
    source_run_id: int,
) -> str:
    if not recommendation_rows:
        raise ValueError("At least one recommendation outcome row is required.")
    recommendation_value_rows = ",\n        ".join(
        _render_recommendation_outcome_value_tuple(row, source_run_id=source_run_id) for row in recommendation_rows
    )
    thesis_value_rows = ",\n        ".join(
        _render_thesis_outcome_value_tuple(row, source_run_id=source_run_id) for row in thesis_rows
    )
    thesis_source_cte = _render_thesis_source_cte(thesis_value_rows, has_rows=bool(thesis_rows))
    return f"""begin;

with recommendation_source (
    recommendation_id,
    measurement_start_date,
    measurement_end_date,
    horizon_days,
    entry_price,
    exit_price,
    absolute_return_pct,
    benchmark_code,
    benchmark_return_pct,
    alpha_pct,
    max_drawdown_pct,
    outcome_label,
    source_run_id
) as (
    values
        {recommendation_value_rows}
),
upsert_recommendation_outcomes as (
    insert into performance.recommendation_outcome (
        recommendation_id,
        measurement_start_date,
        measurement_end_date,
        horizon_days,
        entry_price,
        exit_price,
        absolute_return_pct,
        benchmark_code,
        benchmark_return_pct,
        alpha_pct,
        max_drawdown_pct,
        outcome_label,
        source_run_id
    )
    select
        recommendation_id,
        measurement_start_date,
        measurement_end_date,
        horizon_days,
        entry_price,
        exit_price,
        absolute_return_pct,
        benchmark_code,
        benchmark_return_pct,
        alpha_pct,
        max_drawdown_pct,
        outcome_label,
        source_run_id
    from recommendation_source
    on conflict (recommendation_id, measurement_end_date) do update
    set
        measurement_start_date = excluded.measurement_start_date,
        horizon_days = excluded.horizon_days,
        entry_price = excluded.entry_price,
        exit_price = excluded.exit_price,
        absolute_return_pct = excluded.absolute_return_pct,
        benchmark_code = excluded.benchmark_code,
        benchmark_return_pct = excluded.benchmark_return_pct,
        alpha_pct = excluded.alpha_pct,
        max_drawdown_pct = excluded.max_drawdown_pct,
        outcome_label = excluded.outcome_label,
        source_run_id = excluded.source_run_id
    returning outcome_id
),
{thesis_source_cte},
upsert_thesis_outcomes as (
    insert into performance.thesis_outcome (
        thesis_id,
        recommendation_id,
        measurement_start_date,
        measurement_end_date,
        holding_days,
        status,
        absolute_return_pct,
        benchmark_code,
        benchmark_return_pct,
        alpha_pct,
        success_grade,
        summary,
        source_run_id
    )
    select
        thesis_id,
        recommendation_id,
        measurement_start_date,
        measurement_end_date,
        holding_days,
        status,
        absolute_return_pct,
        benchmark_code,
        benchmark_return_pct,
        alpha_pct,
        success_grade,
        summary,
        source_run_id
    from thesis_source
    on conflict (thesis_id, measurement_end_date) do update
    set
        recommendation_id = excluded.recommendation_id,
        measurement_start_date = excluded.measurement_start_date,
        holding_days = excluded.holding_days,
        status = excluded.status,
        absolute_return_pct = excluded.absolute_return_pct,
        benchmark_code = excluded.benchmark_code,
        benchmark_return_pct = excluded.benchmark_return_pct,
        alpha_pct = excluded.alpha_pct,
        success_grade = excluded.success_grade,
        summary = excluded.summary,
        source_run_id = excluded.source_run_id
    returning outcome_id
)
select json_build_object(
    'recommendation_outcome_count', (select count(*) from upsert_recommendation_outcomes),
    'thesis_outcome_count', (select count(*) from upsert_thesis_outcomes)
)::text;

commit;
"""


def run_performance_outcome_bootstrap(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    measurement_end_date: date,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    market_code: str = _DEFAULT_MARKET_CODE,
    outcome_version: str = _DEFAULT_OUTCOME_VERSION,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    candidates = load_performance_outcome_candidates(
        config=config,
        as_of_date=as_of_date,
        measurement_end_date=measurement_end_date,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        universe_version=universe_version,
        market_code=market_code,
        executor=sql_executor,
    )
    recommendation_rows, thesis_rows = build_performance_outcome_rows(candidates)
    batch_id = candidates[0].batch_id
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="performance_outcome_bootstrap",
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "measurement_end_date": measurement_end_date.isoformat(),
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "universe_version": universe_version,
            "outcome_version": outcome_version,
            "candidate_count": len(candidates),
            "recommendation_outcome_count": len(recommendation_rows),
            "thesis_outcome_count": len(thesis_rows),
        },
    )
    try:
        result = json.loads(
            sql_executor.execute_scalar(
                render_performance_outcome_upsert_sql(recommendation_rows, thesis_rows, source_run_id=run_id)
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    label_counts: dict[str, int] = {}
    for row in recommendation_rows:
        label_counts[row.outcome_label] = label_counts.get(row.outcome_label, 0) + 1

    return {
        "run_id": run_id,
        "batch_id": batch_id,
        "as_of_date": as_of_date.isoformat(),
        "measurement_end_date": measurement_end_date.isoformat(),
        "market_code": market_code,
        "strategy_name": strategy_name,
        "horizon_type": horizon_type,
        "universe_version": universe_version,
        "outcome_version": outcome_version,
        "candidate_count": len(candidates),
        "recommendation_outcome_count": int(result["recommendation_outcome_count"]),
        "thesis_outcome_count": int(result["thesis_outcome_count"]),
        "label_counts": label_counts,
        "symbol_preview": [row.primary_symbol for row in recommendation_rows[:10]],
    }


def resolve_performance_measurement_dates(
    *,
    as_of_date: date,
    measurement_end_dates: tuple[date, ...] = (),
    horizon_days: tuple[int, ...] = (),
) -> tuple[date, ...]:
    if not measurement_end_dates and not horizon_days:
        raise ValueError("At least one measurement_end_date or horizon_day is required.")

    resolved_dates = set(measurement_end_dates)
    for horizon_day in horizon_days:
        if horizon_day <= 0:
            raise ValueError("horizon_day values must be greater than zero.")
        resolved_dates.add(as_of_date + timedelta(days=horizon_day))

    for measurement_end_date in resolved_dates:
        if measurement_end_date < as_of_date:
            raise ValueError("measurement_end_date values must be greater than or equal to as_of_date.")

    return tuple(sorted(resolved_dates))


def resolve_performance_schedule_horizon_days(
    horizon_days: tuple[int, ...] = (),
) -> tuple[int, ...]:
    resolved = horizon_days or _DEFAULT_SCHEDULE_HORIZON_DAYS
    normalized: set[int] = set()
    for horizon_day in resolved:
        if horizon_day <= 0:
            raise ValueError("horizon_day values must be greater than zero.")
        normalized.add(horizon_day)
    return tuple(sorted(normalized))


def run_performance_outcome_batch_bootstrap(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    measurement_end_dates: tuple[date, ...] = (),
    horizon_days: tuple[int, ...] = (),
    market_code: str = _DEFAULT_MARKET_CODE,
    outcome_version: str = _DEFAULT_OUTCOME_VERSION,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    resolved_measurement_dates = resolve_performance_measurement_dates(
        as_of_date=as_of_date,
        measurement_end_dates=measurement_end_dates,
        horizon_days=horizon_days,
    )

    results: list[dict[str, object]] = []
    label_counts: dict[str, int] = {}
    recommendation_outcome_count = 0
    thesis_outcome_count = 0
    candidate_count = 0

    for measurement_end_date in resolved_measurement_dates:
        result = run_performance_outcome_bootstrap(
            config=config,
            as_of_date=as_of_date,
            measurement_end_date=measurement_end_date,
            strategy_name=strategy_name,
            horizon_type=horizon_type,
            universe_version=universe_version,
            market_code=market_code,
            outcome_version=outcome_version,
            executor=sql_executor,
        )
        results.append(result)
        recommendation_outcome_count += int(result["recommendation_outcome_count"])
        thesis_outcome_count += int(result["thesis_outcome_count"])
        candidate_count += int(result["candidate_count"])
        for label, count in dict(result["label_counts"]).items():
            label_counts[str(label)] = label_counts.get(str(label), 0) + int(count)

    return {
        "as_of_date": as_of_date.isoformat(),
        "measurement_end_dates": [measurement_date.isoformat() for measurement_date in resolved_measurement_dates],
        "market_code": market_code,
        "strategy_name": strategy_name,
        "horizon_type": horizon_type,
        "universe_version": universe_version,
        "outcome_version": outcome_version,
        "requested_measurement_count": len(resolved_measurement_dates),
        "succeeded_measurement_count": len(results),
        "candidate_count": candidate_count,
        "recommendation_outcome_count": recommendation_outcome_count,
        "thesis_outcome_count": thesis_outcome_count,
        "label_counts": label_counts,
        "results": results,
    }


def run_performance_outcome_schedule_bootstrap(
    *,
    config: RuntimeConfig,
    due_on_date: date,
    horizon_days: tuple[int, ...] = (),
    market_code: str | None = None,
    strategy_name: str | None = None,
    horizon_type: str | None = None,
    universe_version: str | None = None,
    outcome_version: str = _DEFAULT_OUTCOME_VERSION,
    limit: int | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    resolved_horizon_days = resolve_performance_schedule_horizon_days(horizon_days)
    candidates = load_performance_outcome_schedule_candidates(
        config=config,
        due_on_date=due_on_date,
        horizon_days=resolved_horizon_days,
        market_code=market_code,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        universe_version=universe_version,
        limit=limit,
        executor=sql_executor,
    )
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="performance_outcome_schedule_bootstrap",
        config_json={
            "due_on_date": due_on_date.isoformat(),
            "horizon_days": list(resolved_horizon_days),
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "universe_version": universe_version,
            "outcome_version": outcome_version,
            "limit": limit,
            "candidate_count": len(candidates),
        },
    )

    results: list[dict[str, object]] = []
    label_counts: dict[str, int] = {}
    recommendation_outcome_count = 0
    thesis_outcome_count = 0
    try:
        for candidate in candidates:
            try:
                result = run_performance_outcome_bootstrap(
                    config=config,
                    as_of_date=candidate.as_of_date,
                    measurement_end_date=candidate.measurement_end_date,
                    strategy_name=candidate.strategy_name,
                    horizon_type=candidate.horizon_type,
                    universe_version=candidate.universe_version,
                    market_code=candidate.market_code,
                    outcome_version=outcome_version,
                    executor=sql_executor,
                )
                recommendation_outcome_count += int(result["recommendation_outcome_count"])
                thesis_outcome_count += int(result["thesis_outcome_count"])
                for label, count in dict(result["label_counts"]).items():
                    label_counts[str(label)] = label_counts.get(str(label), 0) + int(count)
                results.append(
                    {
                        "status": "succeeded",
                        "batch_id": candidate.batch_id,
                        "as_of_date": candidate.as_of_date.isoformat(),
                        "horizon_day": candidate.horizon_day,
                        "measurement_end_date": candidate.measurement_end_date.isoformat(),
                        "active_recommendation_count": candidate.active_recommendation_count,
                        "existing_outcome_count": candidate.existing_outcome_count,
                        "run_id": result["run_id"],
                        "recommendation_outcome_count": result["recommendation_outcome_count"],
                        "thesis_outcome_count": result["thesis_outcome_count"],
                    }
                )
            except Exception as exc:
                results.append(
                    {
                        "status": "failed",
                        "batch_id": candidate.batch_id,
                        "as_of_date": candidate.as_of_date.isoformat(),
                        "horizon_day": candidate.horizon_day,
                        "measurement_end_date": candidate.measurement_end_date.isoformat(),
                        "active_recommendation_count": candidate.active_recommendation_count,
                        "existing_outcome_count": candidate.existing_outcome_count,
                        "error": str(exc),
                    }
                )

        failed_candidate_count = sum(1 for result in results if result["status"] == "failed")
        if failed_candidate_count:
            _mark_pipeline_run_failed(
                sql_executor,
                run_id,
                f"{failed_candidate_count} of {len(candidates)} scheduled outcome candidates failed.",
            )
        else:
            _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    succeeded_candidate_count = sum(1 for result in results if result["status"] == "succeeded")
    return {
        "run_id": run_id,
        "due_on_date": due_on_date.isoformat(),
        "horizon_days": list(resolved_horizon_days),
        "market_code": market_code,
        "strategy_name": strategy_name,
        "horizon_type": horizon_type,
        "universe_version": universe_version,
        "outcome_version": outcome_version,
        "candidate_count": len(candidates),
        "succeeded_candidate_count": succeeded_candidate_count,
        "failed_candidate_count": len(results) - succeeded_candidate_count,
        "recommendation_outcome_count": recommendation_outcome_count,
        "thesis_outcome_count": thesis_outcome_count,
        "label_counts": label_counts,
        "results": results,
    }


def _return_pct(start: Decimal, end: Decimal) -> Decimal:
    if start <= 0:
        raise ValueError("start price must be greater than zero.")
    return _quantize((end - start) / start)


def _outcome_label(*, absolute_return: Decimal, alpha_pct: Decimal | None) -> str:
    if alpha_pct is not None:
        if alpha_pct > 0:
            return "outperform"
        if alpha_pct < 0:
            return "underperform"
        return "inline"
    if absolute_return > 0:
        return "positive"
    if absolute_return < 0:
        return "negative"
    return "flat"


def _thesis_outcome_status(outcome_label: str) -> str:
    if outcome_label in {"positive", "outperform"}:
        return "working"
    if outcome_label in {"negative", "underperform"}:
        return "challenged"
    return "neutral"


def _success_grade(absolute_return: Decimal) -> str:
    if absolute_return > 0:
        return "pass"
    if absolute_return < 0:
        return "fail"
    return "flat"


def _thesis_summary(
    candidate: PerformanceOutcomeCandidate,
    *,
    absolute_return: Decimal,
    outcome_label: str,
) -> str:
    return (
        f"{candidate.primary_symbol} thesis outcome {outcome_label}. "
        f"Return from {candidate.measurement_start_date.isoformat()} to "
        f"{candidate.measurement_end_date.isoformat()} was {absolute_return}."
    )


def _render_recommendation_outcome_value_tuple(row: RecommendationOutcomeRow, *, source_run_id: int) -> str:
    return "(" + ", ".join(
        (
            f"{row.recommendation_id}::bigint",
            sql_date(row.measurement_start_date),
            sql_date(row.measurement_end_date),
            f"{row.horizon_days}::integer",
            sql_numeric(row.entry_price),
            sql_numeric(row.exit_price),
            sql_numeric(row.absolute_return_pct),
            _sql_text_or_null(row.benchmark_code),
            _sql_numeric_or_null(row.benchmark_return_pct),
            _sql_numeric_or_null(row.alpha_pct),
            sql_numeric(row.max_drawdown_pct),
            _sql_text(row.outcome_label),
            f"{source_run_id}::bigint",
        )
    ) + ")"


def _render_thesis_outcome_value_tuple(row: ThesisOutcomeRow, *, source_run_id: int) -> str:
    return "(" + ", ".join(
        (
            f"{row.thesis_id}::bigint",
            f"{row.recommendation_id}::bigint",
            sql_date(row.measurement_start_date),
            sql_date(row.measurement_end_date),
            f"{row.holding_days}::integer",
            _sql_text(row.status),
            sql_numeric(row.absolute_return_pct),
            _sql_text_or_null(row.benchmark_code),
            _sql_numeric_or_null(row.benchmark_return_pct),
            _sql_numeric_or_null(row.alpha_pct),
            _sql_text(row.success_grade),
            _sql_text(row.summary),
            f"{source_run_id}::bigint",
        )
    ) + ")"


def _render_thesis_source_cte(value_rows: str, *, has_rows: bool) -> str:
    columns = """thesis_source (
    thesis_id,
    recommendation_id,
    measurement_start_date,
    measurement_end_date,
    holding_days,
    status,
    absolute_return_pct,
    benchmark_code,
    benchmark_return_pct,
    alpha_pct,
    success_grade,
    summary,
    source_run_id
) as"""
    if has_rows:
        return f"""{columns} (
    values
        {value_rows}
)"""
    return f"""{columns} (
    select
        null::bigint,
        null::bigint,
        null::date,
        null::date,
        null::integer,
        null::text,
        null::numeric,
        null::text,
        null::numeric,
        null::numeric,
        null::text,
        null::text,
        null::bigint
    where false
)"""


def _render_schedule_batch_filters(
    *,
    market_code: str | None,
    strategy_name: str | None,
    horizon_type: str | None,
    universe_version: str | None,
) -> str:
    conditions: list[str] = []
    if market_code is not None:
        conditions.append(f"and market_code = {sql_literal(market_code)}")
    if strategy_name is not None:
        conditions.append(f"and strategy_name = {sql_literal(strategy_name)}")
    if horizon_type is not None:
        conditions.append(f"and horizon_type = {sql_literal(horizon_type)}")
    if universe_version is not None:
        conditions.append(f"and universe_version = {sql_literal(universe_version)}")
    if not conditions:
        return ""
    return "\n      ".join(conditions)


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)


def _sql_numeric_or_null(value: Decimal | None) -> str:
    if value is None:
        return "null::numeric"
    return sql_numeric(value)


def _sql_text_or_null(value: str | None) -> str:
    if value is None:
        return "null::text"
    return _sql_text(value)


def _sql_text(value: str) -> str:
    return f"{sql_literal(value)}::text"
