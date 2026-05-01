#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
CONTAINER_NAME="${AI_INTELLIGENCE_VERIFY_CONTAINER_NAME:-stockanalysis-ai-intelligence-verify}"
POSTGRES_IMAGE="${AI_INTELLIGENCE_VERIFY_POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_DB="${AI_INTELLIGENCE_VERIFY_POSTGRES_DB:-stockanalysis}"
POSTGRES_USER="${AI_INTELLIGENCE_VERIFY_POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${AI_INTELLIGENCE_VERIFY_POSTGRES_PASSWORD:-postgres}"

cleanup() {
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
}

trap cleanup EXIT

cleanup

cd "$ROOT_DIR"

python3 -m compileall src tests >/dev/null
PYTHONPATH=src python3 -m unittest discover -s tests -v

docker run \
  --name "$CONTAINER_NAME" \
  -e POSTGRES_DB="$POSTGRES_DB" \
  -e POSTGRES_USER="$POSTGRES_USER" \
  -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  -d "$POSTGRES_IMAGE" >/dev/null

for _ in $(seq 1 60); do
  if docker exec "$CONTAINER_NAME" pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

docker exec "$CONTAINER_NAME" pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null

for migration in "$ROOT_DIR"/db/migrations/*.sql; do
  docker exec -i "$CONTAINER_NAME" psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$migration" >/dev/null
done

for seed in "$ROOT_DIR"/db/seeds/*.sql; do
  [ -e "$seed" ] || continue
  docker exec -i "$CONTAINER_NAME" psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$seed" >/dev/null
done

expected_table_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from information_schema.tables where table_schema = 'ai' and table_name in ('prompt_template', 'model_invocation', 'document_chunk', 'embedding_index', 'extraction_artifact', 'eval_run');")

test "$expected_table_count" = "6"

docker exec -i "$CONTAINER_NAME" psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null <<'SQL'
with inserted_template as (
    insert into ai.prompt_template (
        template_name,
        template_version,
        system_purpose,
        template_text,
        output_schema_json
    )
    values (
        'event-intelligence-llm-extract',
        '2026-04-23',
        'Extract structured investment events with evidence.',
        'Return structured event evidence only.',
        '{"type":"object","additionalProperties":false}'::jsonb
    )
    returning template_id
),
inserted_run as (
    insert into ops.pipeline_run (
        run_kind,
        pipeline_name,
        status,
        ended_at,
        config_json
    )
    values (
        'verify',
        'ai_intelligence_architecture_verify',
        'succeeded',
        now(),
        '{"verify":"ai_intelligence_architecture"}'::jsonb
    )
    returning run_id
),
inserted_document as (
    insert into ingest.source_document (
        data_source_id,
        external_document_id,
        document_type,
        title,
        summary,
        language
    )
    select
        data_source_id,
        'verify-ai-doc-1',
        'verification_note',
        'AI architecture verification document',
        'Synthetic document for AI metadata schema verification.',
        'en'
    from ingest.data_source
    where source_name = 'manual_research'
    returning document_id
),
inserted_invocation as (
    insert into ai.model_invocation (
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
        request_hash
    )
    select
        inserted_run.run_id,
        'event-intelligence-llm-extract',
        'openai',
        'gpt-5.4-nano',
        'low',
        inserted_template.template_id,
        1200,
        180,
        900,
        0.000500,
        250,
        'succeeded',
        'verify-request-hash'
    from inserted_run, inserted_template
    returning invocation_id
),
inserted_chunk as (
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
        0,
        'verify-content-hash',
        'Synthetic chunk preview.',
        42,
        '{"chunker":"verify"}'::jsonb
    from inserted_document
    returning chunk_id, content_hash
),
inserted_embedding as (
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
        'openai',
        'text-embedding-3-small',
        1536,
        'adapter://verify/vector-store/document/1/chunk/0',
        content_hash
    from inserted_chunk
    returning embedding_id
),
inserted_artifact as (
    insert into ai.extraction_artifact (
        invocation_id,
        document_id,
        artifact_type,
        output_json,
        confidence
    )
    select
        inserted_invocation.invocation_id,
        inserted_document.document_id,
        'structured_event_candidate',
        '{"events":[]}'::jsonb,
        0.9900
    from inserted_invocation, inserted_document
    returning artifact_id
)
insert into ai.eval_run (
    eval_name,
    dataset_version,
    provider,
    model_name,
    prompt_template_id,
    score_json
)
select
    'event-extraction-golden',
    'fixture-v1',
    'openai',
    'gpt-5.4-nano',
    inserted_template.template_id,
    '{"passed":1,"failed":0}'::jsonb
from inserted_template;
SQL

template_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from ai.prompt_template where template_name = 'event-intelligence-llm-extract';")
invocation_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from ai.model_invocation where task_name = 'event-intelligence-llm-extract' and cached_input_token_count = 900;")
chunk_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from ai.document_chunk where content_hash = 'verify-content-hash';")
embedding_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from ai.embedding_index where vector_storage_uri like 'adapter://verify/%';")
artifact_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from ai.extraction_artifact where artifact_type = 'structured_event_candidate';")
eval_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from ai.eval_run where eval_name = 'event-extraction-golden';")

test "$template_count" = "1"
test "$invocation_count" = "1"
test "$chunk_count" = "1"
test "$embedding_count" = "1"
test "$artifact_count" = "1"
test "$eval_count" = "1"
