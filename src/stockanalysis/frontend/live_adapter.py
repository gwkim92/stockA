from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

from stockanalysis.ingest.config import RuntimeConfig
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
    return parsed.path == "/api/remediation-tickets" or (
        parsed.path.startswith("/api/portfolio/") and parsed.path.endswith("/coverage")
    )


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
