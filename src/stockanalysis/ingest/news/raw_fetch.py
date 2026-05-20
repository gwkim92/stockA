from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.models import FetchResponse, HttpRequest
from stockanalysis.ingest.psql import PsqlCommandExecutor


DEFAULT_NEWS_RSS_RAW_FETCH_LIMIT = 10
DEFAULT_NEWS_RSS_RAW_MAX_BODY_BYTES = 2_000_000
DEFAULT_NEWS_RSS_RAW_USER_AGENT = "StockAnalysisResearchBot/0.1 (free public RSS article fetch)"

FetchFn = Callable[[HttpRequest], FetchResponse]


@dataclass(frozen=True)
class NewsRssRawFetchCandidate:
    document_id: int
    external_document_id: str
    title: str
    url: str
    raw_storage_uri: str | None
    checksum: str | None


def run_news_rss_raw_fetch(
    *,
    config: RuntimeConfig,
    limit: int = DEFAULT_NEWS_RSS_RAW_FETCH_LIMIT,
    external_document_id: str | None = None,
    exclude_url_hosts: tuple[str, ...] = (),
    artifact_root: str = "artifacts/raw",
    body_path: str | None = None,
    force: bool = False,
    max_body_bytes: int = DEFAULT_NEWS_RSS_RAW_MAX_BODY_BYTES,
    user_agent: str = DEFAULT_NEWS_RSS_RAW_USER_AGENT,
    executor: PsqlCommandExecutor | None = None,
    fetcher: FetchFn | None = None,
) -> dict[str, object]:
    _validate_positive("limit", limit)
    _validate_positive("max_body_bytes", max_body_bytes)
    _validate_non_empty("artifact_root", artifact_root)
    _validate_non_empty("user_agent", user_agent)
    excluded_hosts = tuple(_clean_url_host(host) for host in exclude_url_hosts if host.strip())
    if body_path and not external_document_id:
        raise ValueError("--body-file requires --external-document-id so one file maps to one document")

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="news_rss_raw_fetch",
        config_json={
            "limit": limit,
            "external_document_id": external_document_id,
            "exclude_url_hosts": list(excluded_hosts),
            "artifact_root": str(Path(artifact_root)),
            "body_fixture_path": body_path,
            "force": force,
            "max_body_bytes": max_body_bytes,
            "paid_provider_api": False,
            "live_llm_call": False,
        },
    )
    results: list[dict[str, object]] = []
    try:
        candidates = load_news_rss_raw_fetch_candidates(
            limit=limit,
            external_document_id=external_document_id,
            exclude_url_hosts=excluded_hosts,
            force=force,
            executor=sql_executor,
        )
        for candidate in candidates:
            results.append(
                _process_candidate(
                    candidate,
                    artifact_root=artifact_root,
                    body_path=body_path,
                    force=force,
                    max_body_bytes=max_body_bytes,
                    user_agent=user_agent,
                    executor=sql_executor,
                    fetcher=fetcher,
                )
            )
        failed_count = sum(1 for result in results if result["status"] == "failed")
        if failed_count:
            _mark_pipeline_run_failed(sql_executor, run_id, f"{failed_count} RSS article raw fetches failed")
            status = "failed"
        else:
            _mark_pipeline_run_succeeded(sql_executor, run_id)
            status = "completed"
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    succeeded_count = sum(1 for result in results if result["status"] == "succeeded")
    skipped_count = sum(1 for result in results if result["status"] == "skipped")
    return {
        "report_name": "news_rss_raw_fetch",
        "run_id": run_id,
        "status": status,
        "requested_document_count": len(results),
        "succeeded_document_count": succeeded_count,
        "skipped_document_count": skipped_count,
        "failed_document_count": failed_count,
        "artifact_root": str(Path(artifact_root)),
        "exclude_url_hosts": list(excluded_hosts),
        "paid_provider_api": False,
        "live_llm_call": False,
        "results": results,
    }


def load_news_rss_raw_fetch_candidates(
    *,
    limit: int,
    external_document_id: str | None,
    exclude_url_hosts: tuple[str, ...] = (),
    force: bool,
    executor: PsqlCommandExecutor,
) -> tuple[NewsRssRawFetchCandidate, ...]:
    payload = json.loads(
        executor.execute_scalar(
            render_news_rss_raw_fetch_candidate_lookup_sql(
                limit=limit,
                external_document_id=external_document_id,
                exclude_url_hosts=exclude_url_hosts,
                force=force,
            )
        )
    )
    candidates: list[NewsRssRawFetchCandidate] = []
    for row in payload:
        candidates.append(
            NewsRssRawFetchCandidate(
                document_id=int(row["document_id"]),
                external_document_id=str(row["external_document_id"]),
                title=str(row["title"]),
                url=str(row["url"]),
                raw_storage_uri=row.get("raw_storage_uri"),
                checksum=row.get("checksum"),
            )
        )
    return tuple(candidates)


def render_news_rss_raw_fetch_candidate_lookup_sql(
    *,
    limit: int,
    external_document_id: str | None = None,
    exclude_url_hosts: tuple[str, ...] = (),
    force: bool = False,
) -> str:
    _validate_positive("limit", limit)
    filters = [
        "d.document_type = 'news_rss_item'",
        "d.url is not null",
        "btrim(d.url) <> ''",
    ]
    if external_document_id:
        filters.append(f"d.external_document_id = {sql_literal(external_document_id)}")
    for host in exclude_url_hosts:
        cleaned_host = _clean_url_host(host)
        filters.append(f"not (d.url ~* {sql_literal(_url_host_regex(cleaned_host))})")
    if not force:
        filters.append("d.raw_storage_uri is null")
    where_clause = "\n      and ".join(filters)
    return f"""select coalesce(
    json_agg(
        json_build_object(
            'document_id', document_id,
            'external_document_id', external_document_id,
            'title', title,
            'url', url,
            'raw_storage_uri', raw_storage_uri,
            'checksum', checksum
        )
        order by published_at desc nulls last, document_id desc
    ),
    '[]'::json
)::text
from (
    select
        d.document_id,
        d.external_document_id,
        d.title,
        d.url,
        d.raw_storage_uri,
        d.checksum,
        d.published_at
    from ingest.source_document d
    join ingest.data_source ds
      on ds.data_source_id = d.data_source_id
    where {where_clause}
      and (
          ds.source_kind = 'news_rss'
          or ds.source_name like 'rss_news:%'
          or d.external_document_id like 'rss:%'
      )
    order by d.published_at desc nulls last, d.document_id desc
    limit {limit}
) candidates;"""


def render_news_rss_raw_fetch_source_document_update_sql(
    *,
    document_id: int,
    raw_storage_uri: str,
    checksum: str,
) -> str:
    if document_id <= 0:
        raise ValueError("document_id must be greater than 0")
    return f"""update ingest.source_document
set
    raw_storage_uri = {sql_literal(raw_storage_uri)},
    checksum = {sql_literal(checksum)}
where document_id = {document_id};"""


def _process_candidate(
    candidate: NewsRssRawFetchCandidate,
    *,
    artifact_root: str,
    body_path: str | None,
    force: bool,
    max_body_bytes: int,
    user_agent: str,
    executor: PsqlCommandExecutor,
    fetcher: FetchFn | None,
) -> dict[str, object]:
    if candidate.raw_storage_uri and not force:
        return {
            "document_id": candidate.document_id,
            "external_document_id": candidate.external_document_id,
            "title": candidate.title,
            "status": "skipped",
            "raw_storage_uri": candidate.raw_storage_uri,
            "checksum": candidate.checksum,
            "skipped_reason": "raw_storage_uri already set",
        }
    try:
        body, truncated = _load_article_body(
            candidate,
            body_path=body_path,
            max_body_bytes=max_body_bytes,
            user_agent=user_agent,
            fetcher=fetcher,
        )
        checksum = hashlib.sha256(body).hexdigest()
        artifact_path, raw_storage_uri = _write_artifact(
            candidate,
            body,
            artifact_root=artifact_root,
        )
        executor.execute_non_query(
            render_news_rss_raw_fetch_source_document_update_sql(
                document_id=candidate.document_id,
                raw_storage_uri=raw_storage_uri,
                checksum=checksum,
            )
        )
        return {
            "document_id": candidate.document_id,
            "external_document_id": candidate.external_document_id,
            "title": candidate.title,
            "status": "succeeded",
            "artifact_path": str(artifact_path),
            "raw_storage_uri": raw_storage_uri,
            "checksum": checksum,
            "byte_count": len(body),
            "truncated": truncated,
        }
    except Exception as exc:
        return {
            "document_id": candidate.document_id,
            "external_document_id": candidate.external_document_id,
            "title": candidate.title,
            "status": "failed",
            "error": str(exc)[:500],
        }


def _load_article_body(
    candidate: NewsRssRawFetchCandidate,
    *,
    body_path: str | None,
    max_body_bytes: int,
    user_agent: str,
    fetcher: FetchFn | None,
) -> tuple[bytes, bool]:
    if body_path:
        return _limit_body(Path(body_path).read_bytes(), max_body_bytes=max_body_bytes)

    _require_public_http_url(candidate.url)
    request = HttpRequest(
        source_name="rss_news",
        dataset_name="article_body",
        method="GET",
        url=candidate.url,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain;q=0.8,*/*;q=0.5",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": user_agent,
        },
        timeout_seconds=20.0,
    )
    response = fetcher(request) if fetcher else _execute_public_article_request(request, max_body_bytes=max_body_bytes)
    return _require_success_body(response, candidate.external_document_id, max_body_bytes=max_body_bytes)


def _execute_public_article_request(request: HttpRequest, *, max_body_bytes: int) -> FetchResponse:
    _require_public_http_url(request.url)
    raw_request = Request(request.url, headers=request.headers, method=request.method)
    opener = build_opener(_PublicRedirectHandler)
    try:
        with opener.open(raw_request, timeout=request.timeout_seconds) as response:
            _require_public_http_url(response.geturl())
            return FetchResponse(
                status_code=response.status,
                content_type=response.headers.get_content_type(),
                body=response.read(max_body_bytes + 1),
            )
    except HTTPError as exc:
        return FetchResponse(
            status_code=exc.code,
            content_type=exc.headers.get_content_type() if exc.headers else "text/plain",
            body=exc.read(max_body_bytes + 1),
        )


class _PublicRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        _require_public_http_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _require_success_body(response: FetchResponse, external_document_id: str, *, max_body_bytes: int) -> tuple[bytes, bool]:
    if response.status_code >= 400:
        raise ValueError(f"RSS article raw fetch failed for `{external_document_id}` with status {response.status_code}.")
    return _limit_body(response.body, max_body_bytes=max_body_bytes)


def _limit_body(body: bytes, *, max_body_bytes: int) -> tuple[bytes, bool]:
    if len(body) <= max_body_bytes:
        return body, False
    return body[:max_body_bytes], True


def _write_artifact(
    candidate: NewsRssRawFetchCandidate,
    body: bytes,
    *,
    artifact_root: str,
) -> tuple[Path, str]:
    artifact_dir = Path(artifact_root) / "news" / "rss" / _safe_path_part(candidate.external_document_id)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = (artifact_dir / _resolve_filename(candidate)).resolve()
    artifact_path.write_bytes(body)
    return artifact_path, artifact_path.as_uri()


def _resolve_filename(candidate: NewsRssRawFetchCandidate) -> str:
    parsed = urlparse(candidate.url)
    filename = Path(parsed.path).name or "article.html"
    safe = _safe_filename(filename)
    if "." not in safe:
        return f"{safe[:150]}.html"
    if len(safe) <= 160:
        return safe
    stem, suffix = safe.rsplit(".", 1)
    bounded_suffix = suffix[:24] or "html"
    max_stem_length = max(1, 159 - len(bounded_suffix))
    return f"{stem[:max_stem_length]}.{bounded_suffix}"


def _safe_path_part(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip(".-")
    return cleaned[:140] or "rss-document"


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip(".-")
    return cleaned or "article.html"


def _require_public_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("article URL must use http or https")
    hostname = (parsed.hostname or "").strip().lower().rstrip(".")
    if not hostname:
        raise ValueError("article URL must include a hostname")
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".localhost") or hostname.endswith(".local"):
        raise ValueError("article URL must not target localhost or local network names")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return
    if (
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    ):
        raise ValueError("article URL must not target private or local IP addresses")


def _clean_url_host(value: str) -> str:
    cleaned = value.strip().lower()
    if not cleaned:
        raise ValueError("exclude URL host must not be empty")
    parsed = urlparse(cleaned if "://" in cleaned else f"https://{cleaned}")
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host:
        raise ValueError("exclude URL host must include a hostname")
    return host


def _url_host_regex(host: str) -> str:
    escaped = re.escape(host)
    return rf"^https?://{escaped}([:/?#]|$)"


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
    truncated = error_summary.strip()[:2000] or "news RSS raw fetch failed"
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


def _validate_positive(name: str, value: int) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be greater than 0")


def _validate_non_empty(name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} must not be empty")
