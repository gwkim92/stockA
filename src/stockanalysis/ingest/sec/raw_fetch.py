from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.http import execute_request
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.models import FetchResponse, HttpRequest
from stockanalysis.ingest.psql import PsqlCommandExecutor, PsqlExecutionError
from stockanalysis.ingest.sec.models import SecRawFetchResult, SecSourceDocumentRecord
from stockanalysis.ingest.sec.sql import (
    render_sec_source_document_lookup_sql,
    render_sec_source_document_raw_update_sql,
)

FetchFn = Callable[[HttpRequest], FetchResponse]


def run_sec_filing_raw_fetch(
    external_document_id: str,
    *,
    config: RuntimeConfig,
    artifact_root: str = "artifacts/raw",
    body_path: str | None = None,
    force: bool = False,
    executor: PsqlCommandExecutor | None = None,
    fetcher: FetchFn | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    record = load_sec_source_document_record(external_document_id, executor=sql_executor)
    if record.raw_storage_uri and not force:
        return SecRawFetchResult(
            document_id=record.document_id,
            external_document_id=record.external_document_id,
            title=record.title,
            status="skipped",
            artifact_path=None,
            raw_storage_uri=record.raw_storage_uri,
            checksum=record.checksum,
            byte_count=None,
            run_id=None,
            skipped_reason="raw_storage_uri already set",
        ).summary()

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="sec_filing_raw_fetch",
        config_json={
            "document_id": record.document_id,
            "external_document_id": record.external_document_id,
            "artifact_root": str(Path(artifact_root)),
            "body_fixture_path": body_path,
            "force": force,
        },
    )
    try:
        body = _load_document_body(
            record,
            config=config,
            body_path=body_path,
            fetcher=fetcher,
        )
        checksum = hashlib.sha256(body).hexdigest()
        artifact_path, raw_storage_uri = _write_artifact(
            record,
            body,
            artifact_root=artifact_root,
        )
        sql_executor.execute_non_query(
            render_sec_source_document_raw_update_sql(
                document_id=record.document_id,
                raw_storage_uri=raw_storage_uri,
                checksum=checksum,
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return SecRawFetchResult(
        document_id=record.document_id,
        external_document_id=record.external_document_id,
        title=record.title,
        status="succeeded",
        artifact_path=str(artifact_path),
        raw_storage_uri=raw_storage_uri,
        checksum=checksum,
        byte_count=len(body),
        run_id=run_id,
    ).summary()


def load_sec_source_document_record(
    external_document_id: str,
    *,
    executor: PsqlCommandExecutor,
) -> SecSourceDocumentRecord:
    try:
        payload_text = executor.execute_scalar(render_sec_source_document_lookup_sql(external_document_id))
    except PsqlExecutionError as exc:
        raise ValueError(f"SEC source_document not found for `{external_document_id}`.") from exc
    payload = json.loads(payload_text)
    return SecSourceDocumentRecord(
        document_id=int(payload["document_id"]),
        external_document_id=str(payload["external_document_id"]),
        title=str(payload["title"]),
        url=payload.get("url"),
        raw_storage_uri=payload.get("raw_storage_uri"),
        checksum=payload.get("checksum"),
    )


def _load_document_body(
    record: SecSourceDocumentRecord,
    *,
    config: RuntimeConfig,
    body_path: str | None,
    fetcher: FetchFn | None,
) -> bytes:
    if body_path:
        return Path(body_path).read_bytes()
    if not record.url:
        raise ValueError(f"SEC source_document `{record.external_document_id}` has no URL.")
    user_agent = config.resolve("STOCKANALYSIS_SEC_USER_AGENT", required=True)
    request = HttpRequest(
        source_name="sec",
        dataset_name="filing_document",
        method="GET",
        url=record.url,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": user_agent,
        },
    )
    response = (fetcher or execute_request)(request)
    return _require_success_body(response, record.external_document_id)


def _require_success_body(response: FetchResponse, external_document_id: str) -> bytes:
    if response.status_code >= 400:
        raise ValueError(f"SEC raw fetch failed for `{external_document_id}` with status {response.status_code}.")
    return response.body


def _write_artifact(
    record: SecSourceDocumentRecord,
    body: bytes,
    *,
    artifact_root: str,
) -> tuple[Path, str]:
    filename = _resolve_filename(record)
    artifact_dir = Path(artifact_root) / "sec" / "filings" / record.external_document_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = (artifact_dir / filename).resolve()
    artifact_path.write_bytes(body)
    return artifact_path, artifact_path.as_uri()


def _resolve_filename(record: SecSourceDocumentRecord) -> str:
    if record.url:
        candidate = Path(urlparse(record.url).path).name
        if candidate:
            return candidate
    return f"{record.external_document_id}.html"


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
    truncated = error_summary.strip()[:2000] or "sec raw fetch failed"
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
