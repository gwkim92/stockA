create table if not exists performance.attribution_run (
    attribution_run_id bigint generated always as identity primary key,
    portfolio_id bigint not null references portfolio.portfolio (portfolio_id) on delete cascade,
    snapshot_date date not null,
    measurement_start_date date not null,
    measurement_end_date date not null,
    methodology text not null,
    source_run_id bigint references ops.pipeline_run (run_id),
    created_at timestamptz not null default now(),
    check (measurement_end_date >= measurement_start_date)
);

create unique index if not exists attribution_run_identity_uidx
    on performance.attribution_run (portfolio_id, snapshot_date, measurement_end_date, methodology);

create index if not exists attribution_run_portfolio_date_idx
    on performance.attribution_run (portfolio_id, snapshot_date desc, measurement_end_date desc);

create index if not exists attribution_run_source_run_id_idx
    on performance.attribution_run (source_run_id);

create table if not exists performance.attribution_component (
    attribution_component_id bigint generated always as identity primary key,
    attribution_run_id bigint not null references performance.attribution_run (attribution_run_id) on delete cascade,
    component_type text not null,
    component_key text not null,
    instrument_id bigint references ref.instrument (instrument_id) on delete set null,
    thesis_id bigint references signal.investment_thesis (thesis_id) on delete set null,
    recommendation_id bigint references signal.recommendation (recommendation_id) on delete set null,
    weight numeric(8,4),
    return_pct numeric(12,6),
    benchmark_return_pct numeric(12,6),
    alpha_pct numeric(12,6),
    contribution_bps numeric(12,4) not null,
    summary text,
    created_at timestamptz not null default now()
);

create unique index if not exists attribution_component_identity_uidx
    on performance.attribution_component (attribution_run_id, component_type, component_key);

create index if not exists attribution_component_run_id_idx
    on performance.attribution_component (attribution_run_id);

create index if not exists attribution_component_type_idx
    on performance.attribution_component (component_type);

create index if not exists attribution_component_instrument_id_idx
    on performance.attribution_component (instrument_id);

create index if not exists attribution_component_thesis_id_idx
    on performance.attribution_component (thesis_id);
