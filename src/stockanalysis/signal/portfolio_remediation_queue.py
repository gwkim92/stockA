from __future__ import annotations

import json

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor

_QUEUE_ACTIONS = (
    "exit_review",
    "reduce_review",
    "needs_thesis_review",
    "needs_outcome_review",
    "needs_weight_review",
    "increase_to_target",
    "trim_to_target",
)


def load_portfolio_remediation_queue(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    limit: int = 20,
    review_source: str | None = None,
    action: str | None = None,
    remediation_type: str | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    if limit <= 0:
        raise ValueError("limit must be greater than 0")

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(
        render_portfolio_remediation_queue_sql(
            portfolio_name=portfolio_name,
            limit=limit,
            review_source=review_source,
            action=action,
            remediation_type=remediation_type,
        )
    )
    return json.loads(payload)


def render_portfolio_remediation_queue_sql(
    *,
    portfolio_name: str,
    limit: int,
    review_source: str | None = None,
    action: str | None = None,
    remediation_type: str | None = None,
) -> str:
    review_filters = [f"portfolio.portfolio_name = {sql_literal(portfolio_name)}"]
    if review_source:
        review_filters.append(f"review.review_source = {sql_literal(review_source)}")

    item_filters = [f"item.action in ({', '.join(sql_literal(value) for value in _QUEUE_ACTIONS)})"]
    if action:
        item_filters.append(f"item.action = {sql_literal(action)}")

    queue_filters: list[str] = []
    if remediation_type:
        queue_filters.append(f"remediation_type = {sql_literal(remediation_type)}")

    review_where = "\n      and ".join(review_filters)
    item_where = "\n      and ".join(item_filters)
    queue_where = ""
    if queue_filters:
        queue_where = "where " + "\n  and ".join(queue_filters)

    return f"""-- portfolio remediation queue report
with selected_reviews as (
    select
        review.portfolio_review_id,
        portfolio.portfolio_name,
        review.review_date,
        review.review_source,
        review.risk_level,
        review.source_run_id,
        run.status as run_status
    from portfolio.review review
    join portfolio.portfolio portfolio on portfolio.portfolio_id = review.portfolio_id
    left join ops.pipeline_run run on run.run_id = review.source_run_id
    where {review_where}
    order by review.review_date desc, review.portfolio_review_id desc
    limit {limit}
),
queue_candidates as (
    select
        review.portfolio_review_id,
        review.portfolio_name,
        review.review_date,
        review.review_source,
        review.risk_level,
        review.source_run_id,
        review.run_status,
        instrument.primary_symbol,
        item.action,
        item.priority,
        item.health_score,
        item.current_weight,
        item.recommended_weight,
        item.weight_gap,
        item.market_value,
        item.reason,
        case
            when item.action = 'needs_thesis_review' then 'thesis_remediation'
            when item.action = 'needs_outcome_review' then 'outcome_remediation'
            when item.action = 'needs_weight_review' then 'position_data_remediation'
            when item.action in ('increase_to_target', 'trim_to_target') then 'allocation_review'
            when item.action in ('exit_review', 'reduce_review') then 'risk_review'
            else 'manual_review'
        end as remediation_type,
        case
            when item.action = 'needs_thesis_review' then 'thesis_or_position_link_review'
            when item.action = 'needs_outcome_review' then 'performance_outcome_runner'
            when item.action = 'needs_weight_review' then 'portfolio_position_snapshot_upsert'
            when item.action in ('increase_to_target', 'trim_to_target') then 'allocation_policy_review'
            when item.action in ('exit_review', 'reduce_review') then 'human_risk_review'
            else 'manual_review'
        end as suggested_runner,
        case
            when item.action = 'needs_thesis_review' then 'Create or link an active thesis before the next portfolio review.'
            when item.action = 'needs_outcome_review' then 'Run performance outcome backfill or scheduled outcome runner for the requested measurement date.'
            when item.action = 'needs_weight_review' then 'Reload the position snapshot with a valid position weight.'
            when item.action = 'increase_to_target' then 'Review target allocation before any trade decision.'
            when item.action = 'trim_to_target' then 'Review overweight exposure before any trade decision.'
            when item.action = 'exit_review' then 'Review exit thesis and risk evidence; no trade automation is implied.'
            when item.action = 'reduce_review' then 'Review reduction thesis and risk evidence; no trade automation is implied.'
            else 'Review manually.'
        end as suggested_next_step
    from selected_reviews review
    join portfolio.review_item item on item.portfolio_review_id = review.portfolio_review_id
    join ref.instrument instrument on instrument.instrument_id = item.instrument_id
    where {item_where}
),
queue_items as (
    select *
    from queue_candidates
    {queue_where}
),
remediation_type_counts as (
    select coalesce(jsonb_object_agg(remediation_type, remediation_count), '{{}}'::jsonb) as counts
    from (
        select remediation_type, count(*)::int as remediation_count
        from queue_items
        group by remediation_type
    ) counted
),
action_counts as (
    select coalesce(jsonb_object_agg(action, action_count), '{{}}'::jsonb) as counts
    from (
        select action, count(*)::int as action_count
        from queue_items
        group by action
    ) counted
)
select json_build_object(
    'report_name', 'portfolio_remediation_queue',
    'portfolio_name', {sql_literal(portfolio_name)},
    'limit', {limit},
    'review_source_filter', {sql_literal(review_source)},
    'action_filter', {sql_literal(action)},
    'remediation_type_filter', {sql_literal(remediation_type)},
    'queue_item_count', (select count(*) from queue_items),
    'remediation_type_counts', (select counts from remediation_type_counts),
    'action_counts', (select counts from action_counts),
    'items',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'portfolio_review_id', portfolio_review_id,
                    'portfolio_name', portfolio_name,
                    'review_date', review_date,
                    'review_source', review_source,
                    'risk_level', risk_level,
                    'source_run_id', source_run_id,
                    'run_status', run_status,
                    'symbol', primary_symbol,
                    'action', action,
                    'remediation_type', remediation_type,
                    'suggested_runner', suggested_runner,
                    'suggested_next_step', suggested_next_step,
                    'priority', priority,
                    'health_score', health_score,
                    'current_weight', current_weight,
                    'recommended_weight', recommended_weight,
                    'weight_gap', weight_gap,
                    'market_value', market_value,
                    'reason', reason
                )
                order by review_date desc, priority nulls last, primary_symbol
            )
            from queue_items
        ),
        '[]'::json
    )
)::text;"""
