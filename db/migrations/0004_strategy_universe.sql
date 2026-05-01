create table if not exists signal.strategy_universe_batch (
    universe_batch_id bigint generated always as identity primary key,
    as_of_date date not null,
    market_code text not null references ref.market (market_code),
    strategy_name text not null,
    horizon_type text not null,
    universe_version text not null,
    selection_rule text not null,
    source_run_id bigint references ops.pipeline_run (run_id),
    created_at timestamptz not null default now(),
    unique (as_of_date, market_code, strategy_name, horizon_type, universe_version)
);

create table if not exists signal.strategy_universe_member (
    universe_batch_id bigint not null references signal.strategy_universe_batch (universe_batch_id) on delete cascade,
    instrument_id bigint not null references ref.instrument (instrument_id),
    rank_position integer not null,
    selection_score numeric(10,4) not null,
    latest_trade_date date not null,
    latest_adjusted_close numeric(18,6) not null,
    observation_count integer not null,
    inclusion_reason text not null,
    primary key (universe_batch_id, instrument_id),
    check (rank_position > 0),
    check (observation_count >= 0)
);

create unique index if not exists strategy_universe_member_rank_uidx
    on signal.strategy_universe_member (universe_batch_id, rank_position);

create index if not exists strategy_universe_member_instrument_idx
    on signal.strategy_universe_member (instrument_id, universe_batch_id);

create index if not exists strategy_universe_batch_market_date_idx
    on signal.strategy_universe_batch (market_code, as_of_date desc, strategy_name, horizon_type);
