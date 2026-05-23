create table if not exists signal.hierarchical_propagated_instrument_impact (
    event_id bigint not null references event.event (event_id) on delete cascade,
    source_node_id bigint not null references ref.classification_node (node_id) on delete cascade,
    propagated_node_id bigint not null references ref.classification_node (node_id) on delete cascade,
    instrument_id bigint not null references ref.instrument (instrument_id) on delete cascade,
    propagation_kind text not null default 'hierarchical_factor_exposure',
    node_path_codes jsonb not null,
    path_hash text not null,
    path_depth integer not null,
    path_weight numeric(8,6) not null,
    decay numeric(6,4) not null,
    impact_direction text not null,
    impact_strength numeric(5,4),
    confidence numeric(5,4),
    exposure_weight numeric(6,4),
    rationale text,
    source_run_id bigint references ops.pipeline_run (run_id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (
        event_id,
        source_node_id,
        propagated_node_id,
        instrument_id,
        propagation_kind,
        path_hash
    ),
    check (propagation_kind in ('hierarchical_factor_exposure')),
    check (jsonb_typeof(node_path_codes) = 'array'),
    check (path_depth >= 0 and path_depth <= 10),
    check (path_weight > 0 and path_weight <= 1),
    check (decay > 0 and decay <= 1),
    check (impact_direction in ('supportive', 'risk_review', 'watch', 'mixed', 'unknown')),
    check (impact_strength is null or (impact_strength >= 0 and impact_strength <= 1)),
    check (confidence is null or (confidence >= 0 and confidence <= 1)),
    check (exposure_weight is null or (exposure_weight > 0 and exposure_weight <= 1))
);

create index if not exists idx_hierarchical_propagated_impact_event
    on signal.hierarchical_propagated_instrument_impact (event_id, source_node_id, propagated_node_id);

create index if not exists idx_hierarchical_propagated_impact_instrument
    on signal.hierarchical_propagated_instrument_impact (instrument_id, propagated_node_id, event_id);

create index if not exists idx_hierarchical_propagated_impact_run
    on signal.hierarchical_propagated_instrument_impact (source_run_id);
