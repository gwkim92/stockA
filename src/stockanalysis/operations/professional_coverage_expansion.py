from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Iterable

from stockanalysis.ai.equity_research_reporting import (
    CODEX_OAUTH_PROVIDER,
    FIXTURE_PROVIDER,
    run_equity_research_reporting,
)
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.market.universe import (
    MarketUniverseRecord,
    SelectedMarketUniverseRecord,
    load_market_universe_records,
    select_market_universe_records,
)
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.ingest.sec.companyfacts import run_sec_companyfacts_upsert
from stockanalysis.operations.industry_competitive_positioning import run_industry_competitive_positioning
from stockanalysis.operations.professional_equity_analysis import (
    run_financial_forecast_inputs,
    run_financial_metric_normalization,
    run_peer_relative_analysis,
    run_valuation_snapshot,
)
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_PIPELINE_NAME = "professional_coverage_expansion"
DEFAULT_RESEARCH_PROVIDER = FIXTURE_PROVIDER
SUPPORTED_RESEARCH_PROVIDERS = (FIXTURE_PROVIDER, CODEX_OAUTH_PROVIDER)


@dataclass(frozen=True)
class ProfessionalCoverageGapCandidate:
    instrument_id: int
    primary_symbol: str
    missing_layers: tuple[str, ...]


@dataclass(frozen=True)
class ResolvedProfessionalCoverageTarget:
    instrument_id: int
    primary_symbol: str
    cik: str
    company_name: str
    exchange_name: str
    missing_layers: tuple[str, ...]


def render_active_recommendation_professional_gap_symbols_sql(*, as_of_date: date, limit: int) -> str:
    if limit < 1 or limit > 200:
        raise ValueError("limit must be between 1 and 200.")
    target_date = sql_date(as_of_date)
    return f"""-- active recommendation professional coverage gap lookup
with active_recommendation_symbols as (
    select distinct
        instrument.instrument_id,
        instrument.primary_symbol
    from signal.recommendation recommendation
    join signal.recommendation_batch batch on batch.batch_id = recommendation.batch_id
    join ref.instrument instrument on instrument.instrument_id = recommendation.instrument_id
    where batch.as_of_date <= {target_date}
      and recommendation.status = 'active'
      and instrument.is_active = true
),
coverage_rows as (
    select
        symbol.instrument_id,
        symbol.primary_symbol,
        exists (
            select 1
            from market.financial_metric_normalized metric
            where metric.instrument_id = symbol.instrument_id
              and metric.as_of_date <= {target_date}
              and metric.metric_status = 'computed'
        ) as has_financial_metrics,
        exists (
            select 1
            from market.peer_relative_snapshot peer_snapshot
            where peer_snapshot.instrument_id = symbol.instrument_id
              and peer_snapshot.as_of_date <= {target_date}
        ) as has_peer_relative,
        exists (
            select 1
            from market.valuation_snapshot valuation
            where valuation.instrument_id = symbol.instrument_id
              and valuation.as_of_date <= {target_date}
        ) as has_valuation_snapshot,
        exists (
            select 1
            from research.industry_competitive_position position
            where position.instrument_id = symbol.instrument_id
              and position.as_of_date <= {target_date}
        ) as has_industry_competitive_position,
        exists (
            select 1
            from research.equity_research_artifact artifact
            where artifact.instrument_id = symbol.instrument_id
              and artifact.as_of_date <= {target_date}
        ) as has_equity_research_artifact,
        exists (
            select 1
            from signal.investment_thesis thesis
            where thesis.instrument_id = symbol.instrument_id
              and thesis.status = 'active'
        ) as has_active_thesis
    from active_recommendation_symbols symbol
),
gap_rows as (
    select
        instrument_id,
        primary_symbol,
        array_remove(
            array[
                case when not has_financial_metrics then 'financial_metric_normalized' end,
                case when not has_peer_relative then 'peer_relative_snapshot' end,
                case when not has_valuation_snapshot then 'valuation_snapshot' end,
                case when not has_industry_competitive_position then 'industry_competitive_position' end,
                case when not has_equity_research_artifact then 'equity_research_artifact' end,
                case when not has_active_thesis then 'active_thesis' end
            ],
            null
        ) as missing_layers
    from coverage_rows
    where not (
        has_financial_metrics
        and has_peer_relative
        and has_valuation_snapshot
        and has_industry_competitive_position
        and has_equity_research_artifact
        and has_active_thesis
    )
)
select coalesce(
    json_agg(
        json_build_object(
            'instrument_id', instrument_id,
            'primary_symbol', primary_symbol,
            'missing_layers', missing_layers
        )
        order by primary_symbol
    ),
    '[]'::json
)::text
from (
    select *
    from gap_rows
    order by primary_symbol
    limit {int(limit)}
) limited;"""


def load_professional_coverage_gap_candidates(
    *,
    executor: PsqlCommandExecutor,
    as_of_date: date,
    limit: int,
) -> tuple[ProfessionalCoverageGapCandidate, ...]:
    payload_text = executor.execute_scalar(
        render_active_recommendation_professional_gap_symbols_sql(as_of_date=as_of_date, limit=limit)
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Professional coverage gap lookup did not return a JSON array.")
    candidates: list[ProfessionalCoverageGapCandidate] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("primary_symbol") or "").strip().upper()
        if not symbol:
            continue
        candidates.append(
            ProfessionalCoverageGapCandidate(
                instrument_id=int(item["instrument_id"]),
                primary_symbol=symbol,
                missing_layers=_string_tuple(item.get("missing_layers")),
            )
        )
    return tuple(candidates)


def resolve_professional_coverage_targets(
    candidates: Iterable[ProfessionalCoverageGapCandidate],
    *,
    company_ticker_records: tuple[MarketUniverseRecord, ...],
    exchanges: list[str] | None = None,
) -> tuple[ResolvedProfessionalCoverageTarget, ...]:
    candidate_by_symbol = {candidate.primary_symbol: candidate for candidate in candidates}
    if not candidate_by_symbol:
        return tuple()
    selection = select_market_universe_records(company_ticker_records, exchanges=exchanges)
    selected_by_symbol: dict[str, SelectedMarketUniverseRecord] = {}
    for record in selection.records:
        if record.symbol in candidate_by_symbol and record.symbol not in selected_by_symbol:
            selected_by_symbol[record.symbol] = record
    targets: list[ResolvedProfessionalCoverageTarget] = []
    for symbol in sorted(selected_by_symbol):
        record = selected_by_symbol[symbol]
        candidate = candidate_by_symbol[symbol]
        targets.append(
            ResolvedProfessionalCoverageTarget(
                instrument_id=candidate.instrument_id,
                primary_symbol=symbol,
                cik=record.cik,
                company_name=record.company_name,
                exchange_name=record.exchange_name,
                missing_layers=candidate.missing_layers,
            )
        )
    return tuple(targets)


def run_professional_coverage_expansion(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    limit: int = 25,
    companyfacts_limit: int = 5,
    research_limit: int = 5,
    research_provider: str = DEFAULT_RESEARCH_PROVIDER,
    company_tickers_json_path: str | None = None,
    exchanges: list[str] | None = None,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    _validate_limits(limit=limit, companyfacts_limit=companyfacts_limit, research_limit=research_limit)
    if research_provider not in SUPPORTED_RESEARCH_PROVIDERS:
        raise ValueError("research_provider must be fixture or codex_oauth.")
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    candidates = load_professional_coverage_gap_candidates(
        executor=sql_executor,
        as_of_date=as_of_date,
        limit=limit,
    )
    if not candidates:
        empty_report: dict[str, object] = {
            "report_name": DEFAULT_PIPELINE_NAME,
            "status": "planned" if not execute else "completed",
            "run_id": None,
            "as_of_date": as_of_date.isoformat(),
            "candidate_symbol_count": 0,
            "resolved_target_count": 0,
            "companyfacts_target_count": 0,
            "research_target_count": 0,
            "candidate_symbols": [],
            "companyfacts_targets": [],
            "research_symbols": [],
            "unmatched_symbols": [],
            "research_provider": research_provider,
            "downstream_steps": [],
            "execute": execute,
        }
        if not execute:
            return empty_report
        run_id = _create_pipeline_run(
            sql_executor,
            pipeline_name=DEFAULT_PIPELINE_NAME,
            config_json={
                "as_of_date": as_of_date.isoformat(),
                "limit": limit,
                "companyfacts_limit": companyfacts_limit,
                "research_limit": research_limit,
                "research_provider": research_provider,
                "candidate_symbols": [],
                "companyfacts_symbols": [],
                "research_symbols": [],
                "unmatched_symbols": [],
            },
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
        return empty_report | {"run_id": run_id}
    records = load_market_universe_records(
        config=config,
        company_tickers_json_path=company_tickers_json_path,
    )
    targets = resolve_professional_coverage_targets(
        candidates,
        company_ticker_records=records,
        exchanges=exchanges,
    )
    companyfacts_targets = targets[:companyfacts_limit]
    research_symbols = tuple(target.primary_symbol for target in targets[:research_limit])
    unmatched_symbols = sorted(
        {candidate.primary_symbol for candidate in candidates}
        - {target.primary_symbol for target in targets}
    )

    base_report: dict[str, object] = {
        "report_name": DEFAULT_PIPELINE_NAME,
        "status": "planned" if not execute else "running",
        "run_id": None,
        "as_of_date": as_of_date.isoformat(),
        "candidate_symbol_count": len(candidates),
        "resolved_target_count": len(targets),
        "companyfacts_target_count": len(companyfacts_targets),
        "research_target_count": len(research_symbols),
        "candidate_symbols": [candidate.primary_symbol for candidate in candidates],
        "companyfacts_targets": [_target_payload(target) for target in companyfacts_targets],
        "research_symbols": list(research_symbols),
        "unmatched_symbols": unmatched_symbols,
        "research_provider": research_provider,
        "downstream_steps": [
            "financial_metric_normalization",
            "peer_relative_analysis",
            "valuation_snapshot",
            "industry_competitive_positioning",
            "equity_research_reporting",
        ],
        "execute": execute,
    }
    if not execute:
        return base_report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "limit": limit,
            "companyfacts_limit": companyfacts_limit,
            "research_limit": research_limit,
            "research_provider": research_provider,
            "candidate_symbols": [candidate.primary_symbol for candidate in candidates],
            "companyfacts_symbols": [target.primary_symbol for target in companyfacts_targets],
            "research_symbols": list(research_symbols),
            "unmatched_symbols": unmatched_symbols,
        },
    )
    try:
        companyfacts_reports: list[dict[str, object]] = []
        failed_companyfacts_reports: list[dict[str, object]] = []
        for target in companyfacts_targets:
            try:
                companyfacts_reports.append(
                    run_sec_companyfacts_upsert(
                        target.cik,
                        config=config,
                        fallback_symbol=target.primary_symbol,
                        executor=sql_executor,
                    )
                )
            except Exception as exc:
                failed_companyfacts_reports.append(
                    {
                        "symbol": target.primary_symbol,
                        "cik": target.cik,
                        "company_name": target.company_name,
                        "error_summary": str(exc)[:1000],
                    }
                )
        downstream_reports = {
            "financial_metric_normalization": run_financial_metric_normalization(
                config=config,
                as_of_date=as_of_date,
                execute=True,
                executor=sql_executor,
            ),
            "peer_relative_analysis": run_peer_relative_analysis(
                config=config,
                as_of_date=as_of_date,
                statement_scope="annual",
                execute=True,
                executor=sql_executor,
            ),
            "financial_forecast_inputs": run_financial_forecast_inputs(
                config=config,
                as_of_date=as_of_date,
                statement_scope="annual",
                execute=True,
                executor=sql_executor,
            ),
            "valuation_snapshot": run_valuation_snapshot(
                config=config,
                as_of_date=as_of_date,
                statement_scope="annual",
                execute=True,
                executor=sql_executor,
            ),
            "industry_competitive_positioning": run_industry_competitive_positioning(
                config=config,
                as_of_date=as_of_date,
                execute=True,
                executor=sql_executor,
            ),
        }
        if research_symbols:
            downstream_reports["equity_research_reporting"] = run_equity_research_reporting(
                config=config,
                as_of_date=as_of_date,
                symbols=research_symbols,
                limit=research_limit,
                provider=research_provider,
                execute=True,
                executor=sql_executor,
            )
        else:
            downstream_reports["equity_research_reporting"] = {
                "report_name": "equity_research_reporting",
                "status": "skipped",
                "reason": "No SEC-resolved active recommendation coverage targets.",
            }
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return base_report | {
        "status": "completed_with_failures" if failed_companyfacts_reports else "completed",
        "run_id": run_id,
        "companyfacts_reports": companyfacts_reports,
        "failed_companyfacts_reports": failed_companyfacts_reports,
        "companyfacts_success_count": len(companyfacts_reports),
        "companyfacts_failed_count": len(failed_companyfacts_reports),
        "downstream_reports": downstream_reports,
    }


def _validate_limits(*, limit: int, companyfacts_limit: int, research_limit: int) -> None:
    if limit < 1 or limit > 200:
        raise ValueError("limit must be between 1 and 200.")
    if companyfacts_limit < 0 or companyfacts_limit > limit:
        raise ValueError("companyfacts_limit must be between 0 and limit.")
    if research_limit < 0 or research_limit > limit:
        raise ValueError("research_limit must be between 0 and limit.")


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return tuple()
    return tuple(str(item) for item in value if str(item).strip())


def _target_payload(target: ResolvedProfessionalCoverageTarget) -> dict[str, object]:
    return {
        "instrument_id": target.instrument_id,
        "symbol": target.primary_symbol,
        "cik": target.cik,
        "company_name": target.company_name,
        "exchange_name": target.exchange_name,
        "missing_layers": list(target.missing_layers),
    }
