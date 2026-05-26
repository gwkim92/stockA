create table if not exists research.segment_footnote_evidence (
    evidence_id bigint generated always as identity primary key,
    instrument_id bigint not null references ref.instrument (instrument_id) on delete cascade,
    as_of_date date not null,
    statement_scope text not null,
    segment_key text not null,
    segment_label text not null,
    evidence_type text not null,
    metric_code text not null,
    metric_value numeric(24,8),
    metric_unit text not null,
    period_end date not null,
    source_document_id bigint references ingest.source_document (document_id) on delete set null,
    evidence_text text,
    assumptions_json jsonb not null default '{}'::jsonb,
    confidence numeric(5,4),
    source_run_id bigint references ops.pipeline_run (run_id),
    created_at timestamptz not null default now(),
    unique (
        instrument_id,
        as_of_date,
        statement_scope,
        segment_key,
        evidence_type,
        metric_code,
        period_end
    ),
    check (statement_scope in ('annual', 'quarterly')),
    check (evidence_type in (
        'filing_anchor',
        'consolidated_metric',
        'reported_segment_metric',
        'segment_data_gap'
    )),
    check (confidence is null or (confidence >= 0 and confidence <= 1))
);

create index if not exists segment_footnote_evidence_lookup_idx
    on research.segment_footnote_evidence (instrument_id, as_of_date desc, statement_scope, evidence_type);

create index if not exists segment_footnote_evidence_source_document_idx
    on research.segment_footnote_evidence (source_document_id)
    where source_document_id is not null;
