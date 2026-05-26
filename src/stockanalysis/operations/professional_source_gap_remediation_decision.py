from __future__ import annotations

import json
from datetime import date
from typing import Any

from stockanalysis.frontend.live_adapter import load_frontend_data_health_state
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_EVAL_NAME = "professional_source_gap_remediation_decision"
DEFAULT_DATASET_VERSION = "professional-source-gap-remediation-decision-v1"
DEFAULT_PIPELINE_NAME = "professional_source_gap_remediation_decision"
DEFAULT_MODEL_NAME = "deterministic-source-gap-policy-v1"
DEFAULT_PROVIDER = "deterministic_rules"
NON_REMEDIABLE_FREE_PUBLIC_BLOCKERS = {
    "sec_companyfacts_missing_us_gaap_facts",
}
FUND_NOT_APPLICABLE_BLOCKERS = {
    "fund_company_financial_model_not_applicable",
}


def load_professional_source_gap_prioritization(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    state = load_frontend_data_health_state(config=config, executor=executor)
    payload = state.get("professional_source_gap_prioritization")
    if not isinstance(payload, dict):
        return {
            "status": "missing",
            "gap_count": 0,
            "gaps": [],
            "recommendation_scoring_mutated": False,
            "automatic_weight_change_allowed": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "order_boundary": "read_only_no_order",
        }
    return payload


def build_professional_source_gap_remediation_decision(
    source_gap_payload: dict[str, object],
    *,
    as_of_date: date,
) -> dict[str, object]:
    gaps = [_as_dict(item) for item in _as_list(source_gap_payload.get("gaps"))]
    decisions = [_classify_gap(gap, as_of_date=as_of_date) for gap in gaps]
    company_decisions = [item for item in decisions if item["decision_type"] != "fund_not_applicable"]
    top_gap_decision = company_decisions[0] if company_decisions else (decisions[0] if decisions else {})
    next_remediable_gap = next(
        (
            item
            for item in decisions
            if item["remediation_allowed"] is True
            and item["remediation_command"]
            and item["decision_type"] in {"deterministic_remediation_available", "coverage_expansion_available"}
        ),
        {},
    )
    source_blocker_decisions = [
        item for item in decisions if item["decision_type"] == "non_remediable_current_free_public_data"
    ]
    if not decisions:
        decision_status = "no_source_gap"
        next_action = "전문 분석 source gap이 없다. 정기 감시를 유지한다."
    elif next_remediable_gap:
        decision_status = "next_deterministic_remediation_available"
        next_action = (
            f"{next_remediable_gap['symbol']}의 보강 가능한 layer를 기존 backend CLI로 실행한다."
        )
    elif source_blocker_decisions:
        decision_status = "source_blocker_recorded_no_safe_remediation"
        next_action = "합성 재무를 만들지 말고 raw filing/XBRL 대체 parser task를 별도로 계획한다."
    else:
        decision_status = "monitor_source_gaps"
        next_action = "fund/ETF 비적용 또는 낮은 우선순위 gap은 정기 감시한다."
    return {
        "eval_name": DEFAULT_EVAL_NAME,
        "dataset_version": DEFAULT_DATASET_VERSION,
        "as_of_date": as_of_date.isoformat(),
        "decision_status": decision_status,
        "source_gap_status": str(source_gap_payload.get("status") or "missing"),
        "gap_count": _int(source_gap_payload.get("gap_count")) or len(decisions),
        "source_blocker_count": _int(source_gap_payload.get("source_blocker_count")),
        "coverage_gap_count": _int(source_gap_payload.get("coverage_gap_count")),
        "fund_not_applicable_count": _int(source_gap_payload.get("fund_not_applicable_count")),
        "top_gap_decision": top_gap_decision,
        "next_remediable_gap": next_remediable_gap,
        "decisions": decisions,
        "next_action": next_action,
        "guardrails": {
            "synthetic_financial_facts_allowed": False,
            "paid_provider_required": False,
            "recommendation_scoring_mutated": False,
            "automatic_weight_change_allowed": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "order_boundary": "read_only_no_order",
        },
    }


def render_professional_source_gap_remediation_decision_insert_sql(
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


def run_professional_source_gap_remediation_decision(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    source_gap_payload = load_professional_source_gap_prioritization(config=config, executor=sql_executor)
    decision = build_professional_source_gap_remediation_decision(
        source_gap_payload,
        as_of_date=as_of_date,
    )
    report: dict[str, object] = {
        "report_name": DEFAULT_EVAL_NAME,
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_PIPELINE_NAME,
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
            "as_of_date": as_of_date.isoformat(),
            "decision_only": True,
            "synthetic_financial_facts_allowed": False,
            "recommendation_scoring_mutated": False,
            "automatic_order_allowed": False,
        },
    )
    try:
        eval_run_id = int(
            sql_executor.execute_scalar(
                render_professional_source_gap_remediation_decision_insert_sql(score_json=decision)
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


def _classify_gap(gap: dict[str, object], *, as_of_date: date) -> dict[str, object]:
    symbol = str(gap.get("symbol") or gap.get("primary_symbol") or "UNKNOWN").upper()
    blocker_type = str(gap.get("blocker_type") or "")
    blocker_code = str(gap.get("blocker_code") or "")
    product_type = str(gap.get("product_type") or "operating_company")
    missing_layers = [str(item) for item in _as_list(gap.get("missing_layers")) if item]
    if product_type == "fund_or_etf" or blocker_code in FUND_NOT_APPLICABLE_BLOCKERS or blocker_type == "fund_not_applicable":
        return _decision_row(
            gap,
            decision_type="fund_not_applicable",
            remediation_allowed=False,
            remediation_command="",
            rationale="ETF·펀드는 기업 재무제표 모델 대상이 아니다. 보유종목, 비용, NAV, 추적차이 분석 표면에서 판단한다.",
            future_task="fund_etf_source_layer_monitoring",
            as_of_date=as_of_date,
        )
    if blocker_code in NON_REMEDIABLE_FREE_PUBLIC_BLOCKERS or blocker_type == "source_blocker":
        return _decision_row(
            gap,
            decision_type="non_remediable_current_free_public_data",
            remediation_allowed=False,
            remediation_command="",
            rationale="무료 SEC companyfacts 경로에서 필요한 us-gaap facts가 없어 현재 공개 데이터 파이프라인으로는 안전하게 보강할 수 없다.",
            future_task="raw_filing_xbrl_or_alternate_public_filing_parser",
            as_of_date=as_of_date,
        )
    deterministic_command = _deterministic_command_for_layers(missing_layers, as_of_date=as_of_date)
    if deterministic_command:
        return _decision_row(
            gap,
            decision_type="deterministic_remediation_available",
            remediation_allowed=True,
            remediation_command=deterministic_command,
            rationale="누락 layer가 기존 deterministic backend runner로 보강 가능한 범위다.",
            future_task="run_safe_deterministic_backend_cli",
            as_of_date=as_of_date,
        )
    remediation_command = str(gap.get("remediation_command") or "")
    if remediation_command:
        return _decision_row(
            gap,
            decision_type="coverage_expansion_available",
            remediation_allowed=True,
            remediation_command=remediation_command,
            rationale="기존 professional coverage expansion runner로 보강 가능한 coverage gap이다.",
            future_task="run_existing_backend_cli",
            as_of_date=as_of_date,
        )
    return _decision_row(
        gap,
        decision_type="monitor_or_manual_source_review",
        remediation_allowed=False,
        remediation_command="",
        rationale="현재 gap은 안전한 deterministic remediation command가 확정되지 않았다.",
        future_task="inspect_source_gap_before_remediation",
        as_of_date=as_of_date,
    )


def _decision_row(
    gap: dict[str, object],
    *,
    decision_type: str,
    remediation_allowed: bool,
    remediation_command: str,
    rationale: str,
    future_task: str,
    as_of_date: date,
) -> dict[str, object]:
    return {
        "as_of_date": as_of_date.isoformat(),
        "priority_rank": _int(gap.get("priority_rank")),
        "symbol": str(gap.get("symbol") or gap.get("primary_symbol") or "UNKNOWN").upper(),
        "instrument_id": gap.get("instrument_id"),
        "instrument_name": str(gap.get("instrument_name") or ""),
        "product_type": str(gap.get("product_type") or "operating_company"),
        "blocker_type": str(gap.get("blocker_type") or ""),
        "blocker_code": str(gap.get("blocker_code") or ""),
        "gap_status": str(gap.get("gap_status") or ""),
        "priority_band": str(gap.get("priority_band") or ""),
        "priority_score": _float(gap.get("priority_score")),
        "missing_layers": [str(item) for item in _as_list(gap.get("missing_layers")) if item],
        "decision_type": decision_type,
        "remediation_allowed": remediation_allowed,
        "remediation_command": remediation_command,
        "rationale": rationale,
        "future_task": future_task,
        "recommendation_scoring_mutated": False,
        "automatic_weight_change_allowed": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
    }


def _deterministic_command_for_layers(missing_layers: list[str], *, as_of_date: date) -> str:
    unique_layers = set(missing_layers)
    if unique_layers == {"sum_of_parts_component"}:
        return (
            "stockanalysis-operations sum-of-parts-valuation-run "
            f"--env-file <ENV> --as-of-date {as_of_date.isoformat()} --execute"
        )
    return ""


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _int(value: object) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0


def _float(value: object) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None
