begin;

insert into ref.classification_node (
    taxonomy_family,
    node_type,
    code,
    name,
    description,
    status
)
values
    ('internal_theme', 'theme', 'MARKET_NEWS_FLOW', 'Market News Flow', 'Credential-free news flow used as an early warning layer before AI enrichment.', 'active'),
    ('internal_theme', 'subtheme', 'US_MARKET_BREADTH', 'US Market Breadth', 'Broad US equity index, breadth, futures, and risk appetite news.', 'active'),
    ('internal_theme', 'subtheme', 'MACRO_RATES_FED', 'Macro Rates and Fed', 'Rates, inflation, Treasury market, Fed credibility, and policy path news.', 'active'),
    ('internal_theme', 'macro_regime', 'MACRO_INFLATION', 'Macro Inflation Regime', 'Inflation pressure, disinflation, price expectations, and real-rate stress regime.', 'active'),
    ('internal_theme', 'macro_regime', 'MACRO_LIQUIDITY', 'Macro Liquidity Regime', 'Liquidity, dollar, credit, money-market, and balance-sheet condition regime.', 'active'),
    ('internal_theme', 'macro_regime', 'MACRO_GROWTH', 'Macro Growth Regime', 'Growth, employment, consumer demand, PMI, and recession/expansion regime.', 'active'),
    ('internal_theme', 'domain', 'TECH_DOMAIN', 'Technology Domain', 'Software, semiconductor, AI infrastructure, cloud, automation, and advanced computing domain.', 'active'),
    ('internal_theme', 'domain', 'ENERGY_DOMAIN', 'Energy Domain', 'Energy producers, energy infrastructure, oil, gas, power, and commodity shock domain.', 'active'),
    ('internal_theme', 'subtheme', 'AI_SEMICONDUCTOR_CYCLE', 'AI Semiconductor Cycle', 'AI accelerator, semiconductor capex, GPU supply, and compute demand news.', 'active'),
    ('internal_theme', 'subtheme', 'QUANTUM_COMPUTING_POLICY', 'Quantum Computing Policy', 'Quantum computing equities, public funding, government stake policy, and quantum technology commercialization news.', 'active'),
    ('internal_theme', 'subtheme', 'ENERGY_GEOPOLITICS', 'Energy and Geopolitics', 'Oil, energy supply, commodity shock, and geopolitical risk news.', 'active')
on conflict (taxonomy_family, node_type, code) do update
set
    name = excluded.name,
    description = excluded.description,
    status = excluded.status;

with edge_seed(parent_code, child_code, relation_type, weight) as (
    values
        ('MARKET_NEWS_FLOW', 'US_MARKET_BREADTH', 'hierarchy', 1.0000::numeric),
        ('MARKET_NEWS_FLOW', 'MACRO_RATES_FED', 'hierarchy', 1.0000::numeric),
        ('MARKET_NEWS_FLOW', 'MACRO_INFLATION', 'hierarchy', 1.0000::numeric),
        ('MARKET_NEWS_FLOW', 'MACRO_LIQUIDITY', 'hierarchy', 1.0000::numeric),
        ('MARKET_NEWS_FLOW', 'MACRO_GROWTH', 'hierarchy', 1.0000::numeric),
        ('MARKET_NEWS_FLOW', 'TECH_DOMAIN', 'hierarchy', 1.0000::numeric),
        ('MARKET_NEWS_FLOW', 'ENERGY_DOMAIN', 'hierarchy', 1.0000::numeric),
        ('MACRO_RATES_FED', 'TECH_DOMAIN', 'macro_to_domain', 0.7500::numeric),
        ('MACRO_LIQUIDITY', 'TECH_DOMAIN', 'macro_to_domain', 0.8000::numeric),
        ('MACRO_GROWTH', 'TECH_DOMAIN', 'macro_to_domain', 0.6000::numeric),
        ('MACRO_INFLATION', 'ENERGY_DOMAIN', 'macro_to_domain', 0.6500::numeric),
        ('TECH_DOMAIN', 'AI_SEMICONDUCTOR_CYCLE', 'domain_to_theme', 0.9000::numeric),
        ('TECH_DOMAIN', 'QUANTUM_COMPUTING_POLICY', 'domain_to_theme', 0.7000::numeric),
        ('ENERGY_DOMAIN', 'ENERGY_GEOPOLITICS', 'domain_to_theme', 0.9000::numeric),
        ('MACRO_RATES_FED', 'AI_SEMICONDUCTOR_CYCLE', 'macro_to_theme', 0.5500::numeric),
        ('MACRO_LIQUIDITY', 'AI_SEMICONDUCTOR_CYCLE', 'macro_to_theme', 0.6000::numeric),
        ('MACRO_GROWTH', 'US_MARKET_BREADTH', 'macro_to_theme', 0.7000::numeric)
),
resolved_edges as (
    select
        parent.node_id as parent_node_id,
        child.node_id as child_node_id,
        edge_seed.relation_type,
        edge_seed.weight
    from edge_seed
    join ref.classification_node parent
      on parent.taxonomy_family = 'internal_theme'
     and parent.code = edge_seed.parent_code
    join ref.classification_node child
      on child.taxonomy_family = 'internal_theme'
     and child.code = edge_seed.child_code
)
insert into ref.classification_edge (
    parent_node_id,
    child_node_id,
    relation_type,
    weight,
    valid_from,
    valid_to
)
select
    parent_node_id,
    child_node_id,
    relation_type,
    weight,
    '2024-01-01'::date,
    null::date
from resolved_edges
on conflict (parent_node_id, child_node_id, relation_type, valid_from) do update
set
    weight = excluded.weight,
    valid_to = excluded.valid_to;

with instrument_seed (symbol, name, issuer_display_name, mic_code, instrument_type, currency_code, market_code) as (
    values
        ('QUBT', 'Quantum Computing Inc.', 'Quantum Computing Inc.', 'XNAS', 'equity', 'USD', 'US')
),
inserted_issuers as (
    insert into ref.issuer (
        legal_name,
        display_name,
        country_code,
        issuer_type
    )
    select
        seed.issuer_display_name,
        seed.issuer_display_name,
        'US',
        'corporate'
    from instrument_seed seed
    where not exists (
        select 1
        from ref.instrument instrument
        where upper(instrument.primary_symbol) = seed.symbol
    )
    returning issuer_id, display_name
),
resolved_issuers as (
    select
        seed.symbol,
        seed.name,
        seed.mic_code,
        seed.instrument_type,
        seed.currency_code,
        seed.market_code,
        coalesce(inserted.issuer_id, existing_issuer.issuer_id) as issuer_id
    from instrument_seed seed
    left join inserted_issuers inserted
      on inserted.display_name = seed.issuer_display_name
    left join lateral (
        select issuer_id
        from ref.issuer issuer
        where issuer.display_name = seed.issuer_display_name
        order by issuer.issuer_id desc
        limit 1
    ) existing_issuer on true
)
insert into ref.instrument (
    issuer_id,
    exchange_id,
    market_code,
    primary_symbol,
    instrument_type,
    currency_code,
    name,
    is_active
)
select
    issuer.issuer_id,
    exchange.exchange_id,
    issuer.market_code,
    issuer.symbol,
    issuer.instrument_type,
    issuer.currency_code,
    issuer.name,
    true
from resolved_issuers issuer
join ref.exchange exchange on exchange.mic_code = issuer.mic_code
where issuer.issuer_id is not null
on conflict (exchange_id, primary_symbol) do update
set
    market_code = excluded.market_code,
    instrument_type = excluded.instrument_type,
    currency_code = excluded.currency_code,
    name = excluded.name,
    is_active = excluded.is_active;

delete from ref.instrument_factor_exposure exposure
using ref.instrument instrument, ref.classification_node node
where exposure.instrument_id = instrument.instrument_id
  and exposure.node_id = node.node_id
  and upper(instrument.primary_symbol) = 'QUBT'
  and node.taxonomy_family = 'internal_theme'
  and node.code = 'QUANTUM_COMPUTING_POLICY'
  and exposure.exposure_type = 'macro_sensitivity'
  and exposure.source_document_id is null;

with exposure_seed (symbol, node_code, exposure_type, exposure_weight, sensitivity_direction, confidence, rationale) as (
    values
        ('SPY', 'MACRO_RATES_FED', 'macro_sensitivity', 0.6500::numeric, 'negative', 0.7500::numeric, 'Broad US equities usually de-rate when rate expectations rise.'),
        ('QQQ', 'MACRO_RATES_FED', 'macro_sensitivity', 0.7500::numeric, 'negative', 0.7800::numeric, 'Long-duration growth and technology exposure is sensitive to discount-rate shocks.'),
        ('TLT', 'MACRO_RATES_FED', 'macro_sensitivity', 0.9000::numeric, 'negative', 0.8500::numeric, 'Long-duration Treasury ETF is directly sensitive to higher rate expectations.'),
        ('XLF', 'MACRO_RATES_FED', 'macro_sensitivity', 0.5500::numeric, 'mixed', 0.6000::numeric, 'Financials can benefit from rates but are vulnerable to curve and credit stress.'),
        ('SPY', 'MACRO_GROWTH', 'macro_sensitivity', 0.7500::numeric, 'positive', 0.7200::numeric, 'Broad equity beta is directly exposed to growth and recession expectations.'),
        ('QQQ', 'MACRO_LIQUIDITY', 'macro_sensitivity', 0.8000::numeric, 'positive', 0.7800::numeric, 'Growth-heavy technology exposure benefits from easier liquidity and tighter credit spreads.'),
        ('TLT', 'MACRO_INFLATION', 'macro_sensitivity', 0.8000::numeric, 'negative', 0.7800::numeric, 'Long-duration bonds are vulnerable to renewed inflation pressure.'),
        ('XLE', 'MACRO_INFLATION', 'macro_sensitivity', 0.6000::numeric, 'positive', 0.6500::numeric, 'Energy equities can benefit when inflation is commodity-led.'),
        ('NVDA', 'TECH_DOMAIN', 'theme_membership', 0.8500::numeric, 'positive', 0.8200::numeric, 'NVIDIA is a core AI infrastructure and semiconductor-cycle exposure.'),
        ('MSFT', 'TECH_DOMAIN', 'theme_membership', 0.7000::numeric, 'positive', 0.7400::numeric, 'Microsoft is exposed to cloud, AI platform, and software demand cycles.'),
        ('TSLA', 'TECH_DOMAIN', 'theme_membership', 0.5500::numeric, 'positive', 0.6200::numeric, 'Tesla is a high-beta technology and automation-adjacent exposure.'),
        ('NVDA', 'AI_SEMICONDUCTOR_CYCLE', 'theme_membership', 0.9000::numeric, 'positive', 0.8500::numeric, 'GPU leader is highly exposed to AI semiconductor capex cycles.'),
        ('MSFT', 'AI_SEMICONDUCTOR_CYCLE', 'theme_membership', 0.6500::numeric, 'positive', 0.7000::numeric, 'Cloud and AI platform demand links Microsoft to AI infrastructure cycles.'),
        ('QUBT', 'QUANTUM_COMPUTING_POLICY', 'theme_membership', 0.9000::numeric, 'positive', 0.7600::numeric, 'Quantum Computing Inc. is directly exposed to quantum funding and commercialization headlines.'),
        ('XLE', 'ENERGY_DOMAIN', 'theme_membership', 0.8500::numeric, 'positive', 0.7800::numeric, 'Energy sector ETF is broad energy domain exposure.'),
        ('XOM', 'ENERGY_DOMAIN', 'theme_membership', 0.7500::numeric, 'positive', 0.7700::numeric, 'Integrated energy major is exposed to energy cycle and oil-price shocks.'),
        ('XLE', 'ENERGY_GEOPOLITICS', 'theme_membership', 0.8000::numeric, 'positive', 0.8000::numeric, 'Energy sector ETF benefits from oil supply and geopolitical shock pricing.'),
        ('XOM', 'ENERGY_GEOPOLITICS', 'theme_membership', 0.7500::numeric, 'positive', 0.8000::numeric, 'Integrated energy major has positive oil-price and geopolitical risk exposure.')
),
resolved_exposures as (
    select
        instrument.instrument_id,
        node.node_id,
        exposure_seed.exposure_type,
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
    exposure_type,
    exposure_weight,
    sensitivity_direction,
    confidence,
    rationale,
    '2024-01-01'::date
from resolved_exposures
on conflict (instrument_id, node_id, exposure_type, valid_from) do update
set
    exposure_weight = excluded.exposure_weight,
    sensitivity_direction = excluded.sensitivity_direction,
    confidence = excluded.confidence,
    rationale = excluded.rationale,
    valid_to = null,
    updated_at = now();

commit;
