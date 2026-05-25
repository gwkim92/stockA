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
