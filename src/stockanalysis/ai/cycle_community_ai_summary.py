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

from stockanalysis.ai.cycle_graph_context import (
    build_cycle_community_summary,
    load_cycle_graph_context,
    load_cycle_graph_context_node_codes,
)
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_PIPELINE_NAME = "cycle_community_ai_summary"
DEFAULT_TASK_NAME = "cycle-community-ai-summary-v2"
DEFAULT_TEMPLATE_VERSION = "2026-05-24-cycle-community-ai-v2"
SUMMARY_TYPE = "cycle_community_ai_v2"
FIXTURE_PROVIDER = "fixture"
CODEX_OAUTH_PROVIDER = "codex_oauth"
DEFAULT_MODEL_NAME = "codex-cli-default"
DEFAULT_REASONING_EFFORT = "low"
DEFAULT_MAX_CONTEXT_CHARS = 12000


@dataclass(frozen=True)
class CycleCommunityAiSummaryOutput:
    korean_summary: str
    key_drivers: tuple[str, ...]
    causal_paths: tuple[dict[str, object], ...]
    supporting_events: tuple[dict[str, object], ...]
    conflicts: tuple[str, ...]
    uncertainty: str
    watchlist_symbols: tuple[str, ...]

    def as_summary_json(self) -> dict[str, object]:
        return {
            "korean_summary": self.korean_summary,
            "key_drivers": list(self.key_drivers),
            "causal_paths": list(self.causal_paths),
            "supporting_events": list(self.supporting_events),
            "conflicts": list(self.conflicts),
            "uncertainty": self.uncertainty,
            "watchlist_symbols": list(self.watchlist_symbols),
        }


@dataclass(frozen=True)
class CycleCommunityAiProviderResponse:
    provider: str
    model_name: str
    reasoning_effort: str | None
    output: CycleCommunityAiSummaryOutput
    input_token_count: int | None = None
    output_token_count: int | None = None
    cached_input_token_count: int | None = None
    estimated_cost_usd: Decimal | None = None
    latency_ms: int | None = None


CycleCommunityAiProviderRunner = Callable[
    [dict[str, object], str, str | None, int],
    CycleCommunityAiProviderResponse,
]


def build_codex_oauth_cycle_community_ai_prompt(context: dict[str, object], *, max_context_chars: int) -> str:
    bounded_context = _bounded_context_for_prompt(context, max_context_chars=max_context_chars)
    return "\n".join(
        (
            "You are a cycle-level investment intelligence summarizer.",
            "Use only the supplied Postgres graph context. Do not browse, do not call tools, and do not make buy/sell/order decisions.",
            "Return exactly one JSON object matching the provided output schema.",
            "Write every human-readable field in Korean.",
            "Keep machine identifiers unchanged: node codes, event ids, and ticker symbols.",
            "Summarize the node as a market/cycle community: macro/domain/theme flow, evidence, conflicts, uncertainty, and watchlist symbols.",
            "Ground every watchlist symbol in exposed_instruments, propagated_impacts, or recommendations from the context.",
            "Ground supporting_events in direct_events or propagated_impacts from the context.",
            "If the context is weak, say so in uncertainty instead of inventing facts.",
            "Do not change recommendation scores. The output is explanatory context for later deterministic scoring.",
            "",
            "Output schema intent:",
            "- korean_summary: one concise Korean paragraph explaining the cycle community.",
            "- key_drivers: 2-6 Korean bullets describing what is moving the flow.",
            "- causal_paths: Korean explanations of macro/domain/theme -> symbol or child-node paths.",
            "- supporting_events: event ids/titles from the context that justify the summary.",
            "- conflicts: conflicting signals or missing evidence.",
            "- uncertainty: what must be checked next.",
            "- watchlist_symbols: only grounded ticker symbols from context.",
            "",
            "Postgres graph context:",
            json.dumps(bounded_context, ensure_ascii=False, sort_keys=True),
        )
    )


def build_codex_oauth_cycle_community_ai_output_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["summary"],
        "properties": {
            "summary": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "korean_summary",
                    "key_drivers",
                    "causal_paths",
                    "supporting_events",
                    "conflicts",
                    "uncertainty",
                    "watchlist_symbols",
                ],
                "properties": {
                    "korean_summary": {"type": "string"},
                    "key_drivers": {"type": "array", "items": {"type": "string"}},
                    "causal_paths": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["path", "explanation", "confidence"],
                            "properties": {
                                "path": {"type": "array", "items": {"type": "string"}},
                                "explanation": {"type": "string"},
                                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            },
                        },
                    },
                    "supporting_events": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["event_id", "title", "reason"],
                            "properties": {
                                "event_id": {"type": ["integer", "null"]},
                                "title": {"type": "string"},
                                "reason": {"type": "string"},
                            },
                        },
                    },
                    "conflicts": {"type": "array", "items": {"type": "string"}},
                    "uncertainty": {"type": "string"},
                    "watchlist_symbols": {"type": "array", "items": {"type": "string"}},
                },
            },
            "usage": {
                "type": "object",
                "additionalProperties": True,
            },
        },
    }


def parse_cycle_community_ai_response_payload(
    payload: dict[str, object],
    *,
    context: dict[str, object],
) -> CycleCommunityAiProviderResponse:
    summary_payload = payload.get("summary")
    if not isinstance(summary_payload, dict):
        raise ValueError("Cycle community AI output must contain a summary object.")
    usage_payload = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
    return CycleCommunityAiProviderResponse(
        provider=_optional_text(payload.get("provider")) or CODEX_OAUTH_PROVIDER,
        model_name=_optional_text(payload.get("model_name") or payload.get("model")) or DEFAULT_MODEL_NAME,
        reasoning_effort=_optional_text(payload.get("reasoning_effort")) or DEFAULT_REASONING_EFFORT,
        output=_sanitize_output(parse_cycle_community_ai_summary(summary_payload), context=context),
        input_token_count=_optional_int(usage_payload.get("input_tokens")),
        output_token_count=_optional_int(usage_payload.get("output_tokens")),
        cached_input_token_count=_optional_int(usage_payload.get("cached_input_tokens")),
        estimated_cost_usd=_optional_decimal(usage_payload.get("estimated_cost_usd")),
        latency_ms=_optional_int(usage_payload.get("latency_ms")),
    )


def parse_cycle_community_ai_summary(payload: Mapping[str, object]) -> CycleCommunityAiSummaryOutput:
    return CycleCommunityAiSummaryOutput(
        korean_summary=_required_text(payload, "korean_summary"),
        key_drivers=_text_tuple(payload.get("key_drivers"), limit=6),
        causal_paths=_causal_path_tuple(payload.get("causal_paths"), limit=6),
        supporting_events=_supporting_event_tuple(payload.get("supporting_events"), limit=8),
        conflicts=_text_tuple(payload.get("conflicts"), limit=6),
        uncertainty=_required_text(payload, "uncertainty"),
        watchlist_symbols=_symbol_tuple(payload.get("watchlist_symbols"), limit=12),
    )


def invoke_codex_oauth_cycle_community_ai_provider(
    context: dict[str, object],
    model_name: str,
    reasoning_effort: str | None,
    max_context_chars: int,
) -> CycleCommunityAiProviderResponse:
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

    prompt = build_codex_oauth_cycle_community_ai_prompt(context, max_context_chars=max_context_chars)
    output_schema = build_codex_oauth_cycle_community_ai_output_schema()
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="stockanalysis-cycle-community-codex-oauth.") as tmpdir:
        tmp_path = Path(tmpdir)
        schema_path = tmp_path / "cycle-community-ai-summary.schema.json"
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
                f"codex_oauth cycle community provider failed "
                f"(exit_code={completed.returncode}): {_diagnostic_excerpt(stderr, 2000)}"
            )
        output_text = output_path.read_text(encoding="utf-8") if output_path.exists() else completed.stdout
    parsed = parse_cycle_community_ai_response_payload(_loads_json_object(output_text), context=context)
    return CycleCommunityAiProviderResponse(
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


def build_fixture_cycle_community_ai_response(
    context: dict[str, object],
    model_name: str,
    reasoning_effort: str | None,
    max_context_chars: int,
) -> CycleCommunityAiProviderResponse:
    summary = build_cycle_community_summary(context)
    summary_json = summary.summary_json
    node = _as_dict(summary_json.get("node"))
    counts = _as_dict(summary_json.get("counts"))
    node_code = str(node.get("code") or summary.node_code)
    cycle_state = str(summary_json.get("cycle_state") or "unknown")
    cycle_score = _optional_text(summary_json.get("cycle_score"))
    recent_titles = _text_tuple(summary_json.get("recent_event_titles"), limit=5)
    symbols = _symbol_tuple(summary_json.get("top_symbols"), limit=8)
    parent_codes = _text_tuple(summary_json.get("parent_codes"), limit=4)
    child_codes = _text_tuple(summary_json.get("child_codes"), limit=4)
    event_count = int(counts.get("direct_event_count") or 0)
    propagated_count = int(counts.get("propagated_impact_count") or 0)
    score_part = f", cycle score {cycle_score}" if cycle_score else ""
    korean_summary = (
        f"{node_code} 흐름은 현재 {cycle_state}{score_part} 상태다. "
        f"최근 직접 뉴스 {event_count}건과 전파 영향 {propagated_count}건을 기준으로 "
        f"연결 종목 {', '.join(symbols) if symbols else '없음'}을 점검해야 한다."
    )
    drivers = _non_empty_tuple(
        (
            f"상위 연결: {', '.join(parent_codes)}" if parent_codes else "",
            f"하위 연결: {', '.join(child_codes)}" if child_codes else "",
            f"대표 뉴스: {recent_titles[0]}" if recent_titles else "",
            f"전파 영향 {propagated_count}건이 종목 노출로 이어진다." if propagated_count else "",
        ),
        limit=6,
    )
    output = CycleCommunityAiSummaryOutput(
        korean_summary=korean_summary,
        key_drivers=drivers or ("현재 graph context가 제한적이다.",),
        causal_paths=_fixture_causal_paths(node_code=node_code, child_codes=child_codes, symbols=symbols),
        supporting_events=_fixture_supporting_events(context),
        conflicts=_fixture_conflicts(context),
        uncertainty="AI가 직접 투자 결정을 내리지 않는다. 원천 뉴스, 사이클 상태, 추천 점수의 정합성을 다음 배치에서 다시 확인해야 한다.",
        watchlist_symbols=symbols,
    )
    prompt = build_codex_oauth_cycle_community_ai_prompt(context, max_context_chars=max_context_chars)
    return CycleCommunityAiProviderResponse(
        provider=FIXTURE_PROVIDER,
        model_name=model_name or "cycle-community-ai-fixture-v2",
        reasoning_effort=reasoning_effort,
        output=_sanitize_output(output, context=context),
        input_token_count=_token_count(prompt),
        output_token_count=_token_count(json.dumps(output.as_summary_json(), ensure_ascii=False)),
        cached_input_token_count=0,
        estimated_cost_usd=Decimal("0"),
        latency_ms=0,
    )


def run_cycle_community_ai_summary_v2(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    node_codes: Iterable[str] = (),
    limit: int = 12,
    max_nodes: int = 20,
    provider: str = CODEX_OAUTH_PROVIDER,
    model_name: str = DEFAULT_MODEL_NAME,
    reasoning_effort: str | None = DEFAULT_REASONING_EFFORT,
    max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
    provider_runner: CycleCommunityAiProviderRunner | None = None,
) -> dict[str, object]:
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")
    if max_nodes < 1 or max_nodes > 200:
        raise ValueError("max_nodes must be between 1 and 200.")
    if max_context_chars < 1000 or max_context_chars > 100000:
        raise ValueError("max_context_chars must be between 1000 and 100000.")
    if provider not in {FIXTURE_PROVIDER, CODEX_OAUTH_PROVIDER}:
        raise ValueError("Supported cycle community AI providers are fixture and codex_oauth.")

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    selected_codes = _normalize_node_codes(node_codes)
    if not selected_codes:
        selected_codes = load_cycle_graph_context_node_codes(
            config=config,
            as_of_date=as_of_date,
            limit=max_nodes,
            executor=sql_executor,
        )
    selected_codes = selected_codes[:max_nodes]
    contexts = tuple(
        load_cycle_graph_context(
            config=config,
            node_code=node_code,
            as_of_date=as_of_date,
            limit=limit,
            executor=sql_executor,
        )
        for node_code in selected_codes
    )
    planned_preview = tuple(build_fixture_cycle_community_ai_response(context, model_name, reasoning_effort, max_context_chars) for context in contexts[:3])
    base_report: dict[str, object] = {
        "report_name": "cycle_community_ai_summary_v2",
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "summary_type": SUMMARY_TYPE,
        "provider": provider,
        "model_name": model_name,
        "node_count": len(contexts),
        "node_code_preview": [_node_code_from_context(context) for context in contexts[:10]],
        "summary_preview": [response.output.as_summary_json() for response in planned_preview],
    }
    if not execute:
        return base_report
    if not contexts:
        return {**base_report, "status": "completed", "run_id": None, "inserted_summary_count": 0}

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "summary_type": SUMMARY_TYPE,
            "provider": provider,
            "model_name": model_name,
            "reasoning_effort": reasoning_effort,
            "limit": limit,
            "max_nodes": max_nodes,
            "max_context_chars": max_context_chars,
            "offline_batch_only": True,
        },
    )
    rows = []
    results = []
    failed = 0
    prompt_template_id = 0
    try:
        prompt_template_id = int(sql_executor.execute_scalar(render_cycle_community_ai_prompt_template_upsert_sql()))
        for context in contexts:
            node_code = _node_code_from_context(context)
            request_hash = build_cycle_community_ai_request_hash(
                context=context,
                provider=provider,
                model_name=model_name,
                prompt_template_id=prompt_template_id,
                max_context_chars=max_context_chars,
            )
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
                        render_cycle_community_ai_model_invocation_insert_sql(
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
                rows.append(_build_summary_row(context, response=response, as_of_date=as_of_date, invocation_id=invocation_id))
                results.append({"node_code": node_code, "status": "summarized", "invocation_id": invocation_id})
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
                fallback_response = build_fixture_cycle_community_ai_response(
                    context,
                    model_name="cycle-community-ai-fallback-v2",
                    reasoning_effort=None,
                    max_context_chars=max_context_chars,
                )
                rows.append(_build_summary_row(context, response=fallback_response, as_of_date=as_of_date, invocation_id=None))
                results.append({"node_code": node_code, "status": "summarized_with_fallback", "error": _diagnostic_excerpt(str(exc), 500)})
        if rows:
            sql_executor.execute_non_query(render_cycle_community_ai_summary_upsert_sql(tuple(rows), as_of_date=as_of_date, source_run_id=run_id))
        if failed:
            _mark_pipeline_run_succeeded_with_fallback(sql_executor, run_id, failed_summary_count=failed)
        else:
            _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise
    return {
        **base_report,
        "status": "completed" if failed == 0 else "completed_with_fallback",
        "run_id": run_id,
        "inserted_summary_count": len(rows),
        "failed_summary_count": failed,
        "results": results,
    }


@dataclass(frozen=True)
class _SummaryRow:
    node_id: int
    node_code: str
    summary_json: dict[str, object]


def render_cycle_community_ai_summary_upsert_sql(
    rows: tuple[_SummaryRow, ...],
    *,
    as_of_date: date,
    source_run_id: int,
) -> str:
    if not rows:
        raise ValueError("At least one cycle community AI summary row is required.")
    values = ",\n        ".join(_render_summary_value_tuple(row, as_of_date=as_of_date, source_run_id=source_run_id) for row in rows)
    return f"""insert into ai.cycle_community_summary (
    node_id,
    as_of_date,
    summary_type,
    summary_json,
    source_run_id
)
values
        {values}
on conflict (node_id, as_of_date, summary_type) do update
set
    summary_json = excluded.summary_json,
    source_run_id = excluded.source_run_id,
    updated_at = now();"""


def render_cycle_community_ai_prompt_template_upsert_sql() -> str:
    schema = json.dumps(build_codex_oauth_cycle_community_ai_output_schema()["properties"]["summary"], ensure_ascii=False, sort_keys=True)
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
    'Summarize cycle graph communities using bounded Postgres ontology-lite context.',
    'Return Korean cycle-level drivers, causal paths, supporting events, conflicts, uncertainty, and grounded watchlist symbols. No request-time AI and no trade decisions.',
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


def render_cycle_community_ai_model_invocation_insert_sql(
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


def build_cycle_community_ai_request_hash(
    *,
    context: dict[str, object],
    provider: str,
    model_name: str,
    prompt_template_id: int,
    max_context_chars: int,
) -> str:
    payload = {
        "node_code": _node_code_from_context(context),
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


def _invoke_provider(
    context: dict[str, object],
    *,
    provider: str,
    model_name: str,
    reasoning_effort: str | None,
    max_context_chars: int,
    provider_runner: CycleCommunityAiProviderRunner | None,
) -> CycleCommunityAiProviderResponse:
    if provider_runner is not None:
        return provider_runner(context, model_name, reasoning_effort, max_context_chars)
    if provider == FIXTURE_PROVIDER:
        return build_fixture_cycle_community_ai_response(context, model_name, reasoning_effort, max_context_chars)
    return invoke_codex_oauth_cycle_community_ai_provider(context, model_name, reasoning_effort, max_context_chars)


def _build_summary_row(
    context: dict[str, object],
    *,
    response: CycleCommunityAiProviderResponse,
    as_of_date: date,
    invocation_id: int | None,
) -> _SummaryRow:
    target_node = _as_dict(context.get("target_node"))
    deterministic = build_cycle_community_summary(context)
    counts = _as_dict(deterministic.summary_json.get("counts"))
    summary_json = {
        "summary_type": SUMMARY_TYPE,
        "as_of_date": as_of_date.isoformat(),
        "node": deterministic.summary_json.get("node"),
        "cycle_state": deterministic.summary_json.get("cycle_state"),
        "cycle_score": deterministic.summary_json.get("cycle_score"),
        "cycle_level": deterministic.summary_json.get("cycle_level"),
        "event_heat_score": deterministic.summary_json.get("event_heat_score"),
        "parent_alignment_score": deterministic.summary_json.get("parent_alignment_score"),
        "counts": counts,
        "parent_codes": deterministic.summary_json.get("parent_codes", []),
        "child_codes": deterministic.summary_json.get("child_codes", []),
        "top_symbols": deterministic.summary_json.get("top_symbols", []),
        "recent_event_titles": deterministic.summary_json.get("recent_event_titles", []),
        **response.output.as_summary_json(),
        "summary_text_ko": response.output.korean_summary,
        "source_provider": response.provider,
        "model_name": response.model_name,
        "reasoning_effort": response.reasoning_effort,
        "generation_method": "cycle_community_ai_v2",
        "llm_used": response.provider == CODEX_OAUTH_PROVIDER and invocation_id is not None,
        "invocation_id": invocation_id,
        "prompt_template_version": DEFAULT_TEMPLATE_VERSION,
        "context_hash": hashlib.sha256(json.dumps(_bounded_context_for_prompt(context, max_context_chars=DEFAULT_MAX_CONTEXT_CHARS), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest(),
    }
    return _SummaryRow(
        node_id=int(target_node["node_id"]),
        node_code=str(target_node["code"]).upper(),
        summary_json=summary_json,
    )


def _render_summary_value_tuple(row: _SummaryRow, *, as_of_date: date, source_run_id: int) -> str:
    summary_json = json.dumps(row.summary_json, ensure_ascii=False, sort_keys=True)
    return "(" + ", ".join(
        (
            f"{row.node_id}::bigint",
            sql_date(as_of_date),
            sql_literal(SUMMARY_TYPE),
            f"{sql_literal(summary_json)}::jsonb",
            f"{source_run_id}::bigint",
        )
    ) + ")"


def _bounded_context_for_prompt(context: dict[str, object], *, max_context_chars: int) -> dict[str, object]:
    bounded = {
        "query": context.get("query"),
        "target_node": context.get("target_node"),
        "latest_snapshot": context.get("latest_snapshot"),
        "parent_edges": _limit_list(context.get("parent_edges"), 8),
        "child_edges": _limit_list(context.get("child_edges"), 10),
        "direct_events": _limit_list(context.get("direct_events"), 12),
        "propagated_impacts": _limit_list(context.get("propagated_impacts"), 12),
        "exposed_instruments": _limit_list(context.get("exposed_instruments"), 12),
        "ai_artifacts": _limit_list(context.get("ai_artifacts"), 8),
        "recommendations": _limit_list(context.get("recommendations"), 8),
        "theses": _limit_list(context.get("theses"), 8),
        "previous_summary": context.get("previous_summary"),
    }
    text = json.dumps(bounded, ensure_ascii=False, sort_keys=True)
    if len(text) <= max_context_chars:
        return bounded
    bounded["direct_events"] = _limit_list(context.get("direct_events"), 5)
    bounded["propagated_impacts"] = _limit_list(context.get("propagated_impacts"), 5)
    bounded["exposed_instruments"] = _limit_list(context.get("exposed_instruments"), 8)
    bounded["recommendations"] = _limit_list(context.get("recommendations"), 4)
    bounded["theses"] = _limit_list(context.get("theses"), 4)
    return bounded


def _sanitize_output(output: CycleCommunityAiSummaryOutput, *, context: dict[str, object]) -> CycleCommunityAiSummaryOutput:
    allowed_symbols = set(_context_symbols(context))
    event_ids = set(_context_event_ids(context))
    event_titles = set(_context_event_titles(context))
    supporting_events = []
    for event in output.supporting_events:
        event_id = event.get("event_id")
        title = str(event.get("title") or "").strip()
        if isinstance(event_id, int) and event_id in event_ids or title in event_titles:
            supporting_events.append(event)
    return CycleCommunityAiSummaryOutput(
        korean_summary=output.korean_summary,
        key_drivers=output.key_drivers,
        causal_paths=output.causal_paths,
        supporting_events=tuple(supporting_events[:8]),
        conflicts=output.conflicts,
        uncertainty=output.uncertainty,
        watchlist_symbols=tuple(symbol for symbol in output.watchlist_symbols if symbol in allowed_symbols)[:12],
    )


def _fixture_causal_paths(*, node_code: str, child_codes: tuple[str, ...], symbols: tuple[str, ...]) -> tuple[dict[str, object], ...]:
    paths = []
    for child in child_codes[:3]:
        path = [node_code, child]
        if symbols:
            path.append(symbols[0])
        paths.append({"path": path, "explanation": f"{node_code} 흐름이 {child} 하위 흐름으로 전파된다.", "confidence": 0.72})
    if not paths and symbols:
        paths.append({"path": [node_code, symbols[0]], "explanation": f"{node_code} 흐름이 {symbols[0]} 노출 종목으로 이어진다.", "confidence": 0.68})
    return tuple(paths[:6])


def _fixture_supporting_events(context: dict[str, object]) -> tuple[dict[str, object], ...]:
    events = []
    for row in _limit_list(context.get("direct_events"), 5):
        if not isinstance(row, dict):
            continue
        events.append(
            {
                "event_id": _optional_int(row.get("event_id")),
                "title": str(row.get("korean_title") or row.get("title") or "").strip(),
                "reason": "직접 event classification impact에 연결된 뉴스다.",
            }
        )
    return tuple(events)


def _fixture_conflicts(context: dict[str, object]) -> tuple[str, ...]:
    snapshot = _as_dict(context.get("latest_snapshot"))
    flags = _text_tuple(snapshot.get("conflict_flags"), limit=5)
    if flags:
        return tuple(f"충돌 신호: {flag}" for flag in flags)
    if not _limit_list(context.get("direct_events"), 1):
        return ("직접 뉴스 근거가 적어 전파 영향과 가격/추천 지표를 함께 확인해야 한다.",)
    return ()


def _context_symbols(context: dict[str, object]) -> tuple[str, ...]:
    return _unique_strings(
        [
            str(row.get("primary_symbol") or "")
            for row in (
                *_as_list(context.get("exposed_instruments")),
                *_as_list(context.get("propagated_impacts")),
                *_as_list(context.get("recommendations")),
            )
        ]
    )


def _context_event_ids(context: dict[str, object]) -> tuple[int, ...]:
    ids = []
    for row in (*_as_list(context.get("direct_events")), *_as_list(context.get("propagated_impacts"))):
        event_id = _optional_int(row.get("event_id"))
        if event_id is not None:
            ids.append(event_id)
    return tuple(ids)


def _context_event_titles(context: dict[str, object]) -> tuple[str, ...]:
    return _unique_strings(
        [
            str(row.get("korean_title") or row.get("title") or "")
            for row in (*_as_list(context.get("direct_events")), *_as_list(context.get("propagated_impacts")))
        ]
    )


def _mark_pipeline_run_succeeded_with_fallback(
    executor: PsqlCommandExecutor,
    run_id: int,
    *,
    failed_summary_count: int,
) -> None:
    summary = f"{failed_summary_count} cycle community AI summary node(s) used fixture fallback; review ai.model_invocation errors."
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
            render_cycle_community_ai_model_invocation_insert_sql(
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


def _node_code_from_context(context: dict[str, object]) -> str:
    target_node = _as_dict(context.get("target_node"))
    return str(target_node.get("code") or _as_dict(context.get("query")).get("node_code") or "").upper()


def _normalize_node_codes(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    codes = []
    for value in values:
        code = str(value).strip().upper()
        if not code or code in seen:
            continue
        seen.add(code)
        codes.append(code)
    return tuple(codes)


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _limit_list(value: object, limit: int) -> list[dict[str, object]]:
    return _as_list(value)[:limit]


def _required_text(payload: Mapping[str, object], key: str) -> str:
    value = _optional_text(payload.get(key))
    if not value:
        raise ValueError(f"Cycle community AI output field `{key}` is required.")
    return value


def _optional_text(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _text_tuple(value: object, *, limit: int) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())[:limit]


def _non_empty_tuple(values: Iterable[str], *, limit: int) -> tuple[str, ...]:
    return tuple(value.strip() for value in values if value.strip())[:limit]


def _symbol_tuple(value: object, *, limit: int) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(symbol for symbol in (_normalize_symbol(item) for item in value) if symbol)[:limit]


def _normalize_symbol(value: object) -> str:
    symbol = str(value).strip().upper()
    if not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,9}", symbol):
        return ""
    return symbol


def _causal_path_tuple(value: object, *, limit: int) -> tuple[dict[str, object], ...]:
    if not isinstance(value, list):
        return ()
    result = []
    for item in value:
        if not isinstance(item, dict):
            continue
        path = _text_tuple(item.get("path"), limit=8)
        explanation = _optional_text(item.get("explanation"))
        confidence = _optional_float(item.get("confidence"))
        if path and explanation:
            result.append({"path": list(path), "explanation": explanation, "confidence": confidence if confidence is not None else 0.5})
    return tuple(result[:limit])


def _supporting_event_tuple(value: object, *, limit: int) -> tuple[dict[str, object], ...]:
    if not isinstance(value, list):
        return ()
    result = []
    for item in value:
        if not isinstance(item, dict):
            continue
        title = _optional_text(item.get("title"))
        reason = _optional_text(item.get("reason"))
        if title and reason:
            result.append({"event_id": _optional_int(item.get("event_id")), "title": title, "reason": reason})
    return tuple(result[:limit])


def _unique_strings(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return tuple(result)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, number))


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _token_count(text: str) -> int:
    return max(1, len(text) // 4)


def _loads_json_object(text: str) -> dict[str, object]:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("Cycle community AI provider output must be a JSON object.")
    return payload


def _default_codex_workdir() -> str:
    for candidate in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").exists():
            return str(candidate)
    return str(Path.cwd())


def _bool_env(name: str, *, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _diagnostic_excerpt(text: str, limit: int) -> str:
    normalized = " ".join(str(text).split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(0, limit - 3)] + "..."
