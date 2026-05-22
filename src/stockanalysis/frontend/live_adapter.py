from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qs, quote, unquote, urlsplit

from stockanalysis.ai.evidence_graph import render_instrument_evidence_neighborhood_sql
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.cadence import render_data_operations_expected_jobs_sql_values
from stockanalysis.operations.market_price_free_backfill import (
    MARKET_PRICE_BUDGET_LEDGER_PATH_ENV,
    MARKET_PRICE_PROVIDER_ENV,
    load_market_price_provider_budget_status,
)
from stockanalysis.operations.manual_local_ingest_smoke import load_manual_local_ingest_smoke_visibility_report
from stockanalysis.operations.local_ingest_worker import load_local_ingest_worker_visibility_report
from stockanalysis.frontend.pagination import (
    MAX_PAGE_LIMIT,
    apply_frontend_pagination,
    apply_frontend_sql_pagination,
    frontend_sql_page_window,
)
from stockanalysis.performance.coverage import load_portfolio_outcome_coverage_report
from stockanalysis.signal.portfolio_remediation_ticket import load_portfolio_remediation_ticket_report


CONTRACT_VERSION = "frontend-api-v0.1"
DEFAULT_PORTFOLIO_NAME = "Long Term Paper"
DEFAULT_STRATEGY_NAME = "long_term_core"
DEFAULT_COVERAGE_HORIZON_DAYS = 31
NO_PORTFOLIO_POSITIONS_MESSAGE = "No portfolio positions matched the requested coverage report identity."
SCHEDULER_APPROVAL_GATE_REPORT_ENV = "STOCKANALYSIS_DATA_OPERATIONS_SCHEDULER_APPROVAL_GATE_REPORT"
OPERATING_DATA_PROFILE_SCHEDULER_STATUS_REPORT_ENV = "STOCKANALYSIS_OPERATING_DATA_PROFILE_SCHEDULER_STATUS_REPORT"
DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[3]
_STORY_GROUP_STOP_WORDS = frozenset(
    {
        "about",
        "after",
        "again",
        "against",
        "also",
        "and",
        "are",
        "at",
        "built",
        "but",
        "ceo",
        "for",
        "from",
        "has",
        "how",
        "inc",
        "into",
        "its",
        "new",
        "news",
        "not",
        "now",
        "of",
        "on",
        "over",
        "said",
        "says",
        "the",
        "this",
        "to",
        "up",
        "with",
        "your",
    }
)


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
        return apply_frontend_pagination(
            api_path,
            build_live_dashboard_response(
                config=runtime_config,
                executor=executor,
                generated_at=generated_at_text,
            ),
        )
    if parsed.path == "/api/data-health":
        return apply_frontend_pagination(
            api_path,
            build_live_data_health_response(
                config=runtime_config,
                executor=executor,
                generated_at=generated_at_text,
            ),
        )
    if parsed.path == "/api/stocks":
        return apply_frontend_sql_pagination(
            api_path,
            build_live_stock_list_response(
                parsed,
                api_path=api_path,
                config=runtime_config,
                executor=executor,
                generated_at=generated_at_text,
            ),
        )
    if parsed.path.startswith("/api/stocks/"):
        return apply_frontend_pagination(
            api_path,
            build_live_stock_detail_response(
                parsed,
                config=runtime_config,
                executor=executor,
                generated_at=generated_at_text,
            ),
        )
    if parsed.path == "/api/paper-trading/preview":
        return apply_frontend_sql_pagination(
            api_path,
            build_live_paper_trading_preview_response(
                parsed,
                api_path=api_path,
                config=runtime_config,
                executor=executor,
                generated_at=generated_at_text,
            ),
        )
    if parsed.path == "/api/trading/readiness":
        return apply_frontend_pagination(
            api_path,
            build_live_trading_readiness_response(
                config=runtime_config,
                executor=executor,
                generated_at=generated_at_text,
            ),
        )
    if parsed.path == "/api/cycles":
        return apply_frontend_sql_pagination(
            api_path,
            build_live_cycle_state_list_response(
                parsed,
                api_path=api_path,
                config=runtime_config,
                executor=executor,
                generated_at=generated_at_text,
            ),
        )
    if parsed.path == "/api/recommendations":
        return apply_frontend_sql_pagination(
            api_path,
            build_live_recommendation_list_response(
                parsed,
                api_path=api_path,
                config=runtime_config,
                executor=executor,
                generated_at=generated_at_text,
            ),
        )
    if parsed.path == "/api/events":
        return apply_frontend_sql_pagination(
            api_path,
            build_live_event_list_response(
                parsed,
                api_path=api_path,
                config=runtime_config,
                executor=executor,
                generated_at=generated_at_text,
            ),
        )
    if parsed.path == "/api/ai/news-clusters":
        return apply_frontend_sql_pagination(
            api_path,
            build_live_ai_news_cluster_list_response(
                parsed,
                api_path=api_path,
                config=runtime_config,
                executor=executor,
                generated_at=generated_at_text,
            ),
        )
    if parsed.path.startswith("/api/themes/"):
        return apply_frontend_pagination(
            api_path,
            build_live_theme_detail_response(
                parsed,
                config=runtime_config,
                executor=executor,
                generated_at=generated_at_text,
            ),
        )
    if parsed.path.startswith("/api/performance/") and parsed.path.endswith("/outcomes"):
        return apply_frontend_sql_pagination(
            api_path,
            build_live_performance_outcomes_response(
                parsed,
                api_path=api_path,
                config=runtime_config,
                executor=executor,
                generated_at=generated_at_text,
            ),
        )
    if parsed.path.startswith("/api/recommendations/"):
        return apply_frontend_pagination(
            api_path,
            build_live_recommendation_detail_response(
                parsed,
                config=runtime_config,
                executor=executor,
                generated_at=generated_at_text,
            ),
        )
    if parsed.path.startswith("/api/theses/"):
        return apply_frontend_pagination(
            api_path,
            build_live_thesis_detail_response(
                parsed,
                config=runtime_config,
                executor=executor,
                generated_at=generated_at_text,
            ),
        )
    if parsed.path.startswith("/api/ai/evidence-neighborhoods/"):
        return apply_frontend_pagination(
            api_path,
            build_live_ai_evidence_neighborhood_response(
                parsed,
                config=runtime_config,
                executor=executor,
                generated_at=generated_at_text,
            ),
        )
    if parsed.path.startswith("/api/ai-evidence/"):
        return apply_frontend_pagination(
            api_path,
            build_live_ai_evidence_detail_response(
                parsed,
                config=runtime_config,
                executor=executor,
                generated_at=generated_at_text,
            ),
        )
    if parsed.path.startswith("/api/source-documents/"):
        return apply_frontend_pagination(
            api_path,
            build_live_source_document_detail_response(
                parsed,
                config=runtime_config,
                executor=executor,
                generated_at=generated_at_text,
            ),
        )
    if parsed.path == "/api/remediation-tickets":
        return apply_frontend_sql_pagination(
            api_path,
            build_live_remediation_tickets_response(
                parsed,
                api_path=api_path,
                config=runtime_config,
                executor=executor,
                generated_at=generated_at_text,
            ),
        )
    if parsed.path.startswith("/api/portfolio/") and parsed.path.endswith("/coverage"):
        return apply_frontend_sql_pagination(
            api_path,
            build_live_portfolio_coverage_response(
                parsed,
                api_path=api_path,
                config=runtime_config,
                executor=executor,
                generated_at=generated_at_text,
            ),
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
    provider_budget = _load_provider_budget_for_data_health(state)
    profile_scheduler_status = _load_operating_data_profile_scheduler_status_for_data_health()
    scheduler_activation = _load_scheduler_activation_for_data_health()
    if profile_scheduler_status["install_status"] == "installed":
        scheduler_activation = _installed_profile_scheduler_activation(profile_scheduler_status)
    manual_local_ingest_smoke = load_manual_local_ingest_smoke_visibility_report(
        env=os.environ,
        repo_root=DEFAULT_REPO_ROOT,
    )
    local_ingest_worker = load_local_ingest_worker_visibility_report(
        env=os.environ,
        repo_root=DEFAULT_REPO_ROOT,
    )
    if scheduler_activation["status"] == "pending_manual_approval":
        gate = "scheduler_activation_manual_approval"
        if gate not in open_gates:
            open_gates.append(gate)

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "data": {
            "overall_status": str(state.get("overall_status") or "unknown"),
            "as_of_date": str(state.get("as_of_date") or ""),
            "pipeline_runs": pipeline_runs,
            "scheduler": {
                "install_status": profile_scheduler_status["install_status"],
                "runtime_env_readiness": "template_rendered_placeholder_pending",
                "holiday_skip_mode": "explicit_skip_dates",
                "latest_artifact_root": str(state.get("latest_artifact_root") or ""),
                "activation": scheduler_activation,
                "profile_scheduler": profile_scheduler_status,
            },
            "freshness": freshness,
            "provider_budget": provider_budget,
            "manual_local_ingest_smoke": manual_local_ingest_smoke,
            "local_ingest_worker": local_ingest_worker,
            "open_gates": open_gates,
        },
        "links": {
            "scheduler_env_readiness": "/settings/scheduler",
            "dashboard": "/api/dashboard/today",
        },
    }


def build_live_stock_list_response(
    parsed: ParsedApiPath,
    *,
    api_path: str,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    as_of_date = _parse_optional_date(parsed.query, "asOfDate")
    page_limit, page_offset = frontend_sql_page_window(api_path)
    state = load_frontend_stock_list_state(
        config=config,
        executor=executor,
        as_of_date=as_of_date,
        page_limit=page_limit,
        page_offset=page_offset,
    )
    stocks = [_build_stock_list_item_payload(item) for item in _as_list(state.get("stocks"))]
    summary = _as_dict(state.get("summary"))

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "data": {
            "as_of_date": str(state.get("as_of_date") or (as_of_date.isoformat() if as_of_date else "")),
            "stock_count": int(state.get("stock_count") or len(stocks)),
            "summary": {
                "latest_price_date": str(summary.get("latest_price_date") or ""),
                "priced_stock_count": int(summary.get("priced_stock_count") or 0),
                "recommended_stock_count": int(summary.get("recommended_stock_count") or 0),
                "held_stock_count": int(summary.get("held_stock_count") or 0),
            },
            "stocks": stocks,
        },
        "links": {
            "dashboard": "/api/dashboard/today",
            "data_health": "/api/data-health",
        },
    }


def build_live_stock_detail_response(
    parsed: ParsedApiPath,
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    symbol = _parse_detail_identifier(parsed.path, "/api/stocks/").upper()
    as_of_date = _parse_optional_date(parsed.query, "asOfDate")
    state = load_frontend_stock_detail_state(
        config=config,
        executor=executor,
        symbol=symbol,
        as_of_date=as_of_date,
    )
    price_bars = [_build_stock_price_bar_payload(item) for item in _as_list(state.get("price_bars"))]
    recommendation = _build_stock_recommendation_payload(_as_dict(state.get("recommendation")))
    thesis_id = recommendation.get("linked_thesis_id") if recommendation else None
    recommendation_id = recommendation.get("recommendation_id") if recommendation else None
    as_of_text = str(state.get("as_of_date") or (as_of_date.isoformat() if as_of_date else ""))

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "data": {
            "symbol": str(state.get("symbol") or symbol).upper(),
            "name": str(state.get("name") or ""),
            "instrument_id": _opaque_id("instrument", state.get("instrument_id"), symbol.lower()),
            "market_code": str(state.get("market_code") or "US"),
            "currency_code": str(state.get("currency_code") or "USD"),
            "as_of_date": as_of_text,
            "latest_price": _build_stock_price_payload(_as_dict(state.get("latest_price"))),
            "summary": _build_stock_detail_summary_payload(_as_dict(state.get("summary")), price_bars),
            "price_bars": price_bars,
            "recommendation": recommendation,
            "position": _build_stock_position_payload(_as_dict(state.get("position"))),
            "macro_flow_impacts": [
                _build_stock_macro_flow_payload(item) for item in _as_list(state.get("macro_flow_impacts"))
            ],
            "recent_events": [_build_stock_event_payload(item) for item in _as_list(state.get("recent_events"))],
        },
        "links": {
            "stocks": "/api/stocks",
            "data_health": "/api/data-health",
            "events": f"/api/events?asOfDate={quote(as_of_text)}&symbol={quote(symbol)}" if as_of_text else f"/api/events?symbol={quote(symbol)}",
            **(
                {"recommendation": f"/api/recommendations/{recommendation_id}"}
                if recommendation_id
                else {}
            ),
            **({"thesis": f"/api/theses/{thesis_id}"} if thesis_id else {}),
        },
    }


def build_live_ai_evidence_neighborhood_response(
    parsed: ParsedApiPath,
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    symbol = _parse_detail_identifier(parsed.path, "/api/ai/evidence-neighborhoods/").upper()
    as_of_date = _parse_optional_date(parsed.query, "asOfDate") or date.today()
    limit = _parse_optional_int(parsed.query, "maxItems", default=25, minimum=1, maximum=50)
    state = load_frontend_ai_evidence_neighborhood_state(
        config=config,
        executor=executor,
        symbol=symbol,
        as_of_date=as_of_date,
        limit=limit,
    )
    themes = [_build_neighborhood_theme_payload(item) for item in _as_list(state.get("themes"))]
    theme_edges = [_build_neighborhood_theme_edge_payload(item) for item in _as_list(state.get("theme_edges"))]
    events = [_build_neighborhood_event_payload(item) for item in _as_list(state.get("events"))]
    ai_artifacts = [_build_neighborhood_ai_artifact_payload(item) for item in _as_list(state.get("ai_artifacts"))]
    evidence_chunks = [_build_neighborhood_evidence_chunk_payload(item) for item in _as_list(state.get("evidence_chunks"))]
    story_groups = _build_neighborhood_story_group_payloads(
        raw_events=_as_list(state.get("events")),
        raw_chunks=_as_list(state.get("evidence_chunks")),
    )
    theses = [_build_neighborhood_thesis_payload(item) for item in _as_list(state.get("theses"))]
    recommendations = [
        _build_neighborhood_recommendation_payload(item) for item in _as_list(state.get("recommendations"))
    ]
    positions = [_build_neighborhood_position_payload(item) for item in _as_list(state.get("positions"))]

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "data": {
            "symbol": symbol,
            "as_of_date": as_of_date.isoformat(),
            "retrieval_boundary": {
                "mode": "read_only_evidence_neighborhood",
                "retrieval_backend": "postgres_sql",
                "vector_backend": "not_configured",
                "graph_backend": "postgres_canonical_tables",
                "live_llm_call_enabled": False,
                "token_budget": 0,
                "cost_estimate_usd": 0.0,
            },
            "instrument": _build_neighborhood_instrument_payload(_as_dict(state.get("instrument")), fallback_symbol=symbol),
            "summary": {
                "theme_count": len(themes),
                "theme_edge_count": len(theme_edges),
                "event_count": len(events),
                "story_group_count": len(story_groups),
                "ai_artifact_count": len(ai_artifacts),
                "evidence_chunk_count": len(evidence_chunks),
                "embedded_chunk_count": sum(1 for item in evidence_chunks if item["embedding_status"] == "indexed"),
                "thesis_count": len(theses),
                "recommendation_count": len(recommendations),
                "position_count": len(positions),
            },
            "themes": themes,
            "theme_edges": theme_edges,
            "events": events,
            "story_groups": story_groups,
            "ai_artifacts": ai_artifacts,
            "evidence_chunks": evidence_chunks,
            "theses": theses,
            "recommendations": recommendations,
            "positions": positions,
            "guardrails": [
                "이 응답은 read-only 증거 관계망이며 추천 점수나 주문을 변경하지 않는다.",
                "vector storage URI, DB URL, secret 값은 노출하지 않는다.",
                "현재 retrieval은 Postgres canonical table 기반이며 live LLM 호출을 수행하지 않는다.",
            ],
        },
        "links": {
            "stock": f"/api/stocks/{quote(symbol)}",
            "events": f"/api/events?asOfDate={quote(as_of_date.isoformat())}&symbol={quote(symbol)}",
        },
    }


def build_live_paper_trading_preview_response(
    parsed: ParsedApiPath,
    *,
    api_path: str,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    as_of_date = _parse_optional_date(parsed.query, "asOfDate")
    page_limit, page_offset = frontend_sql_page_window(api_path)
    state = load_frontend_paper_trading_preview_state(
        config=config,
        executor=executor,
        as_of_date=as_of_date,
        page_limit=page_limit,
        page_offset=page_offset,
    )
    latest_batch = _as_dict(state.get("latest_recommendation_batch"))
    quality_summary = _as_dict(state.get("quality_summary"))
    paper_actions = [_build_paper_action_payload(item) for item in _as_list(state.get("paper_actions"))]
    guardrails = state.get("guardrails")

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "data": {
            "as_of_date": str(state.get("as_of_date") or (as_of_date.isoformat() if as_of_date else "")),
            "portfolio_name": str(state.get("portfolio_name") or DEFAULT_PORTFOLIO_NAME),
            "strategy_name": str(state.get("strategy_name") or DEFAULT_STRATEGY_NAME),
            "latest_recommendation_batch": {
                "as_of_date": str(latest_batch.get("as_of_date") or ""),
                "horizon_type": str(latest_batch.get("horizon_type") or "long_term"),
                "universe_version": str(latest_batch.get("universe_version") or "unknown"),
            },
            "quality_summary": {
                "recommendation_count": int(quality_summary.get("recommendation_count") or 0),
                "measured_recommendation_count": int(quality_summary.get("measured_recommendation_count") or 0),
                "unmeasured_recommendation_count": int(quality_summary.get("unmeasured_recommendation_count") or 0),
                "hit_rate": _number(quality_summary.get("hit_rate")),
                "average_alpha": _number(quality_summary.get("average_alpha")),
                "position_recommendation_conflict_count": int(
                    quality_summary.get("position_recommendation_conflict_count") or 0
                ),
                "paper_action_count": int(quality_summary.get("paper_action_count") or len(paper_actions)),
                "requires_human_approval_count": int(quality_summary.get("requires_human_approval_count") or 0),
            },
            "guardrails": [str(item) for item in guardrails] if isinstance(guardrails, list) else _paper_guardrails(),
            "paper_actions": paper_actions,
        },
        "links": {
            "stocks": "/api/stocks",
            "trading_readiness": "/api/trading/readiness",
            "portfolio_coverage": "/api/portfolio/Long%20Term%20Paper/coverage",
            "performance": "/api/performance/Long%20Term%20Paper/outcomes",
            "data_health": "/api/data-health",
        },
    }


def build_live_trading_readiness_response(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    state = load_frontend_trading_readiness_state(config=config, executor=executor)
    gates = _build_trading_readiness_gates(state)
    gate_summary = _summarize_trading_gates(gates)

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "data": {
            "portfolio_name": str(state.get("portfolio_name") or DEFAULT_PORTFOLIO_NAME),
            "execution_mode": str(state.get("execution_mode") or "paper"),
            "readiness_status": _trading_readiness_status(gate_summary),
            "gate_summary": gate_summary,
            "gates": gates,
            "broker_boundary": _build_trading_broker_boundary_payload(_as_dict(state.get("broker_boundary"))),
            "account_permission": _build_trading_account_permission_payload(_as_dict(state.get("account_permission"))),
            "order_limit_policy": _build_trading_order_limit_policy_payload(_as_dict(state.get("order_limit_policy"))),
            "kill_switches": [_build_trading_kill_switch_payload(item) for item in _as_list(state.get("kill_switches"))],
            "paper_validation": _build_trading_paper_validation_payload(_as_dict(state.get("paper_validation"))),
            "audit_summary": _build_trading_audit_summary_payload(_as_dict(state.get("audit_summary"))),
            "guardrails": _trading_readiness_guardrails(),
        },
        "links": {
            "paper_trading_preview": "/api/paper-trading/preview",
            "stocks": "/api/stocks",
            "data_health": "/api/data-health",
        },
    }


def _load_provider_budget_for_data_health(state: dict[str, Any]) -> dict[str, object]:
    budget_date = _parse_optional_iso_date(str(state.get("as_of_date") or "")) or date.today()
    return load_market_price_provider_budget_status(
        ledger_path=os.getenv(MARKET_PRICE_BUDGET_LEDGER_PATH_ENV),
        budget_date=budget_date,
        provider=os.getenv(MARKET_PRICE_PROVIDER_ENV, "alpha_vantage"),
    )


def _load_scheduler_activation_for_data_health() -> dict[str, object]:
    report_path = os.getenv(SCHEDULER_APPROVAL_GATE_REPORT_ENV, "").strip()
    base = {
        "status": "not_configured",
        "job_id": "",
        "pipeline_name": "",
        "domain": "",
        "cadence": "",
        "approval_gate": "not_configured",
        "activation_allowed": False,
        "scheduler_activation": "not_installed",
        "manual_next_step": "configure_scheduler_activation_gate_report",
        "generated_at": "",
        "source": "not_configured",
    }
    if not report_path:
        return base

    try:
        payload = json.loads(Path(report_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            **base,
            "status": "invalid_report",
            "approval_gate": "invalid_report",
            "manual_next_step": "regenerate_scheduler_activation_gate_report",
            "source": "invalid_report",
        }

    if payload.get("report_name") != "data_operations_scheduler_activation_approval_gate":
        return {
            **base,
            "status": "invalid_report",
            "approval_gate": "invalid_report",
            "manual_next_step": "regenerate_scheduler_activation_gate_report",
            "source": "invalid_report",
        }

    approval_gate = str(payload.get("approval_gate") or "unknown")
    activation_allowed = payload.get("activation_allowed") is True
    status = _scheduler_activation_status(approval_gate=approval_gate, activation_allowed=activation_allowed)
    return {
        "status": status,
        "job_id": str(payload.get("job_id") or ""),
        "pipeline_name": str(payload.get("pipeline_name") or ""),
        "domain": str(payload.get("domain") or ""),
        "cadence": str(payload.get("cadence") or ""),
        "approval_gate": approval_gate,
        "activation_allowed": activation_allowed,
        "scheduler_activation": str(payload.get("scheduler_activation") or "not_installed"),
        "manual_next_step": str(payload.get("manual_next_step") or ""),
        "generated_at": str(payload.get("generated_at") or ""),
        "source": "scheduler_activation_approval_gate_report",
    }


def _scheduler_activation_status(*, approval_gate: str, activation_allowed: bool) -> str:
    if approval_gate == "blocked_pending_manual_approval":
        return "pending_manual_approval"
    if approval_gate == "approved_for_manual_activation" and activation_allowed:
        return "approved_for_manual_activation"
    return approval_gate or "unknown"


def _load_operating_data_profile_scheduler_status_for_data_health() -> dict[str, object]:
    report_path = os.getenv(OPERATING_DATA_PROFILE_SCHEDULER_STATUS_REPORT_ENV, "").strip()
    base = {
        "status": "not_configured",
        "install_status": "not_installed",
        "scheduler_type": "",
        "timer_count": 0,
        "active_timer_count": 0,
        "generated_at": "",
        "source": "not_configured",
        "timers": [],
    }
    if not report_path:
        return base

    try:
        payload = json.loads(Path(report_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            **base,
            "status": "invalid_report",
            "install_status": "invalid_report",
            "source": "invalid_report",
        }

    if payload.get("report_name") != "operating_data_profile_scheduler_status":
        return {
            **base,
            "status": "invalid_report",
            "install_status": "invalid_report",
            "source": "invalid_report",
        }

    timers = []
    for item in _as_list(payload.get("timers")):
        if not isinstance(item, Mapping):
            continue
        timers.append(
            {
                "profile_id": str(item.get("profile_id") or ""),
                "service_name": str(item.get("service_name") or ""),
                "timer_name": str(item.get("timer_name") or ""),
                "schedule": str(item.get("schedule") or ""),
                "active_state": str(item.get("active_state") or ""),
                "next_elapse": str(item.get("next_elapse") or ""),
                "last_result": str(item.get("last_result") or ""),
            }
        )

    install_status = str(payload.get("install_status") or "unknown")
    return {
        "status": str(payload.get("status") or install_status),
        "install_status": install_status,
        "scheduler_type": str(payload.get("scheduler_type") or ""),
        "timer_count": int(payload.get("timer_count") or len(timers)),
        "active_timer_count": int(payload.get("active_timer_count") or 0),
        "generated_at": str(payload.get("generated_at") or ""),
        "source": "operating_data_profile_scheduler_status_report",
        "timers": timers,
    }


def _installed_profile_scheduler_activation(profile_scheduler_status: Mapping[str, object]) -> dict[str, object]:
    return {
        "status": "installed",
        "job_id": "operating-data-profile-scheduler",
        "pipeline_name": "operating_data_profile_scheduler",
        "domain": "operations",
        "cadence": "mixed",
        "approval_gate": "installed_on_ec2_systemd",
        "activation_allowed": True,
        "scheduler_activation": "installed",
        "manual_next_step": "",
        "generated_at": str(profile_scheduler_status.get("generated_at") or ""),
        "source": "operating_data_profile_scheduler_status_report",
    }


def build_live_cycle_state_list_response(
    parsed: ParsedApiPath,
    *,
    api_path: str,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    as_of_date = _parse_required_date(parsed.query, "asOfDate")
    page_limit, page_offset = frontend_sql_page_window(api_path)
    state = load_frontend_cycle_state_list_state(
        config=config,
        executor=executor,
        as_of_date=as_of_date,
        page_limit=page_limit,
        page_offset=page_offset,
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


def build_live_recommendation_list_response(
    parsed: ParsedApiPath,
    *,
    api_path: str,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    as_of_date = _parse_optional_date(parsed.query, "asOfDate") or _parse_optional_date(parsed.query, "batchDate")
    page_limit, page_offset = frontend_sql_page_window(api_path)
    state = load_frontend_recommendation_list_state(
        config=config,
        executor=executor,
        as_of_date=as_of_date,
        page_limit=page_limit,
        page_offset=page_offset,
    )
    recommendations = [
        _build_recommendation_list_item_payload(item) for item in _as_list(state.get("recommendations"))
    ]
    summary = _as_dict(state.get("summary"))
    as_of_text = str(state.get("as_of_date") or (as_of_date.isoformat() if as_of_date else ""))

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "data": {
            "as_of_date": as_of_text,
            "strategy_name": str(state.get("strategy_name") or DEFAULT_STRATEGY_NAME),
            "horizon_type": str(state.get("horizon_type") or "long_term"),
            "universe_version": str(state.get("universe_version") or "unknown"),
            "recommendation_count": int(state.get("recommendation_count") or len(recommendations)),
            "summary": {
                "active_count": int(summary.get("active_count") or 0),
                "reviewable_count": int(summary.get("reviewable_count") or 0),
                "blocked_count": int(summary.get("blocked_count") or 0),
                "measured_count": int(summary.get("measured_count") or 0),
                "linked_thesis_count": int(summary.get("linked_thesis_count") or 0),
                "ai_or_event_evidence_count": int(summary.get("ai_or_event_evidence_count") or 0),
                "average_score": _number(summary.get("average_score")),
            },
            "recommendations": recommendations,
        },
        "links": {
            "dashboard": "/api/dashboard/today",
            "stocks": "/api/stocks",
            "paper_trading": "/api/paper-trading/preview",
            "portfolio_coverage": (
                f"/api/portfolio/{quote(DEFAULT_PORTFOLIO_NAME, safe='')}/coverage?asOfDate={quote(as_of_text)}"
                if as_of_text
                else f"/api/portfolio/{quote(DEFAULT_PORTFOLIO_NAME, safe='')}/coverage"
            ),
        },
    }


def build_live_event_list_response(
    parsed: ParsedApiPath,
    *,
    api_path: str,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    as_of_date = _parse_required_date(parsed.query, "asOfDate")
    theme_key = parsed.query.get("themeKey") or None
    symbol = parsed.query.get("symbol") or None
    event_type = parsed.query.get("eventType") or "all"
    page_limit, page_offset = frontend_sql_page_window(api_path)
    state = load_frontend_event_list_state(
        config=config,
        executor=executor,
        as_of_date=as_of_date,
        theme_key=theme_key,
        symbol=symbol,
        event_type=event_type,
        page_limit=page_limit,
        page_offset=page_offset,
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


def build_live_ai_news_cluster_list_response(
    parsed: ParsedApiPath,
    *,
    api_path: str,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    as_of_date = _parse_optional_date(parsed.query, "asOfDate") or date.today()
    theme_key = parsed.query.get("themeKey") or None
    symbol = parsed.query.get("symbol") or None
    page_limit, page_offset = frontend_sql_page_window(api_path)
    state = load_frontend_ai_news_cluster_list_state(
        config=config,
        executor=executor,
        as_of_date=as_of_date,
        theme_key=theme_key,
        symbol=symbol,
        page_limit=page_limit,
        page_offset=page_offset,
    )
    clusters = [_build_ai_news_cluster_payload(item) for item in _as_list(state.get("clusters"))]
    summary = _as_dict(state.get("summary"))

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "data": {
            "as_of_date": str(state.get("as_of_date") or as_of_date.isoformat()),
            "filters": {
                "theme_key": theme_key,
                "symbol": symbol.upper() if symbol else None,
            },
            "summary": {
                "cluster_count": int(summary.get("cluster_count") or len(clusters)),
                "clustered_event_count": int(summary.get("clustered_event_count") or 0),
                "source_document_count": int(summary.get("source_document_count") or 0),
                "chunk_count": int(summary.get("chunk_count") or 0),
                "embedded_chunk_count": int(summary.get("embedded_chunk_count") or 0),
                "local_rule_cluster_count": int(summary.get("local_rule_cluster_count") or 0),
                "estimated_cost_usd": _number(summary.get("estimated_cost_usd")) or 0.0,
            },
            "clusters": clusters,
            "guardrails": [
                "저장된 뉴스 묶음은 read-only 분석 근거이며 추천 점수나 주문을 변경하지 않는다.",
                "RSS 뉴스 묶음은 현재 무료 로컬 규칙 기반이다.",
                "vector storage URI, DB URL, secret 값은 노출하지 않는다.",
                "현재 화면은 live LLM 호출을 수행하지 않는다.",
            ],
        },
        "links": {
            "events": f"/api/events?asOfDate={quote(as_of_date.isoformat())}&eventType=news_rss_item",
            "intelligence": "/intelligence",
        },
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
    api_path: str,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    portfolio_name = _parse_performance_portfolio_name(parsed.path)
    measurement_end_date = _parse_required_date(parsed.query, "measurementEndDate")
    page_limit, page_offset = frontend_sql_page_window(api_path)
    state = load_frontend_performance_outcomes_state(
        config=config,
        executor=executor,
        portfolio_name=portfolio_name,
        measurement_end_date=measurement_end_date,
        outcome_limit=page_limit,
        outcome_offset=page_offset,
    )
    summary = _as_dict(state.get("summary"))
    outcomes = [_build_performance_outcome_payload(item) for item in _as_list(state.get("outcomes"))]
    attribution_components = [
        _build_attribution_component_payload(item) for item in _as_list(state.get("attribution_components"))
    ]
    coverage_exclusions = [_build_coverage_exclusion_payload(item) for item in _as_list(state.get("coverage_exclusions"))]
    quality_gates = [_build_quality_gate_payload(item) for item in _as_list(state.get("quality_gates"))]
    performance_summary = _build_performance_summary(summary, outcomes, attribution_components, coverage_exclusions)
    quality_evaluation = _build_performance_quality_evaluation_payload(
        _as_dict(state.get("quality_evaluation")),
        summary=performance_summary,
        coverage_exclusions=coverage_exclusions,
    )

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
            "summary": performance_summary,
            "quality_evaluation": quality_evaluation,
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
            "evidence_review": _build_recommendation_evidence_review_payload(
                score_components=score_components,
                linked_thesis_id=linked_thesis_id,
                outcome=outcome,
            ),
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
                "summary": str(latest_review.get("summary") or ""),
                "change_notes": str(latest_review.get("change_notes") or ""),
                "next_review_date": _timestamp(latest_review.get("next_review_date")),
            },
            "evidence": evidence,
            "evidence_review": _build_thesis_evidence_review_payload(
                evidence=evidence,
                invalidation_conditions=_as_list(state.get("invalidation_conditions")),
                latest_review=latest_review,
            ),
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
    cluster_summary = _as_dict(state.get("cluster_summary"))
    news_candidate = _as_dict(state.get("news_candidate"))

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
            "news_candidate": _build_ai_evidence_news_candidate_payload(news_candidate),
            "retrieval_context_summary": _build_ai_evidence_retrieval_context_payload(
                _as_dict(state.get("retrieval_context_summary"))
            ),
            "source_chunks": [_build_source_chunk_payload(item) for item in _as_list(state.get("source_chunks"))],
            "cluster_summary": _build_ai_evidence_cluster_summary_payload(cluster_summary),
            "cluster_events": [
                _build_ai_evidence_cluster_event_payload(item) for item in _as_list(state.get("cluster_events"))
            ],
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
    api_path: str,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    status = parsed.query.get("status", "open") or "open"
    page_limit, page_offset = frontend_sql_page_window(api_path)
    report = load_portfolio_remediation_ticket_report(
        config=config,
        portfolio_name=DEFAULT_PORTFOLIO_NAME,
        status=status,
        limit=page_limit,
        offset=page_offset,
        executor=executor,
    )

    tickets = [_build_ticket_payload(ticket) for ticket in _as_list(report.get("tickets"))]
    allocation_policy = _build_allocation_policy_payload(
        _load_remediation_allocation_policy(config=config, executor=executor)
    )
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
            "allocation_policy": allocation_policy,
            "tickets": tickets,
        },
        "links": {
            "dashboard": "/api/dashboard/today",
            "portfolio_coverage": coverage_link,
        },
    }


def _load_remediation_allocation_policy(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    return json_loads_object(
        sql_executor.execute_scalar(render_frontend_remediation_allocation_policy_sql()),
        "remediation allocation policy lookup",
    )


def render_frontend_remediation_allocation_policy_sql() -> str:
    return f"""-- frontend remediation allocation policy lookup
with target_portfolio as (
    select portfolio_id, portfolio_name, strategy_name
    from portfolio.portfolio
    where portfolio_name = {sql_literal(DEFAULT_PORTFOLIO_NAME)}
    order by portfolio_id desc
    limit 1
),
selected_policy as (
    select
        policy.allocation_policy_id,
        policy.policy_name,
        policy.status,
        policy.max_single_position_weight,
        policy.min_rebalance_target_weight,
        policy.valid_from,
        policy.valid_to,
        policy.rationale,
        case
            when policy.portfolio_id = (select portfolio_id from target_portfolio) then 'portfolio'
            when policy.strategy_name = (select strategy_name from target_portfolio) then 'strategy'
            else 'global'
        end as policy_scope
    from portfolio.allocation_policy policy
    where policy.status = 'active'
      and (policy.portfolio_id = (select portfolio_id from target_portfolio) or policy.portfolio_id is null)
      and (policy.strategy_name = (select strategy_name from target_portfolio) or policy.strategy_name is null)
      and policy.valid_from <= current_date
      and (policy.valid_to is null or policy.valid_to >= current_date)
    order by
        case when policy.portfolio_id = (select portfolio_id from target_portfolio) then 0 else 1 end,
        case when policy.strategy_name = (select strategy_name from target_portfolio) then 0 else 1 end,
        policy.valid_from desc,
        policy.allocation_policy_id desc
    limit 1
)
select json_build_object(
    'allocation_policy_id', (select allocation_policy_id from selected_policy),
    'policy_name', coalesce((select policy_name from selected_policy), 'default_fallback'),
    'status', coalesce((select status from selected_policy), 'fallback'),
    'policy_scope', coalesce((select policy_scope from selected_policy), 'fallback'),
    'max_single_position_weight', coalesce((select max_single_position_weight from selected_policy), 0.2500::numeric),
    'min_rebalance_target_weight', coalesce((select min_rebalance_target_weight from selected_policy), 0.1000::numeric),
    'valid_from', (select valid_from::text from selected_policy),
    'valid_to', (select valid_to::text from selected_policy),
    'rationale', coalesce(
        (select rationale from selected_policy),
        'Fallback review-only guardrail used when no active allocation policy row is configured.'
    )
)::text;"""


def build_live_portfolio_coverage_response(
    parsed: ParsedApiPath,
    *,
    api_path: str,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    generated_at: str,
) -> dict[str, Any]:
    portfolio_name = _parse_coverage_portfolio_name(parsed.path)
    as_of_date = _parse_required_date(parsed.query, "asOfDate")
    measurement_end_date = _parse_optional_date(parsed.query, "measurementEndDate") or (
        as_of_date + timedelta(days=DEFAULT_COVERAGE_HORIZON_DAYS)
    )
    page_limit, page_offset = frontend_sql_page_window(api_path)

    missing_position_snapshot = False
    try:
        report = load_portfolio_outcome_coverage_report(
            config=config,
            portfolio_name=portfolio_name,
            snapshot_date=as_of_date,
            measurement_end_date=measurement_end_date,
            position_limit=page_limit,
            position_offset=page_offset,
            executor=executor,
        )
    except ValueError as exc:
        if str(exc) != NO_PORTFOLIO_POSITIONS_MESSAGE:
            raise
        latest_snapshot_date = _load_latest_portfolio_snapshot_date(
            config=config,
            executor=executor,
            portfolio_name=portfolio_name,
            requested_date=as_of_date,
        )
        if latest_snapshot_date and latest_snapshot_date != as_of_date:
            report = load_portfolio_outcome_coverage_report(
                config=config,
                portfolio_name=portfolio_name,
                snapshot_date=latest_snapshot_date,
                measurement_end_date=max(measurement_end_date, latest_snapshot_date),
                position_limit=page_limit,
                position_offset=page_offset,
                executor=executor,
            )
        else:
            missing_position_snapshot = True
            report = _empty_portfolio_coverage_report(
                portfolio_name=portfolio_name,
                snapshot_date=as_of_date,
                measurement_end_date=measurement_end_date,
                position_limit=page_limit,
                position_offset=page_offset,
            )
    positions = [_build_position_payload(position) for position in _as_list(report.get("positions"))]
    blocking_reasons = [
        f"{position['coverage_status']}:{position['symbol']}"
        for position in positions
        if position["coverage_status"] != "covered"
    ]
    if missing_position_snapshot:
        blocking_reasons.append(f"missing_position_snapshot:{portfolio_name}")
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


def _load_latest_portfolio_snapshot_date(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    portfolio_name: str,
    requested_date: date,
) -> date | None:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(
        render_latest_portfolio_snapshot_date_sql(
            portfolio_name=portfolio_name,
            requested_date=requested_date,
        )
    )
    snapshot_text = str(payload or "").strip()
    if not snapshot_text:
        return None
    return date.fromisoformat(snapshot_text)


def render_latest_portfolio_snapshot_date_sql(*, portfolio_name: str, requested_date: date) -> str:
    return f"""-- frontend latest portfolio snapshot date lookup
with selected_portfolio as (
    select portfolio_id
    from portfolio.portfolio
    where portfolio_name = {sql_literal(portfolio_name)}
    limit 1
)
select coalesce(max(position.snapshot_date)::text, '')
from selected_portfolio portfolio
join portfolio.position_snapshot position on position.portfolio_id = portfolio.portfolio_id
where position.snapshot_date <= {sql_date(requested_date)}
  and position.quantity <> 0
"""


def _empty_portfolio_coverage_report(
    *,
    portfolio_name: str,
    snapshot_date: date,
    measurement_end_date: date,
    position_limit: int,
    position_offset: int,
) -> dict[str, Any]:
    return {
        "portfolio_id": None,
        "portfolio_name": portfolio_name,
        "snapshot_date": snapshot_date.isoformat(),
        "measurement_end_date": measurement_end_date.isoformat(),
        "position_limit": position_limit,
        "position_offset": position_offset,
        "position_count": 0,
        "status_counts": {
            "covered": 0,
            "missing_outcome": 0,
            "missing_thesis": 0,
            "missing_weight": 0,
        },
        "weight_by_status": {
            "covered": None,
            "missing_outcome": None,
            "missing_thesis": None,
            "missing_weight": None,
        },
        "cash_weight": None,
        "coverage_ratio_by_weight": None,
        "positions": [],
    }


def is_live_supported_path(api_path: str) -> bool:
    parsed = parse_api_path(api_path)
    return (
        parsed.path
        in {
            "/api/dashboard/today",
            "/api/data-health",
            "/api/stocks",
            "/api/paper-trading/preview",
            "/api/trading/readiness",
            "/api/cycles",
            "/api/recommendations",
            "/api/events",
            "/api/ai/news-clusters",
            "/api/remediation-tickets",
        }
        or parsed.path.startswith("/api/stocks/")
        or parsed.path.startswith("/api/themes/")
        or (parsed.path.startswith("/api/performance/") and parsed.path.endswith("/outcomes"))
        or parsed.path.startswith("/api/recommendations/")
        or parsed.path.startswith("/api/theses/")
        or parsed.path.startswith("/api/ai/evidence-neighborhoods/")
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


def load_frontend_stock_list_state(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    as_of_date: date | None,
    page_limit: int,
    page_offset: int,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(
        render_frontend_stock_list_state_sql(
            as_of_date=as_of_date,
            page_limit=page_limit,
            page_offset=page_offset,
        )
    )
    return json_loads_object(payload, "Frontend stock list state lookup")


def load_frontend_stock_detail_state(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    symbol: str,
    as_of_date: date | None,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(
        render_frontend_stock_detail_state_sql(symbol=symbol, as_of_date=as_of_date)
    )
    return json_loads_object(payload, "Frontend stock detail state lookup")


def load_frontend_ai_evidence_neighborhood_state(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    symbol: str,
    as_of_date: date,
    limit: int,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(
        render_instrument_evidence_neighborhood_sql(primary_symbol=symbol, as_of_date=as_of_date, limit=limit)
    )
    return json_loads_object(payload, "Frontend AI evidence neighborhood state lookup")


def load_frontend_paper_trading_preview_state(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    as_of_date: date | None,
    page_limit: int,
    page_offset: int,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(
        render_frontend_paper_trading_preview_state_sql(
            as_of_date=as_of_date,
            page_limit=page_limit,
            page_offset=page_offset,
        )
    )
    return json_loads_object(payload, "Frontend paper trading preview state lookup")


def load_frontend_trading_readiness_state(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(render_frontend_trading_readiness_state_sql(portfolio_name=DEFAULT_PORTFOLIO_NAME))
    return json_loads_object(payload, "Frontend trading readiness state lookup")


def load_frontend_cycle_state_list_state(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    as_of_date: date,
    page_limit: int,
    page_offset: int,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(
        render_frontend_cycle_state_list_sql(
            as_of_date=as_of_date,
            page_limit=page_limit,
            page_offset=page_offset,
        )
    )
    return json_loads_object(payload, "Frontend cycle state list lookup")


def load_frontend_event_list_state(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    as_of_date: date,
    theme_key: str | None,
    symbol: str | None,
    event_type: str,
    page_limit: int,
    page_offset: int,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(
        render_frontend_event_list_state_sql(
            as_of_date=as_of_date,
            theme_key=theme_key,
            symbol=symbol,
            event_type=event_type,
            page_limit=page_limit,
            page_offset=page_offset,
        )
    )
    return json_loads_object(payload, "Frontend event list state lookup")


def load_frontend_ai_news_cluster_list_state(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    as_of_date: date,
    theme_key: str | None,
    symbol: str | None,
    page_limit: int,
    page_offset: int,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(
        render_frontend_ai_news_cluster_list_state_sql(
            as_of_date=as_of_date,
            theme_key=theme_key,
            symbol=symbol,
            page_limit=page_limit,
            page_offset=page_offset,
        )
    )
    return json_loads_object(payload, "Frontend AI news cluster list state lookup")


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
    outcome_limit: int,
    outcome_offset: int,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(
        render_frontend_performance_outcomes_state_sql(
            portfolio_name=portfolio_name,
            measurement_end_date=measurement_end_date,
            outcome_limit=outcome_limit,
            outcome_offset=outcome_offset,
        )
    )
    return json_loads_object(payload, "Frontend performance outcomes state lookup")


def load_frontend_recommendation_list_state(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None,
    as_of_date: date | None,
    page_limit: int,
    page_offset: int,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(
        render_frontend_recommendation_list_state_sql(
            as_of_date=as_of_date,
            page_limit=page_limit,
            page_offset=page_offset,
        )
    )
    return json_loads_object(payload, "Frontend recommendation list state lookup")


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


def _validate_sql_pagination_window(*, page_limit: int, page_offset: int) -> None:
    if not isinstance(page_limit, int) or isinstance(page_limit, bool):
        raise ValueError("page_limit must be an integer")
    if not isinstance(page_offset, int) or isinstance(page_offset, bool):
        raise ValueError("page_offset must be an integer")
    if page_limit < 1 or page_limit > MAX_PAGE_LIMIT + 1:
        raise ValueError(f"page_limit must be between 1 and {MAX_PAGE_LIMIT + 1}")
    if page_offset < 0:
        raise ValueError("page_offset must be greater than or equal to 0")


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
    expected_jobs_values = render_data_operations_expected_jobs_sql_values()
    return f"""-- frontend data health state lookup
with expected_jobs(
    pipeline_name,
    job_id,
    domain,
    cadence,
    expected_after_local,
    stale_after_hours,
    artifact_policy
) as (
    values
        {expected_jobs_values}
),
latest_runs as (
    select distinct on (expected.pipeline_name)
        expected.pipeline_name,
        expected.job_id,
        expected.domain,
        expected.cadence,
        expected.expected_after_local,
        expected.stale_after_hours,
        expected.artifact_policy,
        run.run_id,
        case
            when run.run_id is null
             and expected.job_id = 'portfolio-attribution-monthly'
             and not exists (select 1 from performance.thesis_outcome)
                then 'not_due'
            else coalesce(run.status, 'missing')
        end as status,
        run.ended_at as finished_at,
        case
            when run.run_id is null
             and expected.job_id = 'portfolio-attribution-monthly'
             and not exists (select 1 from performance.thesis_outcome)
                then 'not_due'
            when run.run_id is null then 'missing'
            when run.status = 'failed' then 'failed'
            when run.status in ('started', 'running') then 'running'
            when run.ended_at is null then 'missing'
            when run.ended_at < now() - make_interval(hours => expected.stale_after_hours) then 'stale'
            else 'ok'
        end as health_status
    from expected_jobs expected
    left join ops.pipeline_run run on run.pipeline_name = expected.pipeline_name
    order by expected.pipeline_name, run.started_at desc nulls last, run.run_id desc nulls last
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
    'overall_status',
    case
        when exists (
            select 1
            from latest_runs
            where health_status in ('missing', 'stale', 'failed')
        ) then 'attention_required'
        else 'healthy'
    end,
    'as_of_date', current_date::text,
    'pipeline_runs',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'pipeline_name', pipeline_name,
                    'job_id', job_id,
                    'domain', domain,
                    'cadence', cadence,
                    'expected_after_local', expected_after_local,
                    'stale_after_hours', stale_after_hours,
                    'artifact_policy', artifact_policy,
                    'latest_status', status,
                    'health_status', health_status,
                    'latest_run_id', run_id,
                    'finished_at', finished_at
                )
                order by cadence, expected_after_local, pipeline_name
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
        'data_operations_artifact_runner'
    )
)::text;"""


def render_frontend_stock_list_state_sql(
    *,
    as_of_date: date | None,
    page_limit: int = 51,
    page_offset: int = 0,
) -> str:
    _validate_sql_pagination_window(page_limit=page_limit, page_offset=page_offset)
    target_date_sql = sql_date(as_of_date) if as_of_date is not None else "current_date"
    return f"""-- frontend stock list state lookup
with target_date as (
    select {target_date_sql}::date as as_of_date
),
latest_price as (
    select distinct on (bar.instrument_id)
        bar.instrument_id,
        bar.trade_date,
        bar.open,
        bar.high,
        bar.low,
        bar.close,
        bar.adjusted_close,
        bar.volume
    from market.daily_price_bar bar
    join target_date target on bar.trade_date <= target.as_of_date
    order by bar.instrument_id, bar.trade_date desc
),
previous_price as (
    select distinct on (bar.instrument_id)
        bar.instrument_id,
        bar.close
    from market.daily_price_bar bar
    join latest_price latest on latest.instrument_id = bar.instrument_id
    where bar.trade_date < latest.trade_date
    order by bar.instrument_id, bar.trade_date desc
),
price_coverage as (
    select
        bar.instrument_id,
        count(*)::int as bar_count,
        min(bar.trade_date) as first_trade_date,
        max(bar.trade_date) as last_trade_date
    from market.daily_price_bar bar
    join target_date target on bar.trade_date <= target.as_of_date
    group by bar.instrument_id
),
latest_recommendation as (
    select distinct on (recommendation.instrument_id)
        recommendation.instrument_id,
        recommendation.recommendation_id,
        recommendation.thesis_id,
        recommendation.action,
        recommendation.total_score,
        recommendation.status,
        batch.as_of_date
    from signal.recommendation recommendation
    join signal.recommendation_batch batch on batch.batch_id = recommendation.batch_id
    join target_date target on batch.as_of_date <= target.as_of_date
    order by recommendation.instrument_id, batch.as_of_date desc, recommendation.recommendation_id desc
),
latest_portfolio_snapshot as (
    select max(position.snapshot_date) as snapshot_date
    from portfolio.position_snapshot position
    join portfolio.portfolio portfolio on portfolio.portfolio_id = position.portfolio_id
    join target_date target on position.snapshot_date <= target.as_of_date
    where portfolio.portfolio_name = {sql_literal(DEFAULT_PORTFOLIO_NAME)}
),
latest_position as (
    select
        position.instrument_id,
        portfolio.portfolio_name,
        position.snapshot_date,
        position.quantity,
        position.weight,
        position.market_price,
        position.market_value,
        position.linked_thesis_id
    from portfolio.position_snapshot position
    join portfolio.portfolio portfolio on portfolio.portfolio_id = position.portfolio_id
    join latest_portfolio_snapshot snapshot on snapshot.snapshot_date = position.snapshot_date
    where portfolio.portfolio_name = {sql_literal(DEFAULT_PORTFOLIO_NAME)}
      and position.quantity <> 0
),
stock_rows as (
    select
        instrument.instrument_id,
        instrument.primary_symbol,
        instrument.name,
        instrument.market_code,
        instrument.currency_code,
        latest.trade_date,
        latest.open,
        latest.high,
        latest.low,
        latest.close,
        latest.adjusted_close,
        latest.volume,
        case
            when previous.close is null or previous.close = 0 then null
            else (latest.close - previous.close) / previous.close
        end as change_pct,
        coverage.bar_count,
        coverage.first_trade_date,
        coverage.last_trade_date,
        recommendation.recommendation_id,
        recommendation.thesis_id,
        recommendation.action,
        recommendation.total_score,
        recommendation.status as recommendation_status,
        recommendation.as_of_date as recommendation_as_of_date,
        position.portfolio_name,
        position.snapshot_date as position_snapshot_date,
        position.quantity,
        position.weight,
        position.market_price,
        position.market_value,
        position.linked_thesis_id
    from ref.instrument instrument
    join latest_price latest on latest.instrument_id = instrument.instrument_id
    join price_coverage coverage on coverage.instrument_id = instrument.instrument_id
    left join previous_price previous on previous.instrument_id = instrument.instrument_id
    left join latest_recommendation recommendation on recommendation.instrument_id = instrument.instrument_id
    left join latest_position position on position.instrument_id = instrument.instrument_id
    where instrument.is_active
),
stock_page as (
    select *
    from stock_rows
    order by primary_symbol
    limit {page_limit}
    offset {page_offset}
)
select json_build_object(
    'as_of_date', (select as_of_date::text from target_date),
    'stock_count', (select count(*)::int from stock_rows),
    'summary',
    json_build_object(
        'latest_price_date', (select max(trade_date)::text from stock_rows),
        'priced_stock_count', (select count(*)::int from stock_rows),
        'recommended_stock_count', (select count(*) filter (where recommendation_id is not null)::int from stock_rows),
        'held_stock_count', (select count(*) filter (where weight is not null and weight <> 0)::int from stock_rows)
    ),
    'stocks',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'symbol', primary_symbol,
                    'name', name,
                    'instrument_id', instrument_id,
                    'market_code', market_code,
                    'currency_code', currency_code,
                    'latest_price',
                    json_build_object(
                        'trade_date', trade_date,
                        'open', open,
                        'high', high,
                        'low', low,
                        'close', close,
                        'adjusted_close', adjusted_close,
                        'volume', volume,
                        'change_pct', change_pct
                    ),
                    'data_coverage',
                    json_build_object(
                        'bar_count', bar_count,
                        'first_trade_date', first_trade_date,
                        'last_trade_date', last_trade_date
                    ),
                    'recommendation',
                    case
                        when recommendation_id is null then null
                        else json_build_object(
                            'recommendation_id', recommendation_id,
                            'linked_thesis_id', thesis_id,
                            'action', action,
                            'score', total_score,
                            'status', recommendation_status,
                            'as_of_date', recommendation_as_of_date
                        )
                    end,
                    'position',
                    case
                        when position_snapshot_date is null then null
                        else json_build_object(
                            'portfolio_name', portfolio_name,
                            'snapshot_date', position_snapshot_date,
                            'quantity', quantity,
                            'weight', weight,
                            'market_price', market_price,
                            'market_value', market_value,
                            'linked_thesis_id', linked_thesis_id
                        )
                    end
                )
                order by primary_symbol
            )
            from stock_page
        ),
        '[]'::json
    )
)::text;"""


def render_frontend_stock_detail_state_sql(*, symbol: str, as_of_date: date | None) -> str:
    target_date_sql = sql_date(as_of_date) if as_of_date is not None else "current_date"
    symbol_literal = sql_literal(symbol.upper())
    return f"""-- frontend stock detail state lookup
with target_date as (
    select {target_date_sql}::date as as_of_date
),
target_instrument as (
    select instrument.*
    from ref.instrument instrument
    where upper(instrument.primary_symbol) = {symbol_literal}
      and instrument.is_active
    order by instrument.instrument_id
    limit 1
),
price_rows_desc as (
    select
        bar.trade_date,
        bar.open,
        bar.high,
        bar.low,
        bar.close,
        bar.adjusted_close,
        bar.volume
    from market.daily_price_bar bar
    join target_instrument instrument on instrument.instrument_id = bar.instrument_id
    join target_date target on bar.trade_date <= target.as_of_date
    order by bar.trade_date desc
    limit 120
),
price_rows as (
    select *
    from price_rows_desc
    order by trade_date
),
latest_price as (
    select *
    from price_rows
    order by trade_date desc
    limit 1
),
first_price as (
    select *
    from price_rows
    order by trade_date
    limit 1
),
latest_recommendation as (
    select
        recommendation.recommendation_id,
        recommendation.thesis_id,
        recommendation.action,
        recommendation.total_score,
        recommendation.status,
        batch.as_of_date
    from signal.recommendation recommendation
    join signal.recommendation_batch batch on batch.batch_id = recommendation.batch_id
    join target_instrument instrument on instrument.instrument_id = recommendation.instrument_id
    join target_date target on batch.as_of_date <= target.as_of_date
    order by batch.as_of_date desc, recommendation.recommendation_id desc
    limit 1
),
latest_portfolio_snapshot as (
    select max(position.snapshot_date) as snapshot_date
    from portfolio.position_snapshot position
    join portfolio.portfolio portfolio on portfolio.portfolio_id = position.portfolio_id
    join target_instrument instrument on instrument.instrument_id = position.instrument_id
    join target_date target on position.snapshot_date <= target.as_of_date
    where portfolio.portfolio_name = {sql_literal(DEFAULT_PORTFOLIO_NAME)}
),
latest_position as (
    select
        portfolio.portfolio_name,
        position.snapshot_date,
        position.quantity,
        position.weight,
        position.market_price,
        position.market_value,
        position.linked_thesis_id
    from portfolio.position_snapshot position
    join portfolio.portfolio portfolio on portfolio.portfolio_id = position.portfolio_id
    join target_instrument instrument on instrument.instrument_id = position.instrument_id
    join latest_portfolio_snapshot snapshot on snapshot.snapshot_date = position.snapshot_date
    where portfolio.portfolio_name = {sql_literal(DEFAULT_PORTFOLIO_NAME)}
      and position.quantity <> 0
    limit 1
),
raw_recent_events as (
    select
        event_row.event_id,
        event_row.title,
        event_row.event_type,
        event_row.event_at,
        coalesce(impact.impact_direction, event_row.impact_polarity, 'unknown') as impact_direction,
        coalesce(impact.impact_strength, event_row.significance_score) as impact_score,
        source_document.external_document_id as source_document_id,
        source_document.document_id as raw_source_document_id,
        source_document.url as source_url,
        source_document.checksum as source_checksum,
        evidence.artifact_id as ai_evidence_id
    from event.event_instrument_impact impact
    join target_instrument instrument on instrument.instrument_id = impact.instrument_id
    join event.event event_row on event_row.event_id = impact.event_id
    left join event.event_document_link document_link
      on document_link.event_id = event_row.event_id
     and document_link.link_type = 'source'
    left join ingest.source_document source_document on source_document.document_id = document_link.document_id
    left join lateral (
        select artifact_id
        from ai.extraction_artifact artifact
        where artifact.event_id = event_row.event_id
           or artifact.document_id = source_document.document_id
        order by artifact.artifact_id desc
        limit 1
    ) evidence on true
    join target_date target on event_row.event_at < (target.as_of_date + interval '1 day')
),
recent_events as (
    select *
    from (
        select distinct on (coalesce(nullif(lower(title), ''), source_checksum, 'event:' || event_id::text))
            event_id,
            title,
            event_type,
            event_at,
            impact_direction,
            impact_score,
            source_document_id,
            raw_source_document_id,
            source_url,
            source_checksum,
            ai_evidence_id
        from raw_recent_events
        order by
            coalesce(nullif(lower(title), ''), source_checksum, 'event:' || event_id::text),
            case when lower(coalesce(source_url, '')) like 'https://news.google.com/%' then 1 else 0 end,
            event_at desc,
            event_id desc
    ) deduped_events
    order by
        case when lower(coalesce(source_url, '')) like 'https://news.google.com/%' then 1 else 0 end,
        event_at desc,
        event_id desc
    limit 8
),
macro_flow_impacts as (
    select
        propagated_impact.event_id,
        event_row.title,
        event_row.event_type,
        event_row.event_at,
        node.code as theme_key,
        node.name as theme_name,
        propagated_impact.impact_direction,
        propagated_impact.impact_strength as impact_score,
        propagated_impact.confidence,
        propagated_impact.exposure_weight,
        propagated_impact.rationale,
        source_document.external_document_id as source_document_id,
        source_document.document_id as raw_source_document_id,
        evidence.artifact_id as ai_evidence_id,
        propagated_impact.source_run_id
    from signal.propagated_instrument_impact propagated_impact
    join target_instrument instrument on instrument.instrument_id = propagated_impact.instrument_id
    join event.event event_row on event_row.event_id = propagated_impact.event_id
    join ref.classification_node node on node.node_id = propagated_impact.node_id
    left join event.event_document_link document_link
      on document_link.event_id = event_row.event_id
     and document_link.link_type = 'source'
    left join ingest.source_document source_document on source_document.document_id = document_link.document_id
    left join lateral (
        select artifact_id
        from ai.extraction_artifact artifact
        where artifact.event_id = event_row.event_id
           or artifact.document_id = source_document.document_id
        order by artifact.artifact_id desc
        limit 1
    ) evidence on true
    join target_date target on event_row.event_at < (target.as_of_date + interval '1 day')
    order by event_row.event_at desc, event_row.event_id desc, node.code
    limit 8
)
select json_build_object(
    'symbol', coalesce((select primary_symbol from target_instrument), {symbol_literal}),
    'name', coalesce((select name from target_instrument), ''),
    'instrument_id', (select instrument_id from target_instrument),
    'market_code', coalesce((select market_code from target_instrument), 'US'),
    'currency_code', coalesce((select currency_code from target_instrument), 'USD'),
    'as_of_date', (select as_of_date::text from target_date),
    'latest_price',
    json_build_object(
        'trade_date', (select trade_date from latest_price),
        'open', (select open from latest_price),
        'high', (select high from latest_price),
        'low', (select low from latest_price),
        'close', (select close from latest_price),
        'adjusted_close', (select adjusted_close from latest_price),
        'volume', (select volume from latest_price)
    ),
    'summary',
    json_build_object(
        'bar_count', (select count(*)::int from price_rows),
        'first_trade_date', (select trade_date from first_price),
        'last_trade_date', (select trade_date from latest_price),
        'low_close', (select min(close) from price_rows),
        'high_close', (select max(close) from price_rows),
        'return_pct',
        case
            when (select adjusted_close from first_price) is null or (select adjusted_close from first_price) = 0 then null
            else ((select adjusted_close from latest_price) - (select adjusted_close from first_price)) / (select adjusted_close from first_price)
        end
    ),
    'price_bars',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'trade_date', trade_date,
                    'open', open,
                    'high', high,
                    'low', low,
                    'close', close,
                    'adjusted_close', adjusted_close,
                    'volume', volume
                )
                order by trade_date
            )
            from price_rows
        ),
        '[]'::json
    ),
    'recommendation',
    (
        select json_build_object(
            'recommendation_id', recommendation_id,
            'linked_thesis_id', thesis_id,
            'action', action,
            'score', total_score,
            'status', status,
            'as_of_date', as_of_date
        )
        from latest_recommendation
    ),
    'position',
    (
        select json_build_object(
            'portfolio_name', portfolio_name,
            'snapshot_date', snapshot_date,
            'quantity', quantity,
            'weight', weight,
            'market_price', market_price,
            'market_value', market_value,
            'linked_thesis_id', linked_thesis_id
        )
        from latest_position
    ),
    'macro_flow_impacts',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'event_id', event_id,
                    'title', title,
                    'event_type', event_type,
                    'event_at', event_at,
                    'theme_key', theme_key,
                    'theme_name', theme_name,
                    'impact_direction', impact_direction,
                    'impact_score', impact_score,
                    'confidence', confidence,
                    'exposure_weight', exposure_weight,
                    'rationale', rationale,
                    'source_document_id', source_document_id,
                    'raw_source_document_id', raw_source_document_id,
                    'ai_evidence_id', ai_evidence_id,
                    'source_run_id', source_run_id
                )
                order by event_at desc, event_id desc, theme_key
            )
            from macro_flow_impacts
        ),
        '[]'::json
    ),
    'recent_events',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'event_id', event_id,
                    'title', title,
                    'event_type', event_type,
                    'event_at', event_at,
                    'impact_direction', impact_direction,
                    'impact_score', impact_score,
                    'source_document_id', source_document_id,
                    'raw_source_document_id', raw_source_document_id,
                    'ai_evidence_id', ai_evidence_id
                )
                order by
                    case when lower(coalesce(source_url, '')) like 'https://news.google.com/%' then 1 else 0 end,
                    event_at desc,
                    event_id desc
            )
            from recent_events
        ),
        '[]'::json
    )
)::text;"""


def render_frontend_paper_trading_preview_state_sql(
    *,
    as_of_date: date | None,
    page_limit: int = 51,
    page_offset: int = 0,
) -> str:
    _validate_sql_pagination_window(page_limit=page_limit, page_offset=page_offset)
    target_date_sql = sql_date(as_of_date) if as_of_date is not None else "current_date"
    return f"""-- frontend paper trading preview state lookup
with target_date as (
    select {target_date_sql}::date as as_of_date
),
latest_batch as (
    select batch.*
    from signal.recommendation_batch batch
    join target_date target on batch.as_of_date <= target.as_of_date
    where batch.strategy_name = {sql_literal(DEFAULT_STRATEGY_NAME)}
    order by batch.as_of_date desc, batch.batch_id desc
    limit 1
),
recommendation_rows as (
    select
        recommendation.recommendation_id,
        recommendation.instrument_id,
        recommendation.thesis_id,
        recommendation.action,
        recommendation.total_score,
        recommendation.recommended_weight,
        recommendation.status,
        batch.as_of_date,
        batch.horizon_type,
        batch.universe_version
    from latest_batch batch
    join signal.recommendation recommendation on recommendation.batch_id = batch.batch_id
    where recommendation.status = 'active'
),
latest_snapshot as (
    select max(position.snapshot_date) as snapshot_date
    from portfolio.position_snapshot position
    join portfolio.portfolio portfolio on portfolio.portfolio_id = position.portfolio_id
    join target_date target on position.snapshot_date <= target.as_of_date
    where portfolio.portfolio_name = {sql_literal(DEFAULT_PORTFOLIO_NAME)}
),
position_rows as (
    select
        position.instrument_id,
        position.snapshot_date,
        position.quantity,
        position.weight,
        position.market_price,
        position.market_value,
        position.linked_thesis_id
    from portfolio.position_snapshot position
    join portfolio.portfolio portfolio on portfolio.portfolio_id = position.portfolio_id
    join latest_snapshot snapshot on snapshot.snapshot_date = position.snapshot_date
    where portfolio.portfolio_name = {sql_literal(DEFAULT_PORTFOLIO_NAME)}
      and position.quantity <> 0
),
latest_price as (
    select distinct on (bar.instrument_id)
        bar.instrument_id,
        bar.trade_date,
        bar.adjusted_close
    from market.daily_price_bar bar
    join target_date target on bar.trade_date <= target.as_of_date
    order by bar.instrument_id, bar.trade_date desc
),
preview_universe as (
    select instrument_id from recommendation_rows
    union
    select instrument_id from position_rows
),
preview_rows as (
    select
        instrument.instrument_id,
        instrument.primary_symbol,
        recommendation.recommendation_id,
        recommendation.thesis_id,
        recommendation.action as recommendation_action,
        recommendation.total_score,
        recommendation.as_of_date as recommendation_as_of_date,
        price.trade_date as latest_price_date,
        price.adjusted_close as latest_price,
        coalesce(position.weight, 0::numeric) as current_weight,
        case
            when recommendation.recommendation_id is null then coalesce(position.weight, 0::numeric)
            when recommendation.action in ('exclude', 'exit', 'sell', 'avoid') then 0::numeric
            when recommendation.recommended_weight is not null then recommendation.recommended_weight
            when recommendation.action in ('accumulate', 'buy', 'monitor_or_accumulate') and coalesce(position.weight, 0::numeric) = 0 then 0.0300::numeric
            else coalesce(position.weight, 0::numeric)
        end as target_weight,
        position.snapshot_date as position_snapshot_date
    from preview_universe preview
    join ref.instrument instrument on instrument.instrument_id = preview.instrument_id
    left join recommendation_rows recommendation on recommendation.instrument_id = preview.instrument_id
    left join position_rows position on position.instrument_id = preview.instrument_id
    left join latest_price price on price.instrument_id = preview.instrument_id
),
classified_rows as (
    select
        *,
        case
            when recommendation_id is null and current_weight > 0 then 'paper_review_no_recommendation'
            when recommendation_action in ('exclude', 'exit', 'sell', 'avoid') and current_weight > 0 then 'paper_sell_to_zero'
            when target_weight > current_weight + 0.0001 and current_weight = 0 then 'paper_buy_to_target'
            when target_weight > current_weight + 0.0001 then 'paper_increase_to_target'
            when target_weight < current_weight - 0.0001 then 'paper_reduce_to_target'
            else 'paper_hold'
        end as paper_action,
        case
            when recommendation_id is null and current_weight > 0 then true
            when recommendation_action in ('exclude', 'exit', 'sell', 'avoid') and current_weight > 0 then true
            else false
        end as conflict,
        case
            when recommendation_id is null and current_weight > 0 then 'high'
            when recommendation_action in ('exclude', 'exit', 'sell', 'avoid') and current_weight > 0 then 'high'
            when target_weight <> current_weight then 'medium'
            else 'low'
        end as risk_level,
        true as requires_human_approval,
        case
            when recommendation_id is null and current_weight > 0
                then '보유 중이지만 최신 추천이 없다. 실제 주문 없이 사람 검토 후보로 표시한다.'
            when recommendation_action in ('exclude', 'exit', 'sell', 'avoid') and current_weight > 0
                then '추천은 제외/매도인데 현재 보유 중이다. 실제 주문 없이 가상 매도 후보로 표시한다.'
            when target_weight > current_weight + 0.0001 and current_weight = 0
                then '추천 목표 비중이 있고 현재 미보유다. 실제 주문 없이 가상 매수 후보로 표시한다.'
            when target_weight > current_weight + 0.0001
                then '추천 목표 비중이 현재 비중보다 높다. 실제 주문 없이 가상 증액 후보로 표시한다.'
            when target_weight < current_weight - 0.0001
                then '추천 목표 비중이 현재 비중보다 낮다. 실제 주문 없이 가상 감액 후보로 표시한다.'
            else '현재 추천과 보유 상태가 크게 충돌하지 않는다. 실제 주문은 만들지 않는다.'
        end as reason
    from preview_rows
),
outcome_rows as (
    select distinct on (outcome.recommendation_id) outcome.*
    from performance.recommendation_outcome outcome
    join recommendation_rows recommendation on recommendation.recommendation_id = outcome.recommendation_id
    order by outcome.recommendation_id, outcome.measurement_end_date desc, outcome.outcome_id desc
),
action_page as (
    select *
    from classified_rows
    order by
        case risk_level when 'high' then 1 when 'medium' then 2 else 3 end,
        primary_symbol
    limit {page_limit}
    offset {page_offset}
)
select json_build_object(
    'as_of_date', (select as_of_date::text from target_date),
    'portfolio_name', {sql_literal(DEFAULT_PORTFOLIO_NAME)},
    'strategy_name', coalesce((select strategy_name from latest_batch), {sql_literal(DEFAULT_STRATEGY_NAME)}),
    'latest_recommendation_batch',
    json_build_object(
        'as_of_date', (select as_of_date from latest_batch),
        'horizon_type', coalesce((select horizon_type from latest_batch), 'long_term'),
        'universe_version', coalesce((select universe_version from latest_batch), 'unknown')
    ),
    'quality_summary',
    json_build_object(
        'recommendation_count', (select count(*)::int from recommendation_rows),
        'measured_recommendation_count', (select count(*)::int from outcome_rows),
        'unmeasured_recommendation_count', greatest(0, (select count(*)::int from recommendation_rows) - (select count(*)::int from outcome_rows)),
        'hit_rate',
        case
            when (select count(*) from outcome_rows) = 0 then null
            else ((select count(*) filter (where alpha_pct > 0 or outcome_label in ('outperform', 'positive')) from outcome_rows)::numeric / (select count(*) from outcome_rows)::numeric)
        end,
        'average_alpha', (select avg(alpha_pct) from outcome_rows),
        'position_recommendation_conflict_count', (select count(*)::int from classified_rows where conflict),
        'paper_action_count', (select count(*)::int from classified_rows where paper_action <> 'paper_hold'),
        'requires_human_approval_count', (select count(*)::int from classified_rows where requires_human_approval)
    ),
    'guardrails',
    json_build_array(
        '이 화면은 가상 거래(Paper) 미리보기이며 실제 주문을 만들지 않는다.',
        '모든 가상 조치는 사람 승인 전까지 실행되지 않는다.',
        '실거래 증권사 API, 계좌 권한, 주문 전송은 아직 연결하지 않았다.'
    ),
    'paper_actions',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'symbol', primary_symbol,
                    'instrument_id', instrument_id,
                    'recommendation_id', recommendation_id,
                    'linked_thesis_id', thesis_id,
                    'recommendation_action', coalesce(recommendation_action, 'no_recommendation'),
                    'recommendation_score', total_score,
                    'recommendation_as_of_date', recommendation_as_of_date,
                    'latest_price_date', latest_price_date,
                    'latest_price', latest_price,
                    'current_weight', current_weight,
                    'target_weight', target_weight,
                    'paper_action', paper_action,
                    'reason', reason,
                    'risk_level', risk_level,
                    'requires_human_approval', requires_human_approval,
                    'conflict', conflict
                )
                order by
                    case risk_level when 'high' then 1 when 'medium' then 2 else 3 end,
                    primary_symbol
            )
            from action_page
        ),
        '[]'::json
    )
)::text;"""


def render_frontend_trading_readiness_state_sql(*, portfolio_name: str) -> str:
    return f"""-- frontend trading readiness state lookup
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
    left join target_portfolio portfolio on portfolio.portfolio_id = permission.portfolio_id
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
    order by
        switch.is_engaged desc,
        case switch.scope when 'global' then 0 else 1 end,
        switch.changed_at desc
),
selected_paper_validation as (
    select validation.*
    from trading.paper_validation_run validation
    where validation.portfolio_id = (select portfolio_id from target_portfolio)
       or validation.portfolio_id is null
    order by validation.validation_date desc, validation.paper_validation_run_id desc
    limit 1
),
audit_summary as (
    select
        count(*)::integer as intent_count,
        count(*) filter (where decision = 'blocked')::integer as blocked_count,
        count(*) filter (where decision = 'approved_for_paper')::integer as approved_for_paper_count,
        count(*) filter (where decision = 'approved_for_live')::integer as approved_for_live_count,
        count(*) filter (where submitted_to_broker)::integer as submitted_to_broker_count,
        max(created_at) as latest_created_at
    from trading.order_intent_audit audit
    where audit.portfolio_id = (select portfolio_id from target_portfolio)
       or audit.portfolio_id is null
)
select json_build_object(
    'portfolio_name', coalesce((select portfolio_name from target_portfolio), {sql_literal(portfolio_name)}),
    'execution_mode', 'paper',
    'broker_boundary',
    (
        select json_build_object(
            'broker_code', broker_code,
            'environment', environment,
            'status', status,
            'supports_order_preview', supports_order_preview,
            'supports_order_submit', supports_order_submit,
            'secret_configured', secret_ref is not null,
            'notes', notes,
            'updated_at', updated_at
        )
        from selected_broker_boundary
    ),
    'account_permission',
    (
        select json_build_object(
            'account_ref', account_ref,
            'permission_scope', permission_scope,
            'status', status,
            'allowed_symbol_count', coalesce(array_length(allowed_symbols, 1), 0),
            'allows_all_symbols', '*' = any(allowed_symbols),
            'max_order_notional', max_order_notional,
            'max_daily_notional', max_daily_notional,
            'approved_by', approved_by,
            'approved_at', approved_at,
            'updated_at', updated_at
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
            'min_cash_buffer_weight', min_cash_buffer_weight,
            'updated_at', updated_at
        )
        from selected_order_limit_policy
    ),
    'kill_switches',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'scope', scope,
                    'scope_ref', scope_ref,
                    'is_engaged', is_engaged,
                    'reason', reason,
                    'changed_by', changed_by,
                    'changed_at', changed_at
                )
                order by is_engaged desc, scope, scope_ref
            )
            from selected_kill_switches
        ),
        '[]'::json
    ),
    'paper_validation',
    (
        select json_build_object(
            'validation_date', validation_date,
            'status', status,
            'recommendation_count', recommendation_count,
            'conflict_count', conflict_count,
            'approved_action_count', approved_action_count,
            'validated_symbol_count', coalesce(array_length(validated_symbols, 1), 0),
            'blocked_reasons', blocked_reasons,
            'created_by', created_by,
            'created_at', created_at
        )
        from selected_paper_validation
    ),
    'audit_summary',
    (
        select json_build_object(
            'intent_count', intent_count,
            'blocked_count', blocked_count,
            'approved_for_paper_count', approved_for_paper_count,
            'approved_for_live_count', approved_for_live_count,
            'submitted_to_broker_count', submitted_to_broker_count,
            'latest_created_at', latest_created_at
        )
        from audit_summary
    )
)::text;"""


def render_frontend_cycle_state_list_sql(*, as_of_date: date, page_limit: int = 51, page_offset: int = 0) -> str:
    _validate_sql_pagination_window(page_limit=page_limit, page_offset=page_offset)
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
),
cycle_page as (
    select current_cycle.*
    from latest_cycle current_cycle
    order by current_cycle.cycle_score desc nulls last, current_cycle.theme_key
    limit {page_limit}
    offset {page_offset}
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
            join cycle_page page_cycle on page_cycle.node_id = current_cycle.node_id
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
    page_limit: int = 51,
    page_offset: int = 0,
) -> str:
    _validate_sql_pagination_window(page_limit=page_limit, page_offset=page_offset)
    filters = _event_list_sql_filters(theme_key=theme_key, symbol=symbol, event_type=event_type)
    return f"""-- frontend event list state lookup
with filtered_event_rows as (
    select
        event_row.event_id,
        event_row.title,
        event_row.event_type,
        event_row.event_at,
        coalesce(instrument.instrument_id, document_instrument.instrument_id) as instrument_id,
        coalesce(instrument.primary_symbol, document_instrument.primary_symbol) as primary_symbol,
        coalesce(theme.code, document_theme.theme_key) as theme_key,
        coalesce(theme.name, document_theme.theme_name) as theme_name,
        coalesce(
            instrument_impact.impact_direction,
            classification_impact.impact_direction,
            document_instrument.impact_direction,
            document_theme.impact_direction,
            event_row.impact_polarity,
            'unknown'
        ) as impact_direction,
        coalesce(
            instrument_impact.impact_strength,
            classification_impact.impact_strength,
            document_instrument.impact_strength,
            document_theme.impact_strength,
            event_row.significance_score
        ) as impact_score,
        source_document.external_document_id as source_document_id,
        source_document.document_id as raw_source_document_id,
        evidence.artifact_id as ai_evidence_id,
        evidence.artifact_type as ai_evidence_type,
        evidence.provider as ai_evidence_provider,
        evidence.confidence as ai_evidence_confidence,
        case
            when evidence.artifact_id is not null then 'human_review_required'
            when source_document.document_id is not null then 'source_document_review_required'
            else 'deterministic_review_required'
        end as quality_gate
    from event.event event_row
    left join lateral (
        select
            impact.instrument_id,
            impact.impact_direction,
            impact.impact_strength
        from event.event_instrument_impact impact
        join ref.instrument impact_instrument
          on impact_instrument.instrument_id = impact.instrument_id
        where impact.event_id = event_row.event_id
        order by
            impact.confidence desc nulls last,
            impact.impact_strength desc nulls last,
            impact_instrument.primary_symbol
        limit 1
    ) instrument_impact on true
    left join ref.instrument instrument on instrument.instrument_id = instrument_impact.instrument_id
    left join lateral (
        select
            impact.node_id,
            impact.impact_direction,
            impact.impact_strength
        from event.event_classification_impact impact
        join ref.classification_node impact_theme
          on impact_theme.node_id = impact.node_id
         and impact_theme.taxonomy_family = 'internal_theme'
        where impact.event_id = event_row.event_id
        order by
            impact.confidence desc nulls last,
            impact.impact_strength desc nulls last,
            impact_theme.code
        limit 1
    ) classification_impact on true
    left join ref.classification_node theme
      on theme.node_id = classification_impact.node_id
     and theme.taxonomy_family = 'internal_theme'
    left join event.event_document_link document_link
      on document_link.event_id = event_row.event_id
     and document_link.link_type = 'source'
    left join ingest.source_document source_document on source_document.document_id = document_link.document_id
    left join lateral (
        select
            fallback_instrument.instrument_id,
            fallback_instrument.primary_symbol,
            fallback_impact.impact_direction,
            fallback_impact.impact_strength
        from event.event_document_link fallback_link
        join event.event_instrument_impact fallback_impact
          on fallback_impact.event_id = fallback_link.event_id
        join ref.instrument fallback_instrument
          on fallback_instrument.instrument_id = fallback_impact.instrument_id
        where fallback_link.document_id = source_document.document_id
          and fallback_link.link_type = 'source'
        order by
            case when fallback_impact.event_id = event_row.event_id then 0 else 1 end,
            fallback_impact.impact_strength desc nulls last,
            fallback_instrument.primary_symbol
        limit 1
    ) document_instrument on true
    left join lateral (
        select
            fallback_theme.code as theme_key,
            fallback_theme.name as theme_name,
            fallback_impact.impact_direction,
            fallback_impact.impact_strength
        from event.event_document_link fallback_link
        join event.event_classification_impact fallback_impact
          on fallback_impact.event_id = fallback_link.event_id
        join ref.classification_node fallback_theme
          on fallback_theme.node_id = fallback_impact.node_id
         and fallback_theme.taxonomy_family = 'internal_theme'
        where fallback_link.document_id = source_document.document_id
          and fallback_link.link_type = 'source'
        order by
            case when fallback_impact.event_id = event_row.event_id then 0 else 1 end,
            fallback_impact.impact_strength desc nulls last,
            fallback_theme.code
        limit 1
    ) document_theme on true
    left join lateral (
        select artifact.artifact_id, artifact.artifact_type, artifact.confidence, invocation.provider
        from ai.extraction_artifact artifact
        left join ai.model_invocation invocation on invocation.invocation_id = artifact.invocation_id
        where artifact.event_id = event_row.event_id
           or artifact.document_id = source_document.document_id
        order by artifact.artifact_id desc
        limit 1
    ) evidence on true
    where event_row.event_at < ({sql_date(as_of_date)} + interval '1 day')
{filters}
),
event_rows as (
    select *
    from filtered_event_rows
    order by event_at desc, event_id desc
    limit {page_limit}
    offset {page_offset}
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'summary',
    json_build_object(
        'event_count', (select count(*)::int from filtered_event_rows),
        'ai_extracted_count', (select count(*) filter (where ai_evidence_id is not null)::int from filtered_event_rows),
        'source_document_count', (select count(distinct raw_source_document_id)::int from filtered_event_rows where raw_source_document_id is not null),
        'themes_represented', (select count(distinct theme_key)::int from filtered_event_rows where theme_key is not null)
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
                    'ai_evidence_type', ai_evidence_type,
                    'ai_evidence_provider', ai_evidence_provider,
                    'ai_evidence_confidence', ai_evidence_confidence,
                    'quality_gate', quality_gate,
                    'related_events',
                    coalesce(
                        (
                            select json_agg(
                                json_build_object(
                                    'event_id', related.event_id,
                                    'title', related.title,
                                    'relation_type', related.relation_type,
                                    'relation_strength', related.relation_strength,
                                    'reason', related.reason,
                                    'symbol', related.primary_symbol,
                                    'theme_key', related.theme_key,
                                    'event_at', related.event_at
                                )
                                order by related.relation_strength desc, related.event_at desc, related.event_id desc
                            )
                            from (
                                select
                                    candidate.event_id,
                                    candidate.title,
                                    candidate.event_at,
                                    candidate.primary_symbol,
                                    candidate.theme_key,
                                    case
                                        when event_rows.raw_source_document_id is not null
                                         and candidate.raw_source_document_id = event_rows.raw_source_document_id
                                            then 'same_source_document'
                                        when candidate.primary_symbol is not null
                                         and candidate.primary_symbol = event_rows.primary_symbol
                                            then 'same_symbol'
                                        else 'same_theme'
                                    end as relation_type,
                                    case
                                        when event_rows.raw_source_document_id is not null
                                         and candidate.raw_source_document_id = event_rows.raw_source_document_id
                                            then 0.9500::numeric
                                        when candidate.primary_symbol is not null
                                         and candidate.primary_symbol = event_rows.primary_symbol
                                            then 0.7600::numeric
                                        else 0.5400::numeric
                                    end as relation_strength,
                                    case
                                        when event_rows.raw_source_document_id is not null
                                         and candidate.raw_source_document_id = event_rows.raw_source_document_id
                                            then '같은 원천 문서에서 파생된 이벤트다.'
                                        when candidate.primary_symbol is not null
                                         and candidate.primary_symbol = event_rows.primary_symbol
                                            then '같은 종목에 연결된 이벤트다.'
                                        else '같은 테마 사이클에 연결된 이벤트다.'
                                    end as reason
                                from filtered_event_rows candidate
                                where candidate.event_id <> event_rows.event_id
                                  and (
                                      (
                                          event_rows.raw_source_document_id is not null
                                      and candidate.raw_source_document_id = event_rows.raw_source_document_id
                                      )
                                      or (
                                          event_rows.primary_symbol is not null
                                      and candidate.primary_symbol = event_rows.primary_symbol
                                      )
                                      or (
                                          event_rows.theme_key is not null
                                      and candidate.theme_key = event_rows.theme_key
                                      )
                                  )
                                order by relation_strength desc, candidate.event_at desc, candidate.event_id desc
                                limit 3
                            ) related
                        ),
                        '[]'::json
                    )
                )
                order by event_at desc, event_id desc
            )
            from event_rows
        ),
        '[]'::json
    )
)::text;"""


def render_frontend_ai_news_cluster_list_state_sql(
    *,
    as_of_date: date,
    theme_key: str | None,
    symbol: str | None,
    page_limit: int = 51,
    page_offset: int = 0,
) -> str:
    _validate_sql_pagination_window(page_limit=page_limit, page_offset=page_offset)
    filters = _ai_news_cluster_sql_filters(theme_key=theme_key, symbol=symbol)
    return f"""-- frontend ai news cluster list state lookup
with raw_cluster_artifacts as (
    select
        artifact.artifact_id,
        artifact.artifact_type,
        artifact.output_json,
        artifact.confidence,
        artifact.created_at,
        artifact.document_id,
        document.external_document_id as representative_source_document_id,
        document.title as representative_source_title,
        invocation.run_id,
        invocation.status as run_status,
        invocation.provider,
        invocation.model_name,
        invocation.reasoning_effort,
        invocation.input_token_count,
        invocation.output_token_count,
        invocation.estimated_cost_usd,
        invocation.request_hash,
        coalesce(artifact.output_json -> 'cluster', '{{}}'::jsonb) as cluster_summary,
        coalesce(artifact.output_json -> 'events', '[]'::jsonb) as cluster_events,
        coalesce(artifact.output_json -> 'audit_notes', '[]'::jsonb) as audit_notes
    from ai.extraction_artifact artifact
    join ai.model_invocation invocation on invocation.invocation_id = artifact.invocation_id
    left join ingest.source_document document on document.document_id = artifact.document_id
    where artifact.artifact_type = 'news_cluster_summary'
),
filtered_cluster_artifacts as (
    select *
    from (
        select
            raw_cluster_artifacts.*,
            row_number() over (
                partition by
                    coalesce(nullif(cluster_summary ->> 'theme_key', ''), artifact_id::text),
                    coalesce(nullif(cluster_summary ->> 'story_key', ''), 'theme')
                order by created_at desc, artifact_id desc
            ) as theme_artifact_rank
        from raw_cluster_artifacts
        where coalesce(nullif(cluster_summary ->> 'as_of_date', '')::date, created_at::date) <= {sql_date(as_of_date)}
    ) ranked_cluster_artifacts
    where theme_artifact_rank = 1
{filters}
),
cluster_artifacts as (
    select *
    from raw_cluster_artifacts
    where artifact_id in (select artifact_id from filtered_cluster_artifacts)
    order by created_at desc, artifact_id desc
    limit {page_limit}
    offset {page_offset}
),
cluster_event_documents as (
    select
        cluster_artifacts.artifact_id,
        source_document.document_id,
        source_document.external_document_id,
        source_document.title,
        source_document.url,
        source_document.published_at
    from cluster_artifacts
    left join lateral jsonb_array_elements(cluster_artifacts.cluster_events) event_item on true
    left join ingest.source_document source_document
      on source_document.external_document_id = event_item ->> 'source_document_id'
    where source_document.document_id is not null
    union
    select
        cluster_artifacts.artifact_id,
        source_document.document_id,
        source_document.external_document_id,
        source_document.title,
        source_document.url,
        source_document.published_at
    from cluster_artifacts
    join ingest.source_document source_document
      on source_document.document_id = cluster_artifacts.document_id
),
cluster_chunk_stats as (
    select
        cluster_event_documents.artifact_id,
        count(distinct chunk.chunk_id)::int as chunk_count,
        count(distinct chunk.chunk_id) filter (where embedding.embedding_id is not null)::int as embedded_chunk_count
    from cluster_event_documents
    left join ai.document_chunk chunk
      on chunk.document_id = cluster_event_documents.document_id
    left join ai.embedding_index embedding
      on embedding.chunk_id = chunk.chunk_id
    group by cluster_event_documents.artifact_id
),
filtered_cluster_document_stats as (
    select
        filtered_cluster_artifacts.artifact_id,
        count(distinct source_document.document_id)::int as source_document_count,
        count(distinct chunk.chunk_id)::int as chunk_count,
        count(distinct chunk.chunk_id) filter (where embedding.embedding_id is not null)::int as embedded_chunk_count
    from filtered_cluster_artifacts
    left join lateral jsonb_array_elements(filtered_cluster_artifacts.cluster_events) event_item on true
    left join ingest.source_document source_document
      on source_document.external_document_id = event_item ->> 'source_document_id'
      or source_document.document_id = filtered_cluster_artifacts.document_id
    left join ai.document_chunk chunk
      on chunk.document_id = source_document.document_id
    left join ai.embedding_index embedding
      on embedding.chunk_id = chunk.chunk_id
    group by filtered_cluster_artifacts.artifact_id
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'summary',
    json_build_object(
        'cluster_count', (select count(*)::int from filtered_cluster_artifacts),
        'clustered_event_count', coalesce(
            (
                select sum(coalesce(nullif(cluster_summary ->> 'event_count', '')::int, jsonb_array_length(cluster_events)))::int
                from filtered_cluster_artifacts
            ),
            0
        ),
        'source_document_count', coalesce((select sum(source_document_count)::int from filtered_cluster_document_stats), 0),
        'chunk_count', coalesce((select sum(chunk_count)::int from filtered_cluster_document_stats), 0),
        'embedded_chunk_count', coalesce((select sum(embedded_chunk_count)::int from filtered_cluster_document_stats), 0),
        'local_rule_cluster_count', (
            select count(*)::int
            from filtered_cluster_artifacts
            where provider in ('local_rules', 'local_deterministic')
        ),
        'estimated_cost_usd', coalesce((select sum(coalesce(estimated_cost_usd, 0)) from filtered_cluster_artifacts), 0.0000)
    ),
    'clusters',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'evidence_id', cluster_artifacts.artifact_id,
                    'title', coalesce(output_json -> 'event' ->> 'title', representative_source_title, 'News cluster summary'),
                    'evidence_type', artifact_type,
                    'created_at', cluster_artifacts.created_at,
                    'confidence', confidence,
                    'cluster_summary', cluster_summary,
                    'cluster_events', cluster_events,
                    'audit_notes', audit_notes,
                    'representative_source_document_id', representative_source_document_id,
                    'source_document_count', coalesce(
                        (
                            select count(distinct document_id)::int
                            from cluster_event_documents
                            where cluster_event_documents.artifact_id = cluster_artifacts.artifact_id
                        ),
                        0
                    ),
                    'chunk_count', coalesce(chunk_stats.chunk_count, 0),
                    'embedded_chunk_count', coalesce(chunk_stats.embedded_chunk_count, 0),
                    'extraction_run',
                    json_build_object(
                        'run_id', run_id,
                        'status', run_status,
                        'provider', provider,
                        'model_id', model_name,
                        'reasoning_effort', reasoning_effort,
                        'input_tokens', input_token_count,
                        'output_tokens', output_token_count,
                        'estimated_cost_usd', estimated_cost_usd,
                        'request_hash', request_hash
                    ),
                    'source_documents',
                    coalesce(
                        (
                            select json_agg(
                                json_build_object(
                                    'source_document_id', source_document.external_document_id,
                                    'title', source_document.title,
                                    'url', source_document.url,
                                    'published_at', source_document.published_at,
                                    'chunk_count', coalesce(document_stats.chunk_count, 0),
                                    'embedded_chunk_count', coalesce(document_stats.embedded_chunk_count, 0)
                                )
                                order by source_document.published_at desc nulls last, source_document.document_id desc
                            )
                            from (
                                select distinct
                                    document_id,
                                    external_document_id,
                                    title,
                                    url,
                                    published_at
                                from cluster_event_documents
                                where cluster_event_documents.artifact_id = cluster_artifacts.artifact_id
                                limit 8
                            ) source_document
                            left join lateral (
                                select
                                    count(distinct chunk.chunk_id)::int as chunk_count,
                                    count(distinct chunk.chunk_id) filter (where embedding.embedding_id is not null)::int as embedded_chunk_count
                                from ai.document_chunk chunk
                                left join ai.embedding_index embedding
                                  on embedding.chunk_id = chunk.chunk_id
                                where chunk.document_id = source_document.document_id
                            ) document_stats on true
                        ),
                        '[]'::json
                    )
                )
                order by cluster_artifacts.created_at desc, cluster_artifacts.artifact_id desc
            )
            from cluster_artifacts
            left join cluster_chunk_stats chunk_stats
              on chunk_stats.artifact_id = cluster_artifacts.artifact_id
        ),
        '[]'::json
    )
)::text;"""


def _ai_news_cluster_sql_filters(theme_key: str | None, symbol: str | None) -> str:
    lines: list[str] = []
    if theme_key:
        lines.append(f"      and cluster_summary ->> 'theme_key' = {sql_literal(theme_key)}")
    if symbol:
        lines.append(
            "      and exists (\n"
            "          select 1\n"
            "          from jsonb_array_elements(cluster_events) event_item\n"
            f"          where upper(coalesce(event_item ->> 'symbol', '')) = {sql_literal(symbol.upper())}\n"
            "      )"
        )
    return "\n".join(lines)


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
           or artifact.document_id = source_document.document_id
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
    outcome_limit: int = 51,
    outcome_offset: int = 0,
) -> str:
    _validate_sql_pagination_window(page_limit=outcome_limit, page_offset=outcome_offset)
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
        recommendation.total_score as recommendation_score,
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
outcome_page as (
    select *
    from outcome_rows
    order by alpha_pct desc nulls last, primary_symbol
    limit {outcome_limit}
    offset {outcome_offset}
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
),
latest_thesis_review as (
    select distinct on (review.thesis_id)
        review.thesis_id,
        review.action,
        review.health_score,
        review.review_date
    from signal.thesis_review review
    join (
        select distinct thesis_id
        from outcome_rows
        where thesis_id is not null
    ) measured_thesis on measured_thesis.thesis_id = review.thesis_id
    order by review.thesis_id, review.review_date desc, review.review_id desc
),
thesis_outcome_rows as (
    select
        thesis_outcome.thesis_id,
        thesis_outcome.alpha_pct,
        thesis_outcome.success_grade,
        thesis_outcome.status
    from selected_run run
    join performance.thesis_outcome thesis_outcome
      on thesis_outcome.measurement_start_date = run.measurement_start_date
     and thesis_outcome.measurement_end_date = run.measurement_end_date
    join (
        select distinct thesis_id
        from outcome_rows
        where thesis_id is not null
    ) measured_thesis on measured_thesis.thesis_id = thesis_outcome.thesis_id
),
review_outcome_mismatch as (
    select count(*)::int as mismatch_count
    from thesis_outcome_rows outcome
    join latest_thesis_review review on review.thesis_id = outcome.thesis_id
    where (
        review.action in ('keep', 'add')
        and coalesce(outcome.alpha_pct, 0) < 0
    )
    or (
        review.action in ('reduce', 'exit')
        and coalesce(outcome.alpha_pct, 0) > 0
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
    'quality_evaluation',
    json_build_object(
        'status',
        case
            when (select count(*) from outcome_rows) = 0 then 'no_outcome_data'
            when (select count(*) from outcome_rows) < 5 then 'insufficient_sample'
            when (select count(*) from coverage_exclusions) > 0 then 'needs_coverage_review'
            when (select mismatch_count from review_outcome_mismatch) > 0 then 'needs_quality_review'
            when (
                (select count(*) filter (where recommendation_score >= 0.7) from outcome_rows) > 0
                and coalesce((select avg(alpha_pct) from outcome_rows where recommendation_score >= 0.7), 0) < coalesce((select avg(alpha_pct) from outcome_rows), 0)
            ) then 'needs_quality_review'
            when coalesce((select avg(alpha_pct) from outcome_rows), 0) > 0 then 'positive_alignment'
            else 'reviewable'
        end,
        'sample_size_status',
        case
            when (select count(*) from outcome_rows) = 0 then 'no_outcome_data'
            when (select count(*) from outcome_rows) < 5 then 'insufficient_sample'
            else 'enough_sample'
        end,
        'score_outcome_alignment',
        case
            when (select count(*) from outcome_rows) = 0 then 'no_outcome_data'
            when (select count(*) from outcome_rows) < 5 then 'insufficient_sample'
            when (select count(*) filter (where recommendation_score >= 0.7) from outcome_rows) = 0 then 'no_high_score_sample'
            when coalesce((select avg(alpha_pct) from outcome_rows where recommendation_score >= 0.7), 0) >= coalesce((select avg(alpha_pct) from outcome_rows), 0) then 'aligned'
            else 'misaligned'
        end,
        'review_outcome_mismatch_count', (select mismatch_count from review_outcome_mismatch),
        'measured_recommendation_count', (select count(*)::int from outcome_rows),
        'measured_thesis_count', (select count(distinct thesis_id)::int from outcome_rows where thesis_id is not null),
        'average_alpha', (select avg(alpha_pct) from outcome_rows),
        'hit_rate',
        case
            when (select count(*) from outcome_rows) = 0 then null
            else ((select count(*) filter (where outcome_label in ('outperform', 'positive')) from outcome_rows)::numeric / (select count(*) from outcome_rows)::numeric)
        end,
        'high_score_recommendation_count', (select count(*) filter (where recommendation_score >= 0.7)::int from outcome_rows),
        'high_score_average_alpha', (select avg(alpha_pct) from outcome_rows where recommendation_score >= 0.7),
        'coverage_exclusion_count', (select count(*)::int from coverage_exclusions)
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
            from outcome_page
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
        recommendation.batch_id,
        recommendation.instrument_id,
        instrument.primary_symbol,
        batch.as_of_date,
        batch.market_code,
        batch.strategy_name,
        batch.horizon_type,
        batch.universe_version,
        batch.source_run_id as recommendation_source_run_id,
        recommendation.action,
        recommendation.rank_position,
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
),
recommendation_event_anchor as (
    select
        event_row.event_id,
        artifact.artifact_id
    from selected_recommendation recommendation
    join event.event_instrument_impact impact
      on impact.instrument_id = recommendation.instrument_id
    join event.event event_row
      on event_row.event_id = impact.event_id
    left join event.event_document_link document_link
      on document_link.event_id = event_row.event_id
     and document_link.link_type = 'source'
    left join lateral (
        select extraction_artifact.artifact_id
        from ai.extraction_artifact extraction_artifact
        where extraction_artifact.event_id = event_row.event_id
           or extraction_artifact.document_id = document_link.document_id
        order by extraction_artifact.artifact_id desc
        limit 1
    ) artifact on true
    where event_row.event_at < (recommendation.as_of_date + interval '1 day')
    order by
        case when artifact.artifact_id is not null then 0 else 1 end,
        event_row.event_at desc,
        event_row.event_id desc
    limit 1
),
recommendation_evidence_anchor as (
    select
        case
            when artifact_id is not null then 'ai-evidence-' || artifact_id::text
            else 'event-' || event_id::text
        end as evidence_id
    from recommendation_event_anchor
),
market_feature_component_map (component_name, feature_code) as (
    values
        ('momentum_score', 'return_since_first_observation'),
        ('short_term_score', 'return_1d')
),
market_feature_provenance as (
    select
        feature_map.component_name,
        feature_map.feature_code,
        definition.feature_name,
        definition.description,
        feature.feature_value,
        feature.zscore,
        feature.as_of_date,
        feature.source_run_id,
        feature.evidence_json
    from market_feature_component_map feature_map
    cross join selected_recommendation recommendation
    left join signal.instrument_feature_value feature
      on feature.instrument_id = recommendation.instrument_id
     and feature.as_of_date = recommendation.as_of_date
     and feature.feature_code = feature_map.feature_code
    left join signal.feature_definition definition
      on definition.feature_code = feature_map.feature_code
),
strategy_universe_provenance as (
    select
        universe_batch.universe_batch_id,
        member.rank_position,
        (
            select count(*)::integer
            from signal.strategy_universe_member counted_member
            where counted_member.universe_batch_id = universe_batch.universe_batch_id
        ) as universe_member_count,
        member.selection_score,
        member.latest_trade_date,
        member.observation_count,
        member.inclusion_reason,
        universe_batch.selection_rule,
        universe_batch.source_run_id
    from selected_recommendation recommendation
    join signal.strategy_universe_batch universe_batch
      on universe_batch.as_of_date = recommendation.as_of_date
     and universe_batch.market_code = recommendation.market_code
     and universe_batch.strategy_name = recommendation.strategy_name
     and universe_batch.horizon_type = recommendation.horizon_type
     and universe_batch.universe_version is not distinct from recommendation.universe_version
    join signal.strategy_universe_member member
      on member.universe_batch_id = universe_batch.universe_batch_id
     and member.instrument_id = recommendation.instrument_id
    order by universe_batch.universe_batch_id desc
    limit 1
),
macro_flow_provenance as (
    select
        count(*)::integer as propagated_impact_count,
        max(source_run_id) as source_run_id,
        json_agg(
            json_build_object(
                'event_id', event_id,
                'title', title,
                'event_at', event_at,
                'theme_key', theme_key,
                'theme_name', theme_name,
                'impact_direction', impact_direction,
                'impact_strength', impact_strength,
                'confidence', confidence,
                'exposure_weight', exposure_weight
            )
            order by event_at desc, event_id desc, theme_key
        ) as recent_flows
    from (
        select
            propagated_impact.event_id,
            event_row.title,
            event_row.event_at,
            node.code as theme_key,
            node.name as theme_name,
            propagated_impact.impact_direction,
            propagated_impact.impact_strength,
            propagated_impact.confidence,
            propagated_impact.exposure_weight,
            propagated_impact.source_run_id
        from selected_recommendation recommendation
        join signal.propagated_instrument_impact propagated_impact
          on propagated_impact.instrument_id = recommendation.instrument_id
        join event.event event_row on event_row.event_id = propagated_impact.event_id
        join ref.classification_node node on node.node_id = propagated_impact.node_id
        where event_row.event_at < (recommendation.as_of_date + interval '1 day')
        order by event_row.event_at desc, event_row.event_id desc, node.code
        limit 8
    ) flow_rows
),
score_component_rows as (
    select
        component.component_name,
        component.component_score,
        component.component_weight,
        case
            when component.component_name in ('cycle_score', 'event_quality', 'event_intensity', 'theme_mapping')
                then coalesce(
                    (select evidence_id from recommendation_evidence_anchor),
                    'cycle-state-' || recommendation.primary_symbol || '-' || recommendation.as_of_date::text
                )
            when component.component_name in ('momentum_score', 'short_term_score')
                then 'market-feature-' || lower(recommendation.primary_symbol) || '-' || recommendation.as_of_date::text || '-' || coalesce(feature.feature_code, feature_map.feature_code)
            when component.component_name = 'rank_score'
                then 'universe-rank-' || lower(recommendation.primary_symbol) || '-' || recommendation.as_of_date::text || coalesce('-' || (select universe_batch_id::text from strategy_universe_provenance), '')
            when component.component_name = 'macro_flow_score'
                then 'macro-flow-' || lower(recommendation.primary_symbol) || '-' || recommendation.as_of_date::text
            else component.component_name
        end as evidence_id,
        case
            when component.component_name in ('cycle_score', 'event_quality', 'event_intensity', 'theme_mapping')
                then json_strip_nulls(json_build_object(
                    'source_type', 'event_or_ai_evidence',
                    'label', '원천 이벤트/AI 근거',
                    'evidence_id', (select evidence_id from recommendation_evidence_anchor)
                ))
            when component.component_name in ('momentum_score', 'short_term_score')
                then json_strip_nulls(json_build_object(
                    'source_type', 'market_feature',
                    'label', '가격 feature snapshot',
                    'feature_code', coalesce(feature.feature_code, feature_map.feature_code),
                    'feature_name', feature.feature_name,
                    'description', feature.description,
                    'feature_value', feature.feature_value,
                    'zscore', feature.zscore,
                    'as_of_date', feature.as_of_date,
                    'source_run_id', feature.source_run_id,
                    'evidence_json', feature.evidence_json
                ))
            when component.component_name = 'rank_score'
                then json_strip_nulls(json_build_object(
                    'source_type', 'strategy_universe_rank',
                    'label', '전략 유니버스 순위',
                    'universe_batch_id', (select universe_batch_id from strategy_universe_provenance),
                    'rank_position', coalesce((select rank_position from strategy_universe_provenance), recommendation.rank_position),
                    'universe_member_count', (select universe_member_count from strategy_universe_provenance),
                    'selection_score', (select selection_score from strategy_universe_provenance),
                    'selection_rule', (select selection_rule from strategy_universe_provenance),
                    'latest_trade_date', (select latest_trade_date from strategy_universe_provenance),
                    'observation_count', (select observation_count from strategy_universe_provenance),
                    'inclusion_reason', (select inclusion_reason from strategy_universe_provenance),
                    'source_run_id', coalesce((select source_run_id from strategy_universe_provenance), recommendation.recommendation_source_run_id)
                ))
            when component.component_name = 'macro_flow_score'
                then json_strip_nulls(json_build_object(
                    'source_type', 'macro_flow_propagation',
                    'label', '상위 흐름 전파 근거',
                    'source_run_id', (select source_run_id from macro_flow_provenance),
                    'evidence_json', json_build_object(
                        'as_of_date', recommendation.as_of_date,
                        'propagated_impact_count', coalesce((select propagated_impact_count from macro_flow_provenance), 0),
                        'recent_flows', coalesce((select recent_flows from macro_flow_provenance), '[]'::json)
                    )
                ))
            else json_build_object(
                'source_type', 'score_component',
                'label', '저장된 점수 구성요소'
            )
        end as provenance
    from signal.recommendation_score_component component
    join selected_recommendation recommendation
      on recommendation.recommendation_id = component.recommendation_id
    left join market_feature_component_map feature_map
      on feature_map.component_name = component.component_name
    left join market_feature_provenance feature
      on feature.component_name = component.component_name
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
                    'component', component_name,
                    'value', component_score,
                    'weight', component_weight,
                    'evidence_id', evidence_id,
                    'provenance', provenance
                )
                order by component_name
            )
            from score_component_rows
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


def render_frontend_recommendation_list_state_sql(
    *,
    as_of_date: date | None,
    page_limit: int = 51,
    page_offset: int = 0,
) -> str:
    _validate_sql_pagination_window(page_limit=page_limit, page_offset=page_offset)
    target_date_sql = sql_date(as_of_date) if as_of_date is not None else "current_date"
    return f"""-- frontend recommendation list state lookup
with target_date as (
    select {target_date_sql}::date as as_of_date
),
latest_batch as (
    select batch.*
    from signal.recommendation_batch batch
    join target_date target on batch.as_of_date <= target.as_of_date
    where batch.strategy_name = {sql_literal(DEFAULT_STRATEGY_NAME)}
    order by batch.as_of_date desc, batch.batch_id desc
    limit 1
),
recommendation_base as (
    select
        recommendation.recommendation_id,
        recommendation.instrument_id,
        recommendation.thesis_id,
        recommendation.bucket,
        recommendation.action,
        recommendation.rank_position,
        recommendation.total_score,
        recommendation.recommended_weight,
        recommendation.status,
        batch.as_of_date,
        batch.strategy_name,
        batch.horizon_type,
        batch.universe_version,
        instrument.primary_symbol,
        instrument.name
    from latest_batch batch
    join signal.recommendation recommendation on recommendation.batch_id = batch.batch_id
    join ref.instrument instrument on instrument.instrument_id = recommendation.instrument_id
),
latest_outcome as (
    select distinct on (outcome.recommendation_id)
        outcome.recommendation_id,
        outcome.measurement_end_date,
        outcome.outcome_label,
        outcome.alpha_pct
    from performance.recommendation_outcome outcome
    join recommendation_base recommendation on recommendation.recommendation_id = outcome.recommendation_id
    order by outcome.recommendation_id, outcome.measurement_end_date desc, outcome.outcome_id desc
),
score_component_counts as (
    select
        component.recommendation_id,
        count(*)::int as score_component_count,
        count(*) filter (
            where component.component_name in ('cycle_score', 'event_quality', 'event_intensity', 'theme_mapping')
        )::int as ai_or_event_component_count,
        count(*) filter (
            where component.component_name in ('momentum_score', 'short_term_score', 'rank_score')
        )::int as market_or_rank_component_count
    from signal.recommendation_score_component component
    join recommendation_base recommendation on recommendation.recommendation_id = component.recommendation_id
    group by component.recommendation_id
),
recommendation_rows as (
    select
        recommendation.*,
        coalesce(component_count.score_component_count, 0) as score_component_count,
        coalesce(component_count.ai_or_event_component_count, 0) as ai_or_event_component_count,
        coalesce(component_count.market_or_rank_component_count, 0) as market_or_rank_component_count,
        case
            when evidence.artifact_id is not null then 'ai-evidence-' || evidence.artifact_id::text
            when evidence.event_id is not null then 'event-' || evidence.event_id::text
            else null
        end as primary_evidence_id,
        outcome.measurement_end_date,
        coalesce(outcome.outcome_label, 'unmeasured') as outcome_label,
        outcome.alpha_pct,
        case
            when recommendation.thesis_id is null then 'blocked'
            when coalesce(component_count.score_component_count, 0) = 0 then 'blocked'
            when coalesce(component_count.ai_or_event_component_count, 0) = 0 then 'needs_evidence'
            else 'ready_for_human_review'
        end as quality_status
    from recommendation_base recommendation
    left join score_component_counts component_count
      on component_count.recommendation_id = recommendation.recommendation_id
    left join latest_outcome outcome
      on outcome.recommendation_id = recommendation.recommendation_id
    left join lateral (
        select
            event_row.event_id,
            artifact.artifact_id
        from event.event_instrument_impact impact
        join event.event event_row on event_row.event_id = impact.event_id
        left join event.event_document_link document_link
          on document_link.event_id = event_row.event_id
         and document_link.link_type = 'source'
        left join lateral (
            select extraction_artifact.artifact_id
            from ai.extraction_artifact extraction_artifact
            where extraction_artifact.event_id = event_row.event_id
               or extraction_artifact.document_id = document_link.document_id
            order by extraction_artifact.artifact_id desc
            limit 1
        ) artifact on true
        where impact.instrument_id = recommendation.instrument_id
          and event_row.event_at < (recommendation.as_of_date + interval '1 day')
        order by
            case when artifact.artifact_id is not null then 0 else 1 end,
            event_row.event_at desc,
            event_row.event_id desc
        limit 1
    ) evidence on true
),
recommendation_page as (
    select *
    from recommendation_rows
    order by rank_position, recommendation_id
    limit {page_limit}
    offset {page_offset}
)
select json_build_object(
    'as_of_date', coalesce((select as_of_date::text from latest_batch), (select as_of_date::text from target_date)),
    'strategy_name', coalesce((select strategy_name from latest_batch), {sql_literal(DEFAULT_STRATEGY_NAME)}),
    'horizon_type', coalesce((select horizon_type from latest_batch), 'long_term'),
    'universe_version', coalesce((select universe_version from latest_batch), 'unknown'),
    'recommendation_count', (select count(*)::int from recommendation_rows),
    'summary',
    json_build_object(
        'active_count', (select count(*) filter (where status = 'active')::int from recommendation_rows),
        'reviewable_count', (select count(*) filter (where quality_status = 'ready_for_human_review')::int from recommendation_rows),
        'blocked_count', (select count(*) filter (where quality_status <> 'ready_for_human_review')::int from recommendation_rows),
        'measured_count', (select count(*) filter (where outcome_label <> 'unmeasured')::int from recommendation_rows),
        'linked_thesis_count', (select count(*) filter (where thesis_id is not null)::int from recommendation_rows),
        'ai_or_event_evidence_count', (select count(*) filter (where ai_or_event_component_count > 0 or primary_evidence_id is not null)::int from recommendation_rows),
        'average_score', (select avg(total_score) from recommendation_rows)
    ),
    'recommendations',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'recommendation_id', recommendation_id,
                    'symbol', primary_symbol,
                    'name', name,
                    'instrument_id', instrument_id,
                    'as_of_date', as_of_date,
                    'rank_position', rank_position,
                    'bucket', bucket,
                    'action', action,
                    'status', status,
                    'score', total_score,
                    'recommended_weight', recommended_weight,
                    'linked_thesis_id', thesis_id,
                    'evidence',
                    json_build_object(
                        'score_component_count', score_component_count,
                        'ai_or_event_component_count', ai_or_event_component_count,
                        'market_or_rank_component_count', market_or_rank_component_count,
                        'quality_status', quality_status,
                        'primary_evidence_id', primary_evidence_id
                    ),
                    'outcome',
                    json_build_object(
                        'measurement_end_date', measurement_end_date,
                        'label', outcome_label,
                        'alpha', alpha_pct
                    )
                )
                order by rank_position, recommendation_id
            )
            from recommendation_page
        ),
        '[]'::json
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
        thesis.exit_conditions,
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
        coalesce(
            (select primary_symbol from selected_thesis),
            'UNKNOWN'
        ) || ' 투자 논리는 주문이 아니라 추천, 사이클, 가격 근거를 함께 검토하기 위한 장기 기록이다.',
        coalesce((select entry_conditions from selected_thesis), ''),
        coalesce((select exit_conditions from selected_thesis), '')
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
        'reviewed_at', (select review_date from latest_review),
        'summary', coalesce((select summary from latest_review), ''),
        'change_notes', coalesce((select change_notes from latest_review), ''),
        'next_review_date', (select next_review_date from latest_review)
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
       or ('event-' || event_row.event_id::text) = {identifier_literal}
       or event_row.dedupe_key = {identifier_literal}
       or document.external_document_id = {identifier_literal}
       or document.external_document_id = regexp_replace({identifier_literal}, '^source-document-', '')
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
    select candidate.*
    from selected_event_candidates candidate
    left join lateral (
        select impact.event_id
        from event.event_instrument_impact impact
        where impact.event_id = candidate.event_id
        limit 1
    ) selected_instrument_impact on true
    left join lateral (
        select impact.event_id
        from event.event_classification_impact impact
        where impact.event_id = candidate.event_id
        limit 1
    ) selected_classification_impact on true
    order by
        case when selected_instrument_impact.event_id is not null then 0 else 1 end,
        case when selected_classification_impact.event_id is not null then 0 else 1 end,
        candidate.event_at desc,
        candidate.event_id desc
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
        (select output_json #>> '{{event,title}}' from selected_artifact),
        (select title from selected_event),
        (select artifact_type from selected_artifact),
        ''
    ),
    'evidence_type',
    case
        when (select artifact_type from selected_artifact) in ('news_event_candidate', 'news_cluster_summary')
            then (select artifact_type from selected_artifact)
        else coalesce(
            (select output_json #>> '{{event,event_type}}' from selected_artifact),
            (select event_type from selected_event),
            (select artifact_type from selected_artifact),
            'source_document_event'
        )
    end,
    'event_at', coalesce((select output_json #>> '{{event,event_at}}' from selected_artifact), (select event_at::text from selected_event)),
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
    'news_candidate',
    case
        when (select artifact_type from selected_artifact) = 'news_event_candidate'
            then coalesce((select output_json -> 'candidate' from selected_artifact), '{{}}'::jsonb)
        else '{{}}'::jsonb
    end,
    'retrieval_context_summary',
    case
        when (select artifact_type from selected_artifact) = 'news_event_candidate'
            then coalesce((select output_json -> 'retrieval_context_summary' from selected_artifact), '{{}}'::jsonb)
        else '{{}}'::jsonb
    end,
    'cluster_summary', coalesce((select output_json -> 'cluster' from selected_artifact), '{{}}'::jsonb),
    'cluster_events', coalesce((select output_json -> 'events' from selected_artifact), '[]'::jsonb),
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
       or document.external_document_id = regexp_replace({identifier_literal}, '^source-document-', '')
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
    select distinct on (artifact.artifact_id)
        artifact.artifact_id,
        coalesce(event_row.event_type, artifact.artifact_type) as evidence_type,
        coalesce(event_row.title, artifact.artifact_type) as title
    from selected_document document
    join ai.extraction_artifact artifact on artifact.document_id = document.document_id
    left join event.event_document_link document_link
      on document_link.document_id = artifact.document_id
     and document_link.link_type = 'source'
    left join event.event event_row on event_row.event_id = coalesce(artifact.event_id, document_link.event_id)
    left join lateral (
        select impact.event_id
        from event.event_instrument_impact impact
        where impact.event_id = event_row.event_id
        limit 1
    ) linked_instrument_impact on true
    left join lateral (
        select impact.event_id
        from event.event_classification_impact impact
        where impact.event_id = event_row.event_id
        limit 1
    ) linked_classification_impact on true
    order by
        artifact.artifact_id desc,
        case when linked_instrument_impact.event_id is not null then 0 else 1 end,
        case when linked_classification_impact.event_id is not null then 0 else 1 end,
        event_row.event_at desc nulls last,
        event_row.event_id desc
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
    fallback_id = str(run.get("job_id") or run.get("pipeline_name") or "unknown").replace("_", "-")
    return {
        "pipeline_name": str(run.get("pipeline_name") or "unknown"),
        "job_id": str(run.get("job_id") or ""),
        "domain": str(run.get("domain") or ""),
        "cadence": str(run.get("cadence") or ""),
        "expected_after_local": str(run.get("expected_after_local") or ""),
        "stale_after_hours": int(run.get("stale_after_hours") or 0),
        "artifact_policy": str(run.get("artifact_policy") or ""),
        "latest_status": str(run.get("latest_status") or run.get("status") or "unknown"),
        "health_status": str(run.get("health_status") or "unknown"),
        "latest_run_id": _opaque_id("pipeline-run", run.get("latest_run_id") or run.get("run_id"), fallback_id),
        "finished_at": _timestamp(run.get("finished_at") or run.get("ended_at")),
    }


def _build_freshness_payload(freshness: dict[str, Any]) -> dict[str, Any]:
    observation_date = freshness.get("latest_observation_date")
    return {
        "dataset": str(freshness.get("dataset") or "unknown"),
        "status": str(freshness.get("status") or "unknown"),
        "latest_observation_date": str(observation_date) if observation_date is not None else "",
    }


def _build_stock_list_item_payload(item: dict[str, Any]) -> dict[str, Any]:
    symbol = str(item.get("symbol") or "UNKNOWN").upper()
    return {
        "symbol": symbol,
        "name": str(item.get("name") or ""),
        "instrument_id": _opaque_id("instrument", item.get("instrument_id"), symbol.lower()),
        "market_code": str(item.get("market_code") or "US"),
        "currency_code": str(item.get("currency_code") or "USD"),
        "latest_price": _build_stock_price_payload(_as_dict(item.get("latest_price"))),
        "data_coverage": _build_stock_coverage_payload(_as_dict(item.get("data_coverage"))),
        "recommendation": _build_stock_recommendation_payload(_as_dict(item.get("recommendation"))),
        "position": _build_stock_position_payload(_as_dict(item.get("position"))),
    }


def _build_stock_price_payload(price: dict[str, Any]) -> dict[str, Any]:
    return {
        "trade_date": str(price.get("trade_date") or ""),
        "open": _number(price.get("open")),
        "high": _number(price.get("high")),
        "low": _number(price.get("low")),
        "close": _number(price.get("close")),
        "adjusted_close": _number(price.get("adjusted_close")),
        "volume": int(price.get("volume") or 0),
        "change_pct": _number(price.get("change_pct")),
    }


def _build_stock_coverage_payload(coverage: dict[str, Any]) -> dict[str, Any]:
    return {
        "bar_count": int(coverage.get("bar_count") or 0),
        "first_trade_date": str(coverage.get("first_trade_date") or ""),
        "last_trade_date": str(coverage.get("last_trade_date") or ""),
    }


def _build_stock_recommendation_payload(recommendation: dict[str, Any]) -> dict[str, Any] | None:
    raw_id = recommendation.get("recommendation_id")
    if raw_id is None:
        return None
    return {
        "recommendation_id": _opaque_id("recommendation", raw_id, None),
        "linked_thesis_id": _opaque_id("thesis", recommendation.get("linked_thesis_id"), None)
        if recommendation.get("linked_thesis_id") is not None
        else None,
        "action": str(recommendation.get("action") or "monitor"),
        "score": _number(recommendation.get("score")),
        "status": str(recommendation.get("status") or "unknown"),
        "as_of_date": str(recommendation.get("as_of_date") or ""),
    }


def _build_stock_position_payload(position: dict[str, Any]) -> dict[str, Any] | None:
    if position.get("snapshot_date") is None:
        return None
    return {
        "portfolio_name": str(position.get("portfolio_name") or DEFAULT_PORTFOLIO_NAME),
        "snapshot_date": str(position.get("snapshot_date") or ""),
        "quantity": _number(position.get("quantity")),
        "weight": _number(position.get("weight")),
        "market_price": _number(position.get("market_price")),
        "market_value": _number(position.get("market_value")),
        "linked_thesis_id": _opaque_id("thesis", position.get("linked_thesis_id"), None)
        if position.get("linked_thesis_id") is not None
        else None,
    }


def _build_stock_price_bar_payload(bar: dict[str, Any]) -> dict[str, Any]:
    return {
        "trade_date": str(bar.get("trade_date") or ""),
        "open": _number(bar.get("open")),
        "high": _number(bar.get("high")),
        "low": _number(bar.get("low")),
        "close": _number(bar.get("close")),
        "adjusted_close": _number(bar.get("adjusted_close")),
        "volume": int(bar.get("volume") or 0),
    }


def _build_stock_detail_summary_payload(summary: dict[str, Any], price_bars: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "bar_count": int(summary.get("bar_count") or len(price_bars)),
        "first_trade_date": str(summary.get("first_trade_date") or ""),
        "last_trade_date": str(summary.get("last_trade_date") or ""),
        "low_close": _number(summary.get("low_close")),
        "high_close": _number(summary.get("high_close")),
        "return_pct": _number(summary.get("return_pct")),
    }


def _build_neighborhood_story_group_payloads(
    *,
    raw_events: list[Any],
    raw_chunks: list[Any],
) -> list[dict[str, Any]]:
    events = [item for item in raw_events if isinstance(item, dict)]
    chunks = [item for item in raw_chunks if isinstance(item, dict)]
    chunks_by_document_id: dict[str, list[dict[str, Any]]] = {}
    for chunk in chunks:
        document_key = _raw_document_key(chunk.get("document_id"))
        if document_key:
            chunks_by_document_id.setdefault(document_key, []).append(chunk)

    groups: dict[str, dict[str, Any]] = {}
    for event in events:
        group_key = _story_group_key(event)
        document_key = _raw_document_key(event.get("document_id"))
        current = groups.get(group_key)
        if current is None:
            current = {
                "group_key": group_key,
                "title": str(event.get("title") or "뉴스 이야기"),
                "events": [],
                "raw_document_keys": set(),
                "source_document_ids": set(),
                "theme_keys": set(),
                "chunks": [],
                "latest_event_at": "",
                "basis": set(),
            }
            groups[group_key] = current

        current["events"].append(event)
        event_time = _timestamp(event.get("event_at"))
        current["latest_event_at"] = max(str(current["latest_event_at"]), event_time)
        title = str(event.get("title") or "")
        if _story_title_signature(title):
            current["basis"].add("same_title_signature")
        if document_key:
            current["raw_document_keys"].add(document_key)
            current["source_document_ids"].add(_opaque_source_document_id_for_event(event))
            current["chunks"].extend(chunks_by_document_id.get(document_key, []))
            current["basis"].add("same_source_document")
        theme_key = str(event.get("theme_key") or "")
        if theme_key and theme_key not in {"UNKNOWN", "UNCLASSIFIED"}:
            current["theme_keys"].add(theme_key)
            current["basis"].add("same_theme")

    payloads: list[dict[str, Any]] = []
    for index, group in enumerate(
        sorted(groups.values(), key=lambda item: (str(item["latest_event_at"]), len(item["events"])), reverse=True),
        start=1,
    ):
        raw_events_for_group = sorted(
            group["events"],
            key=lambda item: (_timestamp(item.get("event_at")), str(item.get("event_id") or "")),
            reverse=True,
        )
        unique_chunks = _unique_raw_chunks(group["chunks"])
        source_document_ids = sorted(str(item) for item in group["source_document_ids"] if item)
        theme_keys = sorted(str(item) for item in group["theme_keys"] if item)
        basis = sorted(str(item) for item in group["basis"] if item)
        event_count = len(raw_events_for_group)
        chunk_count = len(unique_chunks)
        payloads.append(
            {
                "story_id": f"story-{index}",
                "story_key": str(group["group_key"]),
                "title": str(group["title"]),
                "confidence": _story_group_confidence(
                    event_count=event_count,
                    source_document_count=len(source_document_ids),
                    chunk_count=chunk_count,
                    basis_count=len(basis),
                ),
                "event_count": event_count,
                "source_document_count": len(source_document_ids),
                "linked_chunk_count": chunk_count,
                "latest_event_at": str(group["latest_event_at"]),
                "theme_keys": theme_keys,
                "source_document_ids": source_document_ids,
                "linked_chunk_ids": [
                    _opaque_id("chunk", chunk.get("chunk_id"), "unknown")
                    for chunk in unique_chunks[:6]
                ],
                "basis": basis,
                "relation_reasons": _story_group_relation_reasons(
                    event_count=event_count,
                    source_document_count=len(source_document_ids),
                    chunk_count=chunk_count,
                    theme_keys=theme_keys,
                    basis=basis,
                ),
                "events": [_build_neighborhood_event_payload(item) for item in raw_events_for_group[:4]],
            }
        )

    return payloads[:12]


def _story_group_key(event: dict[str, Any]) -> str:
    signature = _story_title_signature(str(event.get("title") or ""))
    if signature:
        return f"title:{signature}"
    document_key = _raw_document_key(event.get("document_id"))
    if document_key:
        return f"document:{document_key}"
    return f"event:{event.get('event_id') or 'unknown'}"


def _story_title_signature(title: str) -> str:
    tokens = [
        token
        for token in re.findall(r"[a-z0-9가-힣]+", title.lower())
        if len(token) >= 3 and token not in _STORY_GROUP_STOP_WORDS
    ]
    if not tokens:
        return ""
    deduped_tokens = list(dict.fromkeys(tokens))
    return "-".join(deduped_tokens[:8])


def _raw_document_key(value: Any) -> str:
    text = str(value or "").strip()
    return text


def _opaque_source_document_id_for_event(event: dict[str, Any]) -> str:
    source_document_id = event.get("external_document_id") or event.get("document_id")
    return (
        _opaque_id("source-document", source_document_id, "unknown")
        if source_document_id is not None
        else "source-document-unknown"
    )


def _unique_raw_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for chunk in chunks:
        chunk_key = str(chunk.get("chunk_id") or "")
        if not chunk_key or chunk_key in seen:
            continue
        seen.add(chunk_key)
        unique.append(chunk)
    return sorted(unique, key=lambda item: (str(item.get("document_id") or ""), int(item.get("chunk_index") or 0)))


def _story_group_confidence(
    *,
    event_count: int,
    source_document_count: int,
    chunk_count: int,
    basis_count: int,
) -> float:
    confidence = 0.52
    if event_count > 1:
        confidence += 0.18
    if source_document_count > 0:
        confidence += 0.08
    if chunk_count > 0:
        confidence += 0.10
    if basis_count > 1:
        confidence += 0.05
    return round(min(confidence, 0.93), 4)


def _story_group_relation_reasons(
    *,
    event_count: int,
    source_document_count: int,
    chunk_count: int,
    theme_keys: list[str],
    basis: list[str],
) -> list[str]:
    reasons: list[str] = []
    if "same_title_signature" in basis:
        reasons.append("제목의 핵심 단어가 같은 이야기 후보로 묶였다.")
    if source_document_count > 0:
        reasons.append(f"원천 문서 {source_document_count}개가 이 이야기의 근거로 연결되어 있다.")
    if chunk_count > 0:
        reasons.append(f"검색/RAG에 사용할 문서 청크 {chunk_count}개가 붙어 있다.")
    if event_count > 1:
        reasons.append(f"같은 이야기 후보에 이벤트 {event_count}개가 연결되어 있다.")
    if theme_keys:
        reasons.append(f"공통 테마: {', '.join(theme_keys[:3])}.")
    return reasons or ["현재는 단일 이벤트 기준의 이야기 후보로 표시한다."]


def _build_neighborhood_instrument_payload(instrument: dict[str, Any], *, fallback_symbol: str) -> dict[str, Any]:
    symbol = str(instrument.get("primary_symbol") or fallback_symbol).upper()
    instrument_id = instrument.get("instrument_id")
    return {
        "symbol": symbol,
        "instrument_id": _opaque_id("instrument", instrument_id, symbol.lower()),
        "name": str(instrument.get("name") or ""),
        "market_code": str(instrument.get("market_code") or "US"),
        "found": instrument_id is not None,
    }


def _build_neighborhood_theme_payload(theme: dict[str, Any]) -> dict[str, Any]:
    source_document_id = theme.get("source_document_id")
    return {
        "theme_key": str(theme.get("code") or "UNCLASSIFIED"),
        "theme_name": str(theme.get("name") or "Unclassified"),
        "taxonomy_family": str(theme.get("taxonomy_family") or ""),
        "node_type": str(theme.get("node_type") or ""),
        "membership_type": str(theme.get("membership_type") or ""),
        "confidence": _number(theme.get("confidence")),
        "source_document_id": _opaque_id("source-document", source_document_id, None)
        if source_document_id is not None
        else None,
    }


def _build_neighborhood_theme_edge_payload(edge: dict[str, Any]) -> dict[str, Any]:
    return {
        "edge_id": _opaque_id("classification-edge", edge.get("edge_id"), "unknown"),
        "parent_theme_key": str(edge.get("parent_code") or "UNCLASSIFIED"),
        "child_theme_key": str(edge.get("child_code") or "UNCLASSIFIED"),
        "relation_type": str(edge.get("relation_type") or "related"),
        "weight": _number(edge.get("weight")),
    }


def _build_neighborhood_event_payload(event: dict[str, Any]) -> dict[str, Any]:
    source_document_id = event.get("external_document_id") or event.get("document_id")
    impact_direction = event.get("instrument_impact_direction") or event.get("theme_impact_direction")
    impact_score = event.get("instrument_impact_strength") or event.get("theme_impact_strength")
    return {
        "event_id": _opaque_id("event", event.get("event_id"), "unknown"),
        "title": str(event.get("title") or ""),
        "event_type": str(event.get("event_type") or "unknown"),
        "event_at": _timestamp(event.get("event_at")),
        "theme_key": str(event.get("theme_key") or "UNCLASSIFIED"),
        "impact_direction": str(impact_direction or "unknown"),
        "impact_score": _number(impact_score),
        "source_document_id": _opaque_id("source-document", source_document_id, None)
        if source_document_id is not None
        else None,
    }


def _build_neighborhood_ai_artifact_payload(artifact: dict[str, Any]) -> dict[str, Any]:
    return {
        "evidence_id": _opaque_id("ai-evidence", artifact.get("artifact_id"), "unknown"),
        "evidence_type": str(artifact.get("artifact_type") or "unknown"),
        "event_id": _opaque_id("event", artifact.get("event_id"), None)
        if artifact.get("event_id") is not None
        else None,
        "source_document_id": _opaque_id("source-document", artifact.get("document_id"), None)
        if artifact.get("document_id") is not None
        else None,
        "provider": str(artifact.get("provider") or "unknown"),
        "model_id": str(artifact.get("model_name") or "unknown"),
        "status": str(artifact.get("status") or "unknown"),
        "confidence": _number(artifact.get("confidence")),
        "estimated_cost_usd": _number(artifact.get("estimated_cost_usd")),
    }


def _build_neighborhood_evidence_chunk_payload(chunk: dict[str, Any]) -> dict[str, Any]:
    embedding_id = chunk.get("embedding_id")
    chunk_metadata = _as_dict(chunk.get("chunk_metadata"))
    source_url = str(chunk.get("source_url") or "")
    return {
        "chunk_id": _opaque_id("chunk", chunk.get("chunk_id"), "unknown"),
        "source_document_id": _opaque_id("source-document", chunk.get("document_id"), "unknown"),
        "chunk_index": int(chunk.get("chunk_index") or 0),
        "text_preview": str(chunk.get("text_preview") or ""),
        "token_count": int(chunk.get("token_count") or 0),
        "source_url_host": _url_host_label(source_url),
        "source_text_kind": str(chunk_metadata.get("source_text_kind") or "unknown"),
        "used_metadata_fallback": bool(chunk_metadata.get("used_metadata_fallback")),
        "embedding_status": "indexed" if embedding_id is not None else "not_indexed",
        "embedding_provider": str(chunk.get("embedding_provider") or ""),
        "embedding_model_id": str(chunk.get("embedding_model_name") or ""),
    }


def _url_host_label(url: str) -> str:
    if not url.strip():
        return ""
    try:
        return (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def _build_neighborhood_thesis_payload(thesis: dict[str, Any]) -> dict[str, Any]:
    return {
        "thesis_id": _opaque_id("thesis", thesis.get("thesis_id"), "unknown"),
        "title": str(thesis.get("title") or ""),
        "status": str(thesis.get("status") or "unknown"),
        "conviction_score": _number(thesis.get("conviction_score")),
        "expected_holding_days": int(thesis.get("expected_holding_days") or 0),
        "invalidation_conditions": str(thesis.get("invalidation_conditions") or ""),
    }


def _build_neighborhood_recommendation_payload(recommendation: dict[str, Any]) -> dict[str, Any]:
    thesis_id = recommendation.get("thesis_id")
    return {
        "recommendation_id": _opaque_id("recommendation", recommendation.get("recommendation_id"), "unknown"),
        "as_of_date": str(recommendation.get("as_of_date") or ""),
        "action": str(recommendation.get("action") or "unknown"),
        "bucket": str(recommendation.get("bucket") or "unknown"),
        "total_score": _number(recommendation.get("total_score")),
        "recommended_weight": _number(recommendation.get("recommended_weight")),
        "linked_thesis_id": _opaque_id("thesis", thesis_id, None) if thesis_id is not None else None,
    }


def _build_neighborhood_position_payload(position: dict[str, Any]) -> dict[str, Any]:
    linked_thesis_id = position.get("linked_thesis_id")
    return {
        "portfolio_name": str(position.get("portfolio_name") or DEFAULT_PORTFOLIO_NAME),
        "snapshot_date": str(position.get("snapshot_date") or ""),
        "market_value": _number(position.get("market_value")),
        "weight": _number(position.get("weight")),
        "linked_thesis_id": _opaque_id("thesis", linked_thesis_id, None) if linked_thesis_id is not None else None,
    }


def _build_stock_event_payload(event: dict[str, Any]) -> dict[str, Any]:
    source_document_id = event.get("source_document_id") or event.get("raw_source_document_id")
    ai_evidence_id = event.get("ai_evidence_id")
    return {
        "event_id": _opaque_id("event", event.get("event_id"), "unknown"),
        "title": str(event.get("title") or ""),
        "event_type": str(event.get("event_type") or "unknown"),
        "event_at": _timestamp(event.get("event_at")),
        "impact_direction": str(event.get("impact_direction") or "unknown"),
        "impact_score": _number(event.get("impact_score")),
        "source_document_id": _opaque_id("source-document", source_document_id, None)
        if source_document_id is not None
        else None,
        "ai_evidence_id": _opaque_id("ai-evidence", ai_evidence_id, None) if ai_evidence_id is not None else None,
    }


def _build_stock_macro_flow_payload(flow: dict[str, Any]) -> dict[str, Any]:
    source_document_id = flow.get("source_document_id") or flow.get("raw_source_document_id")
    ai_evidence_id = flow.get("ai_evidence_id")
    source_run_id = flow.get("source_run_id")
    return {
        "event_id": _opaque_id("event", flow.get("event_id"), "unknown"),
        "title": str(flow.get("title") or ""),
        "event_type": str(flow.get("event_type") or "unknown"),
        "event_at": _timestamp(flow.get("event_at")),
        "theme_key": str(flow.get("theme_key") or ""),
        "theme_name": str(flow.get("theme_name") or ""),
        "impact_direction": str(flow.get("impact_direction") or "unknown"),
        "impact_score": _number(flow.get("impact_score")),
        "confidence": _number(flow.get("confidence")),
        "exposure_weight": _number(flow.get("exposure_weight")),
        "rationale": str(flow.get("rationale") or ""),
        "source_document_id": _opaque_id("source-document", source_document_id, None)
        if source_document_id is not None
        else None,
        "ai_evidence_id": _opaque_id("ai-evidence", ai_evidence_id, None) if ai_evidence_id is not None else None,
        "source_run_id": _opaque_id("pipeline-run", source_run_id, None) if source_run_id is not None else None,
    }


def _build_paper_action_payload(action: dict[str, Any]) -> dict[str, Any]:
    symbol = str(action.get("symbol") or "UNKNOWN").upper()
    recommendation_id = action.get("recommendation_id")
    linked_thesis_id = action.get("linked_thesis_id")
    return {
        "symbol": symbol,
        "instrument_id": _opaque_id("instrument", action.get("instrument_id"), symbol.lower()),
        "recommendation_id": _opaque_id("recommendation", recommendation_id, None)
        if recommendation_id is not None
        else None,
        "linked_thesis_id": _opaque_id("thesis", linked_thesis_id, None) if linked_thesis_id is not None else None,
        "recommendation_action": str(action.get("recommendation_action") or "no_recommendation"),
        "recommendation_score": _number(action.get("recommendation_score")),
        "recommendation_as_of_date": str(action.get("recommendation_as_of_date") or ""),
        "latest_price_date": str(action.get("latest_price_date") or ""),
        "latest_price": _number(action.get("latest_price")),
        "current_weight": _number(action.get("current_weight")),
        "target_weight": _number(action.get("target_weight")),
        "paper_action": str(action.get("paper_action") or "paper_hold"),
        "reason": str(action.get("reason") or ""),
        "risk_level": str(action.get("risk_level") or "low"),
        "requires_human_approval": action.get("requires_human_approval") is not False,
        "conflict": action.get("conflict") is True,
    }


def _paper_guardrails() -> list[str]:
    return [
        "이 화면은 가상 거래(Paper) 미리보기이며 실제 주문을 만들지 않는다.",
        "모든 가상 조치는 사람 승인 전까지 실행되지 않는다.",
        "실거래 증권사 API, 계좌 권한, 주문 전송은 아직 연결하지 않았다.",
    ]


def _build_trading_readiness_gates(state: dict[str, Any]) -> list[dict[str, Any]]:
    broker_boundary = _as_dict(state.get("broker_boundary"))
    account_permission = _as_dict(state.get("account_permission"))
    order_limit_policy = _as_dict(state.get("order_limit_policy"))
    kill_switches = [_build_trading_kill_switch_payload(item) for item in _as_list(state.get("kill_switches"))]
    paper_validation = _as_dict(state.get("paper_validation"))
    audit_summary = _as_dict(state.get("audit_summary"))

    broker_status = str(broker_boundary.get("status") or "")
    broker_preview_supported = broker_boundary.get("supports_order_preview") is True
    account_status = str(account_permission.get("status") or "")
    permission_scope = str(account_permission.get("permission_scope") or "")
    policy_status = str(order_limit_policy.get("status") or "")
    validation_status = str(paper_validation.get("status") or "")
    conflict_count = int(paper_validation.get("conflict_count") or 0)
    intent_count = int(audit_summary.get("intent_count") or 0)
    engaged_kill_switches = [item for item in kill_switches if item["is_engaged"]]

    return [
        _trading_gate(
            "broker_boundary",
            "브로커 경계",
            _gate_status(
                missing=not broker_boundary,
                blocked=broker_status != "enabled" or not broker_preview_supported,
            ),
            "가상 broker preview가 활성화되어야 주문 의도를 평가할 수 있다.",
            "simulated paper broker boundary를 enabled 상태로 등록한다.",
        ),
        _trading_gate(
            "account_permission",
            "계좌 권한",
            _gate_status(
                missing=not account_permission,
                blocked=account_status != "active" or permission_scope not in {"paper_trade", "live_trade"},
            ),
            "계좌는 paper_trade 이상의 scope와 active 상태가 필요하다.",
            "paper 전용 계좌 권한을 승인자와 한도와 함께 등록한다.",
        ),
        _trading_gate(
            "order_limit_policy",
            "주문 한도",
            _gate_status(missing=not order_limit_policy, blocked=policy_status != "active"),
            "단일 주문, 일일 주문, 비중 변화, 현금 버퍼 한도가 active여야 한다.",
            "장기 포트폴리오용 paper 주문 한도 정책을 active로 등록한다.",
        ),
        _trading_gate(
            "kill_switch",
            "킬 스위치",
            "blocked" if engaged_kill_switches else ("missing" if not kill_switches else "pass"),
            "engaged 상태의 킬 스위치가 하나라도 있으면 주문 의도는 차단된다.",
            "실거래 전에는 유지한다. paper 검증만 열 때도 명시 승인 기록 후 해제한다.",
        ),
        _trading_gate(
            "paper_validation",
            "가상 검증",
            _gate_status(
                missing=not paper_validation,
                blocked=validation_status != "passed" or conflict_count > 0,
            ),
            "추천/보유 충돌이 없는 passed paper validation이 필요하다.",
            "paper preview를 기준으로 validation run을 생성하고 남은 충돌을 0으로 만든다.",
        ),
        _trading_gate(
            "audit_log",
            "감사 로그",
            "warning" if intent_count == 0 else "pass",
            "주문 의도는 broker 제출 전에 audit row로 남아야 한다.",
            "paper ledger workflow에서 order intent audit을 먼저 생성한다.",
        ),
    ]


def _trading_gate(
    gate_key: str,
    label: str,
    status: str,
    detail: str,
    next_step: str,
) -> dict[str, Any]:
    return {
        "gate_key": gate_key,
        "label": label,
        "status": status,
        "detail": detail,
        "next_step": next_step,
    }


def _gate_status(*, missing: bool, blocked: bool) -> str:
    if missing:
        return "missing"
    if blocked:
        return "blocked"
    return "pass"


def _summarize_trading_gates(gates: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "pass_count": sum(1 for gate in gates if gate["status"] == "pass"),
        "warning_count": sum(1 for gate in gates if gate["status"] == "warning"),
        "missing_count": sum(1 for gate in gates if gate["status"] == "missing"),
        "blocked_count": sum(1 for gate in gates if gate["status"] == "blocked"),
    }


def _trading_readiness_status(summary: dict[str, int]) -> str:
    if summary["blocked_count"] > 0:
        return "blocked"
    if summary["missing_count"] > 0:
        return "missing_configuration"
    if summary["warning_count"] > 0:
        return "ready_for_paper_audit"
    return "paper_ready"


def _build_trading_broker_boundary_payload(boundary: dict[str, Any]) -> dict[str, Any]:
    return {
        "broker_code": str(boundary.get("broker_code") or ""),
        "environment": str(boundary.get("environment") or "paper"),
        "status": str(boundary.get("status") or "missing"),
        "supports_order_preview": boundary.get("supports_order_preview") is True,
        "supports_order_submit": boundary.get("supports_order_submit") is True,
        "secret_configured": boundary.get("secret_configured") is True,
        "notes": str(boundary.get("notes") or ""),
        "updated_at": _timestamp(boundary.get("updated_at")),
    }


def _build_trading_account_permission_payload(permission: dict[str, Any]) -> dict[str, Any]:
    return {
        "account_ref": str(permission.get("account_ref") or ""),
        "permission_scope": str(permission.get("permission_scope") or "missing"),
        "status": str(permission.get("status") or "missing"),
        "allowed_symbol_count": int(permission.get("allowed_symbol_count") or 0),
        "allows_all_symbols": permission.get("allows_all_symbols") is True,
        "max_order_notional": _number(permission.get("max_order_notional")),
        "max_daily_notional": _number(permission.get("max_daily_notional")),
        "approved_by": str(permission.get("approved_by") or ""),
        "approved_at": _timestamp(permission.get("approved_at")),
        "updated_at": _timestamp(permission.get("updated_at")),
    }


def _build_trading_order_limit_policy_payload(policy: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy_name": str(policy.get("policy_name") or ""),
        "status": str(policy.get("status") or "missing"),
        "max_single_order_notional": _number(policy.get("max_single_order_notional")),
        "max_daily_order_notional": _number(policy.get("max_daily_order_notional")),
        "max_single_order_weight_delta": _number(policy.get("max_single_order_weight_delta")),
        "max_post_trade_symbol_weight": _number(policy.get("max_post_trade_symbol_weight")),
        "min_cash_buffer_weight": _number(policy.get("min_cash_buffer_weight")),
        "updated_at": _timestamp(policy.get("updated_at")),
    }


def _build_trading_kill_switch_payload(switch: dict[str, Any]) -> dict[str, Any]:
    return {
        "scope": str(switch.get("scope") or "global"),
        "scope_ref": str(switch.get("scope_ref") or "global"),
        "is_engaged": switch.get("is_engaged") is True,
        "reason": str(switch.get("reason") or ""),
        "changed_by": str(switch.get("changed_by") or ""),
        "changed_at": _timestamp(switch.get("changed_at")),
    }


def _build_trading_paper_validation_payload(validation: dict[str, Any]) -> dict[str, Any]:
    blocked_reasons = validation.get("blocked_reasons")
    return {
        "validation_date": str(validation.get("validation_date") or ""),
        "status": str(validation.get("status") or "missing"),
        "recommendation_count": int(validation.get("recommendation_count") or 0),
        "conflict_count": int(validation.get("conflict_count") or 0),
        "approved_action_count": int(validation.get("approved_action_count") or 0),
        "validated_symbol_count": int(validation.get("validated_symbol_count") or 0),
        "blocked_reasons": [str(item) for item in blocked_reasons] if isinstance(blocked_reasons, list) else [],
        "created_by": str(validation.get("created_by") or ""),
        "created_at": _timestamp(validation.get("created_at")),
    }


def _build_trading_audit_summary_payload(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "intent_count": int(summary.get("intent_count") or 0),
        "blocked_count": int(summary.get("blocked_count") or 0),
        "approved_for_paper_count": int(summary.get("approved_for_paper_count") or 0),
        "approved_for_live_count": int(summary.get("approved_for_live_count") or 0),
        "submitted_to_broker_count": int(summary.get("submitted_to_broker_count") or 0),
        "latest_created_at": _timestamp(summary.get("latest_created_at")),
    }


def _trading_readiness_guardrails() -> list[str]:
    return [
        "이 화면은 주문 화면이 아니라 거래 안전 상태 점검 화면이다.",
        "FastAPI frontend server는 계속 read-only이며 주문 write endpoint를 제공하지 않는다.",
        "broker secret 값은 노출하지 않고 설정 여부만 표시한다.",
        "submitted_to_broker 값은 0이어야 하며, 실제 broker adapter는 아직 연결하지 않는다.",
    ]


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
        lines.append(f"      and coalesce(theme.code, document_theme.theme_key) = {sql_literal(theme_key)}")
    if symbol:
        lines.append(
            f"      and upper(coalesce(instrument.primary_symbol, document_instrument.primary_symbol)) = {sql_literal(symbol.upper())}"
        )
    if event_type and event_type != "all":
        lines.append(f"      and event_row.event_type = {sql_literal(event_type)}")
    return "\n".join(lines)


def _build_event_payload(event: dict[str, Any]) -> dict[str, Any]:
    symbol = str(event.get("symbol") or "UNKNOWN").upper()
    source_document_id = event.get("source_document_id") or event.get("raw_source_document_id")
    ai_evidence_id = event.get("ai_evidence_id")
    raw_related_events = event.get("related_events")
    related_events = (
        [_build_related_event_payload(item) for item in raw_related_events if isinstance(item, dict)]
        if isinstance(raw_related_events, list)
        else []
    )
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
        "ai_evidence_type": _optional_text(event.get("ai_evidence_type")),
        "ai_evidence_provider": _optional_text(event.get("ai_evidence_provider")),
        "ai_evidence_confidence": _number(event.get("ai_evidence_confidence")),
        "quality_gate": str(event.get("quality_gate") or "deterministic_review_required"),
        "related_events": related_events,
    }


def _build_related_event_payload(event: dict[str, Any]) -> dict[str, Any]:
    symbol = str(event.get("symbol") or "UNKNOWN").upper()
    return {
        "event_id": _opaque_id("event", event.get("event_id"), "unknown"),
        "title": str(event.get("title") or ""),
        "relation_type": str(event.get("relation_type") or "related"),
        "relation_strength": _number(event.get("relation_strength")),
        "reason": str(event.get("reason") or ""),
        "symbol": symbol,
        "theme_key": str(event.get("theme_key") or "UNCLASSIFIED"),
        "event_at": _timestamp(event.get("event_at")),
    }


def _build_ai_news_cluster_payload(cluster: dict[str, Any]) -> dict[str, Any]:
    summary = _build_ai_evidence_cluster_summary_payload(_as_dict(cluster.get("cluster_summary"))) or {
        "as_of_date": "",
        "theme_key": "UNCLASSIFIED",
        "theme_name": "Unclassified",
        "story_key": "theme",
        "story_label": "Unclassified",
        "event_count": 0,
        "symbols": [],
        "direction_counts": {},
        "representative_event_id": None,
        "request_hash": "",
    }
    representative_source_document_id = cluster.get("representative_source_document_id")
    return {
        "evidence_id": _opaque_id("ai-evidence", cluster.get("evidence_id"), "unknown"),
        "title": str(cluster.get("title") or "News cluster summary"),
        "evidence_type": str(cluster.get("evidence_type") or "news_cluster_summary"),
        "created_at": _timestamp(cluster.get("created_at")),
        "confidence": _number(cluster.get("confidence")),
        "theme_key": summary["theme_key"],
        "theme_name": summary["theme_name"],
        "story_key": summary["story_key"],
        "story_label": summary["story_label"],
        "as_of_date": summary["as_of_date"],
        "event_count": summary["event_count"],
        "symbols": summary["symbols"],
        "direction_counts": summary["direction_counts"],
        "representative_event_id": summary["representative_event_id"],
        "request_hash": summary["request_hash"],
        "source_document_count": int(cluster.get("source_document_count") or 0),
        "chunk_count": int(cluster.get("chunk_count") or 0),
        "embedded_chunk_count": int(cluster.get("embedded_chunk_count") or 0),
        "representative_source_document_id": _source_document_detail_id_from_raw(representative_source_document_id)
        if representative_source_document_id is not None
        else None,
        "extraction_run": _build_ai_news_cluster_run_payload(_as_dict(cluster.get("extraction_run"))),
        "events": [_build_ai_evidence_cluster_event_payload(item) for item in _as_list(cluster.get("cluster_events"))],
        "source_documents": [
            _build_ai_news_cluster_source_document_payload(item) for item in _as_list(cluster.get("source_documents"))
        ],
        "audit_notes": [str(note) for note in _as_scalar_list(cluster.get("audit_notes"))],
    }


def _build_ai_news_cluster_run_payload(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": _opaque_id("pipeline-run", run.get("run_id"), "unknown"),
        "status": str(run.get("status") or "unknown"),
        "provider": str(run.get("provider") or "unknown"),
        "model_id": str(run.get("model_id") or "unknown"),
        "reasoning_effort": str(run.get("reasoning_effort") or ""),
        "input_tokens": int(run.get("input_tokens") or 0),
        "output_tokens": int(run.get("output_tokens") or 0),
        "estimated_cost_usd": _number(run.get("estimated_cost_usd")) or 0.0,
        "request_hash": str(run.get("request_hash") or ""),
    }


def _build_ai_news_cluster_source_document_payload(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_document_id": _source_document_detail_id_from_raw(document.get("source_document_id")),
        "title": str(document.get("title") or ""),
        "url": str(document.get("url") or ""),
        "published_at": _timestamp(document.get("published_at")),
        "chunk_count": int(document.get("chunk_count") or 0),
        "embedded_chunk_count": int(document.get("embedded_chunk_count") or 0),
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


def _build_performance_quality_evaluation_payload(
    quality_evaluation: dict[str, Any],
    *,
    summary: dict[str, Any],
    coverage_exclusions: list[dict[str, Any]],
) -> dict[str, Any]:
    measured_recommendation_count = int(
        quality_evaluation.get("measured_recommendation_count")
        or summary.get("measured_recommendation_count")
        or 0
    )
    measured_thesis_count = int(
        quality_evaluation.get("measured_thesis_count")
        or summary.get("measured_thesis_count")
        or 0
    )
    review_outcome_mismatch_count = int(quality_evaluation.get("review_outcome_mismatch_count") or 0)
    high_score_recommendation_count = int(quality_evaluation.get("high_score_recommendation_count") or 0)
    coverage_exclusion_count = int(
        quality_evaluation.get("coverage_exclusion_count")
        or summary.get("excluded_position_count")
        or len(coverage_exclusions)
    )
    average_alpha = _coalesce_number(quality_evaluation.get("average_alpha"), summary.get("average_alpha"))
    hit_rate = _coalesce_number(quality_evaluation.get("hit_rate"), summary.get("hit_rate"))
    high_score_average_alpha = _number(quality_evaluation.get("high_score_average_alpha"))
    sample_size_status = str(
        quality_evaluation.get("sample_size_status")
        or _performance_sample_size_status(measured_recommendation_count)
    )
    score_outcome_alignment = str(
        quality_evaluation.get("score_outcome_alignment")
        or _performance_score_outcome_alignment(measured_recommendation_count, high_score_recommendation_count)
    )
    status = str(
        quality_evaluation.get("status")
        or _performance_quality_status(
            measured_recommendation_count=measured_recommendation_count,
            coverage_exclusion_count=coverage_exclusion_count,
            review_outcome_mismatch_count=review_outcome_mismatch_count,
            score_outcome_alignment=score_outcome_alignment,
            average_alpha=average_alpha,
        )
    )

    return {
        "status": status,
        "sample_size_status": sample_size_status,
        "score_outcome_alignment": score_outcome_alignment,
        "review_outcome_mismatch_count": review_outcome_mismatch_count,
        "measured_recommendation_count": measured_recommendation_count,
        "measured_thesis_count": measured_thesis_count,
        "average_alpha": average_alpha,
        "hit_rate": hit_rate,
        "high_score_recommendation_count": high_score_recommendation_count,
        "high_score_average_alpha": high_score_average_alpha,
        "coverage_exclusion_count": coverage_exclusion_count,
        "checks": [
            {
                "check_key": "sample_size",
                "label": "성과 표본 수",
                "status": _quality_check_status(sample_size_status, passing_values={"enough_sample"}),
                "detail": f"측정된 추천 {measured_recommendation_count}개, 투자 논리 {measured_thesis_count}개.",
                "next_step": "최소 5개 이상의 측정된 장기 추천 표본이 쌓일 때까지 결론을 보류한다.",
            },
            {
                "check_key": "score_outcome_alignment",
                "label": "점수와 성과 정렬",
                "status": _quality_check_status(score_outcome_alignment, passing_values={"aligned"}),
                "detail": f"높은 점수 추천 표본 {high_score_recommendation_count}개를 전체 평균 알파와 비교한다.",
                "next_step": "고점수 추천의 평균 알파가 전체 평균보다 낮으면 점수 구성요소를 재검토한다.",
            },
            {
                "check_key": "review_outcome_consistency",
                "label": "보유 검토와 성과 일치",
                "status": "blocked" if review_outcome_mismatch_count > 0 else "passed",
                "detail": f"최근 thesis review와 성과가 충돌한 항목 {review_outcome_mismatch_count}개.",
                "next_step": "충돌 항목은 thesis review 근거와 무효화 조건을 다시 확인한다.",
            },
            {
                "check_key": "coverage_readiness",
                "label": "성과 커버리지",
                "status": "warning" if coverage_exclusion_count > 0 else "passed",
                "detail": f"성과 해석에서 제외된 보유 항목 {coverage_exclusion_count}개.",
                "next_step": "투자 논리나 outcome이 빠진 보유 종목을 먼저 보완한다.",
            },
        ],
    }


def _coalesce_number(*values: object) -> float | None:
    for value in values:
        if value is not None:
            return _number(value)
    return None


def _performance_sample_size_status(measured_recommendation_count: int) -> str:
    if measured_recommendation_count == 0:
        return "no_outcome_data"
    if measured_recommendation_count < 5:
        return "insufficient_sample"
    return "enough_sample"


def _performance_score_outcome_alignment(
    measured_recommendation_count: int,
    high_score_recommendation_count: int,
) -> str:
    if measured_recommendation_count == 0:
        return "no_outcome_data"
    if measured_recommendation_count < 5:
        return "insufficient_sample"
    if high_score_recommendation_count == 0:
        return "no_high_score_sample"
    return "reviewable"


def _performance_quality_status(
    *,
    measured_recommendation_count: int,
    coverage_exclusion_count: int,
    review_outcome_mismatch_count: int,
    score_outcome_alignment: str,
    average_alpha: float | None,
) -> str:
    if measured_recommendation_count == 0:
        return "no_outcome_data"
    if measured_recommendation_count < 5:
        return "insufficient_sample"
    if coverage_exclusion_count > 0:
        return "needs_coverage_review"
    if review_outcome_mismatch_count > 0 or score_outcome_alignment == "misaligned":
        return "needs_quality_review"
    if average_alpha is not None and average_alpha > 0:
        return "positive_alignment"
    return "reviewable"


def _quality_check_status(value: str, *, passing_values: set[str]) -> str:
    if value in passing_values:
        return "passed"
    if value in {"misaligned", "no_outcome_data"}:
        return "blocked"
    return "warning"


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
    evidence_id = str(component.get("evidence_id") or component.get("explanation") or component_name)
    return {
        "component": component_name,
        "value": _number(component.get("value") or component.get("component_score")),
        "weight": _number(component.get("weight") or component.get("component_weight")),
        "evidence_id": evidence_id,
        "provenance": _build_score_component_provenance_payload(
            _as_dict(component.get("provenance")),
            component_name=component_name,
            evidence_id=evidence_id,
        ),
    }


def _build_score_component_provenance_payload(
    provenance: dict[str, Any],
    *,
    component_name: str,
    evidence_id: str,
) -> dict[str, Any]:
    source_type = _optional_text(provenance.get("source_type")) or _infer_score_component_source_type(evidence_id)
    raw_source_run_id = provenance.get("source_run_id")
    raw_universe_batch_id = provenance.get("universe_batch_id")
    evidence_summary = _build_score_component_evidence_summary(_as_dict(provenance.get("evidence_json")))
    return {
        "source_type": source_type,
        "label": _optional_text(provenance.get("label")) or _default_score_component_provenance_label(source_type),
        "component": component_name,
        "feature_code": _optional_text(provenance.get("feature_code")),
        "feature_name": _optional_text(provenance.get("feature_name")),
        "description": _optional_text(provenance.get("description")),
        "feature_value": _number(provenance.get("feature_value")),
        "zscore": _number(provenance.get("zscore")),
        "as_of_date": _optional_text(provenance.get("as_of_date")),
        "source_run_id": _opaque_id("pipeline-run", raw_source_run_id, None) if raw_source_run_id is not None else None,
        "universe_batch_id": _opaque_id("strategy-universe-batch", raw_universe_batch_id, None)
        if raw_universe_batch_id is not None
        else evidence_summary.get("universe_batch_id"),
        "rank_position": _integer(provenance.get("rank_position")),
        "universe_member_count": _integer(provenance.get("universe_member_count")),
        "selection_score": _number(provenance.get("selection_score")),
        "selection_rule": _optional_text(provenance.get("selection_rule")),
        "latest_trade_date": _optional_text(provenance.get("latest_trade_date")),
        "observation_count": _integer(provenance.get("observation_count")),
        "inclusion_reason": _optional_text(provenance.get("inclusion_reason")),
        "evidence": evidence_summary,
    }


def _build_score_component_evidence_summary(evidence_json: dict[str, Any]) -> dict[str, Any]:
    raw_universe_batch_id = evidence_json.get("universe_batch_id")
    return {
        "feature_set_version": _optional_text(evidence_json.get("feature_set_version")),
        "universe_batch_id": _opaque_id("strategy-universe-batch", raw_universe_batch_id, None)
        if raw_universe_batch_id is not None
        else None,
        "rank_position": _integer(evidence_json.get("rank_position")),
        "observation_count": _integer(evidence_json.get("observation_count")),
        "first_trade_date": _optional_text(evidence_json.get("first_trade_date")),
        "latest_trade_date": _optional_text(evidence_json.get("latest_trade_date")),
        "as_of_date": _optional_text(evidence_json.get("as_of_date")),
        "propagated_impact_count": _integer(evidence_json.get("propagated_impact_count")),
        "recent_flows": _as_list(evidence_json.get("recent_flows")),
    }


def _infer_score_component_source_type(evidence_id: str) -> str:
    if evidence_id.startswith("market-feature-"):
        return "market_feature"
    if evidence_id.startswith("universe-rank-"):
        return "strategy_universe_rank"
    if evidence_id.startswith("macro-flow-"):
        return "macro_flow_propagation"
    if _is_ai_or_event_evidence_id(evidence_id):
        return "event_or_ai_evidence"
    return "score_component"


def _default_score_component_provenance_label(source_type: str) -> str:
    if source_type == "market_feature":
        return "가격 feature snapshot"
    if source_type == "strategy_universe_rank":
        return "전략 유니버스 순위"
    if source_type == "event_or_ai_evidence":
        return "원천 이벤트/AI 근거"
    if source_type == "macro_flow_propagation":
        return "상위 흐름 전파 근거"
    return "저장된 점수 구성요소"


def _build_recommendation_evidence_review_payload(
    *,
    score_components: list[dict[str, Any]],
    linked_thesis_id: Any,
    outcome: dict[str, Any],
) -> dict[str, Any]:
    ai_evidence_component_count = sum(
        1 for component in score_components if _is_ai_or_event_evidence_id(str(component.get("evidence_id") or ""))
    )
    market_or_rank_component_count = sum(
        1 for component in score_components if _is_market_or_rank_score_component(component)
    )
    market_or_rank_provenance_count = sum(
        1 for component in score_components if _is_market_or_rank_score_component(component) and _has_market_or_rank_provenance(component)
    )
    outcome_measured = bool(outcome.get("measurement_end_date")) and str(outcome.get("label") or "unmeasured") != "unmeasured"
    gates = [
        _evidence_review_gate(
            "linked_thesis",
            "투자 논리 연결",
            "pass" if linked_thesis_id is not None else "blocked",
            "추천은 반드시 연결된 투자 논리와 함께 검토해야 한다.",
            "추천을 투자 논리와 연결한 뒤 다시 검토한다.",
        ),
        _evidence_review_gate(
            "score_components",
            "점수 구성요소",
            "pass" if score_components else "blocked",
            "점수는 어떤 입력이 몇 % 반영됐는지 분해되어야 한다.",
            "cycle, 가격, 이벤트, 품질 구성요소를 저장한다.",
        ),
        _evidence_review_gate(
            "ai_or_event_evidence",
            "AI/이벤트 근거",
            "pass" if ai_evidence_component_count > 0 else "warning",
            "점수 구성요소 중 최소 하나는 원천 이벤트나 AI 근거로 추적되어야 한다.",
            "score component evidence_id를 event 또는 ai-evidence에 연결한다.",
        ),
        _evidence_review_gate(
            "market_feature_provenance",
            "가격/순위 입력 근거",
            "pass" if market_or_rank_component_count == market_or_rank_provenance_count else "warning",
            "가격 모멘텀과 유니버스 순위 점수는 feature snapshot, rank, source run으로 추적되어야 한다.",
            "market-feature 또는 rank component의 source_run_id와 feature evidence를 보강한다.",
        ),
        _evidence_review_gate(
            "outcome_measurement",
            "성과 측정",
            "pass" if outcome_measured else "warning",
            "중장기 추천은 이후 성과 측정과 연결되어야 품질을 검토할 수 있다.",
            "성과 측정 윈도우가 끝나면 recommendation outcome을 생성한다.",
        ),
        _evidence_review_gate(
            "order_boundary",
            "주문 차단",
            "pass",
            "이 검토는 실제 주문이나 가상 주문을 만들지 않는 read-only 품질 점검이다.",
            "주문 전송은 별도 broker boundary와 kill switch 승인 뒤에만 다룬다.",
        ),
    ]
    return {
        "quality_status": _evidence_review_status(gates),
        "summary": {
            "gate_count": len(gates),
            "pass_count": sum(1 for gate in gates if gate["status"] == "pass"),
            "warning_count": sum(1 for gate in gates if gate["status"] == "warning"),
            "blocked_count": sum(1 for gate in gates if gate["status"] == "blocked"),
            "score_component_count": len(score_components),
            "ai_evidence_component_count": ai_evidence_component_count,
            "market_or_rank_component_count": market_or_rank_component_count,
            "market_or_rank_provenance_count": market_or_rank_provenance_count,
            "linked_thesis_present": linked_thesis_id is not None,
            "outcome_measured": outcome_measured,
        },
        "gates": gates,
    }


def _build_thesis_evidence_review_payload(
    *,
    evidence: list[dict[str, Any]],
    invalidation_conditions: list[Any],
    latest_review: dict[str, Any],
) -> dict[str, Any]:
    source_event_count = sum(1 for item in evidence if item.get("type") != "performance_outcome")
    performance_evidence_count = sum(1 for item in evidence if item.get("type") == "performance_outcome")
    invalidation_condition_count = len(invalidation_conditions)
    latest_review_present = latest_review.get("review_id") is not None
    gates = [
        _evidence_review_gate(
            "source_events",
            "원천 이벤트",
            "pass" if source_event_count > 0 else "blocked",
            "투자 논리는 원천 뉴스/공시 이벤트로 추적되어야 한다.",
            "관련 이벤트나 AI 근거를 thesis evidence로 연결한다.",
        ),
        _evidence_review_gate(
            "performance_evidence",
            "성과 근거",
            "pass" if performance_evidence_count > 0 else "warning",
            "투자 논리는 시간이 지나면 성과 측정 근거와 함께 검토되어야 한다.",
            "측정 가능 시점 이후 thesis outcome을 연결한다.",
        ),
        _evidence_review_gate(
            "invalidation_conditions",
            "무효화 조건",
            "pass" if invalidation_condition_count > 0 else "blocked",
            "장기 thesis는 틀렸다고 판단할 조건을 명시해야 한다.",
            "가격, 실적, 경쟁, 규제 관련 무효화 조건을 추가한다.",
        ),
        _evidence_review_gate(
            "latest_human_review",
            "최근 사람 검토",
            "pass" if latest_review_present else "warning",
            "보유 판단은 최신 사람 검토 기록과 함께 유지되어야 한다.",
            "thesis review를 생성하거나 다음 검토 일정을 잡는다.",
        ),
        _evidence_review_gate(
            "order_boundary",
            "주문 차단",
            "pass",
            "이 thesis 검토는 실제 주문이나 가상 주문을 만들지 않는다.",
            "주문 전송은 별도 broker boundary와 kill switch 승인 뒤에만 다룬다.",
        ),
    ]
    return {
        "quality_status": _evidence_review_status(gates),
        "summary": {
            "gate_count": len(gates),
            "pass_count": sum(1 for gate in gates if gate["status"] == "pass"),
            "warning_count": sum(1 for gate in gates if gate["status"] == "warning"),
            "blocked_count": sum(1 for gate in gates if gate["status"] == "blocked"),
            "evidence_count": len(evidence),
            "source_event_count": source_event_count,
            "performance_evidence_count": performance_evidence_count,
            "invalidation_condition_count": invalidation_condition_count,
            "latest_review_present": latest_review_present,
        },
        "gates": gates,
    }


def _evidence_review_gate(
    gate_key: str,
    label: str,
    status: str,
    detail: str,
    next_step: str,
) -> dict[str, str]:
    return {
        "gate_key": gate_key,
        "label": label,
        "status": status,
        "detail": detail,
        "next_step": next_step,
    }


def _evidence_review_status(gates: list[dict[str, str]]) -> str:
    if any(gate["status"] == "blocked" for gate in gates):
        return "blocked"
    if any(gate["status"] == "warning" for gate in gates):
        return "needs_evidence_review"
    return "ready_for_human_review"


def _is_market_or_rank_score_component(component: dict[str, Any]) -> bool:
    provenance = _as_dict(component.get("provenance"))
    source_type = str(provenance.get("source_type") or "")
    evidence_id = str(component.get("evidence_id") or "")
    return source_type in {"market_feature", "strategy_universe_rank"} or evidence_id.startswith(
        ("market-feature-", "universe-rank-")
    )


def _has_market_or_rank_provenance(component: dict[str, Any]) -> bool:
    provenance = _as_dict(component.get("provenance"))
    source_type = str(provenance.get("source_type") or "")
    if source_type == "market_feature":
        evidence = _as_dict(provenance.get("evidence"))
        return bool(provenance.get("feature_code")) and (
            provenance.get("source_run_id") is not None or any(value is not None for value in evidence.values())
        )
    if source_type == "strategy_universe_rank":
        return provenance.get("rank_position") is not None and (
            provenance.get("source_run_id") is not None or provenance.get("universe_batch_id") is not None
        )
    return False


def _is_ai_or_event_evidence_id(evidence_id: str) -> bool:
    return evidence_id.startswith(("ai-evidence-", "event-", "sec-event-", "macro-flow-")) or evidence_id.isdigit()


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


def _build_ai_evidence_cluster_summary_payload(summary: dict[str, Any]) -> dict[str, Any] | None:
    if not summary:
        return None
    return {
        "as_of_date": str(summary.get("as_of_date") or ""),
        "theme_key": str(summary.get("theme_key") or "UNCLASSIFIED"),
        "theme_name": str(summary.get("theme_name") or "Unclassified"),
        "story_key": str(summary.get("story_key") or "theme"),
        "story_label": str(summary.get("story_label") or summary.get("theme_name") or "Unclassified"),
        "event_count": int(summary.get("event_count") or 0),
        "symbols": [str(symbol).upper() for symbol in _as_scalar_list(summary.get("symbols")) if str(symbol).strip()],
        "direction_counts": {
            str(key): int(value or 0) for key, value in _as_dict(summary.get("direction_counts")).items()
        },
        "representative_event_id": _opaque_id("event", summary.get("representative_event_id"), None)
        if summary.get("representative_event_id") is not None
        else None,
        "request_hash": str(summary.get("request_hash") or ""),
    }


def _build_ai_evidence_cluster_event_payload(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": _opaque_id("event", event.get("event_id"), "unknown"),
        "title": str(event.get("title") or ""),
        "event_at": _timestamp(event.get("event_at")),
        "symbol": str(event.get("symbol") or "UNKNOWN").upper(),
        "impact_direction": str(event.get("impact_direction") or "unknown"),
        "impact_score": _number(event.get("impact_score")),
        "source_document_id": _source_document_detail_id_from_raw(event.get("source_document_id")),
    }


def _build_ai_evidence_news_candidate_payload(candidate: dict[str, Any]) -> dict[str, Any] | None:
    if not candidate:
        return None
    return {
        "analysis_method": str(candidate.get("analysis_method") or "unknown"),
        "event_summary": str(candidate.get("event_summary") or ""),
        "recommendation_relevance": str(candidate.get("recommendation_relevance") or "unknown"),
        "uncertainty_notes": str(candidate.get("uncertainty_notes") or ""),
        "theme_impacts": [
            _build_news_candidate_impact_payload(item, target_key="theme_code")
            for item in _as_list(candidate.get("theme_impacts"))
        ],
        "instrument_impacts": [
            _build_news_candidate_impact_payload(item, target_key="symbol")
            for item in _as_list(candidate.get("instrument_impacts"))
        ],
    }


def _build_news_candidate_impact_payload(impact: dict[str, Any], *, target_key: str) -> dict[str, Any]:
    return {
        "target": str(impact.get(target_key) or impact.get("target") or "UNKNOWN"),
        "impact_direction": str(impact.get("impact_direction") or "unknown"),
        "impact_strength": _number(impact.get("impact_strength")),
        "confidence": _number(impact.get("confidence")),
        "rationale": str(impact.get("rationale") or ""),
        "evidence_summary": str(impact.get("evidence_summary") or ""),
    }


def _build_ai_evidence_retrieval_context_payload(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "as_of_date": _optional_text(context.get("as_of_date")) or "",
        "known_themes": _as_context_summary_items(context.get("known_themes")),
        "theme_edges": _as_context_summary_items(context.get("theme_edges")),
        "current_event_impacts": _as_context_summary_items(context.get("current_event_impacts")),
        "recent_similar_events": _as_context_summary_items(context.get("recent_similar_events")),
    }


def _as_context_summary_items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _build_linked_evidence_payload(evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "evidence_id": _opaque_id("ai-evidence", evidence.get("evidence_id"), "unknown"),
        "evidence_type": str(evidence.get("evidence_type") or "unknown"),
        "title": str(evidence.get("title") or ""),
    }


def _build_recommendation_list_item_payload(item: dict[str, Any]) -> dict[str, Any]:
    symbol = str(item.get("symbol") or "UNKNOWN").upper()
    evidence = _as_dict(item.get("evidence"))
    outcome = _as_dict(item.get("outcome"))
    linked_thesis_id = item.get("linked_thesis_id")
    primary_evidence_id = evidence.get("primary_evidence_id")
    return {
        "recommendation_id": _opaque_id("recommendation", item.get("recommendation_id"), None),
        "symbol": symbol,
        "name": str(item.get("name") or ""),
        "instrument_id": _opaque_id("instrument", item.get("instrument_id"), symbol.lower()),
        "as_of_date": str(item.get("as_of_date") or ""),
        "rank_position": int(item.get("rank_position") or 0),
        "bucket": str(item.get("bucket") or "unknown"),
        "action": str(item.get("action") or "monitor"),
        "status": str(item.get("status") or "unknown"),
        "score": _number(item.get("score")) or 0.0,
        "recommended_weight": _number(item.get("recommended_weight")),
        "linked_thesis_id": _opaque_id("thesis", linked_thesis_id, None) if linked_thesis_id is not None else None,
        "evidence": {
            "score_component_count": int(evidence.get("score_component_count") or 0),
            "ai_or_event_component_count": int(evidence.get("ai_or_event_component_count") or 0),
            "market_or_rank_component_count": int(evidence.get("market_or_rank_component_count") or 0),
            "quality_status": str(evidence.get("quality_status") or "unknown"),
            "primary_evidence_id": str(primary_evidence_id) if primary_evidence_id else None,
        },
        "outcome": {
            "measurement_end_date": str(outcome.get("measurement_end_date") or ""),
            "label": str(outcome.get("label") or "unmeasured"),
            "alpha": _number(outcome.get("alpha")),
        },
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
        symbol = str(state.get("symbol") or "").upper()
        as_of_date = str(state.get("as_of_date") or "")
        query_parts = []
        if as_of_date:
            query_parts.append(f"asOfDate={quote(as_of_date)}")
        if symbol:
            query_parts.append(f"symbol={quote(symbol)}")
        links["source_events"] = "/api/events" + (f"?{'&'.join(query_parts)}" if query_parts else "")
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


def _build_allocation_policy_payload(policy: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy_id": _opaque_id("allocation-policy", policy.get("allocation_policy_id"), None),
        "policy_name": str(policy.get("policy_name") or "default_fallback"),
        "status": str(policy.get("status") or "fallback"),
        "policy_scope": str(policy.get("policy_scope") or "fallback"),
        "max_single_position_weight": _number(policy.get("max_single_position_weight")),
        "min_rebalance_target_weight": _number(policy.get("min_rebalance_target_weight")),
        "valid_from": str(policy.get("valid_from") or ""),
        "valid_to": str(policy.get("valid_to") or ""),
        "rationale": str(policy.get("rationale") or ""),
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


def _parse_optional_int(
    query: dict[str, str],
    key: str,
    *,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    value = query.get(key)
    parsed_value = default if not value else int(value)
    if parsed_value < minimum or parsed_value > maximum:
        raise FrontendLiveUnsupportedPathError(f"{key} must be between {minimum} and {maximum}.")
    return parsed_value


def _parse_optional_iso_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


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


def _as_scalar_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


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


def _integer(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(Decimal(str(value)))


def _optional_text(value: object) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


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
