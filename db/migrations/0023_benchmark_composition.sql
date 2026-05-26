create table if not exists ref.benchmark_composition (
    benchmark_composition_id bigint generated always as identity primary key,
    benchmark_code text not null,
    component_instrument_id bigint not null references ref.instrument (instrument_id) on delete cascade,
    target_weight numeric(12,8) not null,
    source_type text not null,
    source_name text not null,
    source_as_of_date date not null,
    valid_from date not null,
    valid_to date,
    confidence numeric(5,4) not null default 0.5000,
    rationale text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (target_weight >= 0 and target_weight <= 1),
    check (confidence >= 0 and confidence <= 1),
    check (valid_to is null or valid_to >= valid_from),
    check (source_type in ('manual_seed', 'provider_file', 'operator_upload'))
);

create unique index if not exists benchmark_composition_identity_uidx
    on ref.benchmark_composition (
        benchmark_code,
        component_instrument_id,
        source_type,
        source_name,
        source_as_of_date,
        valid_from
    );

create index if not exists benchmark_composition_benchmark_date_idx
    on ref.benchmark_composition (benchmark_code, valid_from desc, valid_to, source_as_of_date desc);

create index if not exists benchmark_composition_component_idx
    on ref.benchmark_composition (component_instrument_id, benchmark_code);
