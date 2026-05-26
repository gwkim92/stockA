begin;

with benchmark_seed(symbol, target_weight, rationale) as (
    values
        ('AAPL', 0.07000000::numeric, 'Manual MVP benchmark composition seed for portfolio drift smoke. Replace with dated provider holdings before production use.'),
        ('MSFT', 0.06500000::numeric, 'Manual MVP benchmark composition seed for portfolio drift smoke. Replace with dated provider holdings before production use.'),
        ('NVDA', 0.06500000::numeric, 'Manual MVP benchmark composition seed for portfolio drift smoke. Replace with dated provider holdings before production use.'),
        ('TSLA', 0.01500000::numeric, 'Manual MVP benchmark composition seed for portfolio drift smoke. Replace with dated provider holdings before production use.')
),
resolved_seed as (
    select
        instrument.instrument_id,
        benchmark_seed.target_weight,
        benchmark_seed.rationale
    from benchmark_seed
    join ref.instrument instrument
      on upper(instrument.primary_symbol) = benchmark_seed.symbol
     and instrument.is_active
)
insert into ref.benchmark_composition (
    benchmark_code,
    component_instrument_id,
    target_weight,
    source_type,
    source_name,
    source_as_of_date,
    valid_from,
    valid_to,
    confidence,
    rationale
)
select
    'SPY',
    instrument_id,
    target_weight,
    'manual_seed',
    'mvp_manual_spy_component_seed',
    date '2026-05-25',
    date '2024-01-01',
    null::date,
    0.5000::numeric,
    rationale
from resolved_seed
on conflict (
    benchmark_code,
    component_instrument_id,
    source_type,
    source_name,
    source_as_of_date,
    valid_from
) do update
set
    target_weight = excluded.target_weight,
    valid_to = excluded.valid_to,
    confidence = excluded.confidence,
    rationale = excluded.rationale,
    updated_at = now();

commit;
