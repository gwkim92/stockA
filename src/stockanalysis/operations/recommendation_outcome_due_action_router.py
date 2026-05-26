from __future__ import annotations

import json
from datetime import date
from typing import Any, Callable

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.recommendation_outcome_backfill import DEFAULT_OUTCOME_VERSION
from stockanalysis.operations.recommendation_outcome_calibration_sample_expansion import (
    DEFAULT_EXAMPLE_LIMIT,
    DEFAULT_MIN_PROFESSIONAL_COVERAGE_RATE,
    DEFAULT_MIN_SAMPLE_SIZE,
    load_recommendation_outcome_sample_audit,
    run_recommendation_outcome_calibration_sample_expansion,
)
from stockanalysis.performance.outcome import resolve_performance_schedule_horizon_days
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_EVAL_NAME = "recommendation_outcome_due_action_router"
DEFAULT_DATASET_VERSION = "recommendation-outcome-due-action-router-v1"
DEFAULT_PIPELINE_NAME = "recommendation_outcome_due_action_router"
DEFAULT_PROVIDER = "deterministic_recommendation_outcome_due_action_router"
DEFAULT_MODEL_NAME = "recommendation-outcome-due-action-router-v1"

CalibrationRunner = Callable[..., dict[str, object]]


def render_recommendation_outcome_due_action_router_context_sql(*, as_of_date: date) -> str:
    return f"""-- recommendation outcome due action router context lookup
select coalesce(
    (
        select json_build_object(
            'status', 'loaded',
            'eval_run_id', eval_run.eval_run_id,
            'created_at', eval_run.created_at,
            'eval_name', eval_run.eval_name,
            'dataset_version', eval_run.dataset_version,
            'score_json', eval_run.score_json
        )
        from ai.eval_run eval_run
        where eval_run.eval_name = 'recommendation_outcome_calibration_sample_expansion'
          and eval_run.dataset_version = 'recommendation-outcome-calibration-sample-expansion-v1'
          and nullif(eval_run.score_json->>'as_of_date', '')::date <= {sql_date(as_of_date)}
        order by
            nullif(eval_run.score_json->>'as_of_date', '')::date desc nulls last,
            eval_run.created_at desc,
            eval_run.eval_run_id desc
        limit 1
    ),
    json_build_object(
        'status', 'missing',
        'score_json', '{{}}'::json
    )
)::text;"""


def load_recommendation_outcome_due_action_router_context(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    horizon_days: tuple[int, ...],
    market_code: str | None = None,
    strategy_name: str | None = None,
    horizon_type: str | None = None,
    universe_version: str | None = None,
    example_limit: int = DEFAULT_EXAMPLE_LIMIT,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    latest_calibration = json.loads(
        sql_executor.execute_scalar(render_recommendation_outcome_due_action_router_context_sql(as_of_date=as_of_date))
    )
    if not isinstance(latest_calibration, dict):
        raise ValueError("Recommendation outcome due action router context lookup did not return a JSON object.")
    sample_audit = load_recommendation_outcome_sample_audit(
        config=config,
        as_of_date=as_of_date,
        horizon_days=horizon_days,
        market_code=market_code,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        universe_version=universe_version,
        example_limit=example_limit,
        executor=sql_executor,
    )
    return {
        "latest_calibration": latest_calibration,
        "sample_audit": sample_audit,
    }


def build_recommendation_outcome_due_action_router_decision(
    *,
    context: dict[str, object],
    as_of_date: date,
    horizon_days: tuple[int, ...],
    market_code: str | None = None,
    strategy_name: str | None = None,
    horizon_type: str | None = None,
    universe_version: str | None = None,
) -> dict[str, object]:
    latest_calibration = _as_dict(context.get("latest_calibration"))
    sample_audit = _as_dict(context.get("sample_audit"))
    summary = _as_dict(sample_audit.get("summary"))
    ready_count = _int(summary.get("ready_for_backfill_count"))
    missing_entry_count = _int(summary.get("missing_entry_price_count"))
    missing_exit_count = _int(summary.get("missing_exit_price_count"))
    price_gap_count = missing_entry_count + missing_exit_count
    not_due_count = _int(summary.get("not_due_count"))
    outcome_count = _int(summary.get("outcome_count"))
    recommendation_horizon_count = _int(summary.get("recommendation_horizon_count"))
    route_action = "no_op"
    action_status = "no_op_current_window_complete"
    reason = "현재 측정 가능한 추천 성과창은 이미 처리됐다."
    if _has_guardrail_violation(latest_calibration=latest_calibration, sample_audit=sample_audit):
        action_status = "blocked_guardrail_violation"
        reason = "source outcome audit violates read-only recommendation/order guardrails."
    elif recommendation_horizon_count <= 0:
        action_status = "no_op_no_active_recommendation_horizons"
        reason = "측정할 active recommendation horizon이 없다."
    elif ready_count > 0:
        route_action = "execute_calibration"
        action_status = "execute_outcome_calibration_ready"
        reason = f"성과 산출 가능한 추천×기간 {ready_count}개가 있어 outcome calibration을 실행할 수 있다."
    elif price_gap_count > 0:
        action_status = "blocked_by_price_gaps"
        reason = f"가격 이력 누락 {price_gap_count}개 때문에 성과 산출이 막혔다."
    elif not_due_count > 0:
        action_status = "no_op_wait_until_next_due_date"
        reason = "추천 성과 측정창이 아직 열리지 않았다."
    elif outcome_count <= 0:
        action_status = "no_op_no_outcome_sample_available"
        reason = "성과 표본이 아직 없어 추천 weight 검토를 계속 차단한다."

    return {
        "eval_name": DEFAULT_EVAL_NAME,
        "dataset_version": DEFAULT_DATASET_VERSION,
        "as_of_date": as_of_date.isoformat(),
        "horizon_days": list(horizon_days),
        "filters": {
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "universe_version": universe_version,
        },
        "source_calibration_status": str(latest_calibration.get("status") or "missing"),
        "source_calibration_eval_run_id": _int(latest_calibration.get("eval_run_id")),
        "source_calibration_created_at": str(latest_calibration.get("created_at") or ""),
        "source_calibration_summary": _source_calibration_summary(_as_dict(latest_calibration.get("score_json"))),
        "route_action": route_action,
        "action_status": action_status,
        "reason": reason,
        "wait_until": _next_not_due_date(sample_audit),
        "sample_audit_summary": {
            "recommendation_horizon_count": recommendation_horizon_count,
            "recommendation_count": _int(summary.get("recommendation_count")),
            "outcome_count": outcome_count,
            "ready_for_backfill_count": ready_count,
            "not_due_count": not_due_count,
            "missing_entry_price_count": missing_entry_count,
            "missing_exit_price_count": missing_exit_count,
            "price_gap_count": price_gap_count,
            "outcome_coverage_rate": _float(summary.get("outcome_coverage_rate")),
        },
        "horizon_coverage": _as_list(sample_audit.get("horizon_coverage")),
        "missing_reason_counts": _as_dict(sample_audit.get("missing_reason_counts")),
        "missing_examples": _as_list(sample_audit.get("missing_examples"))[:10],
        "child_runner": {
            "executed": False,
            "report_name": "",
            "status": "not_run",
            "run_id": None,
            "eval_run_id": None,
        },
        "recommendation_scoring_mutated": False,
        "benchmark_definition_mutated": False,
        "portfolio_position_mutated": False,
        "automatic_weight_change_allowed": False,
        "automatic_rebalance_allowed": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": "read_only_no_order",
        "next_action": _next_action(route_action=route_action, action_status=action_status),
    }


def render_recommendation_outcome_due_action_router_insert_sql(
    *,
    score_json: dict[str, object],
    eval_name: str = DEFAULT_EVAL_NAME,
    dataset_version: str = DEFAULT_DATASET_VERSION,
    provider: str = DEFAULT_PROVIDER,
    model_name: str = DEFAULT_MODEL_NAME,
) -> str:
    score_text = json.dumps(score_json, ensure_ascii=False, sort_keys=True)
    return f"""insert into ai.eval_run (
    eval_name,
    dataset_version,
    provider,
    model_name,
    score_json
)
values (
    {sql_literal(eval_name)},
    {sql_literal(dataset_version)},
    {sql_literal(provider)},
    {sql_literal(model_name)},
    {sql_literal(score_text)}::jsonb
)
returning eval_run_id;"""


def run_recommendation_outcome_due_action_router(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    horizon_days: tuple[int, ...] = (),
    market_code: str | None = None,
    strategy_name: str | None = None,
    horizon_type: str | None = None,
    universe_version: str | None = None,
    outcome_version: str = DEFAULT_OUTCOME_VERSION,
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
    min_professional_coverage_rate: float = DEFAULT_MIN_PROFESSIONAL_COVERAGE_RATE,
    limit: int | None = None,
    example_limit: int = DEFAULT_EXAMPLE_LIMIT,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
    calibration_runner: CalibrationRunner = run_recommendation_outcome_calibration_sample_expansion,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    resolved_horizon_days = resolve_performance_schedule_horizon_days(horizon_days)
    context = load_recommendation_outcome_due_action_router_context(
        config=config,
        as_of_date=as_of_date,
        horizon_days=resolved_horizon_days,
        market_code=market_code,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        universe_version=universe_version,
        example_limit=example_limit,
        executor=sql_executor,
    )
    action = build_recommendation_outcome_due_action_router_decision(
        context=context,
        as_of_date=as_of_date,
        horizon_days=resolved_horizon_days,
        market_code=market_code,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        universe_version=universe_version,
    )
    report: dict[str, object] = {
        "report_name": DEFAULT_EVAL_NAME,
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "horizon_days": list(resolved_horizon_days),
        "provider": DEFAULT_PROVIDER,
        "model_name": DEFAULT_MODEL_NAME,
        "action": action,
    }
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "horizon_days": list(resolved_horizon_days),
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "universe_version": universe_version,
            "source_calibration_eval_run_id": action["source_calibration_eval_run_id"],
            "route_action": action["route_action"],
            "action_status": action["action_status"],
            "recommendation_scoring_mutated": False,
            "automatic_weight_change_allowed": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
        },
    )
    try:
        executed_action = _execute_router_action(
            action=action,
            config=config,
            as_of_date=as_of_date,
            horizon_days=resolved_horizon_days,
            market_code=market_code,
            strategy_name=strategy_name,
            horizon_type=horizon_type,
            universe_version=universe_version,
            outcome_version=outcome_version,
            min_sample_size=min_sample_size,
            min_professional_coverage_rate=min_professional_coverage_rate,
            limit=limit,
            example_limit=example_limit,
            executor=sql_executor,
            calibration_runner=calibration_runner,
        )
        eval_run_id = int(
            sql_executor.execute_scalar(
                render_recommendation_outcome_due_action_router_insert_sql(score_json=executed_action)
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return {
        **report,
        "status": "completed",
        "run_id": run_id,
        "eval_run_id": eval_run_id,
        "action": executed_action,
    }


def _execute_router_action(
    *,
    action: dict[str, object],
    config: RuntimeConfig,
    as_of_date: date,
    horizon_days: tuple[int, ...],
    market_code: str | None,
    strategy_name: str | None,
    horizon_type: str | None,
    universe_version: str | None,
    outcome_version: str,
    min_sample_size: int,
    min_professional_coverage_rate: float,
    limit: int | None,
    example_limit: int,
    executor: PsqlCommandExecutor,
    calibration_runner: CalibrationRunner,
) -> dict[str, object]:
    route_action = str(action.get("route_action") or "no_op")
    if route_action == "execute_calibration":
        child_report = calibration_runner(
            config=config,
            as_of_date=as_of_date,
            horizon_days=horizon_days,
            market_code=market_code,
            strategy_name=strategy_name,
            horizon_type=horizon_type,
            universe_version=universe_version,
            outcome_version=outcome_version,
            min_sample_size=min_sample_size,
            min_professional_coverage_rate=min_professional_coverage_rate,
            limit=limit,
            example_limit=example_limit,
            execute=True,
            executor=executor,
        )
        return _with_child_report(
            action,
            child_report=child_report,
            action_status="outcome_calibration_executed",
            next_action="calibration 결과와 recommendation weight review gate를 data-health에서 확인한다.",
        )
    return {
        **action,
        "child_runner": {
            "executed": False,
            "report_name": "",
            "status": "not_run",
            "run_id": None,
            "eval_run_id": None,
        },
    }


def _with_child_report(
    action: dict[str, object],
    *,
    child_report: dict[str, object],
    action_status: str,
    next_action: str,
) -> dict[str, object]:
    score = _as_dict(child_report.get("score"))
    return {
        **action,
        "action_status": action_status,
        "child_runner": {
            "executed": True,
            "report_name": str(child_report.get("report_name") or ""),
            "status": str(child_report.get("status") or ""),
            "run_id": _int(child_report.get("run_id")),
            "eval_run_id": _int(child_report.get("eval_run_id")),
            "calibration_status": str(score.get("status") or ""),
            "quality_status": str(score.get("quality_status") or ""),
            "sample_status": str(score.get("sample_status") or ""),
        },
        "next_action": next_action,
    }


def _source_calibration_summary(score_json: dict[str, Any]) -> dict[str, object]:
    return {
        "as_of_date": str(score_json.get("as_of_date") or ""),
        "status": str(score_json.get("status") or "missing"),
        "quality_status": str(score_json.get("quality_status") or "unknown"),
        "sample_status": str(score_json.get("sample_status") or "unknown"),
        "next_action": str(score_json.get("next_action") or ""),
        "recommendation_scoring_mutated": _bool(score_json.get("recommendation_scoring_mutated")),
        "automatic_order_allowed": _bool(score_json.get("automatic_order_allowed")),
        "broker_submit_allowed": _bool(score_json.get("broker_submit_allowed")),
        "order_boundary": str(score_json.get("order_boundary") or "read_only_no_order"),
    }


def _has_guardrail_violation(*, latest_calibration: dict[str, Any], sample_audit: dict[str, Any]) -> bool:
    source_score = _as_dict(latest_calibration.get("score_json"))
    sample_guardrails = _as_dict(sample_audit.get("guardrails"))
    for payload in (source_score, sample_guardrails):
        if any(
            _bool(payload.get(field))
            for field in (
                "recommendation_scoring_mutated",
                "benchmark_definition_mutated",
                "portfolio_position_mutated",
                "automatic_weight_change_allowed",
                "automatic_rebalance_allowed",
                "automatic_order_allowed",
                "broker_submit_allowed",
            )
        ):
            return True
        order_boundary = str(payload.get("order_boundary") or "read_only_no_order")
        if order_boundary != "read_only_no_order":
            return True
    return False


def _next_not_due_date(sample_audit: dict[str, Any]) -> str:
    dates: list[str] = []
    for item in _as_list(sample_audit.get("missing_examples")):
        if str(item.get("sample_status") or "") == "not_due":
            value = str(item.get("expected_measurement_end_date") or "")
            if value:
                dates.append(value)
    return min(dates) if dates else ""


def _next_action(*, route_action: str, action_status: str) -> str:
    if route_action == "execute_calibration":
        return "recommendation-outcome-calibration-sample-expansion-run을 실행해 price-based outcome과 quality eval을 갱신한다."
    if action_status == "blocked_by_price_gaps":
        return "market-price 수집/보강 후 recommendation-outcome-due-action-router-run을 다시 실행한다."
    if action_status == "no_op_wait_until_next_due_date":
        return "다음 성과 측정일까지 추천 weight를 유지하고 기다린다."
    if action_status.startswith("blocked_"):
        return "router guardrail 차단 원인을 점검한다."
    return "다음 daily cadence까지 outcome maturity를 모니터링한다."


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _int(value: object) -> int:
    if value is None:
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _float(value: object) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)

