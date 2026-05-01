from __future__ import annotations

import json

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor

_ATTENTION_ACTIONS = (
    "exit_review",
    "reduce_review",
    "needs_thesis_review",
    "needs_outcome_review",
    "needs_weight_review",
    "increase_to_target",
    "trim_to_target",
)


def load_portfolio_review_run_history(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    limit: int = 20,
    review_source: str | None = None,
    risk_level: str | None = None,
    action: str | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    if limit <= 0:
        raise ValueError("limit must be greater than 0")

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(
        render_portfolio_review_run_history_sql(
            portfolio_name=portfolio_name,
            limit=limit,
            review_source=review_source,
            risk_level=risk_level,
            action=action,
        )
    )
    return json.loads(payload)


def render_portfolio_review_run_history_sql(
    *,
    portfolio_name: str,
    limit: int,
    review_source: str | None = None,
    risk_level: str | None = None,
    action: str | None = None,
) -> str:
    filters = [f"portfolio.portfolio_name = {sql_literal(portfolio_name)}"]
    if review_source:
        filters.append(f"review.review_source = {sql_literal(review_source)}")
    if risk_level:
        filters.append(f"review.risk_level = {sql_literal(risk_level)}")
    if action:
        filters.append(
            f"""exists (
            select 1
            from portfolio.review_item item_filter
            where item_filter.portfolio_review_id = review.portfolio_review_id
              and item_filter.action = {sql_literal(action)}
        )"""
        )

    attention_actions = ", ".join(sql_literal(action_name) for action_name in _ATTENTION_ACTIONS)
    where_clause = "\n      and ".join(filters)

    return f"""-- portfolio review run history report
with selected_reviews as (
    select
        review.portfolio_review_id,
        review.portfolio_id,
        portfolio.portfolio_name,
        review.review_date,
        review.review_source,
        review.overall_summary,
        review.cash_weight,
        review.risk_level,
        review.source_run_id,
        run.status as run_status,
        run.started_at,
        run.ended_at,
        run.error_summary
    from portfolio.review review
    join portfolio.portfolio portfolio on portfolio.portfolio_id = review.portfolio_id
    left join ops.pipeline_run run on run.run_id = review.source_run_id
    where {where_clause}
    order by review.review_date desc, review.portfolio_review_id desc
    limit {limit}
),
item_action_counts as (
    select
        item.portfolio_review_id,
        item.action,
        count(*)::int as action_count
    from portfolio.review_item item
    join selected_reviews review on review.portfolio_review_id = item.portfolio_review_id
    group by item.portfolio_review_id, item.action
),
item_totals as (
    select
        item.portfolio_review_id,
        count(*)::int as item_count
    from portfolio.review_item item
    join selected_reviews review on review.portfolio_review_id = item.portfolio_review_id
    group by item.portfolio_review_id
),
item_counts as (
    select
        totals.portfolio_review_id,
        totals.item_count,
        coalesce(jsonb_object_agg(action_count.action, action_count.action_count), '{{}}'::jsonb) as action_counts
    from item_totals totals
    left join item_action_counts action_count on action_count.portfolio_review_id = totals.portfolio_review_id
    group by totals.portfolio_review_id, totals.item_count
),
attention_items as (
    select
        item.portfolio_review_id,
        count(*) filter (where item.action in ({attention_actions}))::int as attention_item_count,
        coalesce(
            json_agg(
                json_build_object(
                    'symbol', instrument.primary_symbol,
                    'action', item.action,
                    'priority', item.priority,
                    'health_score', item.health_score,
                    'current_weight', item.current_weight,
                    'recommended_weight', item.recommended_weight,
                    'weight_gap', item.weight_gap,
                    'market_value', item.market_value,
                    'reason', item.reason
                )
                order by item.priority nulls last, instrument.primary_symbol
            ) filter (where item.action in ({attention_actions})),
            '[]'::json
        ) as attention_items
    from portfolio.review_item item
    join selected_reviews review on review.portfolio_review_id = item.portfolio_review_id
    join ref.instrument instrument on instrument.instrument_id = item.instrument_id
    group by item.portfolio_review_id
),
risk_counts as (
    select coalesce(jsonb_object_agg(risk_level, review_count), '{{}}'::jsonb) as counts
    from (
        select coalesce(risk_level, 'unknown') as risk_level, count(*)::int as review_count
        from selected_reviews
        group by coalesce(risk_level, 'unknown')
    ) counted
),
global_action_counts as (
    select coalesce(jsonb_object_agg(action, action_count), '{{}}'::jsonb) as counts
    from (
        select item.action, count(*)::int as action_count
        from portfolio.review_item item
        join selected_reviews review on review.portfolio_review_id = item.portfolio_review_id
        group by item.action
    ) counted
),
review_rows as (
    select
        review.*,
        coalesce(item_counts.item_count, 0) as item_count,
        coalesce(item_counts.action_counts, '{{}}'::jsonb) as action_counts,
        coalesce(attention_items.attention_item_count, 0) as attention_item_count,
        coalesce(attention_items.attention_items, '[]'::json) as attention_items
    from selected_reviews review
    left join item_counts on item_counts.portfolio_review_id = review.portfolio_review_id
    left join attention_items on attention_items.portfolio_review_id = review.portfolio_review_id
)
select json_build_object(
    'report_name', 'portfolio_review_run_history',
    'portfolio_name', {sql_literal(portfolio_name)},
    'limit', {limit},
    'review_source_filter', {sql_literal(review_source)},
    'risk_level_filter', {sql_literal(risk_level)},
    'action_filter', {sql_literal(action)},
    'review_count', (select count(*) from selected_reviews),
    'risk_counts', (select counts from risk_counts),
    'action_counts', (select counts from global_action_counts),
    'attention_item_count', coalesce((select sum(attention_item_count)::int from review_rows), 0),
    'latest_review',
    (
        select json_build_object(
            'portfolio_review_id', portfolio_review_id,
            'review_date', review_date,
            'review_source', review_source,
            'risk_level', risk_level,
            'cash_weight', cash_weight,
            'source_run_id', source_run_id,
            'run_status', run_status,
            'item_count', item_count,
            'attention_item_count', attention_item_count
        )
        from review_rows
        order by review_date desc, portfolio_review_id desc
        limit 1
    ),
    'reviews',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'portfolio_review_id', portfolio_review_id,
                    'review_date', review_date,
                    'review_source', review_source,
                    'risk_level', risk_level,
                    'cash_weight', cash_weight,
                    'source_run_id', source_run_id,
                    'run_status', run_status,
                    'started_at', started_at,
                    'ended_at', ended_at,
                    'error_summary', error_summary,
                    'overall_summary', overall_summary,
                    'item_count', item_count,
                    'action_counts', action_counts,
                    'attention_item_count', attention_item_count,
                    'attention_items', attention_items
                )
                order by review_date desc, portfolio_review_id desc
            )
            from review_rows
        ),
        '[]'::json
    )
)::text;"""
