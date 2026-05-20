from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor


DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_DOCUMENT_LIMIT = 20
DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_PROVIDER = "local_deterministic"
DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_MODEL_NAME = "rss_raw_html_text_hash_v1"
DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_EMBEDDING_DIMENSION = 1
DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_MAX_TEXT_CHARS = 1600
DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_MAX_CHUNKS_PER_DOCUMENT = 3


@dataclass(frozen=True)
class NewsRssRawBodyChunkCandidate:
    document_id: int
    external_document_id: str
    title: str
    raw_storage_uri: str
    checksum: str | None
    summary: str | None = None
    url: str | None = None


@dataclass(frozen=True)
class NewsRssRawBodyChunk:
    chunk_index: int
    text: str
    content_hash: str
    token_count: int
    metadata: dict[str, object]

    @property
    def text_preview(self) -> str:
        return self.text[:500]


def run_news_rss_raw_body_chunk_index(
    *,
    config: RuntimeConfig,
    document_limit: int = DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_DOCUMENT_LIMIT,
    external_document_id: str | None = None,
    exclude_url_hosts: tuple[str, ...] = (),
    artifact_root: str = "artifacts/raw",
    provider: str = DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_PROVIDER,
    model_name: str = DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_MODEL_NAME,
    embedding_dimension: int = DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_EMBEDDING_DIMENSION,
    max_text_chars: int = DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_MAX_TEXT_CHARS,
    max_chunks_per_document: int = DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_MAX_CHUNKS_PER_DOCUMENT,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    _validate_positive("document_limit", document_limit)
    _validate_positive("embedding_dimension", embedding_dimension)
    _validate_positive("max_text_chars", max_text_chars)
    _validate_positive("max_chunks_per_document", max_chunks_per_document)
    _validate_non_empty("artifact_root", artifact_root)
    _validate_non_empty("provider", provider)
    _validate_non_empty("model_name", model_name)
    excluded_hosts = tuple(_clean_url_host(host) for host in exclude_url_hosts if host.strip())

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="news_rss_raw_body_chunk_index",
        config_json={
            "document_limit": document_limit,
            "external_document_id": external_document_id,
            "exclude_url_hosts": list(excluded_hosts),
            "artifact_root": str(Path(artifact_root)),
            "provider": provider,
            "model_name": model_name,
            "embedding_dimension": embedding_dimension,
            "max_text_chars": max_text_chars,
            "max_chunks_per_document": max_chunks_per_document,
            "external_embedding_api": False,
            "live_llm_call": False,
        },
    )
    results: list[dict[str, object]] = []
    try:
        candidates = load_news_rss_raw_body_chunk_candidates(
            document_limit=document_limit,
            external_document_id=external_document_id,
            exclude_url_hosts=excluded_hosts,
            executor=sql_executor,
        )
        seen_raw_checksums: set[str] = set()
        for candidate in candidates:
            checksum_key = (candidate.checksum or "").strip().lower()
            if checksum_key and checksum_key in seen_raw_checksums:
                results.append(_build_duplicate_skip_result(candidate))
                continue
            if checksum_key:
                seen_raw_checksums.add(checksum_key)
            results.append(
                _process_candidate(
                    candidate,
                    artifact_root=artifact_root,
                    provider=provider,
                    model_name=model_name,
                    embedding_dimension=embedding_dimension,
                    max_text_chars=max_text_chars,
                    max_chunks_per_document=max_chunks_per_document,
                    executor=sql_executor,
                )
            )
        failed_count = sum(1 for result in results if result["status"] == "failed")
        if failed_count:
            _mark_pipeline_run_failed(sql_executor, run_id, f"{failed_count} RSS raw body chunk index documents failed")
            status = "failed"
        else:
            _mark_pipeline_run_succeeded(sql_executor, run_id)
            status = "completed"
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    chunk_count = sum(int(result.get("chunk_count") or 0) for result in results if result["status"] == "succeeded")
    embedding_count = sum(int(result.get("embedding_count") or 0) for result in results if result["status"] == "succeeded")
    skipped_duplicate_count = sum(1 for result in results if result["status"] == "skipped_duplicate_raw_checksum")
    return {
        "report_name": "news_rss_raw_body_chunk_index",
        "run_id": run_id,
        "status": status,
        "provider": provider,
        "model_name": model_name,
        "embedding_dimension": embedding_dimension,
        "requested_document_count": len(results),
        "succeeded_document_count": sum(1 for result in results if result["status"] == "succeeded"),
        "skipped_duplicate_document_count": skipped_duplicate_count,
        "failed_document_count": failed_count,
        "exclude_url_hosts": list(excluded_hosts),
        "chunk_count": chunk_count,
        "embedding_count": embedding_count,
        "external_embedding_api": False,
        "live_llm_call": False,
        "results": results,
    }


def load_news_rss_raw_body_chunk_candidates(
    *,
    document_limit: int,
    external_document_id: str | None,
    exclude_url_hosts: tuple[str, ...] = (),
    executor: PsqlCommandExecutor,
) -> tuple[NewsRssRawBodyChunkCandidate, ...]:
    payload = json.loads(
        executor.execute_scalar(
            render_news_rss_raw_body_chunk_candidate_lookup_sql(
                document_limit=document_limit,
                external_document_id=external_document_id,
                exclude_url_hosts=exclude_url_hosts,
            )
        )
    )
    return tuple(
        NewsRssRawBodyChunkCandidate(
            document_id=int(row["document_id"]),
            external_document_id=str(row["external_document_id"]),
            title=str(row["title"]),
            raw_storage_uri=str(row["raw_storage_uri"]),
            checksum=row.get("checksum"),
            summary=row.get("summary"),
            url=row.get("url"),
        )
        for row in payload
    )


def render_news_rss_raw_body_chunk_candidate_lookup_sql(
    *,
    document_limit: int,
    external_document_id: str | None = None,
    exclude_url_hosts: tuple[str, ...] = (),
) -> str:
    _validate_positive("document_limit", document_limit)
    filters = [
        "d.document_type = 'news_rss_item'",
        "d.raw_storage_uri is not null",
        "btrim(d.raw_storage_uri) <> ''",
    ]
    if external_document_id:
        filters.append(f"d.external_document_id = {sql_literal(external_document_id)}")
    for host in exclude_url_hosts:
        cleaned_host = _clean_url_host(host)
        filters.append(f"not (d.url ~* {sql_literal(_url_host_regex(cleaned_host))})")
    where_clause = "\n      and ".join(filters)
    return f"""select coalesce(
    json_agg(
        json_build_object(
            'document_id', document_id,
            'external_document_id', external_document_id,
            'title', title,
            'summary', summary,
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
        d.summary,
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
    limit {document_limit}
) candidates;"""


def render_news_rss_raw_body_chunk_upsert_sql(
    *,
    candidate: NewsRssRawBodyChunkCandidate,
    chunks: tuple[NewsRssRawBodyChunk, ...],
    provider: str,
    model_name: str,
    embedding_dimension: int,
) -> str:
    if candidate.document_id <= 0:
        raise ValueError("document_id must be greater than 0")
    if not chunks:
        raise ValueError("chunks must not be empty")
    _validate_positive("embedding_dimension", embedding_dimension)
    _validate_non_empty("provider", provider)
    _validate_non_empty("model_name", model_name)

    value_rows = ",\n        ".join(_render_chunk_tuple(chunk) for chunk in chunks)
    chunk_count = len(chunks)
    return f"""with input_chunks (
    chunk_index,
    content_hash,
    text_preview,
    token_count,
    chunk_metadata
) as (
    values
        {value_rows}
),
deleted_stale_chunks as (
    delete from ai.document_chunk chunk
    where chunk.document_id = {candidate.document_id}
      and chunk.chunk_index >= {chunk_count}
    returning chunk.chunk_id
),
upserted_chunks as (
    insert into ai.document_chunk (
        document_id,
        chunk_index,
        content_hash,
        text_preview,
        token_count,
        chunk_metadata
    )
    select
        {candidate.document_id},
        chunk_index,
        content_hash,
        text_preview,
        token_count,
        chunk_metadata
    from input_chunks
    on conflict (document_id, chunk_index) do update
    set
        content_hash = excluded.content_hash,
        text_preview = excluded.text_preview,
        token_count = excluded.token_count,
        chunk_metadata = excluded.chunk_metadata
    returning
        chunk_id,
        document_id,
        chunk_index,
        content_hash
),
deleted_stale_local_embeddings as (
    delete from ai.embedding_index embedding
    using upserted_chunks chunk
    where embedding.chunk_id = chunk.chunk_id
      and embedding.provider = {sql_literal(provider)}
      and (
          embedding.model_name <> {sql_literal(model_name)}
          or embedding.content_hash <> chunk.content_hash
      )
    returning embedding.embedding_id
),
upserted_embeddings as (
    insert into ai.embedding_index (
        chunk_id,
        provider,
        model_name,
        embedding_dimension,
        vector_storage_uri,
        content_hash
    )
    select
        chunk_id,
        {sql_literal(provider)},
        {sql_literal(model_name)},
        {embedding_dimension},
        'local://stockanalysis/news-rss/raw-body/document/' || document_id::text || '/chunk/' || chunk_index::text || '/' || content_hash,
        content_hash
    from upserted_chunks
    on conflict (chunk_id, provider, model_name, content_hash) do update
    set
        embedding_dimension = excluded.embedding_dimension,
        vector_storage_uri = excluded.vector_storage_uri
    returning embedding_id
)
select json_build_object(
    'document_id', {candidate.document_id},
    'external_document_id', {sql_literal(candidate.external_document_id)},
    'chunk_count', (select count(*)::int from upserted_chunks),
    'embedding_count', (select count(*)::int from upserted_embeddings),
    'stale_chunk_deleted_count', (select count(*)::int from deleted_stale_chunks),
    'stale_local_embedding_deleted_count', (select count(*)::int from deleted_stale_local_embeddings)
)::text;"""


def extract_text_from_html(html: str) -> str:
    parser = _ReadableHtmlTextExtractor()
    parser.feed(html)
    parser.close()
    return parser.best_text()


def build_raw_body_chunks(
    *,
    candidate: NewsRssRawBodyChunkCandidate,
    text: str,
    max_text_chars: int,
    max_chunks_per_document: int,
    source_text_kind: str = "raw_html_text",
    used_metadata_fallback: bool = False,
) -> tuple[NewsRssRawBodyChunk, ...]:
    _validate_positive("max_text_chars", max_text_chars)
    _validate_positive("max_chunks_per_document", max_chunks_per_document)
    chunks: list[NewsRssRawBodyChunk] = []
    for chunk_index, chunk_text in enumerate(_split_text(text, max_text_chars=max_text_chars)):
        if chunk_index >= max_chunks_per_document:
            break
        content_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
        chunks.append(
            NewsRssRawBodyChunk(
                chunk_index=chunk_index,
                text=chunk_text,
                content_hash=content_hash,
                token_count=max(1, (len(chunk_text) + 3) // 4),
                metadata={
                    "chunker": "rss-raw-html-text-v1",
                    "source_text_kind": source_text_kind,
                    "document_type": "news_rss_item",
                    "external_document_id": candidate.external_document_id,
                    "raw_storage_uri_present": True,
                    "used_metadata_fallback": used_metadata_fallback,
                    "checksum": candidate.checksum,
                    "local_only": True,
                    "external_embedding_api": False,
                    "live_llm_call": False,
                    "max_text_chars": max_text_chars,
                },
            )
        )
    return tuple(chunks)


def _process_candidate(
    candidate: NewsRssRawBodyChunkCandidate,
    *,
    artifact_root: str,
    provider: str,
    model_name: str,
    embedding_dimension: int,
    max_text_chars: int,
    max_chunks_per_document: int,
    executor: PsqlCommandExecutor,
) -> dict[str, object]:
    try:
        artifact_path = _resolve_artifact_path(candidate.raw_storage_uri, artifact_root=artifact_root)
        body = artifact_path.read_text(encoding="utf-8", errors="replace")
        text = extract_text_from_html(body)
        source_text_kind = "raw_html_text"
        used_metadata_fallback = False
        if not text:
            text = _metadata_fallback_text(candidate)
            source_text_kind = "source_document_metadata_fallback"
            used_metadata_fallback = True
        chunks = build_raw_body_chunks(
            candidate=candidate,
            text=text,
            max_text_chars=max_text_chars,
            max_chunks_per_document=max_chunks_per_document,
            source_text_kind=source_text_kind,
            used_metadata_fallback=used_metadata_fallback,
        )
        if not chunks:
            raise ValueError("raw article artifact produced no readable text chunks")
        payload = json.loads(
            executor.execute_scalar(
                render_news_rss_raw_body_chunk_upsert_sql(
                    candidate=candidate,
                    chunks=chunks,
                    provider=provider,
                    model_name=model_name,
                    embedding_dimension=embedding_dimension,
                )
            )
        )
        return {
            "document_id": candidate.document_id,
            "external_document_id": candidate.external_document_id,
            "title": candidate.title,
            "status": "succeeded",
            "artifact_path": str(artifact_path),
            "chunk_count": int(payload["chunk_count"]),
            "embedding_count": int(payload["embedding_count"]),
            "stale_chunk_deleted_count": int(payload["stale_chunk_deleted_count"]),
            "stale_local_embedding_deleted_count": int(payload["stale_local_embedding_deleted_count"]),
            "source_text_kind": source_text_kind,
            "used_metadata_fallback": used_metadata_fallback,
            "text_preview": chunks[0].text_preview,
        }
    except Exception as exc:
        return {
            "document_id": candidate.document_id,
            "external_document_id": candidate.external_document_id,
            "title": candidate.title,
            "status": "failed",
            "error": str(exc)[:500],
        }


def _build_duplicate_skip_result(candidate: NewsRssRawBodyChunkCandidate) -> dict[str, object]:
    return {
        "document_id": candidate.document_id,
        "external_document_id": candidate.external_document_id,
        "title": candidate.title,
        "status": "skipped_duplicate_raw_checksum",
        "skipped_reason": "raw checksum already processed in this run",
        "source_text_kind": "duplicate_raw_checksum",
        "used_metadata_fallback": False,
    }


def _render_chunk_tuple(chunk: NewsRssRawBodyChunk) -> str:
    metadata = json.dumps(chunk.metadata, ensure_ascii=False, sort_keys=True)
    return (
        f"({chunk.chunk_index}, "
        f"{sql_literal(chunk.content_hash)}, "
        f"{sql_literal(chunk.text_preview)}, "
        f"{chunk.token_count}, "
        f"{sql_literal(metadata)}::jsonb)"
    )


def _metadata_fallback_text(candidate: NewsRssRawBodyChunkCandidate) -> str:
    return _normalize_text(" ".join(part for part in (candidate.title, candidate.summary, candidate.url) if part))


def _resolve_artifact_path(raw_storage_uri: str, *, artifact_root: str) -> Path:
    parsed = urlparse(raw_storage_uri)
    if parsed.scheme != "file":
        raise ValueError("raw_storage_uri must be a file URI")
    if parsed.netloc not in {"", "localhost"}:
        raise ValueError("raw_storage_uri file URI must not include a remote host")
    root = Path(artifact_root).resolve()
    artifact_path = Path(unquote(parsed.path)).resolve()
    try:
        artifact_path.relative_to(root)
    except ValueError as exc:
        raise ValueError("raw_storage_uri must be under artifact_root") from exc
    if not artifact_path.is_file():
        raise ValueError("raw_storage_uri artifact file does not exist")
    return artifact_path


class _ReadableHtmlTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._candidate_texts: list[str] = []
        self._active_candidate_parts: list[str] = []
        self._active_candidate_depth = 0
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[no-untyped-def]
        tag_name = tag.lower()
        if tag_name in {"script", "style", "noscript", "template", "nav", "footer", "aside", "form", "button"}:
            self._skip_depth += 1
            return
        if self._active_candidate_depth:
            self._active_candidate_depth += 1
            return
        if _is_article_candidate_container(tag_name, attrs):
            self._active_candidate_depth = 1
            self._active_candidate_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag_name = tag.lower()
        if tag_name in {"script", "style", "noscript", "template", "nav", "footer", "aside", "form", "button"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._active_candidate_depth:
            self._active_candidate_depth -= 1
            if self._active_candidate_depth == 0:
                text = _clean_article_text(" ".join(self._active_candidate_parts))
                if text:
                    self._candidate_texts.append(text)
                self._active_candidate_parts = []

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        stripped = data.strip()
        if stripped:
            self.parts.append(stripped)
            if self._active_candidate_depth:
                self._active_candidate_parts.append(stripped)

    def close(self) -> None:
        super().close()
        if self._active_candidate_parts:
            text = _clean_article_text(" ".join(self._active_candidate_parts))
            if text:
                self._candidate_texts.append(text)
            self._active_candidate_parts = []
            self._active_candidate_depth = 0

    def best_text(self) -> str:
        if self._candidate_texts:
            return max(self._candidate_texts, key=lambda value: (len(value.split()), len(value)))
        return _clean_article_text(" ".join(self.parts))


def _split_text(text: str, *, max_text_chars: int) -> tuple[str, ...]:
    normalized = _normalize_text(text)
    if not normalized:
        return ()
    chunks: list[str] = []
    current: list[str] = []
    current_length = 0
    for raw_word in normalized.split(" "):
        word = raw_word
        while len(word) > max_text_chars:
            if current:
                chunks.append(" ".join(current))
                current = []
                current_length = 0
            chunks.append(word[:max_text_chars])
            word = word[max_text_chars:]
        projected_length = current_length + len(word) + (1 if current else 0)
        if current and projected_length > max_text_chars:
            chunks.append(" ".join(current))
            current = [word]
            current_length = len(word)
        else:
            current.append(word)
            current_length = projected_length
    if current:
        chunks.append(" ".join(current))
    return tuple(chunks)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _clean_article_text(value: str) -> str:
    text = _normalize_text(value)
    for pattern in _ARTICLE_BOILERPLATE_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)
    return _normalize_text(text)


def _is_article_candidate_container(tag_name: str, attrs) -> bool:  # type: ignore[no-untyped-def]
    if tag_name in {"article", "main"}:
        return True
    attr_text = " ".join(str(value or "") for name, value in attrs if name.lower() in {"class", "id", "role"}).lower()
    return any(keyword in attr_text for keyword in _ARTICLE_CONTAINER_KEYWORDS)


_ARTICLE_CONTAINER_KEYWORDS = (
    "article-body",
    "article-content",
    "article__body",
    "entry-content",
    "post-content",
    "story-body",
    "main-content",
    "article",
)


_ARTICLE_BOILERPLATE_PATTERNS = (
    r"\bskip to content\b",
    r"\bshare share this article\b",
    r"\bshare this article\b",
    r"\bshare x facebook linkedin email\b",
    r"\bx facebook linkedin email\b",
    r"\bx facebook linkedin\b",
    r"\bfacebook linkedin email\b",
    r"\bcopy link link copied!?",
    r"\b0 comments\b",
    r"\bdiscuss \(0\)\s+l\s+t\s+f\s+r\s+e\b",
    r"\blike discuss \(0\)\b",
    r"\brelated resources\b",
)


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
    truncated = error_summary.strip()[:2000] or "news RSS raw body chunk index failed"
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
