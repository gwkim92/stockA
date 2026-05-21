with exposure_seed (symbol, node_code, exposure_weight, sensitivity_direction, confidence, rationale) as (
    values
        ('SPY', 'MACRO_RATES_FED', 0.6500::numeric, 'negative', 0.7500::numeric, 'Broad US equities usually de-rate when rate expectations rise.'),
        ('QQQ', 'MACRO_RATES_FED', 0.7500::numeric, 'negative', 0.7800::numeric, 'Long-duration growth and technology exposure is sensitive to discount-rate shocks.'),
        ('TLT', 'MACRO_RATES_FED', 0.9000::numeric, 'negative', 0.8500::numeric, 'Long-duration Treasury ETF is directly sensitive to higher rate expectations.'),
        ('XLF', 'MACRO_RATES_FED', 0.5500::numeric, 'mixed', 0.6000::numeric, 'Financials can benefit from rates but are vulnerable to curve and credit stress.'),
        ('SPY', 'US_MARKET_BREADTH', 0.8000::numeric, 'positive', 0.7500::numeric, 'Broad market ETF maps directly to US market breadth.'),
        ('QQQ', 'US_MARKET_BREADTH', 0.8000::numeric, 'positive', 0.7500::numeric, 'Growth-heavy market ETF tends to follow broad risk appetite.'),
        ('TSLA', 'US_MARKET_BREADTH', 0.5500::numeric, 'positive', 0.6000::numeric, 'High-beta equity tends to be sensitive to broad market risk appetite.'),
        ('XLE', 'ENERGY_GEOPOLITICS', 0.8000::numeric, 'positive', 0.8000::numeric, 'Energy sector ETF benefits from oil supply/geopolitical shock pricing.'),
        ('XOM', 'ENERGY_GEOPOLITICS', 0.7500::numeric, 'positive', 0.8000::numeric, 'Integrated energy major has positive oil-price and geopolitical risk exposure.'),
        ('NVDA', 'AI_SEMICONDUCTOR_CYCLE', 0.9000::numeric, 'positive', 0.8500::numeric, 'GPU leader is highly exposed to AI semiconductor capex cycles.'),
        ('MSFT', 'AI_SEMICONDUCTOR_CYCLE', 0.6500::numeric, 'positive', 0.7000::numeric, 'Cloud and AI platform demand links Microsoft to AI infrastructure cycles.')
),
resolved as (
    select
        instrument.instrument_id,
        node.node_id,
        exposure_seed.exposure_weight,
        exposure_seed.sensitivity_direction,
        exposure_seed.confidence,
        exposure_seed.rationale
    from exposure_seed
    join ref.instrument instrument
      on upper(instrument.primary_symbol) = exposure_seed.symbol
     and instrument.is_active
    join ref.classification_node node
      on node.taxonomy_family = 'internal_theme'
     and node.code = exposure_seed.node_code
)
insert into ref.instrument_factor_exposure (
    instrument_id,
    node_id,
    exposure_type,
    exposure_weight,
    sensitivity_direction,
    confidence,
    rationale,
    valid_from
)
select
    instrument_id,
    node_id,
    'macro_sensitivity',
    exposure_weight,
    sensitivity_direction,
    confidence,
    rationale,
    date '2024-01-01'
from resolved
on conflict (instrument_id, node_id, exposure_type, valid_from) do update
set
    exposure_weight = excluded.exposure_weight,
    sensitivity_direction = excluded.sensitivity_direction,
    confidence = excluded.confidence,
    rationale = excluded.rationale,
    valid_to = null,
    updated_at = now();
