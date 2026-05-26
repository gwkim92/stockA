from __future__ import annotations

import json
from datetime import date
from typing import Any

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.ingest.sec.companyfacts import run_sec_companyfacts_upsert
from stockanalysis.ingest.sec.raw_fetch import run_sec_filing_raw_fetch
from stockanalysis.ingest.sec.upsert import run_sec_filings_upsert
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_PIPELINE_NAME = "financial_period_source_linkage"
DEFAULT_MODEL_NAME = "deterministic-financial-period-source-linkage-sql-v1"
DEFAULT_SOURCE_LINKAGE_MAX_FILINGS = 200
SOURCE_LINKAGE_STATEMENT_SCOPES = ("annual", "quarterly", "all")


def render_financial_period_source_linkage_preview_sql(
    *,
    as_of_date: date,
    statement_scope: str = "annual",
    symbol: str | None = None,
) -> str:
    _validate_args(statement_scope=statement_scope, max_filings=1, raw_fetch_limit=0)
    return f"""-- financial period source linkage preview
with period_scope as (
    {_period_scope_select(as_of_date=as_of_date, statement_scope=statement_scope, symbol=symbol)}
),
sec_docs as (
    {_sec_docs_select()}
),
candidate_links as (
    {_candidate_links_select()}
),
raw_fetch_candidates as (
    select distinct doc.document_id
    from period_scope period
    join ingest.source_document doc on doc.document_id = period.source_document_id
    where doc.raw_storage_uri is null
),
post_backfill_raw_fetch_candidates as (
    select distinct link.document_id
    from candidate_links link
    join ingest.source_document doc on doc.document_id = link.document_id
    where doc.raw_storage_uri is null
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'model_name', {sql_literal(DEFAULT_MODEL_NAME)},
    'statement_scope', {sql_literal(statement_scope)},
    'symbol', {sql_literal(_normalize_symbol(symbol))},
    'source_period_count', (select count(*)::integer from period_scope),
    'linked_period_count', (select count(*)::integer from period_scope where source_document_id is not null),
    'unlinked_period_count', (select count(*)::integer from period_scope where source_document_id is null),
    'sec_source_document_count', (select count(*)::integer from sec_docs),
    'sec_raw_document_count', (select count(*)::integer from sec_docs where raw_storage_uri is not null),
    'link_candidate_count', (select count(*)::integer from candidate_links),
    'raw_fetch_candidate_count', (select count(*)::integer from raw_fetch_candidates),
    'post_backfill_raw_fetch_candidate_count', (select count(*)::integer from post_backfill_raw_fetch_candidates)
)::text;"""


def render_financial_period_source_linkage_backfill_sql(
    *,
    as_of_date: date,
    source_run_id: int,
    statement_scope: str = "annual",
    symbol: str | None = None,
) -> str:
    _validate_args(statement_scope=statement_scope, max_filings=1, raw_fetch_limit=0)
    return f"""-- financial period source linkage backfill
with period_scope as (
    {_period_scope_select(as_of_date=as_of_date, statement_scope=statement_scope, symbol=symbol)}
),
sec_docs as (
    {_sec_docs_select()}
),
candidate_links as (
    {_candidate_links_select()}
),
updated_periods as (
    update market.financial_statement_period period
    set source_document_id = candidate.document_id
    from candidate_links candidate
    where period.period_id = candidate.period_id
      and period.source_document_id is null
    returning
        period.period_id,
        period.instrument_id,
        candidate.primary_symbol,
        candidate.document_id,
        candidate.external_document_id,
        candidate.match_basis
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'source_run_id', {int(source_run_id)},
    'statement_scope', {sql_literal(statement_scope)},
    'symbol', {sql_literal(_normalize_symbol(symbol))},
    'linked_period_count', (select count(*)::integer from updated_periods),
    'linked_instrument_count', (select count(distinct instrument_id)::integer from updated_periods),
    'source_document_count', (select count(distinct document_id)::integer from updated_periods),
    'sample_links',
        coalesce(
            (
                select json_agg(
                    json_build_object(
                        'period_id', period_id,
                        'primary_symbol', primary_symbol,
                        'source_document_id', document_id,
                        'external_document_id', external_document_id,
                        'match_basis', match_basis
                    )
                    order by primary_symbol, period_id
                )
                from (
                    select *
                    from updated_periods
                    order by primary_symbol, period_id
                    limit 20
                ) sample
            ),
            '[]'::json
        ),
    'recommendation_scoring_mutated', false
)::text;"""


def render_financial_period_source_raw_fetch_candidates_sql(
    *,
    as_of_date: date,
    statement_scope: str = "annual",
    symbol: str | None = None,
    limit: int = 5,
) -> str:
    _validate_args(statement_scope=statement_scope, max_filings=1, raw_fetch_limit=limit)
    if limit <= 0:
        return "select '[]'::json::text;"
    return f"""-- financial period source raw fetch candidates
with period_scope as (
    {_period_scope_select(as_of_date=as_of_date, statement_scope=statement_scope, symbol=symbol)}
),
candidate_rows as (
    select distinct on (doc.document_id)
        doc.document_id,
        doc.external_document_id,
        doc.title,
        doc.url,
        period.primary_symbol,
        period.period_end,
        period.report_date
    from period_scope period
    join ingest.source_document doc on doc.document_id = period.source_document_id
    join ingest.data_source source on source.data_source_id = doc.data_source_id
    where source.source_name = 'sec_edgar'
      and doc.external_document_id is not null
      and doc.raw_storage_uri is null
    order by doc.document_id, period.period_end desc
    limit {int(limit)}
)
select coalesce(
    json_agg(
        json_build_object(
            'document_id', document_id,
            'external_document_id', external_document_id,
            'title', title,
            'url', url,
            'primary_symbol', primary_symbol,
            'period_end', period_end,
            'report_date', report_date
        )
        order by primary_symbol, period_end desc, document_id
    ),
    '[]'::json
)::text
from candidate_rows;"""


def load_financial_period_source_linkage_preview(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    statement_scope: str = "annual",
    symbol: str | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_financial_period_source_linkage_preview_sql(
                as_of_date=as_of_date,
                statement_scope=statement_scope,
                symbol=symbol,
            )
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Financial period source linkage preview did not return a JSON object.")
    return payload


def load_financial_period_source_raw_fetch_candidates(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    statement_scope: str = "annual",
    symbol: str | None = None,
    limit: int = 5,
    executor: PsqlCommandExecutor | None = None,
) -> list[dict[str, object]]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_financial_period_source_raw_fetch_candidates_sql(
                as_of_date=as_of_date,
                statement_scope=statement_scope,
                symbol=symbol,
                limit=limit,
            )
        )
    )
    if not isinstance(payload, list):
        raise ValueError("Financial period source raw fetch candidates query did not return a JSON array.")
    return [item for item in payload if isinstance(item, dict)]


def run_financial_period_source_linkage(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    statement_scope: str = "annual",
    cik: str | None = None,
    fallback_symbol: str | None = None,
    max_filings: int = DEFAULT_SOURCE_LINKAGE_MAX_FILINGS,
    raw_fetch_limit: int = 2,
    raw_artifact_root: str = "artifacts/raw",
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    _validate_args(statement_scope=statement_scope, max_filings=max_filings, raw_fetch_limit=raw_fetch_limit)
    normalized_cik = _normalize_cik(cik)
    normalized_symbol = _normalize_symbol(fallback_symbol)
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    preview = load_financial_period_source_linkage_preview(
        config=config,
        as_of_date=as_of_date,
        statement_scope=statement_scope,
        symbol=normalized_symbol,
        executor=sql_executor,
    )
    report: dict[str, object] = {
        "report_name": "financial_period_source_linkage",
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "statement_scope": statement_scope,
        "cik": normalized_cik,
        "fallback_symbol": normalized_symbol,
        "max_filings": max_filings,
        "raw_fetch_limit": raw_fetch_limit,
        "raw_artifact_root": raw_artifact_root,
        "model_name": DEFAULT_MODEL_NAME,
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
            "statement_scope": statement_scope,
            "cik": normalized_cik,
            "fallback_symbol": normalized_symbol,
            "max_filings": max_filings,
            "raw_fetch_limit": raw_fetch_limit,
            "raw_artifact_root": raw_artifact_root,
            "model_name": DEFAULT_MODEL_NAME,
            "recommendation_scoring_mutated": False,
        },
    )
    try:
        sec_filings_report: dict[str, object] | None = None
        companyfacts_report: dict[str, object] | None = None
        if normalized_cik is not None:
            sec_filings_report = run_sec_filings_upsert(
                normalized_cik,
                config=config,
                max_filings=max_filings,
                executor=sql_executor,
            )
            companyfacts_report = run_sec_companyfacts_upsert(
                normalized_cik,
                config=config,
                fallback_symbol=normalized_symbol,
                executor=sql_executor,
            )

        backfill_summary = json.loads(
            sql_executor.execute_scalar(
                render_financial_period_source_linkage_backfill_sql(
                    as_of_date=as_of_date,
                    statement_scope=statement_scope,
                    symbol=normalized_symbol,
                    source_run_id=run_id,
                )
            )
        )
        if not isinstance(backfill_summary, dict):
            raise ValueError("Financial period source linkage backfill did not return a JSON object.")

        raw_fetch_candidates = load_financial_period_source_raw_fetch_candidates(
            config=config,
            as_of_date=as_of_date,
            statement_scope=statement_scope,
            symbol=normalized_symbol,
            limit=raw_fetch_limit,
            executor=sql_executor,
        )
        raw_fetch_reports: list[dict[str, object]] = []
        failed_raw_fetch_reports: list[dict[str, object]] = []
        for candidate in raw_fetch_candidates:
            external_document_id = str(candidate.get("external_document_id") or "")
            if not external_document_id:
                continue
            try:
                raw_fetch_reports.append(
                    run_sec_filing_raw_fetch(
                        external_document_id,
                        config=config,
                        artifact_root=raw_artifact_root,
                        executor=sql_executor,
                    )
                )
            except Exception as exc:
                failed_raw_fetch_reports.append(
                    {
                        "external_document_id": external_document_id,
                        "primary_symbol": candidate.get("primary_symbol"),
                        "error_summary": str(exc)[:1000],
                    }
                )

        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return {
        **report,
        "status": "completed_with_raw_fetch_failures" if failed_raw_fetch_reports else "completed",
        "run_id": run_id,
        "sec_filings_report": sec_filings_report,
        "companyfacts_report": companyfacts_report,
        "backfill": backfill_summary,
        "raw_fetch_candidate_count": len(raw_fetch_candidates),
        "raw_fetch_success_count": len(raw_fetch_reports),
        "raw_fetch_failed_count": len(failed_raw_fetch_reports),
        "raw_fetch_reports": raw_fetch_reports,
        "failed_raw_fetch_reports": failed_raw_fetch_reports,
    }


def _period_scope_select(*, as_of_date: date, statement_scope: str, symbol: str | None) -> str:
    return f"""select
        period.period_id,
        period.instrument_id,
        instrument.primary_symbol,
        instrument.name as instrument_name,
        issuer.display_name as issuer_display_name,
        issuer.legal_name as issuer_legal_name,
        period.statement_scope,
        period.period_end,
        period.report_date,
        period.source_document_id
    from market.financial_statement_period period
    join ref.instrument instrument on instrument.instrument_id = period.instrument_id
    join ref.issuer issuer on issuer.issuer_id = instrument.issuer_id
    where period.period_end <= {sql_date(as_of_date)}
      {_statement_scope_filter('period', statement_scope)}
      {_symbol_filter('instrument', symbol)}"""


def _sec_docs_select() -> str:
    return """select
        doc.document_id,
        doc.external_document_id,
        doc.title,
        doc.summary,
        doc.url,
        doc.raw_storage_uri,
        (doc.published_at at time zone 'UTC')::date as filing_date,
        case
            when doc.title ilike '10-K%' or doc.summary ilike 'SEC 10-K%' then 'annual'
            when doc.title ilike '10-Q%' or doc.summary ilike 'SEC 10-Q%' then 'quarterly'
            else null::text
        end as document_statement_scope,
        lower(concat_ws(' ', doc.title, doc.summary, doc.url)) as search_text
    from ingest.source_document doc
    join ingest.data_source source on source.data_source_id = doc.data_source_id
    where source.source_name = 'sec_edgar'
      and doc.external_document_id is not null"""


def _candidate_links_select() -> str:
    return """select distinct on (period.period_id)
        period.period_id,
        period.instrument_id,
        period.primary_symbol,
        doc.document_id,
        doc.external_document_id,
        case
            when period.report_date is not null and doc.filing_date = period.report_date
            then 'report_date_form_company_text'
            else 'period_window_form_company_text'
        end as match_basis
    from period_scope period
    join sec_docs doc
      on doc.document_statement_scope = period.statement_scope
     and doc.filing_date is not null
     and (
         (period.report_date is not null and doc.filing_date = period.report_date)
         or doc.filing_date between period.period_end and (period.period_end + interval '180 days')::date
     )
     and (
         position(lower(period.issuer_display_name) in doc.search_text) > 0
         or position(lower(period.issuer_legal_name) in doc.search_text) > 0
         or position(lower(period.instrument_name) in doc.search_text) > 0
     )
    where period.source_document_id is null
    order by
        period.period_id,
        case when period.report_date is not null and doc.filing_date = period.report_date then 0 else 1 end,
        doc.filing_date desc,
        doc.document_id desc"""


def _statement_scope_filter(alias: str, statement_scope: str) -> str:
    if statement_scope == "all":
        return ""
    return f"and {alias}.statement_scope = {sql_literal(statement_scope)}"


def _symbol_filter(alias: str, symbol: str | None) -> str:
    normalized = _normalize_symbol(symbol)
    if normalized is None:
        return ""
    return f"and upper({alias}.primary_symbol) = {sql_literal(normalized)}"


def _validate_args(*, statement_scope: str, max_filings: int, raw_fetch_limit: int) -> None:
    if statement_scope not in SOURCE_LINKAGE_STATEMENT_SCOPES:
        raise ValueError(f"statement_scope must be one of: {', '.join(SOURCE_LINKAGE_STATEMENT_SCOPES)}.")
    if max_filings <= 0:
        raise ValueError("max_filings must be greater than 0.")
    if raw_fetch_limit < 0:
        raise ValueError("raw_fetch_limit must not be negative.")


def _normalize_cik(value: str | None) -> str | None:
    if value is None:
        return None
    digits = "".join(char for char in str(value).strip() if char.isdigit())
    return digits.zfill(10) if digits else None


def _normalize_symbol(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().upper()
    return normalized or None
