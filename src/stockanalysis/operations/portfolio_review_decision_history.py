from __future__ import annotations

import json
from collections import Counter
from datetime import date
from typing import Any
from urllib.parse import quote

from stockanalysis.frontend.live_adapter import resolve_live_frontend_response
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_EVAL_NAME = "portfolio_review_decision_history"
DEFAULT_DATASET_VERSION = "portfolio-review-decision-history-v1"
DEFAULT_PIPELINE_NAME = "portfolio_review_decision_history"
DEFAULT_PROVIDER = "deterministic_portfolio_review_policy"
DEFAULT_MODEL_NAME = "portfolio-review-decision-history-v1"


def load_portfolio_review_decision_source(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    as_of_date: date,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, Any]:
    encoded_portfolio = quote(portfolio_name, safe="")
    payload = resolve_live_frontend_response(
        f"/api/portfolio/{encoded_portfolio}/coverage?asOfDate={as_of_date.isoformat()}",
        config=config,
        executor=executor,
    )
    return _as_dict(payload.get("data"))


def build_portfolio_review_decision_history(
    *,
    portfolio_coverage: dict[str, Any],
    portfolio_name: str,
    as_of_date: date,
) -> dict[str, object]:
    risk_budget = _as_dict(portfolio_coverage.get("risk_budget"))
    rebalance_review = _as_dict(risk_budget.get("rebalance_candidate_review"))
    position_sizing_review = _as_dict(risk_budget.get("position_sizing_review"))
    benchmark_decisions = [
        _benchmark_decision(item)
        for item in _as_list(rebalance_review.get("candidates"))
    ]
    position_sizing_decisions = [
        _position_sizing_decision(item)
        for item in _as_list(position_sizing_review.get("candidates"))
    ]
    decisions = [*benchmark_decisions, *position_sizing_decisions]
    decision_counts = dict(Counter(str(item.get("decision_type") or "unknown") for item in decisions))
    review_required_count = sum(1 for item in decisions if item.get("review_required") is True)
    decision_status = "review_required" if review_required_count else "within_policy"

    return {
        "eval_name": DEFAULT_EVAL_NAME,
        "dataset_version": DEFAULT_DATASET_VERSION,
        "as_of_date": as_of_date.isoformat(),
        "portfolio_name": str(portfolio_coverage.get("portfolio_name") or portfolio_name),
        "source_portfolio_coverage_as_of_date": str(portfolio_coverage.get("as_of_date") or ""),
        "coverage_measurement_end_date": str(portfolio_coverage.get("coverage_measurement_end_date") or ""),
        "decision_status": decision_status,
        "decision_count": len(decisions),
        "review_required_count": review_required_count,
        "benchmark_decision_count": len(benchmark_decisions),
        "position_sizing_decision_count": len(position_sizing_decisions),
        "decision_counts": decision_counts,
        "top_decision": decisions[0] if decisions else None,
        "risk_budget_status": str(risk_budget.get("status") or ""),
        "rebalance_candidate_review_status": str(rebalance_review.get("status") or ""),
        "position_sizing_review_status": str(position_sizing_review.get("status") or ""),
        "decisions": decisions,
        "latest_decisions": decisions[:12],
        "guardrails": {
            "recommendation_scoring_mutated": False,
            "benchmark_definition_mutated": False,
            "portfolio_position_mutated": False,
            "automatic_rebalance_allowed": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "order_boundary": "read_only_no_order",
        },
        "next_action": _next_action(decision_status),
    }


def render_portfolio_review_decision_history_insert_sql(
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


def run_portfolio_review_decision_history(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    as_of_date: date,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    portfolio_coverage = load_portfolio_review_decision_source(
        config=config,
        portfolio_name=portfolio_name,
        as_of_date=as_of_date,
        executor=sql_executor,
    )
    decision = build_portfolio_review_decision_history(
        portfolio_coverage=portfolio_coverage,
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
        "decision": decision,
    }
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "portfolio_name": portfolio_name,
            "as_of_date": as_of_date.isoformat(),
            "decision_count": decision["decision_count"],
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
        },
    )
    try:
        eval_run_id = int(
            sql_executor.execute_scalar(
                render_portfolio_review_decision_history_insert_sql(score_json=decision)
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


def _benchmark_decision(candidate: dict[str, Any]) -> dict[str, object]:
    return {
        "decision_family": "benchmark_drift",
        "symbol": str(candidate.get("symbol") or ""),
        "priority": _int(candidate.get("priority")) or 0,
        "decision_type": str(candidate.get("review_decision") or candidate.get("suggested_review_action") or ""),
        "decision_label": str(candidate.get("decision_label") or ""),
        "next_review_action": str(candidate.get("next_review_action") or ""),
        "severity": str(candidate.get("severity") or ""),
        "current_weight": _number(candidate.get("current_weight")),
        "benchmark_weight": _number(candidate.get("benchmark_weight")),
        "active_weight": _number(candidate.get("active_weight")),
        "source_evidence": _as_dict(candidate.get("source_evidence")),
        "related_thesis_id": _optional_text(candidate.get("related_thesis_id")),
        "related_recommendation_id": _optional_text(candidate.get("related_recommendation_id")),
        "related_recommendation_action": _optional_text(candidate.get("related_recommendation_action")),
        "related_recommended_weight": _number(candidate.get("related_recommended_weight")),
        "decision_path": _as_list(candidate.get("decision_path")),
        "rationale": str(candidate.get("rationale") or ""),
        "review_required": True,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": "read_only_no_order",
    }


def _position_sizing_decision(candidate: dict[str, Any]) -> dict[str, object]:
    review_band = str(candidate.get("review_band") or "")
    return {
        "decision_family": "position_sizing",
        "symbol": str(candidate.get("symbol") or ""),
        "instrument_id": _optional_text(candidate.get("instrument_id")),
        "priority": _int(candidate.get("priority")) or 0,
        "decision_type": review_band,
        "decision_label": _position_sizing_label(review_band),
        "next_review_action": str(candidate.get("rationale") or ""),
        "severity": str(candidate.get("severity") or ""),
        "current_weight": _number(candidate.get("current_weight")),
        "benchmark_weight": _number(candidate.get("benchmark_weight")),
        "active_weight": _number(candidate.get("active_weight")),
        "policy_ceiling_weight": _number(candidate.get("policy_ceiling_weight")),
        "review_ceiling_weight": _number(candidate.get("review_ceiling_weight")),
        "source_evidence": {
            "current_weight": _number(candidate.get("current_weight")),
            "benchmark_weight": _number(candidate.get("benchmark_weight")),
            "active_weight": _number(candidate.get("active_weight")),
            "policy_ceiling_weight": _number(candidate.get("policy_ceiling_weight")),
            "review_ceiling_weight": _number(candidate.get("review_ceiling_weight")),
            "review_band": review_band,
        },
        "related_thesis_id": _optional_text(candidate.get("related_thesis_id")),
        "related_recommendation_id": _optional_text(candidate.get("related_recommendation_id")),
        "related_recommendation_action": _optional_text(candidate.get("related_recommendation_action")),
        "related_recommended_weight": _number(candidate.get("related_recommended_weight")),
        "links": _as_dict(candidate.get("links")),
        "thesis_status": str(candidate.get("thesis_status") or ""),
        "professional_analysis_status": str(candidate.get("professional_analysis_status") or ""),
        "blocking_factors": [str(item) for item in _as_scalar_list(candidate.get("blocking_factors"))],
        "supporting_factors": [str(item) for item in _as_scalar_list(candidate.get("supporting_factors"))],
        "rationale": str(candidate.get("rationale") or ""),
        "review_required": review_band in {"reduce_review", "add_blocked_until_evidence"},
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": "read_only_no_order",
    }


def _position_sizing_label(review_band: str) -> str:
    return {
        "reduce_review": "비중 축소 검토",
        "add_blocked_until_evidence": "증거 전 비중 확대 금지",
        "watch_small_position": "작은 비중 관찰",
        "hold_review": "유지 검토",
    }.get(review_band, "포지션 검토")


def _next_action(decision_status: str) -> str:
    if decision_status == "review_required":
        return "최신 포트폴리오 검토 결정을 thesis, valuation, 세금/비용, paper validation과 함께 확인한다."
    return "큰 포트폴리오 검토 결정은 없다. 정기 risk budget과 outcome 검증을 유지한다."


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _as_scalar_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _number(value: object) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _optional_text(value: object) -> str | None:
    if value is None or value == "":
        return None
    return str(value)
