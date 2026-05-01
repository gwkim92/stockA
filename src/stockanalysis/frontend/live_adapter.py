from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlsplit

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.performance.coverage import load_portfolio_outcome_coverage_report
from stockanalysis.signal.portfolio_remediation_ticket import load_portfolio_remediation_ticket_report


CONTRACT_VERSION = "frontend-api-v0.1"
DEFAULT_PORTFOLIO_NAME = "Long Term Paper"
DEFAULT_STRATEGY_NAME = "long_term_core"
DEFAULT_COVERAGE_HORIZON_DAYS = 31


class FrontendLiveAdapterError(RuntimeError):
    code = "FrontendLiveReadError"


class FrontendLiveUnsupportedPathError(FrontendLiveAdapterError):
    code = "FrontendLiveReadUnsupportedPath"


class FrontendLiveUnavailableError(FrontendLiveAdapterError):
    code = "FrontendLiveReadUnavailable"


@dataclass(frozen=True)
class ParsedApiPath:
    path: str
    query: dict[str, str]


def resolve_live_frontend_response(
    api_path: str,
    *,
    config: RuntimeConfig | None = None,
    executor: PsqlCommandExecutor | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Resolve supported frontend API DTOs from canonical Postgres read reports."""

    runtime_config = config or RuntimeConfig.from_env()
    if executor is None and not runtime_config.psql_command:
        raise FrontendLiveUnavailableError("Missing required environment variable: STOCKANALYSIS_PSQL_COMMAND")

    parsed = parse_api_path(api_path)
    generated_at_text = _format_generated_at(generated_at)

    if parsed.path == "/api/dashboard/today":
        return build_live_dashboard_response(
            config=runtime_config,
            executor=executor,
            generated_at=generated_at_text,
        )
    if parsed.path == "/api/data-health":
        return build_live_data_health_response(
            config=runtime_config,
            executor=executor,
            generated_at=generated_at_text,
        )
    if parsed.path == "/api/remediation-tickets":
        return build_live_remediation_tickets_response(
            parsed,
            config=runtime_config,
            executor=executor,
            generated_at=generated_at_text,
        )
    if parsed.path.startswith("/api/portfolio/") and parsed.path.endswith("/coverage"):
        return build_live_portfolio_coverage_response(
            parsed,
            config=runtime_config,
            executor=executor,
            generated_at=generated_at_text,
        )

    raise FrontendLiveUnsupportedPathError(f"Live frontend API path is not supported yet: {api_path}")


def parse_api_path(api_path: str) -> ParsedApiPath:
    parsed = urlsplit(api_path)
    query_values = parse_qs(parsed.query, keep_blank_values=True)
    query: dict[str, str] = {}
    for key, values in query_values.items():
        if values:
            query[key] = values[-1]
    return ParsedApiPath(path=parsed.path, query=query)


def build_live_dashboard_response(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    state = load_frontend_dashboard_state(config=config, executor=executor)
    top_actions = [
        _build_dashboard_action_payload(item, index=index)
        for index, item in enumerate(_as_list(state.get("top_actions")), start=1)
    ]
    metrics = _as_dict(state.get("latest_metrics"))

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "data": {
            "as_of_date": str(state.get("as_of_date") or ""),
            "portfolio_name": str(state.get("portfolio_name") or DEFAULT_PORTFOLIO_NAME),
            "run_status": {
                "daily_automation": str(state.get("daily_automation") or "unknown"),
                "latest_run_id": _opaque_id("pipeline-run", state.get("latest_run_id"), "unknown"),
                "scheduler": "not_installed",
                "holiday_skip": {
                    "enabled": True,
                    "source": "PORTFOLIO_REMEDIATION_SKIP_DATES",
                    "would_skip_today": False,
                },
            },
            "attention_summary": {
                "open_ticket_count": int(state.get("open_ticket_count") or 0),
                "critical_blind_spot_count": int(state.get("critical_blind_spot_count") or 0),
                "failed_pipeline_count": int(state.get("failed_pipeline_count") or 0),
                "missing_thesis_count": int(state.get("missing_thesis_count") or 0),
                "missing_outcome_count": int(state.get("missing_outcome_count") or 0),
            },
            "top_actions": top_actions,
            "latest_metrics": {
                "covered_weight": _number(metrics.get("covered_weight")),
                "missing_thesis_weight": _number(metrics.get("missing_thesis_weight")),
                "cash_weight": _number(metrics.get("cash_weight")),
                "weight_coverage_ratio": _number(metrics.get("weight_coverage_ratio")),
            },
        },
        "links": {
            "remediation_tickets": "/api/remediation-tickets?status=open",
            "portfolio_coverage": _dashboard_coverage_link(state),
            "data_health": "/api/data-health",
        },
    }


def build_live_data_health_response(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    state = load_frontend_data_health_state(config=config, executor=executor)
    pipeline_runs = [_build_pipeline_run_payload(item) for item in _as_list(state.get("pipeline_runs"))]
    freshness = [_build_freshness_payload(item) for item in _as_list(state.get("freshness"))]
    raw_open_gates = state.get("open_gates", [])
    open_gates = [str(item) for item in raw_open_gates] if isinstance(raw_open_gates, list) else []

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "data": {
            "overall_status": str(state.get("overall_status") or "unknown"),
            "as_of_date": str(state.get("as_of_date") or ""),
            "pipeline_runs": pipeline_runs,
            "scheduler": {
                "install_status": "not_installed",
                "runtime_env_readiness": "template_rendered_placeholder_pending",
                "holiday_skip_mode": "explicit_skip_dates",
                "latest_artifact_root": str(state.get("latest_artifact_root") or ""),
            },
            "freshness": freshness,
            "open_gates": open_gates,
        },
        "links": {
            "scheduler_env_readiness": "/settings/scheduler",
            "dashboard": "/api/dashboard/today",
        },
    }


def build_live_remediation_tickets_response(
    parsed: ParsedApiPath,
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    status = parsed.query.get("status", "open") or "open"
    report = load_portfolio_remediation_ticket_report(
        config=config,
        portfolio_name=DEFAULT_PORTFOLIO_NAME,
        status=status,
        limit=50,
        executor=executor,
    )

    tickets = [_build_ticket_payload(ticket) for ticket in _as_list(report.get("tickets"))]
    latest_review_date = _latest_review_date(tickets)
    coverage_link = "/api/portfolio/Long%20Term%20Paper/coverage"
    if latest_review_date:
        coverage_link = f"{coverage_link}?asOfDate={latest_review_date}"

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "data": {
            "portfolio_name": str(report.get("portfolio_name") or DEFAULT_PORTFOLIO_NAME),
            "status_filter": status,
            "ticket_count": int(report.get("ticket_count") or len(tickets)),
            "status_counts": _normalize_count_map(
                report.get("status_counts"),
                keys=("open", "in_progress", "resolved", "ignored"),
            ),
            "tickets": tickets,
        },
        "links": {
            "dashboard": "/api/dashboard/today",
            "portfolio_coverage": coverage_link,
        },
    }


def build_live_portfolio_coverage_response(
    parsed: ParsedApiPath,
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    portfolio_name = _parse_coverage_portfolio_name(parsed.path)
    as_of_date = _parse_required_date(parsed.query, "asOfDate")
    measurement_end_date = _parse_optional_date(parsed.query, "measurementEndDate") or (
        as_of_date + timedelta(days=DEFAULT_COVERAGE_HORIZON_DAYS)
    )

    report = load_portfolio_outcome_coverage_report(
        config=config,
        portfolio_name=portfolio_name,
        snapshot_date=as_of_date,
        measurement_end_date=measurement_end_date,
        executor=executor,
    )
    positions = [_build_position_payload(position) for position in _as_list(report.get("positions"))]
    blocking_reasons = [
        f"{position['coverage_status']}:{position['symbol']}"
        for position in positions
        if position["coverage_status"] != "covered"
    ]
    status_counts = _normalize_count_map(
        report.get("status_counts"),
        keys=("covered", "missing_thesis", "missing_outcome", "missing_weight"),
    )
    weight_by_status = _as_dict(report.get("weight_by_status"))

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "data": {
            "portfolio_name": str(report.get("portfolio_name") or portfolio_name),
            "as_of_date": str(report.get("snapshot_date") or as_of_date.isoformat()),
            "strategy_name": DEFAULT_STRATEGY_NAME,
            "coverage_measurement_end_date": str(
                report.get("measurement_end_date") or measurement_end_date.isoformat()
            ),
            "summary": {
                "position_count": int(report.get("position_count") or len(positions)),
                "covered_position_count": status_counts["covered"],
                "missing_thesis_count": status_counts["missing_thesis"],
                "missing_outcome_count": status_counts["missing_outcome"],
                "covered_weight": _number(weight_by_status.get("covered")),
                "missing_thesis_weight": _number(weight_by_status.get("missing_thesis")),
                "cash_weight": _number(report.get("cash_weight")),
                "weight_coverage_ratio": _number(report.get("coverage_ratio_by_weight")),
            },
            "positions": positions,
            "attribution_readiness": {
                "is_ready": not blocking_reasons,
                "blocking_reasons": blocking_reasons,
            },
        },
        "links": {
            "remediation_tickets": "/api/remediation-tickets?status=open",
            "dashboard": "/api/dashboard/today",
        },
    }


def is_live_supported_path(api_path: str) -> bool:
    parsed = parse_api_path(api_path)
    return parsed.path in {"/api/dashboard/today", "/api/data-health", "/api/remediation-tickets"} or (
        parsed.path.startswith("/api/portfolio/") and parsed.path.endswith("/coverage")
    )


def load_frontend_dashboard_state(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(render_frontend_dashboard_state_sql(portfolio_name=DEFAULT_PORTFOLIO_NAME))
    data = json_loads_object(payload, "Frontend dashboard state lookup")
    return data


def load_frontend_data_health_state(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(render_frontend_data_health_state_sql())
    data = json_loads_object(payload, "Frontend data health state lookup")
    return data


def render_frontend_dashboard_state_sql(*, portfolio_name: str) -> str:
    return f"""-- frontend dashboard state lookup
with target_portfolio as (
    select portfolio_id, portfolio_name
    from portfolio.portfolio
    where portfolio_name = {sql_literal(portfolio_name)}
),
latest_daily_run as (
    select run_id, status, started_at, ended_at as finished_at
    from ops.pipeline_run
    where pipeline_name = 'portfolio_remediation_daily_automation'
    order by started_at desc, run_id desc
    limit 1
),
latest_snapshot as (
    select max(position.snapshot_date) as snapshot_date
    from portfolio.position_snapshot position
    join target_portfolio portfolio on portfolio.portfolio_id = position.portfolio_id
),
latest_review as (
    select max(review.review_date) as review_date
    from portfolio.review review
    join target_portfolio portfolio on portfolio.portfolio_id = review.portfolio_id
),
latest_position_rows as (
    select position.*
    from portfolio.position_snapshot position
    join target_portfolio portfolio on portfolio.portfolio_id = position.portfolio_id
    join latest_snapshot snapshot on snapshot.snapshot_date = position.snapshot_date
),
position_metrics as (
    select
        coalesce(sum(case when linked_thesis_id is not null then weight else 0 end), 0)::numeric as covered_weight,
        coalesce(sum(case when linked_thesis_id is null then weight else 0 end), 0)::numeric as missing_thesis_weight,
        coalesce(sum(weight), 0)::numeric as total_position_weight
    from latest_position_rows
    where quantity <> 0
      and weight is not null
),
open_tickets as (
    select
        ticket.remediation_ticket_id,
        ticket.action,
        ticket.suggested_runner,
        ticket.latest_reason,
        ticket.risk_level,
        ticket.remediation_type,
        review.review_date,
        instrument.primary_symbol
    from portfolio.remediation_ticket ticket
    join portfolio.review review on review.portfolio_review_id = ticket.portfolio_review_id
    join target_portfolio portfolio on portfolio.portfolio_id = review.portfolio_id
    join ref.instrument instrument on instrument.instrument_id = ticket.instrument_id
    where ticket.status = 'open'
),
ticket_counts as (
    select
        count(*)::int as open_ticket_count,
        count(*) filter (where risk_level in ('high', 'critical') or remediation_type in ('thesis_remediation', 'outcome_remediation'))::int as critical_blind_spot_count,
        count(*) filter (where action = 'needs_thesis_review')::int as missing_thesis_count,
        count(*) filter (where action = 'needs_outcome_review')::int as missing_outcome_count
    from open_tickets
),
recent_failed_runs as (
    select count(*)::int as failed_pipeline_count
    from ops.pipeline_run
    where status = 'failed'
      and started_at >= coalesce((select started_at from latest_daily_run), now() - interval '7 days')
)
select json_build_object(
    'portfolio_name', {sql_literal(portfolio_name)},
    'as_of_date', coalesce(
        (select review_date::text from latest_review),
        (select snapshot_date::text from latest_snapshot),
        current_date::text
    ),
    'daily_automation', coalesce((select status from latest_daily_run), 'unknown'),
    'latest_run_id', (select run_id from latest_daily_run),
    'failed_pipeline_count', (select failed_pipeline_count from recent_failed_runs),
    'open_ticket_count', (select open_ticket_count from ticket_counts),
    'critical_blind_spot_count', (select critical_blind_spot_count from ticket_counts),
    'missing_thesis_count', (select missing_thesis_count from ticket_counts),
    'missing_outcome_count', (select missing_outcome_count from ticket_counts),
    'top_actions',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'symbol', primary_symbol,
                    'action', action,
                    'reason', latest_reason,
                    'suggested_runner', suggested_runner,
                    'risk_level', risk_level
                )
                order by
                    case risk_level when 'critical' then 1 when 'high' then 2 when 'medium' then 3 else 4 end,
                    review_date desc,
                    remediation_ticket_id desc
            )
            from open_tickets
        ),
        '[]'::json
    ),
    'latest_metrics',
    json_build_object(
        'covered_weight', (select covered_weight from position_metrics),
        'missing_thesis_weight', (select missing_thesis_weight from position_metrics),
        'cash_weight', greatest(0::numeric, 1::numeric - coalesce((select total_position_weight from position_metrics), 0::numeric)),
        'weight_coverage_ratio',
        case
            when coalesce((select total_position_weight from position_metrics), 0::numeric) = 0 then null
            else (select covered_weight / total_position_weight from position_metrics)
        end
    )
)::text;"""


def render_frontend_data_health_state_sql() -> str:
    return """-- frontend data health state lookup
with latest_runs as (
    select distinct on (pipeline_name)
        pipeline_name,
        run_id,
        status,
        ended_at as finished_at
    from ops.pipeline_run
    order by pipeline_name, started_at desc, run_id desc
),
latest_market_price as (
    select max(trade_date) as latest_observation_date
    from market.daily_price_bar
),
latest_position_snapshot as (
    select max(snapshot_date) as latest_observation_date
    from portfolio.position_snapshot
)
select json_build_object(
    'overall_status', 'attention_required',
    'as_of_date', current_date::text,
    'pipeline_runs',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'pipeline_name', pipeline_name,
                    'latest_status', status,
                    'latest_run_id', run_id,
                    'finished_at', finished_at
                )
                order by pipeline_name
            )
            from latest_runs
        ),
        '[]'::json
    ),
    'latest_artifact_root', '',
    'freshness',
    json_build_array(
        json_build_object(
            'dataset', 'market.daily_price_bar',
            'status', case when (select latest_observation_date from latest_market_price) is null then 'missing' else 'observed' end,
            'latest_observation_date', (select latest_observation_date from latest_market_price)
        ),
        json_build_object(
            'dataset', 'portfolio.position_snapshot',
            'status', case when (select latest_observation_date from latest_position_snapshot) is null then 'missing' else 'observed' end,
            'latest_observation_date', (select latest_observation_date from latest_position_snapshot)
        )
    ),
    'open_gates',
    json_build_array(
        'production_api_server',
        'auth_rbac',
        'alert_destination',
        'actual_db_backed_frontend_live_smoke'
    )
)::text;"""


def _build_dashboard_action_payload(action: dict[str, Any], *, index: int) -> dict[str, Any]:
    symbol = str(action.get("symbol") or "UNKNOWN").upper()
    return {
        "rank": index,
        "symbol": symbol,
        "action": str(action.get("action") or "manual_review"),
        "reason": str(action.get("reason") or action.get("latest_reason") or ""),
        "suggested_runner": str(action.get("suggested_runner") or "manual_review"),
        "risk_level": str(action.get("risk_level") or "watch"),
    }


def _build_pipeline_run_payload(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "pipeline_name": str(run.get("pipeline_name") or "unknown"),
        "latest_status": str(run.get("latest_status") or run.get("status") or "unknown"),
        "latest_run_id": _opaque_id("pipeline-run", run.get("latest_run_id") or run.get("run_id"), "unknown"),
        "finished_at": _timestamp(run.get("finished_at") or run.get("ended_at")),
    }


def _build_freshness_payload(freshness: dict[str, Any]) -> dict[str, Any]:
    observation_date = freshness.get("latest_observation_date")
    return {
        "dataset": str(freshness.get("dataset") or "unknown"),
        "status": str(freshness.get("status") or "unknown"),
        "latest_observation_date": str(observation_date) if observation_date is not None else "",
    }


def _dashboard_coverage_link(state: dict[str, Any]) -> str:
    portfolio_name = str(state.get("portfolio_name") or DEFAULT_PORTFOLIO_NAME)
    encoded_name = quote(portfolio_name, safe="")
    coverage_link = f"/api/portfolio/{encoded_name}/coverage"
    as_of_date = state.get("as_of_date")
    if as_of_date:
        coverage_link = f"{coverage_link}?asOfDate={as_of_date}"
    return coverage_link


def _build_ticket_payload(ticket: dict[str, Any]) -> dict[str, Any]:
    symbol = str(ticket.get("symbol") or "UNKNOWN").upper()
    ticket_id = ticket.get("remediation_ticket_id")
    portfolio_review_id = ticket.get("portfolio_review_id")
    action = str(ticket.get("action") or "manual_review")
    return {
        "ticket_id": _opaque_id("remediation-ticket", ticket_id, symbol.lower()),
        "symbol": symbol,
        "instrument_id": _opaque_id("instrument", ticket.get("instrument_id"), symbol.lower()),
        "status": str(ticket.get("status") or "open"),
        "action": action,
        "remediation_type": str(ticket.get("remediation_type") or "manual_review"),
        "suggested_runner": str(ticket.get("suggested_runner") or "manual_review"),
        "reason": str(ticket.get("reason") or ticket.get("latest_reason") or ""),
        "risk_level": str(ticket.get("risk_level") or "watch"),
        "source_review_item_id": _opaque_id("portfolio-review-item", portfolio_review_id, f"{symbol.lower()}-{action}"),
        "source_run_id": _opaque_id("pipeline-run", ticket.get("source_run_id"), "unknown"),
        "created_at": _timestamp(ticket.get("opened_at")),
        "updated_at": _timestamp(ticket.get("updated_at")),
        "required_human_decision": str(ticket.get("suggested_next_step") or "Review manually."),
        "_review_date": str(ticket.get("review_date") or ""),
    }


def _build_position_payload(position: dict[str, Any]) -> dict[str, Any]:
    symbol = str(position.get("symbol") or "UNKNOWN").upper()
    coverage_status = str(position.get("coverage_status") or "missing_thesis")
    return {
        "symbol": symbol,
        "instrument_id": _opaque_id("instrument", position.get("instrument_id"), symbol.lower()),
        "weight": _number(position.get("weight")),
        "coverage_status": coverage_status,
        "active_thesis_id": _opaque_id("thesis", position.get("linked_thesis_id"), None)
        if position.get("linked_thesis_id") is not None
        else None,
        "outcome_status": _coverage_outcome_status(coverage_status, position.get("outcome_status")),
        "action": _coverage_action(coverage_status),
    }


def _parse_coverage_portfolio_name(path: str) -> str:
    prefix = "/api/portfolio/"
    suffix = "/coverage"
    if not path.startswith(prefix) or not path.endswith(suffix):
        raise FrontendLiveUnsupportedPathError(f"Invalid portfolio coverage path: {path}")
    encoded_name = path[len(prefix) : -len(suffix)]
    if not encoded_name:
        raise FrontendLiveUnsupportedPathError("Portfolio coverage path is missing portfolio name.")
    return unquote(encoded_name)


def _parse_required_date(query: dict[str, str], key: str) -> date:
    if key not in query or not query[key]:
        raise FrontendLiveUnsupportedPathError(f"Missing required query parameter: {key}")
    return date.fromisoformat(query[key])


def _parse_optional_date(query: dict[str, str], key: str) -> date | None:
    value = query.get(key)
    if not value:
        return None
    return date.fromisoformat(value)


def _format_generated_at(value: datetime | None) -> str:
    generated_at = value or datetime.now(timezone.utc)
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=timezone.utc)
    return generated_at.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_count_map(value: object, *, keys: tuple[str, ...]) -> dict[str, int]:
    raw = _as_dict(value)
    return {key: int(raw.get(key) or 0) for key in keys}


def _as_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def json_loads_object(payload: str, context: str) -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise FrontendLiveUnavailableError(f"{context} returned invalid JSON.") from exc
    if not isinstance(value, dict):
        raise FrontendLiveUnavailableError(f"{context} returned non-object JSON.")
    return value


def _number(value: object) -> float | None:
    if value is None:
        return None
    return float(Decimal(str(value)))


def _opaque_id(prefix: str, raw_value: object, fallback: str | None) -> str:
    if raw_value is not None:
        return f"{prefix}-{raw_value}"
    if fallback:
        return f"{prefix}-{fallback}"
    return f"{prefix}-unknown"


def _timestamp(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("+00:00", "Z")


def _coverage_outcome_status(coverage_status: str, raw_status: object) -> str:
    if coverage_status == "covered":
        return "measured"
    if coverage_status == "missing_outcome":
        return "missing"
    if coverage_status == "missing_weight":
        return "missing_weight"
    if raw_status:
        return str(raw_status)
    return "not_applicable"


def _coverage_action(coverage_status: str) -> str:
    if coverage_status == "covered":
        return "monitor"
    if coverage_status == "missing_outcome":
        return "needs_outcome_review"
    if coverage_status == "missing_weight":
        return "needs_weight_review"
    return "needs_thesis_review"


def _latest_review_date(tickets: list[dict[str, Any]]) -> str | None:
    dates = sorted(ticket.get("_review_date") for ticket in tickets if ticket.get("_review_date"))
    for ticket in tickets:
        ticket.pop("_review_date", None)
    return dates[-1] if dates else None
