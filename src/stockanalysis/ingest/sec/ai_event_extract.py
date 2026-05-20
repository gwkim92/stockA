from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.ingest.sec.event_extract import (
    _create_pipeline_run,
    _load_raw_text,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
    load_sec_event_source_document_record,
)
from stockanalysis.ingest.sec.models import SecEventSourceDocumentRecord, SecExtractedEventCandidate
from stockanalysis.ingest.sec.sql import render_sec_event_extract_sql

DEFAULT_TASK_NAME = "event-intelligence-llm-extract"
DEFAULT_PIPELINE_NAME = "event_intelligence_llm_extract"
DEFAULT_TEMPLATE_VERSION = "2026-04-23"
DEFAULT_PROVIDER = "fixture"
CODEX_OAUTH_PROVIDER = "codex_oauth"
DEFAULT_MODEL_NAME = "gpt-5.4-nano"
DEFAULT_CODEX_MODEL_NAME = "codex-cli-default"
DEFAULT_REASONING_EFFORT = "low"

EVENT_OUTPUT_SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "event_type",
        "title",
        "summary",
        "event_at",
        "time_horizon",
        "impact_polarity",
        "significance_score",
        "confidence",
        "evidence_summary",
        "uncertainty_notes",
    ],
    "properties": {
        "event_type": {"type": "string"},
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "event_at": {"type": "string", "format": "date-time"},
        "time_horizon": {"type": "string"},
        "impact_polarity": {"type": "string"},
        "significance_score": {"type": "number", "minimum": 0, "maximum": 1},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "evidence_summary": {"type": "string"},
        "uncertainty_notes": {"type": "string"},
    },
}


@dataclass(frozen=True)
class AiDocumentChunk:
    document_id: int
    chunk_index: int
    content_hash: str
    text_preview: str
    token_count: int
    chunk_metadata: dict[str, object]
    text: str


@dataclass(frozen=True)
class StructuredEventOutput:
    event_type: str
    title: str
    summary: str
    event_at: datetime
    time_horizon: str | None
    impact_polarity: str | None
    significance_score: float | None
    confidence: float
    evidence_summary: str
    uncertainty_notes: str

    def as_artifact_json(self) -> dict[str, object]:
        return {
            "event_type": self.event_type,
            "title": self.title,
            "summary": self.summary,
            "event_at": self.event_at.isoformat(),
            "time_horizon": self.time_horizon,
            "impact_polarity": self.impact_polarity,
            "significance_score": self.significance_score,
            "confidence": self.confidence,
            "evidence_summary": self.evidence_summary,
            "uncertainty_notes": self.uncertainty_notes,
        }


@dataclass(frozen=True)
class StructuredEventProviderResponse:
    provider: str
    model_name: str
    reasoning_effort: str | None
    event: StructuredEventOutput
    input_token_count: int | None
    output_token_count: int | None
    cached_input_token_count: int | None
    estimated_cost_usd: Decimal | None
    latency_ms: int | None


StructuredEventProviderRunner = Callable[
    [SecEventSourceDocumentRecord, AiDocumentChunk, str, str | None],
    StructuredEventProviderResponse,
]


def run_event_intelligence_llm_extract(
    external_document_id: str,
    *,
    config: RuntimeConfig,
    llm_output_json_path: str | None = None,
    provider: str = DEFAULT_PROVIDER,
    model_name: str = DEFAULT_MODEL_NAME,
    reasoning_effort: str | None = DEFAULT_REASONING_EFFORT,
    max_input_chars: int = 8000,
    min_confidence: float = 0.8,
    executor: PsqlCommandExecutor | None = None,
    provider_runner: StructuredEventProviderRunner | None = None,
) -> dict[str, object]:
    if max_input_chars <= 0:
        raise ValueError("max_input_chars must be greater than 0")
    if min_confidence < 0 or min_confidence > 1:
        raise ValueError("min_confidence must be between 0 and 1")
    if provider not in {DEFAULT_PROVIDER, CODEX_OAUTH_PROVIDER}:
        raise ValueError("Supported event intelligence providers are fixture and codex_oauth.")
    if provider == DEFAULT_PROVIDER and not llm_output_json_path:
        raise ValueError("--llm-output-json is required when provider=fixture.")
    if provider == CODEX_OAUTH_PROVIDER and model_name == DEFAULT_MODEL_NAME:
        model_name = DEFAULT_CODEX_MODEL_NAME

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    source_document = load_sec_event_source_document_record(
        external_document_id,
        executor=sql_executor,
    )
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "document_id": source_document.document_id,
            "external_document_id": source_document.external_document_id,
            "provider": provider,
            "model_name": model_name,
            "reasoning_effort": reasoning_effort,
            "max_input_chars": max_input_chars,
            "min_confidence": min_confidence,
        },
    )

    prompt_template_id: int | None = None
    model_invocation_id: int | None = None
    chunk_id: int | None = None
    artifact_id: int | None = None
    try:
        prompt_template_id = int(sql_executor.execute_scalar(render_ai_prompt_template_upsert_sql()))
        chunk = build_ai_document_chunk(source_document, max_input_chars=max_input_chars)
        chunk_id = int(sql_executor.execute_scalar(render_ai_document_chunk_upsert_sql(chunk)))
        if provider == DEFAULT_PROVIDER:
            response = load_structured_event_provider_response(
                llm_output_json_path or "",
                provider=provider,
                model_name=model_name,
                reasoning_effort=reasoning_effort,
            )
        else:
            runner = provider_runner or invoke_codex_oauth_structured_event_provider
            response = runner(source_document, chunk, model_name, reasoning_effort)
        candidate = build_sec_event_candidate_from_structured_output(
            source_document,
            response.event,
            min_confidence=min_confidence,
        )
        model_invocation_id = int(
            sql_executor.execute_scalar(
                render_ai_model_invocation_insert_sql(
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
                    request_hash=build_request_hash(
                        source_document=source_document,
                        chunk=chunk,
                        provider=response.provider,
                        model_name=response.model_name,
                        prompt_template_id=prompt_template_id,
                    ),
                )
            )
        )
        artifact_id = int(
            sql_executor.execute_scalar(
                render_ai_extraction_artifact_insert_sql(
                    invocation_id=model_invocation_id,
                    document_id=source_document.document_id,
                    output_json={
                        "source": response.provider,
                        "event": response.event.as_artifact_json(),
                    },
                    confidence=response.event.confidence,
                )
            )
        )
        sql_executor.execute_non_query(render_sec_event_extract_sql(candidate, created_by_run_id=run_id))
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        if prompt_template_id is not None and model_invocation_id is None:
            _record_failed_invocation(
                sql_executor,
                run_id=run_id,
                prompt_template_id=prompt_template_id,
                provider=provider,
                model_name=model_name,
                reasoning_effort=reasoning_effort,
                error_summary=str(exc),
            )
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return {
        "run_id": run_id,
        "document_id": source_document.document_id,
        "external_document_id": source_document.external_document_id,
        "event_type": candidate.event_type,
        "title": candidate.title,
        "dedupe_key": candidate.dedupe_key,
        "status": "succeeded",
        "provider": provider,
        "model_name": response.model_name,
        "reasoning_effort": response.reasoning_effort,
        "prompt_template_id": prompt_template_id,
        "chunk_id": chunk_id,
        "model_invocation_id": model_invocation_id,
        "artifact_id": artifact_id,
        "confidence": response.event.confidence,
    }


def build_ai_document_chunk(
    source_document: SecEventSourceDocumentRecord,
    *,
    max_input_chars: int,
) -> AiDocumentChunk:
    if not source_document.raw_storage_uri:
        raise ValueError(
            f"SEC source_document `{source_document.external_document_id}` does not have raw_storage_uri."
        )
    raw_text = _load_raw_text(source_document.raw_storage_uri)
    normalized = " ".join(raw_text.split())
    bounded = normalized[:max_input_chars].strip()
    if not bounded:
        raise ValueError(f"SEC source_document `{source_document.external_document_id}` raw artifact is empty.")
    content_hash = hashlib.sha256(bounded.encode("utf-8")).hexdigest()
    return AiDocumentChunk(
        document_id=source_document.document_id,
        chunk_index=0,
        content_hash=content_hash,
        text_preview=_truncate(bounded, 500),
        token_count=len(bounded.split()),
        chunk_metadata={
            "source_name": "sec_edgar",
            "external_document_id": source_document.external_document_id,
            "checksum": source_document.checksum,
            "max_input_chars": max_input_chars,
            "chunker": "bounded-leading-text-v1",
        },
        text=bounded,
    )


def load_structured_event_provider_response(
    llm_output_json_path: str,
    *,
    provider: str,
    model_name: str,
    reasoning_effort: str | None,
) -> StructuredEventProviderResponse:
    payload = json.loads(Path(llm_output_json_path).read_text(encoding="utf-8"))
    return build_structured_event_provider_response_from_payload(
        payload,
        provider=provider,
        model_name=model_name,
        reasoning_effort=reasoning_effort,
    )


def build_structured_event_provider_response_from_payload(
    payload: dict[str, object],
    *,
    provider: str,
    model_name: str,
    reasoning_effort: str | None,
) -> StructuredEventProviderResponse:
    event_payload = payload.get("event")
    if not isinstance(event_payload, dict):
        raise ValueError("LLM output must contain an object field named `event`.")
    usage_payload = payload.get("usage") or {}
    if not isinstance(usage_payload, dict):
        raise ValueError("LLM output field `usage` must be an object when present.")
    return StructuredEventProviderResponse(
        provider=_optional_text(payload.get("provider")) or provider,
        model_name=_optional_text(payload.get("model_name") or payload.get("model")) or model_name,
        reasoning_effort=_optional_text(payload.get("reasoning_effort")) or reasoning_effort,
        event=parse_structured_event_output(event_payload),
        input_token_count=_optional_int(usage_payload.get("input_tokens")),
        output_token_count=_optional_int(usage_payload.get("output_tokens")),
        cached_input_token_count=_optional_int(usage_payload.get("cached_input_tokens")),
        estimated_cost_usd=_optional_decimal(usage_payload.get("estimated_cost_usd")),
        latency_ms=_optional_int(usage_payload.get("latency_ms")),
    )


def invoke_codex_oauth_structured_event_provider(
    source_document: SecEventSourceDocumentRecord,
    chunk: AiDocumentChunk,
    model_name: str,
    reasoning_effort: str | None,
) -> StructuredEventProviderResponse:
    command_text = os.getenv("STOCKANALYSIS_CODEX_CLI_COMMAND", "codex").strip() or "codex"
    try:
        base_command = shlex.split(command_text)
    except ValueError as exc:
        raise ValueError(f"Invalid STOCKANALYSIS_CODEX_CLI_COMMAND: {exc}.") from exc
    if not base_command:
        raise ValueError("STOCKANALYSIS_CODEX_CLI_COMMAND must not be empty.")

    prompt = build_codex_oauth_event_prompt(source_document, chunk)
    output_schema = build_codex_oauth_output_schema()
    timeout_seconds = int(os.getenv("STOCKANALYSIS_CODEX_TIMEOUT_SECONDS", "300"))
    if timeout_seconds <= 0:
        raise ValueError("STOCKANALYSIS_CODEX_TIMEOUT_SECONDS must be greater than 0.")

    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="stockanalysis-codex-oauth.") as tmpdir:
        tmp_path = Path(tmpdir)
        schema_path = tmp_path / "event-output.schema.json"
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
        if model_name and model_name not in {DEFAULT_CODEX_MODEL_NAME, "default"}:
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
            raise RuntimeError(f"codex_oauth provider failed: {_truncate(stderr, 2000)}")
        output_text = output_path.read_text(encoding="utf-8") if output_path.exists() else completed.stdout

    payload = _loads_json_object(output_text)
    response = build_structured_event_provider_response_from_payload(
        payload,
        provider=CODEX_OAUTH_PROVIDER,
        model_name=model_name or DEFAULT_CODEX_MODEL_NAME,
        reasoning_effort=reasoning_effort,
    )
    return StructuredEventProviderResponse(
        provider=CODEX_OAUTH_PROVIDER,
        model_name=response.model_name,
        reasoning_effort=response.reasoning_effort,
        event=response.event,
        input_token_count=response.input_token_count or chunk.token_count,
        output_token_count=response.output_token_count,
        cached_input_token_count=response.cached_input_token_count,
        estimated_cost_usd=response.estimated_cost_usd,
        latency_ms=response.latency_ms or latency_ms,
    )


def build_codex_oauth_event_prompt(source_document: SecEventSourceDocumentRecord, chunk: AiDocumentChunk) -> str:
    return "\n".join(
        (
            "You are an investment evidence extraction engine.",
            "Use only the SEC filing context provided below.",
            "Do not browse, do not call tools, do not make buy/sell recommendations.",
            "Return exactly one JSON object matching the provided output schema.",
            "The event must be an investment-relevant filing event with explicit uncertainty notes.",
            "",
            "Document metadata:",
            json.dumps(
                {
                    "external_document_id": source_document.external_document_id,
                    "title": source_document.title,
                    "summary": source_document.summary,
                    "published_at": source_document.published_at.isoformat()
                    if source_document.published_at
                    else None,
                    "checksum": source_document.checksum,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            "",
            "Bounded SEC filing context:",
            chunk.text,
        )
    )


def build_codex_oauth_output_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["event"],
        "properties": {
            "event": EVENT_OUTPUT_SCHEMA,
        },
    }


def parse_structured_event_output(payload: dict[str, object]) -> StructuredEventOutput:
    event_type = _required_text(payload, "event_type")
    title = _required_text(payload, "title")
    summary = _required_text(payload, "summary")
    event_at = datetime.fromisoformat(_required_text(payload, "event_at"))
    confidence = _required_float(payload, "confidence")
    if confidence < 0 or confidence > 1:
        raise ValueError("confidence must be between 0 and 1")
    significance_score = _optional_float(payload.get("significance_score"))
    if significance_score is not None and (significance_score < 0 or significance_score > 1):
        raise ValueError("significance_score must be between 0 and 1")
    return StructuredEventOutput(
        event_type=event_type,
        title=title,
        summary=summary,
        event_at=event_at,
        time_horizon=_optional_text(payload.get("time_horizon")),
        impact_polarity=_optional_text(payload.get("impact_polarity")),
        significance_score=significance_score,
        confidence=confidence,
        evidence_summary=_required_text(payload, "evidence_summary"),
        uncertainty_notes=_required_text(payload, "uncertainty_notes"),
    )


def build_sec_event_candidate_from_structured_output(
    source_document: SecEventSourceDocumentRecord,
    event_output: StructuredEventOutput,
    *,
    min_confidence: float,
) -> SecExtractedEventCandidate:
    if event_output.confidence < min_confidence:
        raise ValueError(
            f"LLM event confidence {event_output.confidence:.4f} is below min_confidence {min_confidence:.4f}."
        )
    return SecExtractedEventCandidate(
        document_id=source_document.document_id,
        external_document_id=source_document.external_document_id,
        event_type=event_output.event_type,
        title=event_output.title,
        summary=event_output.summary,
        event_at=event_output.event_at,
        time_horizon=event_output.time_horizon,
        impact_polarity=event_output.impact_polarity,
        significance_score=event_output.significance_score,
        confidence=event_output.confidence,
        dedupe_key=f"sec_edgar:{source_document.external_document_id}:{event_output.event_type}",
    )


def render_ai_prompt_template_upsert_sql() -> str:
    output_schema = json.dumps(EVENT_OUTPUT_SCHEMA, ensure_ascii=False, sort_keys=True)
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
    'Extract SEC filing events as structured investment evidence, not recommendations.',
    'Read the bounded SEC filing context and return one structured event with evidence and uncertainty notes.',
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


def render_ai_document_chunk_upsert_sql(chunk: AiDocumentChunk) -> str:
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


def render_ai_model_invocation_insert_sql(
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


def render_ai_extraction_artifact_insert_sql(
    *,
    invocation_id: int,
    document_id: int,
    output_json: dict[str, object],
    confidence: float | None,
) -> str:
    output_text = json.dumps(output_json, ensure_ascii=False, sort_keys=True)
    return f"""insert into ai.extraction_artifact (
    invocation_id,
    document_id,
    artifact_type,
    output_json,
    confidence
)
values (
    {invocation_id},
    {document_id},
    'structured_event_candidate',
    {sql_literal(output_text)}::jsonb,
    {sql_literal(confidence)}
)
returning artifact_id;"""


def build_request_hash(
    *,
    source_document: SecEventSourceDocumentRecord,
    chunk: AiDocumentChunk,
    provider: str,
    model_name: str,
    prompt_template_id: int,
) -> str:
    payload = {
        "document_id": source_document.document_id,
        "external_document_id": source_document.external_document_id,
        "content_hash": chunk.content_hash,
        "provider": provider,
        "model_name": model_name,
        "prompt_template_id": prompt_template_id,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _record_failed_invocation(
    executor: PsqlCommandExecutor,
    *,
    run_id: int,
    prompt_template_id: int,
    provider: str,
    model_name: str,
    reasoning_effort: str | None,
    error_summary: str,
) -> None:
    try:
        executor.execute_scalar(
            render_ai_model_invocation_insert_sql(
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
                request_hash=None,
            )
        )
    except Exception:
        return


def _required_text(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    text = _optional_text(value)
    if text is None:
        raise ValueError(f"LLM output event field `{key}` is required.")
    return text


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _required_float(payload: dict[str, object], key: str) -> float:
    value = payload.get(key)
    result = _optional_float(value)
    if result is None:
        raise ValueError(f"LLM output event field `{key}` is required.")
    return result


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
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


def _truncate(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 3].rstrip()}..."


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
        raise ValueError("Codex OAuth provider output must be a JSON object.")
    return payload
