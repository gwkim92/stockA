create schema if not exists ai;

create table if not exists ai.prompt_template (
    template_id bigint generated always as identity primary key,
    template_name text not null,
    template_version text not null,
    system_purpose text not null,
    template_text text not null,
    output_schema_json jsonb,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    unique (template_name, template_version)
);

create table if not exists ai.model_invocation (
    invocation_id bigint generated always as identity primary key,
    run_id bigint references ops.pipeline_run (run_id) on delete set null,
    task_name text not null,
    provider text not null,
    model_name text not null,
    reasoning_effort text,
    prompt_template_id bigint references ai.prompt_template (template_id) on delete set null,
    input_token_count integer,
    output_token_count integer,
    cached_input_token_count integer,
    estimated_cost_usd numeric(12,6),
    latency_ms integer,
    status text not null,
    error_summary text,
    request_hash text,
    created_at timestamptz not null default now(),
    check (input_token_count is null or input_token_count >= 0),
    check (output_token_count is null or output_token_count >= 0),
    check (cached_input_token_count is null or cached_input_token_count >= 0),
    check (estimated_cost_usd is null or estimated_cost_usd >= 0),
    check (latency_ms is null or latency_ms >= 0)
);

create table if not exists ai.document_chunk (
    chunk_id bigint generated always as identity primary key,
    document_id bigint not null references ingest.source_document (document_id) on delete cascade,
    chunk_index integer not null,
    content_hash text not null,
    text_preview text,
    token_count integer,
    chunk_metadata jsonb,
    created_at timestamptz not null default now(),
    unique (document_id, chunk_index),
    check (chunk_index >= 0),
    check (token_count is null or token_count >= 0)
);

create table if not exists ai.embedding_index (
    embedding_id bigint generated always as identity primary key,
    chunk_id bigint not null references ai.document_chunk (chunk_id) on delete cascade,
    provider text not null,
    model_name text not null,
    embedding_dimension integer not null,
    vector_storage_uri text not null,
    content_hash text not null,
    created_at timestamptz not null default now(),
    unique (chunk_id, provider, model_name, content_hash),
    check (embedding_dimension > 0)
);

create table if not exists ai.extraction_artifact (
    artifact_id bigint generated always as identity primary key,
    invocation_id bigint not null references ai.model_invocation (invocation_id) on delete cascade,
    document_id bigint references ingest.source_document (document_id) on delete set null,
    event_id bigint references event.event (event_id) on delete set null,
    artifact_type text not null,
    output_json jsonb not null,
    confidence numeric(5,4),
    created_at timestamptz not null default now(),
    check (confidence is null or (confidence >= 0 and confidence <= 1))
);

create table if not exists ai.eval_run (
    eval_run_id bigint generated always as identity primary key,
    eval_name text not null,
    dataset_version text not null,
    provider text not null,
    model_name text not null,
    prompt_template_id bigint references ai.prompt_template (template_id) on delete set null,
    score_json jsonb not null,
    created_at timestamptz not null default now()
);

create index if not exists ai_prompt_template_active_idx
    on ai.prompt_template (template_name, is_active);

create index if not exists ai_model_invocation_run_id_idx
    on ai.model_invocation (run_id);

create index if not exists ai_model_invocation_task_status_idx
    on ai.model_invocation (task_name, status, created_at desc);

create index if not exists ai_model_invocation_request_hash_idx
    on ai.model_invocation (request_hash)
    where request_hash is not null;

create index if not exists ai_document_chunk_document_idx
    on ai.document_chunk (document_id, chunk_index);

create index if not exists ai_embedding_index_chunk_idx
    on ai.embedding_index (chunk_id);

create index if not exists ai_extraction_artifact_document_idx
    on ai.extraction_artifact (document_id, artifact_type);

create index if not exists ai_extraction_artifact_event_idx
    on ai.extraction_artifact (event_id)
    where event_id is not null;

create index if not exists ai_eval_run_name_created_idx
    on ai.eval_run (eval_name, created_at desc);
