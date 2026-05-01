create table if not exists signal.thesis_review (
    review_id bigint generated always as identity primary key,
    thesis_id bigint not null references signal.investment_thesis (thesis_id) on delete cascade,
    review_date date not null,
    review_source text not null,
    action text not null,
    health_score numeric(6,4),
    summary text not null,
    change_notes text,
    next_review_date date,
    source_run_id bigint references ops.pipeline_run (run_id),
    created_at timestamptz not null default now(),
    check (action in ('keep', 'add', 'reduce', 'exit', 'watch')),
    check (health_score is null or (health_score >= 0 and health_score <= 1)),
    check (next_review_date is null or next_review_date >= review_date)
);

create unique index if not exists thesis_review_identity_uidx
    on signal.thesis_review (thesis_id, review_date, review_source);

create index if not exists thesis_review_review_date_idx
    on signal.thesis_review (review_date desc);

create index if not exists thesis_review_source_run_id_idx
    on signal.thesis_review (source_run_id);
