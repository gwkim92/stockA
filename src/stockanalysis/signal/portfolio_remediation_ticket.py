from __future__ import annotations

import json

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.portfolio_remediation_queue import _QUEUE_ACTIONS
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)

_TICKET_STATUSES = ("open", "in_progress", "resolved", "ignored")


def load_portfolio_remediation_ticket_report(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    limit: int = 20,
    status: str | None = "open",
    action: str | None = None,
    remediation_type: str | None = None,
    suggested_runner: str | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    if limit <= 0:
        raise ValueError("limit must be greater than 0")

    normalized_status = None if status == "all" else status
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(
        render_portfolio_remediation_ticket_report_sql(
            portfolio_name=portfolio_name,
            limit=limit,
            status=normalized_status,
            action=action,
            remediation_type=remediation_type,
            suggested_runner=suggested_runner,
        )
    )
    return json.loads(payload)


def run_portfolio_remediation_ticket_update(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    ticket_id: int,
    status: str,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    if ticket_id <= 0:
        raise ValueError("ticket_id must be greater than 0")
    normalized_status = status.lower()
    if normalized_status not in _TICKET_STATUSES:
        raise ValueError(f"Unsupported ticket status: {status}")

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="portfolio_remediation_ticket_update",
        config_json={
            "portfolio_name": portfolio_name,
            "ticket_id": ticket_id,
            "status": normalized_status,
        },
    )
    try:
        summary = json.loads(
            sql_executor.execute_scalar(
                render_portfolio_remediation_ticket_update_sql(
                    portfolio_name=portfolio_name,
                    ticket_id=ticket_id,
                    status=normalized_status,
                )
            )
        )
        if int(summary["updated_count"]) != 1:
            raise ValueError(
                f"No remediation ticket matched ticket_id={ticket_id} for portfolio {portfolio_name}."
            )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    summary["run_id"] = run_id
    return summary


def run_portfolio_remediation_ticket_bootstrap(
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
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="portfolio_remediation_ticket_bootstrap",
        config_json={
            "portfolio_name": portfolio_name,
            "limit": limit,
            "review_source": review_source,
            "action": action,
            "remediation_type": remediation_type,
        },
    )
    try:
        summary = json.loads(
            sql_executor.execute_scalar(
                render_portfolio_remediation_ticket_bootstrap_sql(
                    portfolio_name=portfolio_name,
                    limit=limit,
                    source_run_id=run_id,
                    review_source=review_source,
                    action=action,
                    remediation_type=remediation_type,
                )
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    summary["run_id"] = run_id
    return summary


def render_portfolio_remediation_ticket_report_sql(
    *,
    portfolio_name: str,
    limit: int,
    status: str | None = "open",
    action: str | None = None,
    remediation_type: str | None = None,
    suggested_runner: str | None = None,
) -> str:
    ticket_filters = [f"portfolio.portfolio_name = {sql_literal(portfolio_name)}"]
    if status:
        ticket_filters.append(f"ticket.status = {sql_literal(status)}")
    if action:
        ticket_filters.append(f"ticket.action = {sql_literal(action)}")
    if remediation_type:
        ticket_filters.append(f"ticket.remediation_type = {sql_literal(remediation_type)}")
    if suggested_runner:
        ticket_filters.append(f"ticket.suggested_runner = {sql_literal(suggested_runner)}")

    ticket_where = "\n      and ".join(ticket_filters)
    return f"""-- portfolio remediation ticket report
with selected_tickets as (
    select
        ticket.remediation_ticket_id,
        ticket.portfolio_review_id,
        portfolio.portfolio_name,
        review.review_date,
        review.review_source,
        instrument.primary_symbol,
        ticket.action,
        ticket.remediation_type,
        ticket.suggested_runner,
        ticket.suggested_next_step,
        ticket.status,
        ticket.priority,
        ticket.risk_level,
        ticket.health_score,
        ticket.current_weight,
        ticket.recommended_weight,
        ticket.latest_reason,
        ticket.source_run_id,
        run.status as source_run_status,
        ticket.opened_at,
        ticket.updated_at,
        ticket.last_seen_at,
        ticket.resolved_at
    from portfolio.remediation_ticket ticket
    join portfolio.review review on review.portfolio_review_id = ticket.portfolio_review_id
    join portfolio.portfolio portfolio on portfolio.portfolio_id = review.portfolio_id
    join ref.instrument instrument on instrument.instrument_id = ticket.instrument_id
    left join ops.pipeline_run run on run.run_id = ticket.source_run_id
    where {ticket_where}
    order by
        case ticket.status
            when 'open' then 1
            when 'in_progress' then 2
            when 'resolved' then 3
            when 'ignored' then 4
            else 5
        end,
        ticket.priority nulls last,
        ticket.last_seen_at desc,
        ticket.remediation_ticket_id desc
    limit {limit}
),
status_counts as (
    select coalesce(jsonb_object_agg(status, status_count), '{{}}'::jsonb) as counts
    from (
        select status, count(*)::int as status_count
        from selected_tickets
        group by status
    ) counted
),
remediation_type_counts as (
    select coalesce(jsonb_object_agg(remediation_type, remediation_count), '{{}}'::jsonb) as counts
    from (
        select remediation_type, count(*)::int as remediation_count
        from selected_tickets
        group by remediation_type
    ) counted
),
action_counts as (
    select coalesce(jsonb_object_agg(action, action_count), '{{}}'::jsonb) as counts
    from (
        select action, count(*)::int as action_count
        from selected_tickets
        group by action
    ) counted
)
select json_build_object(
    'report_name', 'portfolio_remediation_ticket_report',
    'portfolio_name', {sql_literal(portfolio_name)},
    'limit', {limit},
    'status_filter', {sql_literal(status)},
    'action_filter', {sql_literal(action)},
    'remediation_type_filter', {sql_literal(remediation_type)},
    'suggested_runner_filter', {sql_literal(suggested_runner)},
    'ticket_count', (select count(*) from selected_tickets),
    'status_counts', (select counts from status_counts),
    'remediation_type_counts', (select counts from remediation_type_counts),
    'action_counts', (select counts from action_counts),
    'tickets',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'remediation_ticket_id', remediation_ticket_id,
                    'portfolio_review_id', portfolio_review_id,
                    'portfolio_name', portfolio_name,
                    'review_date', review_date,
                    'review_source', review_source,
                    'symbol', primary_symbol,
                    'action', action,
                    'remediation_type', remediation_type,
                    'suggested_runner', suggested_runner,
                    'suggested_next_step', suggested_next_step,
                    'status', status,
                    'priority', priority,
                    'risk_level', risk_level,
                    'health_score', health_score,
                    'current_weight', current_weight,
                    'recommended_weight', recommended_weight,
                    'reason', latest_reason,
                    'source_run_id', source_run_id,
                    'source_run_status', source_run_status,
                    'opened_at', opened_at,
                    'updated_at', updated_at,
                    'last_seen_at', last_seen_at,
                    'resolved_at', resolved_at
                )
                order by
                    case status
                        when 'open' then 1
                        when 'in_progress' then 2
                        when 'resolved' then 3
                        when 'ignored' then 4
                        else 5
                    end,
                    priority nulls last,
                    last_seen_at desc,
                    remediation_ticket_id desc
            )
            from selected_tickets
        ),
        '[]'::json
    )
)::text;"""


def render_portfolio_remediation_ticket_update_sql(
    *,
    portfolio_name: str,
    ticket_id: int,
    status: str,
) -> str:
    resolved_at_sql = "now()" if status in ("resolved", "ignored") else "null::timestamptz"
    return f"""-- portfolio remediation ticket status update
with updated_ticket as (
    update portfolio.remediation_ticket ticket
    set
        status = {sql_literal(status)},
        updated_at = now(),
        resolved_at = {resolved_at_sql}
    from portfolio.review review
    join portfolio.portfolio portfolio on portfolio.portfolio_id = review.portfolio_id
    where ticket.portfolio_review_id = review.portfolio_review_id
      and portfolio.portfolio_name = {sql_literal(portfolio_name)}
      and ticket.remediation_ticket_id = {ticket_id}
    returning
        ticket.remediation_ticket_id,
        ticket.portfolio_review_id,
        ticket.instrument_id,
        ticket.action,
        ticket.remediation_type,
        ticket.suggested_runner,
        ticket.suggested_next_step,
        ticket.status,
        ticket.priority,
        ticket.risk_level,
        ticket.health_score,
        ticket.current_weight,
        ticket.recommended_weight,
        ticket.latest_reason,
        ticket.source_run_id,
        ticket.opened_at,
        ticket.updated_at,
        ticket.last_seen_at,
        ticket.resolved_at
),
ticket_payload as (
    select
        updated_ticket.*,
        portfolio.portfolio_name,
        review.review_date,
        review.review_source,
        instrument.primary_symbol,
        run.status as source_run_status
    from updated_ticket
    join portfolio.review review on review.portfolio_review_id = updated_ticket.portfolio_review_id
    join portfolio.portfolio portfolio on portfolio.portfolio_id = review.portfolio_id
    join ref.instrument instrument on instrument.instrument_id = updated_ticket.instrument_id
    left join ops.pipeline_run run on run.run_id = updated_ticket.source_run_id
)
select json_build_object(
    'report_name', 'portfolio_remediation_ticket_update',
    'portfolio_name', {sql_literal(portfolio_name)},
    'ticket_id', {ticket_id},
    'status', {sql_literal(status)},
    'updated_count', (select count(*) from updated_ticket),
    'ticket',
    (
        select json_build_object(
            'remediation_ticket_id', remediation_ticket_id,
            'portfolio_review_id', portfolio_review_id,
            'portfolio_name', portfolio_name,
            'review_date', review_date,
            'review_source', review_source,
            'symbol', primary_symbol,
            'action', action,
            'remediation_type', remediation_type,
            'suggested_runner', suggested_runner,
            'suggested_next_step', suggested_next_step,
            'status', status,
            'priority', priority,
            'risk_level', risk_level,
            'health_score', health_score,
            'current_weight', current_weight,
            'recommended_weight', recommended_weight,
            'reason', latest_reason,
            'source_run_id', source_run_id,
            'source_run_status', source_run_status,
            'opened_at', opened_at,
            'updated_at', updated_at,
            'last_seen_at', last_seen_at,
            'resolved_at', resolved_at
        )
        from ticket_payload
    )
)::text;"""


def render_portfolio_remediation_ticket_bootstrap_sql(
    *,
    portfolio_name: str,
    limit: int,
    source_run_id: int,
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

    ticket_filters: list[str] = []
    if remediation_type:
        ticket_filters.append(f"remediation_type = {sql_literal(remediation_type)}")

    review_where = "\n      and ".join(review_filters)
    item_where = "\n      and ".join(item_filters)
    ticket_where = ""
    if ticket_filters:
        ticket_where = "where " + "\n  and ".join(ticket_filters)

    return f"""-- portfolio remediation ticket bootstrap
with selected_reviews as (
    select
        review.portfolio_review_id,
        portfolio.portfolio_name,
        review.review_date,
        review.review_source,
        review.risk_level,
        review.source_run_id as review_source_run_id
    from portfolio.review review
    join portfolio.portfolio portfolio on portfolio.portfolio_id = review.portfolio_id
    where {review_where}
    order by review.review_date desc, review.portfolio_review_id desc
    limit {limit}
),
ticket_candidates as (
    select
        review.portfolio_review_id,
        review.portfolio_name,
        review.review_date,
        review.review_source,
        review.risk_level,
        instrument.instrument_id,
        instrument.primary_symbol,
        item.action,
        item.priority,
        item.health_score,
        item.current_weight,
        item.recommended_weight,
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
ticket_items as (
    select *
    from ticket_candidates
    {ticket_where}
),
upsert_tickets as (
    insert into portfolio.remediation_ticket (
        portfolio_review_id,
        instrument_id,
        action,
        remediation_type,
        suggested_runner,
        suggested_next_step,
        status,
        priority,
        risk_level,
        health_score,
        current_weight,
        recommended_weight,
        latest_reason,
        source_run_id,
        last_seen_at
    )
    select
        portfolio_review_id,
        instrument_id,
        action,
        remediation_type,
        suggested_runner,
        suggested_next_step,
        'open',
        priority,
        risk_level,
        health_score,
        current_weight,
        recommended_weight,
        reason,
        {source_run_id}::bigint,
        now()
    from ticket_items
    on conflict (portfolio_review_id, instrument_id, action, remediation_type) do update
    set
        suggested_runner = excluded.suggested_runner,
        suggested_next_step = excluded.suggested_next_step,
        status = 'open',
        priority = excluded.priority,
        risk_level = excluded.risk_level,
        health_score = excluded.health_score,
        current_weight = excluded.current_weight,
        recommended_weight = excluded.recommended_weight,
        latest_reason = excluded.latest_reason,
        source_run_id = excluded.source_run_id,
        updated_at = now(),
        last_seen_at = now(),
        resolved_at = null
    returning
        remediation_ticket_id,
        portfolio_review_id,
        instrument_id,
        action,
        remediation_type,
        suggested_runner,
        suggested_next_step,
        status,
        priority,
        risk_level,
        health_score,
        current_weight,
        recommended_weight,
        latest_reason
),
remediation_type_counts as (
    select coalesce(jsonb_object_agg(remediation_type, remediation_count), '{{}}'::jsonb) as counts
    from (
        select remediation_type, count(*)::int as remediation_count
        from upsert_tickets
        group by remediation_type
    ) counted
),
action_counts as (
    select coalesce(jsonb_object_agg(action, action_count), '{{}}'::jsonb) as counts
    from (
        select action, count(*)::int as action_count
        from upsert_tickets
        group by action
    ) counted
)
select json_build_object(
    'report_name', 'portfolio_remediation_ticket_bootstrap',
    'portfolio_name', {sql_literal(portfolio_name)},
    'limit', {limit},
    'review_source_filter', {sql_literal(review_source)},
    'action_filter', {sql_literal(action)},
    'remediation_type_filter', {sql_literal(remediation_type)},
    'ticket_count', (select count(*) from upsert_tickets),
    'remediation_type_counts', (select counts from remediation_type_counts),
    'action_counts', (select counts from action_counts),
    'tickets',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'remediation_ticket_id', ticket.remediation_ticket_id,
                    'portfolio_review_id', ticket.portfolio_review_id,
                    'symbol', instrument.primary_symbol,
                    'action', ticket.action,
                    'remediation_type', ticket.remediation_type,
                    'suggested_runner', ticket.suggested_runner,
                    'suggested_next_step', ticket.suggested_next_step,
                    'status', ticket.status,
                    'priority', ticket.priority,
                    'risk_level', ticket.risk_level,
                    'health_score', ticket.health_score,
                    'current_weight', ticket.current_weight,
                    'recommended_weight', ticket.recommended_weight,
                    'reason', ticket.latest_reason
                )
                order by ticket.priority nulls last, instrument.primary_symbol
            )
            from upsert_tickets ticket
            join ref.instrument instrument on instrument.instrument_id = ticket.instrument_id
        ),
        '[]'::json
    )
)::text;"""
