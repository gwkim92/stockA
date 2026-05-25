create schema if not exists research;

create table if not exists market.financial_metric_normalized (
    instrument_id bigint not null references ref.instrument (instrument_id) on delete cascade,
    as_of_date date not null,
    period_id bigint references market.financial_statement_period (period_id) on delete cascade,
    statement_scope text not null,
    fiscal_year integer not null,
    fiscal_quarter smallint,
    period_end date not null,
    metric_code text not null,
    metric_value numeric(24,8),
    metric_unit text not null,
    metric_status text not null,
    rationale text,
    source_run_id bigint references ops.pipeline_run (run_id),
    created_at timestamptz not null default now(),
    primary key (instrument_id, as_of_date, statement_scope, period_end, metric_code),
    check (fiscal_quarter is null or fiscal_quarter between 1 and 4),
    check (metric_status in ('computed', 'unavailable', 'insufficient_history')),
    check (metric_status <> 'computed' or metric_value is not null)
);

create index if not exists financial_metric_normalized_metric_idx
    on market.financial_metric_normalized (metric_code, as_of_date desc);

create index if not exists financial_metric_normalized_instrument_idx
    on market.financial_metric_normalized (instrument_id, as_of_date desc, metric_code);

create table if not exists ref.peer_group (
    peer_group_id bigint generated always as identity primary key,
    group_code text not null unique,
    name text not null,
    methodology text not null,
    status text not null default 'active',
    created_at timestamptz not null default now(),
    check (status in ('active', 'inactive'))
);

create table if not exists ref.peer_group_member (
    peer_group_id bigint not null references ref.peer_group (peer_group_id) on delete cascade,
    instrument_id bigint not null references ref.instrument (instrument_id) on delete cascade,
    member_role text not null default 'constituent',
    weight numeric(8,4),
    source text not null,
    valid_from date not null,
    valid_to date,
    created_at timestamptz not null default now(),
    primary key (peer_group_id, instrument_id, valid_from),
    check (valid_to is null or valid_to >= valid_from),
    check (weight is null or (weight >= 0 and weight <= 1))
);

create index if not exists peer_group_member_instrument_idx
    on ref.peer_group_member (instrument_id, valid_from desc);

create table if not exists market.peer_relative_snapshot (
    peer_snapshot_id bigint generated always as identity primary key,
    instrument_id bigint not null references ref.instrument (instrument_id) on delete cascade,
    peer_group_id bigint not null references ref.peer_group (peer_group_id) on delete cascade,
    as_of_date date not null,
    metric_code text not null,
    instrument_value numeric(24,8),
    peer_median_value numeric(24,8),
    percentile_rank numeric(8,4),
    relative_signal text not null,
    source_run_id bigint references ops.pipeline_run (run_id),
    created_at timestamptz not null default now(),
    unique (instrument_id, peer_group_id, as_of_date, metric_code),
    check (percentile_rank is null or (percentile_rank >= 0 and percentile_rank <= 1)),
    check (relative_signal in ('above_peer', 'near_peer', 'below_peer', 'insufficient_data'))
);

create table if not exists market.valuation_snapshot (
    valuation_snapshot_id bigint generated always as identity primary key,
    instrument_id bigint not null references ref.instrument (instrument_id) on delete cascade,
    as_of_date date not null,
    method text not null,
    base_price numeric(18,6),
    fair_value_low numeric(18,6),
    fair_value_base numeric(18,6),
    fair_value_high numeric(18,6),
    margin_of_safety numeric(12,6),
    assumptions_json jsonb not null default '{}'::jsonb,
    confidence numeric(5,4),
    source_run_id bigint references ops.pipeline_run (run_id),
    created_at timestamptz not null default now(),
    unique (instrument_id, as_of_date, method),
    check (method in ('dcf_lite', 'relative_multiple', 'scenario_range')),
    check (confidence is null or (confidence >= 0 and confidence <= 1))
);

create index if not exists valuation_snapshot_as_of_idx
    on market.valuation_snapshot (as_of_date desc, method);

create table if not exists research.equity_research_artifact (
    artifact_id bigint generated always as identity primary key,
    instrument_id bigint not null references ref.instrument (instrument_id) on delete cascade,
    as_of_date date not null,
    artifact_type text not null,
    provider text not null,
    model_name text not null,
    title text not null,
    korean_summary text not null,
    key_points_json jsonb not null default '[]'::jsonb,
    catalysts_json jsonb not null default '[]'::jsonb,
    risks_json jsonb not null default '[]'::jsonb,
    invalidation_conditions_json jsonb not null default '[]'::jsonb,
    valuation_sensitivity_json jsonb not null default '{}'::jsonb,
    source_document_ids jsonb not null default '[]'::jsonb,
    source_run_id bigint references ops.pipeline_run (run_id),
    created_at timestamptz not null default now(),
    unique (instrument_id, as_of_date, artifact_type, provider, model_name),
    check (artifact_type in ('business_overview', 'fundamental_review', 'valuation_review', 'full_equity_research'))
);

create index if not exists equity_research_artifact_instrument_idx
    on research.equity_research_artifact (instrument_id, as_of_date desc);
