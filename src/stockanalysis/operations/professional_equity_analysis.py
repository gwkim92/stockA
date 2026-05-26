from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import unquote, urlparse

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
DEFAULT_REPORTED_SEGMENT_PIPELINE_NAME = "reported_segment_footnote_parser"
DEFAULT_REPORTED_SEGMENT_MODEL_NAME = "deterministic-reported-segment-footnote-html-v1"
DEFAULT_SEGMENT_FOOTNOTE_PIPELINE_NAME = "segment_footnote_evidence"
DEFAULT_SEGMENT_FOOTNOTE_MODEL_NAME = "deterministic-segment-footnote-evidence-sql-v1"
DEFAULT_SOTP_PIPELINE_NAME = "sum_of_parts_valuation"
DEFAULT_SOTP_MODEL_NAME = "deterministic-sum-of-parts-sql-v1"
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
VALUATION_METHODS = ("dcf_lite", "relative_multiple", "scenario_range", "sum_of_parts")
FINANCIAL_FORECAST_SCENARIOS = ("bear", "base", "bull")
FINANCIAL_FORECAST_YEARS = 5
SEGMENT_FOOTNOTE_EVIDENCE_TYPES = (
    "filing_anchor",
    "consolidated_metric",
    "reported_segment_metric",
    "segment_data_gap",
)
REPORTED_SEGMENT_METRIC_CODES = (
    "segment_revenue",
    "segment_operating_income",
    "segment_gross_profit",
    "segment_assets",
    "segment_capex",
)
SOTP_COMPONENT_TYPES = ("operating_business", "balance_sheet_adjustment", "risk_reserve")


@dataclass(frozen=True)
class ReportedSegmentMetricEvidence:
    instrument_id: int
    primary_symbol: str
    as_of_date: date
    statement_scope: str
    segment_key: str
    segment_label: str
    metric_code: str
    metric_value: Decimal
    metric_unit: str
    period_end: date
    source_document_id: int
    evidence_text: str
    assumptions_json: dict[str, object]
    confidence: Decimal


@dataclass(frozen=True)
class HtmlTableContext:
    table_html: str
    context_text: str


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


def render_reported_segment_footnote_candidates_sql(
    *,
    as_of_date: date,
    statement_scope: str = "annual",
    limit: int | None = None,
    periods_per_instrument: int = 1,
) -> str:
    _validate_valuation_args(statement_scope=statement_scope)
    if limit is not None and limit <= 0:
        raise ValueError("limit must be greater than 0.")
    _validate_positive_int(periods_per_instrument, field_name="periods_per_instrument")
    limit_clause = "" if limit is None else f"\n    limit {int(limit)}"
    return f"""-- reported segment footnote candidates
with ranked_periods as (
    select
        period.period_id,
        period.instrument_id,
        instrument.primary_symbol,
        period.period_end,
        period.source_document_id,
        document.title as source_document_title,
        document.raw_storage_uri,
        document.url as source_document_url,
        case
            when exists (
                select 1
                from market.financial_metric_value metric
                where metric.period_id = period.period_id
                  and metric.metric_code in ('revenue', 'operating_income', 'net_income')
            )
            then 0
            else 1
        end as statement_metric_priority,
        row_number() over (
            partition by period.instrument_id
            order by
                case
                    when exists (
                        select 1
                        from market.financial_metric_value metric
                        where metric.period_id = period.period_id
                          and metric.metric_code in ('revenue', 'operating_income', 'net_income')
                    )
                    then 0
                    else 1
                end,
                period.period_end desc,
                period.period_id desc
        ) as period_rank
    from market.financial_statement_period period
    join ref.instrument instrument on instrument.instrument_id = period.instrument_id
    join ingest.source_document document on document.document_id = period.source_document_id
    where period.period_end <= {sql_date(as_of_date)}
      and period.statement_scope = {sql_literal(statement_scope)}
      and document.raw_storage_uri is not null
),
candidate_rows as (
    select *
    from ranked_periods
    where period_rank <= {int(periods_per_instrument)}
    order by primary_symbol, period_end desc, source_document_id desc{limit_clause}
)
select coalesce(
    json_agg(
        json_build_object(
            'instrument_id', instrument_id,
            'primary_symbol', primary_symbol,
            'period_end', period_end,
            'source_document_id', source_document_id,
            'source_document_title', source_document_title,
            'raw_storage_uri', raw_storage_uri,
            'source_document_url', source_document_url
        )
        order by primary_symbol, period_end desc, source_document_id desc
    ),
    '[]'::json
)::text
from candidate_rows;"""


def render_reported_segment_footnote_metric_upsert_sql(
    evidence_rows: list[ReportedSegmentMetricEvidence],
    *,
    as_of_date: date,
    source_run_id: int,
    statement_scope: str = "annual",
) -> str:
    _validate_valuation_args(statement_scope=statement_scope)
    if not evidence_rows:
        return f"""-- reported segment footnote metric upsert
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'source_run_id', {int(source_run_id)},
    'statement_scope', {sql_literal(statement_scope)},
    'reported_segment_metric_count', 0,
    'parsed_instrument_count', 0,
    'removed_gap_count', 0,
    'metric_code_counts', '{{}}'::json,
    'recommendation_scoring_mutated', false
)::text;"""

    value_rows = ",\n        ".join(_render_reported_segment_metric_value_tuple(row) for row in evidence_rows)
    return f"""-- reported segment footnote metric upsert
with input_rows(
    instrument_id,
    as_of_date,
    statement_scope,
    segment_key,
    segment_label,
    evidence_type,
    metric_code,
    metric_value,
    metric_unit,
    period_end,
    source_document_id,
    evidence_text,
    assumptions_json,
    confidence
) as (
    values
        {value_rows}
),
removed_stale_reported_metrics as (
    delete from research.segment_footnote_evidence stale
    where stale.as_of_date = {sql_date(as_of_date)}
      and stale.statement_scope = {sql_literal(statement_scope)}
      and stale.evidence_type = 'reported_segment_metric'
      and exists (
          select 1
          from input_rows input
          where input.instrument_id = stale.instrument_id
            and input.source_document_id = stale.source_document_id
      )
      and not exists (
          select 1
          from input_rows input
          where input.instrument_id = stale.instrument_id
            and input.source_document_id = stale.source_document_id
            and input.segment_key = stale.segment_key
            and input.metric_code = stale.metric_code
            and input.period_end = stale.period_end
      )
    returning stale.evidence_id
),
upsert_evidence as (
    insert into research.segment_footnote_evidence (
        instrument_id,
        as_of_date,
        statement_scope,
        segment_key,
        segment_label,
        evidence_type,
        metric_code,
        metric_value,
        metric_unit,
        period_end,
        source_document_id,
        evidence_text,
        assumptions_json,
        confidence,
        source_run_id
    )
    select
        instrument_id,
        as_of_date,
        statement_scope,
        segment_key,
        segment_label,
        evidence_type,
        metric_code,
        metric_value,
        metric_unit,
        period_end,
        source_document_id,
        evidence_text,
        assumptions_json,
        confidence,
        {int(source_run_id)}::bigint
    from input_rows
    on conflict (
        instrument_id,
        as_of_date,
        statement_scope,
        segment_key,
        evidence_type,
        metric_code,
        period_end
    ) do update
    set
        segment_label = excluded.segment_label,
        metric_value = excluded.metric_value,
        metric_unit = excluded.metric_unit,
        source_document_id = excluded.source_document_id,
        evidence_text = excluded.evidence_text,
        assumptions_json = excluded.assumptions_json,
        confidence = excluded.confidence,
        source_run_id = excluded.source_run_id
    returning instrument_id, metric_code
),
removed_gaps as (
    delete from research.segment_footnote_evidence gap
    where gap.as_of_date = {sql_date(as_of_date)}
      and gap.statement_scope = {sql_literal(statement_scope)}
      and gap.evidence_type = 'segment_data_gap'
      and exists (
          select 1
          from input_rows input
          where input.instrument_id = gap.instrument_id
            and input.period_end = gap.period_end
      )
    returning gap.evidence_id
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'source_run_id', {int(source_run_id)},
    'statement_scope', {sql_literal(statement_scope)},
    'reported_segment_metric_count', (select count(*)::integer from upsert_evidence),
    'parsed_instrument_count', (select count(distinct instrument_id)::integer from upsert_evidence),
    'removed_stale_metric_count', (select count(*)::integer from removed_stale_reported_metrics),
    'removed_gap_count', (select count(*)::integer from removed_gaps),
    'metric_code_counts',
        coalesce(
            (
                select json_object_agg(metric_code, metric_count order by metric_code)
                from (
                    select metric_code, count(*)::integer as metric_count
                    from upsert_evidence
                    group by metric_code
                ) counts
            ),
            '{{}}'::json
        ),
    'recommendation_scoring_mutated', false
)::text;"""


def load_reported_segment_footnote_candidates(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    statement_scope: str = "annual",
    limit: int | None = None,
    periods_per_instrument: int = 1,
    executor: PsqlCommandExecutor | None = None,
) -> list[dict[str, object]]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_reported_segment_footnote_candidates_sql(
                as_of_date=as_of_date,
                statement_scope=statement_scope,
                limit=limit,
                periods_per_instrument=periods_per_instrument,
            )
        )
    )
    if not isinstance(payload, list):
        raise ValueError("Reported segment footnote candidates query did not return a JSON array.")
    return [item for item in payload if isinstance(item, dict)]


def run_reported_segment_footnote_parser(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    statement_scope: str = "annual",
    limit: int | None = None,
    periods_per_instrument: int = 1,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    _validate_positive_int(periods_per_instrument, field_name="periods_per_instrument")
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    candidates = load_reported_segment_footnote_candidates(
        config=config,
        as_of_date=as_of_date,
        statement_scope=statement_scope,
        limit=limit,
        periods_per_instrument=periods_per_instrument,
        executor=sql_executor,
    )
    parsed_rows: list[ReportedSegmentMetricEvidence] = []
    skipped_candidates: list[dict[str, object]] = []
    for candidate in candidates:
        rows, skipped_reason = _parse_reported_segment_candidate(
            candidate,
            as_of_date=as_of_date,
            statement_scope=statement_scope,
        )
        parsed_rows.extend(rows)
        if skipped_reason is not None:
            skipped_candidates.append(
                {
                    "instrument_id": candidate.get("instrument_id"),
                    "primary_symbol": candidate.get("primary_symbol"),
                    "source_document_id": candidate.get("source_document_id"),
                    "reason": skipped_reason,
                }
            )

    preview = {
        "as_of_date": as_of_date.isoformat(),
        "statement_scope": statement_scope,
        "candidate_count": len(candidates),
        "periods_per_instrument": periods_per_instrument,
        "parsed_metric_count": len(parsed_rows),
        "parsed_instrument_count": len({row.instrument_id for row in parsed_rows}),
        "skipped_candidate_count": len(skipped_candidates),
        "metric_code_counts": _count_by_metric_code(parsed_rows),
        "skipped_candidates": skipped_candidates[:20],
    }
    report: dict[str, object] = {
        "report_name": "reported_segment_footnote_parser",
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_REPORTED_SEGMENT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "statement_scope": statement_scope,
        "limit": limit,
        "periods_per_instrument": periods_per_instrument,
        "model_name": DEFAULT_REPORTED_SEGMENT_MODEL_NAME,
        "supported_metric_codes": list(REPORTED_SEGMENT_METRIC_CODES),
        "preview": preview,
        "recommendation_scoring_mutated": False,
    }
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_REPORTED_SEGMENT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "statement_scope": statement_scope,
            "limit": limit,
            "periods_per_instrument": periods_per_instrument,
            "model_name": DEFAULT_REPORTED_SEGMENT_MODEL_NAME,
            "supported_metric_codes": list(REPORTED_SEGMENT_METRIC_CODES),
            "recommendation_scoring_mutated": False,
        },
    )
    try:
        upsert_summary = json.loads(
            sql_executor.execute_scalar(
                render_reported_segment_footnote_metric_upsert_sql(
                    parsed_rows,
                    as_of_date=as_of_date,
                    source_run_id=run_id,
                    statement_scope=statement_scope,
                )
            )
        )
        if not isinstance(upsert_summary, dict):
            raise ValueError("Reported segment footnote parser upsert did not return a JSON object.")
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


def render_segment_footnote_evidence_preview_sql(
    *,
    as_of_date: date,
    statement_scope: str = "annual",
) -> str:
    _validate_valuation_args(statement_scope=statement_scope)
    return f"""-- segment footnote evidence preview
with latest_periods as (
    select distinct on (period.instrument_id)
        period.period_id,
        period.instrument_id,
        period.period_end,
        period.source_document_id
    from market.financial_statement_period period
    where period.period_end <= {sql_date(as_of_date)}
      and period.statement_scope = {sql_literal(statement_scope)}
    order by period.instrument_id, period.period_end desc, period.period_id desc
),
latest_metric_rows as (
    select
        period.instrument_id,
        metric.metric_code
    from latest_periods period
    join market.financial_metric_value metric on metric.period_id = period.period_id
    where metric.metric_code in ('revenue', 'gross_profit', 'operating_income')
),
reported_segment_presence as (
    select distinct evidence.instrument_id
    from research.segment_footnote_evidence evidence
    where evidence.as_of_date <= {sql_date(as_of_date)}
      and evidence.statement_scope = {sql_literal(statement_scope)}
      and evidence.evidence_type = 'reported_segment_metric'
),
existing_evidence as (
    select *
    from research.segment_footnote_evidence evidence
    where evidence.as_of_date = {sql_date(as_of_date)}
      and evidence.statement_scope = {sql_literal(statement_scope)}
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'model_name', {sql_literal(DEFAULT_SEGMENT_FOOTNOTE_MODEL_NAME)},
    'statement_scope', {sql_literal(statement_scope)},
    'evidence_types', {sql_literal(json.dumps(SEGMENT_FOOTNOTE_EVIDENCE_TYPES))}::jsonb,
    'source_period_count', (select count(*)::integer from latest_periods),
    'source_document_count', (select count(distinct source_document_id)::integer from latest_periods where source_document_id is not null),
    'consolidated_metric_count', (select count(*)::integer from latest_metric_rows),
    'reported_segment_instrument_count', (select count(*)::integer from reported_segment_presence),
    'segment_data_gap_candidate_count',
        (
            select count(*)::integer
            from latest_periods period
            where not exists (
                select 1
                from reported_segment_presence presence
                where presence.instrument_id = period.instrument_id
            )
        ),
    'existing_evidence_count', (select count(*)::integer from existing_evidence)
)::text;"""


def render_segment_footnote_evidence_upsert_sql(
    *,
    as_of_date: date,
    source_run_id: int,
    statement_scope: str = "annual",
) -> str:
    _validate_valuation_args(statement_scope=statement_scope)
    return f"""-- segment footnote evidence upsert
with latest_periods as (
    select distinct on (period.instrument_id)
        period.period_id,
        period.instrument_id,
        instrument.primary_symbol,
        period.statement_scope,
        period.period_end,
        period.source_document_id,
        document.title as source_document_title,
        document.summary as source_document_summary,
        document.url as source_document_url
    from market.financial_statement_period period
    join ref.instrument instrument on instrument.instrument_id = period.instrument_id
    left join ingest.source_document document on document.document_id = period.source_document_id
    where period.period_end <= {sql_date(as_of_date)}
      and period.statement_scope = {sql_literal(statement_scope)}
    order by period.instrument_id, period.period_end desc, period.period_id desc
),
latest_metric_rows as (
    select
        period.instrument_id,
        period.primary_symbol,
        period.period_end,
        period.source_document_id,
        period.source_document_title,
        period.source_document_summary,
        period.source_document_url,
        metric.metric_code,
        metric.metric_value,
        metric.unit
    from latest_periods period
    join market.financial_metric_value metric on metric.period_id = period.period_id
    where metric.metric_code in ('revenue', 'gross_profit', 'operating_income')
),
reported_segment_presence as (
    select distinct evidence.instrument_id
    from research.segment_footnote_evidence evidence
    where evidence.as_of_date <= {sql_date(as_of_date)}
      and evidence.statement_scope = {sql_literal(statement_scope)}
      and evidence.evidence_type = 'reported_segment_metric'
),
evidence_rows as (
    select
        period.instrument_id,
        {sql_date(as_of_date)} as as_of_date,
        {sql_literal(statement_scope)}::text as statement_scope,
        'filing_anchor'::text as segment_key,
        'SEC 공시 원천 문서'::text as segment_label,
        'filing_anchor'::text as evidence_type,
        'source_document'::text as metric_code,
        null::numeric as metric_value,
        'n/a'::text as metric_unit,
        period.period_end,
        period.source_document_id,
        coalesce(period.source_document_title, period.primary_symbol || ' SEC filing source') as evidence_text,
        jsonb_build_object(
            'source', 'market.financial_statement_period.source_document_id',
            'primary_symbol', period.primary_symbol,
            'source_document_title', period.source_document_title,
            'source_document_summary', period.source_document_summary,
            'source_document_url', period.source_document_url,
            'interpretation', 'SOTP와 재무제표 모델이 참조하는 최신 SEC filing anchor다.',
            'recommendation_scoring_mutated', false
        ) as assumptions_json,
        case when period.source_document_id is not null then 0.7000::numeric else 0.4500::numeric end as confidence
    from latest_periods period
    union all
    select
        metric.instrument_id,
        {sql_date(as_of_date)} as as_of_date,
        {sql_literal(statement_scope)}::text as statement_scope,
        'consolidated_total'::text as segment_key,
        '연결 기준 전체 회사'::text as segment_label,
        'consolidated_metric'::text as evidence_type,
        metric.metric_code,
        metric.metric_value,
        metric.unit,
        metric.period_end,
        metric.source_document_id,
        metric.primary_symbol || ' consolidated ' || metric.metric_code || ' from SEC companyfacts' as evidence_text,
        jsonb_build_object(
            'source', 'market.financial_metric_value',
            'primary_symbol', metric.primary_symbol,
            'source_document_title', metric.source_document_title,
            'source_document_url', metric.source_document_url,
            'metric_code', metric.metric_code,
            'metric_value', metric.metric_value,
            'metric_unit', metric.unit,
            'interpretation', '사업부별 segment가 아니라 연결 기준 전체 회사 metric이다.',
            'reported_segment_metric', false,
            'recommendation_scoring_mutated', false
        ) as assumptions_json,
        0.6500::numeric as confidence
    from latest_metric_rows metric
    union all
    select
        period.instrument_id,
        {sql_date(as_of_date)} as as_of_date,
        {sql_literal(statement_scope)}::text as statement_scope,
        'segment_data_gap'::text as segment_key,
        '사업부별 세그먼트 데이터 공백'::text as segment_label,
        'segment_data_gap'::text as evidence_type,
        'segment_detail'::text as metric_code,
        null::numeric as metric_value,
        'n/a'::text as metric_unit,
        period.period_end,
        period.source_document_id,
        'SEC footnote parser has not confirmed reported business segment metrics for ' || period.primary_symbol as evidence_text,
        jsonb_build_object(
            'source', 'deterministic_segment_footnote_gap_detector',
            'primary_symbol', period.primary_symbol,
            'source_document_title', period.source_document_title,
            'source_document_url', period.source_document_url,
            'interpretation', '현재는 사업부별 매출·마진·자본배분 footnote가 구조화되지 않아 SOTP가 proxy reserve를 유지해야 한다.',
            'missing_reported_segment_metric', true,
            'recommendation_scoring_mutated', false
        ) as assumptions_json,
        0.8000::numeric as confidence
    from latest_periods period
    where not exists (
        select 1
        from reported_segment_presence presence
        where presence.instrument_id = period.instrument_id
    )
),
upsert_evidence as (
    insert into research.segment_footnote_evidence (
        instrument_id,
        as_of_date,
        statement_scope,
        segment_key,
        segment_label,
        evidence_type,
        metric_code,
        metric_value,
        metric_unit,
        period_end,
        source_document_id,
        evidence_text,
        assumptions_json,
        confidence,
        source_run_id
    )
    select
        instrument_id,
        as_of_date,
        statement_scope,
        segment_key,
        segment_label,
        evidence_type,
        metric_code,
        metric_value,
        metric_unit,
        period_end,
        source_document_id,
        evidence_text,
        assumptions_json,
        confidence,
        {int(source_run_id)}::bigint
    from evidence_rows
    on conflict (
        instrument_id,
        as_of_date,
        statement_scope,
        segment_key,
        evidence_type,
        metric_code,
        period_end
    ) do update
    set
        segment_label = excluded.segment_label,
        metric_value = excluded.metric_value,
        metric_unit = excluded.metric_unit,
        source_document_id = excluded.source_document_id,
        evidence_text = excluded.evidence_text,
        assumptions_json = excluded.assumptions_json,
        confidence = excluded.confidence,
        source_run_id = excluded.source_run_id
    returning evidence_type, metric_code, confidence
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'source_run_id', {int(source_run_id)},
    'statement_scope', {sql_literal(statement_scope)},
    'evidence_row_count', (select count(*)::integer from upsert_evidence),
    'evidence_type_counts',
        coalesce(
            (
                select json_object_agg(evidence_type, evidence_count order by evidence_type)
                from (
                    select evidence_type, count(*)::integer as evidence_count
                    from upsert_evidence
                    group by evidence_type
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
            from upsert_evidence
        ),
    'recommendation_scoring_mutated', false
)::text;"""


def load_segment_footnote_evidence_preview(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    statement_scope: str = "annual",
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_segment_footnote_evidence_preview_sql(as_of_date=as_of_date, statement_scope=statement_scope)
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Segment footnote evidence preview did not return a JSON object.")
    return payload


def run_segment_footnote_evidence(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    statement_scope: str = "annual",
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    preview = load_segment_footnote_evidence_preview(
        config=config,
        as_of_date=as_of_date,
        statement_scope=statement_scope,
        executor=sql_executor,
    )
    report: dict[str, object] = {
        "report_name": "segment_footnote_evidence",
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_SEGMENT_FOOTNOTE_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "statement_scope": statement_scope,
        "model_name": DEFAULT_SEGMENT_FOOTNOTE_MODEL_NAME,
        "evidence_types": list(SEGMENT_FOOTNOTE_EVIDENCE_TYPES),
        "preview": preview,
        "recommendation_scoring_mutated": False,
    }
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_SEGMENT_FOOTNOTE_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "statement_scope": statement_scope,
            "model_name": DEFAULT_SEGMENT_FOOTNOTE_MODEL_NAME,
            "evidence_types": list(SEGMENT_FOOTNOTE_EVIDENCE_TYPES),
            "recommendation_scoring_mutated": False,
        },
    )
    try:
        upsert_summary = json.loads(
            sql_executor.execute_scalar(
                render_segment_footnote_evidence_upsert_sql(
                    as_of_date=as_of_date,
                    source_run_id=run_id,
                    statement_scope=statement_scope,
                )
            )
        )
        if not isinstance(upsert_summary, dict):
            raise ValueError("Segment footnote evidence upsert did not return a JSON object.")
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


def render_sum_of_parts_valuation_preview_sql(
    *,
    as_of_date: date,
    statement_scope: str = "annual",
) -> str:
    _validate_valuation_args(statement_scope=statement_scope)
    return f"""-- sum of parts valuation preview
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
        'total_assets',
        'total_liabilities',
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
        max(metric_value) filter (where metric_code = 'total_assets') as total_assets,
        max(metric_value) filter (where metric_code = 'total_liabilities') as total_liabilities,
        max(metric_value) filter (where metric_code = 'revenue') as revenue
    from latest_raw_metric_rows
    group by instrument_id
),
latest_forecast_rows as (
    select distinct on (forecast.instrument_id, forecast.scenario_key, forecast.forecast_year)
        forecast.instrument_id,
        forecast.as_of_date,
        forecast.scenario_key,
        forecast.forecast_year,
        forecast.free_cash_flow,
        forecast.confidence
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
        max(free_cash_flow) filter (where scenario_key = 'base' and forecast_year = {FINANCIAL_FORECAST_YEARS}) as terminal_base_free_cash_flow,
        avg(confidence) as forecast_confidence
    from latest_forecast_rows
    group by instrument_id
),
reported_segment_history_rows as (
    select
        evidence.instrument_id,
        evidence.segment_key,
        max(evidence.segment_label) as segment_label,
        evidence.period_end,
        max(evidence.metric_value) filter (where evidence.metric_code = 'segment_revenue') as segment_revenue,
        max(evidence.metric_value) filter (where evidence.metric_code = 'segment_operating_income') as segment_operating_income,
        avg(evidence.confidence) as confidence
    from research.segment_footnote_evidence evidence
    where evidence.as_of_date <= {sql_date(as_of_date)}
      and evidence.statement_scope = {sql_literal(statement_scope)}
      and evidence.evidence_type = 'reported_segment_metric'
      and evidence.metric_code in ('segment_revenue', 'segment_operating_income')
    group by evidence.instrument_id, evidence.segment_key, evidence.period_end
    having
        max(evidence.metric_value) filter (where evidence.metric_code = 'segment_revenue') is not null
        or max(evidence.metric_value) filter (where evidence.metric_code = 'segment_operating_income') is not null
),
reported_segment_history_ranked as (
    select
        row.*,
        case
            when row.segment_revenue is not null
             and row.segment_revenue > 0
             and row.segment_operating_income is not null
            then row.segment_operating_income / row.segment_revenue
            else null::numeric
        end as operating_margin,
        row_number() over (partition by row.instrument_id, row.segment_key order by row.period_end asc) as first_period_rank,
        row_number() over (partition by row.instrument_id, row.segment_key order by row.period_end desc) as latest_period_rank
    from reported_segment_history_rows row
),
reported_segment_trend_anchors as (
    select
        instrument_id,
        segment_key,
        count(*)::integer as history_period_count,
        min(period_end) as first_period_end,
        max(period_end) as latest_period_end,
        greatest(1.0000::numeric, ((max(period_end) - min(period_end))::numeric / 365.2500::numeric)) as history_year_span,
        max(segment_revenue) filter (where first_period_rank = 1) as first_revenue,
        max(segment_revenue) filter (where latest_period_rank = 1) as latest_revenue,
        max(operating_margin) filter (where first_period_rank = 1) as first_operating_margin,
        max(operating_margin) filter (where latest_period_rank = 1) as latest_operating_margin,
        avg(confidence) as trend_confidence
    from reported_segment_history_ranked
    group by instrument_id, segment_key
),
reported_segment_trends as (
    select
        anchor.*,
        case
            when anchor.history_period_count >= 2
             and anchor.first_revenue is not null
             and anchor.first_revenue > 0
             and anchor.latest_revenue is not null
             and anchor.latest_revenue > 0
            then power(
                (anchor.latest_revenue / anchor.first_revenue)::double precision,
                (1.0000::numeric / anchor.history_year_span)::double precision
            )::numeric - 1.0000::numeric
            else null::numeric
        end as observed_revenue_cagr,
        case
            when anchor.history_period_count >= 2
             and anchor.first_operating_margin is not null
             and anchor.latest_operating_margin is not null
            then anchor.latest_operating_margin - anchor.first_operating_margin
            else null::numeric
        end as observed_margin_change
    from reported_segment_trend_anchors anchor
),
latest_segment_evidence as (
    select distinct on (evidence.instrument_id, evidence.segment_key, evidence.evidence_type, evidence.metric_code)
        evidence.instrument_id,
        evidence.segment_key,
        evidence.evidence_type,
        evidence.metric_code,
        evidence.metric_value,
        evidence.period_end
    from research.segment_footnote_evidence evidence
    where evidence.as_of_date <= {sql_date(as_of_date)}
      and evidence.statement_scope = {sql_literal(statement_scope)}
    order by
        evidence.instrument_id,
        evidence.segment_key,
        evidence.evidence_type,
        evidence.metric_code,
        evidence.as_of_date desc,
        evidence.evidence_id desc
),
reported_segment_inputs as (
    select
        instrument_id,
        count(distinct segment_key)::integer as reported_segment_input_count
    from latest_segment_evidence
    where evidence_type = 'reported_segment_metric'
      and metric_code in ('segment_revenue', 'segment_operating_income')
    group by instrument_id
),
sotp_context as (
    select
        price.instrument_id,
        price.base_price,
        raw.shares_outstanding,
        raw.operating_cash_flow,
        raw.capital_expenditure,
        raw.total_assets,
        raw.total_liabilities,
        forecast.forecast_row_count
    from latest_prices price
    left join raw_inputs raw on raw.instrument_id = price.instrument_id
    left join forecast_inputs forecast on forecast.instrument_id = price.instrument_id
    where price.base_price > 0
      and raw.shares_outstanding is not null
      and raw.shares_outstanding > 0
      and (
        forecast.terminal_base_free_cash_flow is not null
        or (raw.operating_cash_flow is not null and raw.capital_expenditure is not null)
        or (raw.total_assets is not null and raw.total_liabilities is not null)
      )
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'model_name', {sql_literal(DEFAULT_SOTP_MODEL_NAME)},
    'statement_scope', {sql_literal(statement_scope)},
    'component_types', {sql_literal(json.dumps(SOTP_COMPONENT_TYPES))}::jsonb,
    'price_coverage_count', (select count(*)::integer from latest_prices),
    'raw_input_count', (select count(*)::integer from raw_inputs),
    'forecast_input_count', (select count(*)::integer from forecast_inputs),
    'segment_footnote_evidence_count', (select count(*)::integer from latest_segment_evidence),
    'reported_segment_input_count', coalesce((select sum(reported_segment_input_count)::integer from reported_segment_inputs), 0),
    'sotp_context_count', (select count(*)::integer from sotp_context),
    'existing_component_count',
        (
            select count(*)::integer
            from market.sum_of_parts_component
            where as_of_date = {sql_date(as_of_date)}
              and statement_scope = {sql_literal(statement_scope)}
        )
)::text;"""


def render_sum_of_parts_valuation_upsert_sql(
    *,
    as_of_date: date,
    source_run_id: int,
    statement_scope: str = "annual",
) -> str:
    _validate_valuation_args(statement_scope=statement_scope)
    return f"""-- sum of parts valuation upsert
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
        'total_assets',
        'total_liabilities',
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
        max(metric_value) filter (where metric_code = 'total_assets') as total_assets,
        max(metric_value) filter (where metric_code = 'total_liabilities') as total_liabilities,
        max(metric_value) filter (where metric_code = 'revenue') as revenue,
        max(period_end) as latest_raw_period_end
    from latest_raw_metric_rows
    group by instrument_id
),
latest_forecast_rows as (
    select distinct on (forecast.instrument_id, forecast.scenario_key, forecast.forecast_year)
        forecast.instrument_id,
        forecast.as_of_date,
        forecast.scenario_key,
        forecast.forecast_year,
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
        max(free_cash_flow) filter (where scenario_key = 'base' and forecast_year = {FINANCIAL_FORECAST_YEARS}) as terminal_base_free_cash_flow,
        avg(confidence) as forecast_confidence,
        max(source_run_id) as forecast_source_run_id
    from latest_forecast_rows
    group by instrument_id
),
reported_segment_history_rows as (
    select
        evidence.instrument_id,
        evidence.segment_key,
        max(evidence.segment_label) as segment_label,
        evidence.period_end,
        max(evidence.metric_value) filter (where evidence.metric_code = 'segment_revenue') as segment_revenue,
        max(evidence.metric_value) filter (where evidence.metric_code = 'segment_operating_income') as segment_operating_income,
        avg(evidence.confidence) as confidence
    from research.segment_footnote_evidence evidence
    where evidence.as_of_date <= {sql_date(as_of_date)}
      and evidence.statement_scope = {sql_literal(statement_scope)}
      and evidence.evidence_type = 'reported_segment_metric'
      and evidence.metric_code in ('segment_revenue', 'segment_operating_income')
    group by evidence.instrument_id, evidence.segment_key, evidence.period_end
    having
        max(evidence.metric_value) filter (where evidence.metric_code = 'segment_revenue') is not null
        or max(evidence.metric_value) filter (where evidence.metric_code = 'segment_operating_income') is not null
),
reported_segment_history_ranked as (
    select
        row.*,
        case
            when row.segment_revenue is not null
             and row.segment_revenue > 0
             and row.segment_operating_income is not null
            then row.segment_operating_income / row.segment_revenue
            else null::numeric
        end as operating_margin,
        row_number() over (partition by row.instrument_id, row.segment_key order by row.period_end asc) as first_period_rank,
        row_number() over (partition by row.instrument_id, row.segment_key order by row.period_end desc) as latest_period_rank
    from reported_segment_history_rows row
),
reported_segment_trend_anchors as (
    select
        instrument_id,
        segment_key,
        count(*)::integer as history_period_count,
        min(period_end) as first_period_end,
        max(period_end) as latest_period_end,
        greatest(1.0000::numeric, ((max(period_end) - min(period_end))::numeric / 365.2500::numeric)) as history_year_span,
        max(segment_revenue) filter (where first_period_rank = 1) as first_revenue,
        max(segment_revenue) filter (where latest_period_rank = 1) as latest_revenue,
        max(operating_margin) filter (where first_period_rank = 1) as first_operating_margin,
        max(operating_margin) filter (where latest_period_rank = 1) as latest_operating_margin,
        avg(confidence) as trend_confidence
    from reported_segment_history_ranked
    group by instrument_id, segment_key
),
reported_segment_trends as (
    select
        anchor.*,
        case
            when anchor.history_period_count >= 2
             and anchor.first_revenue is not null
             and anchor.first_revenue > 0
             and anchor.latest_revenue is not null
             and anchor.latest_revenue > 0
            then power(
                (anchor.latest_revenue / anchor.first_revenue)::double precision,
                (1.0000::numeric / anchor.history_year_span)::double precision
            )::numeric - 1.0000::numeric
            else null::numeric
        end as observed_revenue_cagr,
        case
            when anchor.history_period_count >= 2
             and anchor.first_operating_margin is not null
             and anchor.latest_operating_margin is not null
            then anchor.latest_operating_margin - anchor.first_operating_margin
            else null::numeric
        end as observed_margin_change
    from reported_segment_trend_anchors anchor
),
latest_segment_evidence as (
    select distinct on (evidence.instrument_id, evidence.segment_key, evidence.evidence_type, evidence.metric_code)
        evidence.instrument_id,
        evidence.as_of_date,
        evidence.segment_key,
        evidence.segment_label,
        evidence.evidence_type,
        evidence.metric_code,
        evidence.metric_value,
        evidence.metric_unit,
        evidence.period_end,
        evidence.source_document_id,
        evidence.evidence_text,
        evidence.confidence,
        evidence.source_run_id
    from research.segment_footnote_evidence evidence
    where evidence.as_of_date <= {sql_date(as_of_date)}
      and evidence.statement_scope = {sql_literal(statement_scope)}
    order by
        evidence.instrument_id,
        evidence.segment_key,
        evidence.evidence_type,
        evidence.metric_code,
        evidence.as_of_date desc,
        evidence.evidence_id desc
),
reported_segment_input_rows as (
    select
        instrument_id,
        segment_key,
        max(segment_label) as segment_label,
        period_end,
        max(metric_value) filter (where metric_code = 'segment_revenue') as segment_revenue,
        max(metric_value) filter (where metric_code = 'segment_operating_income') as segment_operating_income,
        max(metric_unit) filter (where metric_code = 'segment_revenue') as segment_revenue_unit,
        max(metric_unit) filter (where metric_code = 'segment_operating_income') as segment_operating_income_unit,
        max(source_document_id) filter (where metric_code = 'segment_revenue') as revenue_source_document_id,
        max(source_document_id) filter (where metric_code = 'segment_operating_income') as operating_income_source_document_id,
        avg(confidence) as confidence,
        max(source_run_id) as source_run_id
    from latest_segment_evidence
    where evidence_type = 'reported_segment_metric'
      and metric_code in ('segment_revenue', 'segment_operating_income')
    group by instrument_id, segment_key, period_end
    having
        max(metric_value) filter (where metric_code = 'segment_revenue') is not null
        or max(metric_value) filter (where metric_code = 'segment_operating_income') is not null
),
reported_segment_inputs as (
    select
        instrument_id,
        count(*)::integer as reported_segment_input_count,
        max(period_end) as latest_reported_segment_period_end,
        sum(segment_revenue) as reported_segment_revenue_total,
        sum(segment_operating_income) as reported_segment_operating_income_total,
        avg(confidence) as reported_segment_confidence,
        jsonb_agg(
            jsonb_build_object(
                'segment_key', segment_key,
                'segment_label', segment_label,
                'period_end', period_end,
                'revenue', segment_revenue,
                'operating_income', segment_operating_income,
                'operating_margin',
                    case
                        when segment_revenue is not null
                         and segment_revenue > 0
                         and segment_operating_income is not null
                        then segment_operating_income / segment_revenue
                        else null::numeric
                    end,
                'metric_unit', coalesce(segment_revenue_unit, segment_operating_income_unit, 'USD_as_reported'),
                'source_document_id', coalesce(revenue_source_document_id, operating_income_source_document_id),
                'confidence', confidence,
                'source_run_id', source_run_id
            )
            order by segment_revenue desc nulls last, segment_key
        ) as reported_segment_inputs_json
    from reported_segment_input_rows
    group by instrument_id
),
reported_segment_allocation_rows as (
    select
        row.instrument_id,
        row.segment_key,
        row.segment_label,
        row.period_end,
        row.segment_revenue,
        row.segment_operating_income,
        case
            when total.reported_segment_revenue_total is not null
             and total.reported_segment_revenue_total > 0
             and row.segment_revenue is not null
            then row.segment_revenue / total.reported_segment_revenue_total
            else null::numeric
        end as revenue_share,
        case
            when total.reported_segment_operating_income_total is not null
             and total.reported_segment_operating_income_total > 0
             and row.segment_operating_income is not null
            then row.segment_operating_income / total.reported_segment_operating_income_total
            else null::numeric
        end as operating_income_share,
        case
            when total.reported_segment_operating_income_total is not null
             and total.reported_segment_operating_income_total > 0
             and row.segment_operating_income is not null
            then 'operating_income_share'
            when total.reported_segment_revenue_total is not null
             and total.reported_segment_revenue_total > 0
             and row.segment_revenue is not null
            then 'revenue_share'
            else 'unallocated'
        end as allocation_basis,
        case
            when total.reported_segment_operating_income_total is not null
             and total.reported_segment_operating_income_total > 0
             and row.segment_operating_income is not null
            then row.segment_operating_income / total.reported_segment_operating_income_total
            when total.reported_segment_revenue_total is not null
             and total.reported_segment_revenue_total > 0
             and row.segment_revenue is not null
            then row.segment_revenue / total.reported_segment_revenue_total
            else null::numeric
        end as allocation_weight,
        coalesce(row.revenue_source_document_id, row.operating_income_source_document_id) as source_document_id,
        row.confidence,
        row.source_run_id
    from reported_segment_input_rows row
    join reported_segment_inputs total on total.instrument_id = row.instrument_id
),
reported_segment_assumption_base as (
    select
        allocation.*,
        trend.history_period_count,
        trend.first_period_end,
        trend.latest_period_end,
        trend.history_year_span,
        trend.observed_revenue_cagr,
        trend.observed_margin_change,
        trend.trend_confidence,
        case
            when lower(coalesce(allocation.segment_label, '')) like '%service%' then 'services_installed_base'
            when lower(coalesce(allocation.segment_label, '')) like '%iphone%'
              or lower(coalesce(allocation.segment_label, '')) like '%ipad%'
              or lower(coalesce(allocation.segment_label, '')) like '%mac%'
              or lower(coalesce(allocation.segment_label, '')) like '%wearable%'
              or lower(coalesce(allocation.segment_label, '')) like '%product%' then 'hardware_product_cycle'
            when lower(coalesce(allocation.segment_label, '')) like '%data center%'
              or lower(coalesce(allocation.segment_label, '')) like '%cloud%'
              or lower(coalesce(allocation.segment_label, '')) like '%ai%' then 'ai_data_center_cycle'
            when lower(coalesce(allocation.segment_label, '')) like '%energy%'
              or lower(coalesce(allocation.segment_label, '')) like '%oil%'
              or lower(coalesce(allocation.segment_label, '')) like '%gas%' then 'energy_cycle'
            when lower(coalesce(allocation.segment_label, '')) like '%america%'
              or lower(coalesce(allocation.segment_label, '')) like '%europe%'
              or lower(coalesce(allocation.segment_label, '')) like '%china%'
              or lower(coalesce(allocation.segment_label, '')) like '%japan%'
              or lower(coalesce(allocation.segment_label, '')) like '%asia%' then 'geographic_demand_cycle'
            else 'generic_business_segment'
        end as driver_template_key,
        case
            when lower(coalesce(allocation.segment_label, '')) like '%service%' then '설치 기반·구독·총마진'
            when lower(coalesce(allocation.segment_label, '')) like '%iphone%'
              or lower(coalesce(allocation.segment_label, '')) like '%ipad%'
              or lower(coalesce(allocation.segment_label, '')) like '%mac%'
              or lower(coalesce(allocation.segment_label, '')) like '%wearable%'
              or lower(coalesce(allocation.segment_label, '')) like '%product%' then '제품 교체 사이클·ASP·공급망'
            when lower(coalesce(allocation.segment_label, '')) like '%data center%'
              or lower(coalesce(allocation.segment_label, '')) like '%cloud%'
              or lower(coalesce(allocation.segment_label, '')) like '%ai%' then 'AI/클라우드 투자 사이클'
            when lower(coalesce(allocation.segment_label, '')) like '%energy%'
              or lower(coalesce(allocation.segment_label, '')) like '%oil%'
              or lower(coalesce(allocation.segment_label, '')) like '%gas%' then '원자재 가격·CAPEX 사이클'
            when lower(coalesce(allocation.segment_label, '')) like '%america%'
              or lower(coalesce(allocation.segment_label, '')) like '%europe%'
              or lower(coalesce(allocation.segment_label, '')) like '%china%'
              or lower(coalesce(allocation.segment_label, '')) like '%japan%'
              or lower(coalesce(allocation.segment_label, '')) like '%asia%' then '지역 수요·환율·채널 믹스'
            else '사업부 규모·마진·경쟁 강도'
        end as driver_template_label,
        case
            when allocation.segment_revenue is not null
             and allocation.segment_revenue > 0
             and allocation.segment_operating_income is not null
            then allocation.segment_operating_income / allocation.segment_revenue
            else null::numeric
        end as operating_margin
    from reported_segment_allocation_rows allocation
    left join reported_segment_trends trend
        on trend.instrument_id = allocation.instrument_id
       and trend.segment_key = allocation.segment_key
    where allocation.allocation_weight is not null
),
reported_segment_assumption_rows as (
    select
        base.instrument_id,
        base.segment_key,
        base.segment_label,
        base.period_end,
        base.allocation_basis,
        base.allocation_weight,
        base.revenue_share,
        base.operating_income_share,
        base.segment_revenue,
        base.segment_operating_income,
        base.operating_margin,
        coalesce(base.history_period_count, 1)::integer as history_period_count,
        base.first_period_end,
        base.latest_period_end,
        base.history_year_span,
        base.observed_revenue_cagr,
        base.observed_margin_change,
        base.trend_confidence,
        base.driver_template_key,
        base.driver_template_label,
        case
            when coalesce(base.history_period_count, 1) >= 2
             and base.observed_revenue_cagr is not null
            then 'multi_period_segment_trend_template'
            else 'single_period_margin_share_template_proxy'
        end as calibration_method,
        case
            when base.operating_margin is null then 'margin_unknown'
            when base.operating_margin >= 0.3500::numeric then 'high_margin_cash_engine'
            when base.operating_margin >= 0.2000::numeric then 'core_cash_generator'
            when base.operating_margin > 0 then 'lower_margin_scale_segment'
            else 'loss_or_reinvestment_segment'
        end as driver_key,
        case
            when base.operating_margin is null then '마진 확인 필요'
            when base.operating_margin >= 0.3500::numeric then '고마진 현금창출 사업부'
            when base.operating_margin >= 0.2000::numeric then '핵심 현금창출 사업부'
            when base.operating_margin > 0 then '저마진 규모 사업부'
            else '손실 또는 재투자 사업부'
        end as driver_label,
        case
            when coalesce(base.history_period_count, 1) >= 2
             and base.observed_revenue_cagr is not null
            then least(0.1200::numeric, greatest(-0.0200::numeric, base.observed_revenue_cagr))
            when base.operating_margin is null then 0.0200::numeric
            when base.operating_margin >= 0.3500::numeric and base.allocation_weight >= 0.2500::numeric then 0.0600::numeric
            when base.operating_margin >= 0.3500::numeric then 0.0500::numeric
            when base.operating_margin >= 0.2000::numeric then 0.0400::numeric
            when base.operating_margin > 0 then 0.0250::numeric
            else 0.0100::numeric
        end as base_growth_rate,
        case
            when base.operating_margin is null then 10.0000::numeric
            when base.operating_margin >= 0.3500::numeric then 16.0000::numeric
            when base.operating_margin >= 0.2000::numeric then 13.0000::numeric
            when base.operating_margin > 0 then 9.0000::numeric
            else 7.0000::numeric
        end
        + case
            when base.observed_margin_change >= 0.0300::numeric then 1.0000::numeric
            when base.observed_margin_change <= -0.0300::numeric then -1.0000::numeric
            else 0.0000::numeric
        end as low_multiple,
        case
            when base.operating_margin is null then 14.0000::numeric
            when base.operating_margin >= 0.3500::numeric then 20.0000::numeric
            when base.operating_margin >= 0.2000::numeric then 17.0000::numeric
            when base.operating_margin > 0 then 12.0000::numeric
            else 10.0000::numeric
        end
        + case
            when base.observed_margin_change >= 0.0300::numeric then 1.0000::numeric
            when base.observed_margin_change <= -0.0300::numeric then -1.0000::numeric
            else 0.0000::numeric
        end as base_multiple,
        case
            when base.operating_margin is null then 18.0000::numeric
            when base.operating_margin >= 0.3500::numeric then 24.0000::numeric
            when base.operating_margin >= 0.2000::numeric then 21.0000::numeric
            when base.operating_margin > 0 then 15.0000::numeric
            else 13.0000::numeric
        end
        + case
            when base.observed_margin_change >= 0.0300::numeric then 1.0000::numeric
            when base.observed_margin_change <= -0.0300::numeric then -1.0000::numeric
            else 0.0000::numeric
        end as high_multiple,
        base.source_document_id,
        base.confidence,
        base.source_run_id
    from reported_segment_assumption_base base
),
segment_evidence_inputs as (
    select
        instrument_id,
        count(*)::integer as segment_evidence_count,
        count(*) filter (where evidence_type = 'reported_segment_metric')::integer as reported_segment_metric_count,
        count(*) filter (where evidence_type = 'segment_data_gap')::integer as segment_data_gap_count,
        max(as_of_date) as latest_segment_evidence_as_of_date,
        avg(confidence) as segment_evidence_confidence,
        jsonb_agg(
            jsonb_build_object(
                'segment_key', segment_key,
                'segment_label', segment_label,
                'evidence_type', evidence_type,
                'metric_code', metric_code,
                'metric_value', metric_value,
                'metric_unit', metric_unit,
                'period_end', period_end,
                'source_document_id', source_document_id,
                'evidence_text', evidence_text,
                'confidence', confidence,
                'source_run_id', source_run_id
            )
            order by
                case evidence_type
                    when 'reported_segment_metric' then 1
                    when 'consolidated_metric' then 2
                    when 'filing_anchor' then 3
                    when 'segment_data_gap' then 4
                    else 9
                end,
                segment_key,
                metric_code
        ) as segment_evidence_json
    from latest_segment_evidence
    group by instrument_id
),
sotp_inputs as (
    select
        price.instrument_id,
        price.primary_symbol,
        price.base_price,
        price.price_date,
        raw.latest_raw_period_end,
        raw.operating_cash_flow,
        raw.capital_expenditure,
        case
            when raw.operating_cash_flow is not null and raw.capital_expenditure is not null
            then raw.operating_cash_flow - abs(raw.capital_expenditure)
            else null::numeric
        end as free_cash_flow,
        raw.shares_outstanding,
        raw.total_assets,
        raw.total_liabilities,
        case
            when raw.total_assets is not null and raw.total_liabilities is not null
            then raw.total_assets - raw.total_liabilities
            else null::numeric
        end as book_equity,
        forecast.latest_forecast_as_of_date,
        forecast.forecast_row_count,
        forecast.terminal_base_free_cash_flow,
        forecast.forecast_confidence,
        forecast.forecast_source_run_id,
        segment.segment_evidence_count,
        segment.reported_segment_metric_count,
        segment.segment_data_gap_count,
        segment.latest_segment_evidence_as_of_date,
        segment.segment_evidence_confidence,
        segment.segment_evidence_json,
        reported.reported_segment_input_count,
        reported.latest_reported_segment_period_end,
        reported.reported_segment_revenue_total,
        reported.reported_segment_operating_income_total,
        reported.reported_segment_confidence,
        reported.reported_segment_inputs_json
    from latest_prices price
    left join raw_inputs raw on raw.instrument_id = price.instrument_id
    left join forecast_inputs forecast on forecast.instrument_id = price.instrument_id
    left join segment_evidence_inputs segment on segment.instrument_id = price.instrument_id
    left join reported_segment_inputs reported on reported.instrument_id = price.instrument_id
    where price.base_price > 0
      and raw.shares_outstanding is not null
      and raw.shares_outstanding > 0
      and (
        forecast.terminal_base_free_cash_flow is not null
        or (raw.operating_cash_flow is not null and raw.capital_expenditure is not null)
        or (raw.total_assets is not null and raw.total_liabilities is not null)
      )
),
component_rows as (
    select
        input.instrument_id,
        'operating_business_fcf'::text as component_key,
        '영업사업 가치'::text as component_label,
        'operating_business'::text as component_type,
        (
            coalesce(input.terminal_base_free_cash_flow, input.free_cash_flow)
            * 14.0000::numeric / input.shares_outstanding
        ) as fair_value_low,
        (
            coalesce(input.terminal_base_free_cash_flow, input.free_cash_flow)
            * 18.0000::numeric / input.shares_outstanding
        ) as fair_value_base,
        (
            coalesce(input.terminal_base_free_cash_flow, input.free_cash_flow)
            * 22.0000::numeric / input.shares_outstanding
        ) as fair_value_high,
        'forecast_or_latest_fcf_multiple'::text as valuation_basis,
        jsonb_build_object(
            'component_description', 'Forecast 또는 최근 FCF에 보수적인 FCF multiple을 적용한 핵심 영업사업 가치다.',
            'fcf_source', case when input.terminal_base_free_cash_flow is not null then 'market.financial_forecast_input' else 'latest_financial_metric_value' end,
            'terminal_base_free_cash_flow', input.terminal_base_free_cash_flow,
            'latest_free_cash_flow', input.free_cash_flow,
            'shares_outstanding', input.shares_outstanding,
            'low_multiple', 14.0000,
            'base_multiple', 18.0000,
            'high_multiple', 22.0000,
            'latest_forecast_as_of_date', input.latest_forecast_as_of_date,
            'forecast_row_count', coalesce(input.forecast_row_count, 0),
            'latest_raw_period_end', input.latest_raw_period_end
            , 'reported_segment_allocation_source', 'research.segment_footnote_evidence'
            , 'reported_segment_allocation_method', 'operating_income_share_then_revenue_share'
            , 'reported_segment_allocation_count',
                coalesce(
                    (
                        select count(*)::integer
                        from reported_segment_allocation_rows allocation
                        where allocation.instrument_id = input.instrument_id
                          and allocation.allocation_weight is not null
                    ),
                    0
                )
            , 'reported_segment_allocations',
                coalesce(
                    (
                        select jsonb_agg(
                            jsonb_build_object(
                                'segment_key', allocation.segment_key,
                                'segment_label', allocation.segment_label,
                                'period_end', allocation.period_end,
                                'allocation_basis', allocation.allocation_basis,
                                'allocation_weight', allocation.allocation_weight,
                                'revenue_share', allocation.revenue_share,
                                'operating_income_share', allocation.operating_income_share,
                                'allocated_fair_value_low',
                                    (
                                        coalesce(input.terminal_base_free_cash_flow, input.free_cash_flow)
                                        * 14.0000::numeric / input.shares_outstanding
                                    ) * allocation.allocation_weight,
                                'allocated_fair_value_base',
                                    (
                                        coalesce(input.terminal_base_free_cash_flow, input.free_cash_flow)
                                        * 18.0000::numeric / input.shares_outstanding
                                    ) * allocation.allocation_weight,
                                'allocated_fair_value_high',
                                    (
                                        coalesce(input.terminal_base_free_cash_flow, input.free_cash_flow)
                                        * 22.0000::numeric / input.shares_outstanding
                                    ) * allocation.allocation_weight,
                                'revenue', allocation.segment_revenue,
                                'operating_income', allocation.segment_operating_income,
                                'source_document_id', allocation.source_document_id,
                                'confidence', allocation.confidence,
                                'source_run_id', allocation.source_run_id
                            )
                            order by allocation.allocation_weight desc nulls last, allocation.segment_key
                        )
                        from reported_segment_allocation_rows allocation
                        where allocation.instrument_id = input.instrument_id
                          and allocation.allocation_weight is not null
                    ),
                    '[]'::jsonb
                )
            , 'reported_segment_assumption_source', 'research.segment_footnote_evidence'
            , 'reported_segment_assumption_policy', 'deterministic_margin_share_proxy_no_score_change'
            , 'reported_segment_assumption_count',
                coalesce(
                    (
                        select count(*)::integer
                        from reported_segment_assumption_rows assumption
                        where assumption.instrument_id = input.instrument_id
                    ),
                    0
                )
            , 'reported_segment_assumptions',
                coalesce(
                    (
                        select jsonb_agg(
                            jsonb_build_object(
                                'segment_key', assumption.segment_key,
                                'segment_label', assumption.segment_label,
                                'period_end', assumption.period_end,
                                'driver_key', assumption.driver_key,
                                'driver_label', assumption.driver_label,
                                'driver_template_key', assumption.driver_template_key,
                                'driver_template_label', assumption.driver_template_label,
                                'calibration_method', assumption.calibration_method,
                                'history_period_count', assumption.history_period_count,
                                'first_period_end', assumption.first_period_end,
                                'latest_period_end', assumption.latest_period_end,
                                'history_year_span', assumption.history_year_span,
                                'observed_revenue_cagr', assumption.observed_revenue_cagr,
                                'observed_margin_change', assumption.observed_margin_change,
                                'base_growth_rate', assumption.base_growth_rate,
                                'low_growth_rate', greatest(-0.0200::numeric, assumption.base_growth_rate - 0.0300::numeric),
                                'high_growth_rate', least(0.1200::numeric, assumption.base_growth_rate + 0.0300::numeric),
                                'margin_assumption', assumption.operating_margin,
                                'low_multiple', assumption.low_multiple,
                                'base_multiple', assumption.base_multiple,
                                'high_multiple', assumption.high_multiple,
                                'allocation_weight', assumption.allocation_weight,
                                'allocation_basis', assumption.allocation_basis,
                                'revenue_share', assumption.revenue_share,
                                'operating_income_share', assumption.operating_income_share,
                                'revenue', assumption.segment_revenue,
                                'operating_income', assumption.segment_operating_income,
                                'rationale',
                                    concat(
                                        assumption.driver_label,
                                        ' · 기준 성장률 ',
                                        round(assumption.base_growth_rate * 100, 1),
                                        '% · 기준 밸류에이션 배수 ',
                                        round(assumption.base_multiple, 1),
                                        'x · ',
                                        assumption.driver_template_label,
                                        ' · ',
                                        assumption.calibration_method
                                    ),
                                'source_document_id', assumption.source_document_id,
                                'confidence', assumption.confidence,
                                'source_run_id', assumption.source_run_id
                            )
                            order by assumption.allocation_weight desc nulls last, assumption.segment_key
                        )
                        from reported_segment_assumption_rows assumption
                        where assumption.instrument_id = input.instrument_id
                    ),
                    '[]'::jsonb
                )
        ) as assumptions_json,
        case when coalesce(input.forecast_row_count, 0) >= 15 then 0.4500::numeric else 0.3500::numeric end as confidence
    from sotp_inputs input
    where coalesce(input.terminal_base_free_cash_flow, input.free_cash_flow) is not null
      and coalesce(input.terminal_base_free_cash_flow, input.free_cash_flow) > 0
    union all
    select
        input.instrument_id,
        'balance_sheet_adjustment'::text as component_key,
        '재무상태 조정'::text as component_label,
        'balance_sheet_adjustment'::text as component_type,
        ((input.book_equity / input.shares_outstanding) * 0.0500::numeric) as fair_value_low,
        ((input.book_equity / input.shares_outstanding) * 0.1000::numeric) as fair_value_base,
        ((input.book_equity / input.shares_outstanding) * 0.1500::numeric) as fair_value_high,
        'book_equity_partial_credit'::text as valuation_basis,
        jsonb_build_object(
            'component_description', '현금/부채 세부 분해가 부족하므로 순자산의 일부만 보수적으로 반영한 조정이다.',
            'total_assets', input.total_assets,
            'total_liabilities', input.total_liabilities,
            'book_equity', input.book_equity,
            'shares_outstanding', input.shares_outstanding,
            'low_credit_ratio', 0.0500,
            'base_credit_ratio', 0.1000,
            'high_credit_ratio', 0.1500,
            'latest_raw_period_end', input.latest_raw_period_end
        ) as assumptions_json,
        0.3500::numeric as confidence
    from sotp_inputs input
    where input.book_equity is not null
    union all
    select
        input.instrument_id,
        'segment_data_gap_reserve'::text as component_key,
        '세그먼트 데이터 공백 차감'::text as component_label,
        'risk_reserve'::text as component_type,
        (input.base_price * -0.0500::numeric) as fair_value_low,
        (input.base_price * -0.0300::numeric) as fair_value_base,
        (input.base_price * -0.0100::numeric) as fair_value_high,
        'segment_data_gap_reserve'::text as valuation_basis,
        jsonb_build_object(
            'component_description', '보고 사업부 실적은 근거로 연결하되 사업부별 forecast·자본배분·multiple이 아직 없으므로 SOTP 과신을 막기 위한 reserve다.',
            'base_price', input.base_price,
            'price_date', input.price_date,
            'low_reserve_pct', -0.0500,
            'base_reserve_pct', -0.0300,
            'high_reserve_pct', -0.0100,
            'missing_segment_detail', coalesce(input.reported_segment_metric_count, 0) = 0,
            'segment_footnote_evidence_source', 'research.segment_footnote_evidence',
            'latest_segment_evidence_as_of_date', input.latest_segment_evidence_as_of_date,
            'segment_evidence_count', coalesce(input.segment_evidence_count, 0),
            'reported_segment_metric_count', coalesce(input.reported_segment_metric_count, 0),
            'segment_data_gap_count', coalesce(input.segment_data_gap_count, 0),
            'reported_segment_input_count', coalesce(input.reported_segment_input_count, 0),
            'latest_reported_segment_period_end', input.latest_reported_segment_period_end,
            'reported_segment_revenue_total', input.reported_segment_revenue_total,
            'reported_segment_operating_income_total', input.reported_segment_operating_income_total,
            'reported_segment_confidence', input.reported_segment_confidence,
            'reported_segment_inputs', coalesce(input.reported_segment_inputs_json, '[]'::jsonb),
            'segment_evidence', coalesce(input.segment_evidence_json, '[]'::jsonb)
        ) as assumptions_json,
        0.5000::numeric as confidence
    from sotp_inputs input
),
upsert_components as (
    insert into market.sum_of_parts_component (
        instrument_id,
        as_of_date,
        statement_scope,
        component_key,
        component_label,
        component_type,
        fair_value_low,
        fair_value_base,
        fair_value_high,
        valuation_basis,
        assumptions_json,
        confidence,
        source_run_id
    )
    select
        instrument_id,
        {sql_date(as_of_date)},
        {sql_literal(statement_scope)},
        component_key,
        component_label,
        component_type,
        fair_value_low,
        fair_value_base,
        fair_value_high,
        valuation_basis,
        assumptions_json,
        confidence,
        {int(source_run_id)}::bigint
    from component_rows
    on conflict (instrument_id, as_of_date, statement_scope, component_key) do update
    set
        component_label = excluded.component_label,
        component_type = excluded.component_type,
        fair_value_low = excluded.fair_value_low,
        fair_value_base = excluded.fair_value_base,
        fair_value_high = excluded.fair_value_high,
        valuation_basis = excluded.valuation_basis,
        assumptions_json = excluded.assumptions_json,
        confidence = excluded.confidence,
        source_run_id = excluded.source_run_id
    returning component_type, component_key, confidence
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'source_run_id', {int(source_run_id)},
    'statement_scope', {sql_literal(statement_scope)},
    'component_row_count', (select count(*)::integer from upsert_components),
    'component_type_counts',
        coalesce(
            (
                select json_object_agg(component_type, component_count order by component_type)
                from (
                    select component_type, count(*)::integer as component_count
                    from upsert_components
                    group by component_type
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
            from upsert_components
        )
)::text;"""


def load_sum_of_parts_valuation_preview(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    statement_scope: str = "annual",
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_sum_of_parts_valuation_preview_sql(as_of_date=as_of_date, statement_scope=statement_scope)
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Sum-of-the-parts valuation preview did not return a JSON object.")
    return payload


def run_sum_of_parts_valuation(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    statement_scope: str = "annual",
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    preview = load_sum_of_parts_valuation_preview(
        config=config,
        as_of_date=as_of_date,
        statement_scope=statement_scope,
        executor=sql_executor,
    )
    report: dict[str, object] = {
        "report_name": "sum_of_parts_valuation",
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_SOTP_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "statement_scope": statement_scope,
        "model_name": DEFAULT_SOTP_MODEL_NAME,
        "component_types": list(SOTP_COMPONENT_TYPES),
        "preview": preview,
        "recommendation_scoring_mutated": False,
    }
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_SOTP_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "statement_scope": statement_scope,
            "model_name": DEFAULT_SOTP_MODEL_NAME,
            "component_types": list(SOTP_COMPONENT_TYPES),
            "recommendation_scoring_mutated": False,
        },
    )
    try:
        upsert_summary = json.loads(
            sql_executor.execute_scalar(
                render_sum_of_parts_valuation_upsert_sql(
                    as_of_date=as_of_date,
                    source_run_id=run_id,
                    statement_scope=statement_scope,
                )
            )
        )
        if not isinstance(upsert_summary, dict):
            raise ValueError("Sum-of-the-parts valuation upsert did not return a JSON object.")
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
latest_sotp_components as (
    select distinct on (component.instrument_id, component.component_key)
        component.component_id,
        component.instrument_id,
        component.as_of_date,
        component.statement_scope,
        component.component_key,
        component.component_type,
        component.fair_value_low,
        component.fair_value_base,
        component.fair_value_high,
        component.confidence,
        component.source_run_id
    from market.sum_of_parts_component component
    where component.as_of_date <= {sql_date(as_of_date)}
      and component.statement_scope = {sql_literal(statement_scope)}
    order by
        component.instrument_id,
        component.component_key,
        component.as_of_date desc,
        component.component_id desc
),
sotp_inputs as (
    select
        instrument_id,
        count(*)::integer as sotp_component_count
    from latest_sotp_components
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
        forecast.forecast_row_count,
        sotp.sotp_component_count
    from latest_prices price
    left join raw_inputs raw on raw.instrument_id = price.instrument_id
    left join normalized_inputs normalized on normalized.instrument_id = price.instrument_id
    left join peer_inputs peer on peer.instrument_id = price.instrument_id
    left join forecast_inputs forecast on forecast.instrument_id = price.instrument_id
    left join sotp_inputs sotp on sotp.instrument_id = price.instrument_id
    where raw.instrument_id is not null
       or normalized.instrument_id is not null
       or peer.instrument_id is not null
       or forecast.instrument_id is not null
       or sotp.instrument_id is not null
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
    'sum_of_parts_component_count', (select count(*)::integer from latest_sotp_components),
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
latest_sotp_components as (
    select distinct on (component.instrument_id, component.component_key)
        component.component_id,
        component.instrument_id,
        component.as_of_date,
        component.statement_scope,
        component.component_key,
        component.component_label,
        component.component_type,
        component.fair_value_low,
        component.fair_value_base,
        component.fair_value_high,
        component.valuation_basis,
        component.assumptions_json,
        component.confidence,
        component.source_run_id
    from market.sum_of_parts_component component
    where component.as_of_date <= {sql_date(as_of_date)}
      and component.statement_scope = {sql_literal(statement_scope)}
    order by
        component.instrument_id,
        component.component_key,
        component.as_of_date desc,
        component.component_id desc
),
sotp_inputs as (
    select
        instrument_id,
        count(*)::integer as sotp_component_count,
        max(as_of_date) as latest_sotp_as_of_date,
        sum(fair_value_low) as sotp_fair_value_low,
        sum(fair_value_base) as sotp_fair_value_base,
        sum(fair_value_high) as sotp_fair_value_high,
        avg(confidence) as sotp_confidence,
        bool_or(component_type = 'operating_business') as has_operating_business_component,
        max(nullif(assumptions_json ->> 'latest_segment_evidence_as_of_date', '')) as latest_segment_evidence_as_of_date,
        max(nullif(assumptions_json ->> 'segment_evidence_count', '')::integer) as segment_evidence_count,
        max(nullif(assumptions_json ->> 'reported_segment_metric_count', '')::integer) as reported_segment_metric_count,
        max(nullif(assumptions_json ->> 'segment_data_gap_count', '')::integer) as segment_data_gap_count,
        max(nullif(assumptions_json ->> 'reported_segment_input_count', '')::integer) as reported_segment_input_count,
        max(nullif(assumptions_json ->> 'latest_reported_segment_period_end', '')) as latest_reported_segment_period_end,
        max(nullif(assumptions_json ->> 'reported_segment_revenue_total', '')::numeric) as reported_segment_revenue_total,
        max(nullif(assumptions_json ->> 'reported_segment_operating_income_total', '')::numeric) as reported_segment_operating_income_total,
        coalesce(
            (
                array_agg(assumptions_json -> 'reported_segment_inputs' order by as_of_date desc, component_id desc)
                filter (
                    where jsonb_typeof(assumptions_json -> 'reported_segment_inputs') = 'array'
                      and jsonb_array_length(assumptions_json -> 'reported_segment_inputs') > 0
                )
            )[1],
            '[]'::jsonb
        ) as reported_segment_inputs_json,
        max(nullif(assumptions_json ->> 'reported_segment_allocation_count', '')::integer) as reported_segment_allocation_count,
        coalesce(
            (
                array_agg(assumptions_json -> 'reported_segment_allocations' order by as_of_date desc, component_id desc)
                filter (
                    where jsonb_typeof(assumptions_json -> 'reported_segment_allocations') = 'array'
                      and jsonb_array_length(assumptions_json -> 'reported_segment_allocations') > 0
                )
            )[1],
            '[]'::jsonb
        ) as reported_segment_allocations_json,
        max(nullif(assumptions_json ->> 'reported_segment_assumption_count', '')::integer) as reported_segment_assumption_count,
        coalesce(
            (
                array_agg(assumptions_json -> 'reported_segment_assumptions' order by as_of_date desc, component_id desc)
                filter (
                    where jsonb_typeof(assumptions_json -> 'reported_segment_assumptions') = 'array'
                      and jsonb_array_length(assumptions_json -> 'reported_segment_assumptions') > 0
                )
            )[1],
            '[]'::jsonb
        ) as reported_segment_assumptions_json,
        jsonb_agg(
            jsonb_build_object(
                'component_key', component_key,
                'component_label', component_label,
                'component_type', component_type,
                'fair_value_low', fair_value_low,
                'fair_value_base', fair_value_base,
                'fair_value_high', fair_value_high,
                'valuation_basis', valuation_basis,
                'assumptions', assumptions_json,
                'confidence', confidence,
                'source_run_id', source_run_id
            )
            order by
                case component_type
                    when 'operating_business' then 1
                    when 'balance_sheet_adjustment' then 2
                    when 'risk_reserve' then 3
                    else 9
                end,
                component_key
        ) as components_json
    from latest_sotp_components
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
        sotp.latest_sotp_as_of_date,
        sotp.sotp_component_count,
        sotp.sotp_fair_value_low,
        sotp.sotp_fair_value_base,
        sotp.sotp_fair_value_high,
        sotp.sotp_confidence,
        sotp.has_operating_business_component,
        sotp.latest_segment_evidence_as_of_date,
        sotp.segment_evidence_count,
        sotp.reported_segment_metric_count,
        sotp.segment_data_gap_count,
        sotp.reported_segment_input_count,
        sotp.latest_reported_segment_period_end,
        sotp.reported_segment_revenue_total,
        sotp.reported_segment_operating_income_total,
        sotp.reported_segment_inputs_json,
        sotp.reported_segment_allocation_count,
        sotp.reported_segment_allocations_json,
        sotp.reported_segment_assumption_count,
        sotp.reported_segment_assumptions_json,
        sotp.components_json,
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
    left join sotp_inputs sotp on sotp.instrument_id = price.instrument_id
    where price.base_price > 0
      and (
        raw.instrument_id is not null
        or normalized.instrument_id is not null
        or peer.instrument_id is not null
        or forecast.instrument_id is not null
        or sotp.instrument_id is not null
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
sum_of_parts_rows as (
    select
        input.instrument_id,
        'sum_of_parts' as method,
        input.base_price,
        input.sotp_fair_value_low as fair_value_low,
        input.sotp_fair_value_base as fair_value_base,
        input.sotp_fair_value_high as fair_value_high,
        json_build_object(
            'model_family', 'sum_of_parts',
            'method_description', 'Conservative SOTP proxy that separates operating business value, balance-sheet adjustment, and segment data-gap reserve.',
            'pricing_basis', 'latest adjusted close',
            'sensitivity_basis', 'component low/base/high cases',
            'statement_scope', {sql_literal(statement_scope)},
            'price_date', input.price_date,
            'latest_sotp_as_of_date', input.latest_sotp_as_of_date,
            'sotp_component_source', 'market.sum_of_parts_component',
            'sotp_component_count', coalesce(input.sotp_component_count, 0),
            'segment_footnote_evidence_source', 'research.segment_footnote_evidence',
            'latest_segment_evidence_as_of_date', input.latest_segment_evidence_as_of_date,
            'segment_evidence_count', coalesce(input.segment_evidence_count, 0),
            'reported_segment_metric_count', coalesce(input.reported_segment_metric_count, 0),
            'segment_data_gap_count', coalesce(input.segment_data_gap_count, 0),
            'reported_segment_input_count', coalesce(input.reported_segment_input_count, 0),
            'latest_reported_segment_period_end', input.latest_reported_segment_period_end,
            'reported_segment_revenue_total', input.reported_segment_revenue_total,
            'reported_segment_operating_income_total', input.reported_segment_operating_income_total,
            'reported_segment_inputs', coalesce(input.reported_segment_inputs_json, '[]'::jsonb),
            'reported_segment_allocation_count', coalesce(input.reported_segment_allocation_count, 0),
            'reported_segment_allocations', coalesce(input.reported_segment_allocations_json, '[]'::jsonb),
            'reported_segment_assumption_count', coalesce(input.reported_segment_assumption_count, 0),
            'reported_segment_assumptions', coalesce(input.reported_segment_assumptions_json, '[]'::jsonb),
            'sotp_components', coalesce(input.components_json, '[]'::jsonb),
            'has_operating_business_component', coalesce(input.has_operating_business_component, false),
            'key_variables', json_build_array('sotp_components', 'reported_segment_inputs', 'reported_segment_assumptions', 'operating_business_fcf', 'balance_sheet_adjustment', 'segment_data_gap_reserve'),
            'data_quality', json_build_object(
                'component_count', coalesce(input.sotp_component_count, 0),
                'has_operating_business_component', coalesce(input.has_operating_business_component, false),
                'segment_evidence_count', coalesce(input.segment_evidence_count, 0),
                'reported_segment_metric_count', coalesce(input.reported_segment_metric_count, 0),
                'reported_segment_input_count', coalesce(input.reported_segment_input_count, 0),
                'reported_segment_allocation_count', coalesce(input.reported_segment_allocation_count, 0),
                'reported_segment_assumption_count', coalesce(input.reported_segment_assumption_count, 0),
                'segment_data_gap_count', coalesce(input.segment_data_gap_count, 0),
                'latest_sotp_as_of_date', input.latest_sotp_as_of_date
            ),
            'limitations', json_build_array(
                '사업부별 성장률·마진·밸류에이션 배수는 SEC segment 실적과 allocation share에서 만든 보수적 proxy이며 segment DCF를 대체하지 않는다.',
                '세그먼트 forecast·CAPEX·자본배분 공백 reserve를 차감해 과신을 줄이지만, 완전한 sell-side SOTP를 대체하지 않는다.'
            ),
            'recommendation_scoring_mutated', false
        )::jsonb as assumptions_json,
        least(0.5000::numeric, greatest(0.2000::numeric, coalesce(input.sotp_confidence, 0.2500::numeric))) as confidence
    from valuation_inputs input
    where coalesce(input.sotp_component_count, 0) > 0
      and coalesce(input.has_operating_business_component, false)
      and input.sotp_fair_value_base is not null
),
snapshot_rows as (
    select * from relative_multiple_rows
    union all
    select * from scenario_range_rows
    union all
    select * from dcf_lite_rows
    union all
    select * from sum_of_parts_rows
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


def extract_reported_segment_metrics_from_html(
    html_text: str,
    *,
    instrument_id: int,
    primary_symbol: str,
    as_of_date: date,
    statement_scope: str,
    period_end: date,
    source_document_id: int,
    source_document_title: str | None = None,
    source_document_url: str | None = None,
) -> list[ReportedSegmentMetricEvidence]:
    rows: list[ReportedSegmentMetricEvidence] = []
    seen: set[tuple[str, str]] = set()
    for table_index, table_context in enumerate(_extract_html_table_contexts(html_text), start=1):
        table_html = table_context.table_html
        table_rows = _extract_html_table_rows(table_html)
        if len(table_rows) < 2:
            continue
        rows.extend(
            _extract_multiyear_segment_block_metrics(
                table_rows,
                table_html,
                table_index=table_index,
                seen=seen,
                instrument_id=instrument_id,
                primary_symbol=primary_symbol,
                as_of_date=as_of_date,
                statement_scope=statement_scope,
                period_end=period_end,
                source_document_id=source_document_id,
                source_document_title=source_document_title,
                source_document_url=source_document_url,
                unit_context_text=table_context.context_text,
            )
        )
        rows.extend(
            _extract_transposed_reported_segment_metrics(
                table_rows,
                table_html,
                table_index=table_index,
                seen=seen,
                instrument_id=instrument_id,
                primary_symbol=primary_symbol,
                as_of_date=as_of_date,
                statement_scope=statement_scope,
                period_end=period_end,
                source_document_id=source_document_id,
                source_document_title=source_document_title,
                source_document_url=source_document_url,
                unit_context_text=table_context.context_text,
            )
        )
        header_index = _find_segment_table_header_index(table_rows)
        if header_index is None:
            continue
        headers = table_rows[header_index]
        metric_columns = {
            index: metric_code
            for index, header in enumerate(headers)
            if index > 0
            for metric_code in [_metric_code_from_segment_header(header)]
            if metric_code is not None
        }
        if not metric_columns:
            continue
        unit = _infer_segment_metric_unit(table_context.context_text)
        for row in table_rows[header_index + 1 :]:
            if len(row) < 2:
                continue
            segment_label = _clean_segment_label(row[0])
            if segment_label is None:
                continue
            segment_key = _segment_key(segment_label)
            if not segment_key:
                continue
            for index, metric_code in metric_columns.items():
                if index >= len(row):
                    continue
                value = _parse_segment_metric_value(row[index])
                if value is None:
                    continue
                dedupe_key = (segment_key, metric_code)
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                rows.append(
                    _reported_segment_metric_evidence(
                        instrument_id=instrument_id,
                        primary_symbol=primary_symbol,
                        as_of_date=as_of_date,
                        statement_scope=statement_scope,
                        segment_key=segment_key,
                        segment_label=segment_label,
                        metric_code=metric_code,
                        metric_value=value,
                        metric_unit=unit,
                        period_end=period_end,
                        source_document_id=source_document_id,
                        source_document_title=source_document_title,
                        source_document_url=source_document_url,
                        table_index=table_index,
                        header_cells=headers,
                        parser_layout="segment_label_rows",
                    )
                )
    return rows


def _extract_multiyear_segment_block_metrics(
    table_rows: list[list[str]],
    table_html: str,
    *,
    table_index: int,
    seen: set[tuple[str, str]],
    instrument_id: int,
    primary_symbol: str,
    as_of_date: date,
    statement_scope: str,
    period_end: date,
    source_document_id: int,
    source_document_title: str | None,
    source_document_url: str | None,
    unit_context_text: str,
) -> list[ReportedSegmentMetricEvidence]:
    header_index, years = _find_multiyear_segment_block_header(table_rows)
    if header_index is None or period_end.year not in years:
        return []
    target_year_index = years.index(period_end.year)
    unit = _infer_segment_metric_unit(unit_context_text or table_html)
    rows: list[ReportedSegmentMetricEvidence] = []
    current_segment_label: str | None = None
    for row in table_rows[header_index + 1 :]:
        if not row:
            continue
        segment_label = _segment_block_label(row)
        if segment_label is not None:
            current_segment_label = segment_label
            continue
        if current_segment_label is None:
            continue
        metric_code = _metric_code_from_segment_header(row[0])
        if metric_code not in {"segment_revenue", "segment_operating_income"}:
            continue
        value_cells = _numeric_metric_cells(row[1:])
        if target_year_index >= len(value_cells):
            continue
        value = _parse_segment_metric_value(value_cells[target_year_index])
        if value is None:
            continue
        segment_key = _segment_key(current_segment_label)
        dedupe_key = (segment_key, metric_code)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        rows.append(
            _reported_segment_metric_evidence(
                instrument_id=instrument_id,
                primary_symbol=primary_symbol,
                as_of_date=as_of_date,
                statement_scope=statement_scope,
                segment_key=segment_key,
                segment_label=current_segment_label,
                metric_code=metric_code,
                metric_value=value,
                metric_unit=unit,
                period_end=period_end,
                source_document_id=source_document_id,
                source_document_title=source_document_title,
                source_document_url=source_document_url,
                table_index=table_index,
                header_cells=table_rows[header_index],
                parser_layout="multiyear_segment_block_rows",
            )
        )
    return rows


def _extract_transposed_reported_segment_metrics(
    table_rows: list[list[str]],
    table_html: str,
    *,
    table_index: int,
    seen: set[tuple[str, str]],
    instrument_id: int,
    primary_symbol: str,
    as_of_date: date,
    statement_scope: str,
    period_end: date,
    source_document_id: int,
    source_document_title: str | None,
    source_document_url: str | None,
    unit_context_text: str,
) -> list[ReportedSegmentMetricEvidence]:
    header_index = _find_transposed_segment_header_index(table_rows)
    if header_index is None:
        return []
    table_year = _transposed_segment_table_year(table_rows, header_index=header_index)
    if table_year is None:
        return []
    if table_year != period_end.year:
        return []
    segment_labels = [_clean_segment_label(cell) for cell in table_rows[header_index]]
    if sum(1 for label in segment_labels if label is not None) < 2:
        return []

    unit = _infer_segment_metric_unit(unit_context_text)
    rows: list[ReportedSegmentMetricEvidence] = []
    for row in table_rows[header_index + 1 :]:
        if len(row) < 2:
            continue
        metric_code = _metric_code_from_segment_header(row[0])
        if metric_code is None:
            continue
        value_cells = _transposed_metric_value_cells(row[1:])
        for index, segment_label in enumerate(segment_labels):
            if segment_label is None or index >= len(value_cells):
                continue
            value = _parse_segment_metric_value(value_cells[index])
            if value is None:
                continue
            segment_key = _segment_key(segment_label)
            dedupe_key = (segment_key, metric_code)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            rows.append(
                _reported_segment_metric_evidence(
                    instrument_id=instrument_id,
                    primary_symbol=primary_symbol,
                    as_of_date=as_of_date,
                    statement_scope=statement_scope,
                    segment_key=segment_key,
                    segment_label=segment_label,
                    metric_code=metric_code,
                    metric_value=value,
                    metric_unit=unit,
                    period_end=period_end,
                    source_document_id=source_document_id,
                    source_document_title=source_document_title,
                    source_document_url=source_document_url,
                    table_index=table_index,
                    header_cells=table_rows[header_index],
                    parser_layout="transposed_segment_metric_rows",
                )
            )
    return rows


def _reported_segment_metric_evidence(
    *,
    instrument_id: int,
    primary_symbol: str,
    as_of_date: date,
    statement_scope: str,
    segment_key: str,
    segment_label: str,
    metric_code: str,
    metric_value: Decimal,
    metric_unit: str,
    period_end: date,
    source_document_id: int,
    source_document_title: str | None,
    source_document_url: str | None,
    table_index: int,
    header_cells: list[str],
    parser_layout: str,
) -> ReportedSegmentMetricEvidence:
    return ReportedSegmentMetricEvidence(
        instrument_id=instrument_id,
        primary_symbol=primary_symbol,
        as_of_date=as_of_date,
        statement_scope=statement_scope,
        segment_key=segment_key,
        segment_label=segment_label,
        metric_code=metric_code,
        metric_value=metric_value,
        metric_unit=metric_unit,
        period_end=period_end,
        source_document_id=source_document_id,
        evidence_text=(
            f"{primary_symbol} reported {metric_code} for {segment_label} "
            f"parsed from SEC segment footnote table {table_index}."
        ),
        assumptions_json={
            "source": "sec_raw_filing_html_table",
            "parser_model": DEFAULT_REPORTED_SEGMENT_MODEL_NAME,
            "parser_layout": parser_layout,
            "primary_symbol": primary_symbol,
            "source_document_title": source_document_title,
            "source_document_url": source_document_url,
            "table_index": table_index,
            "header_cells": header_cells,
            "metric_unit": metric_unit,
            "metric_unit_label": _segment_metric_unit_label(metric_unit),
            "metric_unit_scale": _segment_metric_unit_scale(metric_unit),
            "interpretation": "SEC filing의 세그먼트/사업부 표에서 직접 파싱한 reported segment metric이다.",
            "recommendation_scoring_mutated": False,
        },
        confidence=Decimal("0.8200"),
    )


def _parse_reported_segment_candidate(
    candidate: dict[str, object],
    *,
    as_of_date: date,
    statement_scope: str,
) -> tuple[list[ReportedSegmentMetricEvidence], str | None]:
    raw_storage_uri = str(candidate.get("raw_storage_uri") or "")
    if not raw_storage_uri:
        return [], "missing_raw_storage_uri"
    artifact_path = _file_uri_to_path(raw_storage_uri)
    if artifact_path is None:
        return [], "unsupported_raw_storage_uri"
    if not artifact_path.exists():
        return [], "raw_artifact_missing"
    try:
        html_text = artifact_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [], "raw_artifact_unreadable"
    try:
        rows = extract_reported_segment_metrics_from_html(
            html_text,
            instrument_id=int(candidate["instrument_id"]),
            primary_symbol=str(candidate["primary_symbol"]),
            as_of_date=as_of_date,
            statement_scope=statement_scope,
            period_end=date.fromisoformat(str(candidate["period_end"])),
            source_document_id=int(candidate["source_document_id"]),
            source_document_title=(
                str(candidate["source_document_title"]) if candidate.get("source_document_title") is not None else None
            ),
            source_document_url=(
                str(candidate["source_document_url"]) if candidate.get("source_document_url") is not None else None
            ),
        )
        if not rows:
            return [], _single_reportable_segment_skip_reason(html_text) or "unsupported_segment_table_layout"
        return rows, None
    except (KeyError, TypeError, ValueError):
        return [], "candidate_payload_invalid"


def _render_reported_segment_metric_value_tuple(row: ReportedSegmentMetricEvidence) -> str:
    return (
        f"({int(row.instrument_id)}::bigint, "
        f"{sql_date(row.as_of_date)}, "
        f"{sql_literal(row.statement_scope)}::text, "
        f"{sql_literal(row.segment_key)}::text, "
        f"{sql_literal(row.segment_label)}::text, "
        "'reported_segment_metric'::text, "
        f"{sql_literal(row.metric_code)}::text, "
        f"{sql_literal(row.metric_value)}::numeric, "
        f"{sql_literal(row.metric_unit)}::text, "
        f"{sql_date(row.period_end)}, "
        f"{int(row.source_document_id)}::bigint, "
        f"{sql_literal(row.evidence_text)}::text, "
        f"{sql_literal(json.dumps(row.assumptions_json, ensure_ascii=False, sort_keys=True))}::jsonb, "
        f"{sql_literal(row.confidence)}::numeric)"
    )


def _extract_html_tables(html_text: str) -> list[str]:
    return re.findall(r"<table\b[^>]*>.*?</table>", html_text, flags=re.IGNORECASE | re.DOTALL)


def _extract_html_table_contexts(html_text: str, *, context_chars: int = 1600) -> list[HtmlTableContext]:
    contexts: list[HtmlTableContext] = []
    for match in re.finditer(r"<table\b[^>]*>.*?</table>", html_text, flags=re.IGNORECASE | re.DOTALL):
        context_start = max(0, match.start() - context_chars)
        context_end = min(len(html_text), match.end() + context_chars // 4)
        context_html = html_text[context_start:context_end]
        contexts.append(HtmlTableContext(table_html=match.group(0), context_text=_html_to_text(context_html)))
    return contexts


def _extract_html_table_rows(table_html: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for row_html in re.findall(r"<tr\b[^>]*>.*?</tr>", table_html, flags=re.IGNORECASE | re.DOTALL):
        cells = [
            _html_to_text(cell_html)
            for cell_html in re.findall(r"<t[dh]\b[^>]*>.*?</t[dh]>", row_html, flags=re.IGNORECASE | re.DOTALL)
        ]
        if any(cells):
            rows.append(cells)
    return rows


def _single_reportable_segment_skip_reason(html_text: str) -> str | None:
    if _ixbrl_single_count(html_text, "us-gaap:NumberOfOperatingSegments"):
        return "single_reportable_segment_no_disaggregated_segment_table"
    if _ixbrl_single_count(html_text, "us-gaap:NumberOfReportingUnits"):
        return "single_reportable_segment_no_disaggregated_segment_table"
    normalized_text = _html_to_text(html_text).lower()
    if re.search(r"\b(one|single)\s+(operating|reportable)\s+segment\b", normalized_text):
        return "single_reportable_segment_no_disaggregated_segment_table"
    if re.search(r"\boperates\s+as\s+(one|a single)\s+reportable\s+segment\b", normalized_text):
        return "single_reportable_segment_no_disaggregated_segment_table"
    return None


def _ixbrl_single_count(html_text: str, tag_name: str) -> bool:
    escaped_name = re.escape(tag_name)
    pattern = rf"<ix:nonFraction\b[^>]*\bname=[\"']{escaped_name}[\"'][^>]*>\s*1\s*</ix:nonFraction>"
    return re.search(pattern, html_text, flags=re.IGNORECASE | re.DOTALL) is not None


def _html_to_text(fragment: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", fragment)
    text = html.unescape(without_tags)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _find_segment_table_header_index(rows: list[list[str]]) -> int | None:
    for index, row in enumerate(rows[:6]):
        if len(row) < 2:
            continue
        first_cell = row[0].strip().lower()
        has_segment_label = any(token in first_cell for token in ("segment", "business", "product", "category"))
        has_metric = any(_metric_code_from_segment_header(cell) is not None for cell in row[1:])
        if has_segment_label and has_metric:
            return index
    return None


def _find_transposed_segment_header_index(rows: list[list[str]]) -> int | None:
    for index, row in enumerate(rows[:8]):
        if len(row) < 2:
            continue
        segment_label_count = sum(1 for cell in row if _clean_segment_label(cell) is not None)
        if segment_label_count < 2:
            continue
        if any(_metric_code_from_segment_header(cell) is not None for cell in row):
            continue
        following_rows = rows[index + 1 : index + 7]
        if any(row and _metric_code_from_segment_header(row[0]) is not None for row in following_rows):
            return index
    return None


def _find_multiyear_segment_block_header(rows: list[list[str]]) -> tuple[int | None, list[int]]:
    for index, row in enumerate(rows[:10]):
        years = [int(cell.strip()) for cell in row if re.fullmatch(r"20\d{2}", cell.strip())]
        if len(years) < 2:
            continue
        following_rows = rows[index + 1 : index + 20]
        has_segment_label = any(_segment_block_label(candidate) is not None for candidate in following_rows)
        has_operating_income_metric = any(
            candidate and _metric_code_from_segment_header(candidate[0]) == "segment_operating_income"
            for candidate in following_rows
        )
        if has_segment_label and has_operating_income_metric:
            return index, years
    return None, []


def _segment_block_label(row: list[str]) -> str | None:
    if len(row) != 1:
        return None
    raw_label = row[0].strip()
    if not raw_label.endswith(":"):
        return None
    return _clean_segment_label(raw_label)


def _numeric_metric_cells(cells: list[str]) -> list[str]:
    return [cell for cell in cells if not _is_currency_marker(cell) and _parse_segment_metric_value(cell) is not None]


def _transposed_segment_table_year(rows: list[list[str]], *, header_index: int) -> int | None:
    for row in reversed(rows[:header_index]):
        if len(row) != 1:
            continue
        match = re.search(r"\b(20\d{2})\b", row[0])
        if match is not None:
            return int(match.group(1))
    return None


def _transposed_metric_value_cells(cells: list[str]) -> list[str]:
    return [cell for cell in cells if not _is_currency_marker(cell)]


def _is_currency_marker(value: str) -> bool:
    normalized = value.strip()
    return normalized in {"$", "US$", "USD"}


def _metric_code_from_segment_header(header: str) -> str | None:
    normalized = re.sub(r"[^a-z0-9]+", " ", header.lower()).strip()
    if not normalized:
        return None
    if any(token in normalized for token in ("operating income", "operating profit", "income from operations")):
        return "segment_operating_income"
    if "gross profit" in normalized:
        return "segment_gross_profit"
    if "capital expenditure" in normalized or normalized in {"capex", "capital expenditures"}:
        return "segment_capex"
    if "total assets" in normalized or normalized == "assets":
        return "segment_assets"
    if any(token in normalized for token in ("net sales", "revenue", "sales")):
        return "segment_revenue"
    return None


def _infer_segment_metric_unit(table_html: str) -> str:
    normalized = _html_to_text(table_html).lower()
    if "in millions" in normalized or "millions" in normalized:
        return "USD_millions_as_reported"
    if "in thousands" in normalized or "thousands" in normalized:
        return "USD_thousands_as_reported"
    return "USD_as_reported"


def _segment_metric_unit_label(metric_unit: str) -> str:
    if metric_unit == "USD_millions_as_reported":
        return "백만 달러 단위"
    if metric_unit == "USD_thousands_as_reported":
        return "천 달러 단위"
    if metric_unit == "USD_as_reported":
        return "공시 보고 단위"
    return metric_unit


def _segment_metric_unit_scale(metric_unit: str) -> int | None:
    if metric_unit == "USD_millions_as_reported":
        return 1_000_000
    if metric_unit == "USD_thousands_as_reported":
        return 1_000
    return None


def _clean_segment_label(label: str) -> str | None:
    cleaned = re.sub(r"\s+", " ", label).strip(" :-")
    if not cleaned:
        return None
    normalized = cleaned.lower()
    if normalized == "change":
        return None
    if re.fullmatch(r"20\d{2}", normalized):
        return None
    if _looks_like_period_header(normalized):
        return None
    if normalized in {"total", "totals", "consolidated", "consolidated total", "company total"}:
        return None
    if normalized in {"corporate", "corporate total"}:
        return None
    if normalized.startswith("corporate and"):
        return None
    if normalized in {
        "net sales",
        "revenue",
        "sales",
        "deferred tax assets",
        "deferred tax liabilities",
        "deferred tax assets and liabilities",
        "deferred revenue",
    }:
        return None
    if "total net sales" in normalized or "total revenue" in normalized:
        return None
    return cleaned[:120]


def _looks_like_period_header(normalized_label: str) -> bool:
    if any(month in normalized_label for month in _MONTH_NAMES) and re.search(r"\b20\d{2}\b", normalized_label):
        return True
    if normalized_label.startswith(("year ended", "years ended", "period ended", "periods ended")):
        return True
    return False


_MONTH_NAMES = (
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
)


def _segment_key(label: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    return f"reported_{normalized}"[:120]


def _parse_segment_metric_value(value: str) -> Decimal | None:
    cleaned = value.replace("$", "").replace(",", "").strip()
    if not cleaned or cleaned in {"-", "—", "–"}:
        return None
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned.strip("()")
    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if match is None:
        return None
    try:
        parsed = Decimal(match.group(0))
    except InvalidOperation:
        return None
    return -parsed if negative else parsed


def _file_uri_to_path(raw_storage_uri: str) -> Path | None:
    parsed = urlparse(raw_storage_uri)
    if parsed.scheme != "file":
        return None
    if parsed.netloc not in {"", "localhost"}:
        return None
    return Path(unquote(parsed.path))


def _count_by_metric_code(rows: list[ReportedSegmentMetricEvidence]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.metric_code] = counts.get(row.metric_code, 0) + 1
    return dict(sorted(counts.items()))


def _validate_peer_relative_args(*, statement_scope: str, min_peer_count: int) -> None:
    if statement_scope not in PEER_RELATIVE_STATEMENT_SCOPES:
        raise ValueError(f"statement_scope must be one of: {', '.join(PEER_RELATIVE_STATEMENT_SCOPES)}.")
    if min_peer_count < 2:
        raise ValueError("min_peer_count must be at least 2.")


def _validate_valuation_args(*, statement_scope: str) -> None:
    if statement_scope not in VALUATION_STATEMENT_SCOPES:
        raise ValueError(f"statement_scope must be one of: {', '.join(VALUATION_STATEMENT_SCOPES)}.")


def _validate_positive_int(value: int, *, field_name: str) -> None:
    if value <= 0:
        raise ValueError(f"{field_name} must be greater than 0.")


def _statement_scope_filter(alias: str, *, statement_scope: str) -> str:
    if statement_scope == "all":
        return ""
    return f"\n      and {alias}.statement_scope = {sql_literal(statement_scope)}"
