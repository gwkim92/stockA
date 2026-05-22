create table if not exists portfolio.allocation_policy (
    allocation_policy_id bigint generated always as identity primary key,
    portfolio_id bigint references portfolio.portfolio (portfolio_id) on delete cascade,
    strategy_name text,
    policy_name text not null,
    status text not null default 'active',
    max_single_position_weight numeric(8,4) not null default 0.2500,
    min_rebalance_target_weight numeric(8,4) not null default 0.1000,
    valid_from date not null default date '2024-01-01',
    valid_to date,
    rationale text,
    source_run_id bigint references ops.pipeline_run (run_id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (status in ('active', 'inactive', 'retired')),
    check (max_single_position_weight > 0 and max_single_position_weight <= 1),
    check (min_rebalance_target_weight > 0 and min_rebalance_target_weight <= 1),
    check (valid_to is null or valid_to >= valid_from)
);

create unique index if not exists allocation_policy_identity_uidx
    on portfolio.allocation_policy (
        coalesce(portfolio_id, 0),
        coalesce(strategy_name, '__global__'),
        policy_name,
        valid_from
    );

create index if not exists allocation_policy_portfolio_strategy_idx
    on portfolio.allocation_policy (portfolio_id, strategy_name, status, valid_from, valid_to);

create index if not exists allocation_policy_status_idx
    on portfolio.allocation_policy (status);

insert into portfolio.allocation_policy (
    portfolio_id,
    strategy_name,
    policy_name,
    status,
    max_single_position_weight,
    min_rebalance_target_weight,
    valid_from,
    rationale
)
select
    null::bigint,
    null::text,
    'global_default_long_term_guardrail',
    'active',
    0.2500,
    0.1000,
    date '2024-01-01',
    'Default review-only guardrail: signal weights are not rebalance targets below 10%, and single-name exposure above 25% requires human review.'
where not exists (
    select 1
    from portfolio.allocation_policy policy
    where policy.portfolio_id is null
      and policy.strategy_name is null
      and policy.policy_name = 'global_default_long_term_guardrail'
      and policy.valid_from = date '2024-01-01'
);
