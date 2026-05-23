create table if not exists ai.cycle_community_summary (
    node_id bigint not null references ref.classification_node (node_id) on delete cascade,
    as_of_date date not null,
    summary_type text not null,
    summary_json jsonb not null,
    source_run_id bigint references ops.pipeline_run (run_id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (node_id, as_of_date, summary_type),
    check (summary_type in ('cycle_graph_context_v1')),
    check (jsonb_typeof(summary_json) = 'object')
);

create index if not exists idx_cycle_community_summary_date_type
    on ai.cycle_community_summary (as_of_date desc, summary_type);

create index if not exists idx_cycle_community_summary_run
    on ai.cycle_community_summary (source_run_id);
