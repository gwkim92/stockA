create table if not exists market.market_indicator (
    indicator_code text primary key,
    display_name text not null,
    indicator_type text not null,
    preferred_provider text not null,
    fallback_provider text,
    provider_symbol text,
    fred_series_code text,
    instrument_symbol text,
    cboe_csv_url text,
    daily_budget_cost numeric(8,2) not null default 0,
    freshness_sla_days integer not null default 3,
    license_note text not null default '',
    redistribution_allowed_note text not null default '',
    stale_policy text not null default 'mark_stale_no_imputation',
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint market_indicator_provider_check
        check (preferred_provider in ('fred', 'cboe_csv', 'twelve_data', 'sec_edgar', 'rss_gdelt')),
    constraint market_indicator_budget_check check (daily_budget_cost >= 0),
    constraint market_indicator_freshness_check check (freshness_sla_days >= 0)
);

create table if not exists market.market_indicator_observation (
    indicator_code text not null references market.market_indicator(indicator_code),
    observation_date date not null,
    provider text not null,
    source_kind text not null,
    value numeric(24,8) not null,
    open numeric(24,8),
    high numeric(24,8),
    low numeric(24,8),
    close numeric(24,8),
    adjusted_close numeric(24,8),
    volume numeric(24,4),
    source_run_id bigint references ops.pipeline_run(run_id),
    evidence_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (indicator_code, observation_date, provider),
    constraint market_indicator_observation_source_kind_check
        check (source_kind in ('macro_series', 'price_bar', 'official_csv', 'derived'))
);

create index if not exists market_indicator_observation_date_idx
    on market.market_indicator_observation(observation_date desc);

create table if not exists signal.market_indicator_snapshot (
    indicator_code text not null references market.market_indicator(indicator_code),
    as_of_date date not null,
    latest_observation_date date,
    latest_value numeric(24,8),
    return_1d numeric(16,8),
    return_5d numeric(16,8),
    return_20d numeric(16,8),
    return_60d numeric(16,8),
    return_120d numeric(16,8),
    moving_average_20d numeric(24,8),
    moving_average_50d numeric(24,8),
    moving_average_200d numeric(24,8),
    percentile_252d numeric(8,6),
    z_score_252d numeric(16,8),
    drawdown_252d numeric(16,8),
    realized_volatility_20d numeric(16,8),
    trend_state text not null,
    shock_direction text not null,
    shock_magnitude numeric(8,6) not null default 0,
    confidence numeric(8,6) not null default 0,
    freshness_status text not null,
    source_run_id bigint references ops.pipeline_run(run_id),
    evidence_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (indicator_code, as_of_date),
    constraint market_indicator_snapshot_trend_state_check
        check (trend_state in ('up', 'down', 'flat', 'stale', 'insufficient_history')),
    constraint market_indicator_snapshot_shock_direction_check
        check (shock_direction in ('up', 'down', 'neutral')),
    constraint market_indicator_snapshot_freshness_check
        check (freshness_status in ('fresh', 'stale', 'missing'))
);

create table if not exists signal.cross_asset_regime_snapshot (
    regime_code text not null,
    as_of_date date not null,
    regime_state text not null,
    regime_score numeric(8,6) not null,
    confidence numeric(8,6) not null,
    driver_indicator_codes text[] not null default '{}'::text[],
    conflict_flags text[] not null default '{}'::text[],
    source_run_id bigint references ops.pipeline_run(run_id),
    evidence_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (regime_code, as_of_date),
    constraint cross_asset_regime_state_check
        check (regime_state in ('active', 'watch', 'inactive', 'mixed', 'insufficient_data'))
);

create table if not exists event.news_indicator_link (
    document_id bigint not null references ingest.source_document(document_id),
    event_id bigint references event.event(event_id),
    indicator_code text not null references market.market_indicator(indicator_code),
    link_date date not null,
    link_type text not null,
    relationship text not null,
    confidence numeric(8,6) not null,
    rationale text not null,
    source_run_id bigint references ops.pipeline_run(run_id),
    evidence_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    primary key (document_id, indicator_code, link_date, relationship),
    constraint news_indicator_link_type_check
        check (link_type in ('temporal_evidence', 'supports_thesis', 'conflicting_evidence')),
    constraint news_indicator_relationship_check
        check (relationship in ('news_with_indicator_shock', 'news_without_indicator_confirmation'))
);

create index if not exists news_indicator_link_event_idx
    on event.news_indicator_link(event_id, link_date desc);

create table if not exists signal.cross_asset_cycle_impact (
    as_of_date date not null,
    regime_code text not null,
    node_id bigint not null references ref.classification_node(node_id),
    impact_direction text not null,
    impact_strength numeric(8,6) not null,
    confidence numeric(8,6) not null,
    rationale text not null,
    source_run_id bigint references ops.pipeline_run(run_id),
    evidence_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (as_of_date, regime_code, node_id),
    constraint cross_asset_cycle_impact_direction_check
        check (impact_direction in ('supportive', 'risk_review', 'watch', 'neutral'))
);
