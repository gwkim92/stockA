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


DEFAULT_PIPELINE_NAME = "financial_metric_normalization"
DEFAULT_MODEL_NAME = "deterministic-financial-sql-v1"
DEFAULT_PEER_RELATIVE_PIPELINE_NAME = "peer_relative_analysis"
DEFAULT_PEER_RELATIVE_MODEL_NAME = "deterministic-peer-relative-sql-v1"
DEFAULT_PEER_GROUP_CODE = "US_CORE_FINANCIAL_DISCLOSURE"
DEFAULT_PEER_GROUP_NAME = "US Core Financial Disclosure Coverage"
STANDARD_FINANCIAL_METRICS = (
    "revenue_growth_yoy",
    "gross_margin",
    "operating_margin",
    "net_margin",
    "operating_cash_flow_margin",
    "free_cash_flow_margin",
    "cash_flow_quality",
    "roe",
    "leverage_ratio",
    "roic",
)
PEER_RELATIVE_STATEMENT_SCOPES = ("annual", "quarterly", "all")


def render_financial_metric_normalization_preview_sql(*, as_of_date: date, limit: int | None = None) -> str:
    limit_clause = "" if limit is None else f"\n    limit {int(limit)}"
    if limit is not None and limit <= 0:
        raise ValueError("limit must be greater than 0.")
    return f"""-- financial metric normalization preview
with scoped_periods as (
    select
        period.period_id,
        period.instrument_id,
        instrument.primary_symbol,
        period.statement_scope,
        period.fiscal_year,
        period.fiscal_quarter,
        period.period_end
    from market.financial_statement_period period
    join ref.instrument instrument on instrument.instrument_id = period.instrument_id
    where period.period_end <= {sql_date(as_of_date)}
    order by period.period_end desc, instrument.primary_symbol asc, period.period_id desc{limit_clause}
),
metric_codes as (
    select distinct metric.metric_code
    from market.financial_metric_value metric
    join scoped_periods period on period.period_id = metric.period_id
),
normalized_rows as (
    select *
    from market.financial_metric_normalized normalized
    where normalized.as_of_date = {sql_date(as_of_date)}
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'model_name', {sql_literal(DEFAULT_MODEL_NAME)},
    'standard_metric_codes', {sql_literal(json.dumps(STANDARD_FINANCIAL_METRICS))}::jsonb,
    'source_period_count', (select count(*)::integer from scoped_periods),
    'source_instrument_count', (select count(distinct instrument_id)::integer from scoped_periods),
    'latest_source_period_end', (select max(period_end)::text from scoped_periods),
    'source_metric_codes', coalesce((select json_agg(metric_code order by metric_code) from metric_codes), '[]'::json),
    'existing_normalized_count', (select count(*)::integer from normalized_rows),
    'existing_computed_count', (select count(*)::integer from normalized_rows where metric_status = 'computed')
)::text;"""


def render_financial_metric_normalization_upsert_sql(
    *,
    as_of_date: date,
    source_run_id: int,
    limit: int | None = None,
) -> str:
    if limit is not None and limit <= 0:
        raise ValueError("limit must be greater than 0.")
    limit_clause = "" if limit is None else f"\n    limit {int(limit)}"
    source_run = f"{int(source_run_id)}::bigint"
    return f"""-- financial metric normalization upsert
with scoped_periods as (
    select
        period.period_id,
        period.instrument_id,
        instrument.primary_symbol,
        period.statement_scope,
        period.fiscal_year,
        period.fiscal_quarter,
        period.period_end
    from market.financial_statement_period period
    join ref.instrument instrument on instrument.instrument_id = period.instrument_id
    where period.period_end <= {sql_date(as_of_date)}
    order by period.period_end desc, instrument.primary_symbol asc, period.period_id desc{limit_clause}
),
period_metrics as (
    select
        period.period_id,
        period.instrument_id,
        period.statement_scope,
        period.fiscal_year,
        period.fiscal_quarter,
        period.period_end,
        max(metric.metric_value) filter (where metric.metric_code = 'revenue') as revenue,
        max(metric.metric_value) filter (where metric.metric_code = 'gross_profit') as gross_profit,
        max(metric.metric_value) filter (where metric.metric_code = 'operating_income') as operating_income,
        max(metric.metric_value) filter (where metric.metric_code = 'net_income') as net_income,
        max(metric.metric_value) filter (where metric.metric_code = 'operating_cash_flow') as operating_cash_flow,
        max(metric.metric_value) filter (where metric.metric_code = 'capital_expenditure') as capital_expenditure,
        max(metric.metric_value) filter (where metric.metric_code = 'total_assets') as total_assets,
        max(metric.metric_value) filter (where metric.metric_code = 'total_liabilities') as total_liabilities,
        max(metric.metric_value) filter (where metric.metric_code = 'shareholders_equity') as shareholders_equity
    from scoped_periods period
    left join market.financial_metric_value metric on metric.period_id = period.period_id
    group by
        period.period_id,
        period.instrument_id,
        period.statement_scope,
        period.fiscal_year,
        period.fiscal_quarter,
        period.period_end
),
period_with_history as (
    select
        current_period.*,
        previous_period.previous_revenue
    from period_metrics current_period
    left join lateral (
        select previous_period.revenue as previous_revenue
        from period_metrics previous_period
        where previous_period.instrument_id = current_period.instrument_id
          and previous_period.statement_scope = current_period.statement_scope
          and previous_period.fiscal_year = current_period.fiscal_year - 1
          and previous_period.fiscal_quarter is not distinct from current_period.fiscal_quarter
        order by previous_period.period_end desc
        limit 1
    ) previous_period on true
),
metric_rows as (
    select
        period.instrument_id,
        {sql_date(as_of_date)} as as_of_date,
        period.period_id,
        period.statement_scope,
        period.fiscal_year,
        period.fiscal_quarter,
        period.period_end,
        metric.metric_code,
        metric.metric_value,
        metric.metric_unit,
        metric.metric_status,
        metric.rationale
    from period_with_history period
    cross join lateral (
        values
            (
                'revenue_growth_yoy',
                case
                    when period.revenue is not null and period.previous_revenue is not null and period.previous_revenue <> 0
                    then ((period.revenue - period.previous_revenue) / abs(period.previous_revenue))::numeric
                    else null::numeric
                end,
                'ratio',
                case
                    when period.revenue is null then 'unavailable'
                    when period.previous_revenue is null or period.previous_revenue = 0 then 'insufficient_history'
                    else 'computed'
                end,
                case
                    when period.revenue is null then 'Revenue fact is missing from SEC companyfacts.'
                    when period.previous_revenue is null or period.previous_revenue = 0 then 'Prior comparable revenue period is missing or zero.'
                    else 'Current revenue compared with prior fiscal-year comparable period.'
                end
            ),
            (
                'gross_margin',
                case
                    when period.gross_profit is not null and period.revenue is not null and period.revenue <> 0
                    then (period.gross_profit / period.revenue)::numeric
                    else null::numeric
                end,
                'ratio',
                case
                    when period.gross_profit is null or period.revenue is null then 'unavailable'
                    when period.revenue = 0 then 'unavailable'
                    else 'computed'
                end,
                case
                    when period.gross_profit is null then 'Gross profit fact is missing from SEC companyfacts.'
                    when period.revenue is null or period.revenue = 0 then 'Revenue denominator is missing or zero.'
                    else 'Gross profit divided by revenue.'
                end
            ),
            (
                'operating_margin',
                case
                    when period.operating_income is not null and period.revenue is not null and period.revenue <> 0
                    then (period.operating_income / period.revenue)::numeric
                    else null::numeric
                end,
                'ratio',
                case
                    when period.operating_income is null or period.revenue is null then 'unavailable'
                    when period.revenue = 0 then 'unavailable'
                    else 'computed'
                end,
                case
                    when period.operating_income is null then 'Operating income fact is missing from SEC companyfacts.'
                    when period.revenue is null or period.revenue = 0 then 'Revenue denominator is missing or zero.'
                    else 'Operating income divided by revenue.'
                end
            ),
            (
                'net_margin',
                case
                    when period.net_income is not null and period.revenue is not null and period.revenue <> 0
                    then (period.net_income / period.revenue)::numeric
                    else null::numeric
                end,
                'ratio',
                case
                    when period.net_income is null or period.revenue is null then 'unavailable'
                    when period.revenue = 0 then 'unavailable'
                    else 'computed'
                end,
                case
                    when period.net_income is null then 'Net income fact is missing from SEC companyfacts.'
                    when period.revenue is null or period.revenue = 0 then 'Revenue denominator is missing or zero.'
                    else 'Net income divided by revenue.'
                end
            ),
            (
                'operating_cash_flow_margin',
                case
                    when period.operating_cash_flow is not null and period.revenue is not null and period.revenue <> 0
                    then (period.operating_cash_flow / period.revenue)::numeric
                    else null::numeric
                end,
                'ratio',
                case
                    when period.operating_cash_flow is null or period.revenue is null then 'unavailable'
                    when period.revenue = 0 then 'unavailable'
                    else 'computed'
                end,
                case
                    when period.operating_cash_flow is null then 'Operating cash flow fact is missing from SEC companyfacts.'
                    when period.revenue is null or period.revenue = 0 then 'Revenue denominator is missing or zero.'
                    else 'Operating cash flow divided by revenue.'
                end
            ),
            (
                'free_cash_flow_margin',
                case
                    when period.operating_cash_flow is not null
                     and period.capital_expenditure is not null
                     and period.revenue is not null
                     and period.revenue <> 0
                    then ((period.operating_cash_flow - abs(period.capital_expenditure)) / period.revenue)::numeric
                    else null::numeric
                end,
                'ratio',
                case
                    when period.operating_cash_flow is null or period.capital_expenditure is null or period.revenue is null then 'unavailable'
                    when period.revenue = 0 then 'unavailable'
                    else 'computed'
                end,
                case
                    when period.operating_cash_flow is null then 'Operating cash flow fact is missing from SEC companyfacts.'
                    when period.capital_expenditure is null then 'Capital expenditure fact is missing from SEC companyfacts.'
                    when period.revenue is null or period.revenue = 0 then 'Revenue denominator is missing or zero.'
                    else 'Operating cash flow minus absolute capital expenditure, divided by revenue.'
                end
            ),
            (
                'cash_flow_quality',
                case
                    when period.operating_cash_flow is not null and period.net_income is not null and period.net_income <> 0
                    then (period.operating_cash_flow / abs(period.net_income))::numeric
                    else null::numeric
                end,
                'ratio',
                case
                    when period.operating_cash_flow is null or period.net_income is null then 'unavailable'
                    when period.net_income = 0 then 'unavailable'
                    else 'computed'
                end,
                case
                    when period.operating_cash_flow is null then 'Operating cash flow fact is missing from SEC companyfacts.'
                    when period.net_income is null or period.net_income = 0 then 'Net income denominator is missing or zero.'
                    else 'Operating cash flow divided by absolute net income.'
                end
            ),
            (
                'roe',
                case
                    when period.net_income is not null and period.shareholders_equity is not null and period.shareholders_equity <> 0
                    then (period.net_income / abs(period.shareholders_equity))::numeric
                    else null::numeric
                end,
                'ratio',
                case
                    when period.net_income is null or period.shareholders_equity is null then 'unavailable'
                    when period.shareholders_equity = 0 then 'unavailable'
                    else 'computed'
                end,
                case
                    when period.net_income is null then 'Net income fact is missing from SEC companyfacts.'
                    when period.shareholders_equity is null or period.shareholders_equity = 0 then 'Shareholders equity denominator is missing or zero.'
                    else 'Net income divided by absolute shareholders equity.'
                end
            ),
            (
                'leverage_ratio',
                case
                    when period.total_liabilities is not null and period.shareholders_equity is not null and period.shareholders_equity <> 0
                    then (period.total_liabilities / abs(period.shareholders_equity))::numeric
                    else null::numeric
                end,
                'ratio',
                case
                    when period.total_liabilities is null or period.shareholders_equity is null then 'unavailable'
                    when period.shareholders_equity = 0 then 'unavailable'
                    else 'computed'
                end,
                case
                    when period.total_liabilities is null then 'Total liabilities fact is missing from SEC companyfacts.'
                    when period.shareholders_equity is null or period.shareholders_equity = 0 then 'Shareholders equity denominator is missing or zero.'
                    else 'Total liabilities divided by absolute shareholders equity.'
                end
            ),
            (
                'roic',
                null::numeric,
                'ratio',
                'unavailable',
                'ROIC requires a consistent invested capital model; this foundation does not infer it from incomplete facts.'
            )
    ) as metric(metric_code, metric_value, metric_unit, metric_status, rationale)
),
upserted as (
    insert into market.financial_metric_normalized (
        instrument_id,
        as_of_date,
        period_id,
        statement_scope,
        fiscal_year,
        fiscal_quarter,
        period_end,
        metric_code,
        metric_value,
        metric_unit,
        metric_status,
        rationale,
        source_run_id
    )
    select
        instrument_id,
        as_of_date,
        period_id,
        statement_scope,
        fiscal_year,
        fiscal_quarter,
        period_end,
        metric_code,
        metric_value,
        metric_unit,
        metric_status,
        rationale,
        {source_run}
    from metric_rows
    on conflict (instrument_id, as_of_date, statement_scope, period_end, metric_code) do update
    set
        period_id = excluded.period_id,
        fiscal_year = excluded.fiscal_year,
        fiscal_quarter = excluded.fiscal_quarter,
        metric_value = excluded.metric_value,
        metric_unit = excluded.metric_unit,
        metric_status = excluded.metric_status,
        rationale = excluded.rationale,
        source_run_id = excluded.source_run_id
    returning metric_code, metric_status
),
summary as (
    select
        count(*)::integer as upserted_count,
        count(*) filter (where metric_status = 'computed')::integer as computed_count,
        count(*) filter (where metric_status = 'unavailable')::integer as unavailable_count,
        count(*) filter (where metric_status = 'insufficient_history')::integer as insufficient_history_count
    from upserted
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'source_run_id', {int(source_run_id)},
    'summary', (select row_to_json(summary) from summary),
    'metric_counts',
        coalesce(
            (
                select json_object_agg(metric_code, metric_count order by metric_code)
                from (
                    select metric_code, count(*)::integer as metric_count
                    from upserted
                    group by metric_code
                ) counts
            ),
            '{{}}'::json
        ),
    'status_counts',
        coalesce(
            (
                select json_object_agg(metric_status, status_count order by metric_status)
                from (
                    select metric_status, count(*)::integer as status_count
                    from upserted
                    group by metric_status
                ) counts
            ),
            '{{}}'::json
        )
)::text;"""


def load_financial_metric_normalization_preview(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    limit: int | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(render_financial_metric_normalization_preview_sql(as_of_date=as_of_date, limit=limit))
    )
    if not isinstance(payload, dict):
        raise ValueError("Financial metric normalization preview did not return a JSON object.")
    return payload


def run_financial_metric_normalization(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    limit: int | None = None,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    preview = load_financial_metric_normalization_preview(
        config=config,
        as_of_date=as_of_date,
        limit=limit,
        executor=sql_executor,
    )
    report: dict[str, object] = {
        "report_name": "financial_metric_normalization",
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "limit": limit,
        "model_name": DEFAULT_MODEL_NAME,
        "standard_metric_codes": list(STANDARD_FINANCIAL_METRICS),
        "preview": preview,
        "recommendation_scoring_mutated": False,
    }
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "limit": limit,
            "model_name": DEFAULT_MODEL_NAME,
            "recommendation_scoring_mutated": False,
        },
    )
    try:
        upsert_summary = json.loads(
            sql_executor.execute_scalar(
                render_financial_metric_normalization_upsert_sql(
                    as_of_date=as_of_date,
                    source_run_id=run_id,
                    limit=limit,
                )
            )
        )
        if not isinstance(upsert_summary, dict):
            raise ValueError("Financial metric normalization upsert did not return a JSON object.")
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


def render_peer_relative_analysis_preview_sql(
    *,
    as_of_date: date,
    statement_scope: str = "annual",
    min_peer_count: int = 2,
) -> str:
    _validate_peer_relative_args(statement_scope=statement_scope, min_peer_count=min_peer_count)
    scope_filter = _statement_scope_filter("normalized", statement_scope=statement_scope)
    return f"""-- peer relative analysis preview
with latest_metric_rows as (
    select distinct on (normalized.instrument_id, normalized.metric_code)
        normalized.instrument_id,
        normalized.metric_code,
        normalized.metric_value,
        normalized.period_end,
        normalized.statement_scope
    from market.financial_metric_normalized normalized
    where normalized.as_of_date <= {sql_date(as_of_date)}
      and normalized.metric_status = 'computed'{scope_filter}
    order by
        normalized.instrument_id,
        normalized.metric_code,
        normalized.as_of_date desc,
        normalized.period_end desc
),
coverage_instruments as (
    select distinct metric.instrument_id
    from latest_metric_rows metric
),
classification_peer_groups as (
    select
        node.taxonomy_family,
        node.node_type,
        node.code,
        node.name,
        count(distinct membership.instrument_id)::integer as member_count
    from ref.instrument_classification_membership membership
    join coverage_instruments coverage on coverage.instrument_id = membership.instrument_id
    join ref.classification_node node on node.node_id = membership.node_id
    where node.status = 'active'
      and membership.valid_from <= {sql_date(as_of_date)}
      and (membership.valid_to is null or membership.valid_to >= {sql_date(as_of_date)})
    group by node.taxonomy_family, node.node_type, node.code, node.name
    having count(distinct membership.instrument_id) >= {min_peer_count}
),
existing_peer_groups as (
    select count(*)::integer as count
    from ref.peer_group
    where status = 'active'
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'model_name', {sql_literal(DEFAULT_PEER_RELATIVE_MODEL_NAME)},
    'statement_scope', {sql_literal(statement_scope)},
    'min_peer_count', {min_peer_count},
    'standard_metric_codes', {sql_literal(json.dumps(STANDARD_FINANCIAL_METRICS))}::jsonb,
    'coverage_instrument_count', (select count(*)::integer from coverage_instruments),
    'latest_metric_count', (select count(*)::integer from latest_metric_rows),
    'classification_peer_group_count', (select count(*)::integer from classification_peer_groups),
    'existing_peer_group_count', (select count from existing_peer_groups),
    'fallback_group_code', {sql_literal(DEFAULT_PEER_GROUP_CODE)}
)::text;"""


def render_peer_relative_analysis_upsert_sql(
    *,
    as_of_date: date,
    source_run_id: int,
    statement_scope: str = "annual",
    min_peer_count: int = 2,
) -> str:
    _validate_peer_relative_args(statement_scope=statement_scope, min_peer_count=min_peer_count)
    scope_filter = _statement_scope_filter("normalized", statement_scope=statement_scope)
    metric_values = ",\n        ".join(f"({sql_literal(metric_code)})" for metric_code in STANDARD_FINANCIAL_METRICS)
    return f"""-- peer relative analysis upsert
with metric_universe(metric_code) as (
    values
        {metric_values}
),
latest_metric_rows as (
    select distinct on (normalized.instrument_id, normalized.metric_code)
        normalized.instrument_id,
        normalized.metric_code,
        normalized.metric_value,
        normalized.period_end,
        normalized.statement_scope
    from market.financial_metric_normalized normalized
    where normalized.as_of_date <= {sql_date(as_of_date)}
      and normalized.metric_status = 'computed'{scope_filter}
    order by
        normalized.instrument_id,
        normalized.metric_code,
        normalized.as_of_date desc,
        normalized.period_end desc
),
coverage_instruments as (
    select distinct metric.instrument_id
    from latest_metric_rows metric
),
classification_members as (
    select distinct
        (
            'CLASSIFICATION_'
            || regexp_replace(
                upper(node.taxonomy_family || '_' || node.node_type || '_' || node.code),
                '[^A-Z0-9]+',
                '_',
                'g'
            )
        ) as group_code,
        node.name as group_name,
        (
            'classification membership: '
            || node.taxonomy_family
            || '/'
            || node.node_type
            || '/'
            || node.code
        ) as methodology,
        membership.instrument_id
    from ref.instrument_classification_membership membership
    join coverage_instruments coverage on coverage.instrument_id = membership.instrument_id
    join ref.classification_node node on node.node_id = membership.node_id
    where node.status = 'active'
      and membership.valid_from <= {sql_date(as_of_date)}
      and (membership.valid_to is null or membership.valid_to >= {sql_date(as_of_date)})
),
classification_groups as (
    select
        group_code,
        group_name,
        methodology,
        count(distinct instrument_id)::integer as member_count
    from classification_members
    group by group_code, group_name, methodology
    having count(distinct instrument_id) >= {min_peer_count}
),
fallback_group as (
    select
        {sql_literal(DEFAULT_PEER_GROUP_CODE)} as group_code,
        {sql_literal(DEFAULT_PEER_GROUP_NAME)} as group_name,
        'fallback group: all instruments with computed normalized financial metrics' as methodology,
        count(*)::integer as member_count
    from coverage_instruments
    having count(*) >= {min_peer_count}
),
candidate_peer_groups as (
    select group_code, group_name, methodology from classification_groups
    union all
    select group_code, group_name, methodology from fallback_group
),
candidate_group_members as (
    select distinct
        member.group_code,
        member.instrument_id
    from classification_members member
    join classification_groups candidate on candidate.group_code = member.group_code
    union
    select
        {sql_literal(DEFAULT_PEER_GROUP_CODE)} as group_code,
        coverage.instrument_id
    from coverage_instruments coverage
    where exists (select 1 from fallback_group)
),
upsert_groups as (
    insert into ref.peer_group (
        group_code,
        name,
        methodology,
        status
    )
    select
        group_code,
        group_name,
        methodology,
        'active'
    from candidate_peer_groups
    on conflict (group_code) do update
    set
        name = excluded.name,
        methodology = excluded.methodology,
        status = excluded.status
    returning peer_group_id, group_code
),
upsert_members as (
    insert into ref.peer_group_member (
        peer_group_id,
        instrument_id,
        member_role,
        weight,
        source,
        valid_from,
        valid_to
    )
    select
        peer_group.peer_group_id,
        member.instrument_id,
        'constituent',
        null::numeric,
        'peer-relative-analysis-run',
        {sql_date(as_of_date)},
        null::date
    from candidate_group_members member
    join upsert_groups peer_group on peer_group.group_code = member.group_code
    on conflict (peer_group_id, instrument_id, valid_from) do update
    set
        member_role = excluded.member_role,
        weight = excluded.weight,
        source = excluded.source,
        valid_to = excluded.valid_to
    returning peer_group_id, instrument_id
),
member_metric_grid as (
    select
        member.peer_group_id,
        member.instrument_id,
        metric.metric_code
    from upsert_members member
    cross join metric_universe metric
),
member_metric_values as (
    select
        grid.peer_group_id,
        grid.instrument_id,
        grid.metric_code,
        metric.metric_value
    from member_metric_grid grid
    left join latest_metric_rows metric
      on metric.instrument_id = grid.instrument_id
     and metric.metric_code = grid.metric_code
),
group_metric_stats as (
    select
        peer_group_id,
        metric_code,
        count(metric_value)::integer as computed_peer_count,
        percentile_cont(0.5) within group (order by metric_value)::numeric(24,8) as peer_median_value
    from member_metric_values
    where metric_value is not null
    group by peer_group_id, metric_code
),
ranked_values as (
    select
        value.peer_group_id,
        value.instrument_id,
        value.metric_code,
        value.metric_value,
        percent_rank() over (
            partition by value.peer_group_id, value.metric_code
            order by value.metric_value
        )::numeric(8,4) as percentile_rank
    from member_metric_values value
    where value.metric_value is not null
),
snapshot_rows as (
    select
        value.peer_group_id,
        value.instrument_id,
        value.metric_code,
        value.metric_value,
        stats.peer_median_value,
        ranked.percentile_rank,
        case
            when value.metric_value is null then 'insufficient_data'
            when coalesce(stats.computed_peer_count, 0) < {min_peer_count} then 'insufficient_data'
            when ranked.percentile_rank >= 0.6600 then 'above_peer'
            when ranked.percentile_rank <= 0.3400 then 'below_peer'
            else 'near_peer'
        end as relative_signal
    from member_metric_values value
    left join group_metric_stats stats
      on stats.peer_group_id = value.peer_group_id
     and stats.metric_code = value.metric_code
    left join ranked_values ranked
      on ranked.peer_group_id = value.peer_group_id
     and ranked.instrument_id = value.instrument_id
     and ranked.metric_code = value.metric_code
),
upsert_snapshots as (
    insert into market.peer_relative_snapshot (
        instrument_id,
        peer_group_id,
        as_of_date,
        metric_code,
        instrument_value,
        peer_median_value,
        percentile_rank,
        relative_signal,
        source_run_id
    )
    select
        instrument_id,
        peer_group_id,
        {sql_date(as_of_date)},
        metric_code,
        metric_value,
        peer_median_value,
        percentile_rank,
        relative_signal,
        {int(source_run_id)}::bigint
    from snapshot_rows
    on conflict (instrument_id, peer_group_id, as_of_date, metric_code) do update
    set
        instrument_value = excluded.instrument_value,
        peer_median_value = excluded.peer_median_value,
        percentile_rank = excluded.percentile_rank,
        relative_signal = excluded.relative_signal,
        source_run_id = excluded.source_run_id
    returning metric_code, relative_signal
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'source_run_id', {int(source_run_id)},
    'statement_scope', {sql_literal(statement_scope)},
    'min_peer_count', {min_peer_count},
    'peer_group_count', (select count(*)::integer from upsert_groups),
    'peer_member_count', (select count(*)::integer from upsert_members),
    'snapshot_count', (select count(*)::integer from upsert_snapshots),
    'metric_counts',
        coalesce(
            (
                select json_object_agg(metric_code, metric_count order by metric_code)
                from (
                    select metric_code, count(*)::integer as metric_count
                    from upsert_snapshots
                    group by metric_code
                ) counts
            ),
            '{{}}'::json
        ),
    'relative_signal_counts',
        coalesce(
            (
                select json_object_agg(relative_signal, signal_count order by relative_signal)
                from (
                    select relative_signal, count(*)::integer as signal_count
                    from upsert_snapshots
                    group by relative_signal
                ) counts
            ),
            '{{}}'::json
        )
)::text;"""


def load_peer_relative_analysis_preview(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    statement_scope: str = "annual",
    min_peer_count: int = 2,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_peer_relative_analysis_preview_sql(
                as_of_date=as_of_date,
                statement_scope=statement_scope,
                min_peer_count=min_peer_count,
            )
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Peer relative analysis preview did not return a JSON object.")
    return payload


def run_peer_relative_analysis(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    statement_scope: str = "annual",
    min_peer_count: int = 2,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    preview = load_peer_relative_analysis_preview(
        config=config,
        as_of_date=as_of_date,
        statement_scope=statement_scope,
        min_peer_count=min_peer_count,
        executor=sql_executor,
    )
    report: dict[str, object] = {
        "report_name": "peer_relative_analysis",
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_PEER_RELATIVE_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "statement_scope": statement_scope,
        "min_peer_count": min_peer_count,
        "model_name": DEFAULT_PEER_RELATIVE_MODEL_NAME,
        "standard_metric_codes": list(STANDARD_FINANCIAL_METRICS),
        "preview": preview,
        "recommendation_scoring_mutated": False,
    }
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PEER_RELATIVE_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "statement_scope": statement_scope,
            "min_peer_count": min_peer_count,
            "model_name": DEFAULT_PEER_RELATIVE_MODEL_NAME,
            "recommendation_scoring_mutated": False,
        },
    )
    try:
        upsert_summary = json.loads(
            sql_executor.execute_scalar(
                render_peer_relative_analysis_upsert_sql(
                    as_of_date=as_of_date,
                    source_run_id=run_id,
                    statement_scope=statement_scope,
                    min_peer_count=min_peer_count,
                )
            )
        )
        if not isinstance(upsert_summary, dict):
            raise ValueError("Peer relative analysis upsert did not return a JSON object.")
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


def _validate_peer_relative_args(*, statement_scope: str, min_peer_count: int) -> None:
    if statement_scope not in PEER_RELATIVE_STATEMENT_SCOPES:
        raise ValueError(f"statement_scope must be one of: {', '.join(PEER_RELATIVE_STATEMENT_SCOPES)}.")
    if min_peer_count < 2:
        raise ValueError("min_peer_count must be at least 2.")


def _statement_scope_filter(alias: str, *, statement_scope: str) -> str:
    if statement_scope == "all":
        return ""
    return f"\n      and {alias}.statement_scope = {sql_literal(statement_scope)}"
