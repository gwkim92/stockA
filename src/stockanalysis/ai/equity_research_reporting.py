from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import tempfile
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_PIPELINE_NAME = "equity_research_reporting"
DEFAULT_TASK_NAME = "ai-equity-research-reporting"
DEFAULT_TEMPLATE_VERSION = "2026-05-25-equity-research-v1"
ARTIFACT_TYPE = "full_equity_research"
FIXTURE_PROVIDER = "fixture"
CODEX_OAUTH_PROVIDER = "codex_oauth"
DEFAULT_MODEL_NAME = "codex-cli-default"
DEFAULT_REASONING_EFFORT = "low"
DEFAULT_MAX_CONTEXT_CHARS = 16000


@dataclass(frozen=True)
class EquityResearchOutput:
    title: str
    korean_summary: str
    key_points: tuple[str, ...]
    catalysts: tuple[str, ...]
    risks: tuple[str, ...]
    invalidation_conditions: tuple[str, ...]
    valuation_sensitivity: dict[str, object]


@dataclass(frozen=True)
class EquityResearchProviderResponse:
    provider: str
    model_name: str
    reasoning_effort: str | None
    output: EquityResearchOutput
    input_token_count: int | None = None
    output_token_count: int | None = None
    cached_input_token_count: int | None = None
    estimated_cost_usd: Decimal | None = None
    latency_ms: int | None = None


EquityResearchProviderRunner = Callable[
    [dict[str, object], str, str | None, int],
    EquityResearchProviderResponse,
]


def render_equity_research_symbol_lookup_sql(
    *,
    as_of_date: date,
    symbols: Iterable[str] = (),
    limit: int = 5,
) -> str:
    if limit < 1 or limit > 50:
        raise ValueError("limit must be between 1 and 50.")
    normalized_symbols = _normalize_symbols(symbols)
    if normalized_symbols:
        values_sql = ", ".join(f"({sql_literal(symbol)})" for symbol in normalized_symbols)
        return f"""-- equity research symbol lookup
with requested(symbol) as (
    values {values_sql}
)
select coalesce(json_agg(instrument.primary_symbol order by requested.symbol), '[]'::json)::text
from requested
join ref.instrument instrument on upper(instrument.primary_symbol) = requested.symbol
where instrument.is_active = true
limit {limit};"""
    return f"""-- equity research symbol lookup
with latest_batch as (
    select batch.batch_id
    from signal.recommendation_batch batch
    where batch.as_of_date <= {sql_date(as_of_date)}
    order by batch.as_of_date desc, batch.batch_id desc
    limit 1
),
ranked as (
    select
        instrument.primary_symbol,
        recommendation.rank_position
    from latest_batch batch
    join signal.recommendation recommendation on recommendation.batch_id = batch.batch_id
    join ref.instrument instrument on instrument.instrument_id = recommendation.instrument_id
    where recommendation.status = 'active'
    order by recommendation.rank_position asc, instrument.primary_symbol asc
    limit {limit}
)
select coalesce(json_agg(primary_symbol order by rank_position, primary_symbol), '[]'::json)::text
from ranked;"""


def render_equity_research_context_sql(*, symbol: str, as_of_date: date, limit: int = 8) -> str:
    if limit < 1 or limit > 50:
        raise ValueError("limit must be between 1 and 50.")
    symbol_literal = sql_literal(symbol.upper())
    return f"""-- equity research context lookup
with target as (
    select
        instrument.instrument_id,
        instrument.primary_symbol,
        instrument.name,
        instrument.market_code,
        instrument.currency_code
    from ref.instrument instrument
    where upper(instrument.primary_symbol) = {symbol_literal}
      and instrument.is_active = true
    order by instrument.instrument_id desc
    limit 1
),
latest_financial_metrics as (
    select distinct on (normalized.metric_code)
        normalized.metric_code,
        normalized.metric_value,
        normalized.metric_unit,
        normalized.metric_status,
        normalized.rationale,
        normalized.statement_scope,
        normalized.period_end,
        normalized.source_run_id
    from market.financial_metric_normalized normalized
    join target on target.instrument_id = normalized.instrument_id
    where normalized.as_of_date <= {sql_date(as_of_date)}
      and normalized.statement_scope = 'annual'
    order by normalized.metric_code, normalized.as_of_date desc, normalized.period_end desc
),
financial_metric_status_counts as (
    select
        metric_status,
        count(*)::integer as metric_count
    from latest_financial_metrics
    group by metric_status
),
latest_peer_rows as (
    select distinct on (snapshot.metric_code)
        peer_group.group_code as peer_group_code,
        peer_group.name as peer_group_name,
        snapshot.metric_code,
        snapshot.instrument_value as metric_value,
        snapshot.percentile_rank,
        snapshot.relative_signal,
        snapshot.as_of_date,
        snapshot.source_run_id
    from market.peer_relative_snapshot snapshot
    join target on target.instrument_id = snapshot.instrument_id
    join ref.peer_group peer_group on peer_group.peer_group_id = snapshot.peer_group_id
    where snapshot.as_of_date <= {sql_date(as_of_date)}
    order by snapshot.metric_code, snapshot.as_of_date desc, snapshot.peer_snapshot_id desc
),
latest_valuation_rows as (
    select distinct on (valuation.method)
        valuation.method,
        valuation.base_price,
        valuation.fair_value_low,
        valuation.fair_value_base,
        valuation.fair_value_high,
        valuation.margin_of_safety,
        valuation.assumptions_json,
        valuation.confidence,
        valuation.as_of_date,
        valuation.source_run_id
    from market.valuation_snapshot valuation
    join target on target.instrument_id = valuation.instrument_id
    where valuation.as_of_date <= {sql_date(as_of_date)}
    order by valuation.method, valuation.as_of_date desc, valuation.valuation_snapshot_id desc
),
latest_recommendation as (
    select
        recommendation.recommendation_id,
        batch.as_of_date,
        batch.strategy_name,
        batch.horizon_type,
        recommendation.action,
        recommendation.bucket,
        recommendation.rank_position,
        recommendation.total_score,
        recommendation.recommended_weight,
        recommendation.status,
        recommendation.thesis_id,
        batch.source_run_id
    from signal.recommendation recommendation
    join signal.recommendation_batch batch on batch.batch_id = recommendation.batch_id
    join target on target.instrument_id = recommendation.instrument_id
    where batch.as_of_date <= {sql_date(as_of_date)}
    order by batch.as_of_date desc, recommendation.recommendation_id desc
    limit 1
),
fundamental_components as (
    select
        component.component_name,
        component.component_score,
        component.component_weight,
        component.explanation
    from signal.recommendation_score_component component
    join latest_recommendation recommendation on recommendation.recommendation_id = component.recommendation_id
    where component.component_name in (
        'fundamental_quality_score',
        'valuation_margin_score',
        'peer_relative_score',
        'balance_sheet_risk_penalty',
        'thesis_consistency_score'
    )
    order by component.component_name
),
latest_thesis as (
    select
        thesis.thesis_id,
        thesis.title,
        thesis.summary,
        thesis.status,
        thesis.conviction_score,
        thesis.expected_holding_days,
        thesis.benchmark_code,
        thesis.entry_conditions,
        thesis.invalidation_conditions,
        thesis.exit_conditions,
        thesis.created_by_run_id
    from signal.investment_thesis thesis
    join target on target.instrument_id = thesis.instrument_id
    order by
        case when thesis.thesis_id = (select thesis_id from latest_recommendation) then 0 else 1 end,
        case when thesis.status = 'active' then 0 else 1 end,
        thesis.created_at desc,
        thesis.thesis_id desc
    limit 1
),
recent_events as (
    select
        event_row.event_id,
        event_row.title,
        event_row.summary,
        event_row.event_at,
        impact.impact_direction,
        impact.impact_strength,
        coalesce(impact.confidence, event_row.confidence) as confidence,
        impact.rationale,
        source_document.document_id,
        source_document.korean_title,
        source_document.korean_summary,
        source_document.translation_confidence,
        source_document.url
    from target
    join event.event_instrument_impact impact on impact.instrument_id = target.instrument_id
    join event.event event_row on event_row.event_id = impact.event_id
    left join event.event_document_link document_link
      on document_link.event_id = event_row.event_id
     and document_link.link_type = 'source'
    left join ingest.source_document source_document on source_document.document_id = document_link.document_id
    where event_row.event_at <= ({sql_date(as_of_date)}::date + interval '1 day')
    order by event_row.event_at desc, event_row.event_id desc
    limit {limit}
),
cycle_summaries as (
    select
        node.code as node_code,
        node.name as node_name,
        summary.summary_type,
        summary.summary_json,
        summary.as_of_date,
        summary.source_run_id
    from target
    join ref.instrument_classification_membership membership on membership.instrument_id = target.instrument_id
    join ref.classification_node node on node.node_id = membership.node_id
    left join lateral (
        select summary.*
        from ai.cycle_community_summary summary
        where summary.node_id = node.node_id
          and summary.as_of_date <= {sql_date(as_of_date)}
        order by summary.as_of_date desc, summary.updated_at desc
        limit 1
    ) summary on true
    where membership.valid_from <= {sql_date(as_of_date)}
      and (membership.valid_to is null or membership.valid_to >= {sql_date(as_of_date)})
    order by coalesce(membership.confidence, 0) desc, node.code
    limit {limit}
)
select json_build_object(
    'query', json_build_object('symbol', {symbol_literal}, 'as_of_date', {sql_literal(as_of_date.isoformat())}, 'limit', {limit}),
    'instrument', (select row_to_json(target) from target),
    'financial_metrics', coalesce((select json_agg(row_to_json(latest_financial_metrics) order by metric_code) from latest_financial_metrics), '[]'::json),
    'financial_metric_status_counts', coalesce((select json_agg(row_to_json(financial_metric_status_counts) order by metric_status) from financial_metric_status_counts), '[]'::json),
    'peer_relative', coalesce((select json_agg(row_to_json(latest_peer_rows) order by metric_code) from latest_peer_rows), '[]'::json),
    'valuations', coalesce((select json_agg(row_to_json(latest_valuation_rows) order by method) from latest_valuation_rows), '[]'::json),
    'recommendation', (select row_to_json(latest_recommendation) from latest_recommendation),
    'fundamental_components', coalesce((select json_agg(row_to_json(fundamental_components) order by component_name) from fundamental_components), '[]'::json),
    'thesis', (select row_to_json(latest_thesis) from latest_thesis),
    'recent_events', coalesce((select json_agg(row_to_json(recent_events) order by event_at desc, event_id desc) from recent_events), '[]'::json),
    'cycle_summaries', coalesce((select json_agg(row_to_json(cycle_summaries) order by node_code) from cycle_summaries), '[]'::json)
)::text;"""


def build_codex_oauth_equity_research_prompt(context: dict[str, object], *, max_context_chars: int) -> str:
    bounded_context = _bounded_context_for_prompt(context, max_context_chars=max_context_chars)
    return "\n".join(
        (
            "You are an equity research analyst for a medium-to-long-term investment operating system.",
            "Use only the supplied Postgres context. Do not browse, do not call tools, and do not make order decisions.",
            "Return exactly one JSON object matching the output schema.",
            "Write every human-readable field in Korean.",
            "Keep ticker symbols, ids, method names, and machine codes unchanged.",
            "Separate story from numbers: business/fundamental quality, peer position, valuation, thesis, catalysts, risks, and invalidation.",
            "If a field is missing or weak, explicitly say the evidence is missing instead of inventing facts.",
            "Do not change recommendation scores or weights. This output is an explanatory research artifact only.",
            "",
            "Output schema intent:",
            "- title: short Korean report title including the ticker.",
            "- korean_summary: one concise Korean paragraph.",
            "- key_points: 3-7 bullets about business/fundamental/peer/valuation/thesis context.",
            "- catalysts: observable catalysts grounded in recent_events, cycle_summaries, recommendation, or thesis.",
            "- risks: risks, data gaps, valuation pressure, balance-sheet concerns, or cycle conflicts.",
            "- invalidation_conditions: conditions that would weaken or invalidate the thesis.",
            "- valuation_sensitivity: object with base_case, upside_case, downside_case, margin_of_safety_view, confidence.",
            "",
            "Postgres equity research context:",
            json.dumps(bounded_context, ensure_ascii=False, sort_keys=True),
        )
    )


def build_codex_oauth_equity_research_output_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["research", "usage"],
        "properties": {
            "research": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "title",
                    "korean_summary",
                    "key_points",
                    "catalysts",
                    "risks",
                    "invalidation_conditions",
                    "valuation_sensitivity",
                ],
                "properties": {
                    "title": {"type": "string"},
                    "korean_summary": {"type": "string"},
                    "key_points": {"type": "array", "items": {"type": "string"}},
                    "catalysts": {"type": "array", "items": {"type": "string"}},
                    "risks": {"type": "array", "items": {"type": "string"}},
                    "invalidation_conditions": {"type": "array", "items": {"type": "string"}},
                    "valuation_sensitivity": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["base_case", "upside_case", "downside_case", "margin_of_safety_view", "confidence"],
                        "properties": {
                            "base_case": {"type": "string"},
                            "upside_case": {"type": "string"},
                            "downside_case": {"type": "string"},
                            "margin_of_safety_view": {"type": "string"},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        },
                    },
                },
            },
            "usage": {
                "type": "object",
                "additionalProperties": False,
                "required": ["input_tokens", "output_tokens", "cached_input_tokens", "estimated_cost_usd", "latency_ms"],
                "properties": {
                    "input_tokens": {"type": ["integer", "null"]},
                    "output_tokens": {"type": ["integer", "null"]},
                    "cached_input_tokens": {"type": ["integer", "null"]},
                    "estimated_cost_usd": {"type": ["number", "null"]},
                    "latency_ms": {"type": ["integer", "null"]},
                },
            },
        },
    }


def parse_equity_research_response_payload(
    payload: dict[str, object],
    *,
    context: dict[str, object],
) -> EquityResearchProviderResponse:
    research_payload = payload.get("research")
    if not isinstance(research_payload, dict):
        raise ValueError("Equity research AI output must contain a research object.")
    usage_payload = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
    return EquityResearchProviderResponse(
        provider=_optional_text(payload.get("provider")) or CODEX_OAUTH_PROVIDER,
        model_name=_optional_text(payload.get("model_name") or payload.get("model")) or DEFAULT_MODEL_NAME,
        reasoning_effort=_optional_text(payload.get("reasoning_effort")) or DEFAULT_REASONING_EFFORT,
        output=_sanitize_output(parse_equity_research_output(research_payload), context=context),
        input_token_count=_optional_int(usage_payload.get("input_tokens")),
        output_token_count=_optional_int(usage_payload.get("output_tokens")),
        cached_input_token_count=_optional_int(usage_payload.get("cached_input_tokens")),
        estimated_cost_usd=_optional_decimal(usage_payload.get("estimated_cost_usd")),
        latency_ms=_optional_int(usage_payload.get("latency_ms")),
    )


def parse_equity_research_output(payload: Mapping[str, object]) -> EquityResearchOutput:
    return EquityResearchOutput(
        title=_required_text(payload, "title"),
        korean_summary=_required_text(payload, "korean_summary"),
        key_points=_text_tuple(payload.get("key_points"), limit=7),
        catalysts=_text_tuple(payload.get("catalysts"), limit=6),
        risks=_text_tuple(payload.get("risks"), limit=8),
        invalidation_conditions=_text_tuple(payload.get("invalidation_conditions"), limit=8),
        valuation_sensitivity=_valuation_sensitivity_dict(payload.get("valuation_sensitivity")),
    )


def invoke_codex_oauth_equity_research_provider(
    context: dict[str, object],
    model_name: str,
    reasoning_effort: str | None,
    max_context_chars: int,
) -> EquityResearchProviderResponse:
    command_text = os.getenv("STOCKANALYSIS_CODEX_CLI_COMMAND", "codex").strip() or "codex"
    try:
        base_command = shlex.split(command_text)
    except ValueError as exc:
        raise ValueError(f"Invalid STOCKANALYSIS_CODEX_CLI_COMMAND: {exc}.") from exc
    if not base_command:
        raise ValueError("STOCKANALYSIS_CODEX_CLI_COMMAND must not be empty.")
    timeout_seconds = int(os.getenv("STOCKANALYSIS_CODEX_TIMEOUT_SECONDS", "300"))
    if timeout_seconds <= 0:
        raise ValueError("STOCKANALYSIS_CODEX_TIMEOUT_SECONDS must be greater than 0.")

    prompt = build_codex_oauth_equity_research_prompt(context, max_context_chars=max_context_chars)
    output_schema = build_codex_oauth_equity_research_output_schema()
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="stockanalysis-equity-research-codex-oauth.") as tmpdir:
        tmp_path = Path(tmpdir)
        schema_path = tmp_path / "equity-research.schema.json"
        output_path = tmp_path / "last-message.json"
        schema_path.write_text(json.dumps(output_schema, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        command = [
            *base_command,
            "-c",
            'approval_policy="never"',
            "--sandbox",
            "read-only",
            "--cd",
            os.getenv("STOCKANALYSIS_CODEX_WORKDIR") or _default_codex_workdir(),
            "exec",
        ]
        if _bool_env("STOCKANALYSIS_CODEX_SKIP_GIT_REPO_CHECK", default=True):
            command.append("--skip-git-repo-check")
        command.extend(
            [
                "--ephemeral",
                "--ignore-user-config",
                "--ignore-rules",
                "--output-schema",
                str(schema_path),
                "--output-last-message",
                str(output_path),
            ]
        )
        if model_name and model_name not in {DEFAULT_MODEL_NAME, "default"}:
            command.extend(["--model", model_name])
        command.append("-")
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        latency_ms = int((time.monotonic() - started) * 1000)
        if completed.returncode != 0:
            stderr = (completed.stderr or completed.stdout or "codex exec failed").strip()
            raise RuntimeError(
                f"codex_oauth equity research provider failed "
                f"(exit_code={completed.returncode}): {_diagnostic_excerpt(stderr, 2000)}"
            )
        output_text = output_path.read_text(encoding="utf-8") if output_path.exists() else completed.stdout
    parsed = parse_equity_research_response_payload(_loads_json_object(output_text), context=context)
    return EquityResearchProviderResponse(
        provider=CODEX_OAUTH_PROVIDER,
        model_name=parsed.model_name,
        reasoning_effort=parsed.reasoning_effort or reasoning_effort,
        output=parsed.output,
        input_token_count=parsed.input_token_count or _token_count(prompt),
        output_token_count=parsed.output_token_count,
        cached_input_token_count=parsed.cached_input_token_count,
        estimated_cost_usd=parsed.estimated_cost_usd,
        latency_ms=parsed.latency_ms or latency_ms,
    )


def build_fixture_equity_research_response(
    context: dict[str, object],
    model_name: str,
    reasoning_effort: str | None,
    max_context_chars: int,
) -> EquityResearchProviderResponse:
    instrument = _as_dict(context.get("instrument"))
    symbol = str(instrument.get("primary_symbol") or _as_dict(context.get("query")).get("symbol") or "UNKNOWN").upper()
    name = str(instrument.get("name") or symbol)
    recommendation = _as_dict(context.get("recommendation"))
    thesis = _as_dict(context.get("thesis"))
    financial_metrics = _as_list(context.get("financial_metrics"))
    valuations = _as_list(context.get("valuations"))
    peer_rows = _as_list(context.get("peer_relative"))
    latest_event = _first_dict(context.get("recent_events"))
    metric_summary = _fixture_metric_summary(financial_metrics)
    valuation_summary = _fixture_valuation_summary(valuations)
    peer_summary = _fixture_peer_summary(peer_rows)
    action = recommendation.get("action") or "recommendation_missing"
    summary = (
        f"{symbol}({name})는 중장기 관점에서 {action} 후보로 검토된다. "
        f"재무 근거는 {metric_summary}, 피어 비교는 {peer_summary}, 밸류에이션은 {valuation_summary} 상태다. "
        "이 리포트는 주문 결정을 하지 않고, 재무·밸류에이션·thesis 검토 근거를 저장한다."
    )
    key_points = _non_empty_tuple(
        (
            f"최신 추천: {action}, 점수 {recommendation.get('total_score')}" if recommendation else "최신 추천 기록이 없다.",
            f"재무 지표: {metric_summary}",
            f"피어 비교: {peer_summary}",
            f"밸류에이션: {valuation_summary}",
            f"투자 논리: {thesis.get('title')}" if thesis else "연결된 투자 논리가 부족하다.",
        ),
        limit=7,
    )
    catalysts = _non_empty_tuple(
        (
            f"최근 뉴스: {latest_event.get('korean_title') or latest_event.get('title')}" if latest_event else "",
            f"추천 배치 기준일 {recommendation.get('as_of_date')}" if recommendation else "",
            "사이클 요약과 종목 노출도가 업데이트되면 다음 배치에서 재검토한다.",
        ),
        limit=6,
    )
    risks = _non_empty_tuple(
        (
            "무료 SEC/companyfacts와 가격 데이터 기반이므로 segment, footnote, guidance 정보가 제한적이다.",
            "밸류에이션 스냅샷은 DCF-lite와 상대배수의 보수적 초안이며 목표주가가 아니다.",
            "성과 표본이 충분하기 전까지 fundamental component weight는 0으로 유지한다.",
        ),
        limit=8,
    )
    invalidation = _non_empty_tuple(
        (
            str(thesis.get("invalidation_conditions") or "").strip(),
            "재무 품질, 밸류에이션 안전마진, 피어 상대 위치가 동시에 악화되면 재검토한다.",
        ),
        limit=8,
    )
    output = EquityResearchOutput(
        title=f"{symbol} 기업 리서치 요약",
        korean_summary=summary,
        key_points=key_points,
        catalysts=catalysts,
        risks=risks,
        invalidation_conditions=invalidation,
        valuation_sensitivity=_fixture_valuation_sensitivity(valuations),
    )
    prompt = build_codex_oauth_equity_research_prompt(context, max_context_chars=max_context_chars)
    return EquityResearchProviderResponse(
        provider=FIXTURE_PROVIDER,
        model_name=model_name or "equity-research-fixture-v1",
        reasoning_effort=reasoning_effort,
        output=_sanitize_output(output, context=context),
        input_token_count=_token_count(prompt),
        output_token_count=_token_count(json.dumps(_output_to_json(output), ensure_ascii=False)),
        cached_input_token_count=0,
        estimated_cost_usd=Decimal("0"),
        latency_ms=0,
    )


def run_equity_research_reporting(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    symbols: Iterable[str] = (),
    limit: int = 5,
    provider: str = CODEX_OAUTH_PROVIDER,
    model_name: str = DEFAULT_MODEL_NAME,
    reasoning_effort: str | None = DEFAULT_REASONING_EFFORT,
    max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
    provider_runner: EquityResearchProviderRunner | None = None,
) -> dict[str, object]:
    if limit < 1 or limit > 50:
        raise ValueError("limit must be between 1 and 50.")
    if max_context_chars < 2000 or max_context_chars > 100000:
        raise ValueError("max_context_chars must be between 2000 and 100000.")
    if provider not in {FIXTURE_PROVIDER, CODEX_OAUTH_PROVIDER}:
        raise ValueError("Supported equity research providers are fixture and codex_oauth.")
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    selected_symbols = _load_equity_research_symbols(sql_executor, as_of_date=as_of_date, symbols=symbols, limit=limit)
    contexts = tuple(
        load_equity_research_context(
            config=config,
            symbol=symbol,
            as_of_date=as_of_date,
            limit=8,
            executor=sql_executor,
        )
        for symbol in selected_symbols
    )
    preview = tuple(build_fixture_equity_research_response(context, model_name, reasoning_effort, max_context_chars) for context in contexts[:3])
    report: dict[str, object] = {
        "report_name": DEFAULT_PIPELINE_NAME,
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "artifact_type": ARTIFACT_TYPE,
        "as_of_date": as_of_date.isoformat(),
        "provider": provider,
        "model_name": model_name,
        "symbol_count": len(contexts),
        "symbol_preview": selected_symbols[:10],
        "artifact_preview": [_output_to_json(response.output) for response in preview],
        "recommendation_scoring_mutated": False,
        "broker_order_submit_enabled": False,
    }
    if not execute:
        return report
    if not contexts:
        return {**report, "status": "completed", "run_id": None, "inserted_artifact_count": 0}

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "artifact_type": ARTIFACT_TYPE,
            "provider": provider,
            "model_name": model_name,
            "reasoning_effort": reasoning_effort,
            "limit": limit,
            "symbols": selected_symbols,
            "max_context_chars": max_context_chars,
            "offline_batch_only": True,
            "recommendation_scoring_mutated": False,
            "broker_order_submit_enabled": False,
        },
    )
    inserted = 0
    failed = 0
    results = []
    try:
        prompt_template_id = int(sql_executor.execute_scalar(render_equity_research_prompt_template_upsert_sql()))
        for context in contexts:
            symbol = _symbol_from_context(context)
            request_hash = build_equity_research_request_hash(
                context=context,
                provider=provider,
                model_name=model_name,
                prompt_template_id=prompt_template_id,
                max_context_chars=max_context_chars,
            )
            invocation_id: int | None = None
            try:
                response = _invoke_provider(
                    context,
                    provider=provider,
                    model_name=model_name,
                    reasoning_effort=reasoning_effort,
                    max_context_chars=max_context_chars,
                    provider_runner=provider_runner,
                )
                invocation_id = int(
                    sql_executor.execute_scalar(
                        render_equity_research_model_invocation_insert_sql(
                            run_id=run_id,
                            provider=response.provider,
                            model_name=response.model_name,
                            reasoning_effort=response.reasoning_effort,
                            prompt_template_id=prompt_template_id,
                            input_token_count=response.input_token_count,
                            output_token_count=response.output_token_count,
                            cached_input_token_count=response.cached_input_token_count,
                            estimated_cost_usd=response.estimated_cost_usd,
                            latency_ms=response.latency_ms,
                            status="succeeded",
                            error_summary=None,
                            request_hash=request_hash,
                        )
                    )
                )
            except Exception as exc:
                failed += 1
                _record_failed_invocation(
                    sql_executor,
                    run_id=run_id,
                    prompt_template_id=prompt_template_id,
                    provider=provider,
                    model_name=model_name,
                    reasoning_effort=reasoning_effort,
                    error_summary=str(exc),
                    request_hash=request_hash,
                )
                response = build_fixture_equity_research_response(
                    context,
                    model_name="equity-research-fallback-v1",
                    reasoning_effort=None,
                    max_context_chars=max_context_chars,
                )
            sql_executor.execute_scalar(
                render_equity_research_artifact_upsert_sql(
                    context=context,
                    response=response,
                    as_of_date=as_of_date,
                    source_run_id=run_id,
                )
            )
            inserted += 1
            results.append(
                {
                    "symbol": symbol,
                    "status": "reported" if invocation_id is not None or provider == FIXTURE_PROVIDER else "reported_with_fallback",
                    "invocation_id": invocation_id,
                    "provider": response.provider,
                }
            )
        if failed:
            _mark_pipeline_run_succeeded_with_fallback(sql_executor, run_id, failed_report_count=failed)
        else:
            _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise
    return {
        **report,
        "status": "completed" if failed == 0 else "completed_with_fallback",
        "run_id": run_id,
        "inserted_artifact_count": inserted,
        "failed_artifact_count": failed,
        "results": results,
    }


def load_equity_research_context(
    *,
    config: RuntimeConfig,
    symbol: str,
    as_of_date: date,
    limit: int = 8,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(sql_executor.execute_scalar(render_equity_research_context_sql(symbol=symbol, as_of_date=as_of_date, limit=limit)))
    if not isinstance(payload, dict):
        raise ValueError("Equity research context lookup did not return a JSON object.")
    if not payload.get("instrument"):
        raise ValueError(f"No active instrument found for symbol: {symbol}.")
    return payload


def render_equity_research_prompt_template_upsert_sql() -> str:
    schema = json.dumps(build_codex_oauth_equity_research_output_schema()["properties"]["research"], ensure_ascii=False, sort_keys=True)
    return f"""insert into ai.prompt_template (
    template_name,
    template_version,
    system_purpose,
    template_text,
    output_schema_json,
    is_active
)
values (
    {sql_literal(DEFAULT_TASK_NAME)},
    {sql_literal(DEFAULT_TEMPLATE_VERSION)},
    'Generate Korean professional equity research artifacts from bounded Postgres context.',
    'Return Korean business, financial, peer, valuation, catalyst, risk, invalidation, and sensitivity fields. No request-time AI and no trade decisions.',
    {sql_literal(schema)}::jsonb,
    true
)
on conflict (template_name, template_version) do update
set
    system_purpose = excluded.system_purpose,
    template_text = excluded.template_text,
    output_schema_json = excluded.output_schema_json,
    is_active = excluded.is_active
returning template_id;"""


def render_equity_research_model_invocation_insert_sql(
    *,
    run_id: int,
    provider: str,
    model_name: str,
    reasoning_effort: str | None,
    prompt_template_id: int,
    input_token_count: int | None,
    output_token_count: int | None,
    cached_input_token_count: int | None,
    estimated_cost_usd: Decimal | None,
    latency_ms: int | None,
    status: str,
    error_summary: str | None,
    request_hash: str | None,
) -> str:
    return f"""insert into ai.model_invocation (
    run_id,
    task_name,
    provider,
    model_name,
    reasoning_effort,
    prompt_template_id,
    input_token_count,
    output_token_count,
    cached_input_token_count,
    estimated_cost_usd,
    latency_ms,
    status,
    error_summary,
    request_hash
)
values (
    {run_id},
    {sql_literal(DEFAULT_TASK_NAME)},
    {sql_literal(provider)},
    {sql_literal(model_name)},
    {sql_literal(reasoning_effort)},
    {prompt_template_id},
    {sql_literal(input_token_count)},
    {sql_literal(output_token_count)},
    {sql_literal(cached_input_token_count)},
    {sql_literal(estimated_cost_usd)},
    {sql_literal(latency_ms)},
    {sql_literal(status)},
    {sql_literal(error_summary)},
    {sql_literal(request_hash)}
)
returning invocation_id;"""


def render_equity_research_artifact_upsert_sql(
    *,
    context: dict[str, object],
    response: EquityResearchProviderResponse,
    as_of_date: date,
    source_run_id: int,
) -> str:
    instrument = _as_dict(context.get("instrument"))
    instrument_id = int(instrument["instrument_id"])
    source_document_ids = _source_document_ids_from_context(context)
    output = _sanitize_output(response.output, context=context)
    return f"""insert into research.equity_research_artifact (
    instrument_id,
    as_of_date,
    artifact_type,
    provider,
    model_name,
    title,
    korean_summary,
    key_points_json,
    catalysts_json,
    risks_json,
    invalidation_conditions_json,
    valuation_sensitivity_json,
    source_document_ids,
    source_run_id
)
values (
    {instrument_id},
    {sql_date(as_of_date)},
    {sql_literal(ARTIFACT_TYPE)},
    {sql_literal(response.provider)},
    {sql_literal(response.model_name)},
    {sql_literal(output.title)},
    {sql_literal(output.korean_summary)},
    {sql_literal(json.dumps(list(output.key_points), ensure_ascii=False))}::jsonb,
    {sql_literal(json.dumps(list(output.catalysts), ensure_ascii=False))}::jsonb,
    {sql_literal(json.dumps(list(output.risks), ensure_ascii=False))}::jsonb,
    {sql_literal(json.dumps(list(output.invalidation_conditions), ensure_ascii=False))}::jsonb,
    {sql_literal(json.dumps(output.valuation_sensitivity, ensure_ascii=False, sort_keys=True))}::jsonb,
    {sql_literal(json.dumps(source_document_ids))}::jsonb,
    {source_run_id}
)
on conflict (instrument_id, as_of_date, artifact_type, provider, model_name) do update
set
    title = excluded.title,
    korean_summary = excluded.korean_summary,
    key_points_json = excluded.key_points_json,
    catalysts_json = excluded.catalysts_json,
    risks_json = excluded.risks_json,
    invalidation_conditions_json = excluded.invalidation_conditions_json,
    valuation_sensitivity_json = excluded.valuation_sensitivity_json,
    source_document_ids = excluded.source_document_ids,
    source_run_id = excluded.source_run_id
returning artifact_id;"""


def build_equity_research_request_hash(
    *,
    context: dict[str, object],
    provider: str,
    model_name: str,
    prompt_template_id: int,
    max_context_chars: int,
) -> str:
    payload = {
        "symbol": _symbol_from_context(context),
        "as_of_date": _as_dict(context.get("query")).get("as_of_date"),
        "provider": provider,
        "model_name": model_name,
        "prompt_template_id": prompt_template_id,
        "template_version": DEFAULT_TEMPLATE_VERSION,
        "context_hash": hashlib.sha256(
            json.dumps(_bounded_context_for_prompt(context, max_context_chars=max_context_chars), ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _load_equity_research_symbols(
    executor: PsqlCommandExecutor,
    *,
    as_of_date: date,
    symbols: Iterable[str],
    limit: int,
) -> list[str]:
    payload = json.loads(executor.execute_scalar(render_equity_research_symbol_lookup_sql(as_of_date=as_of_date, symbols=symbols, limit=limit)))
    if not isinstance(payload, list):
        raise ValueError("Equity research symbol lookup did not return a JSON array.")
    return [str(item).upper() for item in payload if str(item).strip()][:limit]


def _invoke_provider(
    context: dict[str, object],
    *,
    provider: str,
    model_name: str,
    reasoning_effort: str | None,
    max_context_chars: int,
    provider_runner: EquityResearchProviderRunner | None,
) -> EquityResearchProviderResponse:
    if provider_runner is not None:
        return provider_runner(context, model_name, reasoning_effort, max_context_chars)
    if provider == FIXTURE_PROVIDER:
        return build_fixture_equity_research_response(context, model_name, reasoning_effort, max_context_chars)
    return invoke_codex_oauth_equity_research_provider(context, model_name, reasoning_effort, max_context_chars)


def _mark_pipeline_run_succeeded_with_fallback(
    executor: PsqlCommandExecutor,
    run_id: int,
    *,
    failed_report_count: int,
) -> None:
    summary = f"{failed_report_count} equity research report(s) used fixture fallback; review ai.model_invocation errors."
    executor.execute_non_query(
        f"""update ops.pipeline_run
set
    status = 'succeeded_with_fallback',
    ended_at = now(),
    error_summary = {sql_literal(summary)}
where run_id = {run_id};"""
    )


def _record_failed_invocation(
    executor: PsqlCommandExecutor,
    *,
    run_id: int,
    prompt_template_id: int,
    provider: str,
    model_name: str,
    reasoning_effort: str | None,
    error_summary: str,
    request_hash: str | None,
) -> None:
    try:
        executor.execute_scalar(
            render_equity_research_model_invocation_insert_sql(
                run_id=run_id,
                provider=provider,
                model_name=model_name,
                reasoning_effort=reasoning_effort,
                prompt_template_id=prompt_template_id,
                input_token_count=None,
                output_token_count=None,
                cached_input_token_count=None,
                estimated_cost_usd=None,
                latency_ms=None,
                status="failed",
                error_summary=_diagnostic_excerpt(error_summary, 2000),
                request_hash=request_hash,
            )
        )
    except Exception:
        return


def _bounded_context_for_prompt(context: dict[str, object], *, max_context_chars: int) -> dict[str, object]:
    bounded = {
        "query": context.get("query"),
        "instrument": context.get("instrument"),
        "financial_metrics": _limit_list(context.get("financial_metrics"), 12),
        "financial_metric_status_counts": context.get("financial_metric_status_counts"),
        "peer_relative": _limit_list(context.get("peer_relative"), 12),
        "valuations": _limit_list(context.get("valuations"), 6),
        "recommendation": context.get("recommendation"),
        "fundamental_components": _limit_list(context.get("fundamental_components"), 8),
        "thesis": context.get("thesis"),
        "recent_events": _limit_list(context.get("recent_events"), 8),
        "cycle_summaries": _limit_list(context.get("cycle_summaries"), 8),
    }
    text = json.dumps(bounded, ensure_ascii=False, sort_keys=True)
    if len(text) <= max_context_chars:
        return bounded
    bounded["financial_metrics"] = _limit_list(context.get("financial_metrics"), 8)
    bounded["peer_relative"] = _limit_list(context.get("peer_relative"), 8)
    bounded["recent_events"] = _limit_list(context.get("recent_events"), 4)
    bounded["cycle_summaries"] = _limit_list(context.get("cycle_summaries"), 4)
    return bounded


def _sanitize_output(output: EquityResearchOutput, *, context: dict[str, object]) -> EquityResearchOutput:
    symbol = _symbol_from_context(context)
    title = output.title if symbol in output.title else f"{symbol} {output.title}"
    return EquityResearchOutput(
        title=title[:200],
        korean_summary=output.korean_summary[:2000],
        key_points=_non_empty_tuple(output.key_points, limit=7),
        catalysts=_non_empty_tuple(output.catalysts, limit=6),
        risks=_non_empty_tuple(output.risks, limit=8),
        invalidation_conditions=_non_empty_tuple(output.invalidation_conditions, limit=8),
        valuation_sensitivity=_sanitize_valuation_sensitivity(output.valuation_sensitivity),
    )


def _sanitize_valuation_sensitivity(value: dict[str, object]) -> dict[str, object]:
    allowed = {"base_case", "upside_case", "downside_case", "margin_of_safety_view", "confidence"}
    sanitized = {key: value.get(key) for key in allowed if key in value}
    for key in ("base_case", "upside_case", "downside_case", "margin_of_safety_view"):
        sanitized[key] = str(sanitized.get(key) or "근거 부족").strip()[:500]
    confidence = _optional_decimal(sanitized.get("confidence"))
    sanitized["confidence"] = float(max(Decimal("0"), min(Decimal("1"), confidence or Decimal("0.35"))))
    return sanitized


def _source_document_ids_from_context(context: dict[str, object]) -> list[int]:
    ids = []
    for row in _as_list(context.get("recent_events")):
        document_id = _optional_int(_as_dict(row).get("document_id"))
        if document_id is not None and document_id not in ids:
            ids.append(document_id)
    return ids[:50]


def _output_to_json(output: EquityResearchOutput) -> dict[str, object]:
    return {
        "title": output.title,
        "korean_summary": output.korean_summary,
        "key_points": list(output.key_points),
        "catalysts": list(output.catalysts),
        "risks": list(output.risks),
        "invalidation_conditions": list(output.invalidation_conditions),
        "valuation_sensitivity": output.valuation_sensitivity,
    }


def _valuation_sensitivity_dict(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError("valuation_sensitivity must be an object.")
    return _sanitize_valuation_sensitivity(dict(value))


def _fixture_metric_summary(rows: list[object]) -> str:
    computed = [row for row in rows if _as_dict(row).get("metric_status") == "computed"]
    if not computed:
        return "계산 가능한 재무지표가 부족하다"
    names = [str(_as_dict(row).get("metric_code")) for row in computed[:4]]
    return f"{len(computed)}개 계산 지표({', '.join(names)})"


def _fixture_peer_summary(rows: list[object]) -> str:
    usable = [row for row in rows if _as_dict(row).get("relative_signal") != "insufficient_data"]
    if not usable:
        return "피어 비교 표본이 부족하다"
    avg = sum(float(_as_dict(row).get("percentile_rank") or 0) for row in usable) / len(usable)
    return f"평균 피어 백분위 {avg:.2f}"


def _fixture_valuation_summary(rows: list[object]) -> str:
    if not rows:
        return "밸류에이션 스냅샷이 없다"
    margins = [_optional_decimal(_as_dict(row).get("margin_of_safety")) for row in rows]
    margins = [margin for margin in margins if margin is not None]
    if not margins:
        return f"{len(rows)}개 방식은 있으나 안전마진 계산이 제한적이다"
    avg = sum(margins, Decimal("0")) / Decimal(len(margins))
    return f"{len(rows)}개 방식 평균 안전마진 {avg:.4f}"


def _fixture_valuation_sensitivity(rows: list[object]) -> dict[str, object]:
    if not rows:
        return {
            "base_case": "밸류에이션 스냅샷이 없어 기준 시나리오를 확정하지 않는다.",
            "upside_case": "추가 재무/가격 데이터 확보 후 재평가한다.",
            "downside_case": "재무 공백이 계속되면 투자 논리 신뢰도가 낮아진다.",
            "margin_of_safety_view": "안전마진 미측정",
            "confidence": 0.25,
        }
    methods = ", ".join(str(_as_dict(row).get("method")) for row in rows[:4])
    margin_text = _fixture_valuation_summary(rows)
    return {
        "base_case": f"{methods} 기준 {margin_text}.",
        "upside_case": "매출 성장, 현금흐름 품질, 피어 상대 위치가 동시에 개선되면 상단 시나리오를 재검토한다.",
        "downside_case": "현금흐름 또는 밸류에이션 안전마진이 악화되면 하단 시나리오를 우선한다.",
        "margin_of_safety_view": margin_text,
        "confidence": 0.45,
    }


def _symbol_from_context(context: dict[str, object]) -> str:
    instrument = _as_dict(context.get("instrument"))
    return str(instrument.get("primary_symbol") or _as_dict(context.get("query")).get("symbol") or "").upper()


def _normalize_symbols(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    symbols = []
    for value in values:
        symbol = str(value).strip().upper()
        if symbol and symbol not in seen:
            seen.add(symbol)
            symbols.append(symbol)
    return tuple(symbols)


def _loads_json_object(value: str) -> dict[str, object]:
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("Expected a JSON object.")
    return parsed


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _limit_list(value: object, limit: int) -> list[object]:
    return _as_list(value)[:limit]


def _first_dict(value: object) -> dict[str, Any]:
    rows = _as_list(value)
    return _as_dict(rows[0]) if rows else {}


def _required_text(payload: Mapping[str, object], key: str) -> str:
    value = str(payload.get(key) or "").strip()
    if not value:
        raise ValueError(f"Equity research output missing required field: {key}.")
    return value


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_decimal(value: object) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _text_tuple(value: object, *, limit: int) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return _non_empty_tuple((str(item).strip() for item in value), limit=limit)


def _non_empty_tuple(values: Iterable[str], *, limit: int) -> tuple[str, ...]:
    rows = []
    for value in values:
        text = str(value).strip()
        if text:
            rows.append(text[:1000])
        if len(rows) >= limit:
            break
    return tuple(rows)


def _token_count(text: str) -> int:
    return max(1, len(re.findall(r"\S+", text)))


def _diagnostic_excerpt(value: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    return text[:limit]


def _bool_env(name: str, *, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _default_codex_workdir() -> str:
    return str(Path(__file__).resolve().parents[3])
