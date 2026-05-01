from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor, PsqlExecutionError
from stockanalysis.ingest.sec.models import (
    SecEventExtractionResult,
    SecEventSourceDocumentRecord,
    SecExtractedEventCandidate,
)
from stockanalysis.ingest.sec.sql import (
    render_sec_event_extract_sql,
    render_sec_pending_event_document_ids_sql,
    render_sec_event_source_document_lookup_sql,
)

_COMPANY_NAME_RE = re.compile(r"SEC .* filing for (?P<company>.+?)(?: \||$)")

_FORM_EVENT_CONFIG: dict[str, dict[str, object]] = {
    "10-K": {
        "event_type": "sec_annual_report_filed",
        "title_prefix": "Annual report filed",
        "time_horizon": "long_term",
        "impact_polarity": "neutral",
        "significance_score": 0.75,
        "confidence": 0.95,
    },
    "10-Q": {
        "event_type": "sec_quarterly_report_filed",
        "title_prefix": "Quarterly report filed",
        "time_horizon": "medium_term",
        "impact_polarity": "neutral",
        "significance_score": 0.65,
        "confidence": 0.94,
    },
    "8-K": {
        "event_type": "sec_current_report_filed",
        "title_prefix": "Current report filed",
        "time_horizon": "short_term",
        "impact_polarity": "neutral",
        "significance_score": 0.8,
        "confidence": 0.93,
    },
    "DEF 14A": {
        "event_type": "sec_proxy_statement_filed",
        "title_prefix": "Proxy statement filed",
        "time_horizon": "medium_term",
        "impact_polarity": "neutral",
        "significance_score": 0.55,
        "confidence": 0.92,
    },
}


def run_sec_filings_event_extract(
    external_document_id: str,
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    source_document = load_sec_event_source_document_record(
        external_document_id,
        executor=sql_executor,
    )
    candidate = extract_sec_event_candidate(source_document)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="sec_filings_event_extract",
        config_json={
            "document_id": source_document.document_id,
            "external_document_id": source_document.external_document_id,
            "dedupe_key": candidate.dedupe_key,
            "event_type": candidate.event_type,
        },
    )
    try:
        sql_executor.execute_non_query(
            render_sec_event_extract_sql(
                candidate,
                created_by_run_id=run_id,
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return SecEventExtractionResult(
        document_id=source_document.document_id,
        external_document_id=source_document.external_document_id,
        event_type=candidate.event_type,
        title=candidate.title,
        dedupe_key=candidate.dedupe_key,
        status="succeeded",
        run_id=run_id,
    ).summary()


def run_sec_filings_event_batch_extract(
    *,
    config: RuntimeConfig,
    external_document_ids: list[str] | None = None,
    limit: int = 20,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    requested_ids = tuple(external_document_ids or load_pending_sec_event_document_ids(limit=limit, executor=sql_executor))
    results: list[dict[str, object]] = []
    succeeded = 0
    failed = 0

    for external_document_id in requested_ids:
        try:
            summary = run_sec_filings_event_extract(
                external_document_id,
                config=config,
                executor=sql_executor,
            )
        except Exception as exc:
            failed += 1
            results.append(
                {
                    "external_document_id": external_document_id,
                    "status": "failed",
                    "error": str(exc),
                }
            )
            continue

        succeeded += 1
        results.append(summary)

    return {
        "requested_document_count": len(requested_ids),
        "succeeded_document_count": succeeded,
        "failed_document_count": failed,
        "results": results,
    }


def load_sec_event_source_document_record(
    external_document_id: str,
    *,
    executor: PsqlCommandExecutor,
) -> SecEventSourceDocumentRecord:
    try:
        payload_text = executor.execute_scalar(render_sec_event_source_document_lookup_sql(external_document_id))
    except PsqlExecutionError as exc:
        raise ValueError(f"SEC source_document not found for `{external_document_id}`.") from exc
    payload = json.loads(payload_text)
    published_at = payload.get("published_at")
    return SecEventSourceDocumentRecord(
        document_id=int(payload["document_id"]),
        external_document_id=str(payload["external_document_id"]),
        title=str(payload["title"]),
        summary=payload.get("summary"),
        published_at=datetime.fromisoformat(published_at) if published_at else None,
        raw_storage_uri=payload.get("raw_storage_uri"),
        checksum=payload.get("checksum"),
    )


def load_pending_sec_event_document_ids(
    *,
    limit: int,
    executor: PsqlCommandExecutor,
) -> tuple[str, ...]:
    payload_text = executor.execute_scalar(render_sec_pending_event_document_ids_sql(limit=limit))
    payload = json.loads(payload_text)
    return tuple(str(item) for item in payload)


def extract_sec_event_candidate(source_document: SecEventSourceDocumentRecord) -> SecExtractedEventCandidate:
    if not source_document.raw_storage_uri:
        raise ValueError(
            f"SEC source_document `{source_document.external_document_id}` does not have raw_storage_uri."
        )

    form_type = _extract_form_type(source_document.title)
    config = _FORM_EVENT_CONFIG.get(form_type, _default_form_event_config(form_type))
    company_name = _extract_company_name(source_document.summary) or "Unknown issuer"
    raw_text = _load_raw_text(source_document.raw_storage_uri)
    excerpt = _build_excerpt(raw_text)
    event_title = f"{config['title_prefix']}: {company_name}"
    base_summary = f"{company_name} filed SEC Form {form_type}."
    if excerpt:
        summary = f"{base_summary} Excerpt: {excerpt}"
    else:
        summary = base_summary
    event_at = source_document.published_at or datetime.now(timezone.utc)
    event_type = str(config["event_type"])
    return SecExtractedEventCandidate(
        document_id=source_document.document_id,
        external_document_id=source_document.external_document_id,
        event_type=event_type,
        title=event_title,
        summary=summary,
        event_at=event_at,
        time_horizon=_coerce_optional_str(config.get("time_horizon")),
        impact_polarity=_coerce_optional_str(config.get("impact_polarity")),
        significance_score=_coerce_optional_float(config.get("significance_score")),
        confidence=_coerce_optional_float(config.get("confidence")),
        dedupe_key=f"sec_edgar:{source_document.external_document_id}:{event_type}",
    )


def _extract_form_type(title: str) -> str:
    prefix = title.split(" - ", 1)[0].strip().upper()
    return prefix or "UNKNOWN"


def _extract_company_name(summary: str | None) -> str | None:
    if not summary:
        return None
    match = _COMPANY_NAME_RE.search(summary)
    if not match:
        return None
    company_name = match.group("company").strip()
    return company_name or None


def _load_raw_text(raw_storage_uri: str) -> str:
    parsed = urlparse(raw_storage_uri)
    if parsed.scheme != "file":
        raise ValueError(f"Unsupported raw_storage_uri scheme `{parsed.scheme}` for SEC event extraction.")
    artifact_path = Path(unquote(parsed.path))
    body = artifact_path.read_text(encoding="utf-8", errors="replace")
    return _extract_text(body)


def _build_excerpt(raw_text: str, *, max_length: int = 220) -> str:
    normalized = " ".join(raw_text.split())
    if len(normalized) <= max_length:
        return normalized
    trimmed = normalized[: max_length - 3].rstrip()
    return f"{trimmed}..."


def _extract_text(body: str) -> str:
    parser = _SecHtmlTextParser()
    parser.feed(body)
    return " ".join(parser.parts)


def _default_form_event_config(form_type: str) -> dict[str, object]:
    return {
        "event_type": "sec_filing_recorded",
        "title_prefix": f"SEC filing recorded ({form_type})",
        "time_horizon": "medium_term",
        "impact_polarity": "neutral",
        "significance_score": 0.5,
        "confidence": 0.9,
    }


def _coerce_optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _coerce_optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


class _SecHtmlTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if text:
            self.parts.append(text)


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
    'ingest',
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
    truncated = error_summary.strip()[:2000] or "sec filings event extract failed"
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
