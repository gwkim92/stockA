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
    ('internal_theme', 'sector', 'BROAD_US_EQUITY', 'Broad US Equity', 'Broad US equity market beta and index exposure used for portfolio concentration review.', 'active'),
    ('internal_theme', 'sector', 'TECHNOLOGY', 'Technology', 'Software, semiconductors, AI infrastructure, cloud, and advanced computing exposure.', 'active'),
    ('internal_theme', 'sector', 'CONSUMER_DISCRETIONARY', 'Consumer Discretionary', 'Consumer cyclicals, autos, retail, e-commerce, and demand-sensitive discretionary exposure.', 'active'),
    ('internal_theme', 'sector', 'ENERGY', 'Energy', 'Integrated energy, exploration, production, energy services, and energy sector ETF exposure.', 'active'),
    ('internal_theme', 'sector', 'FINANCIALS', 'Financials', 'Banks, diversified financials, insurance, and financial sector ETF exposure.', 'active'),
    ('internal_theme', 'sector', 'FIXED_INCOME', 'Fixed Income', 'Bond duration and rate-sensitive fixed income exposure.', 'active')
on conflict (taxonomy_family, node_type, code) do update
set
    name = excluded.name,
    description = excluded.description,
    status = excluded.status;

with edge_seed(parent_code, child_code, relation_type, weight) as (
    values
        ('MARKET_NEWS_FLOW', 'BROAD_US_EQUITY', 'domain_to_sector', 0.9000::numeric),
        ('TECH_DOMAIN', 'TECHNOLOGY', 'domain_to_sector', 0.9500::numeric),
        ('ENERGY_DOMAIN', 'ENERGY', 'domain_to_sector', 0.9500::numeric),
        ('MACRO_RATES_FED', 'FINANCIALS', 'macro_to_sector', 0.7000::numeric),
        ('MACRO_RATES_FED', 'FIXED_INCOME', 'macro_to_sector', 0.9500::numeric),
        ('MACRO_GROWTH', 'CONSUMER_DISCRETIONARY', 'macro_to_sector', 0.7000::numeric),
        ('TECHNOLOGY', 'AI_SEMICONDUCTOR_CYCLE', 'sector_to_theme', 0.9000::numeric),
        ('TECHNOLOGY', 'QUANTUM_COMPUTING_POLICY', 'sector_to_theme', 0.7000::numeric),
        ('ENERGY', 'ENERGY_GEOPOLITICS', 'sector_to_theme', 0.9000::numeric),
        ('BROAD_US_EQUITY', 'US_MARKET_BREADTH', 'sector_to_theme', 0.8500::numeric)
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
    date '2024-01-01',
    null::date
from resolved_edges
on conflict (parent_node_id, child_node_id, relation_type, valid_from) do update
set
    weight = excluded.weight,
    valid_to = excluded.valid_to;

with instrument_seed (symbol, name, issuer_display_name, mic_code, instrument_type, currency_code, market_code) as (
    values
        ('AAPL', 'Apple Inc.', 'Apple Inc.', 'XNAS', 'equity', 'USD', 'US'),
        ('BABA', 'Alibaba Group Holding Limited', 'Alibaba Group Holding Limited', 'XNYS', 'equity', 'USD', 'US')
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

delete from ref.instrument_classification_membership membership
using ref.instrument instrument, ref.classification_node node
where membership.instrument_id = instrument.instrument_id
  and membership.node_id = node.node_id
  and membership.membership_type = 'sector_membership'
  and node.taxonomy_family = 'internal_theme'
  and node.node_type = 'sector'
  and upper(instrument.primary_symbol) in (
      'AAPL',
      'MSFT',
      'NVDA',
      'TSLA',
      'XOM',
      'SPY',
      'QQQ',
      'TLT',
      'XLF',
      'XLE',
      'QUBT',
      'BABA'
  );

with sector_membership_seed(symbol, sector_code, confidence, rationale) as (
    values
        ('AAPL', 'TECHNOLOGY', 0.9000::numeric, 'Apple is treated as technology hardware and ecosystem exposure for portfolio concentration review.'),
        ('MSFT', 'TECHNOLOGY', 0.9000::numeric, 'Microsoft is core software, cloud, and AI platform technology exposure.'),
        ('NVDA', 'TECHNOLOGY', 0.9500::numeric, 'NVIDIA is core semiconductor and AI infrastructure technology exposure.'),
        ('QUBT', 'TECHNOLOGY', 0.8500::numeric, 'Quantum Computing Inc. is advanced computing and quantum technology exposure.'),
        ('TSLA', 'CONSUMER_DISCRETIONARY', 0.7500::numeric, 'Tesla is classified as consumer discretionary autos while retaining technology theme exposure separately.'),
        ('BABA', 'CONSUMER_DISCRETIONARY', 0.7000::numeric, 'Alibaba ADR is treated as e-commerce and consumer internet exposure for portfolio risk grouping.'),
        ('XOM', 'ENERGY', 0.9500::numeric, 'Exxon Mobil is integrated energy exposure.'),
        ('XLE', 'ENERGY', 0.9500::numeric, 'XLE is the Energy Select Sector ETF.'),
        ('XLF', 'FINANCIALS', 0.9500::numeric, 'XLF is the Financial Select Sector ETF.'),
        ('TLT', 'FIXED_INCOME', 0.9500::numeric, 'TLT is long-duration Treasury fixed income exposure.'),
        ('SPY', 'BROAD_US_EQUITY', 0.9000::numeric, 'SPY is broad US equity index exposure and should not be forced into a single operating sector.'),
        ('QQQ', 'TECHNOLOGY', 0.8000::numeric, 'QQQ is technology-heavy growth index exposure for concentration review.')
),
resolved_memberships as (
    select
        instrument.instrument_id,
        node.node_id,
        sector_membership_seed.confidence,
        sector_membership_seed.rationale
    from sector_membership_seed
    join ref.instrument instrument
      on upper(instrument.primary_symbol) = sector_membership_seed.symbol
     and instrument.is_active
    join ref.classification_node node
      on node.taxonomy_family = 'internal_theme'
     and node.node_type = 'sector'
     and node.code = sector_membership_seed.sector_code
)
insert into ref.instrument_classification_membership (
    instrument_id,
    node_id,
    membership_type,
    confidence,
    source_document_id,
    valid_from,
    valid_to
)
select
    instrument_id,
    node_id,
    'sector_membership',
    confidence,
    null::bigint,
    date '2024-01-01',
    null::date
from resolved_memberships;

commit;
