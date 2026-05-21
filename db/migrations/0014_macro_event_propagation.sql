create table if not exists ref.instrument_factor_exposure (
    instrument_id bigint not null references ref.instrument (instrument_id) on delete cascade,
    node_id bigint not null references ref.classification_node (node_id) on delete cascade,
    exposure_type text not null default 'macro_sensitivity',
    exposure_weight numeric(6,4) not null,
    sensitivity_direction text not null,
    confidence numeric(5,4),
    rationale text,
    valid_from date not null,
    valid_to date,
    source_document_id bigint references ingest.source_document (document_id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (instrument_id, node_id, exposure_type, valid_from),
    check (exposure_type in ('macro_sensitivity', 'theme_membership', 'sector_proxy', 'manual_seed')),
    check (exposure_weight > 0 and exposure_weight <= 1),
    check (sensitivity_direction in ('positive', 'negative', 'neutral', 'mixed')),
    check (confidence is null or (confidence >= 0 and confidence <= 1)),
    check (valid_to is null or valid_to >= valid_from)
);

create index if not exists idx_instrument_factor_exposure_node_active
    on ref.instrument_factor_exposure (node_id, valid_from, valid_to);

create index if not exists idx_instrument_factor_exposure_instrument_active
    on ref.instrument_factor_exposure (instrument_id, valid_from, valid_to);

create table if not exists signal.propagated_instrument_impact (
    event_id bigint not null references event.event (event_id) on delete cascade,
    node_id bigint not null references ref.classification_node (node_id) on delete cascade,
    instrument_id bigint not null references ref.instrument (instrument_id) on delete cascade,
    propagation_kind text not null default 'factor_exposure',
    impact_direction text not null,
    impact_strength numeric(5,4),
    confidence numeric(5,4),
    exposure_weight numeric(6,4),
    rationale text,
    source_run_id bigint references ops.pipeline_run (run_id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (event_id, node_id, instrument_id, propagation_kind),
    check (propagation_kind in ('factor_exposure')),
    check (impact_direction in ('supportive', 'risk_review', 'watch', 'mixed', 'unknown')),
    check (impact_strength is null or (impact_strength >= 0 and impact_strength <= 1)),
    check (confidence is null or (confidence >= 0 and confidence <= 1)),
    check (exposure_weight is null or (exposure_weight > 0 and exposure_weight <= 1))
);

create index if not exists idx_propagated_instrument_impact_instrument
    on signal.propagated_instrument_impact (instrument_id, node_id, event_id);

create index if not exists idx_propagated_instrument_impact_node
    on signal.propagated_instrument_impact (node_id, event_id);

create index if not exists idx_propagated_instrument_impact_run
    on signal.propagated_instrument_impact (source_run_id);
