create table if not exists ops.pipeline_run (
    run_id bigint generated always as identity primary key,
    run_kind text not null,
    pipeline_name text not null,
    code_version text,
    started_at timestamptz not null default now(),
    ended_at timestamptz,
    status text not null,
    config_json jsonb,
    error_summary text,
    check (ended_at is null or ended_at >= started_at)
);

create table if not exists ref.market (
    market_code text primary key,
    name text not null,
    country_code text not null,
    currency_code text not null,
    timezone text not null,
    is_active boolean not null default true
);

create table if not exists ref.exchange (
    exchange_id bigint generated always as identity primary key,
    market_code text not null references ref.market (market_code),
    mic_code text not null unique,
    name text not null,
    timezone text not null,
    is_primary boolean not null default false
);

create table if not exists ref.issuer (
    issuer_id bigint generated always as identity primary key,
    legal_name text not null,
    display_name text not null,
    country_code text not null,
    issuer_type text not null,
    created_at timestamptz not null default now()
);

create table if not exists ref.instrument (
    instrument_id bigint generated always as identity primary key,
    issuer_id bigint not null references ref.issuer (issuer_id),
    exchange_id bigint not null references ref.exchange (exchange_id),
    market_code text not null references ref.market (market_code),
    primary_symbol text not null,
    instrument_type text not null,
    currency_code text not null,
    name text not null,
    is_active boolean not null default true,
    listed_at timestamptz,
    delisted_at timestamptz,
    check (delisted_at is null or listed_at is null or delisted_at >= listed_at),
    unique (exchange_id, primary_symbol)
);

create table if not exists ref.classification_node (
    node_id bigint generated always as identity primary key,
    taxonomy_family text not null,
    node_type text not null,
    code text not null,
    name text not null,
    description text,
    status text not null default 'active',
    unique (taxonomy_family, node_type, code)
);

create table if not exists ref.classification_edge (
    edge_id bigint generated always as identity primary key,
    parent_node_id bigint not null references ref.classification_node (node_id) on delete cascade,
    child_node_id bigint not null references ref.classification_node (node_id) on delete cascade,
    relation_type text not null,
    weight numeric(10,4),
    valid_from date not null,
    valid_to date,
    check (valid_to is null or valid_to >= valid_from),
    check (parent_node_id <> child_node_id),
    unique (parent_node_id, child_node_id, relation_type, valid_from)
);

create table if not exists ingest.data_source (
    data_source_id bigint generated always as identity primary key,
    source_name text not null unique,
    source_kind text not null,
    base_url text,
    license_type text,
    trust_score numeric(5,4),
    is_active boolean not null default true,
    check (trust_score is null or (trust_score >= 0 and trust_score <= 1))
);

create table if not exists ingest.source_document (
    document_id bigint generated always as identity primary key,
    data_source_id bigint not null references ingest.data_source (data_source_id),
    external_document_id text,
    document_type text not null,
    title text not null,
    summary text,
    url text,
    language text,
    published_at timestamptz,
    ingested_at timestamptz not null default now(),
    raw_storage_uri text,
    checksum text,
    ingested_by_run_id bigint references ops.pipeline_run (run_id)
);

create table if not exists ref.instrument_classification_membership (
    membership_id bigint generated always as identity primary key,
    instrument_id bigint not null references ref.instrument (instrument_id) on delete cascade,
    node_id bigint not null references ref.classification_node (node_id) on delete cascade,
    membership_type text not null,
    confidence numeric(5,4),
    source_document_id bigint references ingest.source_document (document_id) on delete set null,
    valid_from date not null,
    valid_to date,
    check (valid_to is null or valid_to >= valid_from),
    check (confidence is null or (confidence >= 0 and confidence <= 1))
);

create table if not exists market.daily_price_bar (
    instrument_id bigint not null references ref.instrument (instrument_id),
    trade_date date not null,
    open numeric(18,6) not null,
    high numeric(18,6) not null,
    low numeric(18,6) not null,
    close numeric(18,6) not null,
    adjusted_close numeric(18,6) not null,
    volume bigint not null,
    turnover_value numeric(20,2),
    market_cap numeric(20,2),
    source_run_id bigint references ops.pipeline_run (run_id),
    created_at timestamptz not null default now(),
    primary key (instrument_id, trade_date),
    check (volume >= 0),
    check (high >= low),
    check (high >= open and high >= close and high >= adjusted_close),
    check (low <= open and low <= close and low <= adjusted_close)
);

create table if not exists market.financial_statement_period (
    period_id bigint generated always as identity primary key,
    instrument_id bigint not null references ref.instrument (instrument_id),
    statement_scope text not null,
    fiscal_year integer not null,
    fiscal_quarter smallint,
    period_start date not null,
    period_end date not null,
    report_date date,
    currency_code text not null,
    is_audited boolean not null default false,
    source_document_id bigint references ingest.source_document (document_id) on delete set null,
    source_run_id bigint references ops.pipeline_run (run_id),
    check (fiscal_quarter is null or fiscal_quarter between 1 and 4),
    check (period_end >= period_start),
    unique (instrument_id, statement_scope, period_end)
);

create table if not exists market.financial_metric_value (
    period_id bigint not null references market.financial_statement_period (period_id) on delete cascade,
    metric_code text not null,
    metric_value numeric(24,6) not null,
    unit text not null,
    source_run_id bigint references ops.pipeline_run (run_id),
    primary key (period_id, metric_code)
);

create table if not exists market.estimate_snapshot (
    estimate_snapshot_id bigint generated always as identity primary key,
    instrument_id bigint not null references ref.instrument (instrument_id),
    as_of_date date not null,
    fiscal_year integer not null,
    fiscal_quarter smallint,
    metric_code text not null,
    mean_value numeric(24,6),
    median_value numeric(24,6),
    high_value numeric(24,6),
    low_value numeric(24,6),
    analyst_count integer,
    source_run_id bigint references ops.pipeline_run (run_id),
    check (fiscal_quarter is null or fiscal_quarter between 1 and 4),
    check (analyst_count is null or analyst_count >= 0)
);

create table if not exists macro.series (
    series_id bigint generated always as identity primary key,
    series_code text not null unique,
    name text not null,
    category text not null,
    frequency text not null,
    unit text not null,
    region_code text not null,
    data_source_id bigint not null references ingest.data_source (data_source_id),
    is_active boolean not null default true
);

create table if not exists macro.observation (
    series_id bigint not null references macro.series (series_id) on delete cascade,
    observation_date date not null,
    value numeric(24,8) not null,
    released_at timestamptz,
    revision_number integer not null default 0,
    source_run_id bigint references ops.pipeline_run (run_id),
    primary key (series_id, observation_date, revision_number),
    check (revision_number >= 0)
);

create table if not exists event.event (
    event_id bigint generated always as identity primary key,
    event_type text not null,
    title text not null,
    summary text not null,
    event_at timestamptz not null,
    detected_at timestamptz not null default now(),
    time_horizon text,
    impact_polarity text,
    significance_score numeric(5,4),
    confidence numeric(5,4),
    dedupe_key text,
    created_by_run_id bigint references ops.pipeline_run (run_id),
    check (confidence is null or (confidence >= 0 and confidence <= 1))
);

create table if not exists event.event_document_link (
    event_id bigint not null references event.event (event_id) on delete cascade,
    document_id bigint not null references ingest.source_document (document_id) on delete cascade,
    link_type text not null,
    primary key (event_id, document_id, link_type)
);

create table if not exists event.event_instrument_impact (
    event_id bigint not null references event.event (event_id) on delete cascade,
    instrument_id bigint not null references ref.instrument (instrument_id) on delete cascade,
    impact_direction text not null,
    impact_strength numeric(5,4),
    confidence numeric(5,4),
    rationale text,
    primary key (event_id, instrument_id),
    check (confidence is null or (confidence >= 0 and confidence <= 1))
);

create table if not exists event.event_classification_impact (
    event_id bigint not null references event.event (event_id) on delete cascade,
    node_id bigint not null references ref.classification_node (node_id) on delete cascade,
    impact_direction text not null,
    impact_strength numeric(5,4),
    confidence numeric(5,4),
    rationale text,
    primary key (event_id, node_id),
    check (confidence is null or (confidence >= 0 and confidence <= 1))
);

create table if not exists signal.cycle_state_snapshot (
    node_id bigint not null references ref.classification_node (node_id) on delete cascade,
    as_of_date date not null,
    cycle_state text not null,
    cycle_score numeric(6,4) not null,
    trend_score numeric(6,4),
    earnings_revision_score numeric(6,4),
    liquidity_score numeric(6,4),
    valuation_score numeric(6,4),
    event_heat_score numeric(6,4),
    breadth_score numeric(6,4),
    source_run_id bigint references ops.pipeline_run (run_id),
    evidence_json jsonb,
    primary key (node_id, as_of_date)
);

create table if not exists signal.investment_thesis (
    thesis_id bigint generated always as identity primary key,
    instrument_id bigint not null references ref.instrument (instrument_id),
    primary_node_id bigint references ref.classification_node (node_id),
    thesis_type text not null,
    title text not null,
    summary text not null,
    status text not null,
    conviction_score numeric(6,4),
    expected_holding_days integer,
    benchmark_code text,
    entry_conditions text,
    invalidation_conditions text not null,
    exit_conditions text,
    created_at timestamptz not null default now(),
    closed_at timestamptz,
    created_by_run_id bigint references ops.pipeline_run (run_id),
    check (closed_at is null or closed_at >= created_at),
    check (expected_holding_days is null or expected_holding_days > 0)
);

create table if not exists signal.recommendation_batch (
    batch_id bigint generated always as identity primary key,
    as_of_date date not null,
    market_code text not null references ref.market (market_code),
    strategy_name text not null,
    horizon_type text not null,
    universe_version text,
    notes text,
    source_run_id bigint references ops.pipeline_run (run_id),
    created_at timestamptz not null default now()
);

create table if not exists signal.recommendation (
    recommendation_id bigint generated always as identity primary key,
    batch_id bigint not null references signal.recommendation_batch (batch_id) on delete cascade,
    instrument_id bigint not null references ref.instrument (instrument_id),
    thesis_id bigint references signal.investment_thesis (thesis_id) on delete set null,
    bucket text not null,
    action text not null,
    rank_position integer not null,
    total_score numeric(8,4) not null,
    recommended_weight numeric(8,4),
    status text not null default 'active',
    check (rank_position > 0)
);

create table if not exists portfolio.portfolio (
    portfolio_id bigint generated always as identity primary key,
    portfolio_name text not null unique,
    base_currency text not null,
    market_code text not null references ref.market (market_code),
    strategy_name text not null,
    is_paper boolean not null default true,
    created_at timestamptz not null default now()
);

create table if not exists portfolio.position_snapshot (
    portfolio_id bigint not null references portfolio.portfolio (portfolio_id) on delete cascade,
    instrument_id bigint not null references ref.instrument (instrument_id),
    snapshot_date date not null,
    quantity numeric(24,8) not null,
    cost_basis numeric(20,6),
    market_price numeric(18,6) not null,
    market_value numeric(20,2) not null,
    weight numeric(8,4),
    unrealized_pnl numeric(20,2),
    linked_thesis_id bigint references signal.investment_thesis (thesis_id) on delete set null,
    source_run_id bigint references ops.pipeline_run (run_id),
    primary key (portfolio_id, instrument_id, snapshot_date)
);
