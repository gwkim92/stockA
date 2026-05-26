from __future__ import annotations

from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.financial_period_source_linkage import (
    DEFAULT_SOURCE_LINKAGE_MAX_FILINGS,
    run_financial_period_source_linkage,
)
from stockanalysis.operations.professional_equity_analysis import (
    VALUATION_STATEMENT_SCOPES,
    run_reported_segment_footnote_parser,
    run_sum_of_parts_valuation,
    run_valuation_snapshot,
)
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_SEGMENT_HISTORY_PIPELINE_NAME = "segment_history_backfill"
DEFAULT_SEGMENT_HISTORY_MODEL_NAME = "deterministic-segment-history-backfill-orchestrator-v1"
DEFAULT_SEGMENT_HISTORY_PERIODS_PER_INSTRUMENT = 4


def run_segment_history_backfill(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    statement_scope: str = "annual",
    cik: str | None = None,
    fallback_symbol: str | None = None,
    max_filings: int = DEFAULT_SOURCE_LINKAGE_MAX_FILINGS,
    raw_fetch_limit: int | None = None,
    raw_artifact_root: str = "artifacts/raw",
    periods_per_instrument: int = DEFAULT_SEGMENT_HISTORY_PERIODS_PER_INSTRUMENT,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    _validate_segment_history_backfill_args(
        statement_scope=statement_scope,
        max_filings=max_filings,
        raw_fetch_limit=periods_per_instrument if raw_fetch_limit is None else raw_fetch_limit,
        periods_per_instrument=periods_per_instrument,
    )
    resolved_raw_fetch_limit = periods_per_instrument if raw_fetch_limit is None else raw_fetch_limit
    sql_executor = executor or PsqlCommandExecutor.from_config(config)

    report: dict[str, object] = {
        "report_name": "segment_history_backfill",
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_SEGMENT_HISTORY_PIPELINE_NAME,
        "model_name": DEFAULT_SEGMENT_HISTORY_MODEL_NAME,
        "as_of_date": as_of_date.isoformat(),
        "statement_scope": statement_scope,
        "cik": _redact_blank(cik),
        "fallback_symbol": _normalize_symbol(fallback_symbol),
        "max_filings": max_filings,
        "raw_fetch_limit": resolved_raw_fetch_limit,
        "raw_artifact_root": raw_artifact_root,
        "periods_per_instrument": periods_per_instrument,
        "recommendation_scoring_mutated": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": "read_only_no_order",
    }

    if not execute:
        return {
            **report,
            "planned_steps": _planned_step_names(),
            "source_linkage": run_financial_period_source_linkage(
                config=config,
                as_of_date=as_of_date,
                statement_scope=statement_scope,
                cik=cik,
                fallback_symbol=fallback_symbol,
                max_filings=max_filings,
                raw_fetch_limit=resolved_raw_fetch_limit,
                raw_artifact_root=raw_artifact_root,
                execute=False,
                executor=sql_executor,
            ),
            "reported_segment_parser": run_reported_segment_footnote_parser(
                config=config,
                as_of_date=as_of_date,
                statement_scope=statement_scope,
                periods_per_instrument=periods_per_instrument,
                execute=False,
                executor=sql_executor,
            ),
            "sum_of_parts_valuation": run_sum_of_parts_valuation(
                config=config,
                as_of_date=as_of_date,
                statement_scope=statement_scope,
                execute=False,
                executor=sql_executor,
            ),
            "valuation_snapshot": run_valuation_snapshot(
                config=config,
                as_of_date=as_of_date,
                statement_scope=statement_scope,
                execute=False,
                executor=sql_executor,
            ),
        }

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_SEGMENT_HISTORY_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "statement_scope": statement_scope,
            "cik": _redact_blank(cik),
            "fallback_symbol": _normalize_symbol(fallback_symbol),
            "max_filings": max_filings,
            "raw_fetch_limit": resolved_raw_fetch_limit,
            "raw_artifact_root": raw_artifact_root,
            "periods_per_instrument": periods_per_instrument,
            "model_name": DEFAULT_SEGMENT_HISTORY_MODEL_NAME,
            "recommendation_scoring_mutated": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "order_boundary": "read_only_no_order",
        },
    )
    try:
        source_linkage = run_financial_period_source_linkage(
            config=config,
            as_of_date=as_of_date,
            statement_scope=statement_scope,
            cik=cik,
            fallback_symbol=fallback_symbol,
            max_filings=max_filings,
            raw_fetch_limit=resolved_raw_fetch_limit,
            raw_artifact_root=raw_artifact_root,
            execute=True,
            executor=sql_executor,
        )
        reported_segment_parser = run_reported_segment_footnote_parser(
            config=config,
            as_of_date=as_of_date,
            statement_scope=statement_scope,
            periods_per_instrument=periods_per_instrument,
            execute=True,
            executor=sql_executor,
        )
        sum_of_parts_valuation = run_sum_of_parts_valuation(
            config=config,
            as_of_date=as_of_date,
            statement_scope=statement_scope,
            execute=True,
            executor=sql_executor,
        )
        valuation_snapshot = run_valuation_snapshot(
            config=config,
            as_of_date=as_of_date,
            statement_scope=statement_scope,
            execute=True,
            executor=sql_executor,
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return {
        **report,
        "status": "completed",
        "run_id": run_id,
        "planned_steps": _planned_step_names(),
        "source_linkage": source_linkage,
        "reported_segment_parser": reported_segment_parser,
        "sum_of_parts_valuation": sum_of_parts_valuation,
        "valuation_snapshot": valuation_snapshot,
    }


def _planned_step_names() -> list[str]:
    return [
        "financial_period_source_linkage",
        "reported_segment_footnote_parser",
        "sum_of_parts_valuation",
        "valuation_snapshot",
    ]


def _validate_segment_history_backfill_args(
    *,
    statement_scope: str,
    max_filings: int,
    raw_fetch_limit: int,
    periods_per_instrument: int,
) -> None:
    if statement_scope not in VALUATION_STATEMENT_SCOPES:
        raise ValueError(f"statement_scope must be one of: {', '.join(VALUATION_STATEMENT_SCOPES)}.")
    if periods_per_instrument <= 0:
        raise ValueError("periods_per_instrument must be greater than 0.")
    if max_filings <= 0:
        raise ValueError("max_filings must be greater than 0.")
    if raw_fetch_limit <= 0:
        raise ValueError("raw_fetch_limit must be greater than 0.")


def _normalize_symbol(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().upper()
    return normalized or None


def _redact_blank(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None
