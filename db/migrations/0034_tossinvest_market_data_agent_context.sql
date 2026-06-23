alter table market.daily_price_bar
    add column if not exists provider text not null default 'unknown';

create index if not exists daily_price_bar_provider_trade_date_idx
    on market.daily_price_bar (provider, trade_date desc);

create table if not exists market.tossinvest_daily_candle_snapshot (
    tossinvest_daily_candle_snapshot_id bigint generated always as identity primary key,
    provider text not null default 'tossinvest',
    instrument_id bigint references ref.instrument (instrument_id),
    symbol text not null,
    market_code text not null,
    currency_code text not null,
    trade_date date not null,
    open numeric(18,6) not null,
    high numeric(18,6) not null,
    low numeric(18,6) not null,
    close numeric(18,6) not null,
    adjusted_close numeric(18,6) not null,
    volume bigint not null,
    source_run_id bigint references ops.pipeline_run (run_id),
    observed_at timestamptz not null default now(),
    evidence_json jsonb not null default '{}'::jsonb,
    check (provider = 'tossinvest'),
    check (symbol = upper(symbol)),
    check (market_code = upper(market_code)),
    check (currency_code = upper(currency_code) and length(currency_code) = 3),
    check (volume >= 0),
    check (high >= low),
    check (high >= open and high >= close and high >= adjusted_close),
    check (low <= open and low <= close and low <= adjusted_close)
);

create unique index if not exists tossinvest_daily_candle_snapshot_symbol_date_idx
    on market.tossinvest_daily_candle_snapshot (provider, symbol, trade_date);

create index if not exists tossinvest_daily_candle_snapshot_instrument_date_idx
    on market.tossinvest_daily_candle_snapshot (instrument_id, trade_date desc)
    where instrument_id is not null;

create table if not exists market.tossinvest_market_calendar_snapshot (
    tossinvest_market_calendar_snapshot_id bigint generated always as identity primary key,
    provider text not null default 'tossinvest',
    market_code text not null,
    calendar_date date not null,
    is_open boolean not null default false,
    next_business_day date,
    source_run_id bigint references ops.pipeline_run (run_id),
    observed_at timestamptz not null default now(),
    evidence_json jsonb not null default '{}'::jsonb,
    check (provider = 'tossinvest'),
    check (market_code in ('KR', 'US'))
);

create unique index if not exists tossinvest_market_calendar_snapshot_market_date_idx
    on market.tossinvest_market_calendar_snapshot (provider, market_code, calendar_date);

create table if not exists market.tossinvest_stock_warning_snapshot (
    tossinvest_stock_warning_snapshot_id bigint generated always as identity primary key,
    provider text not null default 'tossinvest',
    instrument_id bigint references ref.instrument (instrument_id),
    symbol text not null,
    warning_status text not null,
    warning_count integer not null default 0,
    warning_types jsonb not null default '[]'::jsonb,
    source_run_id bigint references ops.pipeline_run (run_id),
    observed_at timestamptz not null default now(),
    evidence_json jsonb not null default '{}'::jsonb,
    check (provider = 'tossinvest'),
    check (symbol = upper(symbol)),
    check (warning_count >= 0)
);

create index if not exists tossinvest_stock_warning_snapshot_symbol_observed_idx
    on market.tossinvest_stock_warning_snapshot (symbol, observed_at desc);

create table if not exists market.tossinvest_market_microdata_snapshot (
    tossinvest_market_microdata_snapshot_id bigint generated always as identity primary key,
    provider text not null default 'tossinvest',
    instrument_id bigint references ref.instrument (instrument_id),
    symbol text not null,
    microdata_status text not null,
    currency_code text,
    best_bid_price numeric(18,6),
    best_ask_price numeric(18,6),
    latest_trade_price numeric(18,6),
    latest_trade_timestamp timestamptz,
    trade_count integer not null default 0,
    upper_limit_price numeric(18,6),
    lower_limit_price numeric(18,6),
    source_run_id bigint references ops.pipeline_run (run_id),
    observed_at timestamptz not null default now(),
    orderbook_json jsonb not null default '{}'::jsonb,
    trades_json jsonb not null default '{}'::jsonb,
    price_limits_json jsonb not null default '{}'::jsonb,
    check (provider = 'tossinvest'),
    check (symbol = upper(symbol)),
    check (currency_code is null or (currency_code = upper(currency_code) and length(currency_code) = 3)),
    check (trade_count >= 0)
);

create index if not exists tossinvest_market_microdata_snapshot_symbol_observed_idx
    on market.tossinvest_market_microdata_snapshot (symbol, observed_at desc);

create table if not exists market.tossinvest_provider_comparison_snapshot (
    tossinvest_provider_comparison_snapshot_id bigint generated always as identity primary key,
    provider text not null default 'tossinvest',
    instrument_id bigint references ref.instrument (instrument_id),
    symbol text not null,
    comparison_date date not null,
    canonical_provider text not null,
    compared_provider text not null default 'tossinvest',
    latest_canonical_trade_date date,
    latest_compared_trade_date date,
    matched_bar_count integer not null default 0,
    missing_canonical_count integer not null default 0,
    missing_compared_count integer not null default 0,
    max_close_diff_bps numeric(18,6),
    median_close_diff_bps numeric(18,6),
    status text not null,
    reason text not null default '',
    source_run_id bigint references ops.pipeline_run (run_id),
    observed_at timestamptz not null default now(),
    evidence_json jsonb not null default '{}'::jsonb,
    check (provider = 'tossinvest'),
    check (symbol = upper(symbol)),
    check (matched_bar_count >= 0),
    check (missing_canonical_count >= 0),
    check (missing_compared_count >= 0),
    check (status in ('missing', 'shadow_collecting', 'candidate_ready', 'conflict_review_required'))
);

create unique index if not exists tossinvest_provider_comparison_snapshot_symbol_date_idx
    on market.tossinvest_provider_comparison_snapshot (provider, symbol, comparison_date);
