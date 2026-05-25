from __future__ import annotations

import json
from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_PIPELINE_NAME = "recommendation_fundamental_components"
DEFAULT_MODEL_NAME = "deterministic-recommendation-fundamental-components-sql-v1"
DEFAULT_MARKET_CODE = "US"
DEFAULT_STRATEGY_NAME = "long_term_core"
DEFAULT_HORIZON_TYPE = "long_term"
FUNDAMENTAL_COMPONENTS = (
    "fundamental_quality_score",
    "valuation_margin_score",
    "peer_relative_score",
    "balance_sheet_risk_penalty",
    "thesis_consistency_score",
)


def render_recommendation_fundamental_components_preview_sql(
    *,
    as_of_date: date,
    market_code: str = DEFAULT_MARKET_CODE,
    strategy_name: str = DEFAULT_STRATEGY_NAME,
    horizon_type: str = DEFAULT_HORIZON_TYPE,
) -> str:
    return f"""-- recommendation fundamental components preview
with selected_batch as (
    select
        batch_id,
        as_of_date,
        market_code,
        strategy_name,
        horizon_type
    from signal.recommendation_batch
    where as_of_date <= {sql_date(as_of_date)}
      and market_code = {sql_literal(market_code)}
      and strategy_name = {sql_literal(strategy_name)}
      and horizon_type = {sql_literal(horizon_type)}
    order by as_of_date desc, batch_id desc
    limit 1
),
active_recommendations as (
    select
        recommendation.recommendation_id,
        recommendation.instrument_id,
        recommendation.thesis_id
    from selected_batch batch
    join signal.recommendation recommendation on recommendation.batch_id = batch.batch_id
    where recommendation.status = 'active'
),
latest_normalized_rows as (
    select distinct on (normalized.instrument_id, normalized.metric_code)
        normalized.instrument_id,
        normalized.metric_code,
        normalized.metric_value
    from market.financial_metric_normalized normalized
    join active_recommendations recommendation on recommendation.instrument_id = normalized.instrument_id
    where normalized.as_of_date <= {sql_date(as_of_date)}
      and normalized.statement_scope = 'annual'
      and normalized.metric_status = 'computed'
      and normalized.metric_code in (
        'net_margin',
        'operating_margin',
        'free_cash_flow_margin',
        'cash_flow_quality',
        'roe',
        'leverage_ratio'
      )
    order by
        normalized.instrument_id,
        normalized.metric_code,
        normalized.as_of_date desc,
        normalized.period_end desc
),
latest_peer_rows as (
    select distinct on (snapshot.instrument_id, snapshot.peer_group_id, snapshot.metric_code)
        snapshot.instrument_id,
        snapshot.metric_code,
        snapshot.percentile_rank
    from market.peer_relative_snapshot snapshot
    join active_recommendations recommendation on recommendation.instrument_id = snapshot.instrument_id
    where snapshot.as_of_date <= {sql_date(as_of_date)}
      and snapshot.relative_signal <> 'insufficient_data'
    order by
        snapshot.instrument_id,
        snapshot.peer_group_id,
        snapshot.metric_code,
        snapshot.as_of_date desc
),
latest_valuation_rows as (
    select distinct on (valuation.instrument_id, valuation.method)
        valuation.instrument_id,
        valuation.method,
        valuation.margin_of_safety,
        valuation.confidence
    from market.valuation_snapshot valuation
    join active_recommendations recommendation on recommendation.instrument_id = valuation.instrument_id
    where valuation.as_of_date <= {sql_date(as_of_date)}
    order by
        valuation.instrument_id,
        valuation.method,
        valuation.as_of_date desc,
        valuation.valuation_snapshot_id desc
),
existing_components as (
    select component.recommendation_id, component.component_name
    from signal.recommendation_score_component component
    join active_recommendations recommendation on recommendation.recommendation_id = component.recommendation_id
    where component.component_name in ({_component_sql_list()})
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'selected_batch_id', (select batch_id from selected_batch),
    'selected_batch_as_of_date', (select as_of_date::text from selected_batch),
    'market_code', {sql_literal(market_code)},
    'strategy_name', {sql_literal(strategy_name)},
    'horizon_type', {sql_literal(horizon_type)},
    'model_name', {sql_literal(DEFAULT_MODEL_NAME)},
    'component_names', {sql_literal(json.dumps(FUNDAMENTAL_COMPONENTS))}::jsonb,
    'active_recommendation_count', (select count(*)::integer from active_recommendations),
    'financial_coverage_count', (select count(distinct instrument_id)::integer from latest_normalized_rows),
    'peer_coverage_count', (select count(distinct instrument_id)::integer from latest_peer_rows),
    'valuation_coverage_count', (select count(distinct instrument_id)::integer from latest_valuation_rows),
    'linked_thesis_count', (select count(*)::integer from active_recommendations where thesis_id is not null),
    'existing_fundamental_component_count', (select count(*)::integer from existing_components)
)::text;"""


def render_recommendation_fundamental_components_upsert_sql(
    *,
    as_of_date: date,
    source_run_id: int,
    market_code: str = DEFAULT_MARKET_CODE,
    strategy_name: str = DEFAULT_STRATEGY_NAME,
    horizon_type: str = DEFAULT_HORIZON_TYPE,
) -> str:
    return f"""-- recommendation fundamental components upsert
with selected_batch as (
    select
        batch_id,
        as_of_date,
        market_code,
        strategy_name,
        horizon_type
    from signal.recommendation_batch
    where as_of_date <= {sql_date(as_of_date)}
      and market_code = {sql_literal(market_code)}
      and strategy_name = {sql_literal(strategy_name)}
      and horizon_type = {sql_literal(horizon_type)}
    order by as_of_date desc, batch_id desc
    limit 1
),
active_recommendations as (
    select
        recommendation.recommendation_id,
        recommendation.instrument_id,
        instrument.primary_symbol,
        recommendation.thesis_id,
        thesis.status as thesis_status,
        thesis.invalidation_conditions
    from selected_batch batch
    join signal.recommendation recommendation on recommendation.batch_id = batch.batch_id
    join ref.instrument instrument on instrument.instrument_id = recommendation.instrument_id
    left join signal.investment_thesis thesis on thesis.thesis_id = recommendation.thesis_id
    where recommendation.status = 'active'
),
latest_normalized_rows as (
    select distinct on (normalized.instrument_id, normalized.metric_code)
        normalized.instrument_id,
        normalized.metric_code,
        normalized.metric_value,
        normalized.period_end,
        normalized.source_run_id
    from market.financial_metric_normalized normalized
    join active_recommendations recommendation on recommendation.instrument_id = normalized.instrument_id
    where normalized.as_of_date <= {sql_date(as_of_date)}
      and normalized.statement_scope = 'annual'
      and normalized.metric_status = 'computed'
      and normalized.metric_code in (
        'net_margin',
        'operating_margin',
        'free_cash_flow_margin',
        'cash_flow_quality',
        'roe',
        'leverage_ratio'
      )
    order by
        normalized.instrument_id,
        normalized.metric_code,
        normalized.as_of_date desc,
        normalized.period_end desc
),
normalized_inputs as (
    select
        instrument_id,
        max(period_end) as latest_period_end,
        max(source_run_id) as source_run_id,
        avg(
            case metric_code
                when 'net_margin' then least(1::numeric, greatest(0::numeric, (metric_value + 0.1000::numeric) / 0.4000::numeric))
                when 'operating_margin' then least(1::numeric, greatest(0::numeric, (metric_value + 0.0500::numeric) / 0.3500::numeric))
                when 'free_cash_flow_margin' then least(1::numeric, greatest(0::numeric, (metric_value + 0.0500::numeric) / 0.3000::numeric))
                when 'cash_flow_quality' then least(1::numeric, greatest(0::numeric, metric_value / 1.5000::numeric))
                when 'roe' then least(1::numeric, greatest(0::numeric, (metric_value + 0.1000::numeric) / 0.5000::numeric))
                else null::numeric
            end
        ) as normalized_quality_score,
        avg(
            case
                when metric_code = 'leverage_ratio' then 1::numeric - least(1::numeric, greatest(0::numeric, metric_value / 3.0000::numeric))
                else null::numeric
            end
        ) as normalized_balance_sheet_score
    from latest_normalized_rows
    group by instrument_id
),
latest_peer_rows as (
    select distinct on (snapshot.instrument_id, snapshot.peer_group_id, snapshot.metric_code)
        snapshot.instrument_id,
        snapshot.metric_code,
        snapshot.percentile_rank,
        snapshot.source_run_id
    from market.peer_relative_snapshot snapshot
    join active_recommendations recommendation on recommendation.instrument_id = snapshot.instrument_id
    where snapshot.as_of_date <= {sql_date(as_of_date)}
      and snapshot.relative_signal <> 'insufficient_data'
    order by
        snapshot.instrument_id,
        snapshot.peer_group_id,
        snapshot.metric_code,
        snapshot.as_of_date desc
),
peer_inputs as (
    select
        instrument_id,
        max(source_run_id) as source_run_id,
        avg(percentile_rank) filter (
            where metric_code in (
                'net_margin',
                'operating_margin',
                'free_cash_flow_margin',
                'cash_flow_quality',
                'roe'
            )
        ) as peer_quality_score,
        avg(percentile_rank) filter (
            where metric_code in (
                'revenue_growth_yoy',
                'net_margin',
                'operating_margin',
                'free_cash_flow_margin',
                'cash_flow_quality',
                'roe'
            )
        ) as peer_relative_score,
        avg(1::numeric - percentile_rank) filter (where metric_code = 'leverage_ratio') as peer_balance_sheet_score
    from latest_peer_rows
    group by instrument_id
),
latest_valuation_rows as (
    select distinct on (valuation.instrument_id, valuation.method)
        valuation.instrument_id,
        valuation.method,
        valuation.margin_of_safety,
        valuation.confidence,
        valuation.source_run_id
    from market.valuation_snapshot valuation
    join active_recommendations recommendation on recommendation.instrument_id = valuation.instrument_id
    where valuation.as_of_date <= {sql_date(as_of_date)}
    order by
        valuation.instrument_id,
        valuation.method,
        valuation.as_of_date desc,
        valuation.valuation_snapshot_id desc
),
valuation_inputs as (
    select
        instrument_id,
        max(source_run_id) as source_run_id,
        case
            when sum(coalesce(confidence, 0.2500)) > 0 then
                (
                    sum(
                        least(1::numeric, greatest(0::numeric, coalesce(margin_of_safety, 0::numeric) + 0.5000::numeric))
                        * coalesce(confidence, 0.2500)
                    )
                    / sum(coalesce(confidence, 0.2500))
                )::numeric(8,4)
            else null::numeric
        end as valuation_margin_score,
        jsonb_agg(
            jsonb_build_object(
                'method', method,
                'margin_of_safety', margin_of_safety,
                'confidence', confidence
            )
            order by method
        ) as valuation_methods
    from latest_valuation_rows
    group by instrument_id
),
score_inputs as (
    select
        recommendation.recommendation_id,
        recommendation.instrument_id,
        recommendation.primary_symbol,
        recommendation.thesis_id,
        recommendation.thesis_status,
        recommendation.invalidation_conditions,
        coalesce(peer.peer_quality_score, normalized.normalized_quality_score, 0.5000)::numeric(8,4) as fundamental_quality_score,
        coalesce(valuation.valuation_margin_score, 0.5000)::numeric(8,4) as valuation_margin_score,
        coalesce(peer.peer_relative_score, peer.peer_quality_score, normalized.normalized_quality_score, 0.5000)::numeric(8,4) as peer_relative_score,
        coalesce(peer.peer_balance_sheet_score, normalized.normalized_balance_sheet_score, 0.5000)::numeric(8,4) as balance_sheet_risk_penalty,
        case
            when recommendation.thesis_id is null then 0.3500::numeric
            when lower(coalesce(recommendation.thesis_status, '')) in ('active', 'open') then 0.7500::numeric
            when lower(coalesce(recommendation.thesis_status, '')) in ('closed', 'invalidated', 'rejected') then 0.2000::numeric
            else 0.5000::numeric
        end as thesis_consistency_score,
        normalized.source_run_id as financial_source_run_id,
        peer.source_run_id as peer_source_run_id,
        valuation.source_run_id as valuation_source_run_id,
        valuation.valuation_methods,
        normalized.latest_period_end
    from active_recommendations recommendation
    left join normalized_inputs normalized on normalized.instrument_id = recommendation.instrument_id
    left join peer_inputs peer on peer.instrument_id = recommendation.instrument_id
    left join valuation_inputs valuation on valuation.instrument_id = recommendation.instrument_id
),
component_rows as (
    select
        score.recommendation_id,
        component.component_name,
        least(1::numeric, greatest(0::numeric, component.component_score))::numeric(8,4) as component_score,
        0.0000::numeric as component_weight,
        component.explanation
    from score_inputs score
    cross join lateral (
        values
            (
                'fundamental_quality_score',
                score.fundamental_quality_score,
                'Zero-weight financial quality component from normalized profitability, cash-flow quality, and peer context. Source runs: financial='
                    || coalesce(score.financial_source_run_id::text, 'none')
                    || ', peer='
                    || coalesce(score.peer_source_run_id::text, 'none')
                    || '. Latest financial period: '
                    || coalesce(score.latest_period_end::text, 'unknown')
                    || '.'
            ),
            (
                'valuation_margin_score',
                score.valuation_margin_score,
                'Zero-weight valuation margin component from valuation_snapshot margin-of-safety context. Source run: '
                    || coalesce(score.valuation_source_run_id::text, 'none')
                    || '. Valuation methods: '
                    || coalesce(score.valuation_methods::text, '[]')
                    || '.'
            ),
            (
                'peer_relative_score',
                score.peer_relative_score,
                'Zero-weight peer-relative component from peer percentile ranks. Source run: '
                    || coalesce(score.peer_source_run_id::text, 'none')
                    || '.'
            ),
            (
                'balance_sheet_risk_penalty',
                score.balance_sheet_risk_penalty,
                'Zero-weight balance-sheet risk component; higher means lower observed leverage pressure. Source runs: financial='
                    || coalesce(score.financial_source_run_id::text, 'none')
                    || ', peer='
                    || coalesce(score.peer_source_run_id::text, 'none')
                    || '.'
            ),
            (
                'thesis_consistency_score',
                score.thesis_consistency_score,
                'Zero-weight thesis consistency component. Thesis id: '
                    || coalesce(score.thesis_id::text, 'none')
                    || ', status: '
                    || coalesce(score.thesis_status, 'missing')
                    || ', invalidation conditions present: '
                    || case when nullif(trim(coalesce(score.invalidation_conditions, '')), '') is null then 'false' else 'true' end
                    || '.'
            )
    ) as component(component_name, component_score, explanation)
),
upsert_components as (
    insert into signal.recommendation_score_component (
        recommendation_id,
        component_name,
        component_score,
        component_weight,
        explanation
    )
    select
        recommendation_id,
        component_name,
        component_score,
        component_weight,
        explanation
    from component_rows
    on conflict (recommendation_id, component_name) do update
    set
        component_score = excluded.component_score,
        component_weight = excluded.component_weight,
        explanation = excluded.explanation
    returning component_name, component_weight
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'source_run_id', {int(source_run_id)},
    'selected_batch_id', (select batch_id from selected_batch),
    'selected_batch_as_of_date', (select as_of_date::text from selected_batch),
    'active_recommendation_count', (select count(*)::integer from active_recommendations),
    'component_count', (select count(*)::integer from upsert_components),
    'component_counts',
        coalesce(
            (
                select json_object_agg(component_name, component_count order by component_name)
                from (
                    select component_name, count(*)::integer as component_count
                    from upsert_components
                    group by component_name
                ) counts
            ),
            '{{}}'::json
        ),
    'non_zero_weight_count',
        (
            select count(*)::integer
            from upsert_components
            where coalesce(component_weight, 0) <> 0
        ),
    'recommendation_total_score_mutated', false
)::text;"""


def load_recommendation_fundamental_components_preview(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    market_code: str = DEFAULT_MARKET_CODE,
    strategy_name: str = DEFAULT_STRATEGY_NAME,
    horizon_type: str = DEFAULT_HORIZON_TYPE,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_recommendation_fundamental_components_preview_sql(
                as_of_date=as_of_date,
                market_code=market_code,
                strategy_name=strategy_name,
                horizon_type=horizon_type,
            )
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Recommendation fundamental components preview did not return a JSON object.")
    return payload


def run_recommendation_fundamental_components(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    market_code: str = DEFAULT_MARKET_CODE,
    strategy_name: str = DEFAULT_STRATEGY_NAME,
    horizon_type: str = DEFAULT_HORIZON_TYPE,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    preview = load_recommendation_fundamental_components_preview(
        config=config,
        as_of_date=as_of_date,
        market_code=market_code,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        executor=sql_executor,
    )
    report: dict[str, object] = {
        "report_name": "recommendation_fundamental_components",
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "market_code": market_code,
        "strategy_name": strategy_name,
        "horizon_type": horizon_type,
        "model_name": DEFAULT_MODEL_NAME,
        "component_names": list(FUNDAMENTAL_COMPONENTS),
        "preview": preview,
        "recommendation_total_score_mutated": False,
        "recommendation_weight_mutated": False,
    }
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "model_name": DEFAULT_MODEL_NAME,
            "component_names": list(FUNDAMENTAL_COMPONENTS),
            "recommendation_total_score_mutated": False,
            "recommendation_weight_mutated": False,
        },
    )
    try:
        upsert_summary = json.loads(
            sql_executor.execute_scalar(
                render_recommendation_fundamental_components_upsert_sql(
                    as_of_date=as_of_date,
                    source_run_id=run_id,
                    market_code=market_code,
                    strategy_name=strategy_name,
                    horizon_type=horizon_type,
                )
            )
        )
        if not isinstance(upsert_summary, dict):
            raise ValueError("Recommendation fundamental components upsert did not return a JSON object.")
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return {
        **report,
        "status": "completed",
        "run_id": run_id,
        "upsert": upsert_summary,
    }


def _component_sql_list() -> str:
    return ", ".join(sql_literal(component_name) for component_name in FUNDAMENTAL_COMPONENTS)
