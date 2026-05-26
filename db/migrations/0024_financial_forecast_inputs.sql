create table if not exists market.financial_forecast_input (
    forecast_input_id bigint generated always as identity primary key,
    instrument_id bigint not null references ref.instrument (instrument_id) on delete cascade,
    as_of_date date not null,
    statement_scope text not null,
    scenario_key text not null,
    forecast_year integer not null,
    revenue numeric(24,8),
    revenue_growth_rate numeric(12,6),
    operating_margin numeric(12,6),
    free_cash_flow_margin numeric(12,6),
    capex_intensity numeric(12,6),
    free_cash_flow numeric(24,8),
    assumptions_json jsonb not null default '{}'::jsonb,
    confidence numeric(5,4),
    source_run_id bigint references ops.pipeline_run (run_id),
    created_at timestamptz not null default now(),
    unique (instrument_id, as_of_date, statement_scope, scenario_key, forecast_year),
    check (statement_scope in ('annual', 'quarterly')),
    check (scenario_key in ('bear', 'base', 'bull')),
    check (forecast_year between 1 and 5),
    check (confidence is null or (confidence >= 0 and confidence <= 1))
);

create index if not exists financial_forecast_input_lookup_idx
    on market.financial_forecast_input (instrument_id, as_of_date desc, statement_scope, scenario_key, forecast_year);
