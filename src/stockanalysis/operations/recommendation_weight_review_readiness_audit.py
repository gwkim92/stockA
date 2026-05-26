from __future__ import annotations

import json
from datetime import date
from decimal import Decimal, InvalidOperation

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.recommendation_quality_eval import (
    DEFAULT_DATASET_VERSION as QUALITY_DATASET_VERSION,
    DEFAULT_EVAL_NAME as QUALITY_EVAL_NAME,
)
from stockanalysis.operations.recommendation_outcome_calibration_sample_expansion import (
    DEFAULT_DATASET_VERSION as OUTCOME_CALIBRATION_DATASET_VERSION,
    DEFAULT_EVAL_NAME as OUTCOME_CALIBRATION_EVAL_NAME,
)
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_AUDIT_EVAL_NAME = "recommendation_weight_review_readiness_audit"
DEFAULT_AUDIT_DATASET_VERSION = "recommendation-weight-review-readiness-v1"
DEFAULT_PIPELINE_NAME = "recommendation_weight_review_readiness_audit"
DEFAULT_MODEL_NAME = "deterministic-guardrail-v1"
DEFAULT_PROVIDER = "postgres"
DEFAULT_MIN_COMPONENT_OUTCOME_COUNT = 5
READY_DECISION = "ready_for_manual_weight_review"
SAFETY_INTERLOCK_POLICY_DECISION = "paper_actions_waiting_for_safety_interlock_release"
OUTCOME_CALIBRATION_READY_STATUS = "ready_for_manual_weight_review"
OUTCOME_CALIBRATION_BLOCKING_STATUSES = {
    "no_due_outcome_window",
    "backfill_candidates_remain",
    "price_history_gaps_remain",
    "no_outcome_sample_available",
    "missing",
}


def render_recommendation_weight_review_eval_lookup_sql(
    *,
    as_of_date: date,
    eval_run_id: int | None = None,
) -> str:
    eval_filter = ""
    if eval_run_id is not None:
        if eval_run_id <= 0:
            raise ValueError("eval_run_id must be greater than 0.")
        eval_filter = f"\n      and eval_run.eval_run_id = {eval_run_id}"
    return f"""-- recommendation weight review readiness audit source eval lookup
with selected_eval as (
    select
        eval_run.eval_run_id,
        eval_run.eval_name,
        eval_run.dataset_version,
        eval_run.provider,
        eval_run.model_name,
        eval_run.score_json,
        eval_run.created_at
    from ai.eval_run eval_run
    where eval_run.eval_name = {sql_literal(QUALITY_EVAL_NAME)}
      and eval_run.dataset_version = {sql_literal(QUALITY_DATASET_VERSION)}
      and nullif(eval_run.score_json->>'as_of_date', '')::date <= {sql_date(as_of_date)}{eval_filter}
    order by eval_run.created_at desc, eval_run.eval_run_id desc
    limit 1
)
select coalesce(
    (
        select json_build_object(
            'eval_run_id', selected_eval.eval_run_id,
            'eval_name', selected_eval.eval_name,
            'dataset_version', selected_eval.dataset_version,
            'provider', selected_eval.provider,
            'model_name', selected_eval.model_name,
            'score_json', selected_eval.score_json,
            'created_at', selected_eval.created_at
        )
        from selected_eval
    ),
    '{{}}'::json
)::text;"""


def render_recommendation_outcome_calibration_eval_lookup_sql(
    *,
    as_of_date: date,
    eval_run_id: int | None = None,
) -> str:
    eval_filter = ""
    date_filter = f"\n      and nullif(eval_run.score_json->>'as_of_date', '')::date <= {sql_date(as_of_date)}"
    if eval_run_id is not None:
        if eval_run_id <= 0:
            raise ValueError("outcome calibration eval_run_id must be greater than 0.")
        eval_filter = f"\n      and eval_run.eval_run_id = {eval_run_id}"
        date_filter = ""
    return f"""-- recommendation weight review outcome calibration eval lookup
with selected_eval as (
    select
        eval_run.eval_run_id,
        eval_run.eval_name,
        eval_run.dataset_version,
        eval_run.provider,
        eval_run.model_name,
        eval_run.score_json,
        eval_run.created_at
    from ai.eval_run eval_run
    where eval_run.eval_name = {sql_literal(OUTCOME_CALIBRATION_EVAL_NAME)}
      and eval_run.dataset_version = {sql_literal(OUTCOME_CALIBRATION_DATASET_VERSION)}{date_filter}{eval_filter}
    order by
        nullif(eval_run.score_json->>'as_of_date', '')::date desc nulls last,
        eval_run.created_at desc,
        eval_run.eval_run_id desc
    limit 1
)
select coalesce(
    (
        select json_build_object(
            'eval_run_id', selected_eval.eval_run_id,
            'eval_name', selected_eval.eval_name,
            'dataset_version', selected_eval.dataset_version,
            'provider', selected_eval.provider,
            'model_name', selected_eval.model_name,
            'score_json', selected_eval.score_json,
            'created_at', selected_eval.created_at
        )
        from selected_eval
    ),
    '{{}}'::json
)::text;"""


def render_recommendation_weight_review_audit_insert_sql(
    *,
    score_json: dict[str, object],
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
    {sql_literal(DEFAULT_AUDIT_EVAL_NAME)},
    {sql_literal(DEFAULT_AUDIT_DATASET_VERSION)},
    {sql_literal(DEFAULT_PROVIDER)},
    {sql_literal(DEFAULT_MODEL_NAME)},
    {sql_literal(score_text)}::jsonb
)
returning eval_run_id;"""


def render_paper_safety_interlock_policy_lookup_sql(*, as_of_date: date) -> str:
    return f"""-- recommendation weight review paper safety interlock policy lookup
select coalesce(
    (
        select json_build_object(
            'run_id', run.run_id,
            'status', run.status,
            'paper_validation_run_id', nullif(run.config_json->>'paper_validation_run_id', '')::bigint,
            'decision', run.config_json->>'decision',
            'weight_review_allowed', coalesce(nullif(run.config_json->>'weight_review_allowed', '')::boolean, false),
            'automatic_order_allowed', coalesce(nullif(run.config_json->>'automatic_order_allowed', '')::boolean, false),
            'started_at', run.started_at,
            'ended_at', run.ended_at
        )
        from ops.pipeline_run run
        where run.pipeline_name = 'paper_validation_conflict_remediation'
          and run.status = 'succeeded'
          and run.started_at::date <= {sql_date(as_of_date)}
        order by run.ended_at desc nulls last, run.run_id desc
        limit 1
    ),
    '{{}}'::json
)::text;"""


def load_recommendation_weight_review_source_eval(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    eval_run_id: int | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_recommendation_weight_review_eval_lookup_sql(
                as_of_date=as_of_date,
                eval_run_id=eval_run_id,
            )
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Recommendation weight review eval lookup did not return a JSON object.")
    if not payload:
        selector = f"eval_run_id={eval_run_id}" if eval_run_id is not None else f"as_of_date<={as_of_date.isoformat()}"
        raise ValueError(f"No recommendation quality eval_run found for {selector}.")
    return payload


def load_recommendation_outcome_calibration_eval(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    eval_run_id: int | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_recommendation_outcome_calibration_eval_lookup_sql(
                as_of_date=as_of_date,
                eval_run_id=eval_run_id,
            )
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Recommendation outcome calibration eval lookup did not return a JSON object.")
    return payload


def load_paper_safety_interlock_policy(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(sql_executor.execute_scalar(render_paper_safety_interlock_policy_lookup_sql(as_of_date=as_of_date)))
    if not isinstance(payload, dict):
        raise ValueError("Paper safety interlock policy lookup did not return a JSON object.")
    return payload


def audit_recommendation_weight_review_readiness(
    score: dict[str, object],
    *,
    source_eval_run_id: int,
    min_component_outcome_count: int = DEFAULT_MIN_COMPONENT_OUTCOME_COUNT,
    paper_safety_policy: dict[str, object] | None = None,
    outcome_calibration_eval: dict[str, object] | None = None,
) -> dict[str, object]:
    if min_component_outcome_count < 1:
        raise ValueError("min_component_outcome_count must be greater than 0.")

    blockers: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []

    quality_status = str(score.get("quality_status") or "unknown")
    sample_status = str(score.get("sample_status") or "unknown")
    professional_coverage = _as_dict(score.get("professional_analysis_coverage"))
    cycle_guardrail = _as_dict(score.get("cycle_weight_guardrail"))
    fundamental_guardrail = _as_dict(score.get("fundamental_weight_guardrail"))
    paper_validation = _as_dict(score.get("paper_validation"))
    safety_policy = _as_dict(paper_safety_policy)
    outcome_calibration_gate = _outcome_calibration_gate(outcome_calibration_eval)
    outcome_count = _int(score.get("outcome_count"))
    positive_outcome_count = _int(score.get("positive_outcome_count"))

    if not bool(cycle_guardrail.get("cycle_weight_unchanged")):
        blockers.append(_blocker("blocked_by_unapproved_cycle_weight_mutation", "cycle component weight가 이미 0이 아니다. 기존 승인 이력부터 확인해야 한다."))
    if not bool(fundamental_guardrail.get("fundamental_weight_unchanged")):
        blockers.append(_blocker("blocked_by_unapproved_fundamental_weight_mutation", "fundamental/valuation/peer component weight가 이미 0이 아니다. outcome 표본과 승인 이력 없이 반영됐는지 확인해야 한다."))
    if quality_status != "ready_for_weight_review":
        blockers.append(_blocker("blocked_by_quality_eval_status", f"source quality eval status가 {quality_status}이다."))
    if sample_status != "sufficient_sample":
        blockers.append(_blocker("blocked_by_insufficient_sample", f"outcome sample status가 {sample_status}이다."))
    if professional_coverage.get("status") != "sufficient_coverage":
        blockers.append(_blocker("blocked_by_insufficient_professional_coverage", "active recommendation의 재무·피어·밸류에이션·리서치 coverage가 기준 미만이다."))
    outcome_calibration_status = str(outcome_calibration_gate.get("status") or "missing")
    if outcome_calibration_status != OUTCOME_CALIBRATION_READY_STATUS:
        blockers.append(_outcome_calibration_blocker(outcome_calibration_gate))

    paper_status = str(paper_validation.get("latest_status") or "missing")
    paper_conflict_count = _int(paper_validation.get("conflict_count"))
    paper_approved_action_count = _int(paper_validation.get("approved_action_count"))
    if paper_status == "missing":
        blockers.append(_blocker("blocked_by_missing_paper_validation", "최신 paper validation run이 없다."))
    elif paper_conflict_count > 0:
        blockers.append(
            _blocker(
                "blocked_by_paper_validation_conflicts",
                f"paper validation status={paper_status}, conflict_count={paper_conflict_count}이다.",
            )
        )
    elif paper_status != "passed":
        if safety_policy.get("decision") == SAFETY_INTERLOCK_POLICY_DECISION:
            warnings.append(
                _warning(
                    "paper_actions_blocked_by_intentional_safety_interlock",
                    "paper validation conflict는 0이지만 kill switch/human approval 안전장치 때문에 order action은 계속 차단된다.",
                )
            )
        else:
            blockers.append(
                _blocker(
                    "blocked_by_paper_validation_failed",
                    f"paper validation status={paper_status}이지만 conflict_count는 0이다. safety interlock 또는 승인 gate를 별도로 확인해야 한다.",
                )
            )
    elif paper_approved_action_count <= 0:
        warnings.append(
            _warning(
                "paper_validation_has_no_approved_actions",
                "paper validation은 통과했지만 승인 가능한 paper action이 없다. 실제 action 확대 전 별도 확인이 필요하다.",
            )
        )

    if outcome_count > 0 and positive_outcome_count == 0:
        blockers.append(_blocker("blocked_by_no_positive_outcomes", "성과 표본은 있으나 positive/outperform outcome이 0건이다."))
    elif positive_outcome_count < min(3, min_component_outcome_count):
        warnings.append(
            _warning(
                "positive_outcome_sample_is_thin",
                f"positive/outperform outcome이 {positive_outcome_count}건이라 component spread 해석 신뢰도가 낮다.",
            )
        )

    component_reviews = _component_reviews(
        _as_list(score.get("component_metrics")),
        min_component_outcome_count=min_component_outcome_count,
    )
    decision = blockers[0]["code"] if blockers else READY_DECISION
    return {
        "audit_name": DEFAULT_AUDIT_EVAL_NAME,
        "source_eval_run_id": source_eval_run_id,
        "source_quality_status": quality_status,
        "decision": decision,
        "manual_weight_review_allowed": decision == READY_DECISION,
        "automatic_weight_change_allowed": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "recommendation_scoring_mutated": False,
        "blockers": blockers,
        "warnings": warnings,
        "sample": {
            "sample_status": sample_status,
            "outcome_count": outcome_count,
            "positive_outcome_count": positive_outcome_count,
            "outcome_coverage_rate": score.get("outcome_coverage_rate"),
            "positive_outcome_rate": score.get("positive_outcome_rate"),
            "horizon_days": score.get("horizon_days"),
        },
        "outcome_calibration_gate": outcome_calibration_gate,
        "professional_analysis_coverage": professional_coverage,
        "paper_validation": {
            "latest_status": paper_status,
            "validation_date": paper_validation.get("validation_date"),
            "recommendation_count": _int(paper_validation.get("recommendation_count")),
            "conflict_count": paper_conflict_count,
            "approved_action_count": paper_approved_action_count,
        },
        "paper_safety_interlock_policy": {
            "run_id": _int(safety_policy.get("run_id")),
            "paper_validation_run_id": _int(safety_policy.get("paper_validation_run_id")),
            "decision": safety_policy.get("decision"),
            "is_intentional_safety_interlock": safety_policy.get("decision") == SAFETY_INTERLOCK_POLICY_DECISION,
            "weight_review_allowed_by_policy": safety_policy.get("decision") == SAFETY_INTERLOCK_POLICY_DECISION,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
        },
        "guardrails": {
            "cycle_weight_unchanged": bool(cycle_guardrail.get("cycle_weight_unchanged")),
            "fundamental_weight_unchanged": bool(fundamental_guardrail.get("fundamental_weight_unchanged")),
        },
        "component_reviews": component_reviews,
        "next_action": _next_action(decision),
    }


def run_recommendation_weight_review_readiness_audit(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    eval_run_id: int | None = None,
    outcome_calibration_eval_run_id: int | None = None,
    min_component_outcome_count: int = DEFAULT_MIN_COMPONENT_OUTCOME_COUNT,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    source_eval = load_recommendation_weight_review_source_eval(
        config=config,
        as_of_date=as_of_date,
        eval_run_id=eval_run_id,
        executor=sql_executor,
    )
    source_score = _as_dict(source_eval.get("score_json"))
    if not source_score:
        raise ValueError("Recommendation quality eval score_json is empty.")
    source_eval_run_id = _int(source_eval.get("eval_run_id"))
    safety_policy = load_paper_safety_interlock_policy(
        config=config,
        as_of_date=as_of_date,
        executor=sql_executor,
    )
    outcome_calibration_eval = load_recommendation_outcome_calibration_eval(
        config=config,
        as_of_date=as_of_date,
        eval_run_id=outcome_calibration_eval_run_id,
        executor=sql_executor,
    )
    audit = audit_recommendation_weight_review_readiness(
        source_score,
        source_eval_run_id=source_eval_run_id,
        min_component_outcome_count=min_component_outcome_count,
        paper_safety_policy=safety_policy,
        outcome_calibration_eval=outcome_calibration_eval,
    )
    report: dict[str, object] = {
        "report_name": DEFAULT_AUDIT_EVAL_NAME,
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "source_eval": {
            "eval_run_id": source_eval_run_id,
            "eval_name": source_eval.get("eval_name"),
            "dataset_version": source_eval.get("dataset_version"),
            "provider": source_eval.get("provider"),
            "model_name": source_eval.get("model_name"),
            "created_at": source_eval.get("created_at"),
        },
        "outcome_calibration_eval": {
            "eval_run_id": _int(outcome_calibration_eval.get("eval_run_id")),
            "eval_name": outcome_calibration_eval.get("eval_name"),
            "dataset_version": outcome_calibration_eval.get("dataset_version"),
            "provider": outcome_calibration_eval.get("provider"),
            "model_name": outcome_calibration_eval.get("model_name"),
            "created_at": outcome_calibration_eval.get("created_at"),
        },
        "audit": audit,
    }
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "source_eval_run_id": source_eval_run_id,
            "outcome_calibration_eval_run_id": audit["outcome_calibration_gate"]["eval_run_id"],
            "outcome_calibration_status": audit["outcome_calibration_gate"]["status"],
            "decision": audit["decision"],
            "manual_weight_review_allowed": audit["manual_weight_review_allowed"],
            "automatic_weight_change_allowed": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "paper_safety_interlock_decision": audit["paper_safety_interlock_policy"]["decision"],
            "recommendation_scoring_mutated": False,
        },
    )
    try:
        audit_eval_run_id = int(
            sql_executor.execute_scalar(
                render_recommendation_weight_review_audit_insert_sql(score_json=audit)
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
        "audit_eval_run_id": audit_eval_run_id,
    }


def _outcome_calibration_gate(eval_payload: dict[str, object] | None) -> dict[str, object]:
    payload = _as_dict(eval_payload)
    score = _as_dict(payload.get("score_json"))
    if not payload or not score:
        return {
            "status": "missing",
            "eval_run_id": 0,
            "eval_name": OUTCOME_CALIBRATION_EVAL_NAME,
            "dataset_version": OUTCOME_CALIBRATION_DATASET_VERSION,
            "as_of_date": None,
            "horizon_days": [],
            "quality_status": "unknown",
            "sample_status": "unknown",
            "recommendation_horizon_count": 0,
            "recommendation_count": 0,
            "outcome_count": 0,
            "ready_for_backfill_count": 0,
            "missing_entry_price_count": 0,
            "missing_exit_price_count": 0,
            "missing_reason_counts": {},
            "next_action": "recommendation-outcome-calibration-sample-expansion-run을 먼저 실행한다.",
        }
    after_summary = _as_dict(_as_dict(score.get("sample_audit_after")).get("summary"))
    missing_reason_counts = _as_dict(_as_dict(score.get("sample_audit_after")).get("missing_reason_counts"))
    outcome_delta = _as_dict(score.get("outcome_delta"))
    return {
        "status": str(score.get("status") or "unknown"),
        "eval_run_id": _int(payload.get("eval_run_id")),
        "eval_name": payload.get("eval_name"),
        "dataset_version": payload.get("dataset_version"),
        "as_of_date": score.get("as_of_date"),
        "horizon_days": _int_list(score.get("horizon_days")),
        "quality_status": str(score.get("quality_status") or "unknown"),
        "sample_status": str(score.get("sample_status") or "unknown"),
        "recommendation_horizon_count": _int(after_summary.get("recommendation_horizon_count")),
        "recommendation_count": _int(after_summary.get("recommendation_count")),
        "outcome_count": _int(after_summary.get("outcome_count")),
        "ready_for_backfill_count": _int(outcome_delta.get("ready_for_backfill_count_after")),
        "missing_entry_price_count": _int(after_summary.get("missing_entry_price_count")),
        "missing_exit_price_count": _int(after_summary.get("missing_exit_price_count")),
        "missing_reason_counts": {
            str(key): _int(value)
            for key, value in missing_reason_counts.items()
        },
        "next_action": str(score.get("next_action") or "성과 calibration 상태를 확인한다."),
    }


def _outcome_calibration_blocker(gate: dict[str, object]) -> dict[str, object]:
    status = str(gate.get("status") or "missing")
    if status in OUTCOME_CALIBRATION_BLOCKING_STATUSES:
        code = f"blocked_by_outcome_calibration_{status}"
    else:
        code = "blocked_by_outcome_calibration_not_ready"
    next_action = str(gate.get("next_action") or "성과 calibration gate를 먼저 통과시켜야 한다.")
    if status == "missing":
        message = "최신 recommendation outcome calibration eval이 없다. quality eval만으로는 weight review를 열 수 없다."
    elif status == "no_due_outcome_window":
        message = "선택한 30/90/180/365일 성과 측정창이 아직 도래하지 않았다. quality eval이 ready여도 weight review는 대기해야 한다."
    elif status == "backfill_candidates_remain":
        message = "성과 산출 가능한 추천×기간 후보가 남아 있다. backfill을 먼저 완료해야 한다."
    elif status == "price_history_gaps_remain":
        message = "성과 산출에 필요한 entry/exit 가격 이력이 부족하다. 캔들 보강이 먼저다."
    elif status == "no_outcome_sample_available":
        message = "성과 표본이 없다. 추천 weight 검토를 시작할 근거가 부족하다."
    else:
        message = f"outcome calibration status가 {status}이다. ready_for_manual_weight_review 전까지 weight review를 열 수 없다."
    return {
        "code": code,
        "message": message,
        "outcome_calibration_status": status,
        "outcome_calibration_eval_run_id": _int(gate.get("eval_run_id")),
        "next_action": next_action,
    }


def _component_reviews(
    component_metrics: list[dict[str, object]],
    *,
    min_component_outcome_count: int,
) -> list[dict[str, object]]:
    reviews: list[dict[str, object]] = []
    for item in component_metrics:
        outcome_count = _int(item.get("outcome_count"))
        spread = _decimal(item.get("positive_score_spread"))
        avg_weight = _decimal(item.get("avg_component_weight"))
        if outcome_count < min_component_outcome_count:
            readiness = "insufficient_component_sample"
        elif spread is None:
            readiness = "missing_component_spread"
        elif spread <= 0:
            readiness = "do_not_increase_weight"
        elif avg_weight is not None and avg_weight != 0:
            readiness = "already_weighted_review_only"
        else:
            readiness = "eligible_for_manual_pilot_review"
        reviews.append(
            {
                "component_name": item.get("component_name"),
                "outcome_count": outcome_count,
                "positive_score_spread": _decimal_text(spread),
                "avg_component_weight": _decimal_text(avg_weight),
                "readiness": readiness,
                "automatic_weight_change_allowed": False,
            }
        )
    return sorted(
        reviews,
        key=lambda item: (
            item["readiness"] == "eligible_for_manual_pilot_review",
            abs(float(item["positive_score_spread"] or 0)),
        ),
        reverse=True,
    )


def _next_action(decision: str) -> str:
    if decision == READY_DECISION:
        return "자동 weight 변경은 금지한다. component별 spread와 실패 케이스를 사람이 검토한 뒤 별도 pilot-weight task를 열 수 있다."
    if decision.startswith("blocked_by_outcome_calibration_"):
        return "horizon-grid 성과 calibration gate를 먼저 통과해야 한다. quality eval이 ready여도 추천 weight는 그대로 둔다."
    if decision == "blocked_by_paper_validation_conflicts":
        return "paper validation conflict를 먼저 해소해야 한다. 추천 weight 변경과 action 확대는 계속 금지한다."
    if decision == "blocked_by_paper_validation_failed":
        return "paper validation conflict는 해소됐지만 validation status가 아직 failed다. kill switch/human approval 같은 safety interlock을 별도 task에서 확인해야 한다."
    if decision == "blocked_by_insufficient_sample":
        return "outcome 표본을 더 쌓아야 한다. 30일 이상 중장기 horizon 표본이 충분해질 때까지 weight 변경 금지."
    if decision == "blocked_by_insufficient_professional_coverage":
        return "active recommendation의 전문 분석 coverage를 먼저 보강해야 한다."
    if decision.startswith("blocked_by_unapproved"):
        return "이미 weight가 변경된 component가 있다. 승인 이력과 배포 이력을 먼저 감사해야 한다."
    return "차단 사유를 해소한 뒤 readiness audit를 다시 실행한다."


def _blocker(code: str, message: str) -> dict[str, object]:
    return {"code": code, "message": message}


def _warning(code: str, message: str) -> dict[str, object]:
    return {"code": code, "message": message}


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _int_list(value: object) -> list[int]:
    if not isinstance(value, list):
        return []
    result: list[int] = []
    for item in value:
        try:
            result.append(int(str(item)))
        except (TypeError, ValueError):
            continue
    return result


def _int(value: object) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _decimal_text(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value, "f")
