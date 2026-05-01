from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlsplit

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
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
    if parsed.path == "/api/cycles":
        return build_live_cycle_state_list_response(
            parsed,
            config=runtime_config,
            executor=executor,
            generated_at=generated_at_text,
        )
    if parsed.path == "/api/events":
        return build_live_event_list_response(
            parsed,
            config=runtime_config,
            executor=executor,
            generated_at=generated_at_text,
        )
    if parsed.path.startswith("/api/themes/"):
        return build_live_theme_detail_response(
            parsed,
            config=runtime_config,
            executor=executor,
            generated_at=generated_at_text,
        )
    if parsed.path.startswith("/api/performance/") and parsed.path.endswith("/outcomes"):
        return build_live_performance_outcomes_response(
            parsed,
            config=runtime_config,
            executor=executor,
            generated_at=generated_at_text,
        )
    if parsed.path.startswith("/api/recommendations/"):
        return build_live_recommendation_detail_response(
            parsed,
            config=runtime_config,
            executor=executor,
            generated_at=generated_at_text,
        )
    if parsed.path.startswith("/api/theses/"):
        return build_live_thesis_detail_response(
            parsed,
            config=runtime_config,
            executor=executor,
            generated_at=generated_at_text,
        )
    if parsed.path.startswith("/api/ai-evidence/"):
        return build_live_ai_evidence_detail_response(
            parsed,
            config=runtime_config,
            executor=executor,
            generated_at=generated_at_text,
        )
    if parsed.path.startswith("/api/source-documents/"):
        return build_live_source_document_detail_response(
            parsed,
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


def build_live_cycle_state_list_response(
    parsed: ParsedApiPath,
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    as_of_date = _parse_required_date(parsed.query, "asOfDate")
    state = load_frontend_cycle_state_list_state(
        config=config,
        executor=executor,
        as_of_date=as_of_date,
    )
    cycle_states = [_build_cycle_state_item_payload(item) for item in _as_list(state.get("cycle_states"))]

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "data": {
            "as_of_date": str(state.get("as_of_date") or as_of_date.isoformat()),
            "strategy_name": str(state.get("strategy_name") or DEFAULT_STRATEGY_NAME),
            "horizon_type": str(state.get("horizon_type") or "long_term"),
            "universe_version": str(state.get("universe_version") or "unknown"),
            "cycle_states": cycle_states,
        },
        "links": _cycle_state_list_links(cycle_states, as_of_date=as_of_date),
    }


def build_live_event_list_response(
    parsed: ParsedApiPath,
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    as_of_date = _parse_required_date(parsed.query, "asOfDate")
    theme_key = parsed.query.get("themeKey") or None
    symbol = parsed.query.get("symbol") or None
    event_type = parsed.query.get("eventType") or "all"
    state = load_frontend_event_list_state(
        config=config,
        executor=executor,
        as_of_date=as_of_date,
        theme_key=theme_key,
        symbol=symbol,
        event_type=event_type,
    )
    events = [_build_event_payload(item) for item in _as_list(state.get("events"))]
    summary = _as_dict(state.get("summary"))

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "data": {
            "as_of_date": str(state.get("as_of_date") or as_of_date.isoformat()),
            "filters": {
                "theme_key": theme_key,
                "symbol": symbol.upper() if symbol else None,
                "event_type": event_type,
            },
            "summary": {
                "event_count": int(summary.get("event_count") or len(events)),
                "ai_extracted_count": int(summary.get("ai_extracted_count") or 0),
                "source_document_count": int(summary.get("source_document_count") or 0),
                "themes_represented": int(summary.get("themes_represented") or 0),
            },
            "events": events,
        },
        "links": _event_list_links(events, as_of_date=as_of_date),
    }


def build_live_theme_detail_response(
    parsed: ParsedApiPath,
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    as_of_date = _parse_required_date(parsed.query, "asOfDate")
    theme_key = _parse_theme_key(parsed.path)
    state = load_frontend_theme_detail_state(
        config=config,
        executor=executor,
        theme_key=theme_key,
        as_of_date=as_of_date,
    )
    features = _as_dict(state.get("features"))
    linked_instruments = [
        _build_theme_linked_instrument_payload(item) for item in _as_list(state.get("linked_instruments"))
    ]
    supporting_events = [_build_theme_supporting_event_payload(item) for item in _as_list(state.get("supporting_events"))]

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "data": {
            "theme_key": str(state.get("theme_key") or theme_key),
            "theme_name": str(state.get("theme_name") or theme_key),
            "as_of_date": str(state.get("as_of_date") or as_of_date.isoformat()),
            "strategy_name": DEFAULT_STRATEGY_NAME,
            "horizon_type": "long_term",
            "state": str(state.get("state") or "unknown"),
            "previous_state": str(state.get("previous_state") or "unknown"),
            "confidence": _number(state.get("confidence")),
            "cycle_score": _number(state.get("cycle_score")),
            "cycle_history": [_build_cycle_history_payload(item) for item in _as_list(state.get("cycle_history"))],
            "features": {
                "event_intensity": _number(features.get("event_intensity")),
                "price_momentum": _number(features.get("price_momentum")),
                "fundamental_quality": _number(features.get("fundamental_quality")),
            },
            "linked_instruments": linked_instruments,
            "supporting_events": supporting_events,
            "operator_notes": [
                "Cycle state is context for thesis quality, not an automatic buy signal.",
                "Supporting events require evidence review before they justify thesis mutation.",
            ],
        },
        "links": _theme_detail_links(theme_key=theme_key, as_of_date=as_of_date, linked_instruments=linked_instruments, supporting_events=supporting_events),
    }


def build_live_performance_outcomes_response(
    parsed: ParsedApiPath,
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    portfolio_name = _parse_performance_portfolio_name(parsed.path)
    measurement_end_date = _parse_required_date(parsed.query, "measurementEndDate")
    state = load_frontend_performance_outcomes_state(
        config=config,
        executor=executor,
        portfolio_name=portfolio_name,
        measurement_end_date=measurement_end_date,
    )
    summary = _as_dict(state.get("summary"))
    outcomes = [_build_performance_outcome_payload(item) for item in _as_list(state.get("outcomes"))]
    attribution_components = [
        _build_attribution_component_payload(item) for item in _as_list(state.get("attribution_components"))
    ]
    coverage_exclusions = [_build_coverage_exclusion_payload(item) for item in _as_list(state.get("coverage_exclusions"))]
    quality_gates = [_build_quality_gate_payload(item) for item in _as_list(state.get("quality_gates"))]

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "data": {
            "portfolio_name": str(state.get("portfolio_name") or portfolio_name),
            "strategy_name": str(state.get("strategy_name") or DEFAULT_STRATEGY_NAME),
            "snapshot_date": str(state.get("snapshot_date") or ""),
            "measurement_start_date": str(state.get("measurement_start_date") or ""),
            "measurement_end_date": str(state.get("measurement_end_date") or measurement_end_date.isoformat()),
            "benchmark_code": str(state.get("benchmark_code") or "SPY"),
            "methodology": str(state.get("methodology") or "position_weighted_alpha_v1"),
            "summary": _build_performance_summary(summary, outcomes, attribution_components, coverage_exclusions),
            "outcomes": outcomes,
            "attribution_components": attribution_components,
            "coverage_exclusions": coverage_exclusions,
            "quality_gates": quality_gates,
        },
        "links": _performance_links(
            portfolio_name=str(state.get("portfolio_name") or portfolio_name),
            snapshot_date=str(state.get("snapshot_date") or ""),
            outcomes=outcomes,
            attribution_components=attribution_components,
        ),
    }


def build_live_recommendation_detail_response(
    parsed: ParsedApiPath,
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    identifier = _parse_detail_identifier(parsed.path, "/api/recommendations/")
    state = load_frontend_recommendation_detail_state(config=config, executor=executor, identifier=identifier)
    score_components = [
        _build_recommendation_score_component_payload(item) for item in _as_list(state.get("score_components"))
    ]
    linked_thesis_id = state.get("linked_thesis_id")
    outcome = _as_dict(state.get("outcome"))
    symbol = str(state.get("symbol") or "UNKNOWN").upper()

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "data": {
            "recommendation_id": _recommendation_detail_id(state, identifier),
            "symbol": symbol,
            "instrument_id": _opaque_id("instrument", state.get("instrument_id"), symbol.lower()),
            "as_of_date": str(state.get("as_of_date") or ""),
            "strategy_name": str(state.get("strategy_name") or DEFAULT_STRATEGY_NAME),
            "horizon_type": str(state.get("horizon_type") or "long_term"),
            "recommendation": str(state.get("recommendation") or "monitor"),
            "score": _number(state.get("score")),
            "score_version": str(state.get("score_version") or "unknown"),
            "score_components": score_components,
            "linked_thesis_id": _opaque_id("thesis", linked_thesis_id, None) if linked_thesis_id is not None else None,
            "outcome": {
                "measurement_end_date": str(outcome.get("measurement_end_date") or ""),
                "absolute_return": _number(outcome.get("absolute_return")),
                "benchmark_return": _number(outcome.get("benchmark_return")),
                "alpha": _number(outcome.get("alpha")),
                "label": str(outcome.get("label") or "unmeasured"),
            },
        },
        "links": _recommendation_detail_links(state, identifier=identifier),
    }


def build_live_thesis_detail_response(
    parsed: ParsedApiPath,
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    identifier = _parse_detail_identifier(parsed.path, "/api/theses/")
    state = load_frontend_thesis_detail_state(config=config, executor=executor, identifier=identifier)
    symbol = str(state.get("symbol") or "UNKNOWN").upper()
    latest_review = _as_dict(state.get("latest_review"))
    evidence = [_build_thesis_evidence_payload(item) for item in _as_list(state.get("evidence"))]

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "data": {
            "thesis_id": _thesis_detail_id(state, identifier),
            "symbol": symbol,
            "instrument_id": _opaque_id("instrument", state.get("instrument_id"), symbol.lower()),
            "status": str(state.get("status") or "unknown"),
            "thesis_version": str(state.get("thesis_version") or "bootstrap-v1"),
            "created_from_recommendation_id": _opaque_id(
                "recommendation",
                state.get("created_from_recommendation_id"),
                None,
            )
            if state.get("created_from_recommendation_id") is not None
            else None,
            "summary": str(state.get("summary") or ""),
            "core_claims": [str(item) for item in state.get("core_claims", [])]
            if isinstance(state.get("core_claims"), list)
            else [],
            "invalidation_conditions": [
                _build_invalidation_condition_payload(item)
                for item in _as_list(state.get("invalidation_conditions"))
            ],
            "latest_review": {
                "review_id": _opaque_id("thesis-review", latest_review.get("review_id"), None)
                if latest_review.get("review_id") is not None
                else None,
                "action": str(latest_review.get("action") or "unreviewed"),
                "risk_level": str(latest_review.get("risk_level") or "unknown"),
                "reviewed_at": _timestamp(latest_review.get("reviewed_at")),
            },
            "evidence": evidence,
        },
        "links": _thesis_detail_links(state, identifier=identifier),
    }


def build_live_ai_evidence_detail_response(
    parsed: ParsedApiPath,
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    identifier = _parse_detail_identifier(parsed.path, "/api/ai-evidence/")
    state = load_frontend_ai_evidence_detail_state(config=config, executor=executor, identifier=identifier)
    instrument = _as_dict(state.get("instrument"))
    classification = _as_dict(state.get("classification"))
    extraction_run = _as_dict(state.get("extraction_run"))

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "data": {
            "evidence_id": _ai_evidence_detail_id(state, identifier),
            "title": str(state.get("title") or ""),
            "evidence_type": str(state.get("evidence_type") or "source_document_event"),
            "event_at": _timestamp(state.get("event_at")),
            "instrument": {
                "symbol": str(instrument.get("symbol") or "UNKNOWN").upper(),
                "instrument_id": _opaque_id("instrument", instrument.get("instrument_id"), "unknown"),
            },
            "source_document_id": _source_document_detail_id_from_raw(state.get("source_document_id")),
            "classification": {
                "theme_key": str(classification.get("theme_key") or "UNCLASSIFIED"),
                "theme_name": str(classification.get("theme_name") or "Unclassified"),
                "impact_direction": str(classification.get("impact_direction") or "unknown"),
                "impact_score": _number(classification.get("impact_score")),
            },
            "extraction_run": {
                "run_id": _opaque_id("pipeline-run", extraction_run.get("run_id"), "unknown"),
                "status": str(extraction_run.get("status") or "unknown"),
                "provider": str(extraction_run.get("provider") or "unknown"),
                "model_id": str(extraction_run.get("model_id") or "unknown"),
                "prompt_version": str(extraction_run.get("prompt_version") or "unknown"),
                "finished_at": _timestamp(extraction_run.get("finished_at")),
                "input_tokens": int(extraction_run.get("input_tokens") or 0),
                "output_tokens": int(extraction_run.get("output_tokens") or 0),
                "estimated_cost_usd": _number(extraction_run.get("estimated_cost_usd")),
                "quality_gate": str(extraction_run.get("quality_gate") or "human_review_required"),
            },
            "extracted_fields": [_build_extracted_field_payload(item) for item in _as_list(state.get("extracted_fields"))],
            "source_chunks": [_build_source_chunk_payload(item) for item in _as_list(state.get("source_chunks"))],
            "audit_notes": [
                "AI output is stored as evidence metadata only; it does not place trades or mutate thesis state.",
                "quality_gate requires human review before this event can justify a thesis change.",
            ],
        },
        "links": _ai_evidence_links(state, identifier=identifier),
    }


def build_live_source_document_detail_response(
    parsed: ParsedApiPath,
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    identifier = _parse_detail_identifier(parsed.path, "/api/source-documents/")
    state = load_frontend_source_document_detail_state(config=config, executor=executor, identifier=identifier)
    retrieval = _as_dict(state.get("retrieval"))

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "data": {
            "document_id": _source_document_detail_id(state, identifier),
            "title": str(state.get("title") or ""),
            "source_type": str(state.get("source_type") or "source_document"),
            "publisher": str(state.get("publisher") or "unknown"),
            "symbol": str(state.get("symbol") or "UNKNOWN").upper(),
            "cik": str(state.get("cik") or ""),
            "form_type": str(state.get("form_type") or ""),
            "period_end": str(state.get("period_end") or ""),
            "filed_at": _timestamp(state.get("filed_at")),
            "accession_id": str(state.get("accession_id") or ""),
            "storage_uri": str(state.get("storage_uri") or ""),
            "checksum": str(state.get("checksum") or ""),
            "retrieval": {
                "source_run_id": _opaque_id("pipeline-run", retrieval.get("source_run_id"), "unknown"),
                "fetched_at": _timestamp(retrieval.get("fetched_at")),
                "parser_version": str(retrieval.get("parser_version") or "unknown"),
            },
            "excerpts": [_build_source_chunk_payload(item) for item in _as_list(state.get("excerpts"))],
            "linked_evidence": [_build_linked_evidence_payload(item) for item in _as_list(state.get("linked_evidence"))],
            "access_policy": {
                "browser_download_enabled": False,
                "reason": "raw document delivery and access control are deferred until auth/RBAC exists",
            },
        },
        "links": _source_document_links(state, identifier=identifier),
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
    return (
        parsed.path
        in {"/api/dashboard/today", "/api/data-health", "/api/cycles", "/api/events", "/api/remediation-tickets"}
        or parsed.path.startswith("/api/themes/")
        or (parsed.path.startswith("/api/performance/") and parsed.path.endswith("/outcomes"))
        or parsed.path.startswith("/api/recommendations/")
        or parsed.path.startswith("/api/theses/")
        or parsed.path.startswith("/api/ai-evidence/")
        or parsed.path.startswith("/api/source-documents/")
        or (parsed.path.startswith("/api/portfolio/") and parsed.path.endswith("/coverage"))
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


def load_frontend_cycle_state_list_state(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    as_of_date: date,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(render_frontend_cycle_state_list_sql(as_of_date=as_of_date))
    return json_loads_object(payload, "Frontend cycle state list lookup")


def load_frontend_event_list_state(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    as_of_date: date,
    theme_key: str | None,
    symbol: str | None,
    event_type: str,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(
        render_frontend_event_list_state_sql(
            as_of_date=as_of_date,
            theme_key=theme_key,
            symbol=symbol,
            event_type=event_type,
        )
    )
    return json_loads_object(payload, "Frontend event list state lookup")


def load_frontend_theme_detail_state(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    theme_key: str,
    as_of_date: date,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(
        render_frontend_theme_detail_state_sql(theme_key=theme_key, as_of_date=as_of_date)
    )
    return json_loads_object(payload, "Frontend theme detail state lookup")


def load_frontend_performance_outcomes_state(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    portfolio_name: str,
    measurement_end_date: date,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(
        render_frontend_performance_outcomes_state_sql(
            portfolio_name=portfolio_name,
            measurement_end_date=measurement_end_date,
        )
    )
    return json_loads_object(payload, "Frontend performance outcomes state lookup")


def load_frontend_recommendation_detail_state(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    identifier: str,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(render_frontend_recommendation_detail_state_sql(identifier=identifier))
    return json_loads_object(payload, "Frontend recommendation detail state lookup")


def load_frontend_thesis_detail_state(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    identifier: str,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(render_frontend_thesis_detail_state_sql(identifier=identifier))
    return json_loads_object(payload, "Frontend thesis detail state lookup")


def load_frontend_ai_evidence_detail_state(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    identifier: str,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(render_frontend_ai_evidence_detail_state_sql(identifier=identifier))
    return json_loads_object(payload, "Frontend AI evidence detail state lookup")


def load_frontend_source_document_detail_state(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    identifier: str,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(render_frontend_source_document_detail_state_sql(identifier=identifier))
    return json_loads_object(payload, "Frontend source document detail state lookup")


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


def render_frontend_cycle_state_list_sql(*, as_of_date: date) -> str:
    return f"""-- frontend cycle state list lookup
with selected_universe as (
    select batch.*
    from signal.strategy_universe_batch batch
    where batch.as_of_date <= {sql_date(as_of_date)}
      and batch.strategy_name = {sql_literal(DEFAULT_STRATEGY_NAME)}
    order by batch.as_of_date desc, batch.universe_batch_id desc
    limit 1
),
latest_cycle as (
    select distinct on (snapshot.node_id)
        snapshot.*,
        node.code as theme_key,
        node.name as theme_name
    from signal.cycle_state_snapshot snapshot
    join ref.classification_node node on node.node_id = snapshot.node_id
    where node.taxonomy_family = 'internal_theme'
      and snapshot.as_of_date <= {sql_date(as_of_date)}
    order by snapshot.node_id, snapshot.as_of_date desc
),
previous_cycle as (
    select distinct on (snapshot.node_id)
        snapshot.node_id,
        snapshot.cycle_state
    from signal.cycle_state_snapshot snapshot
    join latest_cycle current_cycle on current_cycle.node_id = snapshot.node_id
    where snapshot.as_of_date < current_cycle.as_of_date
    order by snapshot.node_id, snapshot.as_of_date desc
),
instrument_rollup as (
    select
        current_cycle.node_id,
        count(distinct instrument.instrument_id)::integer as instrument_count,
        array_remove((array_agg(distinct instrument.primary_symbol order by instrument.primary_symbol))[1:5], null::text) as top_symbols
    from latest_cycle current_cycle
    left join ref.instrument_classification_membership membership
      on membership.node_id = current_cycle.node_id
     and membership.membership_type = 'derived_theme'
     and membership.valid_from <= {sql_date(as_of_date)}
     and (membership.valid_to is null or membership.valid_to >= {sql_date(as_of_date)})
    left join ref.instrument instrument on instrument.instrument_id = membership.instrument_id
    group by current_cycle.node_id
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'strategy_name', coalesce((select strategy_name from selected_universe), {sql_literal(DEFAULT_STRATEGY_NAME)}),
    'horizon_type', coalesce((select horizon_type from selected_universe), 'long_term'),
    'universe_version', coalesce((select universe_version from selected_universe), 'unknown'),
    'cycle_states',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'theme_key', current_cycle.theme_key,
                    'theme_name', current_cycle.theme_name,
                    'state', current_cycle.cycle_state,
                    'previous_state', coalesce(previous_cycle.cycle_state, 'unknown'),
                    'confidence',
                    coalesce(
                        nullif(current_cycle.evidence_json ->> 'average_event_confidence', '')::numeric,
                        current_cycle.cycle_score
                    ),
                    'instrument_count', coalesce(instrument_rollup.instrument_count, 0),
                    'top_symbols', coalesce(instrument_rollup.top_symbols, array[]::text[]),
                    'features',
                    json_build_object(
                        'event_intensity',
                        coalesce(
                            current_cycle.event_heat_score,
                            nullif(current_cycle.evidence_json ->> 'event_heat_score', '')::numeric
                        ),
                        'price_momentum',
                        coalesce(
                            current_cycle.trend_score,
                            nullif(current_cycle.evidence_json ->> 'trend_score', '')::numeric
                        ),
                        'fundamental_quality',
                        coalesce(
                            current_cycle.valuation_score,
                            current_cycle.breadth_score,
                            nullif(current_cycle.evidence_json ->> 'breadth_score', '')::numeric
                        )
                    )
                )
                order by current_cycle.cycle_score desc nulls last, current_cycle.theme_key
            )
            from latest_cycle current_cycle
            left join previous_cycle on previous_cycle.node_id = current_cycle.node_id
            left join instrument_rollup on instrument_rollup.node_id = current_cycle.node_id
        ),
        '[]'::json
    )
)::text;"""


def render_frontend_event_list_state_sql(
    *,
    as_of_date: date,
    theme_key: str | None,
    symbol: str | None,
    event_type: str,
) -> str:
    filters = _event_list_sql_filters(theme_key=theme_key, symbol=symbol, event_type=event_type)
    return f"""-- frontend event list state lookup
with event_rows as (
    select
        event_row.event_id,
        event_row.title,
        event_row.event_type,
        event_row.event_at,
        instrument.instrument_id,
        instrument.primary_symbol,
        theme.code as theme_key,
        theme.name as theme_name,
        coalesce(instrument_impact.impact_direction, classification_impact.impact_direction, event_row.impact_polarity, 'unknown') as impact_direction,
        coalesce(instrument_impact.impact_strength, classification_impact.impact_strength, event_row.significance_score) as impact_score,
        source_document.external_document_id as source_document_id,
        source_document.document_id as raw_source_document_id,
        evidence.artifact_id as ai_evidence_id,
        case
            when evidence.artifact_id is not null then 'human_review_required'
            when source_document.document_id is not null then 'source_document_review_required'
            else 'deterministic_review_required'
        end as quality_gate
    from event.event event_row
    left join event.event_instrument_impact instrument_impact on instrument_impact.event_id = event_row.event_id
    left join ref.instrument instrument on instrument.instrument_id = instrument_impact.instrument_id
    left join event.event_classification_impact classification_impact on classification_impact.event_id = event_row.event_id
    left join ref.classification_node theme
      on theme.node_id = classification_impact.node_id
     and theme.taxonomy_family = 'internal_theme'
    left join event.event_document_link document_link
      on document_link.event_id = event_row.event_id
     and document_link.link_type = 'source'
    left join ingest.source_document source_document on source_document.document_id = document_link.document_id
    left join lateral (
        select artifact_id
        from ai.extraction_artifact artifact
        where artifact.event_id = event_row.event_id
        order by artifact.artifact_id desc
        limit 1
    ) evidence on true
    where event_row.event_at < ({sql_date(as_of_date)} + interval '1 day')
{filters}
    order by event_row.event_at desc, event_row.event_id desc
    limit 100
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'summary',
    json_build_object(
        'event_count', (select count(*)::int from event_rows),
        'ai_extracted_count', (select count(*) filter (where ai_evidence_id is not null)::int from event_rows),
        'source_document_count', (select count(distinct raw_source_document_id)::int from event_rows where raw_source_document_id is not null),
        'themes_represented', (select count(distinct theme_key)::int from event_rows where theme_key is not null)
    ),
    'events',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'event_id', event_id,
                    'title', title,
                    'event_type', event_type,
                    'event_at', event_at,
                    'instrument_id', instrument_id,
                    'symbol', primary_symbol,
                    'theme_key', theme_key,
                    'theme_name', theme_name,
                    'impact_direction', impact_direction,
                    'impact_score', impact_score,
                    'source_document_id', source_document_id,
                    'raw_source_document_id', raw_source_document_id,
                    'ai_evidence_id', ai_evidence_id,
                    'quality_gate', quality_gate
                )
                order by event_at desc, event_id desc
            )
            from event_rows
        ),
        '[]'::json
    )
)::text;"""


def render_frontend_theme_detail_state_sql(*, theme_key: str, as_of_date: date) -> str:
    return f"""-- frontend theme detail state lookup
with target_theme as (
    select node_id, code, name
    from ref.classification_node
    where taxonomy_family = 'internal_theme'
      and code = {sql_literal(theme_key)}
    limit 1
),
current_cycle as (
    select snapshot.*
    from signal.cycle_state_snapshot snapshot
    join target_theme theme on theme.node_id = snapshot.node_id
    where snapshot.as_of_date <= {sql_date(as_of_date)}
    order by snapshot.as_of_date desc
    limit 1
),
previous_cycle as (
    select snapshot.*
    from signal.cycle_state_snapshot snapshot
    join target_theme theme on theme.node_id = snapshot.node_id
    where snapshot.as_of_date < (select as_of_date from current_cycle)
    order by snapshot.as_of_date desc
    limit 1
),
cycle_history as (
    select snapshot.as_of_date, snapshot.cycle_state, snapshot.cycle_score
    from signal.cycle_state_snapshot snapshot
    join target_theme theme on theme.node_id = snapshot.node_id
    where snapshot.as_of_date <= {sql_date(as_of_date)}
    order by snapshot.as_of_date desc
    limit 6
),
linked_instruments as (
    select
        instrument.instrument_id,
        instrument.primary_symbol,
        membership.confidence as membership_strength,
        thesis.thesis_id as active_thesis_id,
        recommendation.recommendation_id as latest_recommendation_id
    from ref.instrument_classification_membership membership
    join target_theme theme on theme.node_id = membership.node_id
    join ref.instrument instrument on instrument.instrument_id = membership.instrument_id
    left join lateral (
        select thesis_id
        from signal.investment_thesis thesis
        where thesis.instrument_id = instrument.instrument_id
          and thesis.status = 'active'
        order by thesis.thesis_id desc
        limit 1
    ) thesis on true
    left join lateral (
        select recommendation.recommendation_id
        from signal.recommendation recommendation
        join signal.recommendation_batch batch on batch.batch_id = recommendation.batch_id
        where recommendation.instrument_id = instrument.instrument_id
          and batch.as_of_date <= {sql_date(as_of_date)}
        order by batch.as_of_date desc, recommendation.recommendation_id desc
        limit 1
    ) recommendation on true
    where membership.valid_from <= {sql_date(as_of_date)}
      and (membership.valid_to is null or membership.valid_to >= {sql_date(as_of_date)})
    order by membership.confidence desc nulls last, instrument.primary_symbol
    limit 25
),
supporting_events as (
    select
        event_row.event_id,
        event_row.title,
        event_row.event_at,
        instrument.primary_symbol,
        coalesce(instrument_impact.impact_direction, classification_impact.impact_direction, event_row.impact_polarity, 'unknown') as impact_direction,
        coalesce(instrument_impact.impact_strength, classification_impact.impact_strength, event_row.significance_score) as impact_score,
        source_document.external_document_id as source_document_id,
        source_document.document_id as raw_source_document_id,
        evidence.artifact_id as ai_evidence_id
    from target_theme theme
    join event.event_classification_impact classification_impact on classification_impact.node_id = theme.node_id
    join event.event event_row on event_row.event_id = classification_impact.event_id
    left join event.event_instrument_impact instrument_impact on instrument_impact.event_id = event_row.event_id
    left join ref.instrument instrument on instrument.instrument_id = instrument_impact.instrument_id
    left join event.event_document_link document_link
      on document_link.event_id = event_row.event_id
     and document_link.link_type = 'source'
    left join ingest.source_document source_document on source_document.document_id = document_link.document_id
    left join lateral (
        select artifact_id
        from ai.extraction_artifact artifact
        where artifact.event_id = event_row.event_id
        order by artifact.artifact_id desc
        limit 1
    ) evidence on true
    where event_row.event_at < ({sql_date(as_of_date)} + interval '1 day')
    order by event_row.event_at desc, event_row.event_id desc
    limit 25
)
select json_build_object(
    'theme_key', coalesce((select code from target_theme), {sql_literal(theme_key)}),
    'theme_name', coalesce((select name from target_theme), {sql_literal(theme_key)}),
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'state', coalesce((select cycle_state from current_cycle), 'unknown'),
    'previous_state', coalesce((select cycle_state from previous_cycle), 'unknown'),
    'confidence', coalesce((select (evidence_json ->> 'average_event_confidence')::numeric from current_cycle), (select cycle_score from current_cycle)),
    'cycle_score', (select cycle_score from current_cycle),
    'cycle_history',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'as_of_date', as_of_date,
                    'state', cycle_state,
                    'confidence', cycle_score
                )
                order by as_of_date
            )
            from cycle_history
        ),
        '[]'::json
    ),
    'features',
    json_build_object(
        'event_intensity', (select event_heat_score from current_cycle),
        'price_momentum', (select trend_score from current_cycle),
        'fundamental_quality', coalesce((select valuation_score from current_cycle), (select breadth_score from current_cycle))
    ),
    'linked_instruments',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'symbol', primary_symbol,
                    'instrument_id', instrument_id,
                    'membership_strength', membership_strength,
                    'active_thesis_id', active_thesis_id,
                    'latest_recommendation_id', latest_recommendation_id
                )
                order by membership_strength desc nulls last, primary_symbol
            )
            from linked_instruments
        ),
        '[]'::json
    ),
    'supporting_events',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'event_id', event_id,
                    'title', title,
                    'event_at', event_at,
                    'symbol', primary_symbol,
                    'impact_direction', impact_direction,
                    'impact_score', impact_score,
                    'ai_evidence_id', ai_evidence_id,
                    'source_document_id', source_document_id,
                    'raw_source_document_id', raw_source_document_id
                )
                order by event_at desc, event_id desc
            )
            from supporting_events
        ),
        '[]'::json
    )
)::text;"""


def render_frontend_performance_outcomes_state_sql(
    *,
    portfolio_name: str,
    measurement_end_date: date,
) -> str:
    return f"""-- frontend performance outcomes state lookup
with selected_portfolio as (
    select portfolio_id, portfolio_name, strategy_name
    from portfolio.portfolio
    where portfolio_name = {sql_literal(portfolio_name)}
    limit 1
),
selected_run as (
    select run.*
    from performance.attribution_run run
    join selected_portfolio portfolio on portfolio.portfolio_id = run.portfolio_id
    where run.measurement_end_date = {sql_date(measurement_end_date)}
    order by run.snapshot_date desc, run.attribution_run_id desc
    limit 1
),
outcome_rows as (
    select
        outcome.outcome_id,
        outcome.recommendation_id,
        recommendation.thesis_id,
        instrument.instrument_id,
        instrument.primary_symbol,
        recommendation.action as recommendation_action,
        outcome.horizon_days,
        outcome.absolute_return_pct,
        outcome.benchmark_code,
        outcome.benchmark_return_pct,
        outcome.alpha_pct,
        outcome.outcome_label,
        position.weight as position_weight,
        outcome.source_run_id
    from selected_run run
    join performance.recommendation_outcome outcome
      on outcome.measurement_start_date = run.measurement_start_date
     and outcome.measurement_end_date = run.measurement_end_date
    join signal.recommendation recommendation on recommendation.recommendation_id = outcome.recommendation_id
    join ref.instrument instrument on instrument.instrument_id = recommendation.instrument_id
    join portfolio.position_snapshot position
      on position.portfolio_id = run.portfolio_id
     and position.snapshot_date = run.snapshot_date
     and position.instrument_id = recommendation.instrument_id
     and position.quantity <> 0
    order by outcome.alpha_pct desc nulls last, instrument.primary_symbol
),
component_rows as (
    select
        component.attribution_component_id,
        component.component_type,
        component.component_key,
        component.instrument_id,
        instrument.primary_symbol,
        node.code as theme_key,
        component.weight,
        component.return_pct,
        component.benchmark_return_pct,
        component.alpha_pct,
        component.contribution_bps,
        component.summary
    from selected_run run
    join performance.attribution_component component on component.attribution_run_id = run.attribution_run_id
    left join ref.instrument instrument on instrument.instrument_id = component.instrument_id
    left join signal.investment_thesis thesis on thesis.thesis_id = component.thesis_id
    left join ref.classification_node node on node.node_id = thesis.primary_node_id
    order by component.attribution_component_id
),
coverage_exclusions as (
    select
        instrument.primary_symbol,
        instrument.instrument_id,
        position.weight,
        case
            when position.linked_thesis_id is null then 'missing_thesis'
            when thesis_outcome.outcome_id is null then 'missing_outcome'
            when position.weight is null then 'missing_weight'
            else 'covered'
        end as reason
    from selected_run run
    join portfolio.position_snapshot position
      on position.portfolio_id = run.portfolio_id
     and position.snapshot_date = run.snapshot_date
    join ref.instrument instrument on instrument.instrument_id = position.instrument_id
    left join performance.thesis_outcome thesis_outcome
      on thesis_outcome.thesis_id = position.linked_thesis_id
     and thesis_outcome.measurement_start_date = run.measurement_start_date
     and thesis_outcome.measurement_end_date = run.measurement_end_date
    where position.quantity <> 0
      and (
          position.linked_thesis_id is null
          or thesis_outcome.outcome_id is null
          or position.weight is null
      )
)
select json_build_object(
    'portfolio_name', coalesce((select portfolio_name from selected_portfolio), {sql_literal(portfolio_name)}),
    'strategy_name', coalesce((select strategy_name from selected_portfolio), {sql_literal(DEFAULT_STRATEGY_NAME)}),
    'snapshot_date', (select snapshot_date from selected_run),
    'measurement_start_date', (select measurement_start_date from selected_run),
    'measurement_end_date', coalesce((select measurement_end_date from selected_run), {sql_date(measurement_end_date)}),
    'benchmark_code', coalesce((select benchmark_code from outcome_rows where benchmark_code is not null limit 1), 'SPY'),
    'methodology', coalesce((select methodology from selected_run), 'position_weighted_alpha_v1'),
    'summary',
    json_build_object(
        'measured_recommendation_count', (select count(*)::int from outcome_rows),
        'measured_thesis_count', (select count(distinct thesis_id)::int from outcome_rows where thesis_id is not null),
        'outperform_count', (select count(*) filter (where outcome_label = 'outperform')::int from outcome_rows),
        'underperform_count', (select count(*) filter (where outcome_label = 'underperform')::int from outcome_rows),
        'hit_rate',
        case
            when (select count(*) from outcome_rows) = 0 then null
            else ((select count(*) filter (where outcome_label in ('outperform', 'positive')) from outcome_rows)::numeric / (select count(*) from outcome_rows)::numeric)
        end,
        'average_alpha', (select avg(alpha_pct) from outcome_rows),
        'security_lens_contribution_bps', coalesce((select sum(contribution_bps) from component_rows where component_type = 'security_selection'), 0),
        'theme_lens_contribution_bps', coalesce((select sum(contribution_bps) from component_rows where component_type = 'theme_exposure'), 0),
        'cash_timing_contribution_bps', coalesce((select sum(contribution_bps) from component_rows where component_type = 'cash_timing'), 0),
        'attribution_component_count', (select count(*)::int from component_rows),
        'excluded_position_count', (select count(*)::int from coverage_exclusions),
        'excluded_weight', coalesce((select sum(weight) from coverage_exclusions), 0),
        'cash_weight', coalesce((select weight from component_rows where component_type = 'cash_timing' limit 1), 0)
    ),
    'outcomes',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'outcome_id', outcome_id,
                    'recommendation_id', recommendation_id,
                    'thesis_id', thesis_id,
                    'symbol', primary_symbol,
                    'instrument_id', instrument_id,
                    'recommendation', recommendation_action,
                    'horizon_days', horizon_days,
                    'absolute_return', absolute_return_pct,
                    'benchmark_return', benchmark_return_pct,
                    'alpha', alpha_pct,
                    'label', outcome_label,
                    'position_weight', position_weight,
                    'security_contribution_bps', coalesce(position_weight * alpha_pct * 10000, 0),
                    'source_run_id', source_run_id
                )
                order by alpha_pct desc nulls last, primary_symbol
            )
            from outcome_rows
        ),
        '[]'::json
    ),
    'attribution_components',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'component_id', attribution_component_id,
                    'component_type', component_type,
                    'label', coalesce(summary, component_key),
                    'symbol', primary_symbol,
                    'theme_key', theme_key,
                    'weight', weight,
                    'absolute_return', return_pct,
                    'benchmark_return', benchmark_return_pct,
                    'alpha', alpha_pct,
                    'contribution_bps', contribution_bps,
                    'interpretation', coalesce(summary, component_key)
                )
                order by attribution_component_id
            )
            from component_rows
        ),
        '[]'::json
    ),
    'coverage_exclusions',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'symbol', primary_symbol,
                    'instrument_id', instrument_id,
                    'weight', weight,
                    'reason', reason,
                    'required_action',
                    case
                        when reason = 'missing_outcome' then 'needs_outcome_review'
                        when reason = 'missing_weight' then 'needs_weight_review'
                        else 'needs_thesis_review'
                    end
                )
                order by primary_symbol
            )
            from coverage_exclusions
        ),
        '[]'::json
    ),
    'quality_gates',
    json_build_array(
        json_build_object(
            'gate', 'coverage_ready',
            'status', case when (select count(*) from coverage_exclusions) = 0 then 'passed' else 'blocked' end,
            'reason', case when (select count(*) from coverage_exclusions) = 0 then 'Portfolio positions have thesis/outcome coverage.' else 'Some positions are excluded from attribution coverage.' end
        ),
        json_build_object(
            'gate', 'outcome_run',
            'status', case when (select count(*) from outcome_rows) > 0 then 'passed' else 'blocked' end,
            'reason', case when (select count(*) from outcome_rows) > 0 then 'Recommendation outcomes exist for the measurement window.' else 'No recommendation outcomes exist for the measurement window.' end
        ),
        json_build_object(
            'gate', 'methodology_boundary',
            'status', 'passed',
            'reason', 'Security and theme components are explanatory lenses, not additive totals.'
        )
    )
)::text;"""


def render_frontend_recommendation_detail_state_sql(*, identifier: str) -> str:
    identifier_literal = sql_literal(identifier)
    return f"""-- frontend recommendation detail state lookup
with selected_recommendation as (
    select
        recommendation.recommendation_id,
        recommendation.instrument_id,
        instrument.primary_symbol,
        batch.as_of_date,
        batch.strategy_name,
        batch.horizon_type,
        batch.universe_version,
        recommendation.action,
        recommendation.total_score,
        recommendation.thesis_id
    from signal.recommendation recommendation
    join signal.recommendation_batch batch on batch.batch_id = recommendation.batch_id
    join ref.instrument instrument on instrument.instrument_id = recommendation.instrument_id
    where recommendation.recommendation_id::text = regexp_replace({identifier_literal}, '^recommendation-', '')
       or ('recommendation-' || recommendation.recommendation_id::text) = {identifier_literal}
       or (instrument.primary_symbol || '-' || batch.as_of_date::text) = {identifier_literal}
    order by batch.as_of_date desc, recommendation.recommendation_id desc
    limit 1
),
latest_outcome as (
    select outcome.*
    from performance.recommendation_outcome outcome
    join selected_recommendation recommendation
      on recommendation.recommendation_id = outcome.recommendation_id
    order by outcome.measurement_end_date desc, outcome.outcome_id desc
    limit 1
)
select json_build_object(
    'recommendation_id', (select recommendation_id from selected_recommendation),
    'symbol', (select primary_symbol from selected_recommendation),
    'instrument_id', (select instrument_id from selected_recommendation),
    'as_of_date', (select as_of_date from selected_recommendation),
    'strategy_name', (select strategy_name from selected_recommendation),
    'horizon_type', (select horizon_type from selected_recommendation),
    'recommendation', (select action from selected_recommendation),
    'score', (select total_score from selected_recommendation),
    'score_version', coalesce((select universe_version from selected_recommendation), 'bootstrap-v1'),
    'score_components',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'component', component.component_name,
                    'value', component.component_score,
                    'weight', component.component_weight,
                    'evidence_id',
                    case
                        when component.component_name = 'cycle_score'
                            then 'cycle-state-' || recommendation.primary_symbol || '-' || recommendation.as_of_date::text
                        when component.component_name in ('momentum_score', 'short_term_score', 'rank_score')
                            then 'market-feature-' || lower(recommendation.primary_symbol) || '-' || recommendation.as_of_date::text
                        else component.component_name
                    end
                )
                order by component.component_name
            )
            from signal.recommendation_score_component component
            join selected_recommendation recommendation
              on recommendation.recommendation_id = component.recommendation_id
        ),
        '[]'::json
    ),
    'linked_thesis_id', (select thesis_id from selected_recommendation),
    'outcome',
    json_build_object(
        'measurement_end_date', (select measurement_end_date from latest_outcome),
        'absolute_return', (select absolute_return_pct from latest_outcome),
        'benchmark_return', (select benchmark_return_pct from latest_outcome),
        'alpha', (select alpha_pct from latest_outcome),
        'label', coalesce((select outcome_label from latest_outcome), 'unmeasured')
    )
)::text;"""


def render_frontend_thesis_detail_state_sql(*, identifier: str) -> str:
    identifier_literal = sql_literal(identifier)
    return f"""-- frontend thesis detail state lookup
with selected_thesis as (
    select
        thesis.thesis_id,
        thesis.instrument_id,
        instrument.primary_symbol,
        thesis.status,
        thesis.thesis_type,
        thesis.title,
        thesis.summary,
        thesis.entry_conditions,
        thesis.invalidation_conditions,
        thesis.created_at,
        thesis.primary_node_id
    from signal.investment_thesis thesis
    join ref.instrument instrument on instrument.instrument_id = thesis.instrument_id
    where thesis.thesis_id::text = regexp_replace({identifier_literal}, '^thesis-', '')
       or ('thesis-' || thesis.thesis_id::text) = {identifier_literal}
       or (instrument.primary_symbol || '-bootstrap-v1') = {identifier_literal}
    order by thesis.created_at desc, thesis.thesis_id desc
    limit 1
),
latest_recommendation as (
    select recommendation.recommendation_id
    from signal.recommendation recommendation
    join signal.recommendation_batch batch on batch.batch_id = recommendation.batch_id
    join selected_thesis thesis on thesis.thesis_id = recommendation.thesis_id
    order by batch.as_of_date desc, recommendation.recommendation_id desc
    limit 1
),
latest_review as (
    select review.*
    from signal.thesis_review review
    join selected_thesis thesis on thesis.thesis_id = review.thesis_id
    order by review.review_date desc, review.review_id desc
    limit 1
),
event_evidence as (
    select
        event_row.event_id::text as evidence_id,
        event_row.event_type as evidence_type,
        event_row.title
    from selected_thesis thesis
    join event.event_instrument_impact instrument_impact on instrument_impact.instrument_id = thesis.instrument_id
    join event.event event_row on event_row.event_id = instrument_impact.event_id
    left join event.event_classification_impact classification_impact
      on classification_impact.event_id = event_row.event_id
     and classification_impact.node_id = thesis.primary_node_id
    order by event_row.event_at desc, event_row.event_id desc
    limit 5
),
outcome_evidence as (
    select
        outcome.outcome_id::text as evidence_id,
        'performance_outcome' as evidence_type,
        selected_thesis.primary_symbol || ' thesis outcome ' || outcome.success_grade as title
    from selected_thesis
    join performance.thesis_outcome outcome on outcome.thesis_id = selected_thesis.thesis_id
    order by outcome.measurement_end_date desc, outcome.outcome_id desc
    limit 3
),
evidence_rows as (
    select * from event_evidence
    union all
    select * from outcome_evidence
)
select json_build_object(
    'thesis_id', (select thesis_id from selected_thesis),
    'symbol', (select primary_symbol from selected_thesis),
    'instrument_id', (select instrument_id from selected_thesis),
    'status', (select status from selected_thesis),
    'thesis_version', coalesce((select thesis_type from selected_thesis), 'bootstrap-v1'),
    'created_from_recommendation_id', (select recommendation_id from latest_recommendation),
    'summary', coalesce((select summary from selected_thesis), ''),
    'core_claims',
    json_build_array(
        coalesce((select title from selected_thesis), ''),
        coalesce((select entry_conditions from selected_thesis), ''),
        coalesce((select summary from selected_thesis), '')
    ),
    'invalidation_conditions',
    json_build_array(
        json_build_object(
            'condition', coalesce((select invalidation_conditions from selected_thesis), 'not_defined'),
            'current_status', 'not_triggered'
        )
    ),
    'latest_review',
    json_build_object(
        'review_id', (select review_id from latest_review),
        'action', coalesce((select action from latest_review), 'unreviewed'),
        'risk_level',
        case
            when (select action from latest_review) in ('exit', 'reduce') then 'high'
            when (select action from latest_review) = 'watch' then 'medium'
            when (select action from latest_review) = 'keep' then 'low'
            else 'unknown'
        end,
        'reviewed_at', (select review_date from latest_review)
    ),
    'evidence',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'evidence_id', evidence_id,
                    'type', evidence_type,
                    'title', title
                )
                order by evidence_type, evidence_id
            )
            from evidence_rows
        ),
        '[]'::json
    )
)::text;"""


def render_frontend_ai_evidence_detail_state_sql(*, identifier: str) -> str:
    identifier_literal = sql_literal(identifier)
    return f"""-- frontend ai evidence detail state lookup
with selected_artifact as (
    select artifact.*
    from ai.extraction_artifact artifact
    left join ingest.source_document document on document.document_id = artifact.document_id
    left join event.event_document_link document_link
      on document_link.document_id = artifact.document_id
     and document_link.link_type = 'source'
    left join event.event event_row
      on event_row.event_id = coalesce(artifact.event_id, document_link.event_id)
    where artifact.artifact_id::text = regexp_replace({identifier_literal}, '^ai-evidence-', '')
       or ('ai-evidence-' || artifact.artifact_id::text) = {identifier_literal}
       or event_row.dedupe_key = {identifier_literal}
       or document.external_document_id = {identifier_literal}
    order by artifact.artifact_id desc
    limit 1
),
selected_event_candidates as (
    select event_row.*
    from event.event event_row
    join selected_artifact artifact on artifact.event_id = event_row.event_id
    union all
    select event_row.*
    from selected_artifact artifact
    join event.event_document_link document_link
      on document_link.document_id = artifact.document_id
     and document_link.link_type = 'source'
    join event.event event_row on event_row.event_id = document_link.event_id
    where artifact.event_id is null
),
selected_event as (
    select *
    from selected_event_candidates
    order by event_at desc, event_id desc
    limit 1
),
selected_document as (
    select document.*
    from ingest.source_document document
    join selected_artifact artifact on artifact.document_id = document.document_id
),
instrument_row as (
    select instrument.instrument_id, instrument.primary_symbol
    from selected_event event_row
    join event.event_instrument_impact impact on impact.event_id = event_row.event_id
    join ref.instrument instrument on instrument.instrument_id = impact.instrument_id
    order by impact.impact_strength desc nulls last, instrument.primary_symbol
    limit 1
),
classification_row as (
    select
        node.code as theme_key,
        node.name as theme_name,
        impact.impact_direction,
        impact.impact_strength as impact_score
    from selected_event event_row
    join event.event_classification_impact impact on impact.event_id = event_row.event_id
    join ref.classification_node node on node.node_id = impact.node_id
    where node.taxonomy_family = 'internal_theme'
    order by impact.impact_strength desc nulls last, node.code
    limit 1
),
invocation_row as (
    select invocation.*, template.template_name, template.template_version
    from ai.model_invocation invocation
    join selected_artifact artifact on artifact.invocation_id = invocation.invocation_id
    left join ai.prompt_template template on template.template_id = invocation.prompt_template_id
),
chunk_rows as (
    select chunk.*
    from ai.document_chunk chunk
    join selected_document document on document.document_id = chunk.document_id
    order by chunk.chunk_index
    limit 10
)
select json_build_object(
    'evidence_id', (select artifact_id from selected_artifact),
    'title',
    coalesce(
        (select title from selected_event),
        (select output_json #>> '{{event,title}}' from selected_artifact),
        (select artifact_type from selected_artifact),
        ''
    ),
    'evidence_type',
    coalesce(
        (select event_type from selected_event),
        (select output_json #>> '{{event,event_type}}' from selected_artifact),
        (select artifact_type from selected_artifact),
        'source_document_event'
    ),
    'event_at', coalesce((select event_at::text from selected_event), (select output_json #>> '{{event,event_at}}' from selected_artifact)),
    'instrument',
    json_build_object(
        'symbol', (select primary_symbol from instrument_row),
        'instrument_id', (select instrument_id from instrument_row)
    ),
    'source_document_id', coalesce((select external_document_id from selected_document), (select document_id::text from selected_document)),
    'classification',
    json_build_object(
        'theme_key', (select theme_key from classification_row),
        'theme_name', (select theme_name from classification_row),
        'impact_direction', (select impact_direction from classification_row),
        'impact_score', (select impact_score from classification_row)
    ),
    'extraction_run',
    json_build_object(
        'run_id', (select run_id from invocation_row),
        'status', (select status from invocation_row),
        'provider', (select provider from invocation_row),
        'model_id', (select model_name from invocation_row),
        'prompt_version', coalesce((select template_version from invocation_row), (select template_name from invocation_row)),
        'finished_at', (select created_at from invocation_row),
        'input_tokens', (select input_token_count from invocation_row),
        'output_tokens', (select output_token_count from invocation_row),
        'estimated_cost_usd', (select estimated_cost_usd from invocation_row),
        'quality_gate', 'human_review_required'
    ),
    'extracted_fields', coalesce((select output_json -> 'extracted_fields' from selected_artifact), '[]'::jsonb),
    'source_chunks',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'chunk_id', chunk_id,
                    'section', coalesce(chunk_metadata ->> 'section', 'source'),
                    'locator', coalesce(chunk_metadata ->> 'locator', 'document chunk ' || chunk_index::text),
                    'summary', text_preview,
                    'relevance', coalesce(chunk_metadata ->> 'relevance', 'supporting_context')
                )
                order by chunk_index
            )
            from chunk_rows
        ),
        '[]'::json
    )
)::text;"""


def render_frontend_source_document_detail_state_sql(*, identifier: str) -> str:
    identifier_literal = sql_literal(identifier)
    return f"""-- frontend source document detail state lookup
with selected_document as (
    select document.*, data_source.source_name, data_source.source_kind
    from ingest.source_document document
    join ingest.data_source data_source on data_source.data_source_id = document.data_source_id
    where document.document_id::text = regexp_replace({identifier_literal}, '^source-document-', '')
       or ('source-document-' || document.document_id::text) = {identifier_literal}
       or document.external_document_id = {identifier_literal}
    order by document.document_id desc
    limit 1
),
retrieval_run as (
    select run.*
    from ops.pipeline_run run
    join selected_document document on document.ingested_by_run_id = run.run_id
),
instrument_row as (
    select instrument.instrument_id, instrument.primary_symbol
    from selected_document document
    join event.event_document_link link on link.document_id = document.document_id
    join event.event_instrument_impact impact on impact.event_id = link.event_id
    join ref.instrument instrument on instrument.instrument_id = impact.instrument_id
    order by impact.impact_strength desc nulls last, instrument.primary_symbol
    limit 1
),
chunk_rows as (
    select chunk.*
    from ai.document_chunk chunk
    join selected_document document on document.document_id = chunk.document_id
    order by chunk.chunk_index
    limit 10
),
linked_evidence as (
    select
        artifact.artifact_id,
        coalesce(event_row.event_type, artifact.artifact_type) as evidence_type,
        coalesce(event_row.title, artifact.artifact_type) as title
    from selected_document document
    join ai.extraction_artifact artifact on artifact.document_id = document.document_id
    left join event.event event_row on event_row.event_id = artifact.event_id
    order by artifact.artifact_id desc
    limit 10
)
select json_build_object(
    'document_id', coalesce((select external_document_id from selected_document), (select document_id::text from selected_document)),
    'title', (select title from selected_document),
    'source_type', (select document_type from selected_document),
    'publisher', (select source_name from selected_document),
    'symbol', (select primary_symbol from instrument_row),
    'cik', '',
    'form_type', (select document_type from selected_document),
    'period_end', (select published_at::date from selected_document),
    'filed_at', (select published_at from selected_document),
    'accession_id', coalesce((select external_document_id from selected_document), ''),
    'storage_uri', coalesce((select raw_storage_uri from selected_document), ''),
    'checksum', coalesce((select checksum from selected_document), ''),
    'retrieval',
    json_build_object(
        'source_run_id', (select run_id from retrieval_run),
        'fetched_at', (select ended_at from retrieval_run),
        'parser_version', coalesce((select code_version from retrieval_run), 'unknown')
    ),
    'excerpts',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'chunk_id', chunk_id,
                    'section', coalesce(chunk_metadata ->> 'section', 'source'),
                    'locator', coalesce(chunk_metadata ->> 'locator', 'document chunk ' || chunk_index::text),
                    'summary', text_preview
                )
                order by chunk_index
            )
            from chunk_rows
        ),
        '[]'::json
    ),
    'linked_evidence',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'evidence_id', artifact_id,
                    'evidence_type', evidence_type,
                    'title', title
                )
                order by artifact_id desc
            )
            from linked_evidence
        ),
        '[]'::json
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


def _event_list_sql_filters(*, theme_key: str | None, symbol: str | None, event_type: str) -> str:
    lines: list[str] = []
    if theme_key:
        lines.append(f"      and theme.code = {sql_literal(theme_key)}")
    if symbol:
        lines.append(f"      and upper(instrument.primary_symbol) = {sql_literal(symbol.upper())}")
    if event_type and event_type != "all":
        lines.append(f"      and event_row.event_type = {sql_literal(event_type)}")
    return "\n".join(lines)


def _build_event_payload(event: dict[str, Any]) -> dict[str, Any]:
    symbol = str(event.get("symbol") or "UNKNOWN").upper()
    source_document_id = event.get("source_document_id") or event.get("raw_source_document_id")
    ai_evidence_id = event.get("ai_evidence_id")
    return {
        "event_id": _opaque_id("event", event.get("event_id"), "unknown"),
        "title": str(event.get("title") or ""),
        "event_type": str(event.get("event_type") or "unknown"),
        "event_at": _timestamp(event.get("event_at")),
        "symbol": symbol,
        "instrument_id": _opaque_id("instrument", event.get("instrument_id"), symbol.lower()),
        "theme_key": str(event.get("theme_key") or "UNCLASSIFIED"),
        "theme_name": str(event.get("theme_name") or "Unclassified"),
        "impact_direction": str(event.get("impact_direction") or "unknown"),
        "impact_score": _number(event.get("impact_score")),
        "source_document_id": _opaque_id("source-document", source_document_id, None)
        if source_document_id is not None
        else None,
        "ai_evidence_id": _opaque_id("ai-evidence", ai_evidence_id, None) if ai_evidence_id is not None else None,
        "quality_gate": str(event.get("quality_gate") or "deterministic_review_required"),
    }


def _build_cycle_state_item_payload(item: dict[str, Any]) -> dict[str, Any]:
    features = _as_dict(item.get("features"))
    raw_symbols = item.get("top_symbols")
    top_symbols = [str(symbol).upper() for symbol in raw_symbols if symbol] if isinstance(raw_symbols, list) else []
    return {
        "theme_key": str(item.get("theme_key") or "UNCLASSIFIED"),
        "theme_name": str(item.get("theme_name") or "Unclassified"),
        "state": str(item.get("state") or item.get("cycle_state") or "unknown"),
        "previous_state": str(item.get("previous_state") or "unknown"),
        "confidence": _number(item.get("confidence") or item.get("cycle_score")),
        "instrument_count": int(item.get("instrument_count") or len(top_symbols)),
        "top_symbols": top_symbols,
        "features": {
            "event_intensity": _number(features.get("event_intensity")),
            "price_momentum": _number(features.get("price_momentum")),
            "fundamental_quality": _number(features.get("fundamental_quality")),
        },
    }


def _build_cycle_history_payload(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "as_of_date": str(item.get("as_of_date") or ""),
        "state": str(item.get("state") or item.get("cycle_state") or "unknown"),
        "confidence": _number(item.get("confidence") or item.get("cycle_score")),
    }


def _build_theme_linked_instrument_payload(item: dict[str, Any]) -> dict[str, Any]:
    symbol = str(item.get("symbol") or "UNKNOWN").upper()
    return {
        "symbol": symbol,
        "instrument_id": _opaque_id("instrument", item.get("instrument_id"), symbol.lower()),
        "membership_strength": _number(item.get("membership_strength")),
        "active_thesis_id": _opaque_id("thesis", item.get("active_thesis_id"), None)
        if item.get("active_thesis_id") is not None
        else None,
        "latest_recommendation_id": _opaque_id("recommendation", item.get("latest_recommendation_id"), None)
        if item.get("latest_recommendation_id") is not None
        else None,
    }


def _build_theme_supporting_event_payload(event: dict[str, Any]) -> dict[str, Any]:
    symbol = str(event.get("symbol") or "UNKNOWN").upper()
    source_document_id = event.get("source_document_id") or event.get("raw_source_document_id")
    ai_evidence_id = event.get("ai_evidence_id")
    return {
        "event_id": _opaque_id("event", event.get("event_id"), "unknown"),
        "title": str(event.get("title") or ""),
        "event_at": _timestamp(event.get("event_at")),
        "symbol": symbol,
        "impact_direction": str(event.get("impact_direction") or "unknown"),
        "impact_score": _number(event.get("impact_score")),
        "ai_evidence_id": _opaque_id("ai-evidence", ai_evidence_id, None) if ai_evidence_id is not None else None,
        "source_document_id": _opaque_id("source-document", source_document_id, None)
        if source_document_id is not None
        else None,
    }


def _build_performance_outcome_payload(outcome: dict[str, Any]) -> dict[str, Any]:
    symbol = str(outcome.get("symbol") or "UNKNOWN").upper()
    return {
        "outcome_id": _opaque_id("outcome", outcome.get("outcome_id"), "unknown"),
        "recommendation_id": _opaque_id("recommendation", outcome.get("recommendation_id"), None)
        if outcome.get("recommendation_id") is not None
        else None,
        "thesis_id": _opaque_id("thesis", outcome.get("thesis_id"), None) if outcome.get("thesis_id") is not None else None,
        "symbol": symbol,
        "instrument_id": _opaque_id("instrument", outcome.get("instrument_id"), symbol.lower()),
        "recommendation": str(outcome.get("recommendation") or outcome.get("recommendation_action") or "monitor"),
        "horizon_days": int(outcome.get("horizon_days") or 0),
        "absolute_return": _number(outcome.get("absolute_return")),
        "benchmark_return": _number(outcome.get("benchmark_return")),
        "alpha": _number(outcome.get("alpha")),
        "label": str(outcome.get("label") or outcome.get("outcome_label") or "unknown"),
        "position_weight": _number(outcome.get("position_weight")),
        "security_contribution_bps": _number(outcome.get("security_contribution_bps")),
        "source_run_id": _opaque_id("pipeline-run", outcome.get("source_run_id"), None)
        if outcome.get("source_run_id") is not None
        else None,
    }


def _build_attribution_component_payload(component: dict[str, Any]) -> dict[str, Any]:
    symbol = component.get("symbol")
    return {
        "component_id": _opaque_id("attribution-component", component.get("component_id"), "unknown"),
        "component_type": str(component.get("component_type") or "unknown"),
        "label": str(component.get("label") or ""),
        "symbol": str(symbol).upper() if symbol else None,
        "theme_key": str(component.get("theme_key")) if component.get("theme_key") is not None else None,
        "weight": _number(component.get("weight")),
        "absolute_return": _number(component.get("absolute_return")),
        "benchmark_return": _number(component.get("benchmark_return")),
        "alpha": _number(component.get("alpha")),
        "contribution_bps": _number(component.get("contribution_bps")),
        "interpretation": str(component.get("interpretation") or ""),
    }


def _build_coverage_exclusion_payload(exclusion: dict[str, Any]) -> dict[str, Any]:
    symbol = str(exclusion.get("symbol") or "UNKNOWN").upper()
    reason = str(exclusion.get("reason") or "missing_thesis")
    return {
        "symbol": symbol,
        "instrument_id": _opaque_id("instrument", exclusion.get("instrument_id"), symbol.lower()),
        "weight": _number(exclusion.get("weight")),
        "reason": reason,
        "required_action": str(exclusion.get("required_action") or _coverage_action(reason)),
    }


def _build_quality_gate_payload(gate: dict[str, Any]) -> dict[str, Any]:
    return {
        "gate": str(gate.get("gate") or "unknown"),
        "status": str(gate.get("status") or "unknown"),
        "reason": str(gate.get("reason") or ""),
    }


def _build_performance_summary(
    summary: dict[str, Any],
    outcomes: list[dict[str, Any]],
    attribution_components: list[dict[str, Any]],
    coverage_exclusions: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "measured_recommendation_count": int(summary.get("measured_recommendation_count") or len(outcomes)),
        "measured_thesis_count": int(summary.get("measured_thesis_count") or 0),
        "outperform_count": int(summary.get("outperform_count") or 0),
        "underperform_count": int(summary.get("underperform_count") or 0),
        "hit_rate": _number(summary.get("hit_rate")),
        "average_alpha": _number(summary.get("average_alpha")),
        "security_lens_contribution_bps": _number(summary.get("security_lens_contribution_bps")),
        "theme_lens_contribution_bps": _number(summary.get("theme_lens_contribution_bps")),
        "cash_timing_contribution_bps": _number(summary.get("cash_timing_contribution_bps")),
        "attribution_component_count": int(summary.get("attribution_component_count") or len(attribution_components)),
        "excluded_position_count": int(summary.get("excluded_position_count") or len(coverage_exclusions)),
        "excluded_weight": _number(summary.get("excluded_weight")),
        "cash_weight": _number(summary.get("cash_weight")),
    }


def _event_list_links(events: list[dict[str, Any]], *, as_of_date: date) -> dict[str, str]:
    first_event = events[0] if events else {}
    links = {"theme_detail": f"/api/themes/{first_event.get('theme_key', 'UNCLASSIFIED')}?asOfDate={as_of_date}"}
    if first_event.get("ai_evidence_id"):
        links["ai_evidence"] = f"/api/ai-evidence/{first_event['ai_evidence_id']}"
    if first_event.get("source_document_id"):
        links["source_document"] = f"/api/source-documents/{first_event['source_document_id']}"
    return links


def _cycle_state_list_links(cycle_states: list[dict[str, Any]], *, as_of_date: date) -> dict[str, str]:
    first_cycle = cycle_states[0] if cycle_states else {}
    return {
        "theme_detail": f"/api/themes/{first_cycle.get('theme_key', 'UNCLASSIFIED')}?asOfDate={as_of_date}",
        "recommendations": f"/api/recommendations?batchDate={as_of_date}",
    }


def _theme_detail_links(
    *,
    theme_key: str,
    as_of_date: date,
    linked_instruments: list[dict[str, Any]],
    supporting_events: list[dict[str, Any]],
) -> dict[str, str]:
    links = {"events": f"/api/events?asOfDate={as_of_date}"}
    first_event = supporting_events[0] if supporting_events else {}
    first_instrument = linked_instruments[0] if linked_instruments else {}
    if first_event.get("ai_evidence_id"):
        links["ai_evidence"] = f"/api/ai-evidence/{first_event['ai_evidence_id']}"
    if first_instrument.get("latest_recommendation_id"):
        links["recommendation"] = f"/api/recommendations/{first_instrument['latest_recommendation_id']}"
    if first_instrument.get("active_thesis_id"):
        links["thesis"] = f"/api/theses/{first_instrument['active_thesis_id']}"
    if not first_event.get("ai_evidence_id"):
        links["theme"] = f"/api/themes/{theme_key}?asOfDate={as_of_date}"
    return links


def _performance_links(
    *,
    portfolio_name: str,
    snapshot_date: str,
    outcomes: list[dict[str, Any]],
    attribution_components: list[dict[str, Any]],
) -> dict[str, str]:
    encoded_portfolio_name = quote(portfolio_name, safe="")
    links = {
        "coverage": f"/api/portfolio/{encoded_portfolio_name}/coverage?asOfDate={snapshot_date}",
        "dashboard": "/api/dashboard/today",
    }
    first_outcome = outcomes[0] if outcomes else {}
    first_theme_component = next((item for item in attribution_components if item.get("theme_key")), {})
    if first_outcome.get("recommendation_id"):
        links["recommendation"] = f"/api/recommendations/{first_outcome['recommendation_id']}"
    if first_outcome.get("thesis_id"):
        links["thesis"] = f"/api/theses/{first_outcome['thesis_id']}"
    if first_theme_component.get("theme_key") and snapshot_date:
        links["theme"] = f"/api/themes/{first_theme_component['theme_key']}?asOfDate={snapshot_date}"
    return links


def _build_recommendation_score_component_payload(component: dict[str, Any]) -> dict[str, Any]:
    component_name = str(component.get("component") or component.get("component_name") or "unknown")
    return {
        "component": component_name,
        "value": _number(component.get("value") or component.get("component_score")),
        "weight": _number(component.get("weight") or component.get("component_weight")),
        "evidence_id": str(component.get("evidence_id") or component.get("explanation") or component_name),
    }


def _build_thesis_evidence_payload(evidence: dict[str, Any]) -> dict[str, Any]:
    evidence_type = str(evidence.get("type") or evidence.get("evidence_type") or "evidence")
    raw_id = evidence.get("evidence_id")
    if evidence_type == "performance_outcome":
        evidence_id = _opaque_id("performance-outcome", raw_id, "unknown")
    else:
        evidence_id = _opaque_id("event", raw_id, "unknown")
    return {
        "evidence_id": evidence_id,
        "type": evidence_type,
        "title": str(evidence.get("title") or ""),
    }


def _build_invalidation_condition_payload(condition: dict[str, Any]) -> dict[str, str]:
    return {
        "condition": str(condition.get("condition") or "not_defined"),
        "current_status": str(condition.get("current_status") or "unknown"),
    }


def _build_extracted_field_payload(field: dict[str, Any]) -> dict[str, Any]:
    return {
        "field": str(field.get("field") or "unknown"),
        "value": str(field.get("value") or ""),
        "confidence": _number(field.get("confidence")),
        "source_chunk_id": _opaque_id("chunk", field.get("source_chunk_id"), None)
        if field.get("source_chunk_id") is not None
        else None,
    }


def _build_source_chunk_payload(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "chunk_id": _opaque_id("chunk", chunk.get("chunk_id"), "unknown"),
        "section": str(chunk.get("section") or "source"),
        "locator": str(chunk.get("locator") or ""),
        "summary": str(chunk.get("summary") or ""),
        **({"relevance": str(chunk.get("relevance"))} if chunk.get("relevance") is not None else {}),
    }


def _build_linked_evidence_payload(evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "evidence_id": _opaque_id("ai-evidence", evidence.get("evidence_id"), "unknown"),
        "evidence_type": str(evidence.get("evidence_type") or "unknown"),
        "title": str(evidence.get("title") or ""),
    }


def _recommendation_detail_id(state: dict[str, Any], identifier: str) -> str:
    if identifier.startswith("recommendation-") or not state.get("recommendation_id"):
        return identifier
    return _opaque_id("recommendation", state.get("recommendation_id"), identifier)


def _thesis_detail_id(state: dict[str, Any], identifier: str) -> str:
    if identifier.startswith("thesis-") or not state.get("thesis_id"):
        return identifier
    return _opaque_id("thesis", state.get("thesis_id"), identifier)


def _ai_evidence_detail_id(state: dict[str, Any], identifier: str) -> str:
    if identifier.startswith("ai-evidence-") or not state.get("evidence_id"):
        return identifier
    return _opaque_id("ai-evidence", state.get("evidence_id"), identifier)


def _source_document_detail_id(state: dict[str, Any], identifier: str) -> str:
    return _source_document_detail_id_from_raw(state.get("document_id") or identifier)


def _source_document_detail_id_from_raw(raw_value: object) -> str:
    if raw_value is None:
        return "source-document-unknown"
    raw_text = str(raw_value)
    if raw_text.startswith("source-document-"):
        return raw_text
    return raw_text if not raw_text.isdigit() else f"source-document-{raw_text}"


def _recommendation_detail_links(state: dict[str, Any], *, identifier: str) -> dict[str, str]:
    links = {"cycle_state": f"/api/cycles?asOfDate={state.get('as_of_date') or ''}"}
    if state.get("linked_thesis_id") is not None:
        links["thesis"] = f"/api/theses/{_opaque_id('thesis', state.get('linked_thesis_id'), None)}"
    source_event_id = _first_score_component_event_id(state)
    if source_event_id:
        links["source_event"] = f"/api/events/{source_event_id}"
    if "thesis" not in links:
        links["recommendation"] = f"/api/recommendations/{identifier}"
    return links


def _thesis_detail_links(state: dict[str, Any], *, identifier: str) -> dict[str, str]:
    latest_review = _as_dict(state.get("latest_review"))
    reviewed_at = str(latest_review.get("reviewed_at") or "")
    coverage_path = "/api/portfolio/Long%20Term%20Paper/coverage"
    if reviewed_at:
        coverage_path = f"{coverage_path}?asOfDate={reviewed_at[:10]}"
    links = {"portfolio_coverage": coverage_path}
    recommendation_id = state.get("created_from_recommendation_id")
    if recommendation_id is not None:
        links["recommendation"] = f"/api/recommendations/{_opaque_id('recommendation', recommendation_id, None)}"
    else:
        links["thesis"] = f"/api/theses/{identifier}"
    return links


def _ai_evidence_links(state: dict[str, Any], *, identifier: str) -> dict[str, str]:
    links = {"ai_evidence": f"/api/ai-evidence/{identifier}"}
    source_document_id = state.get("source_document_id")
    if source_document_id is not None:
        links["source_document"] = f"/api/source-documents/{_source_document_detail_id_from_raw(source_document_id)}"
    return links


def _source_document_links(state: dict[str, Any], *, identifier: str) -> dict[str, str]:
    links = {"source_document": f"/api/source-documents/{identifier}"}
    linked_evidence = _as_list(state.get("linked_evidence"))
    if linked_evidence:
        links["ai_evidence"] = f"/api/ai-evidence/{_opaque_id('ai-evidence', linked_evidence[0].get('evidence_id'), 'unknown')}"
    return links


def _first_score_component_event_id(state: dict[str, Any]) -> str | None:
    for component in _as_list(state.get("score_components")):
        evidence_id = component.get("evidence_id")
        evidence_text = str(evidence_id or "")
        if evidence_text.startswith(("event-", "sec-event-")):
            return evidence_text
        if evidence_text.isdigit():
            return _opaque_id("event", evidence_text, None)
    return None


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


def _parse_theme_key(path: str) -> str:
    prefix = "/api/themes/"
    if not path.startswith(prefix):
        raise FrontendLiveUnsupportedPathError(f"Invalid theme detail path: {path}")
    encoded_key = path[len(prefix) :]
    if not encoded_key:
        raise FrontendLiveUnsupportedPathError("Theme detail path is missing theme key.")
    return unquote(encoded_key)


def _parse_performance_portfolio_name(path: str) -> str:
    prefix = "/api/performance/"
    suffix = "/outcomes"
    if not path.startswith(prefix) or not path.endswith(suffix):
        raise FrontendLiveUnsupportedPathError(f"Invalid performance outcomes path: {path}")
    encoded_name = path[len(prefix) : -len(suffix)]
    if not encoded_name:
        raise FrontendLiveUnsupportedPathError("Performance outcomes path is missing portfolio name.")
    return unquote(encoded_name)


def _parse_detail_identifier(path: str, prefix: str) -> str:
    if not path.startswith(prefix):
        raise FrontendLiveUnsupportedPathError(f"Invalid detail path: {path}")
    encoded_identifier = path[len(prefix) :]
    if not encoded_identifier:
        raise FrontendLiveUnsupportedPathError("Detail path is missing identifier.")
    return unquote(encoded_identifier)


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
