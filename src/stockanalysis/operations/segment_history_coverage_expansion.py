from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Iterable

from stockanalysis.frontend.live_adapter import DEFAULT_PORTFOLIO_NAME
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.market.universe import (
    MarketUniverseRecord,
    SelectedMarketUniverseRecord,
    load_market_universe_records,
    select_market_universe_records,
)
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.financial_period_source_linkage import DEFAULT_SOURCE_LINKAGE_MAX_FILINGS
from stockanalysis.operations.professional_equity_analysis import VALUATION_STATEMENT_SCOPES
from stockanalysis.operations.segment_history_backfill import (
    DEFAULT_SEGMENT_HISTORY_PERIODS_PER_INSTRUMENT,
    run_segment_history_backfill,
)
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_SEGMENT_HISTORY_COVERAGE_PIPELINE_NAME = "segment_history_coverage_expansion"
DEFAULT_SEGMENT_HISTORY_COVERAGE_MODEL_NAME = "deterministic-segment-history-coverage-expansion-v1"
BAD_REPORTED_SEGMENT_KEYS = (
    "reported_net_sales",
    "reported_deferred_tax_assets",
    "reported_deferred_tax_liabilities",
    "reported_deferred_tax_assets_and_liabilities",
    "reported_deferred_revenue",
)


@dataclass(frozen=True)
class SegmentHistoryCoverageCandidate:
    instrument_id: int
    primary_symbol: str
    source_kinds: tuple[str, ...]


@dataclass(frozen=True)
class ResolvedSegmentHistoryCoverageTarget:
    instrument_id: int
    primary_symbol: str
    cik: str
    company_name: str
    exchange_name: str
    source_kinds: tuple[str, ...]


def render_active_segment_history_coverage_targets_sql(
    *,
    as_of_date: date,
    portfolio_name: str,
    limit: int,
) -> str:
    _validate_limit(limit)
    target_date = sql_date(as_of_date)
    return f"""-- segment history coverage active targets
with active_recommendation_symbols as (
    select distinct
        instrument.instrument_id,
        instrument.primary_symbol,
        'active_recommendation'::text as source_kind
    from signal.recommendation recommendation
    join signal.recommendation_batch batch on batch.batch_id = recommendation.batch_id
    join ref.instrument instrument on instrument.instrument_id = recommendation.instrument_id
    where batch.as_of_date <= {target_date}
      and recommendation.status = 'active'
      and instrument.is_active = true
),
selected_portfolio as (
    select portfolio_id
    from portfolio.portfolio
    where portfolio_name = {sql_literal(portfolio_name)}
    limit 1
),
latest_portfolio_snapshot as (
    select max(position.snapshot_date) as snapshot_date
    from portfolio.position_snapshot position
    join selected_portfolio portfolio on portfolio.portfolio_id = position.portfolio_id
    where position.snapshot_date <= {target_date}
      and position.quantity <> 0
),
portfolio_symbols as (
    select distinct
        instrument.instrument_id,
        instrument.primary_symbol,
        'portfolio_holding'::text as source_kind
    from selected_portfolio portfolio
    join latest_portfolio_snapshot snapshot on snapshot.snapshot_date is not null
    join portfolio.position_snapshot position
      on position.portfolio_id = portfolio.portfolio_id
     and position.snapshot_date = snapshot.snapshot_date
    join ref.instrument instrument on instrument.instrument_id = position.instrument_id
    where position.quantity <> 0
      and instrument.is_active = true
),
unioned as (
    select * from active_recommendation_symbols
    union all
    select * from portfolio_symbols
),
grouped as (
    select
        instrument_id,
        primary_symbol,
        array_agg(distinct source_kind order by source_kind) as source_kinds
    from unioned
    group by instrument_id, primary_symbol
)
select coalesce(
    json_agg(
        json_build_object(
            'instrument_id', instrument_id,
            'primary_symbol', primary_symbol,
            'source_kinds', source_kinds
        )
        order by primary_symbol
    ),
    '[]'::json
)::text
from (
    select *
    from grouped
    order by primary_symbol
    limit {int(limit)}
) limited;"""


def render_segment_history_coverage_report_sql(
    *,
    as_of_date: date,
    statement_scope: str,
    periods_per_instrument: int,
    targets: tuple[ResolvedSegmentHistoryCoverageTarget, ...],
) -> str:
    _validate_statement_scope(statement_scope)
    _validate_periods_per_instrument(periods_per_instrument)
    if not targets:
        return "select '[]'::json::text;"
    value_rows = ",\n        ".join(_render_target_value_tuple(target) for target in targets)
    return f"""-- segment history coverage report
with target_rows(
    instrument_id,
    primary_symbol,
    cik,
    company_name,
    exchange_name,
    source_kinds
) as (
    values
        {value_rows}
),
ranked_periods as (
    select
        period.instrument_id,
        period.period_id,
        period.period_end,
        period.source_document_id,
        doc.raw_storage_uri,
        row_number() over (
            partition by period.instrument_id
            order by period.period_end desc, period.period_id desc
        ) as period_rank
    from market.financial_statement_period period
    join target_rows target on target.instrument_id = period.instrument_id
    left join ingest.source_document doc on doc.document_id = period.source_document_id
    where period.period_end <= {sql_date(as_of_date)}
      and period.statement_scope = {sql_literal(statement_scope)}
),
bounded_periods as (
    select *
    from ranked_periods
    where period_rank <= {int(periods_per_instrument)}
),
parsed_evidence as (
    select
        evidence.instrument_id,
        evidence.period_end,
        evidence.segment_key,
        evidence.segment_label,
        evidence.metric_code
    from research.segment_footnote_evidence evidence
    join target_rows target on target.instrument_id = evidence.instrument_id
    where evidence.as_of_date <= {sql_date(as_of_date)}
      and evidence.statement_scope = {sql_literal(statement_scope)}
      and evidence.evidence_type = 'reported_segment_metric'
),
latest_sotp as (
    select distinct on (component.instrument_id)
        component.instrument_id,
        component.assumptions_json
    from market.sum_of_parts_component component
    join target_rows target on target.instrument_id = component.instrument_id
    where component.as_of_date <= {sql_date(as_of_date)}
      and component.statement_scope = {sql_literal(statement_scope)}
      and component.component_key = 'operating_business_fcf'
    order by component.instrument_id, component.as_of_date desc, component.component_id desc
),
assumption_rows as (
    select
        latest_sotp.instrument_id,
        assumption.value as assumption_json
    from latest_sotp
    cross join lateral jsonb_array_elements(
        case
            when jsonb_typeof(latest_sotp.assumptions_json -> 'reported_segment_assumptions') = 'array'
            then latest_sotp.assumptions_json -> 'reported_segment_assumptions'
            else '[]'::jsonb
        end
    ) assumption(value)
),
coverage_rows as (
    select
        target.instrument_id,
        target.primary_symbol,
        target.cik,
        target.company_name,
        target.exchange_name,
        target.source_kinds,
        coalesce((select count(*)::integer from bounded_periods period where period.instrument_id = target.instrument_id), 0) as bounded_period_count,
        coalesce((select count(*)::integer from bounded_periods period where period.instrument_id = target.instrument_id and period.source_document_id is not null), 0) as source_document_period_count,
        coalesce((select count(*)::integer from bounded_periods period where period.instrument_id = target.instrument_id and period.raw_storage_uri is not null), 0) as raw_document_period_count,
        coalesce((select count(distinct evidence.period_end)::integer from parsed_evidence evidence where evidence.instrument_id = target.instrument_id), 0) as parsed_period_count,
        coalesce((select count(distinct evidence.segment_key)::integer from parsed_evidence evidence where evidence.instrument_id = target.instrument_id), 0) as parsed_segment_count,
        coalesce((select count(*)::integer from parsed_evidence evidence where evidence.instrument_id = target.instrument_id), 0) as parsed_metric_count,
        coalesce((select count(*)::integer from parsed_evidence evidence where evidence.instrument_id = target.instrument_id and evidence.segment_key in ({_bad_key_literals()})), 0) as bad_segment_count,
        coalesce((select count(*)::integer from assumption_rows assumption where assumption.instrument_id = target.instrument_id), 0) as assumption_count,
        coalesce((
            select count(*)::integer
            from assumption_rows assumption
            where assumption.instrument_id = target.instrument_id
              and assumption.assumption_json ->> 'calibration_method' = 'multi_period_segment_trend_template'
        ), 0) as trend_backed_assumption_count,
        coalesce((
            select max(nullif(assumption.assumption_json ->> 'history_period_count', '')::integer)
            from assumption_rows assumption
            where assumption.instrument_id = target.instrument_id
        ), 0) as max_history_period_count
    from target_rows target
)
select coalesce(
    json_agg(
        json_build_object(
            'instrument_id', instrument_id,
            'symbol', primary_symbol,
            'cik', cik,
            'company_name', company_name,
            'exchange_name', exchange_name,
            'source_kinds', source_kinds,
            'bounded_period_count', bounded_period_count,
            'source_document_period_count', source_document_period_count,
            'raw_document_period_count', raw_document_period_count,
            'parsed_period_count', parsed_period_count,
            'parsed_segment_count', parsed_segment_count,
            'parsed_metric_count', parsed_metric_count,
            'bad_segment_count', bad_segment_count,
            'assumption_count', assumption_count,
            'trend_backed_assumption_count', trend_backed_assumption_count,
            'max_history_period_count', max_history_period_count,
            'unsupported_candidate_count', greatest(raw_document_period_count - parsed_period_count, 0),
            'single_period_fallback', parsed_period_count = 1 or max_history_period_count = 1,
            'coverage_status',
                case
                    when bad_segment_count > 0 then 'contaminated_segment_labels'
                    when trend_backed_assumption_count > 0 and max_history_period_count >= 2 then 'trend_backed'
                    when parsed_period_count = 1 then 'single_period_fallback'
                    when raw_document_period_count > 0 and parsed_period_count = 0 then 'unsupported_layout'
                    when source_document_period_count = 0 then 'missing_source_document_linkage'
                    when raw_document_period_count = 0 then 'missing_raw_sec_artifact'
                    else 'insufficient_segment_history'
                end
        )
        order by primary_symbol
    ),
    '[]'::json
)::text
from coverage_rows;"""


def load_active_segment_history_coverage_candidates(
    *,
    executor: PsqlCommandExecutor,
    as_of_date: date,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
    limit: int = 25,
) -> tuple[SegmentHistoryCoverageCandidate, ...]:
    payload_text = executor.execute_scalar(
        render_active_segment_history_coverage_targets_sql(
            as_of_date=as_of_date,
            portfolio_name=portfolio_name,
            limit=limit,
        )
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Segment history coverage target lookup did not return a JSON array.")
    candidates: list[SegmentHistoryCoverageCandidate] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("primary_symbol") or "").strip().upper()
        if not symbol:
            continue
        candidates.append(
            SegmentHistoryCoverageCandidate(
                instrument_id=int(item["instrument_id"]),
                primary_symbol=symbol,
                source_kinds=_string_tuple(item.get("source_kinds")),
            )
        )
    return tuple(candidates)


def resolve_segment_history_coverage_targets(
    candidates: Iterable[SegmentHistoryCoverageCandidate],
    *,
    company_ticker_records: tuple[MarketUniverseRecord, ...],
    exchanges: list[str] | None = None,
) -> tuple[ResolvedSegmentHistoryCoverageTarget, ...]:
    candidate_by_symbol = {candidate.primary_symbol: candidate for candidate in candidates}
    if not candidate_by_symbol:
        return tuple()
    selection = select_market_universe_records(company_ticker_records, exchanges=exchanges)
    selected_by_symbol: dict[str, SelectedMarketUniverseRecord] = {}
    for record in selection.records:
        if record.symbol in candidate_by_symbol and record.symbol not in selected_by_symbol:
            selected_by_symbol[record.symbol] = record

    targets: list[ResolvedSegmentHistoryCoverageTarget] = []
    for symbol in sorted(selected_by_symbol):
        record = selected_by_symbol[symbol]
        candidate = candidate_by_symbol[symbol]
        targets.append(
            ResolvedSegmentHistoryCoverageTarget(
                instrument_id=candidate.instrument_id,
                primary_symbol=symbol,
                cik=record.cik,
                company_name=record.company_name,
                exchange_name=record.exchange_name,
                source_kinds=candidate.source_kinds,
            )
        )
    return tuple(targets)


def load_segment_history_coverage_report(
    *,
    executor: PsqlCommandExecutor,
    as_of_date: date,
    statement_scope: str,
    periods_per_instrument: int,
    targets: tuple[ResolvedSegmentHistoryCoverageTarget, ...],
) -> list[dict[str, object]]:
    payload_text = executor.execute_scalar(
        render_segment_history_coverage_report_sql(
            as_of_date=as_of_date,
            statement_scope=statement_scope,
            periods_per_instrument=periods_per_instrument,
            targets=targets,
        )
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Segment history coverage report query did not return a JSON array.")
    return [item for item in payload if isinstance(item, dict)]


def run_segment_history_coverage_expansion(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
    statement_scope: str = "annual",
    limit: int = 25,
    target_limit: int = 5,
    max_filings: int = DEFAULT_SOURCE_LINKAGE_MAX_FILINGS,
    raw_fetch_limit: int | None = None,
    raw_artifact_root: str = "artifacts/raw",
    periods_per_instrument: int = DEFAULT_SEGMENT_HISTORY_PERIODS_PER_INSTRUMENT,
    company_tickers_json_path: str | None = None,
    exchanges: list[str] | None = None,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    _validate_statement_scope(statement_scope)
    _validate_limit(limit)
    _validate_limit(target_limit)
    _validate_periods_per_instrument(periods_per_instrument)
    if target_limit > limit:
        raise ValueError("target_limit must be less than or equal to limit.")
    resolved_raw_fetch_limit = periods_per_instrument if raw_fetch_limit is None else raw_fetch_limit
    if resolved_raw_fetch_limit <= 0:
        raise ValueError("raw_fetch_limit must be greater than 0.")
    if max_filings <= 0:
        raise ValueError("max_filings must be greater than 0.")

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    candidates = load_active_segment_history_coverage_candidates(
        executor=sql_executor,
        as_of_date=as_of_date,
        portfolio_name=portfolio_name,
        limit=limit,
    )
    if candidates:
        records = load_market_universe_records(config=config, company_tickers_json_path=company_tickers_json_path)
        targets = resolve_segment_history_coverage_targets(candidates, company_ticker_records=records, exchanges=exchanges)
    else:
        targets = tuple()
    selected_targets = targets[:target_limit]
    unmatched_symbols = sorted({candidate.primary_symbol for candidate in candidates} - {target.primary_symbol for target in targets})
    coverage_before = load_segment_history_coverage_report(
        executor=sql_executor,
        as_of_date=as_of_date,
        statement_scope=statement_scope,
        periods_per_instrument=periods_per_instrument,
        targets=selected_targets,
    )

    base_report: dict[str, object] = {
        "report_name": DEFAULT_SEGMENT_HISTORY_COVERAGE_PIPELINE_NAME,
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_SEGMENT_HISTORY_COVERAGE_PIPELINE_NAME,
        "model_name": DEFAULT_SEGMENT_HISTORY_COVERAGE_MODEL_NAME,
        "as_of_date": as_of_date.isoformat(),
        "portfolio_name": portfolio_name,
        "statement_scope": statement_scope,
        "limit": limit,
        "target_limit": target_limit,
        "max_filings": max_filings,
        "raw_fetch_limit": resolved_raw_fetch_limit,
        "raw_artifact_root": raw_artifact_root,
        "periods_per_instrument": periods_per_instrument,
        "candidate_symbol_count": len(candidates),
        "resolved_target_count": len(targets),
        "selected_target_count": len(selected_targets),
        "candidate_symbols": [candidate.primary_symbol for candidate in candidates],
        "selected_targets": [_target_payload(target) for target in selected_targets],
        "unmatched_symbols": unmatched_symbols,
        "coverage_before": coverage_before,
        "recommendation_scoring_mutated": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": "read_only_no_order",
    }
    if not execute:
        return base_report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_SEGMENT_HISTORY_COVERAGE_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "portfolio_name": portfolio_name,
            "statement_scope": statement_scope,
            "limit": limit,
            "target_limit": target_limit,
            "max_filings": max_filings,
            "raw_fetch_limit": resolved_raw_fetch_limit,
            "raw_artifact_root": raw_artifact_root,
            "periods_per_instrument": periods_per_instrument,
            "selected_symbols": [target.primary_symbol for target in selected_targets],
            "unmatched_symbols": unmatched_symbols,
            "model_name": DEFAULT_SEGMENT_HISTORY_COVERAGE_MODEL_NAME,
            "recommendation_scoring_mutated": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "order_boundary": "read_only_no_order",
        },
    )
    try:
        target_reports: list[dict[str, object]] = []
        failed_target_reports: list[dict[str, object]] = []
        for target in selected_targets:
            try:
                target_reports.append(
                    run_segment_history_backfill(
                        config=config,
                        as_of_date=as_of_date,
                        statement_scope=statement_scope,
                        cik=target.cik,
                        fallback_symbol=target.primary_symbol,
                        max_filings=max_filings,
                        raw_fetch_limit=resolved_raw_fetch_limit,
                        raw_artifact_root=raw_artifact_root,
                        periods_per_instrument=periods_per_instrument,
                        execute=True,
                        executor=sql_executor,
                    )
                    | {
                        "target_symbol": target.primary_symbol,
                        "target_cik": target.cik,
                        "target_source_kinds": list(target.source_kinds),
                    }
                )
            except Exception as exc:
                failed_target_reports.append(
                    {
                        "symbol": target.primary_symbol,
                        "cik": target.cik,
                        "company_name": target.company_name,
                        "source_kinds": list(target.source_kinds),
                        "error_summary": str(exc)[:1000],
                    }
                )
        coverage_after = load_segment_history_coverage_report(
            executor=sql_executor,
            as_of_date=as_of_date,
            statement_scope=statement_scope,
            periods_per_instrument=periods_per_instrument,
            targets=selected_targets,
        )
        coverage_after = _apply_parser_skip_reason_overrides(coverage_after, target_reports)
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return {
        **base_report,
        "status": "completed_with_failures" if failed_target_reports else "completed",
        "run_id": run_id,
        "target_success_count": len(target_reports),
        "target_failed_count": len(failed_target_reports),
        "target_reports": target_reports,
        "failed_target_reports": failed_target_reports,
        "coverage_after": coverage_after,
        "coverage_summary": _coverage_summary(coverage_after),
    }


def _coverage_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    status_counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("coverage_status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "target_count": len(rows),
        "status_counts": dict(sorted(status_counts.items())),
        "trend_backed_count": status_counts.get("trend_backed", 0),
        "unsupported_layout_count": status_counts.get("unsupported_layout", 0),
        "single_reportable_segment_no_detail_count": status_counts.get(
            "single_reportable_segment_no_disaggregated_segment_table", 0
        ),
        "single_period_fallback_count": status_counts.get("single_period_fallback", 0),
        "contaminated_segment_label_count": status_counts.get("contaminated_segment_labels", 0),
        "recommendation_scoring_mutated": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": "read_only_no_order",
    }


def _apply_parser_skip_reason_overrides(
    coverage_rows: list[dict[str, object]], target_reports: list[dict[str, object]]
) -> list[dict[str, object]]:
    skip_reasons_by_symbol = _parser_skip_reasons_by_symbol(target_reports)
    if not skip_reasons_by_symbol:
        return coverage_rows
    updated_rows: list[dict[str, object]] = []
    for row in coverage_rows:
        symbol = str(row.get("symbol") or "").strip().upper()
        reasons = skip_reasons_by_symbol.get(symbol, [])
        updated = dict(row)
        if reasons:
            updated["segment_parser_skip_reasons"] = reasons
        if (
            updated.get("coverage_status") == "unsupported_layout"
            and "single_reportable_segment_no_disaggregated_segment_table" in reasons
        ):
            updated["coverage_status"] = "single_reportable_segment_no_disaggregated_segment_table"
        updated_rows.append(updated)
    return updated_rows


def _parser_skip_reasons_by_symbol(target_reports: list[dict[str, object]]) -> dict[str, list[str]]:
    reasons_by_symbol: dict[str, list[str]] = {}
    for report in target_reports:
        symbol = str(report.get("target_symbol") or "").strip().upper()
        if not symbol:
            continue
        parser_report = report.get("reported_segment_parser")
        if not isinstance(parser_report, dict):
            continue
        preview = parser_report.get("preview")
        if not isinstance(preview, dict):
            continue
        skipped_candidates = preview.get("skipped_candidates")
        if not isinstance(skipped_candidates, list):
            continue
        reasons: list[str] = []
        for skipped in skipped_candidates:
            if not isinstance(skipped, dict):
                continue
            reason = str(skipped.get("reason") or "").strip()
            if reason and reason not in reasons:
                reasons.append(reason)
        if reasons:
            reasons_by_symbol[symbol] = reasons
    return reasons_by_symbol


def _render_target_value_tuple(target: ResolvedSegmentHistoryCoverageTarget) -> str:
    return (
        f"({int(target.instrument_id)}::bigint, "
        f"{sql_literal(target.primary_symbol)}::text, "
        f"{sql_literal(target.cik)}::text, "
        f"{sql_literal(target.company_name)}::text, "
        f"{sql_literal(target.exchange_name)}::text, "
        f"{sql_literal(json.dumps(list(target.source_kinds), sort_keys=True))}::jsonb)"
    )


def _target_payload(target: ResolvedSegmentHistoryCoverageTarget) -> dict[str, object]:
    return {
        "instrument_id": target.instrument_id,
        "symbol": target.primary_symbol,
        "cik": target.cik,
        "company_name": target.company_name,
        "exchange_name": target.exchange_name,
        "source_kinds": list(target.source_kinds),
    }


def _bad_key_literals() -> str:
    return ", ".join(sql_literal(key) for key in BAD_REPORTED_SEGMENT_KEYS)


def _validate_statement_scope(statement_scope: str) -> None:
    if statement_scope not in VALUATION_STATEMENT_SCOPES:
        raise ValueError(f"statement_scope must be one of: {', '.join(VALUATION_STATEMENT_SCOPES)}.")


def _validate_limit(value: int) -> None:
    if value < 1 or value > 200:
        raise ValueError("limit must be between 1 and 200.")


def _validate_periods_per_instrument(value: int) -> None:
    if value <= 0:
        raise ValueError("periods_per_instrument must be greater than 0.")


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return tuple()
    return tuple(str(item) for item in value if str(item).strip())
