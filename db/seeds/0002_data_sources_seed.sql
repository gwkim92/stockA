insert into ingest.data_source (
    source_name,
    source_kind,
    base_url,
    license_type,
    trust_score,
    is_active
)
values
    ('manual_bootstrap', 'manual', null, 'internal', 1.0000, true),
    ('manual_research', 'manual', null, 'internal', 0.9000, true),
    ('fred', 'macro', 'https://fred.stlouisfed.org/', 'public', 0.9800, true),
    ('sec_edgar', 'filings', 'https://www.sec.gov/edgar', 'public', 0.9900, true),
    ('sec_companyfacts', 'filings', 'https://data.sec.gov/api/xbrl/companyfacts/', 'public', 0.9900, true),
    ('alpha_vantage', 'market_data', 'https://www.alphavantage.co/', 'public', 0.8500, true)
on conflict (source_name) do update
set
    source_kind = excluded.source_kind,
    base_url = excluded.base_url,
    license_type = excluded.license_type,
    trust_score = excluded.trust_score,
    is_active = excluded.is_active;
