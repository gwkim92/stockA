create table if not exists research.industry_competitive_position (
    competitive_position_id bigint generated always as identity primary key,
    instrument_id bigint not null references ref.instrument (instrument_id) on delete cascade,
    peer_group_id bigint not null references ref.peer_group (peer_group_id) on delete cascade,
    sector_node_id bigint references ref.classification_node (node_id) on delete set null,
    as_of_date date not null,
    methodology text not null,
    competitive_position text not null,
    moat_score numeric(5,4),
    pricing_power_score numeric(5,4),
    profitability_score numeric(5,4),
    growth_position_score numeric(5,4),
    financial_strength_score numeric(5,4),
    rivalry_risk_score numeric(5,4),
    buyer_power_risk_score numeric(5,4),
    supplier_power_risk_score numeric(5,4),
    substitute_threat_risk_score numeric(5,4),
    new_entry_threat_risk_score numeric(5,4),
    capacity_cycle_risk_score numeric(5,4),
    metric_coverage_count integer not null default 0,
    peer_count integer not null default 0,
    key_strengths_json jsonb not null default '[]'::jsonb,
    key_risks_json jsonb not null default '[]'::jsonb,
    peer_context_json jsonb not null default '{}'::jsonb,
    rationale text,
    source_run_id bigint references ops.pipeline_run (run_id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (instrument_id, peer_group_id, as_of_date, methodology),
    check (competitive_position in ('leader', 'advantaged', 'in_line', 'challenged', 'insufficient_data')),
    check (moat_score is null or (moat_score >= 0 and moat_score <= 1)),
    check (pricing_power_score is null or (pricing_power_score >= 0 and pricing_power_score <= 1)),
    check (profitability_score is null or (profitability_score >= 0 and profitability_score <= 1)),
    check (growth_position_score is null or (growth_position_score >= 0 and growth_position_score <= 1)),
    check (financial_strength_score is null or (financial_strength_score >= 0 and financial_strength_score <= 1)),
    check (rivalry_risk_score is null or (rivalry_risk_score >= 0 and rivalry_risk_score <= 1)),
    check (buyer_power_risk_score is null or (buyer_power_risk_score >= 0 and buyer_power_risk_score <= 1)),
    check (supplier_power_risk_score is null or (supplier_power_risk_score >= 0 and supplier_power_risk_score <= 1)),
    check (substitute_threat_risk_score is null or (substitute_threat_risk_score >= 0 and substitute_threat_risk_score <= 1)),
    check (new_entry_threat_risk_score is null or (new_entry_threat_risk_score >= 0 and new_entry_threat_risk_score <= 1)),
    check (capacity_cycle_risk_score is null or (capacity_cycle_risk_score >= 0 and capacity_cycle_risk_score <= 1)),
    check (metric_coverage_count >= 0),
    check (peer_count >= 0)
);

create index if not exists industry_competitive_position_instrument_idx
    on research.industry_competitive_position (instrument_id, as_of_date desc);

create index if not exists industry_competitive_position_peer_group_idx
    on research.industry_competitive_position (peer_group_id, as_of_date desc);

create index if not exists industry_competitive_position_sector_idx
    on research.industry_competitive_position (sector_node_id, as_of_date desc);

create index if not exists industry_competitive_position_source_run_idx
    on research.industry_competitive_position (source_run_id);
