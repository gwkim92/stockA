create table if not exists signal.asset_correlation_snapshot (
    as_of_date date not null,
    lookback_days integer not null,
    primary_asset_key text not null,
    primary_asset_type text not null,
    primary_instrument_id bigint references ref.instrument(instrument_id) on delete cascade,
    primary_indicator_code text references market.market_indicator(indicator_code) on delete cascade,
    primary_display_name text not null,
    comparison_asset_key text not null,
    comparison_asset_type text not null,
    comparison_instrument_id bigint references ref.instrument(instrument_id) on delete cascade,
    comparison_indicator_code text references market.market_indicator(indicator_code) on delete cascade,
    comparison_display_name text not null,
    observation_count integer not null,
    correlation numeric(10,8),
    beta numeric(16,8),
    primary_return_volatility numeric(16,8),
    comparison_return_volatility numeric(16,8),
    relationship_label text not null,
    confidence numeric(8,6) not null,
    latest_primary_date date,
    latest_comparison_date date,
    source_run_id bigint references ops.pipeline_run(run_id),
    evidence_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (as_of_date, lookback_days, primary_asset_key, comparison_asset_key),
    constraint asset_correlation_lookback_check check (lookback_days > 0),
    constraint asset_correlation_primary_type_check check (primary_asset_type in ('instrument', 'indicator')),
    constraint asset_correlation_comparison_type_check check (comparison_asset_type in ('instrument', 'indicator')),
    constraint asset_correlation_count_check check (observation_count >= 0),
    constraint asset_correlation_value_check check (correlation is null or (correlation >= -1 and correlation <= 1)),
    constraint asset_correlation_confidence_check check (confidence >= 0 and confidence <= 1)
);

create index if not exists asset_correlation_snapshot_primary_idx
    on signal.asset_correlation_snapshot (primary_asset_key, as_of_date desc, lookback_days);

create index if not exists asset_correlation_snapshot_comparison_idx
    on signal.asset_correlation_snapshot (comparison_asset_key, as_of_date desc, lookback_days);

create index if not exists asset_correlation_snapshot_relationship_idx
    on signal.asset_correlation_snapshot (as_of_date desc, relationship_label, confidence desc);
