create table if not exists market.sum_of_parts_component (
    component_id bigint generated always as identity primary key,
    instrument_id bigint not null references ref.instrument (instrument_id) on delete cascade,
    as_of_date date not null,
    statement_scope text not null,
    component_key text not null,
    component_label text not null,
    component_type text not null,
    fair_value_low numeric(18,6),
    fair_value_base numeric(18,6),
    fair_value_high numeric(18,6),
    valuation_basis text not null,
    assumptions_json jsonb not null default '{}'::jsonb,
    confidence numeric(5,4),
    source_run_id bigint references ops.pipeline_run (run_id),
    created_at timestamptz not null default now(),
    unique (instrument_id, as_of_date, statement_scope, component_key),
    check (statement_scope in ('annual', 'quarterly')),
    check (component_type in ('operating_business', 'balance_sheet_adjustment', 'risk_reserve')),
    check (confidence is null or (confidence >= 0 and confidence <= 1))
);

create index if not exists sum_of_parts_component_lookup_idx
    on market.sum_of_parts_component (instrument_id, as_of_date desc, statement_scope, component_type);

alter table market.valuation_snapshot
    drop constraint if exists valuation_snapshot_method_check;

alter table market.valuation_snapshot
    add constraint valuation_snapshot_method_check
    check (method in ('dcf_lite', 'relative_multiple', 'scenario_range', 'sum_of_parts'));
