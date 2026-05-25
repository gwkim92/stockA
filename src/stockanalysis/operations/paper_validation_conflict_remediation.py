from __future__ import annotations

import json
from dataclasses import dataclass
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


DEFAULT_PIPELINE_NAME = "paper_validation_conflict_remediation"
ACTION_BLOCK_REASON_CODES = frozenset(
    {
        "broker_boundary_not_enabled",
        "broker_environment_mismatch",
        "broker_preview_not_supported",
        "broker_submit_not_supported",
        "account_permission_not_active",
        "invalid_account_permission_scope",
        "account_permission_scope_insufficient",
        "symbol_not_allowed_for_account",
        "order_limit_policy_not_active",
        "single_order_notional_limit_exceeded",
        "daily_order_notional_limit_exceeded",
        "account_order_notional_limit_exceeded",
        "account_daily_notional_limit_exceeded",
        "single_order_weight_delta_limit_exceeded",
        "post_trade_symbol_weight_limit_exceeded",
        "cash_buffer_limit_exceeded",
        "invalid_symbol",
        "invalid_side",
        "invalid_order_type",
        "invalid_execution_mode",
        "quantity_must_be_positive",
        "estimated_price_must_be_positive",
        "buy_intent_does_not_increase_weight",
        "sell_intent_does_not_reduce_weight",
    }
)
SAFETY_INTERLOCK_CODES = frozenset({"kill_switch_engaged", "human_approval_required"})


@dataclass(frozen=True)
class ParsedBlockedReason:
    raw_reason: str
    symbol: str
    code: str
    detail: str | None


def render_paper_validation_conflict_remediation_sql(
    *,
    as_of_date: date,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
) -> str:
    return f"""-- paper validation conflict remediation lookup
with target_portfolio as (
    select portfolio_id, portfolio_name
    from portfolio.portfolio
    where portfolio_name = {sql_literal(portfolio_name)}
    order by portfolio_id
    limit 1
),
selected_validation as (
    select validation.*
    from trading.paper_validation_run validation
    where validation.validation_date <= {sql_date(as_of_date)}
      and (
          validation.portfolio_id = (select portfolio_id from target_portfolio)
          or validation.portfolio_id is null
      )
    order by validation.validation_date desc, validation.paper_validation_run_id desc
    limit 1
),
audit_rows as (
    select
        audit.order_intent_audit_id,
        audit.symbol,
        audit.side,
        audit.execution_mode,
        audit.estimated_notional,
        audit.current_weight,
        audit.target_weight,
        audit.decision,
        audit.blocked_reasons,
        audit.requires_human_approval,
        audit.human_approved,
        audit.submitted_to_broker,
        audit.created_at
    from trading.order_intent_audit audit
    join selected_validation validation
      on validation.paper_validation_run_id = audit.paper_validation_run_id
    order by audit.symbol, audit.order_intent_audit_id
)
select coalesce(
    (
        select json_build_object(
            'as_of_date', {sql_literal(as_of_date.isoformat())},
            'portfolio_name', coalesce((select portfolio_name from target_portfolio), {sql_literal(portfolio_name)}),
            'paper_validation',
            json_build_object(
                'paper_validation_run_id', validation.paper_validation_run_id,
                'validation_date', validation.validation_date,
                'status', validation.status,
                'recommendation_count', validation.recommendation_count,
                'conflict_count', validation.conflict_count,
                'approved_action_count', validation.approved_action_count,
                'validated_symbols', validation.validated_symbols,
                'blocked_reasons', validation.blocked_reasons,
                'created_by', validation.created_by,
                'created_at', validation.created_at
            ),
            'order_intent_audits',
            coalesce(
                (
                    select json_agg(row_to_json(audit_rows) order by symbol, order_intent_audit_id)
                    from audit_rows
                ),
                '[]'::json
            )
        )
        from selected_validation validation
    ),
    '{{}}'::json
)::text;"""


def load_paper_validation_conflict_remediation_payload(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_paper_validation_conflict_remediation_sql(
                as_of_date=as_of_date,
                portfolio_name=portfolio_name,
            )
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Paper validation conflict remediation lookup did not return a JSON object.")
    if not payload:
        raise ValueError(f"No paper validation run found for {portfolio_name} on or before {as_of_date.isoformat()}.")
    return payload


def classify_paper_validation_conflicts(payload: dict[str, object]) -> dict[str, object]:
    validation = _as_dict(payload.get("paper_validation"))
    reasons = [str(item) for item in _as_list(validation.get("blocked_reasons"))]
    parsed_reasons = [_parse_blocked_reason(reason) for reason in reasons]
    by_symbol: dict[str, list[ParsedBlockedReason]] = {}
    for reason in parsed_reasons:
        by_symbol.setdefault(reason.symbol, []).append(reason)

    issue_rows: list[dict[str, object]] = []
    for symbol in sorted(by_symbol):
        symbol_reasons = by_symbol[symbol]
        issue_rows.append(_classify_symbol_issue(symbol, symbol_reasons))

    portfolio_coverage_issues = [item for item in issue_rows if item["issue_type"] == "portfolio_recommendation_coverage_gap"]
    non_actionable_zero_delta = [item for item in issue_rows if item["order_delta_status"] == "zero_delta_review_only"]
    safety_interlocks = [item for item in issue_rows if item["issue_type"] == "safety_interlock"]
    action_blocks = [item for item in issue_rows if item["issue_type"] == "actionable_trade_block"]
    unknown_issues = [item for item in issue_rows if item["issue_type"] == "unknown_blocker"]
    if portfolio_coverage_issues:
        decision = "blocked_by_portfolio_recommendation_coverage_gap"
    elif action_blocks:
        decision = "blocked_by_actionable_trade_safety_policy"
    elif unknown_issues:
        decision = "blocked_by_unknown_paper_validation_reason"
    elif safety_interlocks:
        decision = "paper_actions_waiting_for_safety_interlock_release"
    elif str(validation.get("status") or "missing") == "passed":
        decision = "paper_validation_passed"
    else:
        decision = "ready_for_paper_validation_recheck"

    return {
        "classification_name": "paper_validation_conflict_remediation",
        "paper_validation_run_id": _int(validation.get("paper_validation_run_id")),
        "validation_date": validation.get("validation_date"),
        "source_status": validation.get("status"),
        "source_conflict_count": _int(validation.get("conflict_count")),
        "source_approved_action_count": _int(validation.get("approved_action_count")),
        "decision": decision,
        "weight_review_allowed": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "summary": {
            "issue_count": len(issue_rows),
            "portfolio_coverage_issue_count": len(portfolio_coverage_issues),
            "non_actionable_zero_delta_issue_count": len(non_actionable_zero_delta),
            "safety_interlock_issue_count": len(safety_interlocks),
            "actionable_trade_block_count": len(action_blocks),
            "unknown_issue_count": len(unknown_issues),
        },
        "issues": issue_rows,
        "next_action": _next_action(decision),
    }


def run_paper_validation_conflict_remediation(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = load_paper_validation_conflict_remediation_payload(
        config=config,
        as_of_date=as_of_date,
        portfolio_name=portfolio_name,
        executor=sql_executor,
    )
    classification = classify_paper_validation_conflicts(payload)
    report: dict[str, object] = {
        "report_name": "paper_validation_conflict_remediation",
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "portfolio_name": portfolio_name,
        "classification": classification,
    }
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "portfolio_name": portfolio_name,
            "paper_validation_run_id": classification["paper_validation_run_id"],
            "decision": classification["decision"],
            "weight_review_allowed": False,
            "automatic_order_allowed": False,
        },
    )
    try:
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise
    return {**report, "status": "completed", "run_id": run_id}


def _classify_symbol_issue(symbol: str, reasons: list[ParsedBlockedReason]) -> dict[str, object]:
    codes = tuple(dict.fromkeys(reason.code for reason in reasons))
    has_position_conflict = "position_recommendation_conflict" in codes
    has_zero_delta_skip = any(reason.code == "skipped" and reason.detail == "target_weight_equals_current_weight" for reason in reasons)
    action_block_codes = [code for code in codes if code in ACTION_BLOCK_REASON_CODES]
    safety_codes = [code for code in codes if code in SAFETY_INTERLOCK_CODES]
    if has_position_conflict:
        issue_type = "portfolio_recommendation_coverage_gap"
        severity = "high"
        order_delta_status = "zero_delta_review_only" if has_zero_delta_skip else "actionable_position_conflict"
        remediation = "보유 중인 종목에 active recommendation/thesis coverage를 다시 만들거나, 보유 종료 thesis를 명확히 저장한 뒤 paper validation을 재실행한다."
    elif action_block_codes:
        issue_type = "actionable_trade_block"
        severity = "high"
        order_delta_status = "actionable_order_blocked"
        remediation = "주문 한도, 계좌 권한, 심볼 허용 목록, 가격/수량 입력을 고친 뒤 paper validation을 재실행한다."
    elif safety_codes:
        issue_type = "safety_interlock"
        severity = "medium"
        order_delta_status = "blocked_by_operator_gate"
        remediation = "kill switch와 human approval은 의도된 안전장치다. 추천 weight 검토 전에 주문 확대가 필요한지 별도 승인 task로 판단한다."
    else:
        issue_type = "unknown_blocker"
        severity = "medium"
        order_delta_status = "unknown"
        remediation = "blocked reason parser가 모르는 사유다. paper validation writer와 safety evaluator mapping을 갱신한다."
    return {
        "symbol": symbol,
        "issue_type": issue_type,
        "severity": severity,
        "reason_codes": list(codes),
        "raw_reasons": [reason.raw_reason for reason in reasons],
        "order_delta_status": order_delta_status,
        "remediation": remediation,
    }


def _parse_blocked_reason(raw_reason: str) -> ParsedBlockedReason:
    if raw_reason.startswith("position_recommendation_conflict:"):
        return ParsedBlockedReason(
            raw_reason=raw_reason,
            symbol=raw_reason.split(":", 1)[1].upper(),
            code="position_recommendation_conflict",
            detail=None,
        )
    if raw_reason.startswith("skipped:"):
        parts = raw_reason.split(":", 2)
        symbol = parts[1].upper() if len(parts) > 1 else "UNKNOWN"
        detail = parts[2] if len(parts) > 2 else None
        return ParsedBlockedReason(raw_reason=raw_reason, symbol=symbol, code="skipped", detail=detail)
    symbol, separator, code = raw_reason.partition(":")
    if separator:
        return ParsedBlockedReason(raw_reason=raw_reason, symbol=symbol.upper(), code=code, detail=None)
    return ParsedBlockedReason(raw_reason=raw_reason, symbol="UNKNOWN", code=raw_reason, detail=None)


def _next_action(decision: str) -> str:
    if decision == "blocked_by_portfolio_recommendation_coverage_gap":
        return "보유 중이지만 최신 추천/보유 thesis coverage가 끊긴 종목부터 복구한다. 현재 이 문제는 주문 델타 0인 review-only gap이지만, portfolio risk와 thesis lifecycle 품질 문제라 weight 변경 전 해소해야 한다."
    if decision == "blocked_by_actionable_trade_safety_policy":
        return "실제 paper action을 막는 주문 한도/계좌 권한/심볼/가격 입력 문제를 고친 뒤 paper validation을 재실행한다."
    if decision == "paper_actions_waiting_for_safety_interlock_release":
        return "남은 차단은 kill switch/human approval 같은 의도된 안전장치다. 실거래는 계속 금지하고, paper-only 승인 정책을 별도 task에서 결정한다."
    if decision == "paper_validation_passed":
        return "paper validation은 통과했다. 그래도 자동 weight 변경은 금지하고 별도 pilot-weight review task를 열어야 한다."
    if decision == "ready_for_paper_validation_recheck":
        return "분류상 치명적 conflict가 없다. paper validation audit를 재실행해 최신 상태를 갱신한다."
    return "알 수 없는 차단 사유를 먼저 parser와 safety mapping에 추가한다."


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _int(value: object) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
