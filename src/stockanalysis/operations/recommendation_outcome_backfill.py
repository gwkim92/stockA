from __future__ import annotations

from datetime import date
from typing import Any

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.performance.outcome import (
    PerformanceOutcomeScheduleCandidate,
    load_performance_outcome_schedule_candidates,
    resolve_performance_schedule_horizon_days,
    run_performance_outcome_schedule_bootstrap,
)


DEFAULT_REPORT_NAME = "recommendation_outcome_backfill"
DEFAULT_OUTCOME_VERSION = "bootstrap-v1"


def run_recommendation_outcome_backfill(
    *,
    config: RuntimeConfig,
    due_on_date: date,
    horizon_days: tuple[int, ...] = (),
    market_code: str | None = None,
    strategy_name: str | None = None,
    horizon_type: str | None = None,
    universe_version: str | None = None,
    outcome_version: str = DEFAULT_OUTCOME_VERSION,
    limit: int | None = None,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    resolved_horizon_days = resolve_performance_schedule_horizon_days(horizon_days)
    candidates = load_performance_outcome_schedule_candidates(
        config=config,
        due_on_date=due_on_date,
        horizon_days=resolved_horizon_days,
        market_code=market_code,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        universe_version=universe_version,
        limit=limit,
        executor=sql_executor,
    )

    report: dict[str, Any] = {
        "report_name": DEFAULT_REPORT_NAME,
        "mode": "execute" if execute else "preview",
        "status": _preview_status(candidates),
        "due_on_date": due_on_date.isoformat(),
        "horizon_days": list(resolved_horizon_days),
        "filters": {
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "universe_version": universe_version,
            "outcome_version": outcome_version,
            "limit": limit,
        },
        "candidate_count": len(candidates),
        "active_recommendation_count": sum(candidate.active_recommendation_count for candidate in candidates),
        "existing_outcome_count": sum(candidate.existing_outcome_count for candidate in candidates),
        "missing_outcome_count": sum(
            max(candidate.active_recommendation_count - candidate.existing_outcome_count, 0)
            for candidate in candidates
        ),
        "candidate_preview": [_candidate_payload(candidate) for candidate in candidates[:10]],
        "writes_enabled": execute,
        "writes_target": {
            "recommendation_outcomes": "performance.recommendation_outcome",
            "thesis_outcomes": "performance.thesis_outcome",
            "pipeline_run": "ops.pipeline_run",
        },
        "data_policy": "price_based_outcomes_only_no_synthetic_returns",
    }

    if not execute:
        return report

    execution = run_performance_outcome_schedule_bootstrap(
        config=config,
        due_on_date=due_on_date,
        horizon_days=resolved_horizon_days,
        market_code=market_code,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        universe_version=universe_version,
        outcome_version=outcome_version,
        limit=limit,
        executor=sql_executor,
    )
    report.update(
        {
            "status": _execution_status(execution),
            "run_id": execution["run_id"],
            "execution": execution,
            "succeeded_candidate_count": execution["succeeded_candidate_count"],
            "failed_candidate_count": execution["failed_candidate_count"],
            "recommendation_outcome_count": execution["recommendation_outcome_count"],
            "thesis_outcome_count": execution["thesis_outcome_count"],
            "label_counts": execution["label_counts"],
        }
    )
    return report


def _preview_status(candidates: tuple[PerformanceOutcomeScheduleCandidate, ...]) -> str:
    if candidates:
        return "preview_candidates_available"
    return "preview_no_due_candidates"


def _execution_status(execution: dict[str, Any]) -> str:
    if int(execution["candidate_count"]) == 0:
        return "executed_no_due_candidates"
    if int(execution["failed_candidate_count"]) > 0:
        return "executed_with_failures"
    return "executed"


def _candidate_payload(candidate: PerformanceOutcomeScheduleCandidate) -> dict[str, Any]:
    missing_count = max(candidate.active_recommendation_count - candidate.existing_outcome_count, 0)
    return {
        "batch_id": candidate.batch_id,
        "as_of_date": candidate.as_of_date.isoformat(),
        "market_code": candidate.market_code,
        "strategy_name": candidate.strategy_name,
        "horizon_type": candidate.horizon_type,
        "universe_version": candidate.universe_version,
        "horizon_day": candidate.horizon_day,
        "measurement_end_date": candidate.measurement_end_date.isoformat(),
        "active_recommendation_count": candidate.active_recommendation_count,
        "existing_outcome_count": candidate.existing_outcome_count,
        "missing_outcome_count": missing_count,
    }
