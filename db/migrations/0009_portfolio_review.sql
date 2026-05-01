create table if not exists portfolio.review (
    portfolio_review_id bigint generated always as identity primary key,
    portfolio_id bigint not null references portfolio.portfolio (portfolio_id) on delete cascade,
    review_date date not null,
    review_source text not null,
    overall_summary text not null,
    cash_weight numeric(8,4),
    risk_level text,
    source_run_id bigint references ops.pipeline_run (run_id),
    created_at timestamptz not null default now(),
    check (cash_weight is null or (cash_weight >= 0 and cash_weight <= 1))
);

create unique index if not exists portfolio_review_identity_uidx
    on portfolio.review (portfolio_id, review_date, review_source);

create index if not exists portfolio_review_review_date_idx
    on portfolio.review (review_date desc);

create index if not exists portfolio_review_source_run_id_idx
    on portfolio.review (source_run_id);

create table if not exists portfolio.review_item (
    review_item_id bigint generated always as identity primary key,
    portfolio_review_id bigint not null references portfolio.review (portfolio_review_id) on delete cascade,
    instrument_id bigint not null references ref.instrument (instrument_id),
    thesis_id bigint references signal.investment_thesis (thesis_id) on delete set null,
    recommendation_id bigint references signal.recommendation (recommendation_id) on delete set null,
    thesis_review_id bigint references signal.thesis_review (review_id) on delete set null,
    action text not null,
    reason text not null,
    priority integer,
    health_score numeric(6,4),
    current_weight numeric(8,4),
    recommended_weight numeric(8,4),
    weight_gap numeric(8,4),
    market_value numeric(20,2),
    unrealized_pnl numeric(20,2),
    created_at timestamptz not null default now(),
    check (priority is null or priority > 0),
    check (health_score is null or (health_score >= 0 and health_score <= 1)),
    check (current_weight is null or (current_weight >= 0 and current_weight <= 1)),
    check (recommended_weight is null or (recommended_weight >= 0 and recommended_weight <= 1))
);

create unique index if not exists portfolio_review_item_review_instrument_uidx
    on portfolio.review_item (portfolio_review_id, instrument_id);

create index if not exists portfolio_review_item_action_idx
    on portfolio.review_item (action);

create index if not exists portfolio_review_item_instrument_id_idx
    on portfolio.review_item (instrument_id);

create index if not exists portfolio_review_item_thesis_id_idx
    on portfolio.review_item (thesis_id);

create index if not exists portfolio_review_item_recommendation_id_idx
    on portfolio.review_item (recommendation_id);

create index if not exists portfolio_review_item_thesis_review_id_idx
    on portfolio.review_item (thesis_review_id);
