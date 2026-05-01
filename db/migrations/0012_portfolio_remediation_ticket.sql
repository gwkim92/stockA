create table if not exists portfolio.remediation_ticket (
    remediation_ticket_id bigint generated always as identity primary key,
    portfolio_review_id bigint not null references portfolio.review (portfolio_review_id) on delete cascade,
    instrument_id bigint not null references ref.instrument (instrument_id) on delete cascade,
    action text not null,
    remediation_type text not null,
    suggested_runner text not null,
    suggested_next_step text not null,
    status text not null default 'open',
    priority integer,
    risk_level text,
    health_score numeric(6,4),
    current_weight numeric(8,4),
    recommended_weight numeric(8,4),
    latest_reason text not null,
    source_run_id bigint references ops.pipeline_run (run_id),
    opened_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    last_seen_at timestamptz not null default now(),
    resolved_at timestamptz,
    check (status in ('open', 'in_progress', 'resolved', 'ignored')),
    check (priority is null or priority > 0),
    check (health_score is null or (health_score >= 0 and health_score <= 1)),
    check (current_weight is null or (current_weight >= 0 and current_weight <= 1)),
    check (recommended_weight is null or (recommended_weight >= 0 and recommended_weight <= 1)),
    check ((status in ('resolved', 'ignored') and resolved_at is not null) or (status not in ('resolved', 'ignored')))
);

create unique index if not exists remediation_ticket_identity_uidx
    on portfolio.remediation_ticket (portfolio_review_id, instrument_id, action, remediation_type);

create index if not exists remediation_ticket_status_idx
    on portfolio.remediation_ticket (status);

create index if not exists remediation_ticket_type_idx
    on portfolio.remediation_ticket (remediation_type);

create index if not exists remediation_ticket_action_idx
    on portfolio.remediation_ticket (action);

create index if not exists remediation_ticket_instrument_id_idx
    on portfolio.remediation_ticket (instrument_id);

create index if not exists remediation_ticket_source_run_id_idx
    on portfolio.remediation_ticket (source_run_id);
