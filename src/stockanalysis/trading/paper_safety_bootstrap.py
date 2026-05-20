from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from stockanalysis.frontend.live_adapter import DEFAULT_PORTFOLIO_NAME
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal, sql_numeric
from stockanalysis.ingest.psql import PsqlCommandExecutor


DEFAULT_PAPER_BROKER_CODE = "simulated_paper"
DEFAULT_PAPER_ACCOUNT_REF = "paper-account-long-term"
DEFAULT_PAPER_POLICY_NAME = "long-term-paper-default"
DEFAULT_CREATED_BY = "paper-safety-bootstrap-config"
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_:.@/-]{2,160}$")
BROKER_CODE_RE = re.compile(r"^[a-z0-9_:-]{2,80}$")


@dataclass(frozen=True)
class PaperSafetyBootstrapConfig:
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME
    broker_code: str = DEFAULT_PAPER_BROKER_CODE
    account_ref: str = DEFAULT_PAPER_ACCOUNT_REF
    policy_name: str = DEFAULT_PAPER_POLICY_NAME
    max_single_order_notional: Decimal = Decimal("50000")
    max_daily_order_notional: Decimal = Decimal("100000")
    max_single_order_weight_delta: Decimal = Decimal("0.20")
    max_post_trade_symbol_weight: Decimal = Decimal("0.40")
    min_cash_buffer_weight: Decimal = Decimal("0.02")
    created_by: str = DEFAULT_CREATED_BY


def run_paper_safety_bootstrap_config(
    *,
    config: RuntimeConfig | None = None,
    executor: Any | None = None,
    bootstrap_config: PaperSafetyBootstrapConfig | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    runtime_config = config or RuntimeConfig.from_env()
    selected_config = bootstrap_config or PaperSafetyBootstrapConfig()
    sql = render_paper_safety_bootstrap_sql(selected_config)
    write_result: dict[str, Any] | None = None

    if not dry_run:
        sql_executor = executor or PsqlCommandExecutor.from_config(runtime_config)
        write_result = _json_object(sql_executor.execute_scalar(sql), "paper safety bootstrap write result")

    return build_paper_safety_bootstrap_report(
        selected_config,
        dry_run=dry_run,
        write_result=write_result,
    )


def render_paper_safety_bootstrap_sql(config: PaperSafetyBootstrapConfig) -> str:
    _validate_config(config)
    return f"""with target_portfolio as (
    select portfolio_id, portfolio_name
    from portfolio.portfolio
    where portfolio_name = {sql_literal(config.portfolio_name)}
    order by portfolio_id
    limit 1
),
broker_upsert as (
    insert into trading.broker_boundary (
        broker_code,
        environment,
        status,
        supports_order_preview,
        supports_order_submit,
        secret_ref,
        notes
    )
    values (
        {sql_literal(config.broker_code)},
        'paper',
        'enabled',
        true,
        false,
        null,
        'simulated paper-only boundary; no external credential configured'
    )
    on conflict (broker_code, environment) do update
    set
        status = 'enabled',
        supports_order_preview = true,
        supports_order_submit = false,
        secret_ref = null,
        notes = excluded.notes,
        updated_at = now()
    returning broker_boundary_id, broker_code, environment, status, supports_order_preview, supports_order_submit
),
permission_upsert as (
    insert into trading.account_permission (
        broker_boundary_id,
        portfolio_id,
        account_ref,
        permission_scope,
        status,
        allowed_symbols,
        max_order_notional,
        max_daily_notional,
        approved_by,
        approved_at
    )
    select
        broker_boundary_id,
        (select portfolio_id from target_portfolio),
        {sql_literal(config.account_ref)},
        'paper_trade',
        'active',
        array['*']::text[],
        {sql_numeric(config.max_single_order_notional)},
        {sql_numeric(config.max_daily_order_notional)},
        {sql_literal(config.created_by)},
        now()
    from broker_upsert
    on conflict (broker_boundary_id, account_ref, permission_scope) do update
    set
        portfolio_id = excluded.portfolio_id,
        status = 'active',
        allowed_symbols = excluded.allowed_symbols,
        max_order_notional = excluded.max_order_notional,
        max_daily_notional = excluded.max_daily_notional,
        approved_by = excluded.approved_by,
        approved_at = now(),
        updated_at = now()
    returning account_permission_id, permission_scope, status, allowed_symbols, max_order_notional, max_daily_notional
),
policy_upsert as (
    insert into trading.order_limit_policy (
        portfolio_id,
        policy_name,
        status,
        max_single_order_notional,
        max_daily_order_notional,
        max_single_order_weight_delta,
        max_post_trade_symbol_weight,
        min_cash_buffer_weight
    )
    values (
        (select portfolio_id from target_portfolio),
        {sql_literal(config.policy_name)},
        'active',
        {sql_numeric(config.max_single_order_notional)},
        {sql_numeric(config.max_daily_order_notional)},
        {sql_numeric(config.max_single_order_weight_delta)},
        {sql_numeric(config.max_post_trade_symbol_weight)},
        {sql_numeric(config.min_cash_buffer_weight)}
    )
    on conflict (portfolio_id, policy_name) do update
    set
        status = 'active',
        max_single_order_notional = excluded.max_single_order_notional,
        max_daily_order_notional = excluded.max_daily_order_notional,
        max_single_order_weight_delta = excluded.max_single_order_weight_delta,
        max_post_trade_symbol_weight = excluded.max_post_trade_symbol_weight,
        min_cash_buffer_weight = excluded.min_cash_buffer_weight,
        updated_at = now()
    returning order_limit_policy_id, policy_name, status
),
kill_switch_summary as (
    select coalesce(bool_or(is_engaged), true) as kill_switch_engaged
    from trading.kill_switch_state
    where scope = 'global'
       or (scope = 'portfolio' and scope_ref = coalesce((select portfolio_id::text from target_portfolio), {sql_literal(config.portfolio_name)}))
)
select json_build_object(
    'status', 'written',
    'portfolio_name', {sql_literal(config.portfolio_name)},
    'portfolio_id', (select portfolio_id from target_portfolio),
    'broker_code', (select broker_code from broker_upsert),
    'broker_boundary_status', (select status from broker_upsert),
    'supports_order_preview', (select supports_order_preview from broker_upsert),
    'supports_order_submit', (select supports_order_submit from broker_upsert),
    'secret_configured', false,
    'account_ref', {sql_literal(config.account_ref)},
    'account_permission_scope', (select permission_scope from permission_upsert),
    'account_permission_status', (select status from permission_upsert),
    'allowed_symbols', (select allowed_symbols from permission_upsert),
    'order_limit_policy_name', (select policy_name from policy_upsert),
    'order_limit_policy_status', (select status from policy_upsert),
    'kill_switch_engaged', (select kill_switch_engaged from kill_switch_summary),
    'submitted_to_broker_count', 0
)::text;"""


def build_paper_safety_bootstrap_report(
    config: PaperSafetyBootstrapConfig,
    *,
    dry_run: bool,
    write_result: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "report_name": "paper_safety_bootstrap_config",
        "status": "dry_run" if dry_run else "written",
        "portfolio_name": config.portfolio_name,
        "broker_code": config.broker_code,
        "broker_environment": "paper",
        "supports_order_preview": True,
        "supports_order_submit": False,
        "secret_configured": False,
        "account_ref": config.account_ref,
        "permission_scope": "paper_trade",
        "order_limit_policy_name": config.policy_name,
        "max_single_order_notional": str(config.max_single_order_notional),
        "max_daily_order_notional": str(config.max_daily_order_notional),
        "max_single_order_weight_delta": str(config.max_single_order_weight_delta),
        "max_post_trade_symbol_weight": str(config.max_post_trade_symbol_weight),
        "min_cash_buffer_weight": str(config.min_cash_buffer_weight),
        "kill_switch_changed": False,
        "kill_switch_note": "global kill switch remains unchanged; real trading stays blocked",
        "submitted_to_broker_count": 0,
        "write_result": write_result or {},
    }


def _validate_config(config: PaperSafetyBootstrapConfig) -> None:
    if not config.portfolio_name.strip():
        raise ValueError("portfolio_name is required")
    if not BROKER_CODE_RE.fullmatch(config.broker_code):
        raise ValueError("broker_code must match paper broker code policy")
    for label, value in (
        ("account_ref", config.account_ref),
        ("policy_name", config.policy_name),
        ("created_by", config.created_by),
    ):
        if not IDENTIFIER_RE.fullmatch(value):
            raise ValueError(f"{label} must match identifier policy")
    _require_positive("max_single_order_notional", config.max_single_order_notional)
    _require_positive("max_daily_order_notional", config.max_daily_order_notional)
    if config.max_daily_order_notional < config.max_single_order_notional:
        raise ValueError("max_daily_order_notional must be >= max_single_order_notional")
    _require_unit_interval("max_single_order_weight_delta", config.max_single_order_weight_delta)
    _require_unit_interval("max_post_trade_symbol_weight", config.max_post_trade_symbol_weight)
    if config.min_cash_buffer_weight < 0 or config.min_cash_buffer_weight > 1:
        raise ValueError("min_cash_buffer_weight must be between 0 and 1")


def decimal_from_cli(value: str, *, label: str) -> Decimal:
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{label} must be a decimal") from exc


def _require_positive(label: str, value: Decimal) -> None:
    if value <= 0:
        raise ValueError(f"{label} must be positive")


def _require_unit_interval(label: str, value: Decimal) -> None:
    if value <= 0 or value > 1:
        raise ValueError(f"{label} must be > 0 and <= 1")


def _json_object(value: str, label: str) -> dict[str, Any]:
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must be a JSON object")
    return parsed
