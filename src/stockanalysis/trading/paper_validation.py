from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from stockanalysis.frontend.api_adapter import resolve_frontend_response
from stockanalysis.frontend.live_adapter import DEFAULT_PORTFOLIO_NAME
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal, sql_numeric
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.trading.safety import (
    AccountPermission,
    BrokerBoundary,
    KillSwitchState,
    OrderIntent,
    OrderLimitPolicy,
    PaperValidationState,
    evaluate_order_intent,
)


DEFAULT_CREATED_BY = "paper-validation-audit-run"
DEFAULT_PAPER_PORTFOLIO_NOTIONAL = Decimal("100000")
ACTIONABLE_PAPER_ACTIONS = frozenset(
    {
        "paper_buy_to_target",
        "paper_increase_to_target",
        "paper_reduce_to_target",
        "paper_sell_to_zero",
        "paper_review_no_recommendation",
    }
)


@dataclass(frozen=True)
class SafetyConfigSnapshot:
    broker_boundary: BrokerBoundary
    account_permission: AccountPermission
    order_limit_policy: OrderLimitPolicy
    kill_switch: KillSwitchState
    broker_boundary_id: int | None = None
    account_permission_id: int | None = None


@dataclass(frozen=True)
class PaperAuditDecision:
    idempotency_key: str
    symbol: str
    paper_action: str
    decision: Any


@dataclass(frozen=True)
class PaperValidationAuditPlan:
    portfolio_name: str
    validation_date: date
    validation_status: str
    source_preview_hash: str
    recommendation_count: int
    conflict_count: int
    actionable_action_count: int
    approved_action_count: int
    skipped_action_count: int
    blocked_reasons: tuple[str, ...]
    validated_symbols: tuple[str, ...]
    audit_decisions: tuple[PaperAuditDecision, ...]


def run_paper_validation_audit(
    *,
    config: RuntimeConfig | None = None,
    executor: Any | None = None,
    source: str = "live",
    as_of_date: date | None = None,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
    portfolio_notional: Decimal = DEFAULT_PAPER_PORTFOLIO_NOTIONAL,
    created_by: str = DEFAULT_CREATED_BY,
    human_approved: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    runtime_config = config or RuntimeConfig.from_env()
    sql_executor = executor
    if sql_executor is None and (source == "live" or not dry_run):
        sql_executor = PsqlCommandExecutor.from_config(runtime_config)
    request_path = "/api/paper-trading/preview"
    if as_of_date is not None and source != "fixture":
        request_path = f"{request_path}?asOfDate={as_of_date.isoformat()}"

    preview_payload = resolve_frontend_response(
        request_path,
        source=source,
        config=runtime_config,
        executor=sql_executor,
    )
    safety_config = (
        load_paper_validation_safety_config(
            executor=sql_executor,
            portfolio_name=portfolio_name,
        )
        if sql_executor is not None
        else default_blocking_safety_config()
    )
    plan = build_paper_validation_audit_plan(
        preview_payload=preview_payload,
        safety_config=safety_config,
        validation_date=as_of_date,
        portfolio_name=portfolio_name,
        portfolio_notional=portfolio_notional,
        created_by=created_by,
        human_approved=human_approved,
    )
    sql = render_paper_validation_audit_sql(plan, created_by=created_by)

    write_result: dict[str, Any] | None = None
    if not dry_run:
        if sql_executor is None:
            raise ValueError("paper validation audit write requires a SQL executor")
        write_result = _json_object(sql_executor.execute_scalar(sql), "paper validation audit write result")

    return build_paper_validation_audit_report(
        plan,
        safety_config=safety_config,
        dry_run=dry_run,
        source=source,
        write_result=write_result,
    )


def load_paper_validation_safety_config(
    *,
    executor: Any,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
) -> SafetyConfigSnapshot:
    payload = _json_object(
        executor.execute_scalar(render_paper_validation_safety_config_sql(portfolio_name=portfolio_name)),
        "paper validation safety config",
    )
    return safety_config_from_payload(payload)


def safety_config_from_payload(payload: dict[str, Any]) -> SafetyConfigSnapshot:
    broker = _as_dict(payload.get("broker_boundary"))
    account = _as_dict(payload.get("account_permission"))
    policy = _as_dict(payload.get("order_limit_policy"))
    kill_switch = _as_dict(payload.get("kill_switch"))

    allowed_symbols = account.get("allowed_symbols")
    return SafetyConfigSnapshot(
        broker_boundary=BrokerBoundary(
            broker_code=str(broker.get("broker_code") or "not_configured"),
            environment=str(broker.get("environment") or "paper"),
            status=str(broker.get("status") or "not_configured"),
            supports_order_preview=broker.get("supports_order_preview") is True,
            supports_order_submit=broker.get("supports_order_submit") is True,
        ),
        account_permission=AccountPermission(
            account_ref=str(account.get("account_ref") or "not_configured"),
            permission_scope=str(account.get("permission_scope") or "read_only"),
            status=str(account.get("status") or "inactive"),
            allowed_symbols=tuple(str(symbol).upper() for symbol in allowed_symbols)
            if isinstance(allowed_symbols, list)
            else (),
            max_order_notional=_optional_decimal(account.get("max_order_notional")),
            max_daily_notional=_optional_decimal(account.get("max_daily_notional")),
        ),
        order_limit_policy=OrderLimitPolicy(
            status=str(policy.get("status") or "inactive"),
            max_single_order_notional=_decimal_or_default(
                policy.get("max_single_order_notional"),
                Decimal("999999999"),
            ),
            max_daily_order_notional=_decimal_or_default(
                policy.get("max_daily_order_notional"),
                Decimal("999999999"),
            ),
            max_single_order_weight_delta=_decimal_or_default(
                policy.get("max_single_order_weight_delta"),
                Decimal("1"),
            ),
            max_post_trade_symbol_weight=_decimal_or_default(
                policy.get("max_post_trade_symbol_weight"),
                Decimal("1"),
            ),
            min_cash_buffer_weight=_decimal_or_default(policy.get("min_cash_buffer_weight"), Decimal("0")),
        ),
        kill_switch=KillSwitchState(
            is_engaged=kill_switch.get("is_engaged") is not False,
            reason=str(kill_switch.get("reason") or "default paper audit lock"),
        ),
        broker_boundary_id=_optional_int(broker.get("broker_boundary_id")),
        account_permission_id=_optional_int(account.get("account_permission_id")),
    )


def default_blocking_safety_config() -> SafetyConfigSnapshot:
    return SafetyConfigSnapshot(
        broker_boundary=BrokerBoundary(
            broker_code="not_configured",
            environment="paper",
            status="not_configured",
            supports_order_preview=False,
            supports_order_submit=False,
        ),
        account_permission=AccountPermission(
            account_ref="not_configured",
            permission_scope="read_only",
            status="inactive",
            allowed_symbols=(),
        ),
        order_limit_policy=OrderLimitPolicy(
            status="inactive",
            max_single_order_notional=Decimal("999999999"),
            max_daily_order_notional=Decimal("999999999"),
            max_single_order_weight_delta=Decimal("1"),
            max_post_trade_symbol_weight=Decimal("1"),
            min_cash_buffer_weight=Decimal("0"),
        ),
        kill_switch=KillSwitchState(is_engaged=True, reason="default paper audit lock"),
    )


def build_paper_validation_audit_plan(
    *,
    preview_payload: dict[str, Any],
    safety_config: SafetyConfigSnapshot | None = None,
    validation_date: date | None = None,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
    portfolio_notional: Decimal = DEFAULT_PAPER_PORTFOLIO_NOTIONAL,
    created_by: str = DEFAULT_CREATED_BY,
    human_approved: bool = False,
) -> PaperValidationAuditPlan:
    _validate_created_by(created_by)
    data = _as_dict(preview_payload.get("data"))
    quality = _as_dict(data.get("quality_summary"))
    source_hash = _source_preview_hash(preview_payload)
    selected_date = validation_date or _parse_date(str(data.get("as_of_date") or "")) or date.today()
    config = safety_config or default_blocking_safety_config()

    paper_actions = _as_list(data.get("paper_actions"))
    recommendation_count = int(quality.get("recommendation_count") or 0)
    conflict_count = int(quality.get("position_recommendation_conflict_count") or 0)
    blocked_reasons: list[str] = []
    audit_decisions: list[PaperAuditDecision] = []
    skipped_count = 0
    cumulative_notional = Decimal("0")

    for index, action in enumerate(paper_actions, start=1):
        paper_action = str(action.get("paper_action") or "paper_hold")
        if paper_action not in ACTIONABLE_PAPER_ACTIONS:
            continue
        symbol = str(action.get("symbol") or "UNKNOWN").upper()
        if action.get("conflict") is True:
            blocked_reasons.append(f"position_recommendation_conflict:{symbol}")
        try:
            intent = paper_action_to_order_intent(
                action,
                portfolio_notional=portfolio_notional,
            )
        except ValueError as exc:
            skipped_count += 1
            blocked_reasons.append(f"skipped:{symbol}:{exc}")
            continue

        decision = evaluate_order_intent(
            intent,
            broker_boundary=config.broker_boundary,
            account_permission=config.account_permission,
            order_limit_policy=config.order_limit_policy,
            kill_switch=config.kill_switch,
            paper_validation=PaperValidationState(status="missing", validated_symbols=(), conflict_count=0),
            human_approved=human_approved,
            daily_submitted_notional=cumulative_notional,
        )
        cumulative_notional += decision.estimated_notional
        for reason in decision.reasons:
            blocked_reasons.append(f"{symbol}:{reason}")
        audit_decisions.append(
            PaperAuditDecision(
                idempotency_key=_idempotency_key(
                    validation_date=selected_date,
                    source_hash=source_hash,
                    symbol=symbol,
                    index=index,
                ),
                symbol=symbol,
                paper_action=paper_action,
                decision=decision,
            )
        )

    approved_symbols = tuple(decision.symbol for decision in audit_decisions if decision.decision.allowed)
    approved_action_count = len(approved_symbols)
    validation_status = "passed"
    if conflict_count > 0 or skipped_count > 0 or any(not item.decision.allowed for item in audit_decisions):
        validation_status = "failed"

    return PaperValidationAuditPlan(
        portfolio_name=portfolio_name,
        validation_date=selected_date,
        validation_status=validation_status,
        source_preview_hash=source_hash,
        recommendation_count=recommendation_count,
        conflict_count=conflict_count,
        actionable_action_count=len(audit_decisions) + skipped_count,
        approved_action_count=approved_action_count,
        skipped_action_count=skipped_count,
        blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
        validated_symbols=tuple(dict.fromkeys(approved_symbols)),
        audit_decisions=tuple(audit_decisions),
    )


def paper_action_to_order_intent(
    action: dict[str, Any],
    *,
    portfolio_notional: Decimal,
) -> OrderIntent:
    paper_action = str(action.get("paper_action") or "paper_hold")
    side = _paper_action_side(paper_action)
    if side is None:
        raise ValueError(f"unsupported_paper_action:{paper_action}")

    symbol = str(action.get("symbol") or "").upper()
    current_weight = _required_decimal(action.get("current_weight"), "current_weight")
    target_weight = _required_decimal(action.get("target_weight"), "target_weight")
    latest_price = _required_decimal(action.get("latest_price"), "latest_price")
    if latest_price <= 0:
        raise ValueError("latest_price_must_be_positive")
    delta_weight = abs(target_weight - current_weight)
    if delta_weight <= 0:
        raise ValueError("target_weight_equals_current_weight")
    estimated_notional = (portfolio_notional * delta_weight).quantize(Decimal("0.01"))
    if estimated_notional <= 0:
        raise ValueError("estimated_notional_must_be_positive")
    quantity = (estimated_notional / latest_price).quantize(Decimal("0.00000001"))
    if quantity <= 0:
        raise ValueError("quantity_must_be_positive")

    return OrderIntent(
        symbol=symbol,
        side=side,
        quantity=quantity,
        estimated_price=latest_price,
        order_type="market",
        execution_mode="paper",
        current_weight=current_weight,
        target_weight=target_weight,
    )


def render_paper_validation_audit_sql(
    plan: PaperValidationAuditPlan,
    *,
    created_by: str,
) -> str:
    _validate_created_by(created_by)
    return f"""with target_portfolio as (
    select portfolio_id, portfolio_name
    from portfolio.portfolio
    where portfolio_name = {sql_literal(plan.portfolio_name)}
    order by portfolio_id
    limit 1
),
selected_broker_boundary as (
    select broker_boundary_id
    from trading.broker_boundary
    where environment = 'paper'
    order by
        case status when 'enabled' then 0 when 'disabled' then 1 else 2 end,
        updated_at desc,
        broker_boundary_id desc
    limit 1
),
selected_account_permission as (
    select account_permission_id
    from trading.account_permission
    where permission_scope in ('paper_trade', 'live_trade', 'read_only')
      and (
          portfolio_id = (select portfolio_id from target_portfolio)
          or portfolio_id is null
      )
    order by
        case status when 'active' then 0 when 'inactive' then 1 else 2 end,
        case permission_scope when 'paper_trade' then 0 when 'live_trade' then 1 else 2 end,
        updated_at desc,
        account_permission_id desc
    limit 1
),
validation_run as (
    insert into trading.paper_validation_run (
        portfolio_id,
        validation_date,
        status,
        source_preview_hash,
        recommendation_count,
        conflict_count,
        approved_action_count,
        validated_symbols,
        blocked_reasons,
        created_by
    )
    values (
        (select portfolio_id from target_portfolio),
        {sql_date(plan.validation_date)},
        {sql_literal(plan.validation_status)},
        {sql_literal(plan.source_preview_hash)},
        {plan.recommendation_count},
        {plan.conflict_count},
        {plan.approved_action_count},
        {sql_text_array(plan.validated_symbols)},
        {_jsonb_literal(list(plan.blocked_reasons))},
        {sql_literal(created_by)}
    )
    returning paper_validation_run_id, portfolio_id
),
audit_input (
    idempotency_key,
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
    request_snapshot,
    decision_snapshot
) as (
    {_audit_input_rows_sql(plan.audit_decisions)}
),
audit_insert as (
    insert into trading.order_intent_audit (
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
    select
        input.idempotency_key,
        (select portfolio_id from validation_run),
        (select broker_boundary_id from selected_broker_boundary),
        (select account_permission_id from selected_account_permission),
        (select paper_validation_run_id from validation_run),
        input.symbol,
        input.side,
        input.order_type,
        input.execution_mode,
        input.quantity,
        input.estimated_price,
        input.estimated_notional,
        input.current_weight,
        input.target_weight,
        input.decision,
        input.blocked_reasons,
        input.requires_human_approval,
        input.human_approved,
        false,
        input.request_snapshot,
        input.decision_snapshot,
        {sql_literal(created_by)}
    from audit_input input
    on conflict (idempotency_key) do update
    set
        paper_validation_run_id = excluded.paper_validation_run_id,
        decision = excluded.decision,
        blocked_reasons = excluded.blocked_reasons,
        requires_human_approval = excluded.requires_human_approval,
        human_approved = excluded.human_approved,
        submitted_to_broker = false,
        request_snapshot = excluded.request_snapshot,
        decision_snapshot = excluded.decision_snapshot
    returning order_intent_audit_id
)
select json_build_object(
    'paper_validation_run_id', (select paper_validation_run_id from validation_run),
    'audit_insert_count', (select count(*)::int from audit_insert),
    'submitted_to_broker_count', 0
)::text;"""


def render_paper_validation_safety_config_sql(*, portfolio_name: str = DEFAULT_PORTFOLIO_NAME) -> str:
    return f"""-- paper validation safety config lookup
with target_portfolio as (
    select portfolio_id, portfolio_name
    from portfolio.portfolio
    where portfolio_name = {sql_literal(portfolio_name)}
    order by portfolio_id
    limit 1
),
selected_broker_boundary as (
    select boundary.*
    from trading.broker_boundary boundary
    where boundary.environment = 'paper'
    order by
        case boundary.status when 'enabled' then 0 when 'disabled' then 1 else 2 end,
        boundary.updated_at desc,
        boundary.broker_boundary_id desc
    limit 1
),
selected_account_permission as (
    select permission.*
    from trading.account_permission permission
    where permission.permission_scope in ('paper_trade', 'live_trade', 'read_only')
      and (
          permission.portfolio_id = (select portfolio_id from target_portfolio)
          or permission.portfolio_id is null
      )
    order by
        case permission.status when 'active' then 0 when 'inactive' then 1 else 2 end,
        case permission.permission_scope when 'paper_trade' then 0 when 'live_trade' then 1 else 2 end,
        permission.updated_at desc,
        permission.account_permission_id desc
    limit 1
),
selected_order_limit_policy as (
    select policy.*
    from trading.order_limit_policy policy
    where policy.portfolio_id = (select portfolio_id from target_portfolio)
       or policy.portfolio_id is null
    order by
        case policy.status when 'active' then 0 when 'inactive' then 1 else 2 end,
        policy.updated_at desc,
        policy.order_limit_policy_id desc
    limit 1
),
selected_kill_switches as (
    select switch.*
    from trading.kill_switch_state switch
    where switch.scope = 'global'
       or (switch.scope = 'portfolio' and switch.scope_ref = coalesce((select portfolio_id::text from target_portfolio), {sql_literal(portfolio_name)}))
)
select json_build_object(
    'portfolio_id', (select portfolio_id from target_portfolio),
    'broker_boundary',
    (
        select json_build_object(
            'broker_boundary_id', broker_boundary_id,
            'broker_code', broker_code,
            'environment', environment,
            'status', status,
            'supports_order_preview', supports_order_preview,
            'supports_order_submit', supports_order_submit
        )
        from selected_broker_boundary
    ),
    'account_permission',
    (
        select json_build_object(
            'account_permission_id', account_permission_id,
            'account_ref', account_ref,
            'permission_scope', permission_scope,
            'status', status,
            'allowed_symbols', allowed_symbols,
            'max_order_notional', max_order_notional,
            'max_daily_notional', max_daily_notional
        )
        from selected_account_permission
    ),
    'order_limit_policy',
    (
        select json_build_object(
            'policy_name', policy_name,
            'status', status,
            'max_single_order_notional', max_single_order_notional,
            'max_daily_order_notional', max_daily_order_notional,
            'max_single_order_weight_delta', max_single_order_weight_delta,
            'max_post_trade_symbol_weight', max_post_trade_symbol_weight,
            'min_cash_buffer_weight', min_cash_buffer_weight
        )
        from selected_order_limit_policy
    ),
    'kill_switch',
    json_build_object(
        'is_engaged', coalesce((select bool_or(is_engaged) from selected_kill_switches), true),
        'reason', coalesce((select string_agg(reason, '; ' order by changed_at desc) from selected_kill_switches where is_engaged), 'default paper audit lock')
    )
)::text;"""


def build_paper_validation_audit_report(
    plan: PaperValidationAuditPlan,
    *,
    safety_config: SafetyConfigSnapshot,
    dry_run: bool,
    source: str,
    write_result: dict[str, Any] | None,
) -> dict[str, Any]:
    blocked_intent_count = sum(1 for item in plan.audit_decisions if not item.decision.allowed)
    return {
        "report_name": "paper_validation_audit_writer",
        "status": "dry_run" if dry_run else "written",
        "source_mode": source,
        "portfolio_name": plan.portfolio_name,
        "validation_date": plan.validation_date.isoformat(),
        "validation_status": plan.validation_status,
        "source_preview_hash": plan.source_preview_hash,
        "recommendation_count": plan.recommendation_count,
        "conflict_count": plan.conflict_count,
        "actionable_action_count": plan.actionable_action_count,
        "audited_intent_count": len(plan.audit_decisions),
        "approved_action_count": plan.approved_action_count,
        "blocked_intent_count": blocked_intent_count,
        "skipped_action_count": plan.skipped_action_count,
        "submitted_to_broker_count": 0,
        "blocked_reasons": list(plan.blocked_reasons),
        "safety_config": {
            "broker_boundary_status": safety_config.broker_boundary.status,
            "account_permission_scope": safety_config.account_permission.permission_scope,
            "account_permission_status": safety_config.account_permission.status,
            "order_limit_policy_status": safety_config.order_limit_policy.status,
            "kill_switch_engaged": safety_config.kill_switch.is_engaged,
        },
        "write_result": write_result or {},
        "manual_next_step": "review_trading_readiness_before_any_broker_integration",
    }


def _paper_action_side(paper_action: str) -> str | None:
    if paper_action in {"paper_buy_to_target", "paper_increase_to_target"}:
        return "buy"
    if paper_action in {"paper_reduce_to_target", "paper_sell_to_zero", "paper_review_no_recommendation"}:
        return "sell"
    return None


def _idempotency_key(*, validation_date: date, source_hash: str, symbol: str, index: int) -> str:
    return f"paper:{validation_date.isoformat()}:{symbol}:{index}:{source_hash.split(':', 1)[-1][:12]}"


def _source_preview_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload.get("data", payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _audit_input_rows_sql(decisions: tuple[PaperAuditDecision, ...]) -> str:
    if not decisions:
        return """select
        null::text,
        null::text,
        null::text,
        null::text,
        null::text,
        null::numeric,
        null::numeric,
        null::numeric,
        null::numeric,
        null::numeric,
        null::text,
        '[]'::jsonb,
        null::boolean,
        null::boolean,
        '{}'::jsonb,
        '{}'::jsonb
    where false"""
    rows = ",\n        ".join(_audit_input_value_tuple(item) for item in decisions)
    return f"values\n        {rows}"


def _audit_input_value_tuple(item: PaperAuditDecision) -> str:
    payload = item.decision.audit_payload
    request = payload["request"]
    decision_payload = payload["decision"]
    blocked_reasons = decision_payload["blocked_reasons"]
    return (
        "("
        f"{sql_literal(item.idempotency_key)}, "
        f"{sql_literal(request['symbol'])}, "
        f"{sql_literal(request['side'])}, "
        f"{sql_literal(request['order_type'])}, "
        f"{sql_literal(request['execution_mode'])}, "
        f"{sql_numeric(Decimal(request['quantity']))}, "
        f"{sql_numeric(Decimal(request['estimated_price']))}, "
        f"{sql_numeric(item.decision.estimated_notional)}, "
        f"{_optional_decimal_sql(request.get('current_weight'))}, "
        f"{_optional_decimal_sql(request.get('target_weight'))}, "
        f"{sql_literal(item.decision.decision)}, "
        f"{_jsonb_literal(blocked_reasons)}, "
        f"{sql_literal(item.decision.requires_human_approval)}, "
        f"{sql_literal(item.decision.human_approved)}, "
        f"{_jsonb_literal(request)}, "
        f"{_jsonb_literal(decision_payload)}"
        ")"
    )


def sql_text_array(values: tuple[str, ...]) -> str:
    if not values:
        return "array[]::text[]"
    return "array[" + ", ".join(sql_literal(value) for value in values) + "]::text[]"


def _jsonb_literal(value: object) -> str:
    return f"{sql_literal(json.dumps(value, ensure_ascii=False, sort_keys=True))}::jsonb"


def _optional_decimal_sql(value: object) -> str:
    if value is None:
        return "null::numeric"
    return sql_numeric(Decimal(str(value)))


def _required_decimal(value: object, label: str) -> Decimal:
    parsed = _optional_decimal(value)
    if parsed is None:
        raise ValueError(f"missing_{label}")
    return parsed


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return _decimal_or_default(value, None)


def _decimal_or_default(value: object, default: Decimal | None) -> Decimal:
    if value is None:
        if default is None:
            raise ValueError("decimal value is required")
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        if default is None:
            raise ValueError(f"Invalid decimal value: {value}") from exc
        return default


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _validate_created_by(value: str) -> None:
    if len(value) < 2 or len(value) > 160:
        raise ValueError("created_by must be between 2 and 160 characters")


def _json_object(value: str, label: str) -> dict[str, Any]:
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must be a JSON object")
    return parsed


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]
