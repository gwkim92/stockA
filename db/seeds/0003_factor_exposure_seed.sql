with instrument_seed (symbol, name, issuer_display_name, mic_code, instrument_type, currency_code, market_code) as (
    values
        ('SPY', 'SPDR S&P 500 ETF Trust', 'SPDR S&P 500 ETF Trust', 'ARCX', 'etf', 'USD', 'US'),
        ('QQQ', 'Invesco QQQ Trust', 'Invesco QQQ Trust', 'XNAS', 'etf', 'USD', 'US'),
        ('TLT', 'iShares 20+ Year Treasury Bond ETF', 'iShares 20+ Year Treasury Bond ETF', 'ARCX', 'etf', 'USD', 'US'),
        ('XLF', 'Financial Select Sector SPDR Fund', 'Financial Select Sector SPDR Fund', 'ARCX', 'etf', 'USD', 'US'),
        ('XLE', 'Energy Select Sector SPDR Fund', 'Energy Select Sector SPDR Fund', 'ARCX', 'etf', 'USD', 'US'),
        ('NVDA', 'NVIDIA Corporation', 'NVIDIA Corporation', 'XNAS', 'equity', 'USD', 'US'),
        ('MSFT', 'Microsoft Corporation', 'Microsoft Corporation', 'XNAS', 'equity', 'USD', 'US'),
        ('TSLA', 'Tesla, Inc.', 'Tesla, Inc.', 'XNAS', 'equity', 'USD', 'US'),
        ('XOM', 'Exxon Mobil Corporation', 'Exxon Mobil Corporation', 'XNYS', 'equity', 'USD', 'US')
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
        case when seed.instrument_type = 'etf' then 'fund' else 'corporate' end
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
),
instrument_upsert as (
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
        is_active = excluded.is_active
    returning instrument_id, primary_symbol
),
available_instruments as (
    select instrument_id, primary_symbol
    from instrument_upsert
    union all
    select instrument.instrument_id, instrument.primary_symbol
    from ref.instrument instrument
    join instrument_seed seed on upper(instrument.primary_symbol) = seed.symbol
    where instrument.is_active
      and not exists (
          select 1
          from instrument_upsert upserted
          where upper(upserted.primary_symbol) = upper(instrument.primary_symbol)
      )
),
exposure_seed (symbol, node_code, exposure_weight, sensitivity_direction, confidence, rationale) as (
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
    join available_instruments instrument
      on upper(instrument.primary_symbol) = exposure_seed.symbol
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
