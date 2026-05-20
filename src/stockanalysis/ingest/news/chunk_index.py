from __future__ import annotations

import json

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor


DEFAULT_RSS_CHUNK_INDEX_DOCUMENT_LIMIT = 100
DEFAULT_RSS_CHUNK_INDEX_PROVIDER = "local_deterministic"
DEFAULT_RSS_CHUNK_INDEX_MODEL_NAME = "rss_title_summary_hash_v1"
DEFAULT_RSS_CHUNK_INDEX_EMBEDDING_DIMENSION = 1
DEFAULT_RSS_CHUNK_INDEX_MAX_TEXT_CHARS = 1600


def run_news_rss_local_chunk_index(
    *,
    config: RuntimeConfig,
    document_limit: int = DEFAULT_RSS_CHUNK_INDEX_DOCUMENT_LIMIT,
    provider: str = DEFAULT_RSS_CHUNK_INDEX_PROVIDER,
    model_name: str = DEFAULT_RSS_CHUNK_INDEX_MODEL_NAME,
    embedding_dimension: int = DEFAULT_RSS_CHUNK_INDEX_EMBEDDING_DIMENSION,
    max_text_chars: int = DEFAULT_RSS_CHUNK_INDEX_MAX_TEXT_CHARS,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    _validate_positive("document_limit", document_limit)
    _validate_positive("embedding_dimension", embedding_dimension)
    _validate_positive("max_text_chars", max_text_chars)
    _validate_non_empty("provider", provider)
    _validate_non_empty("model_name", model_name)

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="news_rss_local_chunk_index",
        config_json={
            "document_limit": document_limit,
            "provider": provider,
            "model_name": model_name,
            "embedding_dimension": embedding_dimension,
            "max_text_chars": max_text_chars,
            "external_embedding_api": False,
            "live_llm_call": False,
        },
    )
    try:
        payload = json.loads(
            sql_executor.execute_scalar(
                render_news_rss_local_chunk_index_sql(
                    document_limit=document_limit,
                    provider=provider,
                    model_name=model_name,
                    embedding_dimension=embedding_dimension,
                    max_text_chars=max_text_chars,
                )
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    payload["run_id"] = run_id
    payload["status"] = "completed"
    return payload


def render_news_rss_local_chunk_index_sql(
    *,
    document_limit: int = DEFAULT_RSS_CHUNK_INDEX_DOCUMENT_LIMIT,
    provider: str = DEFAULT_RSS_CHUNK_INDEX_PROVIDER,
    model_name: str = DEFAULT_RSS_CHUNK_INDEX_MODEL_NAME,
    embedding_dimension: int = DEFAULT_RSS_CHUNK_INDEX_EMBEDDING_DIMENSION,
    max_text_chars: int = DEFAULT_RSS_CHUNK_INDEX_MAX_TEXT_CHARS,
) -> str:
    _validate_positive("document_limit", document_limit)
    _validate_positive("embedding_dimension", embedding_dimension)
    _validate_positive("max_text_chars", max_text_chars)
    _validate_non_empty("provider", provider)
    _validate_non_empty("model_name", model_name)

    return f"""-- news rss local chunk index upsert
with candidate_documents as (
    select
        d.document_id,
        d.external_document_id,
        d.document_type,
        d.title,
        d.summary,
        d.url,
        d.language,
        d.published_at,
        d.checksum,
        ds.source_name,
        ds.source_kind
    from ingest.source_document d
    join ingest.data_source ds
      on ds.data_source_id = d.data_source_id
    where d.document_type = 'news_rss_item'
       or ds.source_kind = 'news_rss'
       or ds.source_name like 'rss_news:%'
       or d.external_document_id like 'rss:%'
    order by d.published_at desc nulls last, d.document_id desc
    limit {document_limit}
),
bounded_documents as (
    select
        document_id,
        external_document_id,
        document_type,
        source_name,
        source_kind,
        title,
        summary,
        url,
        language,
        published_at,
        checksum,
        left(
            btrim(
                regexp_replace(
                    concat_ws(E'\\n\\n', nullif(title, ''), nullif(summary, ''), nullif(url, '')),
                    '[[:space:]]+',
                    ' ',
                    'g'
                )
            ),
            {max_text_chars}
        ) as chunk_text
    from candidate_documents
),
chunk_input as (
    select
        document_id,
        0 as chunk_index,
        md5(chunk_text) as content_hash,
        left(chunk_text, 500) as text_preview,
        greatest(1, ceiling(length(chunk_text)::numeric / 4)::int) as token_count,
        jsonb_strip_nulls(
            jsonb_build_object(
                'chunker', 'rss-title-summary-url-v1',
                'source_name', source_name,
                'source_kind', source_kind,
                'document_type', document_type,
                'external_document_id', external_document_id,
                'language', language,
                'published_at', published_at,
                'checksum', checksum,
                'url', url,
                'local_only', true,
                'external_embedding_api', false,
                'live_llm_call', false,
                'max_text_chars', {max_text_chars}
            )
        ) as chunk_metadata
    from bounded_documents
    where chunk_text <> ''
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
        document_id,
        chunk_index,
        content_hash,
        text_preview,
        token_count,
        chunk_metadata
    from chunk_input
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
deleted_stale_embeddings as (
    delete from ai.embedding_index e
    using upserted_chunks c
    where e.chunk_id = c.chunk_id
      and e.provider = {sql_literal(provider)}
      and e.model_name = {sql_literal(model_name)}
      and e.content_hash <> c.content_hash
    returning e.embedding_id
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
        'local://stockanalysis/news-rss/document/' || document_id::text || '/chunk/' || chunk_index::text || '/' || content_hash,
        content_hash
    from upserted_chunks
    on conflict (chunk_id, provider, model_name, content_hash) do update
    set
        embedding_dimension = excluded.embedding_dimension,
        vector_storage_uri = excluded.vector_storage_uri
    returning embedding_id, chunk_id
)
select json_build_object(
    'report_name', 'news_rss_local_chunk_index',
    'provider', {sql_literal(provider)},
    'model_name', {sql_literal(model_name)},
    'embedding_dimension', {embedding_dimension},
    'document_limit', {document_limit},
    'candidate_document_count', (select count(*)::int from candidate_documents),
    'chunk_count', (select count(*)::int from upserted_chunks),
    'embedding_count', (select count(*)::int from upserted_embeddings),
    'stale_embedding_deleted_count', (select count(*)::int from deleted_stale_embeddings),
    'external_embedding_api', false,
    'live_llm_call', false
)::text;"""


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
    truncated = error_summary.strip()[:2000] or "news RSS local chunk index failed"
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
