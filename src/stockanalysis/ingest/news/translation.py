from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import tempfile
import time
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.news.sql import (
    render_news_rss_translation_candidates_sql,
    render_source_document_translation_update_sql,
)
from stockanalysis.ingest.psql import PsqlCommandExecutor

DEFAULT_TASK_NAME = "news-rss-korean-translation"
DEFAULT_PIPELINE_NAME = "news_rss_korean_translation"
DEFAULT_TEMPLATE_VERSION = "2026-05-23-ko-translation-v1"
FIXTURE_PROVIDER = "fixture"
CODEX_OAUTH_PROVIDER = "codex_oauth"
DEFAULT_MODEL_NAME = "codex-cli-default"
DEFAULT_REASONING_EFFORT = "low"
_LATIN_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9&.+/-]*")

NEWS_TRANSLATION_OUTPUT_SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["korean_title", "korean_summary", "translation_confidence"],
    "properties": {
        "korean_title": {"type": "string"},
        "korean_summary": {"type": "string"},
        "translation_confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
}


@dataclass(frozen=True)
class NewsRssTranslationCandidate:
    event_id: int | None
    document_id: int
    title: str
    summary: str
    published_at: str
    source_name: str | None
    external_document_id: str | None
    source_url: str | None
    existing_theme_code: str | None
    existing_instrument_symbol: str | None
    impact_direction: str | None
    impact_score: float | None


@dataclass(frozen=True)
class NewsTranslationOutput:
    korean_title: str
    korean_summary: str
    translation_confidence: float

    def as_json(self) -> dict[str, object]:
        return {
            "korean_title": self.korean_title,
            "korean_summary": self.korean_summary,
            "translation_confidence": self.translation_confidence,
        }


@dataclass(frozen=True)
class NewsTranslationProviderResponse:
    provider: str
    model_name: str
    reasoning_effort: str | None
    output: NewsTranslationOutput
    input_token_count: int | None
    output_token_count: int | None
    cached_input_token_count: int | None
    estimated_cost_usd: Decimal | None
    latency_ms: int | None


NewsTranslationProviderRunner = Callable[
    [NewsRssTranslationCandidate, str, str, str | None],
    NewsTranslationProviderResponse,
]


def run_news_rss_translation(
    *,
    config: RuntimeConfig,
    as_of_date: date | None = None,
    limit: int = 20,
    provider: str = CODEX_OAUTH_PROVIDER,
    model_name: str = DEFAULT_MODEL_NAME,
    reasoning_effort: str | None = DEFAULT_REASONING_EFFORT,
    max_input_chars: int = 4000,
    execute: bool = False,
    llm_output_json_path: str | None = None,
    executor: PsqlCommandExecutor | None = None,
    provider_runner: NewsTranslationProviderRunner | None = None,
) -> dict[str, object]:
    if limit <= 0:
        raise ValueError("limit must be greater than 0")
    if max_input_chars <= 0:
        raise ValueError("max_input_chars must be greater than 0")
    if provider not in {FIXTURE_PROVIDER, CODEX_OAUTH_PROVIDER}:
        raise ValueError("Supported news translation providers are fixture and codex_oauth.")
    if provider == FIXTURE_PROVIDER and execute and not llm_output_json_path and provider_runner is None:
        raise ValueError("--llm-output-json is required when provider=fixture and --execute is used.")

    target_date = as_of_date or date.today()
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    candidates = load_news_rss_translation_candidates(
        as_of_date=target_date,
        limit=limit,
        executor=sql_executor,
    )
    if not execute:
        return {
            **_empty_summary(as_of_date=target_date, provider=provider, model_name=model_name),
            "status": "planned",
            "requested_document_count": len(candidates),
            "planned_document_count": len(candidates),
            "results": [_planned_result(candidate) for candidate in candidates],
        }
    if not candidates:
        return _empty_summary(as_of_date=target_date, provider=provider, model_name=model_name)

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": target_date.isoformat(),
            "limit": limit,
            "provider": provider,
            "model_name": model_name,
            "reasoning_effort": reasoning_effort,
            "max_input_chars": max_input_chars,
            "requested_document_count": len(candidates),
            "offline_batch_only": True,
        },
    )
    prompt_template_id = int(sql_executor.execute_scalar(render_news_translation_prompt_template_upsert_sql()))
    updated = 0
    failed = 0
    results: list[dict[str, object]] = []

    try:
        for candidate in candidates:
            request_hash = ""
            try:
                bounded_text = build_news_translation_input(candidate, max_input_chars=max_input_chars)
                request_hash = build_news_translation_request_hash(
                    candidate=candidate,
                    bounded_text=bounded_text,
                    provider=provider,
                    model_name=model_name,
                    prompt_template_id=prompt_template_id,
                )
                response = _invoke_provider(
                    candidate,
                    bounded_text,
                    provider=provider,
                    model_name=model_name,
                    reasoning_effort=reasoning_effort,
                    llm_output_json_path=llm_output_json_path,
                    provider_runner=provider_runner,
                )
                validate_news_translation_output_grounding(
                    candidate=candidate,
                    bounded_text=bounded_text,
                    output=response.output,
                )
                invocation_id = int(
                    sql_executor.execute_scalar(
                        render_news_translation_model_invocation_insert_sql(
                            run_id=run_id,
                            provider=response.provider,
                            model_name=response.model_name,
                            reasoning_effort=response.reasoning_effort,
                            prompt_template_id=prompt_template_id,
                            input_token_count=response.input_token_count or _token_count(bounded_text),
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
                sql_executor.execute_scalar(
                    render_source_document_translation_update_sql(
                        document_id=candidate.document_id,
                        korean_title=response.output.korean_title,
                        korean_summary=response.output.korean_summary,
                        translation_confidence=response.output.translation_confidence,
                        translation_provider=response.provider,
                        translation_model_name=response.model_name,
                        translation_invocation_id=invocation_id,
                    )
                )
                updated += 1
                results.append(
                    _result(
                        candidate,
                        status="updated",
                        run_id=run_id,
                        invocation_id=invocation_id,
                        request_hash=request_hash,
                        translation_confidence=response.output.translation_confidence,
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
                    request_hash=request_hash or None,
                )
                results.append(
                    _result(
                        candidate,
                        status="failed",
                        run_id=run_id,
                        request_hash=request_hash or None,
                        error=str(exc),
                    )
                )

        if failed == 0:
            _mark_pipeline_run_succeeded(sql_executor, run_id)
        else:
            _mark_pipeline_run_succeeded_with_fallback(sql_executor, run_id, failed_document_count=failed)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return {
        "report_name": "news_rss_korean_translation",
        "status": "completed" if failed == 0 else "completed_with_fallback",
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "as_of_date": target_date.isoformat(),
        "run_id": run_id,
        "provider": provider,
        "model_name": model_name,
        "requested_document_count": len(candidates),
        "updated_document_count": updated,
        "failed_document_count": failed,
        "results": results,
    }


def load_news_rss_translation_candidates(
    *,
    as_of_date: date,
    limit: int,
    executor: PsqlCommandExecutor,
) -> tuple[NewsRssTranslationCandidate, ...]:
    payload_text = executor.execute_scalar(render_news_rss_translation_candidates_sql(as_of_date=as_of_date, limit=limit))
    payload = json.loads(payload_text)
    return tuple(
        NewsRssTranslationCandidate(
            event_id=int(item["event_id"]) if item.get("event_id") is not None else None,
            document_id=int(item["document_id"]),
            title=str(item["title"]),
            summary=str(item.get("summary") or ""),
            published_at=str(item.get("published_at") or ""),
            source_name=item.get("source_name"),
            external_document_id=item.get("external_document_id"),
            source_url=item.get("source_url"),
            existing_theme_code=item.get("existing_theme_code"),
            existing_instrument_symbol=item.get("existing_instrument_symbol"),
            impact_direction=item.get("impact_direction"),
            impact_score=float(item["impact_score"]) if item.get("impact_score") is not None else None,
        )
        for item in payload
    )


def build_news_translation_input(candidate: NewsRssTranslationCandidate, *, max_input_chars: int) -> str:
    source_text = "\n".join(
        (
            f"Title: {candidate.title}",
            f"Summary: {candidate.summary}",
            f"Published At: {candidate.published_at}",
            f"Source: {candidate.source_name or ''}",
            f"URL: {candidate.source_url or ''}",
            f"Theme Code: {candidate.existing_theme_code or ''}",
            f"Symbol: {candidate.existing_instrument_symbol or ''}",
            f"Impact Direction: {candidate.impact_direction or ''}",
        )
    )
    bounded = " ".join(source_text.split())[:max_input_chars].strip()
    if not bounded:
        raise ValueError(f"news RSS document `{candidate.document_id}` has no translatable text.")
    return bounded


def build_news_translation_request_hash(
    *,
    candidate: NewsRssTranslationCandidate,
    bounded_text: str,
    provider: str,
    model_name: str,
    prompt_template_id: int,
) -> str:
    payload = {
        "document_id": candidate.document_id,
        "external_document_id": candidate.external_document_id,
        "content_hash": hashlib.sha256(bounded_text.encode("utf-8")).hexdigest(),
        "provider": provider,
        "model_name": model_name,
        "prompt_template_id": prompt_template_id,
        "schema": DEFAULT_TEMPLATE_VERSION,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def validate_news_translation_output_grounding(
    *,
    candidate: NewsRssTranslationCandidate,
    bounded_text: str,
    output: NewsTranslationOutput,
) -> None:
    """Reject translations that introduce unsupported English entities."""

    allowed_tokens = _expand_allowed_latin_tokens(
        _latin_tokens(
            " ".join(
                (
                    bounded_text,
                    candidate.title,
                    candidate.summary,
                    candidate.source_name or "",
                    candidate.source_url or "",
                    candidate.external_document_id or "",
                    candidate.existing_theme_code or "",
                    candidate.existing_instrument_symbol or "",
                )
            )
        )
    )
    output_tokens = _latin_tokens(f"{output.korean_title} {output.korean_summary}")
    novel_tokens = sorted(token for token in output_tokens if token not in allowed_tokens)
    if novel_tokens:
        sample = ", ".join(novel_tokens[:8])
        raise ValueError(
            "news translation output contains ungrounded latin token(s) "
            f"for document_id={candidate.document_id}: {sample}"
        )


def _latin_tokens(text: str) -> set[str]:
    tokens = set()
    for match in _LATIN_TOKEN_PATTERN.finditer(text):
        token = _normalize_latin_token(match.group(0))
        if token:
            tokens.add(token)
    return tokens


def _normalize_latin_token(token: str) -> str:
    return token.strip(".,:;!?()[]{}\"'`“”‘’").lower()


def _expand_allowed_latin_tokens(tokens: set[str]) -> set[str]:
    expanded = set(tokens)
    for token in list(tokens):
        parts = [part for part in re.split(r"[._/+\\-]+", token) if part]
        expanded.update(parts)
        if token.endswith("s") and len(token) > 2:
            expanded.add(token[:-1])
        if token == "etfs" or "etfs" in parts:
            expanded.add("etf")
        if token == "openai" or "openai" in parts:
            expanded.add("ai")
        if token in {"cryptocurrency", "cryptocurrencies"} or any(
            part in {"cryptocurrency", "cryptocurrencies"} for part in parts
        ):
            expanded.add("crypto")
    if "personal" in expanded and ("computer" in expanded or "computers" in expanded):
        expanded.update({"pc", "pcs"})
    return expanded


def parse_news_translation_output(payload: dict[str, object]) -> NewsTranslationOutput:
    title = _required_text(payload, "korean_title")
    summary = _required_text(payload, "korean_summary")
    confidence = _required_float(payload, "translation_confidence")
    if confidence < 0 or confidence > 1:
        raise ValueError("translation_confidence must be between 0 and 1.")
    return NewsTranslationOutput(
        korean_title=title,
        korean_summary=summary,
        translation_confidence=confidence,
    )


def build_news_translation_provider_response_from_payload(
    payload: dict[str, object],
    *,
    provider: str,
    model_name: str,
    reasoning_effort: str | None,
) -> NewsTranslationProviderResponse:
    translation_payload = payload.get("translation") or payload
    if not isinstance(translation_payload, dict):
        raise ValueError("News translation output must contain a translation object.")
    usage_payload = payload.get("usage") or {}
    if not isinstance(usage_payload, dict):
        raise ValueError("News translation output field `usage` must be an object when present.")
    return NewsTranslationProviderResponse(
        provider=_optional_text(payload.get("provider")) or provider,
        model_name=_optional_text(payload.get("model_name") or payload.get("model")) or model_name,
        reasoning_effort=_optional_text(payload.get("reasoning_effort")) or reasoning_effort,
        output=parse_news_translation_output(translation_payload),
        input_token_count=_optional_int(usage_payload.get("input_tokens")),
        output_token_count=_optional_int(usage_payload.get("output_tokens")),
        cached_input_token_count=_optional_int(usage_payload.get("cached_input_tokens")),
        estimated_cost_usd=_optional_decimal(usage_payload.get("estimated_cost_usd")),
        latency_ms=_optional_int(usage_payload.get("latency_ms")),
    )


def invoke_codex_oauth_news_translation_provider(
    candidate: NewsRssTranslationCandidate,
    bounded_text: str,
    model_name: str,
    reasoning_effort: str | None,
) -> NewsTranslationProviderResponse:
    command_text = os.getenv("STOCKANALYSIS_CODEX_CLI_COMMAND", "codex").strip() or "codex"
    try:
        base_command = shlex.split(command_text)
    except ValueError as exc:
        raise ValueError(f"Invalid STOCKANALYSIS_CODEX_CLI_COMMAND: {exc}.") from exc
    if not base_command:
        raise ValueError("STOCKANALYSIS_CODEX_CLI_COMMAND must not be empty.")

    prompt = build_codex_oauth_news_translation_prompt(candidate, bounded_text)
    output_schema = build_codex_oauth_news_translation_output_schema()
    timeout_seconds = int(os.getenv("STOCKANALYSIS_CODEX_TIMEOUT_SECONDS", "300"))
    if timeout_seconds <= 0:
        raise ValueError("STOCKANALYSIS_CODEX_TIMEOUT_SECONDS must be greater than 0.")

    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="stockanalysis-news-translation-codex-oauth.") as tmpdir:
        tmp_path = Path(tmpdir)
        schema_path = tmp_path / "news-translation.schema.json"
        output_path = tmp_path / "last-message.json"
        schema_path.write_text(json.dumps(output_schema, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        cwd = os.getenv("STOCKANALYSIS_CODEX_WORKDIR") or _default_codex_workdir()
        command = [
            *base_command,
            "-c",
            'approval_policy="never"',
            "--sandbox",
            "read-only",
            "--cd",
            cwd,
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
                f"codex_oauth news translation provider failed "
                f"(exit_code={completed.returncode}): {_diagnostic_excerpt(stderr, 2000)}"
            )
        output_text = output_path.read_text(encoding="utf-8") if output_path.exists() else completed.stdout

    response = build_news_translation_provider_response_from_payload(
        _loads_json_object(output_text),
        provider=CODEX_OAUTH_PROVIDER,
        model_name=model_name or DEFAULT_MODEL_NAME,
        reasoning_effort=reasoning_effort,
    )
    return NewsTranslationProviderResponse(
        provider=CODEX_OAUTH_PROVIDER,
        model_name=response.model_name,
        reasoning_effort=response.reasoning_effort,
        output=response.output,
        input_token_count=response.input_token_count or _token_count(bounded_text),
        output_token_count=response.output_token_count,
        cached_input_token_count=response.cached_input_token_count,
        estimated_cost_usd=response.estimated_cost_usd,
        latency_ms=response.latency_ms or latency_ms,
    )


def build_codex_oauth_news_translation_prompt(candidate: NewsRssTranslationCandidate, bounded_text: str) -> str:
    return "\n".join(
        (
            "You are a Korean financial-news translation engine for an investment cockpit.",
            "Use only the RSS item below. Do not browse, do not call tools, and do not make buy/sell/order recommendations.",
            "Return exactly one JSON object matching the provided output schema.",
            "Translate the original title into natural Korean sentence-level wording.",
            "Write korean_summary as one or two Korean sentences explaining what happened and why it matters.",
            "Preserve ticker symbols, company names, policy names, and theme codes when they are important.",
            "Do not introduce English company names, tickers, acronyms, or product names that are not present in the RSS item or metadata.",
            "Do not replace the title with a generic label such as 'market news' or 'rate news'.",
            "Set translation_confidence lower when the RSS text is ambiguous, truncated, or lacks enough context.",
            "",
            "News metadata:",
            json.dumps(
                {
                    "event_id": candidate.event_id,
                    "document_id": candidate.document_id,
                    "title": candidate.title,
                    "summary": candidate.summary,
                    "published_at": candidate.published_at,
                    "source_name": candidate.source_name,
                    "source_url": candidate.source_url,
                    "existing_theme_code": candidate.existing_theme_code,
                    "existing_instrument_symbol": candidate.existing_instrument_symbol,
                    "impact_direction": candidate.impact_direction,
                    "impact_score": candidate.impact_score,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            "",
            "Bounded translation context:",
            bounded_text,
        )
    )


def build_codex_oauth_news_translation_output_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["translation"],
        "properties": {
            "translation": NEWS_TRANSLATION_OUTPUT_SCHEMA,
        },
    }


def render_news_translation_prompt_template_upsert_sql() -> str:
    output_schema = json.dumps(NEWS_TRANSLATION_OUTPUT_SCHEMA, ensure_ascii=False, sort_keys=True)
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
    'Translate RSS news titles and summaries into Korean for AI review and user reading.',
    'Use bounded RSS title/summary text to produce korean_title, korean_summary, and translation_confidence. Do not make investment recommendations.',
    {sql_literal(output_schema)}::jsonb,
    true
)
on conflict (template_name, template_version) do update
set
    system_purpose = excluded.system_purpose,
    template_text = excluded.template_text,
    output_schema_json = excluded.output_schema_json,
    is_active = excluded.is_active
returning template_id;"""


def render_news_translation_model_invocation_insert_sql(
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


def _invoke_provider(
    candidate: NewsRssTranslationCandidate,
    bounded_text: str,
    *,
    provider: str,
    model_name: str,
    reasoning_effort: str | None,
    llm_output_json_path: str | None,
    provider_runner: NewsTranslationProviderRunner | None,
) -> NewsTranslationProviderResponse:
    if provider_runner is not None:
        return provider_runner(candidate, bounded_text, model_name, reasoning_effort)
    if provider == FIXTURE_PROVIDER:
        payload = _loads_json_object(Path(llm_output_json_path or "").read_text(encoding="utf-8"))
        return build_news_translation_provider_response_from_payload(
            payload,
            provider=provider,
            model_name=model_name,
            reasoning_effort=reasoning_effort,
        )
    return invoke_codex_oauth_news_translation_provider(candidate, bounded_text, model_name, reasoning_effort)


def _create_pipeline_run(
    executor: PsqlCommandExecutor,
    *,
    pipeline_name: str,
    config_json: dict[str, object],
) -> int:
    payload = json.dumps(config_json, ensure_ascii=False, sort_keys=True)
    sql = f"""insert into ops.pipeline_run (
    run_kind,
    pipeline_name,
    status,
    config_json
)
values (
    'ai',
    {sql_literal(pipeline_name)},
    'running',
    {sql_literal(payload)}::jsonb
)
returning run_id;"""
    return int(executor.execute_scalar(sql))


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
            render_news_translation_model_invocation_insert_sql(
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


def _mark_pipeline_run_succeeded(executor: PsqlCommandExecutor, run_id: int) -> None:
    executor.execute_non_query(
        f"""update ops.pipeline_run
set
    status = 'succeeded',
    ended_at = now(),
    error_summary = null
where run_id = {run_id};"""
    )


def _mark_pipeline_run_succeeded_with_fallback(
    executor: PsqlCommandExecutor,
    run_id: int,
    *,
    failed_document_count: int,
) -> None:
    summary = f"{failed_document_count} news translation document(s) failed; UI falls back to deterministic labels."
    executor.execute_non_query(
        f"""update ops.pipeline_run
set
    status = 'succeeded_with_fallback',
    ended_at = now(),
    error_summary = {sql_literal(summary)}
where run_id = {run_id};"""
    )


def _mark_pipeline_run_failed(executor: PsqlCommandExecutor, run_id: int, error_summary: str) -> None:
    truncated = _diagnostic_excerpt(error_summary, 2000) or "news RSS Korean translation failed"
    try:
        executor.execute_non_query(
            f"""update ops.pipeline_run
set
    status = 'failed',
    ended_at = now(),
    error_summary = {sql_literal(truncated)}
where run_id = {run_id};"""
        )
    except Exception:
        return


def _empty_summary(*, as_of_date: date, provider: str, model_name: str) -> dict[str, object]:
    return {
        "report_name": "news_rss_korean_translation",
        "status": "completed",
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "run_id": None,
        "provider": provider,
        "model_name": model_name,
        "requested_document_count": 0,
        "updated_document_count": 0,
        "failed_document_count": 0,
        "results": [],
    }


def _planned_result(candidate: NewsRssTranslationCandidate) -> dict[str, object]:
    return _result(candidate, status="planned")


def _result(
    candidate: NewsRssTranslationCandidate,
    *,
    status: str,
    run_id: int | None = None,
    invocation_id: int | None = None,
    request_hash: str | None = None,
    translation_confidence: float | None = None,
    error: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "document_id": candidate.document_id,
        "event_id": candidate.event_id,
        "external_document_id": candidate.external_document_id,
        "status": status,
        "run_id": run_id,
        "invocation_id": invocation_id,
        "request_hash": request_hash,
        "translation_confidence": translation_confidence,
    }
    if error:
        payload["error"] = error
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


def _loads_json_object(text: str) -> dict[str, object]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("News translation provider output must be a JSON object.")
    return payload


def _required_text(payload: dict[str, object], key: str) -> str:
    value = _optional_text(payload.get(key))
    if value is None:
        raise ValueError(f"News translation output field `{key}` is required.")
    return value


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _required_float(payload: dict[str, object], key: str) -> float:
    value = payload.get(key)
    if value is None:
        raise ValueError(f"News translation output field `{key}` is required.")
    return float(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal value `{value}`.") from exc


def _token_count(text: str) -> int:
    return max(1, len(text.split()))


def _diagnostic_excerpt(text: str, max_length: int) -> str:
    stripped = text.strip()
    if len(stripped) <= max_length:
        return stripped
    marker = "...<truncated; showing diagnostic tail>\n"
    tail_length = max(0, max_length - len(marker))
    return marker + stripped[-tail_length:].lstrip()
