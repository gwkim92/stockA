from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import date
from typing import Any

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


ASSET_CORRELATION_PIPELINE_NAME = "asset_correlation_analysis"
DEFAULT_CORRELATION_LOOKBACK_DAYS = (20, 60, 120)
DEFAULT_COMPARISON_SYMBOLS = (
    "SPY",
    "QQQ",
    "IWM",
    "DIA",
    "XLK",
    "XLE",
    "XLF",
    "TLT",
    "HYG",
    "LQD",
)


def parse_lookback_days(raw_values: Iterable[str] | None) -> tuple[int, ...]:
    if raw_values is None:
        return DEFAULT_CORRELATION_LOOKBACK_DAYS

    values: list[int] = []
    for raw_value in raw_values:
        for token in str(raw_value).split(","):
            token = token.strip()
            if not token:
                continue
            value = int(token)
            if value < 10 or value > 252:
                raise ValueError("lookback days must be between 10 and 252.")
            values.append(value)
    if not values:
        return DEFAULT_CORRELATION_LOOKBACK_DAYS
    return tuple(sorted(set(values)))


def run_correlation_analysis(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    execute: bool,
    lookback_days: Iterable[int] = DEFAULT_CORRELATION_LOOKBACK_DAYS,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, Any]:
    normalized_lookbacks = tuple(sorted(set(int(value) for value in lookback_days)))
    if not normalized_lookbacks:
        raise ValueError("At least one lookback day must be provided.")
    for value in normalized_lookbacks:
        if value < 10 or value > 252:
            raise ValueError("lookback days must be between 10 and 252.")

    report: dict[str, Any] = {
        "report_name": ASSET_CORRELATION_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "lookback_days": list(normalized_lookbacks),
        "analysis_policy": "rolling_return_correlation_co_movement_only_not_causality",
        "recommendation_scoring_mutated": False,
        "automatic_weight_change_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": "read_only_no_order",
        "execute": execute,
    }
    if not execute:
        report["status"] = "planned"
        return report

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=ASSET_CORRELATION_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "lookback_days": list(normalized_lookbacks),
            "analysis_policy": "co_movement_only_not_causality",
        },
    )
    try:
        sql_executor.execute_non_query(
            render_asset_correlation_snapshot_upsert_sql(
                as_of_date=as_of_date,
                lookback_days=normalized_lookbacks,
                source_run_id=run_id,
            )
        )
        report["summary"] = _load_json_scalar(
            sql_executor,
            render_asset_correlation_summary_sql(as_of_date=as_of_date),
            default={},
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    report["status"] = "completed"
    report["run_id"] = run_id
    return report


def render_asset_correlation_snapshot_upsert_sql(
    *,
    as_of_date: date,
    lookback_days: Iterable[int],
    source_run_id: int,
    comparison_symbols: Iterable[str] = DEFAULT_COMPARISON_SYMBOLS,
) -> str:
    lookback_values = ",\n        ".join(f"({int(value)}::integer)" for value in sorted(set(lookback_days)))
    comparison_symbol_values = ",\n        ".join(
        f"({sql_literal(str(symbol).upper())})" for symbol in sorted(set(comparison_symbols))
    )
    max_lookback = max(int(value) for value in lookback_days)
    return f"""with target_date as (
    select {sql_date(as_of_date)}::date as as_of_date
),
lookbacks(lookback_days) as (
    values
        {lookback_values}
),
comparison_symbols(symbol) as (
    values
        {comparison_symbol_values}
),
latest_recommendation_batch as (
    select batch.batch_id
    from signal.recommendation_batch batch
    join target_date target on batch.as_of_date <= target.as_of_date
    order by batch.as_of_date desc, batch.batch_id desc
    limit 1
),
primary_instruments as (
    select distinct recommendation.instrument_id
    from signal.recommendation recommendation
    join latest_recommendation_batch batch on batch.batch_id = recommendation.batch_id
    where recommendation.status = 'active'
    union
    select distinct position.instrument_id
    from portfolio.position_snapshot position
    join (
        select portfolio_id, max(snapshot_date) as snapshot_date
        from portfolio.position_snapshot snapshot
        join target_date target on snapshot.snapshot_date <= target.as_of_date
        group by portfolio_id
    ) latest_position
      on latest_position.portfolio_id = position.portfolio_id
     and latest_position.snapshot_date = position.snapshot_date
),
comparison_instruments as (
    select instrument.instrument_id
    from ref.instrument instrument
    join comparison_symbols symbol on upper(instrument.primary_symbol) = symbol.symbol
    where instrument.is_active = true
    union
    select instrument_id from primary_instruments
),
instrument_values as (
    select
        'instrument:' || instrument.primary_symbol as asset_key,
        'instrument'::text as asset_type,
        price.instrument_id,
        null::text as indicator_code,
        instrument.primary_symbol as display_name,
        price.trade_date as observation_date,
        price.adjusted_close::numeric as asset_value,
        case when price.instrument_id in (select instrument_id from primary_instruments) then true else false end as is_primary_candidate
    from market.daily_price_bar price
    join ref.instrument instrument on instrument.instrument_id = price.instrument_id
    join target_date target on price.trade_date <= target.as_of_date
    where price.trade_date >= (select as_of_date from target_date) - ({max_lookback * 3} || ' days')::interval
      and price.adjusted_close > 0
      and price.instrument_id in (select instrument_id from comparison_instruments)
),
indicator_values_deduped as (
    select distinct on (observation.indicator_code, observation.observation_date)
        'indicator:' || observation.indicator_code as asset_key,
        'indicator'::text as asset_type,
        null::bigint as instrument_id,
        observation.indicator_code,
        indicator.display_name,
        observation.observation_date,
        observation.value::numeric as asset_value,
        false as is_primary_candidate
    from market.market_indicator_observation observation
    join market.market_indicator indicator on indicator.indicator_code = observation.indicator_code
    join target_date target on observation.observation_date <= target.as_of_date
    where observation.observation_date >= (select as_of_date from target_date) - ({max_lookback * 3} || ' days')::interval
      and observation.value > 0
      and indicator.is_active = true
    order by
        observation.indicator_code,
        observation.observation_date,
        case observation.provider when 'fred' then 1 when 'cboe_csv' then 2 when 'twelve_data' then 3 else 9 end,
        observation.created_at desc
),
asset_values as (
    select * from instrument_values
    union all
    select * from indicator_values_deduped
),
asset_returns as (
    select
        asset_key,
        asset_type,
        instrument_id,
        indicator_code,
        display_name,
        observation_date,
        is_primary_candidate,
        case
            when lag(asset_value) over (partition by asset_key order by observation_date) > 0
                then asset_value / lag(asset_value) over (partition by asset_key order by observation_date) - 1
            else null
        end as return_value
    from asset_values
),
ranked_returns as (
    select
        *,
        row_number() over (partition by asset_key order by observation_date desc) as return_rank
    from asset_returns
    where return_value is not null
),
pair_observations as (
    select
        lookbacks.lookback_days,
        primary_asset.asset_key as primary_asset_key,
        primary_asset.asset_type as primary_asset_type,
        primary_asset.instrument_id as primary_instrument_id,
        primary_asset.indicator_code as primary_indicator_code,
        primary_asset.display_name as primary_display_name,
        comparison_asset.asset_key as comparison_asset_key,
        comparison_asset.asset_type as comparison_asset_type,
        comparison_asset.instrument_id as comparison_instrument_id,
        comparison_asset.indicator_code as comparison_indicator_code,
        comparison_asset.display_name as comparison_display_name,
        primary_asset.observation_date as primary_date,
        comparison_asset.observation_date as comparison_date,
        primary_asset.return_value::double precision as primary_return,
        comparison_asset.return_value::double precision as comparison_return
    from lookbacks
    join ranked_returns primary_asset
      on primary_asset.is_primary_candidate = true
     and primary_asset.asset_type = 'instrument'
     and primary_asset.return_rank <= lookbacks.lookback_days
    join ranked_returns comparison_asset
      on comparison_asset.observation_date = primary_asset.observation_date
     and comparison_asset.asset_key <> primary_asset.asset_key
     and comparison_asset.return_rank <= lookbacks.lookback_days
),
pair_stats as (
    select
        (select as_of_date from target_date) as as_of_date,
        lookback_days,
        primary_asset_key,
        primary_asset_type,
        primary_instrument_id,
        primary_indicator_code,
        max(primary_display_name) as primary_display_name,
        comparison_asset_key,
        comparison_asset_type,
        comparison_instrument_id,
        comparison_indicator_code,
        max(comparison_display_name) as comparison_display_name,
        count(*)::integer as observation_count,
        corr(primary_return, comparison_return)::numeric(10,8) as correlation,
        case
            when var_samp(comparison_return) is null or var_samp(comparison_return) = 0 then null
            else (covar_samp(primary_return, comparison_return) / var_samp(comparison_return))::numeric(16,8)
        end as beta,
        stddev_samp(primary_return)::numeric(16,8) as primary_return_volatility,
        stddev_samp(comparison_return)::numeric(16,8) as comparison_return_volatility,
        max(primary_date) as latest_primary_date,
        max(comparison_date) as latest_comparison_date
    from pair_observations
    group by
        lookback_days,
        primary_asset_key,
        primary_asset_type,
        primary_instrument_id,
        primary_indicator_code,
        comparison_asset_key,
        comparison_asset_type,
        comparison_instrument_id,
        comparison_indicator_code
    having count(*) >= least(20, greatest(8, lookback_days / 3))
       and corr(primary_return, comparison_return) is not null
),
source_rows as (
    select
        *,
        case
            when abs(correlation) >= 0.75 and correlation > 0 then 'strong_positive'
            when abs(correlation) >= 0.75 and correlation < 0 then 'strong_negative'
            when abs(correlation) >= 0.40 and correlation > 0 then 'moderate_positive'
            when abs(correlation) >= 0.40 and correlation < 0 then 'moderate_negative'
            else 'weak_or_unclear'
        end as relationship_label,
        least(
            1::numeric,
            greatest(0::numeric, (observation_count::numeric / greatest(lookback_days::numeric, 1::numeric)) * 0.70)
            + least(0.30::numeric, abs(correlation)::numeric * 0.30)
        )::numeric(8,6) as confidence
    from pair_stats
)
insert into signal.asset_correlation_snapshot (
    as_of_date,
    lookback_days,
    primary_asset_key,
    primary_asset_type,
    primary_instrument_id,
    primary_indicator_code,
    primary_display_name,
    comparison_asset_key,
    comparison_asset_type,
    comparison_instrument_id,
    comparison_indicator_code,
    comparison_display_name,
    observation_count,
    correlation,
    beta,
    primary_return_volatility,
    comparison_return_volatility,
    relationship_label,
    confidence,
    latest_primary_date,
    latest_comparison_date,
    source_run_id,
    evidence_json,
    updated_at
)
select
    as_of_date,
    lookback_days,
    primary_asset_key,
    primary_asset_type,
    primary_instrument_id,
    primary_indicator_code,
    primary_display_name,
    comparison_asset_key,
    comparison_asset_type,
    comparison_instrument_id,
    comparison_indicator_code,
    comparison_display_name,
    observation_count,
    correlation,
    beta,
    primary_return_volatility,
    comparison_return_volatility,
    relationship_label,
    confidence,
    latest_primary_date,
    latest_comparison_date,
    {source_run_id}::bigint,
    jsonb_build_object(
        'analysis_type', 'rolling_return_correlation',
        'lookback_days', lookback_days,
        'causal_claim', false,
        'policy', 'co_movement_only_not_causality'
    ),
    now()
from source_rows
on conflict (as_of_date, lookback_days, primary_asset_key, comparison_asset_key) do update
set
    primary_asset_type = excluded.primary_asset_type,
    primary_instrument_id = excluded.primary_instrument_id,
    primary_indicator_code = excluded.primary_indicator_code,
    primary_display_name = excluded.primary_display_name,
    comparison_asset_type = excluded.comparison_asset_type,
    comparison_instrument_id = excluded.comparison_instrument_id,
    comparison_indicator_code = excluded.comparison_indicator_code,
    comparison_display_name = excluded.comparison_display_name,
    observation_count = excluded.observation_count,
    correlation = excluded.correlation,
    beta = excluded.beta,
    primary_return_volatility = excluded.primary_return_volatility,
    comparison_return_volatility = excluded.comparison_return_volatility,
    relationship_label = excluded.relationship_label,
    confidence = excluded.confidence,
    latest_primary_date = excluded.latest_primary_date,
    latest_comparison_date = excluded.latest_comparison_date,
    source_run_id = excluded.source_run_id,
    evidence_json = excluded.evidence_json,
    updated_at = now();"""


def render_asset_correlation_summary_sql(*, as_of_date: date) -> str:
    return f"""with selected_date as (
    select max(as_of_date) as as_of_date
    from signal.asset_correlation_snapshot
    where as_of_date <= {sql_date(as_of_date)}
),
rows as (
    select snapshot.*
    from signal.asset_correlation_snapshot snapshot
    join selected_date selected on selected.as_of_date = snapshot.as_of_date
)
select json_build_object(
    'as_of_date', (select as_of_date from selected_date),
    'snapshot_count', count(*),
    'primary_asset_count', count(distinct primary_asset_key),
    'comparison_asset_count', count(distinct comparison_asset_key),
    'strong_relationship_count', count(*) filter (where relationship_label in ('strong_positive', 'strong_negative')),
    'moderate_relationship_count', count(*) filter (where relationship_label in ('moderate_positive', 'moderate_negative')),
    'lookback_days', coalesce(array_agg(distinct lookback_days order by lookback_days), '{{}}'::integer[]),
    'recommendation_scoring_mutated', false,
    'automatic_weight_change_allowed', false,
    'broker_submit_allowed', false,
    'order_boundary', 'read_only_no_order'
)::text
from rows;"""


def _load_json_scalar(
    executor: PsqlCommandExecutor,
    sql: str,
    *,
    default: dict[str, Any],
) -> dict[str, Any]:
    try:
        raw = executor.execute_scalar(sql)
    except Exception:
        return dict(default)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return dict(default)
    return payload if isinstance(payload, dict) else dict(default)
