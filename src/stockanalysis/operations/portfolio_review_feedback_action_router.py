from __future__ import annotations

import json
from datetime import date
from typing import Any, Callable

from stockanalysis.frontend.live_adapter import DEFAULT_PORTFOLIO_NAME
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.portfolio_review_decision_feedback import (
    run_portfolio_review_decision_feedback,
)
from stockanalysis.operations.portfolio_review_feedback_calibration import (
    run_portfolio_review_feedback_calibration,
)
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_EVAL_NAME = "portfolio_review_feedback_action_router"
DEFAULT_DATASET_VERSION = "portfolio-review-feedback-action-router-v1"
DEFAULT_PIPELINE_NAME = "portfolio_review_feedback_action_router"
DEFAULT_PROVIDER = "deterministic_portfolio_review_feedback_action_router"
DEFAULT_MODEL_NAME = "portfolio-review-feedback-action-router-v1"

FeedbackRunner = Callable[..., dict[str, object]]
CalibrationRunner = Callable[..., dict[str, object]]


def render_portfolio_review_feedback_action_router_context_sql(
    *,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
    as_of_date: date,
) -> str:
    return f"""-- portfolio review feedback action router context lookup
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
        where eval_run.eval_name = 'portfolio_review_feedback_cadence'
          and eval_run.dataset_version = 'portfolio-review-feedback-cadence-v1'
          and coalesce(eval_run.score_json->>'portfolio_name', {sql_literal(portfolio_name)}) = {sql_literal(portfolio_name)}
          and nullif(eval_run.score_json->>'as_of_date', '')::date <= {sql_date(as_of_date)}
        order by
            nullif(eval_run.score_json->>'as_of_date', '')::date desc nulls last,
            eval_run.created_at desc,
            eval_run.eval_run_id desc
        limit 1
    ),
    json_build_object(
        'status', 'missing',
        'portfolio_name', {sql_literal(portfolio_name)},
        'score_json', '{{}}'::json
    )
)::text;"""


def load_portfolio_review_feedback_action_router_context(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    as_of_date: date,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_portfolio_review_feedback_action_router_context_sql(
                portfolio_name=portfolio_name,
                as_of_date=as_of_date,
            )
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Portfolio review feedback action router lookup did not return a JSON object.")
    return payload


def build_portfolio_review_feedback_action_router_decision(
    *,
    context: dict[str, object],
    portfolio_name: str,
    as_of_date: date,
) -> dict[str, object]:
    cadence = _as_dict(context.get("score_json"))
    source_status = str(context.get("status") or "missing")
    source_cadence_eval_run_id = _int(context.get("eval_run_id"))
    cadence_status = str(cadence.get("cadence_status") or "missing")
    source_action_type = str(cadence.get("action_type") or "inspect")
    should_run_now = _bool(cadence.get("should_run_now"))
    history = _as_dict(cadence.get("history"))
    history_eval_run_id = _int(history.get("eval_run_id"))
    guardrail_violation = _has_guardrail_violation(cadence)

    route_action = "no_op"
    action_status = f"no_op_{cadence_status}"
    reason = _no_op_reason(cadence_status)
    if source_status != "loaded":
        action_status = "no_op_missing_cadence"
        reason = "latest portfolio review feedback cadence artifact is missing."
    elif guardrail_violation:
        action_status = "blocked_guardrail_violation"
        reason = "source cadence artifact violates read-only broker/order guardrails."
    elif cadence_status == "run_feedback_now" and source_action_type == "execute_feedback" and should_run_now:
        if history_eval_run_id is None:
            action_status = "blocked_missing_history_eval_run"
            reason = "feedback execution requires a source history eval_run_id."
        else:
            route_action = "execute_feedback"
            action_status = "execute_feedback_ready"
            reason = "cadence says the decision history is mature and latest feedback is missing or stale."
    elif cadence_status == "run_calibration_now" and source_action_type == "execute_calibration" and should_run_now:
        route_action = "execute_calibration"
        action_status = "execute_calibration_ready"
        reason = "cadence says feedback exists and calibration is missing or stale."
    elif should_run_now:
        action_status = "blocked_unsupported_cadence_action"
        reason = "cadence asked to run now, but the action/status pair is not supported by the router."

    return {
        "eval_name": DEFAULT_EVAL_NAME,
        "dataset_version": DEFAULT_DATASET_VERSION,
        "as_of_date": as_of_date.isoformat(),
        "portfolio_name": portfolio_name,
        "source_cadence_status": source_status,
        "source_cadence_eval_run_id": source_cadence_eval_run_id,
        "source_cadence_created_at": str(context.get("created_at") or ""),
        "source_cadence_as_of_date": str(cadence.get("as_of_date") or ""),
        "cadence_status": cadence_status,
        "source_action_type": source_action_type,
        "source_should_run_now": should_run_now,
        "route_action": route_action,
        "action_status": action_status,
        "reason": reason,
        "history_eval_run_id": history_eval_run_id,
        "feedback_eval_run_id": _int(_as_dict(cadence.get("feedback")).get("eval_run_id")),
        "calibration_eval_run_id": _int(_as_dict(cadence.get("calibration")).get("eval_run_id")),
        "source_cadence": _cadence_summary(cadence),
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


def render_portfolio_review_feedback_action_router_insert_sql(
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


def run_portfolio_review_feedback_action_router(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    as_of_date: date,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
    feedback_runner: FeedbackRunner = run_portfolio_review_decision_feedback,
    calibration_runner: CalibrationRunner = run_portfolio_review_feedback_calibration,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    context = load_portfolio_review_feedback_action_router_context(
        config=config,
        portfolio_name=portfolio_name,
        as_of_date=as_of_date,
        executor=sql_executor,
    )
    action = build_portfolio_review_feedback_action_router_decision(
        context=context,
        portfolio_name=portfolio_name,
        as_of_date=as_of_date,
    )
    report: dict[str, object] = {
        "report_name": DEFAULT_EVAL_NAME,
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "portfolio_name": portfolio_name,
        "as_of_date": as_of_date.isoformat(),
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
            "portfolio_name": portfolio_name,
            "as_of_date": as_of_date.isoformat(),
            "source_cadence_eval_run_id": action["source_cadence_eval_run_id"],
            "cadence_status": action["cadence_status"],
            "route_action": action["route_action"],
            "action_status": action["action_status"],
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
        },
    )
    try:
        executed_action = _execute_router_action(
            action=action,
            config=config,
            portfolio_name=portfolio_name,
            as_of_date=as_of_date,
            executor=sql_executor,
            feedback_runner=feedback_runner,
            calibration_runner=calibration_runner,
        )
        eval_run_id = int(
            sql_executor.execute_scalar(
                render_portfolio_review_feedback_action_router_insert_sql(score_json=executed_action)
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
    portfolio_name: str,
    as_of_date: date,
    executor: PsqlCommandExecutor,
    feedback_runner: FeedbackRunner,
    calibration_runner: CalibrationRunner,
) -> dict[str, object]:
    route_action = str(action.get("route_action") or "no_op")
    if route_action == "execute_feedback":
        child_report = feedback_runner(
            config=config,
            portfolio_name=portfolio_name,
            as_of_date=as_of_date,
            history_eval_run_id=_int(action.get("history_eval_run_id")),
            execute=True,
            executor=executor,
        )
        return _with_child_report(
            action,
            child_report=child_report,
            action_status="feedback_executed",
            next_action="feedback 실행 결과를 반영하려면 다음 cadence run에서 calibration 필요 여부를 다시 판단한다.",
        )
    if route_action == "execute_calibration":
        child_report = calibration_runner(
            config=config,
            portfolio_name=portfolio_name,
            as_of_date=as_of_date,
            execute=True,
            executor=executor,
        )
        return _with_child_report(
            action,
            child_report=child_report,
            action_status="calibration_executed",
            next_action="calibration 결과를 data-health와 portfolio coverage에서 확인한다.",
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
    return {
        **action,
        "action_status": action_status,
        "child_runner": {
            "executed": True,
            "report_name": str(child_report.get("report_name") or ""),
            "status": str(child_report.get("status") or ""),
            "run_id": _int(child_report.get("run_id")),
            "eval_run_id": _int(child_report.get("eval_run_id")),
            "feedback_status": str(_as_dict(child_report.get("feedback")).get("feedback_status") or ""),
            "calibration_status": str(_as_dict(child_report.get("calibration")).get("calibration_status") or ""),
        },
        "next_action": next_action,
    }


def _cadence_summary(cadence: dict[str, Any]) -> dict[str, object]:
    return {
        "as_of_date": str(cadence.get("as_of_date") or ""),
        "cadence_status": str(cadence.get("cadence_status") or "missing"),
        "action_type": str(cadence.get("action_type") or "inspect"),
        "should_run_now": _bool(cadence.get("should_run_now")),
        "should_wait": _bool(cadence.get("should_wait")),
        "command": str(cadence.get("command") or ""),
        "follow_up_command": str(cadence.get("follow_up_command") or ""),
        "history": _as_dict(cadence.get("history")),
        "feedback": _as_dict(cadence.get("feedback")),
        "calibration": _as_dict(cadence.get("calibration")),
        "evidence": _as_dict(cadence.get("evidence")),
    }


def _has_guardrail_violation(cadence: dict[str, Any]) -> bool:
    return any(
        _bool(cadence.get(field))
        for field in (
            "recommendation_scoring_mutated",
            "benchmark_definition_mutated",
            "portfolio_position_mutated",
            "automatic_weight_change_allowed",
            "automatic_rebalance_allowed",
            "automatic_order_allowed",
            "broker_submit_allowed",
        )
    ) or str(cadence.get("order_boundary") or "read_only_no_order") != "read_only_no_order"


def _no_op_reason(cadence_status: str) -> str:
    if cadence_status == "wait_for_outcome_window":
        return "decision history has not reached the minimum outcome observation window."
    if cadence_status == "missing_evidence_review_required":
        return "required history, outcome, price, or paper validation evidence is missing."
    if cadence_status == "calibration_current":
        return "latest feedback and calibration are current."
    return "cadence state does not require a safe runner execution."


def _next_action(*, route_action: str, action_status: str) -> str:
    if route_action == "execute_feedback":
        return "portfolio-review-decision-outcome-feedback-run을 실행한다."
    if route_action == "execute_calibration":
        return "portfolio-review-feedback-calibration-run을 실행한다."
    if action_status == "no_op_wait_for_outcome_window":
        return "성과 관찰 기간이 끝날 때까지 기다린다."
    if action_status == "no_op_missing_evidence_review_required":
        return "부족한 검토 이력, 가격, paper validation, outcome 근거를 먼저 보강한다."
    if action_status == "no_op_calibration_current":
        return "다음 daily cadence까지 모니터링한다."
    if action_status.startswith("blocked_"):
        return "router guardrail 차단 원인을 점검한다."
    return "cadence artifact를 다시 계산한다."


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)
