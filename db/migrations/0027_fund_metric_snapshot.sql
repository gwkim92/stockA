create table if not exists market.fund_metric_snapshot (
    fund_metric_snapshot_id bigint generated always as identity primary key,
    instrument_id bigint not null references ref.instrument (instrument_id) on delete cascade,
    as_of_date date not null,
    metric_code text not null,
    metric_value numeric(18,8) not null,
    metric_unit text not null,
    source_name text not null,
    source_url text not null,
    source_as_of_date date not null,
    source_observed_at timestamptz not null default now(),
    confidence numeric(5,4) not null default 0.9000,
    rationale text,
    source_run_id bigint references ops.pipeline_run (run_id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (instrument_id, metric_code, source_name, source_as_of_date),
    check (metric_code in ('gross_expense_ratio', 'net_expense_ratio')),
    check (metric_unit = 'ratio'),
    check (metric_value >= 0 and metric_value < 1),
    check (confidence >= 0 and confidence <= 1)
);

create index if not exists fund_metric_snapshot_instrument_metric_idx
    on market.fund_metric_snapshot (instrument_id, metric_code, source_as_of_date desc);
