create table if not exists signal.recommendation_score_component (
    recommendation_id bigint not null references signal.recommendation (recommendation_id) on delete cascade,
    component_name text not null,
    component_score numeric(8,4) not null,
    component_weight numeric(8,4),
    explanation text,
    created_at timestamptz not null default now(),
    primary key (recommendation_id, component_name),
    check (component_score >= 0 and component_score <= 1),
    check (component_weight is null or (component_weight >= 0 and component_weight <= 1))
);

create index if not exists recommendation_score_component_name_idx
    on signal.recommendation_score_component (component_name);

create index if not exists recommendation_score_component_score_idx
    on signal.recommendation_score_component (component_name, component_score desc);
