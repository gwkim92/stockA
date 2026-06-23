create table if not exists market.fx_rate_snapshot (
    fx_rate_snapshot_id bigint generated always as identity primary key,
    provider text not null,
    base_currency text not null,
    quote_currency text not null,
    observed_at timestamptz not null default now(),
    valid_from timestamptz,
    valid_until timestamptz,
    rate numeric(24,8) not null,
    mid_rate numeric(24,8),
    basis_point numeric(16,8),
    rate_change_type text,
    source_run_id bigint references ops.pipeline_run (run_id),
    evidence_json jsonb not null default '{}'::jsonb,
    check (base_currency = upper(base_currency) and length(base_currency) = 3),
    check (quote_currency = upper(quote_currency) and length(quote_currency) = 3),
    check (base_currency <> quote_currency),
    check (rate > 0),
    check (mid_rate is null or mid_rate > 0),
    check (valid_until is null or valid_from is null or valid_until >= valid_from)
);

create unique index if not exists fx_rate_snapshot_provider_pair_valid_from_idx
    on market.fx_rate_snapshot (provider, base_currency, quote_currency, valid_from)
    where valid_from is not null;

create index if not exists fx_rate_snapshot_pair_observed_idx
    on market.fx_rate_snapshot (base_currency, quote_currency, observed_at desc);

alter table portfolio.position_snapshot
    add column if not exists native_currency_code text,
    add column if not exists market_price_native numeric(18,6),
    add column if not exists market_value_native numeric(20,2),
    add column if not exists cost_basis_native numeric(20,6),
    add column if not exists unrealized_pnl_native numeric(20,2),
    add column if not exists fx_rate_to_base numeric(24,8),
    add column if not exists fx_rate_snapshot_id bigint references market.fx_rate_snapshot (fx_rate_snapshot_id),
    add column if not exists currency_conversion_note text;

alter table portfolio.position_snapshot
    add constraint position_snapshot_native_currency_code_chk
    check (native_currency_code is null or (native_currency_code = upper(native_currency_code) and length(native_currency_code) = 3)) not valid;

alter table portfolio.position_snapshot
    add constraint position_snapshot_fx_rate_to_base_chk
    check (fx_rate_to_base is null or fx_rate_to_base > 0) not valid;

create index if not exists position_snapshot_fx_rate_snapshot_idx
    on portfolio.position_snapshot (fx_rate_snapshot_id)
    where fx_rate_snapshot_id is not null;
