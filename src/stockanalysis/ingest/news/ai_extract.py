from __future__ import annotations

import hashlib
import json
import os
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
from stockanalysis.ingest.news.enrichment import (
    classify_theme,
    detect_instrument_symbol,
    infer_impact_direction_and_strength,
    resolve_instrument_by_symbol,
)
from stockanalysis.ingest.news.models import (
    NewsRssAiExtractionCandidate,
    NewsRssAiExtractionResult,
    NewsRssEventEnrichmentCandidate,
)
from stockanalysis.ingest.news.sql import (
    render_classification_node_lookup_by_code_sql,
    render_existing_news_ai_candidate_artifact_lookup_sql,
    render_news_ai_extraction_artifact_insert_sql,
    render_news_rss_ai_extraction_candidates_sql,
    render_news_rss_ai_retrieval_context_sql,
)
from stockanalysis.ingest.psql import PsqlCommandExecutor, PsqlExecutionError
from stockanalysis.ingest.sec.sql import (
    render_event_classification_impact_upsert_sql,
    render_event_instrument_impact_upsert_sql,
)

DEFAULT_TASK_NAME = "news-rss-ai-extract"
DEFAULT_PIPELINE_NAME = "event_intelligence_llm_extract"
DEFAULT_TEMPLATE_VERSION = "2026-05-21-ko-v2"
FIXTURE_PROVIDER = "fixture"
CODEX_OAUTH_PROVIDER = "codex_oauth"
DEFAULT_MODEL_NAME = "codex-cli-default"
DEFAULT_REASONING_EFFORT = "low"
DEFAULT_MIN_CONFIDENCE = 0.72
NEWS_AI_CHUNK_INDEX = 9000
ALLOWED_IMPACT_DIRECTIONS = ("risk_review", "supportive", "watch")
UNCLASSIFIED_SYMBOLS = {"", "UNKNOWN", "UNCLASSIFIED"}
LOW_SIGNAL_AI_SOURCE_NAMES = {"rss_news:marketwatch-topstories"}
LOW_SIGNAL_AI_EXTERNAL_DOCUMENT_PREFIXES = ("rss:marketwatch-topstories:",)

NEWS_AI_OUTPUT_SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "analysis_method",
        "event_summary",
        "theme_impacts",
        "instrument_impacts",
        "uncertainty_notes",
        "recommendation_relevance",
    ],
    "properties": {
        "analysis_method": {"type": "string"},
        "event_summary": {"type": "string"},
        "theme_impacts": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "theme_code",
                    "impact_direction",
                    "impact_strength",
                    "confidence",
                    "rationale",
                    "evidence_summary",
                ],
                "properties": {
                    "theme_code": {"type": "string"},
                    "impact_direction": {"type": "string", "enum": list(ALLOWED_IMPACT_DIRECTIONS)},
                    "impact_strength": {"type": "number", "minimum": 0, "maximum": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "rationale": {"type": "string"},
                    "evidence_summary": {"type": "string"},
                },
            },
        },
        "instrument_impacts": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "symbol",
                    "impact_direction",
                    "impact_strength",
                    "confidence",
                    "rationale",
                    "evidence_summary",
                ],
                "properties": {
                    "symbol": {"type": "string"},
                    "impact_direction": {"type": "string", "enum": list(ALLOWED_IMPACT_DIRECTIONS)},
                    "impact_strength": {"type": "number", "minimum": 0, "maximum": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "rationale": {"type": "string"},
                    "evidence_summary": {"type": "string"},
                },
            },
        },
        "uncertainty_notes": {"type": "string"},
        "recommendation_relevance": {"type": "string"},
    },
}


@dataclass(frozen=True)
class NewsAiDocumentChunk:
    document_id: int
    chunk_index: int
    content_hash: str
    text_preview: str
    token_count: int
    chunk_metadata: dict[str, object]
    text: str


@dataclass(frozen=True)
class NewsAiImpactOutput:
    target: str
    impact_direction: str
    impact_strength: float
    confidence: float
    rationale: str
    evidence_summary: str


@dataclass(frozen=True)
class NewsAiOutput:
    analysis_method: str
    event_summary: str
    theme_impacts: tuple[NewsAiImpactOutput, ...]
    instrument_impacts: tuple[NewsAiImpactOutput, ...]
    uncertainty_notes: str
    recommendation_relevance: str

    @property
    def confidence(self) -> float:
        impacts = (*self.theme_impacts, *self.instrument_impacts)
        if not impacts:
            return 0.0
        return min(1.0, sum(impact.confidence for impact in impacts) / len(impacts))

    def as_artifact_json(self) -> dict[str, object]:
        return {
            "analysis_method": self.analysis_method,
            "event_summary": self.event_summary,
            "theme_impacts": [
                {
                    "theme_code": impact.target,
                    "impact_direction": impact.impact_direction,
                    "impact_strength": impact.impact_strength,
                    "confidence": impact.confidence,
                    "rationale": impact.rationale,
                    "evidence_summary": impact.evidence_summary,
                }
                for impact in self.theme_impacts
            ],
            "instrument_impacts": [
                {
                    "symbol": impact.target,
                    "impact_direction": impact.impact_direction,
                    "impact_strength": impact.impact_strength,
                    "confidence": impact.confidence,
                    "rationale": impact.rationale,
                    "evidence_summary": impact.evidence_summary,
                }
                for impact in self.instrument_impacts
            ],
            "uncertainty_notes": self.uncertainty_notes,
            "recommendation_relevance": self.recommendation_relevance,
        }


@dataclass(frozen=True)
class NewsAiProviderResponse:
    provider: str
    model_name: str
    reasoning_effort: str | None
    output: NewsAiOutput
    input_token_count: int | None
    output_token_count: int | None
    cached_input_token_count: int | None
    estimated_cost_usd: Decimal | None
    latency_ms: int | None


@dataclass(frozen=True)
class ClassificationNodeLookup:
    node_id: int
    code: str
    node_type: str
    name: str


@dataclass(frozen=True)
class ValidatedThemeImpact:
    node_code: str
    node_type: str
    impact_direction: str
    impact_strength: float
    confidence: float
    rationale: str


@dataclass(frozen=True)
class ValidatedInstrumentImpact:
    instrument_id: int
    primary_symbol: str
    impact_direction: str
    impact_strength: float
    confidence: float
    rationale: str


@dataclass(frozen=True)
class ValidatedNewsAiOutput:
    theme_impacts: tuple[ValidatedThemeImpact, ...]
    instrument_impacts: tuple[ValidatedInstrumentImpact, ...]
    rejected_impact_count: int


NewsAiProviderRunner = Callable[
    [NewsRssAiExtractionCandidate, NewsAiDocumentChunk, dict[str, object], str, str | None],
    NewsAiProviderResponse,
]


def run_news_rss_ai_extract(
    *,
    config: RuntimeConfig,
    as_of_date: date | None = None,
    limit: int = 10,
    provider: str = CODEX_OAUTH_PROVIDER,
    model_name: str = DEFAULT_MODEL_NAME,
    reasoning_effort: str | None = DEFAULT_REASONING_EFFORT,
    max_input_chars: int = 6000,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    execute: bool = False,
    llm_output_json_path: str | None = None,
    executor: PsqlCommandExecutor | None = None,
    provider_runner: NewsAiProviderRunner | None = None,
) -> dict[str, object]:
    if limit <= 0:
        raise ValueError("limit must be greater than 0")
    if max_input_chars <= 0:
        raise ValueError("max_input_chars must be greater than 0")
    if min_confidence < 0 or min_confidence > 1:
        raise ValueError("min_confidence must be between 0 and 1")
    if provider not in {FIXTURE_PROVIDER, CODEX_OAUTH_PROVIDER}:
        raise ValueError("Supported news AI providers are fixture and codex_oauth.")
    if provider == FIXTURE_PROVIDER and execute and not llm_output_json_path and provider_runner is None:
        raise ValueError("--llm-output-json is required when provider=fixture and --execute is used.")

    target_date = as_of_date or date.today()
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    candidates = load_news_rss_ai_extraction_candidates(
        as_of_date=target_date,
        limit=limit,
        executor=sql_executor,
    )
    if not execute:
        return {
            **_empty_summary(as_of_date=target_date, provider=provider, model_name=model_name),
            "status": "planned",
            "requested_event_count": len(candidates),
            "planned_event_count": len(candidates),
            "results": [_planned_result(candidate).summary() for candidate in candidates],
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
            "min_confidence": min_confidence,
            "requested_event_count": len(candidates),
            "offline_batch_only": True,
        },
    )
    inserted = 0
    skipped = 0
    failed = 0
    validated_theme_count = 0
    validated_instrument_count = 0
    rejected_impact_count = 0
    results: list[dict[str, object]] = []

    try:
        prompt_template_id = int(sql_executor.execute_scalar(render_news_ai_prompt_template_upsert_sql()))
        for candidate in candidates:
            request_hash = ""
            try:
                retrieval_context = load_news_rss_ai_retrieval_context(
                    candidate.event_id,
                    as_of_date=target_date,
                    executor=sql_executor,
                )
                chunk = build_news_ai_document_chunk(
                    candidate,
                    retrieval_context=retrieval_context,
                    max_input_chars=max_input_chars,
                )
                request_hash = build_news_ai_request_hash(
                    candidate=candidate,
                    chunk=chunk,
                    provider=provider,
                    model_name=model_name,
                    prompt_template_id=prompt_template_id,
                )
                existing_artifact_id = lookup_existing_news_ai_candidate_artifact(
                    event_id=candidate.event_id,
                    request_hash=request_hash,
                    executor=sql_executor,
                )
                if existing_artifact_id is not None:
                    skipped += 1
                    results.append(
                        NewsRssAiExtractionResult(
                            event_id=candidate.event_id,
                            document_id=candidate.document_id,
                            status="skipped_existing",
                            artifact_id=existing_artifact_id,
                            run_id=run_id,
                            request_hash=request_hash,
                        ).summary()
                    )
                    continue

                chunk_id = int(sql_executor.execute_scalar(render_news_ai_document_chunk_upsert_sql(chunk)))
                response = _invoke_provider(
                    candidate,
                    chunk,
                    retrieval_context,
                    provider=provider,
                    model_name=model_name,
                    reasoning_effort=reasoning_effort,
                    llm_output_json_path=llm_output_json_path,
                    provider_runner=provider_runner,
                )
                invocation_id = int(
                    sql_executor.execute_scalar(
                        render_news_ai_model_invocation_insert_sql(
                            run_id=run_id,
                            task_name=DEFAULT_TASK_NAME,
                            provider=response.provider,
                            model_name=response.model_name,
                            reasoning_effort=response.reasoning_effort,
                            prompt_template_id=prompt_template_id,
                            input_token_count=response.input_token_count or chunk.token_count,
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
                artifact_id = int(
                    sql_executor.execute_scalar(
                        render_news_ai_extraction_artifact_insert_sql(
                            invocation_id=invocation_id,
                            document_id=candidate.document_id,
                            event_id=candidate.event_id,
                            output_json={
                                "source": response.provider,
                                "candidate": response.output.as_artifact_json(),
                                "extracted_fields": build_news_ai_extracted_fields(response.output),
                                "retrieval_context_summary": summarize_retrieval_context(retrieval_context),
                                "chunk_id": chunk_id,
                                "validator": {
                                    "min_confidence": min_confidence,
                                    "allowed_impact_directions": list(ALLOWED_IMPACT_DIRECTIONS),
                                },
                            },
                            confidence=response.output.confidence,
                        )
                    )
                )
                validated = validate_news_ai_output(
                    response.output,
                    min_confidence=min_confidence,
                    executor=sql_executor,
                )
                for impact in validated.theme_impacts:
                    sql_executor.execute_non_query(
                        render_event_classification_impact_upsert_sql(
                            event_id=candidate.event_id,
                            node_code=impact.node_code,
                            node_type=impact.node_type,
                            impact_direction=impact.impact_direction,
                            impact_strength=impact.impact_strength,
                            confidence=impact.confidence,
                            rationale=impact.rationale,
                        )
                    )
                for impact in validated.instrument_impacts:
                    sql_executor.execute_non_query(
                        render_event_instrument_impact_upsert_sql(
                            event_id=candidate.event_id,
                            instrument_id=impact.instrument_id,
                            impact_direction=impact.impact_direction,
                            impact_strength=impact.impact_strength,
                            confidence=impact.confidence,
                            rationale=impact.rationale,
                        )
                    )

                inserted += 1
                validated_theme_count += len(validated.theme_impacts)
                validated_instrument_count += len(validated.instrument_impacts)
                rejected_impact_count += validated.rejected_impact_count
                results.append(
                    NewsRssAiExtractionResult(
                        event_id=candidate.event_id,
                        document_id=candidate.document_id,
                        status="inserted_validated"
                        if validated.theme_impacts or validated.instrument_impacts
                        else "inserted_no_validated_impacts",
                        artifact_id=artifact_id,
                        invocation_id=invocation_id,
                        run_id=run_id,
                        request_hash=request_hash,
                        validated_theme_count=len(validated.theme_impacts),
                        validated_instrument_count=len(validated.instrument_impacts),
                        rejected_impact_count=validated.rejected_impact_count,
                    ).summary()
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
                    NewsRssAiExtractionResult(
                        event_id=candidate.event_id,
                        document_id=candidate.document_id,
                        status="failed_fallback_rules",
                        run_id=run_id,
                        request_hash=request_hash or None,
                        error=str(exc),
                    ).summary()
                )

        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return {
        "report_name": "news_rss_ai_extract",
        "status": "completed" if failed == 0 else "completed_with_fallback",
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "as_of_date": target_date.isoformat(),
        "run_id": run_id,
        "provider": provider,
        "model_name": model_name,
        "requested_event_count": len(candidates),
        "inserted_artifact_count": inserted,
        "skipped_existing_count": skipped,
        "failed_candidate_count": failed,
        "validated_theme_impact_count": validated_theme_count,
        "validated_instrument_impact_count": validated_instrument_count,
        "rejected_impact_count": rejected_impact_count,
        "results": results,
    }


def load_news_rss_ai_extraction_candidates(
    *,
    as_of_date: date,
    limit: int,
    executor: PsqlCommandExecutor,
) -> tuple[NewsRssAiExtractionCandidate, ...]:
    payload_text = executor.execute_scalar(
        render_news_rss_ai_extraction_candidates_sql(
            as_of_date=as_of_date,
            limit=limit,
            prompt_template_name=DEFAULT_TASK_NAME,
            prompt_template_version=DEFAULT_TEMPLATE_VERSION,
        )
    )
    payload = json.loads(payload_text)
    candidates = tuple(
        NewsRssAiExtractionCandidate(
            event_id=int(item["event_id"]),
            document_id=int(item["document_id"]),
            title=str(item["title"]),
            summary=str(item.get("summary") or ""),
            event_at=str(item["event_at"]),
            source_name=item.get("source_name"),
            external_document_id=item.get("external_document_id"),
            source_url=item.get("source_url"),
            existing_theme_code=item.get("existing_theme_code"),
            existing_instrument_symbol=item.get("existing_instrument_symbol"),
        )
        for item in payload
    )
    return tuple(candidate for candidate in candidates if is_news_ai_candidate_quality_eligible(candidate))


def is_news_ai_candidate_quality_eligible(candidate: NewsRssAiExtractionCandidate) -> bool:
    """Keep expensive AI extraction for items likely to affect tradable evidence."""

    if _is_low_signal_no_symbol_topstory(candidate):
        return False
    return True


def _is_low_signal_no_symbol_topstory(candidate: NewsRssAiExtractionCandidate) -> bool:
    if _has_classified_symbol(candidate.existing_instrument_symbol):
        return False
    source_name = (candidate.source_name or "").strip().lower()
    external_document_id = (candidate.external_document_id or "").strip().lower()
    return source_name in LOW_SIGNAL_AI_SOURCE_NAMES or external_document_id.startswith(
        LOW_SIGNAL_AI_EXTERNAL_DOCUMENT_PREFIXES
    )


def _has_classified_symbol(symbol: str | None) -> bool:
    return bool(symbol and symbol.strip().upper() not in UNCLASSIFIED_SYMBOLS)


def load_news_rss_ai_retrieval_context(
    event_id: int,
    *,
    as_of_date: date,
    executor: PsqlCommandExecutor,
) -> dict[str, object]:
    payload = json.loads(executor.execute_scalar(render_news_rss_ai_retrieval_context_sql(event_id=event_id, as_of_date=as_of_date)))
    return payload if isinstance(payload, dict) else {}


def build_news_ai_document_chunk(
    candidate: NewsRssAiExtractionCandidate,
    *,
    retrieval_context: dict[str, object],
    max_input_chars: int,
) -> NewsAiDocumentChunk:
    source_text = "\n".join(
        (
            f"Title: {candidate.title}",
            f"Summary: {candidate.summary}",
            f"Published/Event At: {candidate.event_at}",
            f"Source: {candidate.source_name or ''}",
            f"URL: {candidate.source_url or ''}",
            "",
            "Retrieval context:",
            json.dumps(summarize_retrieval_context(retrieval_context), ensure_ascii=False, sort_keys=True),
        )
    )
    normalized = " ".join(source_text.split())
    bounded = normalized[:max_input_chars].strip()
    if not bounded:
        raise ValueError(f"news RSS event `{candidate.event_id}` has no analyzable text.")
    return NewsAiDocumentChunk(
        document_id=candidate.document_id,
        chunk_index=NEWS_AI_CHUNK_INDEX,
        content_hash=hashlib.sha256(bounded.encode("utf-8")).hexdigest(),
        text_preview=_truncate(bounded, 500),
        token_count=len(bounded.split()),
        chunk_metadata={
            "source_name": candidate.source_name,
            "external_document_id": candidate.external_document_id,
            "event_id": candidate.event_id,
            "source_text_kind": "news_ai_candidate_context",
            "max_input_chars": max_input_chars,
            "chunker": "news-ai-context-v1",
        },
        text=bounded,
    )


def summarize_retrieval_context(context: dict[str, object]) -> dict[str, object]:
    return {
        "as_of_date": context.get("as_of_date"),
        "known_themes": _bounded_list(context.get("known_themes"), 12),
        "theme_edges": _bounded_list(context.get("theme_edges"), 20),
        "current_event_impacts": _bounded_list(context.get("current_event_impacts"), 8),
        "recent_similar_events": _bounded_list(context.get("recent_similar_events"), 8),
    }


def build_news_ai_extracted_fields(output: NewsAiOutput) -> list[dict[str, object]]:
    fields: list[dict[str, object]] = [
        {
            "field": "analysis_method",
            "value": output.analysis_method,
            "confidence": 1.0,
            "source_chunk_id": "news-ai-candidate",
        },
        {
            "field": "event_summary",
            "value": output.event_summary,
            "confidence": output.confidence,
            "source_chunk_id": "news-ai-candidate",
        },
        {
            "field": "recommendation_relevance",
            "value": output.recommendation_relevance,
            "confidence": output.confidence,
            "source_chunk_id": "news-ai-candidate",
        },
        {
            "field": "uncertainty_notes",
            "value": output.uncertainty_notes,
            "confidence": output.confidence,
            "source_chunk_id": "news-ai-candidate",
        },
    ]
    fields.extend(
        {
            "field": "theme_impact",
            "value": f"{impact.target} / {impact.impact_direction} / {impact.evidence_summary}",
            "confidence": impact.confidence,
            "source_chunk_id": "news-ai-theme-impact",
        }
        for impact in output.theme_impacts
    )
    fields.extend(
        {
            "field": "instrument_impact",
            "value": f"{impact.target} / {impact.impact_direction} / {impact.evidence_summary}",
            "confidence": impact.confidence,
            "source_chunk_id": "news-ai-instrument-impact",
        }
        for impact in output.instrument_impacts
    )
    return fields


def validate_news_ai_output(
    output: NewsAiOutput,
    *,
    min_confidence: float,
    executor: PsqlCommandExecutor,
) -> ValidatedNewsAiOutput:
    validated_themes: list[ValidatedThemeImpact] = []
    validated_instruments: list[ValidatedInstrumentImpact] = []
    rejected = 0

    for impact in output.theme_impacts:
        if not _impact_is_valid(impact, min_confidence=min_confidence):
            rejected += 1
            continue
        node = resolve_classification_node_by_code(impact.target, executor=executor)
        if node is None:
            rejected += 1
            continue
        validated_themes.append(
            ValidatedThemeImpact(
                node_code=node.code,
                node_type=node.node_type,
                impact_direction=impact.impact_direction,
                impact_strength=impact.impact_strength,
                confidence=impact.confidence,
                rationale=_validated_rationale(impact, output.uncertainty_notes),
            )
        )

    for impact in output.instrument_impacts:
        if not _impact_is_valid(impact, min_confidence=min_confidence):
            rejected += 1
            continue
        instrument = resolve_instrument_by_symbol(impact.target, executor=executor)
        if instrument is None:
            rejected += 1
            continue
        validated_instruments.append(
            ValidatedInstrumentImpact(
                instrument_id=instrument.instrument_id,
                primary_symbol=instrument.primary_symbol,
                impact_direction=impact.impact_direction,
                impact_strength=impact.impact_strength,
                confidence=impact.confidence,
                rationale=_validated_rationale(impact, output.uncertainty_notes),
            )
        )

    return ValidatedNewsAiOutput(
        theme_impacts=tuple(validated_themes),
        instrument_impacts=tuple(validated_instruments),
        rejected_impact_count=rejected,
    )


def resolve_classification_node_by_code(
    theme_code: str,
    *,
    executor: PsqlCommandExecutor,
) -> ClassificationNodeLookup | None:
    try:
        payload_text = executor.execute_scalar(render_classification_node_lookup_by_code_sql(theme_code))
    except PsqlExecutionError:
        return None
    payload = json.loads(payload_text)
    return ClassificationNodeLookup(
        node_id=int(payload["node_id"]),
        code=str(payload["code"]),
        node_type=str(payload["node_type"]),
        name=str(payload["name"]),
    )


def parse_news_ai_output(payload: dict[str, object]) -> NewsAiOutput:
    return NewsAiOutput(
        analysis_method=_required_text(payload, "analysis_method"),
        event_summary=_required_text(payload, "event_summary"),
        theme_impacts=tuple(
            _parse_impact(item, target_key="theme_code")
            for item in _required_list(payload, "theme_impacts")
        ),
        instrument_impacts=tuple(
            _parse_impact(item, target_key="symbol")
            for item in _required_list(payload, "instrument_impacts")
        ),
        uncertainty_notes=_required_text(payload, "uncertainty_notes"),
        recommendation_relevance=_required_text(payload, "recommendation_relevance"),
    )


def build_news_ai_provider_response_from_payload(
    payload: dict[str, object],
    *,
    provider: str,
    model_name: str,
    reasoning_effort: str | None,
) -> NewsAiProviderResponse:
    candidate_payload = payload.get("candidate") or payload.get("news_event_candidate")
    if not isinstance(candidate_payload, dict):
        raise ValueError("News AI output must contain an object field named `candidate`.")
    usage_payload = payload.get("usage") or {}
    if not isinstance(usage_payload, dict):
        raise ValueError("News AI output field `usage` must be an object when present.")
    return NewsAiProviderResponse(
        provider=_optional_text(payload.get("provider")) or provider,
        model_name=_optional_text(payload.get("model_name") or payload.get("model")) or model_name,
        reasoning_effort=_optional_text(payload.get("reasoning_effort")) or reasoning_effort,
        output=parse_news_ai_output(candidate_payload),
        input_token_count=_optional_int(usage_payload.get("input_tokens")),
        output_token_count=_optional_int(usage_payload.get("output_tokens")),
        cached_input_token_count=_optional_int(usage_payload.get("cached_input_tokens")),
        estimated_cost_usd=_optional_decimal(usage_payload.get("estimated_cost_usd")),
        latency_ms=_optional_int(usage_payload.get("latency_ms")),
    )


def invoke_codex_oauth_news_ai_provider(
    candidate: NewsRssAiExtractionCandidate,
    chunk: NewsAiDocumentChunk,
    retrieval_context: dict[str, object],
    model_name: str,
    reasoning_effort: str | None,
) -> NewsAiProviderResponse:
    command_text = os.getenv("STOCKANALYSIS_CODEX_CLI_COMMAND", "codex").strip() or "codex"
    try:
        base_command = shlex.split(command_text)
    except ValueError as exc:
        raise ValueError(f"Invalid STOCKANALYSIS_CODEX_CLI_COMMAND: {exc}.") from exc
    if not base_command:
        raise ValueError("STOCKANALYSIS_CODEX_CLI_COMMAND must not be empty.")

    prompt = build_codex_oauth_news_ai_prompt(candidate, chunk, retrieval_context)
    output_schema = build_codex_oauth_news_ai_output_schema()
    timeout_seconds = int(os.getenv("STOCKANALYSIS_CODEX_TIMEOUT_SECONDS", "300"))
    if timeout_seconds <= 0:
        raise ValueError("STOCKANALYSIS_CODEX_TIMEOUT_SECONDS must be greater than 0.")

    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="stockanalysis-news-codex-oauth.") as tmpdir:
        tmp_path = Path(tmpdir)
        schema_path = tmp_path / "news-event-candidate.schema.json"
        output_path = tmp_path / "last-message.json"
        schema_path.write_text(json.dumps(output_schema, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        cwd = os.getenv("STOCKANALYSIS_CODEX_WORKDIR") or str(Path.cwd())
        command = [
            *base_command,
            "-c",
            'approval_policy="never"',
            "--sandbox",
            "read-only",
            "--cd",
            cwd,
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(output_path),
        ]
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
            raise RuntimeError(f"codex_oauth news provider failed: {_truncate(stderr, 2000)}")
        output_text = output_path.read_text(encoding="utf-8") if output_path.exists() else completed.stdout

    response = build_news_ai_provider_response_from_payload(
        _loads_json_object(output_text),
        provider=CODEX_OAUTH_PROVIDER,
        model_name=model_name or DEFAULT_MODEL_NAME,
        reasoning_effort=reasoning_effort,
    )
    return NewsAiProviderResponse(
        provider=CODEX_OAUTH_PROVIDER,
        model_name=response.model_name,
        reasoning_effort=response.reasoning_effort,
        output=response.output,
        input_token_count=response.input_token_count or chunk.token_count,
        output_token_count=response.output_token_count,
        cached_input_token_count=response.cached_input_token_count,
        estimated_cost_usd=response.estimated_cost_usd,
        latency_ms=response.latency_ms or latency_ms,
    )


def build_codex_oauth_news_ai_prompt(
    candidate: NewsRssAiExtractionCandidate,
    chunk: NewsAiDocumentChunk,
    retrieval_context: dict[str, object],
) -> str:
    return "\n".join(
        (
            "You are an investment news evidence extraction engine.",
            "Use only the RSS news item and retrieval context below.",
            "Do not browse, do not call tools, and do not make buy/sell/order recommendations.",
            "Return exactly one JSON object matching the provided output schema.",
            "Write all human-readable natural-language fields in Korean.",
            "This includes event_summary, rationale, evidence_summary, uncertainty_notes, and recommendation_relevance.",
            "Keep machine codes and market identifiers unchanged, including theme_code, impact_direction, and ticker symbols.",
            "Use only theme_code values present in known_themes.",
            "Use only exchange symbols directly supported by the text or current_event_impacts.",
            f"Allowed impact_direction values: {', '.join(ALLOWED_IMPACT_DIRECTIONS)}.",
            "If the item is ambiguous, lower confidence and explain uncertainty.",
            "",
            "News metadata:",
            json.dumps(
                {
                    "event_id": candidate.event_id,
                    "document_id": candidate.document_id,
                    "title": candidate.title,
                    "summary": candidate.summary,
                    "event_at": candidate.event_at,
                    "source_name": candidate.source_name,
                    "source_url": candidate.source_url,
                    "existing_theme_code": candidate.existing_theme_code,
                    "existing_instrument_symbol": candidate.existing_instrument_symbol,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            "",
            "Retrieval context summary:",
            json.dumps(summarize_retrieval_context(retrieval_context), ensure_ascii=False, sort_keys=True),
            "",
            "Bounded analysis context:",
            chunk.text,
        )
    )


def build_codex_oauth_news_ai_output_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["candidate"],
        "properties": {
            "candidate": NEWS_AI_OUTPUT_SCHEMA,
        },
    }


def build_rule_fallback_news_ai_output(candidate: NewsRssAiExtractionCandidate) -> NewsAiOutput:
    enrichment_candidate = NewsRssEventEnrichmentCandidate(
        event_id=candidate.event_id,
        event_type="news_rss_item",
        dedupe_key=None,
        title=candidate.title,
        summary=candidate.summary,
        source_name=candidate.source_name,
        external_document_id=candidate.external_document_id,
    )
    theme = classify_theme(enrichment_candidate)
    direction, strength = infer_impact_direction_and_strength(enrichment_candidate)
    symbol = detect_instrument_symbol(enrichment_candidate)
    instrument_impacts = (
        (
            NewsAiImpactOutput(
                target=symbol,
                impact_direction=direction,
                impact_strength=strength,
                confidence=0.72,
                rationale="Rule fallback symbol match used when AI provider is unavailable.",
                evidence_summary=f"Matched `{symbol}` from RSS title/summary keywords.",
            ),
        )
        if symbol
        else ()
    )
    return NewsAiOutput(
        analysis_method="free_rule_fallback",
        event_summary=candidate.summary or candidate.title,
        theme_impacts=(
            NewsAiImpactOutput(
                target=theme.node_code,
                impact_direction=direction,
                impact_strength=max(theme.impact_strength, strength),
                confidence=theme.confidence,
                rationale=theme.rationale,
                evidence_summary="Mapped by feed and keyword rule baseline.",
            ),
        ),
        instrument_impacts=instrument_impacts,
        uncertainty_notes="Rule fallback was used; treat as lower quality than validated AI extraction.",
        recommendation_relevance="watchlist",
    )


def render_news_ai_prompt_template_upsert_sql() -> str:
    output_schema = json.dumps(NEWS_AI_OUTPUT_SCHEMA, ensure_ascii=False, sort_keys=True)
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
    'Extract RSS news into validated investment evidence, not recommendations.',
    'Use bounded news and Postgres ontology-lite context to return theme/instrument impacts with Korean evidence and uncertainty.',
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


def render_news_ai_document_chunk_upsert_sql(chunk: NewsAiDocumentChunk) -> str:
    chunk_metadata = json.dumps(chunk.chunk_metadata, ensure_ascii=False, sort_keys=True)
    return f"""insert into ai.document_chunk (
    document_id,
    chunk_index,
    content_hash,
    text_preview,
    token_count,
    chunk_metadata
)
values (
    {chunk.document_id},
    {chunk.chunk_index},
    {sql_literal(chunk.content_hash)},
    {sql_literal(chunk.text_preview)},
    {chunk.token_count},
    {sql_literal(chunk_metadata)}::jsonb
)
on conflict (document_id, chunk_index) do update
set
    content_hash = excluded.content_hash,
    text_preview = excluded.text_preview,
    token_count = excluded.token_count,
    chunk_metadata = excluded.chunk_metadata
returning chunk_id;"""


def render_news_ai_model_invocation_insert_sql(
    *,
    run_id: int,
    task_name: str,
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
    {sql_literal(task_name)},
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


def build_news_ai_request_hash(
    *,
    candidate: NewsRssAiExtractionCandidate,
    chunk: NewsAiDocumentChunk,
    provider: str,
    model_name: str,
    prompt_template_id: int,
) -> str:
    payload = {
        "event_id": candidate.event_id,
        "document_id": candidate.document_id,
        "external_document_id": candidate.external_document_id,
        "content_hash": chunk.content_hash,
        "provider": provider,
        "model_name": model_name,
        "prompt_template_id": prompt_template_id,
        "schema": DEFAULT_TEMPLATE_VERSION,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def lookup_existing_news_ai_candidate_artifact(
    *,
    event_id: int,
    request_hash: str,
    executor: PsqlCommandExecutor,
) -> int | None:
    try:
        return int(
            executor.execute_scalar(
                render_existing_news_ai_candidate_artifact_lookup_sql(event_id=event_id, request_hash=request_hash)
            )
        )
    except PsqlExecutionError:
        return None


def _invoke_provider(
    candidate: NewsRssAiExtractionCandidate,
    chunk: NewsAiDocumentChunk,
    retrieval_context: dict[str, object],
    *,
    provider: str,
    model_name: str,
    reasoning_effort: str | None,
    llm_output_json_path: str | None,
    provider_runner: NewsAiProviderRunner | None,
) -> NewsAiProviderResponse:
    if provider_runner is not None:
        return provider_runner(candidate, chunk, retrieval_context, model_name, reasoning_effort)
    if provider == FIXTURE_PROVIDER:
        payload = _loads_json_object(Path(llm_output_json_path or "").read_text(encoding="utf-8"))
        return build_news_ai_provider_response_from_payload(
            payload,
            provider=provider,
            model_name=model_name,
            reasoning_effort=reasoning_effort,
        )
    return invoke_codex_oauth_news_ai_provider(candidate, chunk, retrieval_context, model_name, reasoning_effort)


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
            render_news_ai_model_invocation_insert_sql(
                run_id=run_id,
                task_name=DEFAULT_TASK_NAME,
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
                error_summary=error_summary[:2000],
                request_hash=request_hash,
            )
        )
    except Exception:
        return


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


def _mark_pipeline_run_succeeded(executor: PsqlCommandExecutor, run_id: int) -> None:
    executor.execute_non_query(
        f"""update ops.pipeline_run
set
    status = 'succeeded',
    ended_at = now(),
    error_summary = null
where run_id = {run_id};"""
    )


def _mark_pipeline_run_failed(executor: PsqlCommandExecutor, run_id: int, error_summary: str) -> None:
    truncated = error_summary.strip()[:2000] or "news RSS AI extract failed"
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


def _planned_result(candidate: NewsRssAiExtractionCandidate) -> NewsRssAiExtractionResult:
    return NewsRssAiExtractionResult(
        event_id=candidate.event_id,
        document_id=candidate.document_id,
        status="planned",
    )


def _empty_summary(*, as_of_date: date, provider: str, model_name: str) -> dict[str, object]:
    return {
        "report_name": "news_rss_ai_extract",
        "status": "completed",
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "run_id": None,
        "provider": provider,
        "model_name": model_name,
        "requested_event_count": 0,
        "inserted_artifact_count": 0,
        "skipped_existing_count": 0,
        "failed_candidate_count": 0,
        "validated_theme_impact_count": 0,
        "validated_instrument_impact_count": 0,
        "rejected_impact_count": 0,
        "results": [],
    }


def _parse_impact(payload: object, *, target_key: str) -> NewsAiImpactOutput:
    if not isinstance(payload, dict):
        raise ValueError("Impact item must be an object.")
    direction = _required_text(payload, "impact_direction")
    if direction not in ALLOWED_IMPACT_DIRECTIONS:
        raise ValueError(f"impact_direction must be one of: {', '.join(ALLOWED_IMPACT_DIRECTIONS)}.")
    strength = _required_float(payload, "impact_strength")
    confidence = _required_float(payload, "confidence")
    if strength < 0 or strength > 1:
        raise ValueError("impact_strength must be between 0 and 1.")
    if confidence < 0 or confidence > 1:
        raise ValueError("confidence must be between 0 and 1.")
    return NewsAiImpactOutput(
        target=_required_text(payload, target_key).upper(),
        impact_direction=direction,
        impact_strength=strength,
        confidence=confidence,
        rationale=_required_text(payload, "rationale"),
        evidence_summary=_required_text(payload, "evidence_summary"),
    )


def _impact_is_valid(impact: NewsAiImpactOutput, *, min_confidence: float) -> bool:
    return (
        impact.confidence >= min_confidence
        and impact.impact_direction in ALLOWED_IMPACT_DIRECTIONS
        and bool(impact.rationale.strip())
        and bool(impact.evidence_summary.strip())
    )


def _validated_rationale(impact: NewsAiImpactOutput, uncertainty_notes: str) -> str:
    return _truncate(
        (
            "AI-validated RSS news evidence via offline batch. "
            f"Rationale: {impact.rationale} "
            f"Evidence: {impact.evidence_summary} "
            f"Uncertainty: {uncertainty_notes}"
        ),
        1800,
    )


def _required_list(payload: dict[str, object], key: str) -> list[object]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"News AI output field `{key}` must be a list.")
    return value


def _required_text(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    text = _optional_text(value)
    if text is None:
        raise ValueError(f"News AI output field `{key}` is required.")
    return text


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _required_float(payload: dict[str, object], key: str) -> float:
    value = payload.get(key)
    if value is None:
        raise ValueError(f"News AI output field `{key}` is required.")
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
        raise ValueError("News AI provider output must be a JSON object.")
    return payload


def _bounded_list(value: object, limit: int) -> list[object]:
    if not isinstance(value, list):
        return []
    return value[:limit]


def _truncate(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 3].rstrip()}..."
