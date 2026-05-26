from __future__ import annotations

import json
from datetime import date
from decimal import Decimal, InvalidOperation

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.recommendation_weight_review_readiness_audit import (
    DEFAULT_AUDIT_DATASET_VERSION as SOURCE_AUDIT_DATASET_VERSION,
    DEFAULT_AUDIT_EVAL_NAME as SOURCE_AUDIT_EVAL_NAME,
    READY_DECISION,
)
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_REPORT_NAME = "manual_weight_review_calibration_report"
DEFAULT_PIPELINE_NAME = "manual_weight_review_calibration_report"
DEFAULT_DATASET_VERSION = "manual-weight-review-calibration-v1"
DEFAULT_PROVIDER = "postgres"
DEFAULT_MODEL_NAME = "deterministic-calibration-report-v1"
DEFAULT_FAILURE_CASE_LIMIT = 10
POSITIVE_OUTCOME_LABELS = ("positive", "outperform")


def render_manual_weight_review_audit_eval_lookup_sql(
    *,
    as_of_date: date,
    audit_eval_run_id: int | None = None,
) -> str:
    eval_filter = ""
    date_filter = f"\n      and eval_run.created_at::date <= {sql_date(as_of_date)}"
    if audit_eval_run_id is not None:
        if audit_eval_run_id <= 0:
            raise ValueError("audit_eval_run_id must be greater than 0.")
        eval_filter = f"\n      and eval_run.eval_run_id = {audit_eval_run_id}"
        date_filter = ""
    return f"""-- manual weight review calibration source audit eval lookup
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
    where eval_run.eval_name = {sql_literal(SOURCE_AUDIT_EVAL_NAME)}
      and eval_run.dataset_version = {sql_literal(SOURCE_AUDIT_DATASET_VERSION)}
      and nullif(eval_run.score_json->>'source_eval_run_id', '')::bigint is not null
      and coalesce(nullif(eval_run.score_json->>'source_quality_status', ''), 'unknown') <> 'unknown'{date_filter}{eval_filter}
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


def render_manual_weight_review_failure_case_lookup_sql(
    *,
    as_of_date: date,
    horizon_days: int,
    limit: int = DEFAULT_FAILURE_CASE_LIMIT,
) -> str:
    if horizon_days < 1 or horizon_days > 3650:
        raise ValueError("horizon_days must be between 1 and 3650.")
    if limit < 0 or limit > 100:
        raise ValueError("limit must be between 0 and 100.")
    positive_labels = ", ".join(sql_literal(label) for label in POSITIVE_OUTCOME_LABELS)
    return f"""-- manual weight review calibration failure case lookup
with recommendation_window as (
    select
        recommendation.recommendation_id,
        recommendation.instrument_id,
        instrument.primary_symbol,
        recommendation.bucket,
        recommendation.action,
        recommendation.total_score,
        batch.as_of_date as recommendation_date,
        batch.strategy_name,
        batch.horizon_type
    from signal.recommendation recommendation
    join signal.recommendation_batch batch on batch.batch_id = recommendation.batch_id
    join ref.instrument instrument on instrument.instrument_id = recommendation.instrument_id
    where batch.as_of_date <= {sql_date(as_of_date)}
      and recommendation.status = 'active'
),
outcome_window as (
    select distinct on (outcome.recommendation_id)
        outcome.recommendation_id,
        outcome.measurement_start_date,
        outcome.measurement_end_date,
        outcome.horizon_days,
        outcome.absolute_return_pct,
        outcome.benchmark_return_pct,
        outcome.alpha_pct,
        outcome.max_drawdown_pct,
        outcome.outcome_label
    from performance.recommendation_outcome outcome
    join recommendation_window recommendation on recommendation.recommendation_id = outcome.recommendation_id
    where outcome.measurement_end_date <= {sql_date(as_of_date)}
      and outcome.horizon_days <= {horizon_days}
    order by outcome.recommendation_id, outcome.measurement_end_date desc
),
failure_rows as (
    select
        recommendation.recommendation_id,
        recommendation.primary_symbol,
        recommendation.bucket,
        recommendation.action,
        recommendation.total_score,
        recommendation.recommendation_date,
        recommendation.strategy_name,
        recommendation.horizon_type,
        outcome.outcome_label,
        outcome.measurement_start_date,
        outcome.measurement_end_date,
        outcome.horizon_days,
        outcome.absolute_return_pct,
        outcome.benchmark_return_pct,
        outcome.alpha_pct,
        outcome.max_drawdown_pct,
        coalesce(
            (
                select json_agg(
                    json_build_object(
                        'component_name', component.component_name,
                        'component_score', component.component_score,
                        'component_weight', component.component_weight
                    )
                    order by component.component_name
                )
                from signal.recommendation_score_component component
                where component.recommendation_id = recommendation.recommendation_id
            ),
            '[]'::json
        ) as component_scores
    from recommendation_window recommendation
    join outcome_window outcome on outcome.recommendation_id = recommendation.recommendation_id
    where outcome.outcome_label not in ({positive_labels})
    order by outcome.alpha_pct asc nulls last, outcome.max_drawdown_pct asc nulls last, recommendation.recommendation_id desc
    limit {limit}
)
select coalesce(json_agg(row_to_json(failure_rows)), '[]'::json)::text
from failure_rows;"""


def render_manual_weight_review_calibration_insert_sql(*, score_json: dict[str, object]) -> str:
    score_text = json.dumps(score_json, ensure_ascii=False, sort_keys=True)
    return f"""insert into ai.eval_run (
    eval_name,
    dataset_version,
    provider,
    model_name,
    score_json
)
values (
    {sql_literal(DEFAULT_REPORT_NAME)},
    {sql_literal(DEFAULT_DATASET_VERSION)},
    {sql_literal(DEFAULT_PROVIDER)},
    {sql_literal(DEFAULT_MODEL_NAME)},
    {sql_literal(score_text)}::jsonb
)
returning eval_run_id;"""


def load_manual_weight_review_audit_eval(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    audit_eval_run_id: int | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_manual_weight_review_audit_eval_lookup_sql(
                as_of_date=as_of_date,
                audit_eval_run_id=audit_eval_run_id,
            )
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Manual weight review audit eval lookup did not return a JSON object.")
    if not payload:
        selector = (
            f"audit_eval_run_id={audit_eval_run_id}"
            if audit_eval_run_id is not None
            else f"as_of_date<={as_of_date.isoformat()}"
        )
        raise ValueError(f"No recommendation weight review audit eval_run found for {selector}.")
    return payload


def load_manual_weight_review_failure_cases(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    horizon_days: int,
    limit: int = DEFAULT_FAILURE_CASE_LIMIT,
    executor: PsqlCommandExecutor | None = None,
) -> list[dict[str, object]]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_manual_weight_review_failure_case_lookup_sql(
                as_of_date=as_of_date,
                horizon_days=horizon_days,
                limit=limit,
            )
        )
    )
    if not isinstance(payload, list):
        raise ValueError("Manual weight review failure case lookup did not return a JSON array.")
    rows: list[dict[str, object]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Manual weight review failure case lookup returned a non-object row.")
        rows.append(item)
    return rows


def build_manual_weight_review_calibration_report(
    *,
    as_of_date: date,
    audit_eval: dict[str, object],
    failure_cases: list[dict[str, object]],
    execute: bool = False,
) -> dict[str, object]:
    audit = _as_dict(audit_eval.get("score_json"))
    if not audit:
        raise ValueError("Manual weight review source audit score_json is empty.")
    sample = _as_dict(audit.get("sample"))
    component_reviews = [_as_dict(item) for item in _as_list(audit.get("component_reviews"))]
    component_groups = _group_component_reviews(component_reviews)
    manual_review_allowed = bool(audit.get("manual_weight_review_allowed"))
    eligible_count = len(component_groups["eligible_for_manual_pilot_review"])
    keep_zero_count = len(component_groups["keep_zero_or_do_not_increase"])
    decision = _decision(
        manual_review_allowed=manual_review_allowed,
        eligible_count=eligible_count,
        failure_case_count=len(failure_cases),
    )
    return {
        "report_name": DEFAULT_REPORT_NAME,
        "status": "planned" if not execute else "running",
        "execute": execute,
        "as_of_date": as_of_date.isoformat(),
        "source_audit_eval": {
            "eval_run_id": _int(audit_eval.get("eval_run_id")),
            "eval_name": audit_eval.get("eval_name"),
            "dataset_version": audit_eval.get("dataset_version"),
            "created_at": audit_eval.get("created_at"),
            "source_quality_eval_run_id": _int(audit.get("source_eval_run_id")),
            "source_quality_status": audit.get("source_quality_status"),
        },
        "decision": decision,
        "manual_weight_review_allowed": manual_review_allowed,
        "automatic_weight_change_allowed": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "recommendation_scoring_mutated": False,
        "korean_summary": _korean_summary(
            manual_review_allowed=manual_review_allowed,
            eligible_count=eligible_count,
            keep_zero_count=keep_zero_count,
            failure_case_count=len(failure_cases),
        ),
        "sample": {
            "sample_status": sample.get("sample_status"),
            "outcome_count": _int(sample.get("outcome_count")),
            "positive_outcome_count": _int(sample.get("positive_outcome_count")),
            "positive_outcome_rate": sample.get("positive_outcome_rate"),
            "horizon_days": _int(sample.get("horizon_days")),
        },
        "component_summary": _component_summary(component_groups, component_reviews),
        "component_groups": component_groups,
        "failure_case_examples": [_failure_case_payload(item) for item in failure_cases],
        "safety_boundary": {
            "weight_change_policy": "automatic_weight_change_forbidden_until_explicit_pilot_task",
            "paper_order_policy": "paper_actions_still_require_safety_interlock_release",
            "broker_policy": "live_broker_submit_out_of_scope",
        },
        "next_actions": _next_actions(decision, eligible_count=eligible_count),
    }


def run_manual_weight_review_calibration_report(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    audit_eval_run_id: int | None = None,
    failure_case_limit: int = DEFAULT_FAILURE_CASE_LIMIT,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    audit_eval = load_manual_weight_review_audit_eval(
        config=config,
        as_of_date=as_of_date,
        audit_eval_run_id=audit_eval_run_id,
        executor=sql_executor,
    )
    audit = _as_dict(audit_eval.get("score_json"))
    sample = _as_dict(audit.get("sample"))
    horizon_days = _int(sample.get("horizon_days")) or 30
    failure_cases = load_manual_weight_review_failure_cases(
        config=config,
        as_of_date=as_of_date,
        horizon_days=horizon_days,
        limit=failure_case_limit,
        executor=sql_executor,
    )
    report = build_manual_weight_review_calibration_report(
        as_of_date=as_of_date,
        audit_eval=audit_eval,
        failure_cases=failure_cases,
        execute=execute,
    )
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "source_audit_eval_run_id": report["source_audit_eval"]["eval_run_id"],
            "decision": report["decision"],
            "automatic_weight_change_allowed": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "recommendation_scoring_mutated": False,
        },
    )
    try:
        report_eval_run_id = int(
            sql_executor.execute_scalar(
                render_manual_weight_review_calibration_insert_sql(score_json={**report, "status": "completed"})
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
        "report_eval_run_id": report_eval_run_id,
    }


def _group_component_reviews(component_reviews: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    groups = {
        "eligible_for_manual_pilot_review": [],
        "already_weighted_review_only": [],
        "keep_zero_or_do_not_increase": [],
        "insufficient_or_missing_evidence": [],
        "other": [],
    }
    for item in component_reviews:
        readiness = str(item.get("readiness") or "other")
        payload = {
            "component_name": item.get("component_name"),
            "readiness": readiness,
            "outcome_count": _int(item.get("outcome_count")),
            "positive_score_spread": item.get("positive_score_spread"),
            "avg_component_weight": item.get("avg_component_weight"),
            "automatic_weight_change_allowed": False,
        }
        if readiness == "eligible_for_manual_pilot_review":
            groups["eligible_for_manual_pilot_review"].append(payload)
        elif readiness == "already_weighted_review_only":
            groups["already_weighted_review_only"].append(payload)
        elif readiness == "do_not_increase_weight":
            groups["keep_zero_or_do_not_increase"].append(payload)
        elif readiness in {"insufficient_component_sample", "missing_component_spread"}:
            groups["insufficient_or_missing_evidence"].append(payload)
        else:
            groups["other"].append(payload)
    return groups


def _component_summary(
    component_groups: dict[str, list[dict[str, object]]],
    component_reviews: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "component_count": len(component_reviews),
        "eligible_for_manual_pilot_review_count": len(component_groups["eligible_for_manual_pilot_review"]),
        "already_weighted_review_only_count": len(component_groups["already_weighted_review_only"]),
        "keep_zero_or_do_not_increase_count": len(component_groups["keep_zero_or_do_not_increase"]),
        "insufficient_or_missing_evidence_count": len(component_groups["insufficient_or_missing_evidence"]),
        "other_count": len(component_groups["other"]),
    }


def _decision(*, manual_review_allowed: bool, eligible_count: int, failure_case_count: int) -> str:
    if not manual_review_allowed:
        return "manual_review_not_allowed"
    if eligible_count > 0:
        return "manual_pilot_review_possible_no_automatic_change"
    if failure_case_count > 0:
        return "manual_review_allowed_keep_weights_collect_more_evidence"
    return "manual_review_allowed_no_weight_change"


def _korean_summary(
    *,
    manual_review_allowed: bool,
    eligible_count: int,
    keep_zero_count: int,
    failure_case_count: int,
) -> str:
    if not manual_review_allowed:
        return "아직 추천 weight 수동 검토 조건도 충족하지 못했다. 자동 변경과 주문은 계속 금지한다."
    if eligible_count > 0:
        return (
            f"수동 검토는 가능하지만 자동 weight 변경은 금지다. pilot 후보 {eligible_count}개는 별도 승인 task에서만 다룬다."
        )
    return (
        "수동 검토는 가능하지만 현재 바로 올릴 신규 weight 후보는 없다. "
        f"{keep_zero_count}개 component는 성과 설명력이 약하거나 음수이며, "
        f"부진 outcome 예시 {failure_case_count}건을 먼저 검토해야 한다."
    )


def _next_actions(decision: str, *, eligible_count: int) -> list[str]:
    if decision == "manual_review_not_allowed":
        return [
            "quality eval, paper validation, professional coverage blocker를 먼저 해소한다.",
            "추천 weight와 주문 경계는 그대로 둔다.",
        ]
    actions = [
        "현재 추천 weight를 유지한다.",
        "component별 positive_score_spread와 failure case를 사람이 검토한다.",
        "자동 weight 변경, 자동 주문, broker submit은 계속 금지한다.",
    ]
    if eligible_count > 0:
        actions.append("pilot weight 조정이 필요하면 별도 task contract와 승인 기록을 만든다.")
    else:
        actions.append("신규 zero-weight component는 더 많은 outcome 표본이 쌓일 때까지 0 weight를 유지한다.")
    return actions


def _failure_case_payload(item: dict[str, object]) -> dict[str, object]:
    components = [_as_dict(component) for component in _as_list(item.get("component_scores"))]
    components = sorted(
        (
            {
                "component_name": component.get("component_name"),
                "component_score": _decimal_text(component.get("component_score")),
                "component_weight": _decimal_text(component.get("component_weight")),
            }
            for component in components
        ),
        key=lambda component: str(component.get("component_name") or ""),
    )
    return {
        "recommendation_id": _int(item.get("recommendation_id")),
        "symbol": item.get("primary_symbol"),
        "bucket": item.get("bucket"),
        "action": item.get("action"),
        "total_score": _decimal_text(item.get("total_score")),
        "recommendation_date": item.get("recommendation_date"),
        "outcome_label": item.get("outcome_label"),
        "alpha_pct": _decimal_text(item.get("alpha_pct")),
        "max_drawdown_pct": _decimal_text(item.get("max_drawdown_pct")),
        "measurement_end_date": item.get("measurement_end_date"),
        "component_scores": components,
    }


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _int(value: object) -> int:
    if value is None or value == "":
        return 0
    return int(value)


def _decimal_text(value: object) -> str | None:
    if value is None or value == "":
        return None
    try:
        return format(Decimal(str(value)), "f")
    except (InvalidOperation, ValueError):
        return str(value)
