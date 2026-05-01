create table if not exists performance.recommendation_outcome (
    outcome_id bigint generated always as identity primary key,
    recommendation_id bigint not null references signal.recommendation (recommendation_id) on delete cascade,
    measurement_start_date date not null,
    measurement_end_date date not null,
    horizon_days integer not null,
    entry_price numeric(18,6) not null,
    exit_price numeric(18,6) not null,
    absolute_return_pct numeric(12,6) not null,
    benchmark_code text,
    benchmark_return_pct numeric(12,6),
    alpha_pct numeric(12,6),
    max_drawdown_pct numeric(12,6),
    outcome_label text not null,
    source_run_id bigint references ops.pipeline_run (run_id),
    created_at timestamptz not null default now(),
    check (measurement_end_date >= measurement_start_date),
    check (horizon_days >= 0),
    check (entry_price > 0),
    check (exit_price > 0)
);

create unique index if not exists recommendation_outcome_identity_uidx
    on performance.recommendation_outcome (recommendation_id, measurement_end_date);

create index if not exists recommendation_outcome_measurement_end_date_idx
    on performance.recommendation_outcome (measurement_end_date desc);

create index if not exists recommendation_outcome_source_run_id_idx
    on performance.recommendation_outcome (source_run_id);

create index if not exists recommendation_outcome_label_idx
    on performance.recommendation_outcome (outcome_label);

create table if not exists performance.thesis_outcome (
    outcome_id bigint generated always as identity primary key,
    thesis_id bigint not null references signal.investment_thesis (thesis_id) on delete cascade,
    recommendation_id bigint references signal.recommendation (recommendation_id) on delete set null,
    measurement_start_date date not null,
    measurement_end_date date not null,
    holding_days integer not null,
    status text not null,
    absolute_return_pct numeric(12,6) not null,
    benchmark_code text,
    benchmark_return_pct numeric(12,6),
    alpha_pct numeric(12,6),
    success_grade text not null,
    summary text not null,
    source_run_id bigint references ops.pipeline_run (run_id),
    created_at timestamptz not null default now(),
    check (measurement_end_date >= measurement_start_date),
    check (holding_days >= 0)
);

create unique index if not exists thesis_outcome_identity_uidx
    on performance.thesis_outcome (thesis_id, measurement_end_date);

create index if not exists thesis_outcome_measurement_end_date_idx
    on performance.thesis_outcome (measurement_end_date desc);

create index if not exists thesis_outcome_source_run_id_idx
    on performance.thesis_outcome (source_run_id);

create index if not exists thesis_outcome_success_grade_idx
    on performance.thesis_outcome (success_grade);
