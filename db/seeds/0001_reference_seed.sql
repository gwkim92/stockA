insert into ref.market (
    market_code,
    name,
    country_code,
    currency_code,
    timezone,
    is_active
)
values
    ('US', 'United States Equities', 'US', 'USD', 'America/New_York', true)
on conflict (market_code) do update
set
    name = excluded.name,
    country_code = excluded.country_code,
    currency_code = excluded.currency_code,
    timezone = excluded.timezone,
    is_active = excluded.is_active;

insert into ref.exchange (
    market_code,
    mic_code,
    name,
    timezone,
    is_primary
)
values
    ('US', 'XNAS', 'NASDAQ', 'America/New_York', true),
    ('US', 'XNYS', 'New York Stock Exchange', 'America/New_York', true),
    ('US', 'ARCX', 'NYSE Arca', 'America/New_York', false)
on conflict (mic_code) do update
set
    market_code = excluded.market_code,
    name = excluded.name,
    timezone = excluded.timezone,
    is_primary = excluded.is_primary;
