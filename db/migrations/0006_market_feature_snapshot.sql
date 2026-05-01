create table if not exists signal.feature_definition (
    feature_code text primary key,
    subject_kind text not null,
    feature_name text not null,
    description text not null,
    value_type text not null,
    default_horizon text,
    owner text,
    is_active boolean not null default true
);

create table if not exists signal.instrument_feature_value (
    instrument_id bigint not null references ref.instrument (instrument_id) on delete cascade,
    as_of_date date not null,
    feature_code text not null references signal.feature_definition (feature_code),
    feature_value numeric(24,8),
    feature_text text,
    zscore numeric(24,8),
    source_run_id bigint references ops.pipeline_run (run_id),
    evidence_json jsonb,
    primary key (instrument_id, as_of_date, feature_code)
);

create index if not exists feature_definition_subject_kind_idx
    on signal.feature_definition (subject_kind, is_active);

create index if not exists instrument_feature_value_as_of_date_idx
    on signal.instrument_feature_value (as_of_date desc);

create index if not exists instrument_feature_value_feature_code_idx
    on signal.instrument_feature_value (feature_code, as_of_date desc);

create index if not exists instrument_feature_value_source_run_id_idx
    on signal.instrument_feature_value (source_run_id);
