create schema if not exists trading;

create table if not exists trading.broker_boundary (
    broker_boundary_id bigint generated always as identity primary key,
    broker_code text not null,
    environment text not null,
    status text not null default 'not_configured',
    supports_order_preview boolean not null default true,
    supports_order_submit boolean not null default false,
    secret_ref text,
    notes text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (broker_code ~ '^[a-z0-9_:-]{2,80}$'),
    check (environment in ('paper', 'live')),
    check (status in ('not_configured', 'disabled', 'enabled')),
    check (secret_ref is null or length(secret_ref) <= 240)
);

create unique index if not exists broker_boundary_identity_uidx
    on trading.broker_boundary (broker_code, environment);

create index if not exists broker_boundary_status_idx
    on trading.broker_boundary (status);

create table if not exists trading.account_permission (
    account_permission_id bigint generated always as identity primary key,
    broker_boundary_id bigint not null references trading.broker_boundary (broker_boundary_id) on delete cascade,
    portfolio_id bigint references portfolio.portfolio (portfolio_id) on delete restrict,
    account_ref text not null,
    permission_scope text not null default 'read_only',
    status text not null default 'inactive',
    allowed_symbols text[] not null default '{}',
    max_order_notional numeric(18,2),
    max_daily_notional numeric(18,2),
    approved_by text,
    approved_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (permission_scope in ('read_only', 'paper_trade', 'live_trade')),
    check (status in ('inactive', 'active', 'revoked')),
    check (account_ref ~ '^[A-Za-z0-9_:.@/-]{3,160}$'),
    check (max_order_notional is null or max_order_notional > 0),
    check (max_daily_notional is null or max_daily_notional > 0),
    check ((status = 'active' and approved_at is not null) or status <> 'active')
);

create unique index if not exists account_permission_identity_uidx
    on trading.account_permission (broker_boundary_id, account_ref, permission_scope);

create index if not exists account_permission_portfolio_idx
    on trading.account_permission (portfolio_id);

create index if not exists account_permission_status_idx
    on trading.account_permission (status);

create table if not exists trading.order_limit_policy (
    order_limit_policy_id bigint generated always as identity primary key,
    portfolio_id bigint references portfolio.portfolio (portfolio_id) on delete cascade,
    policy_name text not null,
    status text not null default 'inactive',
    max_single_order_notional numeric(18,2) not null,
    max_daily_order_notional numeric(18,2) not null,
    max_single_order_weight_delta numeric(8,4) not null,
    max_post_trade_symbol_weight numeric(8,4) not null,
    min_cash_buffer_weight numeric(8,4) not null default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (status in ('inactive', 'active', 'retired')),
    check (max_single_order_notional > 0),
    check (max_daily_order_notional >= max_single_order_notional),
    check (max_single_order_weight_delta > 0 and max_single_order_weight_delta <= 1),
    check (max_post_trade_symbol_weight > 0 and max_post_trade_symbol_weight <= 1),
    check (min_cash_buffer_weight >= 0 and min_cash_buffer_weight <= 1)
);

create unique index if not exists order_limit_policy_identity_uidx
    on trading.order_limit_policy (portfolio_id, policy_name);

create index if not exists order_limit_policy_status_idx
    on trading.order_limit_policy (status);

create table if not exists trading.kill_switch_state (
    kill_switch_id bigint generated always as identity primary key,
    scope text not null,
    scope_ref text not null default 'global',
    is_engaged boolean not null default true,
    reason text not null,
    changed_by text not null,
    changed_at timestamptz not null default now(),
    check (scope in ('global', 'broker', 'account', 'portfolio', 'symbol')),
    check (length(scope_ref) between 1 and 160),
    check (length(reason) between 3 and 500),
    check (length(changed_by) between 2 and 160)
);

create unique index if not exists kill_switch_scope_uidx
    on trading.kill_switch_state (scope, scope_ref);

create index if not exists kill_switch_engaged_idx
    on trading.kill_switch_state (is_engaged);

insert into trading.kill_switch_state (scope, scope_ref, is_engaged, reason, changed_by)
values ('global', 'global', true, 'default locked until explicit operator approval', 'migration-0013')
on conflict (scope, scope_ref) do nothing;

create table if not exists trading.paper_validation_run (
    paper_validation_run_id bigint generated always as identity primary key,
    portfolio_id bigint references portfolio.portfolio (portfolio_id) on delete cascade,
    validation_date date not null,
    status text not null,
    source_preview_hash text not null,
    recommendation_count integer not null default 0,
    conflict_count integer not null default 0,
    approved_action_count integer not null default 0,
    validated_symbols text[] not null default '{}',
    blocked_reasons jsonb not null default '[]'::jsonb,
    created_by text not null,
    created_at timestamptz not null default now(),
    check (status in ('missing', 'failed', 'passed', 'stale')),
    check (recommendation_count >= 0),
    check (conflict_count >= 0),
    check (approved_action_count >= 0),
    check (source_preview_hash ~ '^[A-Za-z0-9_:.@/-]{8,180}$'),
    check (length(created_by) between 2 and 160)
);

create index if not exists paper_validation_run_portfolio_date_idx
    on trading.paper_validation_run (portfolio_id, validation_date desc);

create index if not exists paper_validation_run_status_idx
    on trading.paper_validation_run (status);

create table if not exists trading.order_intent_audit (
    order_intent_audit_id bigint generated always as identity primary key,
    idempotency_key text not null,
    portfolio_id bigint references portfolio.portfolio (portfolio_id) on delete restrict,
    broker_boundary_id bigint references trading.broker_boundary (broker_boundary_id) on delete restrict,
    account_permission_id bigint references trading.account_permission (account_permission_id) on delete restrict,
    paper_validation_run_id bigint references trading.paper_validation_run (paper_validation_run_id) on delete restrict,
    symbol text not null,
    side text not null,
    order_type text not null,
    execution_mode text not null,
    quantity numeric(24,8) not null,
    estimated_price numeric(18,6) not null,
    estimated_notional numeric(18,2) not null,
    current_weight numeric(8,4),
    target_weight numeric(8,4),
    decision text not null,
    blocked_reasons jsonb not null default '[]'::jsonb,
    requires_human_approval boolean not null default true,
    human_approved boolean not null default false,
    submitted_to_broker boolean not null default false,
    request_snapshot jsonb not null,
    decision_snapshot jsonb not null,
    created_by text not null,
    created_at timestamptz not null default now(),
    check (idempotency_key ~ '^[A-Za-z0-9_:.@/-]{8,180}$'),
    check (symbol ~ '^[A-Z0-9.-]{1,20}$'),
    check (side in ('buy', 'sell')),
    check (order_type in ('market', 'limit')),
    check (execution_mode in ('paper', 'live')),
    check (quantity > 0),
    check (estimated_price > 0),
    check (estimated_notional > 0),
    check (current_weight is null or (current_weight >= 0 and current_weight <= 1)),
    check (target_weight is null or (target_weight >= 0 and target_weight <= 1)),
    check (decision in ('blocked', 'approved_for_paper', 'approved_for_live')),
    check ((submitted_to_broker = false) or (execution_mode = 'live' and decision = 'approved_for_live' and human_approved = true)),
    check (length(created_by) between 2 and 160)
);

create unique index if not exists order_intent_audit_idempotency_uidx
    on trading.order_intent_audit (idempotency_key);

create index if not exists order_intent_audit_symbol_idx
    on trading.order_intent_audit (symbol);

create index if not exists order_intent_audit_decision_idx
    on trading.order_intent_audit (decision);

create index if not exists order_intent_audit_created_at_idx
    on trading.order_intent_audit (created_at desc);
