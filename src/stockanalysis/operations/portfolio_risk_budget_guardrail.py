from __future__ import annotations

import json
from datetime import date
from decimal import Decimal, InvalidOperation

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_EVAL_NAME = "portfolio_risk_budget_guardrail"
DEFAULT_DATASET_VERSION = "portfolio-risk-budget-guardrail-v1"
DEFAULT_PIPELINE_NAME = "portfolio_risk_budget_guardrail"
DEFAULT_PROVIDER = "postgres"
DEFAULT_MODEL_NAME = "deterministic-risk-budget-v1"
DEFAULT_MAX_SECTOR_WEIGHT = Decimal("0.45")
DEFAULT_MAX_THEME_WEIGHT = Decimal("0.40")
DEFAULT_MAX_UNCLASSIFIED_WEIGHT = Decimal("0.10")


def render_portfolio_risk_budget_state_sql(*, portfolio_name: str, as_of_date: date) -> str:
    return f"""-- portfolio risk budget guardrail state lookup
with selected_portfolio as (
    select portfolio_id, portfolio_name, strategy_name, market_code
    from portfolio.portfolio
    where portfolio_name = {sql_literal(portfolio_name)}
    order by portfolio_id desc
    limit 1
),
selected_snapshot as (
    select max(position.snapshot_date) as snapshot_date
    from selected_portfolio portfolio
    join portfolio.position_snapshot position on position.portfolio_id = portfolio.portfolio_id
    where position.snapshot_date <= {sql_date(as_of_date)}
),
selected_policy as (
    select
        policy.allocation_policy_id,
        policy.policy_name,
        case when policy.portfolio_id is null then 'global' else 'portfolio' end as policy_scope,
        policy.max_single_position_weight,
        policy.min_rebalance_target_weight,
        policy.rationale
    from selected_portfolio portfolio
    join portfolio.allocation_policy policy
      on (policy.portfolio_id = portfolio.portfolio_id or policy.portfolio_id is null)
     and (policy.strategy_name = portfolio.strategy_name or policy.strategy_name is null)
     and policy.status = 'active'
     and policy.valid_from <= {sql_date(as_of_date)}
     and (policy.valid_to is null or policy.valid_to >= {sql_date(as_of_date)})
    order by
        case when policy.portfolio_id = portfolio.portfolio_id then 0 else 1 end,
        case when policy.strategy_name = portfolio.strategy_name then 0 else 1 end,
        policy.valid_from desc,
        policy.allocation_policy_id desc
    limit 1
),
position_rows as (
    select
        position.instrument_id,
        instrument.primary_symbol as symbol,
        position.snapshot_date,
        position.quantity,
        position.market_value,
        position.weight
    from selected_portfolio portfolio
    join selected_snapshot snapshot on snapshot.snapshot_date is not null
    join portfolio.position_snapshot position
      on position.portfolio_id = portfolio.portfolio_id
     and position.snapshot_date = snapshot.snapshot_date
    join ref.instrument instrument on instrument.instrument_id = position.instrument_id
    where position.quantity <> 0
      and position.weight is not null
),
membership_rows as (
    select distinct
        position.instrument_id,
        position.symbol,
        position.weight,
        node.code,
        node.name,
        node.node_type,
        node.taxonomy_family,
        case
            when node.node_type = 'sector' then 'sector'
            when node.node_type in ('macro', 'domain', 'theme') then 'theme'
            when node.taxonomy_family = 'internal_theme' then 'theme'
            else 'other'
        end as exposure_type
    from position_rows position
    join ref.instrument_classification_membership membership
      on membership.instrument_id = position.instrument_id
     and membership.valid_from <= coalesce((select snapshot_date from selected_snapshot), {sql_date(as_of_date)})
     and (
        membership.valid_to is null
        or membership.valid_to >= coalesce((select snapshot_date from selected_snapshot), {sql_date(as_of_date)})
     )
    join ref.classification_node node on node.node_id = membership.node_id
    where node.status = 'active'
),
classified_positions as (
    select distinct instrument_id
    from membership_rows
    where exposure_type in ('sector', 'theme')
),
unclassified_positions as (
    select position.symbol, position.weight
    from position_rows position
    left join classified_positions classified on classified.instrument_id = position.instrument_id
    where classified.instrument_id is null
),
sector_exposure_rows as (
    select
        code as exposure_key,
        name as exposure_name,
        sum(weight) as exposure_weight,
        count(distinct instrument_id)::integer as position_count,
        array_agg(distinct symbol order by symbol) as symbols
    from membership_rows
    where exposure_type = 'sector'
    group by code, name
),
theme_exposure_rows as (
    select
        code as exposure_key,
        name as exposure_name,
        sum(weight) as exposure_weight,
        count(distinct instrument_id)::integer as position_count,
        array_agg(distinct symbol order by symbol) as symbols
    from membership_rows
    where exposure_type = 'theme'
    group by code, name
),
position_json_rows as (
    select *
    from position_rows
    order by weight desc, symbol
),
sector_json_rows as (
    select *
    from sector_exposure_rows
    order by exposure_weight desc, exposure_key
),
theme_json_rows as (
    select *
    from theme_exposure_rows
    order by exposure_weight desc, exposure_key
)
select json_build_object(
    'portfolio_name', coalesce((select portfolio_name from selected_portfolio), {sql_literal(portfolio_name)}),
    'portfolio_found', exists(select 1 from selected_portfolio),
    'market_code', (select market_code from selected_portfolio),
    'requested_as_of_date', {sql_literal(as_of_date.isoformat())},
    'snapshot_date', (select snapshot_date::text from selected_snapshot),
    'position_count', (select count(*)::integer from position_rows),
    'position_weight_total', coalesce((select sum(weight) from position_rows), 0),
    'allocation_policy',
    coalesce(
        (
            select json_build_object(
                'allocation_policy_id', allocation_policy_id,
                'policy_name', policy_name,
                'policy_scope', policy_scope,
                'max_single_position_weight', max_single_position_weight,
                'min_rebalance_target_weight', min_rebalance_target_weight,
                'rationale', rationale
            )
            from selected_policy
        ),
        '{{}}'::json
    ),
    'positions',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'instrument_id', instrument_id,
                    'symbol', symbol,
                    'weight', weight,
                    'market_value', market_value
                )
                order by weight desc, symbol
            )
            from position_json_rows
        ),
        '[]'::json
    ),
    'sector_exposures',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'exposure_key', exposure_key,
                    'exposure_name', exposure_name,
                    'exposure_weight', exposure_weight,
                    'position_count', position_count,
                    'symbols', symbols
                )
                order by exposure_weight desc, exposure_key
            )
            from sector_json_rows
        ),
        '[]'::json
    ),
    'theme_exposures',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'exposure_key', exposure_key,
                    'exposure_name', exposure_name,
                    'exposure_weight', exposure_weight,
                    'position_count', position_count,
                    'symbols', symbols
                )
                order by exposure_weight desc, exposure_key
            )
            from theme_json_rows
        ),
        '[]'::json
    ),
    'unclassified_weight', coalesce((select sum(weight) from unclassified_positions), 0),
    'unclassified_symbols', coalesce((select array_agg(symbol order by symbol) from unclassified_positions), array[]::text[])
)::text;"""


def render_portfolio_risk_budget_guardrail_insert_sql(*, score_json: dict[str, object]) -> str:
    score_text = json.dumps(score_json, ensure_ascii=False, sort_keys=True)
    return f"""insert into ai.eval_run (
    eval_name,
    dataset_version,
    provider,
    model_name,
    score_json
)
values (
    {sql_literal(DEFAULT_EVAL_NAME)},
    {sql_literal(DEFAULT_DATASET_VERSION)},
    {sql_literal(DEFAULT_PROVIDER)},
    {sql_literal(DEFAULT_MODEL_NAME)},
    {sql_literal(score_text)}::jsonb
)
returning eval_run_id;"""


def load_portfolio_risk_budget_state(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    as_of_date: date,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_portfolio_risk_budget_state_sql(
                portfolio_name=portfolio_name,
                as_of_date=as_of_date,
            )
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Portfolio risk budget guardrail state lookup did not return a JSON object.")
    return payload


def build_portfolio_risk_budget_guardrail_report(
    *,
    portfolio_name: str,
    as_of_date: date,
    state: dict[str, object],
    execute: bool = False,
) -> dict[str, object]:
    policy = _as_dict(state.get("allocation_policy"))
    max_single = _decimal(policy.get("max_single_position_weight")) or Decimal("0.25")
    min_rebalance = _decimal(policy.get("min_rebalance_target_weight")) or Decimal("0.10")
    positions = [_position_payload(item, max_single=max_single, min_rebalance=min_rebalance) for item in _as_list(state.get("positions"))]
    sector_exposures = [
        _exposure_payload(item, exposure_type="sector", limit=DEFAULT_MAX_SECTOR_WEIGHT)
        for item in _as_list(state.get("sector_exposures"))
    ]
    theme_exposures = [
        _exposure_payload(item, exposure_type="theme", limit=DEFAULT_MAX_THEME_WEIGHT)
        for item in _as_list(state.get("theme_exposures"))
    ]
    unclassified_weight = _decimal(state.get("unclassified_weight")) or Decimal("0")
    unclassified_symbols = [str(item) for item in _as_list(state.get("unclassified_symbols"))]
    blocking_reasons = _blocking_reasons(
        portfolio_found=bool(state.get("portfolio_found")),
        snapshot_date=state.get("snapshot_date"),
        positions=positions,
        sector_exposures=sector_exposures,
        theme_exposures=theme_exposures,
        unclassified_weight=unclassified_weight,
    )
    warnings = _warning_reasons(
        sector_exposures=sector_exposures,
        theme_exposures=theme_exposures,
        benchmark_drift_status="insufficient_benchmark_composition",
    )
    risk_gate_decision = _risk_gate_decision(blocking_reasons)
    return {
        "report_name": DEFAULT_EVAL_NAME,
        "status": "planned" if not execute else "running",
        "execute": execute,
        "portfolio_name": portfolio_name,
        "as_of_date": as_of_date.isoformat(),
        "effective_snapshot_date": state.get("snapshot_date"),
        "risk_gate_decision": risk_gate_decision,
        "risk_gate_passed": risk_gate_decision == "within_budget",
        "recommendation_scoring_mutated": False,
        "paper_validation_input_allowed": risk_gate_decision == "within_budget",
        "automatic_rebalance_allowed": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "blocking_reasons": blocking_reasons,
        "warning_reasons": warnings,
        "allocation_policy": {
            "allocation_policy_id": _int(policy.get("allocation_policy_id")),
            "policy_name": policy.get("policy_name"),
            "policy_scope": policy.get("policy_scope"),
            "max_single_position_weight": _decimal_text(max_single),
            "min_rebalance_target_weight": _decimal_text(min_rebalance),
            "max_sector_weight": _decimal_text(DEFAULT_MAX_SECTOR_WEIGHT),
            "max_theme_weight": _decimal_text(DEFAULT_MAX_THEME_WEIGHT),
            "max_unclassified_weight": _decimal_text(DEFAULT_MAX_UNCLASSIFIED_WEIGHT),
        },
        "position_summary": {
            "position_count": len(positions),
            "position_weight_total": _decimal_text(_decimal(state.get("position_weight_total")) or Decimal("0")),
            "cash_or_unallocated_weight": _decimal_text(max(Decimal("0"), Decimal("1") - (_decimal(state.get("position_weight_total")) or Decimal("0")))),
            "over_single_position_limit_count": sum(1 for item in positions if item["position_size_status"] == "over_single_position_limit"),
            "below_rebalance_floor_count": sum(1 for item in positions if item["position_size_status"] == "below_rebalance_floor"),
        },
        "concentration_summary": {
            "sector_over_limit_count": sum(1 for item in sector_exposures if item["status"] == "over_limit"),
            "theme_over_limit_count": sum(1 for item in theme_exposures if item["status"] == "over_limit"),
            "unclassified_weight": _decimal_text(unclassified_weight),
            "unclassified_symbols": unclassified_symbols,
            "unclassified_over_limit": unclassified_weight > DEFAULT_MAX_UNCLASSIFIED_WEIGHT,
        },
        "benchmark_drift": {
            "status": "insufficient_benchmark_composition",
            "benchmark_source": None,
            "drift_calculated": False,
            "reason": "benchmark 구성비 데이터가 canonical DB에 없으므로 drift를 추정하지 않는다.",
        },
        "positions": positions,
        "sector_exposures": sector_exposures,
        "theme_exposures": theme_exposures,
        "next_actions": _next_actions(risk_gate_decision),
    }


def run_portfolio_risk_budget_guardrail(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    as_of_date: date,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    state = load_portfolio_risk_budget_state(
        config=config,
        portfolio_name=portfolio_name,
        as_of_date=as_of_date,
        executor=sql_executor,
    )
    report = build_portfolio_risk_budget_guardrail_report(
        portfolio_name=portfolio_name,
        as_of_date=as_of_date,
        state=state,
        execute=execute,
    )
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "portfolio_name": portfolio_name,
            "as_of_date": as_of_date.isoformat(),
            "effective_snapshot_date": report.get("effective_snapshot_date"),
            "risk_gate_decision": report["risk_gate_decision"],
            "paper_validation_input_allowed": report["paper_validation_input_allowed"],
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
        },
    )
    try:
        eval_run_id = int(
            sql_executor.execute_scalar(
                render_portfolio_risk_budget_guardrail_insert_sql(score_json={**report, "status": "completed"})
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


def _position_payload(item: object, *, max_single: Decimal, min_rebalance: Decimal) -> dict[str, object]:
    row = _as_dict(item)
    weight = _decimal(row.get("weight")) or Decimal("0")
    if weight > max_single:
        status = "over_single_position_limit"
    elif Decimal("0") < weight < min_rebalance:
        status = "below_rebalance_floor"
    else:
        status = "within_budget"
    return {
        "instrument_id": _int(row.get("instrument_id")),
        "symbol": row.get("symbol"),
        "weight": _decimal_text(weight),
        "market_value": _decimal_text(_decimal(row.get("market_value"))),
        "position_size_status": status,
        "excess_weight": _decimal_text(max(Decimal("0"), weight - max_single)),
        "shortfall_to_rebalance_floor": _decimal_text(max(Decimal("0"), min_rebalance - weight) if weight > 0 else Decimal("0")),
    }


def _exposure_payload(item: object, *, exposure_type: str, limit: Decimal) -> dict[str, object]:
    row = _as_dict(item)
    weight = _decimal(row.get("exposure_weight")) or Decimal("0")
    return {
        "exposure_type": exposure_type,
        "exposure_key": row.get("exposure_key"),
        "exposure_name": row.get("exposure_name") or row.get("exposure_key"),
        "exposure_weight": _decimal_text(weight),
        "position_count": _int(row.get("position_count")),
        "symbols": [str(item) for item in _as_list(row.get("symbols"))],
        "limit": _decimal_text(limit),
        "excess_weight": _decimal_text(max(Decimal("0"), weight - limit)),
        "status": "over_limit" if weight > limit else "within_limit",
    }


def _blocking_reasons(
    *,
    portfolio_found: bool,
    snapshot_date: object,
    positions: list[dict[str, object]],
    sector_exposures: list[dict[str, object]],
    theme_exposures: list[dict[str, object]],
    unclassified_weight: Decimal,
) -> list[dict[str, object]]:
    reasons: list[dict[str, object]] = []
    if not portfolio_found:
        reasons.append(_reason("portfolio_not_found", "포트폴리오가 없다."))
        return reasons
    if not snapshot_date or not positions:
        reasons.append(_reason("missing_position_snapshot", "해당 기준일 이전 보유 스냅샷이 없다."))
        return reasons
    for position in positions:
        if position["position_size_status"] == "over_single_position_limit":
            reasons.append(_reason("over_single_position_limit", f"{position['symbol']} 단일 종목 비중이 한도를 넘었다.", symbol=position["symbol"]))
    for exposure in [*sector_exposures, *theme_exposures]:
        if exposure["status"] == "over_limit":
            reasons.append(
                _reason(
                    f"{exposure['exposure_type']}_over_limit",
                    f"{exposure['exposure_name']} 노출이 한도를 넘었다.",
                    exposure_key=exposure["exposure_key"],
                )
            )
    if unclassified_weight > DEFAULT_MAX_UNCLASSIFIED_WEIGHT:
        reasons.append(_reason("unclassified_exposure_over_limit", "분류되지 않은 보유 비중이 한도를 넘었다."))
    return reasons


def _warning_reasons(
    *,
    sector_exposures: list[dict[str, object]],
    theme_exposures: list[dict[str, object]],
    benchmark_drift_status: str,
) -> list[dict[str, object]]:
    warnings = [
        _reason(
            benchmark_drift_status,
            "benchmark 구성비가 없어 drift는 아직 계산하지 않았다. 임의 proxy로 대체하지 않는다.",
        )
    ]
    if not sector_exposures:
        warnings.append(_reason("sector_classification_missing", "섹터 분류가 없어 섹터 집중도를 계산할 수 없다."))
    if not theme_exposures:
        warnings.append(_reason("theme_classification_missing", "테마 분류가 없어 테마 집중도를 계산할 수 없다."))
    return warnings


def _risk_gate_decision(blocking_reasons: list[dict[str, object]]) -> str:
    if not blocking_reasons:
        return "within_budget"
    first_code = str(blocking_reasons[0].get("code") or "")
    if first_code in {"portfolio_not_found", "missing_position_snapshot"}:
        return first_code
    return "blocked_by_risk_budget_review"


def _next_actions(decision: str) -> list[str]:
    if decision == "within_budget":
        return [
            "paper validation과 추천 검토 입력으로 사용할 수 있다.",
            "자동 주문과 broker submit은 계속 금지한다.",
            "benchmark drift 데이터 소스를 별도 task에서 보강한다.",
        ]
    if decision in {"portfolio_not_found", "missing_position_snapshot"}:
        return [
            "포트폴리오 또는 최신 보유 스냅샷을 먼저 적재한다.",
            "스냅샷 없이는 paper validation 입력으로 쓰지 않는다.",
        ]
    return [
        "초과 종목, 초과 섹터/테마, 미분류 노출을 먼저 검토한다.",
        "paper validation 입력은 risk review가 끝날 때까지 보류한다.",
        "자동 주문과 broker submit은 계속 금지한다.",
    ]


def _reason(code: str, message: str, **details: object) -> dict[str, object]:
    return {"code": code, "message": message, "details": details}


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _int(value: object) -> int:
    if value is None or value == "":
        return 0
    return int(value)


def _decimal(value: object) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _decimal_text(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value, "f")
