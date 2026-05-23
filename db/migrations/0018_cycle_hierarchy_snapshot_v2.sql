create table if not exists signal.cycle_hierarchy_state_snapshot (
    node_id bigint not null references ref.classification_node (node_id) on delete cascade,
    as_of_date date not null,
    cycle_level text not null,
    cycle_state text not null,
    cycle_score numeric(6,4) not null,
    trend_score numeric(6,4),
    breadth_score numeric(6,4),
    event_heat_score numeric(6,4),
    liquidity_score numeric(6,4),
    valuation_pressure numeric(6,4),
    parent_alignment_score numeric(6,4),
    conflict_flags jsonb not null default '[]'::jsonb,
    evidence_event_ids jsonb not null default '[]'::jsonb,
    evidence_json jsonb,
    source_run_id bigint references ops.pipeline_run (run_id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (node_id, as_of_date),
    check (cycle_level in ('macro', 'domain', 'sector', 'theme', 'instrument', 'unknown')),
    check (cycle_state in ('expanding', 'forming', 'neutral', 'cooling', 'structurally_broken', 'unknown')),
    check (cycle_score >= 0 and cycle_score <= 1),
    check (trend_score is null or (trend_score >= 0 and trend_score <= 1)),
    check (breadth_score is null or (breadth_score >= 0 and breadth_score <= 1)),
    check (event_heat_score is null or (event_heat_score >= 0 and event_heat_score <= 1)),
    check (liquidity_score is null or (liquidity_score >= 0 and liquidity_score <= 1)),
    check (valuation_pressure is null or (valuation_pressure >= 0 and valuation_pressure <= 1)),
    check (parent_alignment_score is null or (parent_alignment_score >= 0 and parent_alignment_score <= 1)),
    check (jsonb_typeof(conflict_flags) = 'array'),
    check (jsonb_typeof(evidence_event_ids) = 'array')
);

create index if not exists idx_cycle_hierarchy_state_snapshot_date_level
    on signal.cycle_hierarchy_state_snapshot (as_of_date, cycle_level, cycle_score desc);

create index if not exists idx_cycle_hierarchy_state_snapshot_run
    on signal.cycle_hierarchy_state_snapshot (source_run_id);

create table if not exists signal.cycle_hierarchy_transition_log (
    transition_id bigint generated always as identity primary key,
    node_id bigint not null references ref.classification_node (node_id) on delete cascade,
    as_of_date date not null,
    from_state text not null,
    to_state text not null,
    drivers jsonb not null default '[]'::jsonb,
    evidence_event_ids jsonb not null default '[]'::jsonb,
    source_run_id bigint references ops.pipeline_run (run_id) on delete set null,
    created_at timestamptz not null default now(),
    unique (node_id, as_of_date, from_state, to_state),
    check (jsonb_typeof(drivers) = 'array'),
    check (jsonb_typeof(evidence_event_ids) = 'array')
);

create index if not exists idx_cycle_hierarchy_transition_log_node_date
    on signal.cycle_hierarchy_transition_log (node_id, as_of_date desc);

create index if not exists idx_cycle_hierarchy_transition_log_run
    on signal.cycle_hierarchy_transition_log (source_run_id);
