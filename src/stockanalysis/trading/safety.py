from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from stockanalysis.ingest.macro.sql import sql_literal, sql_numeric


VALID_SIDES = frozenset({"buy", "sell"})
VALID_ORDER_TYPES = frozenset({"market", "limit"})
VALID_EXECUTION_MODES = frozenset({"paper", "live"})
VALID_PERMISSION_SCOPES = frozenset({"read_only", "paper_trade", "live_trade"})
SYMBOL_RE = re.compile(r"^[A-Z0-9.-]{1,20}$")


@dataclass(frozen=True)
class BrokerBoundary:
    broker_code: str
    environment: str
    status: str
    supports_order_preview: bool
    supports_order_submit: bool


@dataclass(frozen=True)
class AccountPermission:
    account_ref: str
    permission_scope: str
    status: str
    allowed_symbols: tuple[str, ...]
    max_order_notional: Decimal | None = None
    max_daily_notional: Decimal | None = None


@dataclass(frozen=True)
class OrderLimitPolicy:
    status: str
    max_single_order_notional: Decimal
    max_daily_order_notional: Decimal
    max_single_order_weight_delta: Decimal
    max_post_trade_symbol_weight: Decimal
    min_cash_buffer_weight: Decimal = Decimal("0")


@dataclass(frozen=True)
class KillSwitchState:
    is_engaged: bool
    reason: str


@dataclass(frozen=True)
class PaperValidationState:
    status: str
    validated_symbols: tuple[str, ...]
    conflict_count: int
    max_allowed_conflicts: int = 0


@dataclass(frozen=True)
class OrderIntent:
    symbol: str
    side: str
    quantity: Decimal
    estimated_price: Decimal
    order_type: str
    execution_mode: str
    current_weight: Decimal | None
    target_weight: Decimal | None
    projected_cash_weight: Decimal | None = None


@dataclass(frozen=True)
class OrderSafetyDecision:
    allowed: bool
    decision: str
    reasons: tuple[str, ...]
    estimated_notional: Decimal
    requires_human_approval: bool
    human_approved: bool
    audit_payload: dict[str, Any]


def evaluate_order_intent(
    intent: OrderIntent,
    *,
    broker_boundary: BrokerBoundary,
    account_permission: AccountPermission,
    order_limit_policy: OrderLimitPolicy,
    kill_switch: KillSwitchState,
    paper_validation: PaperValidationState,
    human_approved: bool,
    daily_submitted_notional: Decimal = Decimal("0"),
    require_human_approval: bool = True,
) -> OrderSafetyDecision:
    """Evaluate an order intent without submitting it to any broker."""

    symbol = intent.symbol.upper()
    reasons: list[str] = []

    if not SYMBOL_RE.fullmatch(symbol):
        reasons.append("invalid_symbol")
    if intent.side not in VALID_SIDES:
        reasons.append("invalid_side")
    if intent.order_type not in VALID_ORDER_TYPES:
        reasons.append("invalid_order_type")
    if intent.execution_mode not in VALID_EXECUTION_MODES:
        reasons.append("invalid_execution_mode")

    quantity = _decimal(intent.quantity)
    estimated_price = _decimal(intent.estimated_price)
    if quantity <= 0:
        reasons.append("quantity_must_be_positive")
    if estimated_price <= 0:
        reasons.append("estimated_price_must_be_positive")
    estimated_notional = _money(quantity * estimated_price)

    if broker_boundary.status != "enabled":
        reasons.append("broker_boundary_not_enabled")
    if broker_boundary.environment != intent.execution_mode:
        reasons.append("broker_environment_mismatch")
    if intent.execution_mode == "paper" and not broker_boundary.supports_order_preview:
        reasons.append("broker_preview_not_supported")
    if intent.execution_mode == "live" and not broker_boundary.supports_order_submit:
        reasons.append("broker_submit_not_supported")

    if account_permission.status != "active":
        reasons.append("account_permission_not_active")
    if account_permission.permission_scope not in VALID_PERMISSION_SCOPES:
        reasons.append("invalid_account_permission_scope")
    elif not _scope_allows(account_permission.permission_scope, intent.execution_mode):
        reasons.append("account_permission_scope_insufficient")
    if not _symbol_allowed(symbol, account_permission.allowed_symbols):
        reasons.append("symbol_not_allowed_for_account")

    if order_limit_policy.status != "active":
        reasons.append("order_limit_policy_not_active")
    if estimated_notional > order_limit_policy.max_single_order_notional:
        reasons.append("single_order_notional_limit_exceeded")
    daily_total = _money(_decimal(daily_submitted_notional) + estimated_notional)
    if daily_total > order_limit_policy.max_daily_order_notional:
        reasons.append("daily_order_notional_limit_exceeded")
    if account_permission.max_order_notional is not None and estimated_notional > account_permission.max_order_notional:
        reasons.append("account_order_notional_limit_exceeded")
    if account_permission.max_daily_notional is not None and daily_total > account_permission.max_daily_notional:
        reasons.append("account_daily_notional_limit_exceeded")

    current_weight = _optional_decimal(intent.current_weight)
    target_weight = _optional_decimal(intent.target_weight)
    if current_weight is not None and target_weight is not None:
        weight_delta = abs(target_weight - current_weight)
        if weight_delta > order_limit_policy.max_single_order_weight_delta:
            reasons.append("single_order_weight_delta_limit_exceeded")
        if target_weight > order_limit_policy.max_post_trade_symbol_weight:
            reasons.append("post_trade_symbol_weight_limit_exceeded")
        if intent.side == "buy" and target_weight <= current_weight:
            reasons.append("buy_intent_does_not_increase_weight")
        if intent.side == "sell" and target_weight >= current_weight:
            reasons.append("sell_intent_does_not_reduce_weight")

    projected_cash_weight = _optional_decimal(intent.projected_cash_weight)
    if projected_cash_weight is not None and projected_cash_weight < order_limit_policy.min_cash_buffer_weight:
        reasons.append("cash_buffer_limit_exceeded")

    if kill_switch.is_engaged:
        reasons.append("kill_switch_engaged")

    if require_human_approval and not human_approved:
        reasons.append("human_approval_required")

    if intent.execution_mode == "live":
        if paper_validation.status != "passed":
            reasons.append("paper_validation_not_passed")
        if not _symbol_allowed(symbol, paper_validation.validated_symbols):
            reasons.append("symbol_not_paper_validated")
        if paper_validation.conflict_count > paper_validation.max_allowed_conflicts:
            reasons.append("paper_validation_conflicts_remaining")

    allowed = not reasons
    decision = _allowed_decision(intent.execution_mode) if allowed else "blocked"
    audit_payload = _audit_payload(
        intent=intent,
        symbol=symbol,
        estimated_notional=estimated_notional,
        decision=decision,
        reasons=tuple(reasons),
        requires_human_approval=require_human_approval,
        human_approved=human_approved,
    )
    return OrderSafetyDecision(
        allowed=allowed,
        decision=decision,
        reasons=tuple(reasons),
        estimated_notional=estimated_notional,
        requires_human_approval=require_human_approval,
        human_approved=human_approved,
        audit_payload=audit_payload,
    )


def render_order_intent_audit_insert_sql(
    decision: OrderSafetyDecision,
    *,
    idempotency_key: str,
    created_by: str,
    portfolio_id: int | None = None,
    broker_boundary_id: int | None = None,
    account_permission_id: int | None = None,
    paper_validation_run_id: int | None = None,
) -> str:
    """Render an audit insert. This is not an order submission statement."""

    payload = decision.audit_payload
    request_snapshot = _jsonb_literal(payload["request"])
    decision_snapshot = _jsonb_literal(payload["decision"])
    blocked_reasons = _jsonb_literal(payload["decision"]["blocked_reasons"])
    return f"""insert into trading.order_intent_audit (
    idempotency_key,
    portfolio_id,
    broker_boundary_id,
    account_permission_id,
    paper_validation_run_id,
    symbol,
    side,
    order_type,
    execution_mode,
    quantity,
    estimated_price,
    estimated_notional,
    current_weight,
    target_weight,
    decision,
    blocked_reasons,
    requires_human_approval,
    human_approved,
    submitted_to_broker,
    request_snapshot,
    decision_snapshot,
    created_by
)
values (
    {sql_literal(idempotency_key)},
    {_optional_int_sql(portfolio_id)},
    {_optional_int_sql(broker_boundary_id)},
    {_optional_int_sql(account_permission_id)},
    {_optional_int_sql(paper_validation_run_id)},
    {sql_literal(payload["request"]["symbol"])},
    {sql_literal(payload["request"]["side"])},
    {sql_literal(payload["request"]["order_type"])},
    {sql_literal(payload["request"]["execution_mode"])},
    {sql_numeric(Decimal(payload["request"]["quantity"]))},
    {sql_numeric(Decimal(payload["request"]["estimated_price"]))},
    {sql_numeric(decision.estimated_notional)},
    {_optional_decimal_sql(payload["request"].get("current_weight"))},
    {_optional_decimal_sql(payload["request"].get("target_weight"))},
    {sql_literal(decision.decision)},
    {blocked_reasons},
    {sql_literal(decision.requires_human_approval)},
    {sql_literal(decision.human_approved)},
    false,
    {request_snapshot},
    {decision_snapshot},
    {sql_literal(created_by)}
)
on conflict (idempotency_key) do update
set
    decision = excluded.decision,
    blocked_reasons = excluded.blocked_reasons,
    decision_snapshot = excluded.decision_snapshot;"""


def _audit_payload(
    *,
    intent: OrderIntent,
    symbol: str,
    estimated_notional: Decimal,
    decision: str,
    reasons: tuple[str, ...],
    requires_human_approval: bool,
    human_approved: bool,
) -> dict[str, Any]:
    return {
        "request": {
            "symbol": symbol,
            "side": intent.side,
            "order_type": intent.order_type,
            "execution_mode": intent.execution_mode,
            "quantity": str(_decimal(intent.quantity)),
            "estimated_price": str(_decimal(intent.estimated_price)),
            "estimated_notional": str(estimated_notional),
            "current_weight": _optional_decimal_text(intent.current_weight),
            "target_weight": _optional_decimal_text(intent.target_weight),
            "projected_cash_weight": _optional_decimal_text(intent.projected_cash_weight),
        },
        "decision": {
            "decision": decision,
            "blocked_reasons": list(reasons),
            "requires_human_approval": requires_human_approval,
            "human_approved": human_approved,
            "submitted_to_broker": False,
        },
    }


def _allowed_decision(execution_mode: str) -> str:
    if execution_mode == "live":
        return "approved_for_live"
    return "approved_for_paper"


def _scope_allows(scope: str, execution_mode: str) -> bool:
    if execution_mode == "paper":
        return scope in {"paper_trade", "live_trade"}
    if execution_mode == "live":
        return scope == "live_trade"
    return False


def _symbol_allowed(symbol: str, allowed_symbols: tuple[str, ...]) -> bool:
    normalized = {item.upper() for item in allowed_symbols}
    return "*" in normalized or symbol in normalized


def _decimal(value: Decimal | int | str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid decimal value: {value}") from exc


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def _optional_decimal(value: Decimal | int | str | None) -> Decimal | None:
    if value is None:
        return None
    return _decimal(value)


def _optional_decimal_text(value: Decimal | int | str | None) -> str | None:
    parsed = _optional_decimal(value)
    return str(parsed) if parsed is not None else None


def _optional_int_sql(value: int | None) -> str:
    return "null::bigint" if value is None else f"{value}::bigint"


def _optional_decimal_sql(value: object) -> str:
    if value is None:
        return "null::numeric"
    return sql_numeric(Decimal(str(value)))


def _jsonb_literal(value: object) -> str:
    return f"{sql_literal(json.dumps(value, ensure_ascii=False, sort_keys=True))}::jsonb"
