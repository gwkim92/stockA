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
DEFAULT_VALUATION_PIPELINE_NAME = "valuation_snapshot"
DEFAULT_VALUATION_MODEL_NAME = "deterministic-valuation-snapshot-sql-v1"
DEFAULT_FINANCIAL_FORECAST_PIPELINE_NAME = "financial_forecast_inputs"
DEFAULT_FINANCIAL_FORECAST_MODEL_NAME = "deterministic-financial-forecast-inputs-sql-v1"
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
    "free_cash_flow_to_net_income",
    "accrual_ratio",
    "capex_intensity",
    "roe",
    "leverage_ratio",
    "liabilities_to_assets",
    "roic",
)
PEER_RELATIVE_STATEMENT_SCOPES = ("annual", "quarterly", "all")
VALUATION_STATEMENT_SCOPES = ("annual", "quarterly")
VALUATION_METHODS = ("dcf_lite", "relative_multiple", "scenario_range")
FINANCIAL_FORECAST_SCENARIOS = ("bear", "base", "bull")
FINANCIAL_FORECAST_YEARS = 5


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
                'free_cash_flow_to_net_income',
                case
                    when period.operating_cash_flow is not null
                     and period.capital_expenditure is not null
                     and period.net_income is not null
                     and period.net_income <> 0
                    then ((period.operating_cash_flow - abs(period.capital_expenditure)) / abs(period.net_income))::numeric
                    else null::numeric
                end,
                'ratio',
                case
                    when period.operating_cash_flow is null or period.capital_expenditure is null or period.net_income is null then 'unavailable'
                    when period.net_income = 0 then 'unavailable'
                    else 'computed'
                end,
                case
                    when period.operating_cash_flow is null then 'Operating cash flow fact is missing from SEC companyfacts.'
                    when period.capital_expenditure is null then 'Capital expenditure fact is missing from SEC companyfacts.'
                    when period.net_income is null or period.net_income = 0 then 'Net income denominator is missing or zero.'
                    else 'Operating cash flow minus absolute capital expenditure, divided by absolute net income.'
                end
            ),
            (
                'accrual_ratio',
                case
                    when period.net_income is not null
                     and period.operating_cash_flow is not null
                     and period.total_assets is not null
                     and period.total_assets <> 0
                    then ((period.net_income - period.operating_cash_flow) / abs(period.total_assets))::numeric
                    else null::numeric
                end,
                'ratio',
                case
                    when period.net_income is null or period.operating_cash_flow is null or period.total_assets is null then 'unavailable'
                    when period.total_assets = 0 then 'unavailable'
                    else 'computed'
                end,
                case
                    when period.net_income is null then 'Net income fact is missing from SEC companyfacts.'
                    when period.operating_cash_flow is null then 'Operating cash flow fact is missing from SEC companyfacts.'
                    when period.total_assets is null or period.total_assets = 0 then 'Total assets denominator is missing or zero.'
                    else 'Net income minus operating cash flow, divided by absolute total assets. Lower positive accruals are generally higher earnings quality.'
                end
            ),
            (
                'capex_intensity',
                case
                    when period.capital_expenditure is not null and period.revenue is not null and period.revenue <> 0
                    then (abs(period.capital_expenditure) / period.revenue)::numeric
                    else null::numeric
                end,
                'ratio',
                case
                    when period.capital_expenditure is null or period.revenue is null then 'unavailable'
                    when period.revenue = 0 then 'unavailable'
                    else 'computed'
                end,
                case
                    when period.capital_expenditure is null then 'Capital expenditure fact is missing from SEC companyfacts.'
                    when period.revenue is null or period.revenue = 0 then 'Revenue denominator is missing or zero.'
                    else 'Absolute capital expenditure divided by revenue.'
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
                'liabilities_to_assets',
                case
                    when period.total_liabilities is not null and period.total_assets is not null and period.total_assets <> 0
                    then (period.total_liabilities / abs(period.total_assets))::numeric
                    else null::numeric
                end,
                'ratio',
                case
                    when period.total_liabilities is null or period.total_assets is null then 'unavailable'
                    when period.total_assets = 0 then 'unavailable'
                    else 'computed'
                end,
                case
                    when period.total_liabilities is null then 'Total liabilities fact is missing from SEC companyfacts.'
                    when period.total_assets is null or period.total_assets = 0 then 'Total assets denominator is missing or zero.'
                    else 'Total liabilities divided by absolute total assets.'
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


def render_financial_forecast_inputs_preview_sql(
    *,
    as_of_date: date,
    statement_scope: str = "annual",
) -> str:
    _validate_valuation_args(statement_scope=statement_scope)
    return f"""-- financial forecast inputs preview
with latest_raw_metric_rows as (
    select distinct on (period.instrument_id, metric.metric_code)
        period.instrument_id,
        metric.metric_code,
        metric.metric_value,
        period.period_end
    from market.financial_statement_period period
    join market.financial_metric_value metric on metric.period_id = period.period_id
    where period.period_end <= {sql_date(as_of_date)}
      and period.statement_scope = {sql_literal(statement_scope)}
      and metric.metric_code in (
        'revenue',
        'operating_cash_flow',
        'capital_expenditure'
      )
    order by period.instrument_id, metric.metric_code, period.period_end desc
),
raw_inputs as (
    select
        instrument_id,
        max(metric_value) filter (where metric_code = 'revenue') as revenue,
        max(metric_value) filter (where metric_code = 'operating_cash_flow') as operating_cash_flow,
        max(metric_value) filter (where metric_code = 'capital_expenditure') as capital_expenditure
    from latest_raw_metric_rows
    group by instrument_id
),
latest_normalized_rows as (
    select distinct on (normalized.instrument_id, normalized.metric_code)
        normalized.instrument_id,
        normalized.metric_code,
        normalized.metric_value
    from market.financial_metric_normalized normalized
    where normalized.as_of_date <= {sql_date(as_of_date)}
      and normalized.statement_scope = {sql_literal(statement_scope)}
      and normalized.metric_status = 'computed'
      and normalized.metric_code in (
        'revenue_growth_yoy',
        'operating_margin',
        'free_cash_flow_margin',
        'capex_intensity',
        'cash_flow_quality'
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
        max(metric_value) filter (where metric_code = 'revenue_growth_yoy') as revenue_growth_yoy,
        max(metric_value) filter (where metric_code = 'operating_margin') as operating_margin,
        max(metric_value) filter (where metric_code = 'free_cash_flow_margin') as free_cash_flow_margin,
        max(metric_value) filter (where metric_code = 'capex_intensity') as capex_intensity,
        max(metric_value) filter (where metric_code = 'cash_flow_quality') as cash_flow_quality
    from latest_normalized_rows
    group by instrument_id
),
forecast_context as (
    select
        raw.instrument_id,
        raw.revenue,
        raw.operating_cash_flow,
        raw.capital_expenditure,
        normalized.revenue_growth_yoy,
        normalized.operating_margin,
        normalized.free_cash_flow_margin,
        normalized.capex_intensity,
        normalized.cash_flow_quality
    from raw_inputs raw
    left join normalized_inputs normalized on normalized.instrument_id = raw.instrument_id
    where raw.revenue is not null
      and raw.revenue > 0
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'model_name', {sql_literal(DEFAULT_FINANCIAL_FORECAST_MODEL_NAME)},
    'statement_scope', {sql_literal(statement_scope)},
    'scenario_keys', {sql_literal(json.dumps(FINANCIAL_FORECAST_SCENARIOS))}::jsonb,
    'forecast_years', {FINANCIAL_FORECAST_YEARS},
    'raw_input_count', (select count(*)::integer from raw_inputs),
    'normalized_input_count', (select count(*)::integer from normalized_inputs),
    'forecast_context_count', (select count(*)::integer from forecast_context),
    'existing_forecast_row_count',
        (
            select count(*)::integer
            from market.financial_forecast_input
            where as_of_date = {sql_date(as_of_date)}
              and statement_scope = {sql_literal(statement_scope)}
        )
)::text;"""


def render_financial_forecast_inputs_upsert_sql(
    *,
    as_of_date: date,
    source_run_id: int,
    statement_scope: str = "annual",
) -> str:
    _validate_valuation_args(statement_scope=statement_scope)
    return f"""-- financial forecast inputs upsert
with latest_raw_metric_rows as (
    select distinct on (period.instrument_id, metric.metric_code)
        period.instrument_id,
        metric.metric_code,
        metric.metric_value,
        period.period_end
    from market.financial_statement_period period
    join market.financial_metric_value metric on metric.period_id = period.period_id
    where period.period_end <= {sql_date(as_of_date)}
      and period.statement_scope = {sql_literal(statement_scope)}
      and metric.metric_code in (
        'revenue',
        'operating_cash_flow',
        'capital_expenditure'
      )
    order by period.instrument_id, metric.metric_code, period.period_end desc
),
raw_inputs as (
    select
        instrument_id,
        max(metric_value) filter (where metric_code = 'revenue') as revenue,
        max(metric_value) filter (where metric_code = 'operating_cash_flow') as operating_cash_flow,
        max(metric_value) filter (where metric_code = 'capital_expenditure') as capital_expenditure,
        max(period_end) as latest_raw_period_end
    from latest_raw_metric_rows
    group by instrument_id
),
latest_normalized_rows as (
    select distinct on (normalized.instrument_id, normalized.metric_code)
        normalized.instrument_id,
        normalized.metric_code,
        normalized.metric_value,
        normalized.period_end
    from market.financial_metric_normalized normalized
    where normalized.as_of_date <= {sql_date(as_of_date)}
      and normalized.statement_scope = {sql_literal(statement_scope)}
      and normalized.metric_status = 'computed'
      and normalized.metric_code in (
        'revenue_growth_yoy',
        'operating_margin',
        'free_cash_flow_margin',
        'capex_intensity',
        'cash_flow_quality'
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
        max(metric_value) filter (where metric_code = 'revenue_growth_yoy') as revenue_growth_yoy,
        max(metric_value) filter (where metric_code = 'operating_margin') as operating_margin,
        max(metric_value) filter (where metric_code = 'free_cash_flow_margin') as free_cash_flow_margin,
        max(metric_value) filter (where metric_code = 'capex_intensity') as capex_intensity,
        max(metric_value) filter (where metric_code = 'cash_flow_quality') as cash_flow_quality,
        max(period_end) as latest_normalized_period_end
    from latest_normalized_rows
    group by instrument_id
),
forecast_context as (
    select
        raw.instrument_id,
        raw.latest_raw_period_end,
        normalized.latest_normalized_period_end,
        raw.revenue as base_revenue,
        raw.operating_cash_flow,
        raw.capital_expenditure,
        case
            when raw.operating_cash_flow is not null and raw.capital_expenditure is not null
            then raw.operating_cash_flow - abs(raw.capital_expenditure)
            else null::numeric
        end as latest_free_cash_flow,
        least(0.1800::numeric, greatest(-0.1000::numeric, coalesce(normalized.revenue_growth_yoy, 0.0300::numeric))) as base_revenue_growth_rate,
        least(0.6000::numeric, greatest(-0.2000::numeric, coalesce(normalized.operating_margin, 0.1000::numeric))) as base_operating_margin,
        least(
            0.5000::numeric,
            greatest(
                -0.2000::numeric,
                coalesce(
                    normalized.free_cash_flow_margin,
                    case
                        when raw.revenue is not null and raw.revenue <> 0
                        then (raw.operating_cash_flow - abs(raw.capital_expenditure)) / raw.revenue
                        else null::numeric
                    end,
                    0.0600::numeric
                )
            )
        ) as base_free_cash_flow_margin,
        least(
            0.3500::numeric,
            greatest(
                0::numeric,
                coalesce(
                    normalized.capex_intensity,
                    case
                        when raw.revenue is not null and raw.revenue <> 0
                        then abs(raw.capital_expenditure) / raw.revenue
                        else null::numeric
                    end,
                    0.0500::numeric
                )
            )
        ) as base_capex_intensity,
        (
            (normalized.revenue_growth_yoy is not null)::integer
            + (normalized.operating_margin is not null)::integer
            + (normalized.free_cash_flow_margin is not null)::integer
            + (normalized.capex_intensity is not null)::integer
            + (normalized.cash_flow_quality is not null)::integer
        ) as normalized_metric_count
    from raw_inputs raw
    left join normalized_inputs normalized on normalized.instrument_id = raw.instrument_id
    where raw.revenue is not null
      and raw.revenue > 0
),
scenario_adjustments as (
    select *
    from (
        values
            ('bear'::text, -0.0300::numeric, -0.0200::numeric, -0.0200::numeric, 0.0100::numeric, 0.8500::numeric),
            ('base'::text, 0.0000::numeric, 0.0000::numeric, 0.0000::numeric, 0.0000::numeric, 1.0000::numeric),
            ('bull'::text, 0.0300::numeric, 0.0200::numeric, 0.0200::numeric, -0.0050::numeric, 0.9000::numeric)
    ) as scenario(scenario_key, growth_adjustment, operating_margin_adjustment, fcf_margin_adjustment, capex_intensity_adjustment, confidence_multiplier)
),
forecast_years as (
    select generate_series(1, {FINANCIAL_FORECAST_YEARS})::integer as forecast_year
),
forecast_rows as (
    select
        context.instrument_id,
        {sql_date(as_of_date)} as as_of_date,
        {sql_literal(statement_scope)} as statement_scope,
        scenario.scenario_key,
        year.forecast_year,
        context.base_revenue,
        least(0.2500::numeric, greatest(-0.2000::numeric, context.base_revenue_growth_rate + scenario.growth_adjustment)) as revenue_growth_rate,
        least(0.6500::numeric, greatest(-0.2500::numeric, context.base_operating_margin + scenario.operating_margin_adjustment)) as operating_margin,
        least(0.5500::numeric, greatest(-0.2500::numeric, context.base_free_cash_flow_margin + scenario.fcf_margin_adjustment)) as free_cash_flow_margin,
        least(0.4000::numeric, greatest(0::numeric, context.base_capex_intensity + scenario.capex_intensity_adjustment)) as capex_intensity,
        context.latest_raw_period_end,
        context.latest_normalized_period_end,
        context.latest_free_cash_flow,
        context.normalized_metric_count,
        scenario.confidence_multiplier
    from forecast_context context
    cross join scenario_adjustments scenario
    cross join forecast_years year
),
computed_forecast_rows as (
    select
        row.instrument_id,
        row.as_of_date,
        row.statement_scope,
        row.scenario_key,
        row.forecast_year,
        (row.base_revenue * power(1 + row.revenue_growth_rate, row.forecast_year))::numeric as revenue,
        row.revenue_growth_rate,
        row.operating_margin,
        row.free_cash_flow_margin,
        row.capex_intensity,
        (row.base_revenue * power(1 + row.revenue_growth_rate, row.forecast_year) * row.free_cash_flow_margin)::numeric as free_cash_flow,
        json_build_object(
            'model_family', 'deterministic_financial_forecast_inputs',
            'scenario_key', row.scenario_key,
            'forecast_year', row.forecast_year,
            'forecast_years', {FINANCIAL_FORECAST_YEARS},
            'source_statement_scope', row.statement_scope,
            'latest_raw_period_end', row.latest_raw_period_end,
            'latest_normalized_period_end', row.latest_normalized_period_end,
            'base_revenue', row.base_revenue,
            'latest_free_cash_flow', row.latest_free_cash_flow,
            'normalized_metric_count', row.normalized_metric_count,
            'key_variables', json_build_array('revenue_growth_rate', 'operating_margin', 'free_cash_flow_margin', 'capex_intensity'),
            'limitations', json_build_array(
                '과거 재무제표와 정규화 지표로 만든 deterministic forecast input이며 경영진 가이던스나 상세 segment forecast를 대체하지 않는다.',
                '추천 점수와 주문을 직접 변경하지 않는 밸류에이션 입력 근거다.'
            ),
            'recommendation_scoring_mutated', false
        )::jsonb as assumptions_json,
        least(0.6500::numeric, greatest(0.2000::numeric, (0.2500::numeric + row.normalized_metric_count * 0.0500::numeric) * row.confidence_multiplier)) as confidence
    from forecast_rows row
),
upsert_forecasts as (
    insert into market.financial_forecast_input (
        instrument_id,
        as_of_date,
        statement_scope,
        scenario_key,
        forecast_year,
        revenue,
        revenue_growth_rate,
        operating_margin,
        free_cash_flow_margin,
        capex_intensity,
        free_cash_flow,
        assumptions_json,
        confidence,
        source_run_id
    )
    select
        instrument_id,
        as_of_date,
        statement_scope,
        scenario_key,
        forecast_year,
        revenue,
        revenue_growth_rate,
        operating_margin,
        free_cash_flow_margin,
        capex_intensity,
        free_cash_flow,
        assumptions_json,
        confidence,
        {int(source_run_id)}::bigint
    from computed_forecast_rows
    on conflict (instrument_id, as_of_date, statement_scope, scenario_key, forecast_year) do update
    set
        revenue = excluded.revenue,
        revenue_growth_rate = excluded.revenue_growth_rate,
        operating_margin = excluded.operating_margin,
        free_cash_flow_margin = excluded.free_cash_flow_margin,
        capex_intensity = excluded.capex_intensity,
        free_cash_flow = excluded.free_cash_flow,
        assumptions_json = excluded.assumptions_json,
        confidence = excluded.confidence,
        source_run_id = excluded.source_run_id
    returning scenario_key, forecast_year, confidence
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'source_run_id', {int(source_run_id)},
    'statement_scope', {sql_literal(statement_scope)},
    'forecast_row_count', (select count(*)::integer from upsert_forecasts),
    'scenario_counts',
        coalesce(
            (
                select json_object_agg(scenario_key, scenario_count order by scenario_key)
                from (
                    select scenario_key, count(*)::integer as scenario_count
                    from upsert_forecasts
                    group by scenario_key
                ) counts
            ),
            '{{}}'::json
        ),
    'max_forecast_year', (select max(forecast_year)::integer from upsert_forecasts),
    'confidence_summary',
        (
            select json_build_object(
                'min', min(confidence),
                'avg', avg(confidence),
                'max', max(confidence)
            )
            from upsert_forecasts
        )
)::text;"""


def load_financial_forecast_inputs_preview(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    statement_scope: str = "annual",
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_financial_forecast_inputs_preview_sql(as_of_date=as_of_date, statement_scope=statement_scope)
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Financial forecast inputs preview did not return a JSON object.")
    return payload


def run_financial_forecast_inputs(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    statement_scope: str = "annual",
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    preview = load_financial_forecast_inputs_preview(
        config=config,
        as_of_date=as_of_date,
        statement_scope=statement_scope,
        executor=sql_executor,
    )
    report: dict[str, object] = {
        "report_name": "financial_forecast_inputs",
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_FINANCIAL_FORECAST_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "statement_scope": statement_scope,
        "model_name": DEFAULT_FINANCIAL_FORECAST_MODEL_NAME,
        "scenario_keys": list(FINANCIAL_FORECAST_SCENARIOS),
        "forecast_years": FINANCIAL_FORECAST_YEARS,
        "preview": preview,
        "recommendation_scoring_mutated": False,
    }
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_FINANCIAL_FORECAST_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "statement_scope": statement_scope,
            "model_name": DEFAULT_FINANCIAL_FORECAST_MODEL_NAME,
            "scenario_keys": list(FINANCIAL_FORECAST_SCENARIOS),
            "forecast_years": FINANCIAL_FORECAST_YEARS,
            "recommendation_scoring_mutated": False,
        },
    )
    try:
        upsert_summary = json.loads(
            sql_executor.execute_scalar(
                render_financial_forecast_inputs_upsert_sql(
                    as_of_date=as_of_date,
                    source_run_id=run_id,
                    statement_scope=statement_scope,
                )
            )
        )
        if not isinstance(upsert_summary, dict):
            raise ValueError("Financial forecast inputs upsert did not return a JSON object.")
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


def render_valuation_snapshot_preview_sql(
    *,
    as_of_date: date,
    statement_scope: str = "annual",
) -> str:
    _validate_valuation_args(statement_scope=statement_scope)
    return f"""-- valuation snapshot preview
with latest_prices as (
    select distinct on (bar.instrument_id)
        bar.instrument_id,
        coalesce(bar.adjusted_close, bar.close) as base_price,
        bar.trade_date as price_date
    from market.daily_price_bar bar
    where bar.trade_date <= {sql_date(as_of_date)}
      and coalesce(bar.adjusted_close, bar.close) is not null
    order by bar.instrument_id, bar.trade_date desc
),
latest_raw_metric_rows as (
    select distinct on (period.instrument_id, metric.metric_code)
        period.instrument_id,
        metric.metric_code,
        metric.metric_value,
        period.period_end
    from market.financial_statement_period period
    join market.financial_metric_value metric on metric.period_id = period.period_id
    where period.period_end <= {sql_date(as_of_date)}
      and period.statement_scope = {sql_literal(statement_scope)}
      and metric.metric_code in (
        'operating_cash_flow',
        'capital_expenditure',
        'shares_outstanding',
        'revenue'
      )
    order by period.instrument_id, metric.metric_code, period.period_end desc
),
raw_inputs as (
    select
        instrument_id,
        max(metric_value) filter (where metric_code = 'operating_cash_flow') as operating_cash_flow,
        max(metric_value) filter (where metric_code = 'capital_expenditure') as capital_expenditure,
        max(metric_value) filter (where metric_code = 'shares_outstanding') as shares_outstanding,
        max(metric_value) filter (where metric_code = 'revenue') as revenue
    from latest_raw_metric_rows
    group by instrument_id
),
latest_normalized_rows as (
    select distinct on (normalized.instrument_id, normalized.metric_code)
        normalized.instrument_id,
        normalized.metric_code,
        normalized.metric_value
    from market.financial_metric_normalized normalized
    where normalized.as_of_date <= {sql_date(as_of_date)}
      and normalized.statement_scope = {sql_literal(statement_scope)}
      and normalized.metric_status = 'computed'
      and normalized.metric_code in (
        'revenue_growth_yoy',
        'net_margin',
        'free_cash_flow_margin',
        'cash_flow_quality',
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
        max(metric_value) filter (where metric_code = 'revenue_growth_yoy') as revenue_growth_yoy,
        max(metric_value) filter (where metric_code = 'net_margin') as net_margin,
        max(metric_value) filter (where metric_code = 'free_cash_flow_margin') as free_cash_flow_margin,
        max(metric_value) filter (where metric_code = 'cash_flow_quality') as cash_flow_quality,
        max(metric_value) filter (where metric_code = 'leverage_ratio') as leverage_ratio
    from latest_normalized_rows
    group by instrument_id
),
latest_peer_rows as (
    select distinct on (snapshot.instrument_id, snapshot.peer_group_id, snapshot.metric_code)
        snapshot.instrument_id,
        snapshot.metric_code,
        snapshot.percentile_rank
    from market.peer_relative_snapshot snapshot
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
        avg(percentile_rank) filter (
            where metric_code in (
                'revenue_growth_yoy',
                'net_margin',
                'free_cash_flow_margin',
                'cash_flow_quality'
            )
        ) as quality_percentile,
        avg(percentile_rank) filter (where metric_code = 'leverage_ratio') as leverage_percentile
    from latest_peer_rows
    group by instrument_id
),
latest_forecast_rows as (
    select distinct on (forecast.instrument_id, forecast.scenario_key, forecast.forecast_year)
        forecast.instrument_id,
        forecast.as_of_date,
        forecast.statement_scope,
        forecast.scenario_key,
        forecast.forecast_year,
        forecast.revenue,
        forecast.revenue_growth_rate,
        forecast.operating_margin,
        forecast.free_cash_flow_margin,
        forecast.capex_intensity,
        forecast.free_cash_flow,
        forecast.confidence,
        forecast.source_run_id
    from market.financial_forecast_input forecast
    where forecast.as_of_date <= {sql_date(as_of_date)}
      and forecast.statement_scope = {sql_literal(statement_scope)}
    order by
        forecast.instrument_id,
        forecast.scenario_key,
        forecast.forecast_year,
        forecast.as_of_date desc,
        forecast.forecast_input_id desc
),
forecast_inputs as (
    select
        instrument_id,
        count(*)::integer as forecast_row_count,
        max(as_of_date) as latest_forecast_as_of_date,
        avg(confidence) as forecast_confidence,
        avg(free_cash_flow) filter (where scenario_key = 'base') as base_forecast_free_cash_flow,
        avg(revenue_growth_rate) filter (where scenario_key = 'base') as base_forecast_revenue_growth_rate,
        avg(free_cash_flow_margin) filter (where scenario_key = 'base') as base_forecast_free_cash_flow_margin,
        jsonb_agg(
            jsonb_build_object(
                'scenario_key', scenario_key,
                'forecast_year', forecast_year,
                'revenue', revenue,
                'revenue_growth_rate', revenue_growth_rate,
                'operating_margin', operating_margin,
                'free_cash_flow_margin', free_cash_flow_margin,
                'capex_intensity', capex_intensity,
                'free_cash_flow', free_cash_flow,
                'confidence', confidence,
                'source_run_id', source_run_id
            )
            order by scenario_key, forecast_year
        ) as forecast_rows_json
    from latest_forecast_rows
    group by instrument_id
),
valuation_inputs as (
    select
        price.instrument_id,
        price.base_price,
        raw.operating_cash_flow,
        raw.capital_expenditure,
        raw.shares_outstanding,
        raw.revenue,
        normalized.revenue_growth_yoy,
        normalized.net_margin,
        normalized.free_cash_flow_margin,
        normalized.cash_flow_quality,
        normalized.leverage_ratio,
        peer.quality_percentile,
        peer.leverage_percentile,
        forecast.forecast_row_count
    from latest_prices price
    left join raw_inputs raw on raw.instrument_id = price.instrument_id
    left join normalized_inputs normalized on normalized.instrument_id = price.instrument_id
    left join peer_inputs peer on peer.instrument_id = price.instrument_id
    left join forecast_inputs forecast on forecast.instrument_id = price.instrument_id
    where raw.instrument_id is not null
       or normalized.instrument_id is not null
       or peer.instrument_id is not null
       or forecast.instrument_id is not null
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'model_name', {sql_literal(DEFAULT_VALUATION_MODEL_NAME)},
    'statement_scope', {sql_literal(statement_scope)},
    'methods', {sql_literal(json.dumps(VALUATION_METHODS))}::jsonb,
    'price_coverage_count', (select count(*)::integer from latest_prices),
    'raw_financial_input_count', (select count(*)::integer from raw_inputs),
    'normalized_input_count', (select count(*)::integer from normalized_inputs),
    'peer_context_count', (select count(*)::integer from peer_inputs),
    'financial_forecast_input_count', (select count(*)::integer from latest_forecast_rows),
    'valuation_context_count', (select count(*)::integer from valuation_inputs),
    'dcf_lite_eligible_count',
        (
            select count(*)::integer
            from valuation_inputs
            where base_price > 0
              and operating_cash_flow is not null
              and capital_expenditure is not null
              and shares_outstanding is not null
              and shares_outstanding > 0
              and (operating_cash_flow - abs(capital_expenditure)) > 0
        ),
    'existing_valuation_count',
        (
            select count(*)::integer
            from market.valuation_snapshot
            where as_of_date = {sql_date(as_of_date)}
        )
)::text;"""


def render_valuation_snapshot_upsert_sql(
    *,
    as_of_date: date,
    source_run_id: int,
    statement_scope: str = "annual",
) -> str:
    _validate_valuation_args(statement_scope=statement_scope)
    return f"""-- valuation snapshot upsert
with latest_prices as (
    select distinct on (bar.instrument_id)
        bar.instrument_id,
        instrument.primary_symbol,
        coalesce(bar.adjusted_close, bar.close) as base_price,
        bar.trade_date as price_date
    from market.daily_price_bar bar
    join ref.instrument instrument on instrument.instrument_id = bar.instrument_id
    where bar.trade_date <= {sql_date(as_of_date)}
      and coalesce(bar.adjusted_close, bar.close) is not null
    order by bar.instrument_id, bar.trade_date desc
),
latest_raw_metric_rows as (
    select distinct on (period.instrument_id, metric.metric_code)
        period.instrument_id,
        metric.metric_code,
        metric.metric_value,
        period.period_end
    from market.financial_statement_period period
    join market.financial_metric_value metric on metric.period_id = period.period_id
    where period.period_end <= {sql_date(as_of_date)}
      and period.statement_scope = {sql_literal(statement_scope)}
      and metric.metric_code in (
        'operating_cash_flow',
        'capital_expenditure',
        'shares_outstanding',
        'revenue'
      )
    order by period.instrument_id, metric.metric_code, period.period_end desc
),
raw_inputs as (
    select
        instrument_id,
        max(metric_value) filter (where metric_code = 'operating_cash_flow') as operating_cash_flow,
        max(metric_value) filter (where metric_code = 'capital_expenditure') as capital_expenditure,
        max(metric_value) filter (where metric_code = 'shares_outstanding') as shares_outstanding,
        max(metric_value) filter (where metric_code = 'revenue') as revenue,
        max(period_end) as latest_raw_period_end
    from latest_raw_metric_rows
    group by instrument_id
),
latest_normalized_rows as (
    select distinct on (normalized.instrument_id, normalized.metric_code)
        normalized.instrument_id,
        normalized.metric_code,
        normalized.metric_value,
        normalized.period_end
    from market.financial_metric_normalized normalized
    where normalized.as_of_date <= {sql_date(as_of_date)}
      and normalized.statement_scope = {sql_literal(statement_scope)}
      and normalized.metric_status = 'computed'
      and normalized.metric_code in (
        'revenue_growth_yoy',
        'net_margin',
        'free_cash_flow_margin',
        'cash_flow_quality',
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
        max(metric_value) filter (where metric_code = 'revenue_growth_yoy') as revenue_growth_yoy,
        max(metric_value) filter (where metric_code = 'net_margin') as net_margin,
        max(metric_value) filter (where metric_code = 'free_cash_flow_margin') as free_cash_flow_margin,
        max(metric_value) filter (where metric_code = 'cash_flow_quality') as cash_flow_quality,
        max(metric_value) filter (where metric_code = 'leverage_ratio') as leverage_ratio,
        max(period_end) as latest_normalized_period_end
    from latest_normalized_rows
    group by instrument_id
),
latest_peer_rows as (
    select distinct on (snapshot.instrument_id, snapshot.peer_group_id, snapshot.metric_code)
        snapshot.instrument_id,
        snapshot.metric_code,
        snapshot.percentile_rank
    from market.peer_relative_snapshot snapshot
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
        avg(percentile_rank) filter (
            where metric_code in (
                'revenue_growth_yoy',
                'net_margin',
                'free_cash_flow_margin',
                'cash_flow_quality'
            )
        ) as quality_percentile,
        avg(percentile_rank) filter (where metric_code = 'leverage_ratio') as leverage_percentile
    from latest_peer_rows
    group by instrument_id
),
latest_forecast_rows as (
    select distinct on (forecast.instrument_id, forecast.scenario_key, forecast.forecast_year)
        forecast.instrument_id,
        forecast.as_of_date,
        forecast.statement_scope,
        forecast.scenario_key,
        forecast.forecast_year,
        forecast.revenue,
        forecast.revenue_growth_rate,
        forecast.operating_margin,
        forecast.free_cash_flow_margin,
        forecast.capex_intensity,
        forecast.free_cash_flow,
        forecast.confidence,
        forecast.source_run_id
    from market.financial_forecast_input forecast
    where forecast.as_of_date <= {sql_date(as_of_date)}
      and forecast.statement_scope = {sql_literal(statement_scope)}
    order by
        forecast.instrument_id,
        forecast.scenario_key,
        forecast.forecast_year,
        forecast.as_of_date desc,
        forecast.forecast_input_id desc
),
forecast_inputs as (
    select
        instrument_id,
        count(*)::integer as forecast_row_count,
        max(as_of_date) as latest_forecast_as_of_date,
        avg(confidence) as forecast_confidence,
        avg(free_cash_flow) filter (where scenario_key = 'base') as base_forecast_free_cash_flow,
        avg(revenue_growth_rate) filter (where scenario_key = 'base') as base_forecast_revenue_growth_rate,
        avg(free_cash_flow_margin) filter (where scenario_key = 'base') as base_forecast_free_cash_flow_margin,
        jsonb_agg(
            jsonb_build_object(
                'scenario_key', scenario_key,
                'forecast_year', forecast_year,
                'revenue', revenue,
                'revenue_growth_rate', revenue_growth_rate,
                'operating_margin', operating_margin,
                'free_cash_flow_margin', free_cash_flow_margin,
                'capex_intensity', capex_intensity,
                'free_cash_flow', free_cash_flow,
                'confidence', confidence,
                'source_run_id', source_run_id
            )
            order by scenario_key, forecast_year
        ) as forecast_rows_json
    from latest_forecast_rows
    group by instrument_id
),
valuation_inputs as (
    select
        price.instrument_id,
        price.primary_symbol,
        price.base_price,
        price.price_date,
        raw.latest_raw_period_end,
        normalized.latest_normalized_period_end,
        raw.operating_cash_flow,
        raw.capital_expenditure,
        raw.shares_outstanding,
        raw.revenue,
        case
            when raw.operating_cash_flow is not null and raw.capital_expenditure is not null
            then raw.operating_cash_flow - abs(raw.capital_expenditure)
            else null::numeric
        end as free_cash_flow,
        normalized.revenue_growth_yoy,
        normalized.net_margin,
        normalized.free_cash_flow_margin,
        normalized.cash_flow_quality,
        normalized.leverage_ratio,
        peer.quality_percentile,
        peer.leverage_percentile,
        forecast.latest_forecast_as_of_date,
        forecast.forecast_row_count,
        forecast.forecast_confidence,
        forecast.base_forecast_free_cash_flow,
        forecast.base_forecast_revenue_growth_rate,
        forecast.base_forecast_free_cash_flow_margin,
        forecast.forecast_rows_json,
        least(
            1::numeric,
            greatest(
                0::numeric,
                (
                    coalesce(peer.quality_percentile, 0.5000)
                    + coalesce(1::numeric - peer.leverage_percentile, 0.5000)
                ) / 2
            )
        ) as quality_score,
        least(0.1200::numeric, greatest(-0.0500::numeric, coalesce(normalized.revenue_growth_yoy, 0.0300))) as growth_rate,
        (
            (normalized.revenue_growth_yoy is not null)::integer
            + (normalized.net_margin is not null)::integer
            + (normalized.free_cash_flow_margin is not null)::integer
            + (normalized.cash_flow_quality is not null)::integer
            + (normalized.leverage_ratio is not null)::integer
        ) as normalized_metric_count
    from latest_prices price
    left join raw_inputs raw on raw.instrument_id = price.instrument_id
    left join normalized_inputs normalized on normalized.instrument_id = price.instrument_id
    left join peer_inputs peer on peer.instrument_id = price.instrument_id
    left join forecast_inputs forecast on forecast.instrument_id = price.instrument_id
    where price.base_price > 0
      and (
        raw.instrument_id is not null
        or normalized.instrument_id is not null
        or peer.instrument_id is not null
        or forecast.instrument_id is not null
      )
),
relative_multiple_rows as (
    select
        input.instrument_id,
        'relative_multiple' as method,
        input.base_price,
        (
            input.base_price
            * (1::numeric + ((input.quality_score - 0.5000::numeric) * 0.3000::numeric))
            * 0.8500::numeric
        ) as fair_value_low,
        (
            input.base_price
            * (1::numeric + ((input.quality_score - 0.5000::numeric) * 0.3000::numeric))
        ) as fair_value_base,
        (
            input.base_price
            * (1::numeric + ((input.quality_score - 0.5000::numeric) * 0.3000::numeric))
            * 1.1500::numeric
        ) as fair_value_high,
        json_build_object(
            'model_family', 'relative_valuation',
            'method_description', 'Peer percentile adjusted current-price range. This is not an absolute intrinsic value model.',
            'pricing_basis', 'latest adjusted close',
            'sensitivity_basis', 'quality_score +/- 15% price band',
            'statement_scope', {sql_literal(statement_scope)},
            'price_date', input.price_date,
            'latest_raw_period_end', input.latest_raw_period_end,
            'quality_score', round(input.quality_score, 4),
            'peer_quality_percentile', input.quality_percentile,
            'leverage_percentile', input.leverage_percentile,
            'key_variables', json_build_array('quality_score', 'peer_quality_percentile', 'leverage_percentile'),
            'data_quality', json_build_object(
                'peer_quality_percentile_present', input.quality_percentile is not null,
                'leverage_percentile_present', input.leverage_percentile is not null
            ),
            'limitations', json_build_array(
                '현재가를 피어 품질 점수로 조정한 상대가치 범위이며 독립적인 내재가치 산정은 아니다.',
                '피어 그룹 품질과 레버리지 백분위가 부정확하면 목표가 범위도 흔들린다.'
            ),
            'recommendation_scoring_mutated', false
        )::jsonb as assumptions_json,
        case
            when input.quality_percentile is not null then 0.4500::numeric
            else 0.2500::numeric
        end as confidence
    from valuation_inputs input
),
scenario_range_rows as (
    select
        input.instrument_id,
        'scenario_range' as method,
        input.base_price,
        input.base_price * (0.7500::numeric + input.quality_score * 0.1000::numeric) as fair_value_low,
        input.base_price * (0.9000::numeric + input.quality_score * 0.2000::numeric) as fair_value_base,
        input.base_price * (1.0500::numeric + input.quality_score * 0.2500::numeric) as fair_value_high,
        json_build_object(
            'model_family', 'scenario_range',
            'method_description', 'Conservative bear/base/bull range anchored to current price and financial-quality context.',
            'pricing_basis', 'latest adjusted close',
            'sensitivity_basis', 'bear/base/bull band from current price and quality_score',
            'statement_scope', {sql_literal(statement_scope)},
            'price_date', input.price_date,
            'latest_normalized_period_end', input.latest_normalized_period_end,
            'quality_score', round(input.quality_score, 4),
            'normalized_metric_count', input.normalized_metric_count,
            'forecast_input_source', case when coalesce(input.forecast_row_count, 0) > 0 then 'market.financial_forecast_input' else null end,
            'latest_forecast_as_of_date', input.latest_forecast_as_of_date,
            'forecast_row_count', coalesce(input.forecast_row_count, 0),
            'forecast_confidence', input.forecast_confidence,
            'forecast_scenarios', coalesce(input.forecast_rows_json, '[]'::jsonb),
            'key_variables', json_build_array('quality_score', 'normalized_metric_count', 'base_price'),
            'data_quality', json_build_object(
                'normalized_metric_count', input.normalized_metric_count,
                'latest_normalized_period_end', input.latest_normalized_period_end,
                'forecast_row_count', coalesce(input.forecast_row_count, 0)
            ),
            'limitations', json_build_array(
                '보수·기준·낙관 case를 가격 앵커와 품질 점수로 만든 단순 범위다.',
                '실적 forecast나 확률가중 기대값을 직접 계산한 모델은 아니다.'
            ),
            'recommendation_scoring_mutated', false
        )::jsonb as assumptions_json,
        case
            when input.normalized_metric_count >= 3 then 0.4000::numeric
            else 0.2000::numeric
        end as confidence
    from valuation_inputs input
),
dcf_inputs as (
    select
        input.*,
        (coalesce(input.base_forecast_free_cash_flow, input.free_cash_flow) / input.shares_outstanding) as fcf_per_share,
        least(0.1200::numeric, greatest(-0.0500::numeric, coalesce(input.base_forecast_revenue_growth_rate, input.growth_rate))) as dcf_growth_rate,
        0.1000::numeric as discount_rate,
        0.0250::numeric as terminal_growth_rate
    from valuation_inputs input
    where coalesce(input.base_forecast_free_cash_flow, input.free_cash_flow) is not null
      and coalesce(input.base_forecast_free_cash_flow, input.free_cash_flow) > 0
      and input.shares_outstanding is not null
      and input.shares_outstanding > 0
),
dcf_lite_rows as (
    select
        input.instrument_id,
        'dcf_lite' as method,
        input.base_price,
        intrinsic.fair_value_base * 0.8500::numeric as fair_value_low,
        intrinsic.fair_value_base,
        intrinsic.fair_value_base * 1.1500::numeric as fair_value_high,
        json_build_object(
            'model_family', 'intrinsic_dcf_lite',
            'method_description', 'Five-year free-cash-flow-per-share DCF-lite with fixed discount and terminal growth assumptions.',
            'pricing_basis', 'latest adjusted close',
            'forecast_years', 5,
            'sensitivity_basis', 'growth_rate, discount_rate, terminal_growth_rate',
            'statement_scope', {sql_literal(statement_scope)},
            'price_date', input.price_date,
            'latest_raw_period_end', input.latest_raw_period_end,
            'free_cash_flow', input.free_cash_flow,
            'forecast_input_source', case when coalesce(input.forecast_row_count, 0) > 0 then 'market.financial_forecast_input' else null end,
            'latest_forecast_as_of_date', input.latest_forecast_as_of_date,
            'forecast_row_count', coalesce(input.forecast_row_count, 0),
            'forecast_confidence', input.forecast_confidence,
            'forecast_base_free_cash_flow', input.base_forecast_free_cash_flow,
            'forecast_base_free_cash_flow_margin', input.base_forecast_free_cash_flow_margin,
            'forecast_scenarios', coalesce(input.forecast_rows_json, '[]'::jsonb),
            'shares_outstanding', input.shares_outstanding,
            'fcf_per_share', round(input.fcf_per_share, 6),
            'growth_rate', input.dcf_growth_rate,
            'discount_rate', input.discount_rate,
            'terminal_growth_rate', input.terminal_growth_rate,
            'key_variables', json_build_array('fcf_per_share', 'growth_rate', 'discount_rate', 'terminal_growth_rate', 'forecast_scenarios'),
            'data_quality', json_build_object(
                'free_cash_flow_present', input.free_cash_flow is not null,
                'forecast_row_count', coalesce(input.forecast_row_count, 0),
                'shares_outstanding_present', input.shares_outstanding is not null,
                'normalized_metric_count', input.normalized_metric_count
            ),
            'limitations', json_build_array(
                '5년 FCF/share를 단순 할인한 모델이며 상세 매출·마진·CAPEX forecast를 대체하지 않는다.',
                '할인율과 영구성장률은 고정 가정이므로 금리·위험 프리미엄 변화에 민감하다.'
            ),
            'recommendation_scoring_mutated', false
        )::jsonb as assumptions_json,
        case
            when input.normalized_metric_count >= 3 then 0.3500::numeric
            else 0.2500::numeric
        end as confidence
    from dcf_inputs input
    cross join lateral (
        select (
            (input.fcf_per_share * power(1 + input.dcf_growth_rate, 1) / power(1 + input.discount_rate, 1))
            + (input.fcf_per_share * power(1 + input.dcf_growth_rate, 2) / power(1 + input.discount_rate, 2))
            + (input.fcf_per_share * power(1 + input.dcf_growth_rate, 3) / power(1 + input.discount_rate, 3))
            + (input.fcf_per_share * power(1 + input.dcf_growth_rate, 4) / power(1 + input.discount_rate, 4))
            + (input.fcf_per_share * power(1 + input.dcf_growth_rate, 5) / power(1 + input.discount_rate, 5))
            + (
                input.fcf_per_share
                * power(1 + input.dcf_growth_rate, 5)
                * (1 + input.terminal_growth_rate)
                / (input.discount_rate - input.terminal_growth_rate)
                / power(1 + input.discount_rate, 5)
            )
        )::numeric as fair_value_base
    ) intrinsic
),
snapshot_rows as (
    select * from relative_multiple_rows
    union all
    select * from scenario_range_rows
    union all
    select * from dcf_lite_rows
),
upsert_snapshots as (
    insert into market.valuation_snapshot (
        instrument_id,
        as_of_date,
        method,
        base_price,
        fair_value_low,
        fair_value_base,
        fair_value_high,
        margin_of_safety,
        assumptions_json,
        confidence,
        source_run_id
    )
    select
        instrument_id,
        {sql_date(as_of_date)},
        method,
        base_price,
        fair_value_low,
        fair_value_base,
        fair_value_high,
        case
            when base_price is not null and base_price <> 0 and fair_value_base is not null
            then ((fair_value_base - base_price) / base_price)::numeric
            else null::numeric
        end,
        assumptions_json,
        confidence,
        {int(source_run_id)}::bigint
    from snapshot_rows
    on conflict (instrument_id, as_of_date, method) do update
    set
        base_price = excluded.base_price,
        fair_value_low = excluded.fair_value_low,
        fair_value_base = excluded.fair_value_base,
        fair_value_high = excluded.fair_value_high,
        margin_of_safety = excluded.margin_of_safety,
        assumptions_json = excluded.assumptions_json,
        confidence = excluded.confidence,
        source_run_id = excluded.source_run_id
    returning method, confidence
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'source_run_id', {int(source_run_id)},
    'statement_scope', {sql_literal(statement_scope)},
    'snapshot_count', (select count(*)::integer from upsert_snapshots),
    'method_counts',
        coalesce(
            (
                select json_object_agg(method, method_count order by method)
                from (
                    select method, count(*)::integer as method_count
                    from upsert_snapshots
                    group by method
                ) counts
            ),
            '{{}}'::json
        ),
    'confidence_summary',
        (
            select json_build_object(
                'min', min(confidence),
                'avg', avg(confidence),
                'max', max(confidence)
            )
            from upsert_snapshots
        )
)::text;"""


def load_valuation_snapshot_preview(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    statement_scope: str = "annual",
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_valuation_snapshot_preview_sql(as_of_date=as_of_date, statement_scope=statement_scope)
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Valuation snapshot preview did not return a JSON object.")
    return payload


def run_valuation_snapshot(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    statement_scope: str = "annual",
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    preview = load_valuation_snapshot_preview(
        config=config,
        as_of_date=as_of_date,
        statement_scope=statement_scope,
        executor=sql_executor,
    )
    report: dict[str, object] = {
        "report_name": "valuation_snapshot",
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_VALUATION_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "statement_scope": statement_scope,
        "model_name": DEFAULT_VALUATION_MODEL_NAME,
        "methods": list(VALUATION_METHODS),
        "preview": preview,
        "recommendation_scoring_mutated": False,
    }
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_VALUATION_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "statement_scope": statement_scope,
            "model_name": DEFAULT_VALUATION_MODEL_NAME,
            "methods": list(VALUATION_METHODS),
            "recommendation_scoring_mutated": False,
        },
    )
    try:
        upsert_summary = json.loads(
            sql_executor.execute_scalar(
                render_valuation_snapshot_upsert_sql(
                    as_of_date=as_of_date,
                    source_run_id=run_id,
                    statement_scope=statement_scope,
                )
            )
        )
        if not isinstance(upsert_summary, dict):
            raise ValueError("Valuation snapshot upsert did not return a JSON object.")
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


def _validate_valuation_args(*, statement_scope: str) -> None:
    if statement_scope not in VALUATION_STATEMENT_SCOPES:
        raise ValueError(f"statement_scope must be one of: {', '.join(VALUATION_STATEMENT_SCOPES)}.")


def _statement_scope_filter(alias: str, *, statement_scope: str) -> str:
    if statement_scope == "all":
        return ""
    return f"\n      and {alias}.statement_scope = {sql_literal(statement_scope)}"
