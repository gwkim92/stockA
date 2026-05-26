from __future__ import annotations

import json
from collections import Counter
from datetime import date
from typing import Any

from stockanalysis.frontend.live_adapter import DEFAULT_PORTFOLIO_NAME
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_EVAL_NAME = "portfolio_review_feedback_calibration"
DEFAULT_DATASET_VERSION = "portfolio-review-feedback-calibration-v1"
DEFAULT_PIPELINE_NAME = "portfolio_review_feedback_calibration"
DEFAULT_PROVIDER = "deterministic_portfolio_review_feedback_calibration"
DEFAULT_MODEL_NAME = "portfolio-review-feedback-calibration-v1"
DEFAULT_LOOKBACK_DAYS = 365
DEFAULT_LIMIT = 50
DEFAULT_MIN_FEEDBACK_RUNS = 3
DEFAULT_MIN_MATURE_DECISIONS = 10
DEFAULT_MAX_CONTRADICTION_RATE = 0.15


def render_portfolio_review_feedback_artifacts_lookup_sql(
    *,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
    as_of_date: date,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    limit: int = DEFAULT_LIMIT,
) -> str:
    if lookback_days < 1:
        raise ValueError("lookback_days must be positive.")
    if limit < 1:
        raise ValueError("limit must be positive.")
    return f"""-- portfolio review feedback calibration artifacts lookup
with feedback_runs as (
    select
        eval_run.eval_run_id,
        eval_run.created_at,
        eval_run.score_json
    from ai.eval_run eval_run
    where eval_run.eval_name = 'portfolio_review_decision_outcome_feedback'
      and eval_run.dataset_version = 'portfolio-review-decision-outcome-feedback-v1'
      and coalesce(eval_run.score_json->>'portfolio_name', {sql_literal(portfolio_name)}) = {sql_literal(portfolio_name)}
      and nullif(eval_run.score_json->>'as_of_date', '')::date <= {sql_date(as_of_date)}
      and nullif(eval_run.score_json->>'as_of_date', '')::date >= ({sql_date(as_of_date)} - {int(lookback_days)})
    order by
        nullif(eval_run.score_json->>'as_of_date', '')::date desc nulls last,
        eval_run.created_at desc,
        eval_run.eval_run_id desc
    limit {int(limit)}
)
select coalesce(
    json_agg(
        json_build_object(
            'eval_run_id', eval_run_id,
            'created_at', created_at,
            'score_json', score_json
        )
        order by created_at desc, eval_run_id desc
    ),
    '[]'::json
)::text
from feedback_runs;"""


def load_portfolio_review_feedback_artifacts(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    as_of_date: date,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    limit: int = DEFAULT_LIMIT,
    executor: PsqlCommandExecutor | None = None,
) -> list[dict[str, object]]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_portfolio_review_feedback_artifacts_lookup_sql(
                portfolio_name=portfolio_name,
                as_of_date=as_of_date,
                lookback_days=lookback_days,
                limit=limit,
            )
        )
    )
    if not isinstance(payload, list):
        raise ValueError("Portfolio review feedback artifact lookup did not return a JSON array.")
    return [item for item in payload if isinstance(item, dict)]


def build_portfolio_review_feedback_calibration(
    *,
    feedback_artifacts: list[dict[str, object]],
    portfolio_name: str,
    as_of_date: date,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    min_feedback_runs: int = DEFAULT_MIN_FEEDBACK_RUNS,
    min_mature_decisions: int = DEFAULT_MIN_MATURE_DECISIONS,
    max_contradiction_rate: float = DEFAULT_MAX_CONTRADICTION_RATE,
) -> dict[str, object]:
    if lookback_days < 1:
        raise ValueError("lookback_days must be positive.")
    if min_feedback_runs < 1:
        raise ValueError("min_feedback_runs must be positive.")
    if min_mature_decisions < 1:
        raise ValueError("min_mature_decisions must be positive.")
    if max_contradiction_rate < 0 or max_contradiction_rate > 1:
        raise ValueError("max_contradiction_rate must be between 0 and 1.")

    normalized_artifacts = [_feedback_artifact_payload(item) for item in feedback_artifacts]
    all_items: list[dict[str, Any]] = []
    run_summaries: list[dict[str, object]] = []
    for artifact in normalized_artifacts:
        score = artifact["score_json"]
        items = _as_list(score.get("items")) or _as_list(score.get("latest_items"))
        all_items.extend(items)
        run_summaries.append(
            {
                "eval_run_id": _int(artifact.get("eval_run_id")),
                "created_at": str(artifact.get("created_at") or ""),
                "as_of_date": str(score.get("as_of_date") or ""),
                "feedback_status": str(score.get("feedback_status") or ""),
                "decision_count": _int(score.get("decision_count")) or len(items),
                "too_early_count": _int(score.get("too_early_count")) or 0,
                "validated_count": _int(score.get("validated_count")) or 0,
                "contradicted_count": _int(score.get("contradicted_count")) or 0,
                "needs_more_data_count": _int(score.get("needs_more_data_count")) or 0,
            }
        )

    status_counts = Counter(str(item.get("feedback_status") or "unknown") for item in all_items)
    decision_count = len(all_items)
    feedback_run_count = len(normalized_artifacts)
    too_early_count = status_counts.get("too_early", 0)
    validated_count = status_counts.get("validated", 0)
    contradicted_count = status_counts.get("contradicted", 0)
    needs_more_data_count = status_counts.get("needs_more_data", 0)
    mature_decision_count = validated_count + contradicted_count
    contradiction_rate = _ratio(contradicted_count, mature_decision_count)
    validated_rate = _ratio(validated_count, mature_decision_count)
    calibration_status = _calibration_status(
        feedback_run_count=feedback_run_count,
        decision_count=decision_count,
        mature_decision_count=mature_decision_count,
        too_early_count=too_early_count,
        needs_more_data_count=needs_more_data_count,
        contradiction_rate=contradiction_rate,
        max_contradiction_rate=max_contradiction_rate,
        min_feedback_runs=min_feedback_runs,
        min_mature_decisions=min_mature_decisions,
    )

    return {
        "eval_name": DEFAULT_EVAL_NAME,
        "dataset_version": DEFAULT_DATASET_VERSION,
        "as_of_date": as_of_date.isoformat(),
        "portfolio_name": portfolio_name,
        "lookback_days": lookback_days,
        "min_feedback_runs": min_feedback_runs,
        "min_mature_decisions": min_mature_decisions,
        "max_contradiction_rate": max_contradiction_rate,
        "calibration_status": calibration_status,
        "feedback_run_count": feedback_run_count,
        "decision_count": decision_count,
        "mature_decision_count": mature_decision_count,
        "too_early_count": too_early_count,
        "validated_count": validated_count,
        "contradicted_count": contradicted_count,
        "needs_more_data_count": needs_more_data_count,
        "contradiction_rate": contradiction_rate,
        "validated_rate": validated_rate,
        "status_counts": dict(status_counts),
        "family_summaries": _group_summaries(all_items, key_name="decision_family"),
        "decision_type_summaries": _group_summaries(all_items, key_name="decision_type"),
        "symbol_summaries": _group_summaries(all_items, key_name="symbol", limit=15),
        "latest_feedback_runs": run_summaries[:10],
        "guardrails": {
            "recommendation_scoring_mutated": False,
            "benchmark_definition_mutated": False,
            "portfolio_position_mutated": False,
            "automatic_rebalance_allowed": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "order_boundary": "read_only_no_order",
        },
        "next_action": _next_action(calibration_status),
    }


def render_portfolio_review_feedback_calibration_insert_sql(
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


def run_portfolio_review_feedback_calibration(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    as_of_date: date,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    limit: int = DEFAULT_LIMIT,
    min_feedback_runs: int = DEFAULT_MIN_FEEDBACK_RUNS,
    min_mature_decisions: int = DEFAULT_MIN_MATURE_DECISIONS,
    max_contradiction_rate: float = DEFAULT_MAX_CONTRADICTION_RATE,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    artifacts = load_portfolio_review_feedback_artifacts(
        config=config,
        portfolio_name=portfolio_name,
        as_of_date=as_of_date,
        lookback_days=lookback_days,
        limit=limit,
        executor=sql_executor,
    )
    calibration = build_portfolio_review_feedback_calibration(
        feedback_artifacts=artifacts,
        portfolio_name=portfolio_name,
        as_of_date=as_of_date,
        lookback_days=lookback_days,
        min_feedback_runs=min_feedback_runs,
        min_mature_decisions=min_mature_decisions,
        max_contradiction_rate=max_contradiction_rate,
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
        "calibration": calibration,
    }
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "portfolio_name": portfolio_name,
            "as_of_date": as_of_date.isoformat(),
            "lookback_days": lookback_days,
            "feedback_run_count": calibration["feedback_run_count"],
            "decision_count": calibration["decision_count"],
            "calibration_status": calibration["calibration_status"],
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
        },
    )
    try:
        eval_run_id = int(
            sql_executor.execute_scalar(
                render_portfolio_review_feedback_calibration_insert_sql(score_json=calibration)
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
    }


def _calibration_status(
    *,
    feedback_run_count: int,
    decision_count: int,
    mature_decision_count: int,
    too_early_count: int,
    needs_more_data_count: int,
    contradiction_rate: float,
    max_contradiction_rate: float,
    min_feedback_runs: int,
    min_mature_decisions: int,
) -> str:
    if feedback_run_count < min_feedback_runs or decision_count == 0:
        return "insufficient_history"
    if mature_decision_count > 0 and contradiction_rate > max_contradiction_rate:
        return "contradiction_review_required"
    if mature_decision_count < min_mature_decisions or too_early_count > 0 or needs_more_data_count > 0:
        return "collect_more_feedback"
    return "manual_review_ready"


def _group_summaries(items: list[dict[str, Any]], *, key_name: str, limit: int | None = None) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        key = str(item.get(key_name) or "unknown")
        grouped.setdefault(key, []).append(item)
    summaries: list[dict[str, object]] = []
    for key, group_items in grouped.items():
        counts = Counter(str(item.get("feedback_status") or "unknown") for item in group_items)
        mature_count = counts.get("validated", 0) + counts.get("contradicted", 0)
        summaries.append(
            {
                key_name: key,
                "decision_count": len(group_items),
                "mature_decision_count": mature_count,
                "too_early_count": counts.get("too_early", 0),
                "validated_count": counts.get("validated", 0),
                "contradicted_count": counts.get("contradicted", 0),
                "needs_more_data_count": counts.get("needs_more_data", 0),
                "contradiction_rate": _ratio(counts.get("contradicted", 0), mature_count),
                "status_counts": dict(counts),
            }
        )
    summaries.sort(
        key=lambda item: (
            -int(item["contradicted_count"]),
            -int(item["needs_more_data_count"]),
            -int(item["too_early_count"]),
            -int(item["decision_count"]),
            str(item.get(key_name) or ""),
        )
    )
    return summaries[:limit] if limit is not None else summaries


def _feedback_artifact_payload(value: dict[str, object]) -> dict[str, Any]:
    score = _as_dict(value.get("score_json"))
    return {
        "eval_run_id": value.get("eval_run_id"),
        "created_at": value.get("created_at"),
        "score_json": score,
    }


def _next_action(calibration_status: str) -> str:
    if calibration_status == "insufficient_history":
        return "portfolio-review-decision-outcome-feedback-run 결과가 더 쌓일 때까지 weight 검토를 금지한다."
    if calibration_status == "contradiction_review_required":
        return "반박된 검토 결정의 thesis, valuation, 포지션 정책을 먼저 수동 점검한다."
    if calibration_status == "collect_more_feedback":
        return "성과 window가 끝난 feedback을 더 누적한 뒤 calibration을 재실행한다."
    if calibration_status == "manual_review_ready":
        return "자동 weight 변경은 여전히 금지하고, 별도 승인된 manual pilot review task에서만 검토한다."
    return "feedback calibration 상태를 확인한다."


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(float(numerator) / float(denominator), 6)


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None
