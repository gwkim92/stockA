from __future__ import annotations

import json
import time
from collections.abc import Callable
from csv import DictReader
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from io import StringIO
from typing import Any

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.http import execute_request
from stockanalysis.ingest.macro.sql import sql_date, sql_literal, sql_numeric
from stockanalysis.ingest.market.price import (
    MarketDailyPriceBarRecord,
    normalize_twelve_data_time_series_payload,
)
from stockanalysis.ingest.models import HttpRequest
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.ingest.registry import get_source
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


FREE_PROVIDER_REGISTRY_PIPELINE_NAME = "free_provider_capacity_registry"
CROSS_ASSET_INDICATOR_PROVIDER_FETCH_PIPELINE_NAME = "cross_asset_indicator_provider_fetch"
CROSS_ASSET_INDICATOR_INGEST_PIPELINE_NAME = "cross_asset_indicator_ingest"
CROSS_ASSET_REGIME_SNAPSHOT_PIPELINE_NAME = "cross_asset_regime_snapshot"
INDICATOR_NEWS_LINKAGE_PIPELINE_NAME = "indicator_news_linkage"
RECOMMENDATION_CROSS_ASSET_COMPONENTS_PIPELINE_NAME = "recommendation_cross_asset_components"

REGISTRY_VERSION = "free-provider-cross-asset-v1"
DEFAULT_LOOKBACK_DAYS = 2
DEFAULT_PROVIDER_FETCH_OUTPUTSIZE = "120"
DEFAULT_PROVIDER_FETCH_MAX_REQUESTS = 8
DEFAULT_PROVIDER_FETCH_THROTTLE_SECONDS = 8.0
XAG_USD_TWELVE_DATA_SYMBOL_CANDIDATES = ("XAG/USD", "XAGUSD", "SILVER")


@dataclass(frozen=True)
class MarketIndicatorDefinition:
    indicator_code: str
    display_name: str
    indicator_type: str
    preferred_provider: str
    fallback_provider: str | None = None
    provider_symbol: str | None = None
    fred_series_code: str | None = None
    instrument_symbol: str | None = None
    cboe_csv_url: str | None = None
    daily_budget_cost: Decimal = Decimal("0")
    freshness_sla_days: int = 3
    license_note: str = ""
    redistribution_allowed_note: str = ""
    stale_policy: str = "mark_stale_no_imputation"
    is_active: bool = True


@dataclass(frozen=True)
class MarketIndicatorSnapshotInput:
    indicator_code: str
    latest_observation_date: date | None
    latest_value: Decimal | None
    return_5d: Decimal | None
    return_20d: Decimal | None
    z_score_252d: Decimal | None
    shock_direction: str
    shock_magnitude: Decimal
    trend_state: str
    confidence: Decimal
    freshness_status: str


@dataclass(frozen=True)
class MarketIndicatorObservationInput:
    indicator_code: str
    observation_date: date
    provider: str
    source_kind: str
    value: Decimal
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    close: Decimal | None = None
    adjusted_close: Decimal | None = None
    volume: Decimal | None = None
    evidence_json: dict[str, Any] | None = None


@dataclass(frozen=True)
class CrossAssetRegimeOutput:
    regime_code: str
    regime_state: str
    regime_score: Decimal
    confidence: Decimal
    driver_indicator_codes: tuple[str, ...]
    conflict_flags: tuple[str, ...]
    evidence_json: dict[str, Any]


FRED_LICENSE_NOTE = "FRED public API. Cache metadata and do not impute missing values."
TWELVE_DATA_LICENSE_NOTE = "Twelve Data free tier. Keep 800/day hard cap and do not redistribute raw bulk feeds."
CBOE_LICENSE_NOTE = "CBOE official historical CSV. Use as market indicator evidence, not bulk redistribution."

CBOE_HISTORICAL_DATA_PAGE_URL = "https://www.cboe.com/tradable_products/vix/vix_historical_data"
CBOE_DAILY_PRICE_CSV_URLS = {
    "VIX9D": "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX9D_History.csv",
    "VVIX": "https://cdn.cboe.com/api/global/us_indices/daily_prices/VVIX_History.csv",
    "OVX": "https://cdn.cboe.com/api/global/us_indices/daily_prices/OVX_History.csv",
    "GVZ": "https://cdn.cboe.com/api/global/us_indices/daily_prices/GVZ_History.csv",
}


DEFAULT_MARKET_INDICATORS: tuple[MarketIndicatorDefinition, ...] = (
    MarketIndicatorDefinition(
        "US_2Y_YIELD",
        "미국 2년 국채 금리",
        "rates",
        "fred",
        fred_series_code="DGS2",
        provider_symbol="DGS2",
        freshness_sla_days=5,
        license_note=FRED_LICENSE_NOTE,
        redistribution_allowed_note="Show normalized indicators and attribution, not raw feed dumps.",
    ),
    MarketIndicatorDefinition(
        "US_10Y_YIELD",
        "미국 10년 국채 금리",
        "rates",
        "fred",
        fred_series_code="DGS10",
        provider_symbol="DGS10",
        freshness_sla_days=5,
        license_note=FRED_LICENSE_NOTE,
        redistribution_allowed_note="Show normalized indicators and attribution, not raw feed dumps.",
    ),
    MarketIndicatorDefinition(
        "US_10Y_REAL_YIELD",
        "미국 10년 실질금리",
        "real_rates",
        "fred",
        fred_series_code="DFII10",
        provider_symbol="DFII10",
        freshness_sla_days=5,
        license_note=FRED_LICENSE_NOTE,
        redistribution_allowed_note="Show normalized indicators and attribution, not raw feed dumps.",
    ),
    MarketIndicatorDefinition(
        "US_10Y_BREAKEVEN",
        "미국 10년 기대 인플레이션",
        "inflation_expectations",
        "fred",
        fred_series_code="T10YIE",
        provider_symbol="T10YIE",
        freshness_sla_days=5,
        license_note=FRED_LICENSE_NOTE,
        redistribution_allowed_note="Show normalized indicators and attribution, not raw feed dumps.",
    ),
    MarketIndicatorDefinition(
        "US_10Y_2Y_CURVE",
        "미국 10년-2년 금리차",
        "rates_curve",
        "fred",
        fred_series_code="T10Y2Y",
        provider_symbol="T10Y2Y",
        freshness_sla_days=5,
        license_note=FRED_LICENSE_NOTE,
        redistribution_allowed_note="Show normalized indicators and attribution, not raw feed dumps.",
    ),
    MarketIndicatorDefinition(
        "US_10Y_3M_CURVE",
        "미국 10년-3개월 금리차",
        "rates_curve",
        "fred",
        fred_series_code="T10Y3M",
        provider_symbol="T10Y3M",
        freshness_sla_days=5,
        license_note=FRED_LICENSE_NOTE,
        redistribution_allowed_note="Show normalized indicators and attribution, not raw feed dumps.",
    ),
    MarketIndicatorDefinition(
        "USD_BROAD_INDEX",
        "미국 달러 광의 지수",
        "dollar",
        "fred",
        fred_series_code="DTWEXBGS",
        provider_symbol="DTWEXBGS",
        freshness_sla_days=10,
        stale_policy="fred_lag_tolerant_no_imputation_weaken_dollar_regime_after_sla",
        license_note=FRED_LICENSE_NOTE,
        redistribution_allowed_note="Show normalized indicators and attribution, not raw feed dumps.",
    ),
    MarketIndicatorDefinition(
        "WTI_CRUDE",
        "WTI 원유",
        "commodity_energy",
        "fred",
        fallback_provider="twelve_data",
        fred_series_code="DCOILWTICO",
        provider_symbol="DCOILWTICO",
        daily_budget_cost=Decimal("0"),
        freshness_sla_days=5,
        license_note=FRED_LICENSE_NOTE,
        redistribution_allowed_note="Show normalized indicators and attribution, not raw feed dumps.",
    ),
    MarketIndicatorDefinition(
        "BRENT_CRUDE",
        "브렌트 원유",
        "commodity_energy",
        "fred",
        fallback_provider="twelve_data",
        fred_series_code="DCOILBRENTEU",
        provider_symbol="DCOILBRENTEU",
        freshness_sla_days=5,
        license_note=FRED_LICENSE_NOTE,
        redistribution_allowed_note="Show normalized indicators and attribution, not raw feed dumps.",
    ),
    MarketIndicatorDefinition(
        "HENRY_HUB_GAS",
        "Henry Hub 천연가스",
        "commodity_energy",
        "fred",
        fallback_provider="twelve_data",
        fred_series_code="DHHNGSP",
        provider_symbol="DHHNGSP",
        freshness_sla_days=5,
        license_note=FRED_LICENSE_NOTE,
        redistribution_allowed_note="Show normalized indicators and attribution, not raw feed dumps.",
    ),
    MarketIndicatorDefinition(
        "VIX",
        "VIX 변동성 지수",
        "volatility",
        "fred",
        fallback_provider="cboe_csv",
        fred_series_code="VIXCLS",
        provider_symbol="VIXCLS",
        freshness_sla_days=5,
        license_note=FRED_LICENSE_NOTE,
        redistribution_allowed_note="Show normalized indicators and attribution, not raw feed dumps.",
    ),
    MarketIndicatorDefinition(
        "US_HIGH_YIELD_SPREAD",
        "미국 하이일드 신용 스프레드",
        "credit",
        "fred",
        fred_series_code="BAMLH0A0HYM2",
        provider_symbol="BAMLH0A0HYM2",
        freshness_sla_days=5,
        license_note=FRED_LICENSE_NOTE,
        redistribution_allowed_note="Show normalized indicators and attribution, not raw feed dumps.",
    ),
    MarketIndicatorDefinition(
        "US_CORPORATE_SPREAD",
        "미국 회사채 신용 스프레드",
        "credit",
        "fred",
        fred_series_code="BAMLC0A0CM",
        provider_symbol="BAMLC0A0CM",
        freshness_sla_days=5,
        license_note=FRED_LICENSE_NOTE,
        redistribution_allowed_note="Show normalized indicators and attribution, not raw feed dumps.",
    ),
    MarketIndicatorDefinition(
        "SPY",
        "S&P 500 ETF",
        "equity_index",
        "twelve_data",
        instrument_symbol="SPY",
        provider_symbol="SPY",
        daily_budget_cost=Decimal("1"),
        freshness_sla_days=7,
        license_note=TWELVE_DATA_LICENSE_NOTE,
        redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution.",
    ),
    MarketIndicatorDefinition(
        "QQQ",
        "Nasdaq 100 ETF",
        "equity_index",
        "twelve_data",
        instrument_symbol="QQQ",
        provider_symbol="QQQ",
        daily_budget_cost=Decimal("1"),
        freshness_sla_days=7,
        license_note=TWELVE_DATA_LICENSE_NOTE,
        redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution.",
    ),
    MarketIndicatorDefinition(
        "IWM",
        "Russell 2000 ETF",
        "equity_index",
        "twelve_data",
        instrument_symbol="IWM",
        provider_symbol="IWM",
        daily_budget_cost=Decimal("1"),
        freshness_sla_days=7,
        license_note=TWELVE_DATA_LICENSE_NOTE,
        redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution.",
    ),
    MarketIndicatorDefinition(
        "DIA",
        "Dow Jones ETF",
        "equity_index",
        "twelve_data",
        instrument_symbol="DIA",
        provider_symbol="DIA",
        daily_budget_cost=Decimal("1"),
        freshness_sla_days=7,
        license_note=TWELVE_DATA_LICENSE_NOTE,
        redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution.",
    ),
    MarketIndicatorDefinition("XLK", "기술 섹터 ETF", "sector_etf", "twelve_data", instrument_symbol="XLK", provider_symbol="XLK", daily_budget_cost=Decimal("1"), freshness_sla_days=7, license_note=TWELVE_DATA_LICENSE_NOTE, redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution."),
    MarketIndicatorDefinition("XLF", "금융 섹터 ETF", "sector_etf", "twelve_data", instrument_symbol="XLF", provider_symbol="XLF", daily_budget_cost=Decimal("1"), freshness_sla_days=7, license_note=TWELVE_DATA_LICENSE_NOTE, redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution."),
    MarketIndicatorDefinition("XLE", "에너지 섹터 ETF", "sector_etf", "twelve_data", instrument_symbol="XLE", provider_symbol="XLE", daily_budget_cost=Decimal("1"), freshness_sla_days=7, license_note=TWELVE_DATA_LICENSE_NOTE, redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution."),
    MarketIndicatorDefinition("XLV", "헬스케어 섹터 ETF", "sector_etf", "twelve_data", instrument_symbol="XLV", provider_symbol="XLV", daily_budget_cost=Decimal("1"), freshness_sla_days=7, license_note=TWELVE_DATA_LICENSE_NOTE, redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution."),
    MarketIndicatorDefinition("XLI", "산업재 섹터 ETF", "sector_etf", "twelve_data", instrument_symbol="XLI", provider_symbol="XLI", daily_budget_cost=Decimal("1"), freshness_sla_days=7, license_note=TWELVE_DATA_LICENSE_NOTE, redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution."),
    MarketIndicatorDefinition("XLY", "임의소비재 섹터 ETF", "sector_etf", "twelve_data", instrument_symbol="XLY", provider_symbol="XLY", daily_budget_cost=Decimal("1"), freshness_sla_days=7, license_note=TWELVE_DATA_LICENSE_NOTE, redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution."),
    MarketIndicatorDefinition("XLP", "필수소비재 섹터 ETF", "sector_etf", "twelve_data", instrument_symbol="XLP", provider_symbol="XLP", daily_budget_cost=Decimal("1"), freshness_sla_days=7, license_note=TWELVE_DATA_LICENSE_NOTE, redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution."),
    MarketIndicatorDefinition("XLU", "유틸리티 섹터 ETF", "sector_etf", "twelve_data", instrument_symbol="XLU", provider_symbol="XLU", daily_budget_cost=Decimal("1"), freshness_sla_days=7, license_note=TWELVE_DATA_LICENSE_NOTE, redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution."),
    MarketIndicatorDefinition("XLB", "소재 섹터 ETF", "sector_etf", "twelve_data", instrument_symbol="XLB", provider_symbol="XLB", daily_budget_cost=Decimal("1"), freshness_sla_days=7, license_note=TWELVE_DATA_LICENSE_NOTE, redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution."),
    MarketIndicatorDefinition("XLC", "커뮤니케이션 섹터 ETF", "sector_etf", "twelve_data", instrument_symbol="XLC", provider_symbol="XLC", daily_budget_cost=Decimal("1"), freshness_sla_days=7, license_note=TWELVE_DATA_LICENSE_NOTE, redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution."),
    MarketIndicatorDefinition("XLRE", "부동산 섹터 ETF", "sector_etf", "twelve_data", instrument_symbol="XLRE", provider_symbol="XLRE", daily_budget_cost=Decimal("1"), freshness_sla_days=7, license_note=TWELVE_DATA_LICENSE_NOTE, redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution."),
    MarketIndicatorDefinition("TLT", "미국 장기국채 ETF", "rates_etf", "twelve_data", instrument_symbol="TLT", provider_symbol="TLT", daily_budget_cost=Decimal("1"), freshness_sla_days=7, license_note=TWELVE_DATA_LICENSE_NOTE, redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution."),
    MarketIndicatorDefinition("HYG", "하이일드 채권 ETF", "credit_etf", "twelve_data", instrument_symbol="HYG", provider_symbol="HYG", daily_budget_cost=Decimal("1"), freshness_sla_days=7, license_note=TWELVE_DATA_LICENSE_NOTE, redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution."),
    MarketIndicatorDefinition("LQD", "투자등급 회사채 ETF", "credit_etf", "twelve_data", instrument_symbol="LQD", provider_symbol="LQD", daily_budget_cost=Decimal("1"), freshness_sla_days=7, license_note=TWELVE_DATA_LICENSE_NOTE, redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution."),
    MarketIndicatorDefinition(
        "XAU_USD",
        "금 현물 달러",
        "precious_metals",
        "twelve_data",
        provider_symbol="XAU/USD",
        daily_budget_cost=Decimal("1"),
        freshness_sla_days=7,
        license_note=TWELVE_DATA_LICENSE_NOTE,
        redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution.",
    ),
    MarketIndicatorDefinition(
        "XAG_USD",
        "은 가격 프록시 지수",
        "precious_metals",
        "fred",
        provider_symbol="NASDAQQSLVO",
        fred_series_code="NASDAQQSLVO",
        daily_budget_cost=Decimal("1"),
        freshness_sla_days=7,
        license_note="FRED Nasdaq Daily Index Data. Silver proxy only; verify copyright before raw redistribution.",
        redistribution_allowed_note="Show normalized proxy indicators and attribution, not raw index dumps. Do not label as spot XAG/USD.",
    ),
    MarketIndicatorDefinition(
        "BTC_USD",
        "비트코인 달러",
        "crypto_liquidity",
        "twelve_data",
        provider_symbol="BTC/USD",
        daily_budget_cost=Decimal("1"),
        freshness_sla_days=3,
        license_note=TWELVE_DATA_LICENSE_NOTE,
        redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution.",
    ),
    MarketIndicatorDefinition(
        "ETH_USD",
        "이더리움 달러",
        "crypto_liquidity",
        "twelve_data",
        provider_symbol="ETH/USD",
        daily_budget_cost=Decimal("1"),
        freshness_sla_days=3,
        license_note=TWELVE_DATA_LICENSE_NOTE,
        redistribution_allowed_note="Show derived metrics and attribution. Avoid raw feed redistribution.",
    ),
    MarketIndicatorDefinition("VIX9D", "9일 VIX", "volatility", "cboe_csv", provider_symbol="VIX9D", cboe_csv_url=CBOE_DAILY_PRICE_CSV_URLS["VIX9D"], daily_budget_cost=Decimal("0"), freshness_sla_days=5, license_note=CBOE_LICENSE_NOTE, redistribution_allowed_note="Show normalized indicators and attribution, not raw CSV dumps."),
    MarketIndicatorDefinition("VVIX", "VVIX 변동성 지수", "volatility", "cboe_csv", provider_symbol="VVIX", cboe_csv_url=CBOE_DAILY_PRICE_CSV_URLS["VVIX"], daily_budget_cost=Decimal("0"), freshness_sla_days=5, license_note=CBOE_LICENSE_NOTE, redistribution_allowed_note="Show normalized indicators and attribution, not raw CSV dumps."),
    MarketIndicatorDefinition("OVX", "원유 변동성 지수", "volatility", "cboe_csv", provider_symbol="OVX", cboe_csv_url=CBOE_DAILY_PRICE_CSV_URLS["OVX"], daily_budget_cost=Decimal("0"), freshness_sla_days=5, license_note=CBOE_LICENSE_NOTE, redistribution_allowed_note="Show normalized indicators and attribution, not raw CSV dumps."),
    MarketIndicatorDefinition("GVZ", "금 변동성 지수", "volatility", "cboe_csv", provider_symbol="GVZ", cboe_csv_url=CBOE_DAILY_PRICE_CSV_URLS["GVZ"], daily_budget_cost=Decimal("0"), freshness_sla_days=5, license_note=CBOE_LICENSE_NOTE, redistribution_allowed_note="Show normalized indicators and attribution, not raw CSV dumps."),
)


NEWS_NODE_INDICATOR_MAP: tuple[tuple[str, str, str], ...] = (
    ("MACRO_RATES_FED", "US_10Y_YIELD", "news_with_indicator_shock"),
    ("MACRO_RATES_FED", "US_10Y_REAL_YIELD", "news_with_indicator_shock"),
    ("MACRO_INFLATION", "US_10Y_BREAKEVEN", "news_with_indicator_shock"),
    ("MACRO_LIQUIDITY", "USD_BROAD_INDEX", "news_with_indicator_shock"),
    ("MACRO_GROWTH", "SPY", "news_with_indicator_shock"),
    ("ENERGY_GEOPOLITICS", "WTI_CRUDE", "news_with_indicator_shock"),
    ("ENERGY_GEOPOLITICS", "BRENT_CRUDE", "news_with_indicator_shock"),
    ("ENERGY_GEOPOLITICS", "XLE", "news_with_indicator_shock"),
    ("TECH_DOMAIN", "QQQ", "news_with_indicator_shock"),
    ("AI_SEMICONDUCTOR_CYCLE", "QQQ", "news_with_indicator_shock"),
    ("QUANTUM_COMPUTING_POLICY", "QQQ", "news_with_indicator_shock"),
)


RECOMMENDATION_COMPONENT_NAMES: tuple[str, ...] = (
    "index_regime_score",
    "cross_asset_regime_score",
    "real_rate_duration_penalty",
    "usd_liquidity_pressure",
    "commodity_input_cost_score",
    "energy_shock_risk",
    "volatility_risk_penalty",
    "credit_stress_penalty",
)


def cross_asset_instrument_price_symbols(
    definitions: tuple[MarketIndicatorDefinition, ...] = DEFAULT_MARKET_INDICATORS,
) -> tuple[str, ...]:
    """Return registry-backed instruments that need price-bar refresh before indicator sync."""
    symbols: list[str] = []
    seen: set[str] = set()
    for definition in definitions:
        symbol = str(definition.instrument_symbol or "").strip().upper()
        if not symbol or symbol in seen:
            continue
        if definition.preferred_provider != "twelve_data":
            continue
        symbols.append(symbol)
        seen.add(symbol)
    return tuple(symbols)


def run_free_provider_capacity_registry(
    *,
    config: RuntimeConfig,
    execute: bool,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, Any]:
    report = _base_registry_report()
    if not execute:
        report["status"] = "planned"
        report["execute"] = False
        return report

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=FREE_PROVIDER_REGISTRY_PIPELINE_NAME,
        config_json={"registry_version": REGISTRY_VERSION},
    )
    try:
        sql_executor.execute_non_query(render_market_indicator_registry_upsert_sql(DEFAULT_MARKET_INDICATORS))
        sql_executor.execute_non_query(render_cross_asset_instrument_bootstrap_sql(DEFAULT_MARKET_INDICATORS))
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise
    report["status"] = "completed"
    report["execute"] = True
    report["run_id"] = run_id
    report["instrument_symbol_count"] = len(cross_asset_instrument_price_symbols())
    return report


def render_cross_asset_instrument_bootstrap_sql(
    definitions: tuple[MarketIndicatorDefinition, ...] = DEFAULT_MARKET_INDICATORS,
) -> str:
    symbols = tuple(
        definition
        for definition in definitions
        if definition.instrument_symbol and definition.preferred_provider == "twelve_data"
    )
    if not symbols:
        return "select 1;"
    value_rows = ",\n        ".join(
        f"({sql_literal(str(definition.instrument_symbol or '').upper())}, "
        f"{sql_literal(definition.display_name)}, "
        f"{sql_literal('etf' if definition.indicator_type.endswith('_etf') or definition.indicator_type == 'equity_index' else 'listed_security')})"
        for definition in symbols
    )
    return f"""with seed(symbol, display_name, instrument_type) as (
    values
        {value_rows}
),
missing_seed as (
    select seed.*
    from seed
    where not exists (
        select 1
        from ref.instrument instrument
        where instrument.is_active = true
          and lower(instrument.primary_symbol) = lower(seed.symbol)
    )
),
existing_issuers as (
    select
        seed.symbol,
        issuer.issuer_id
    from missing_seed seed
    join lateral (
        select issuer_id
        from ref.issuer issuer
        where issuer.display_name = seed.display_name
        order by issuer.issuer_id
        limit 1
    ) issuer on true
),
inserted_issuers as (
    insert into ref.issuer (
        legal_name,
        display_name,
        country_code,
        issuer_type
    )
    select
        seed.display_name,
        seed.display_name,
        'US',
        'fund'
    from missing_seed seed
    where not exists (
        select 1
        from existing_issuers issuer
        where issuer.symbol = seed.symbol
    )
    returning issuer_id, display_name
),
resolved_issuers as (
    select
        seed.symbol,
        seed.display_name,
        seed.instrument_type,
        coalesce(existing.issuer_id, inserted.issuer_id) as issuer_id
    from missing_seed seed
    left join existing_issuers existing on existing.symbol = seed.symbol
    left join inserted_issuers inserted on inserted.display_name = seed.display_name
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
    resolved.issuer_id,
    exchange.exchange_id,
    'US',
    resolved.symbol,
    resolved.instrument_type,
    'USD',
    resolved.display_name,
    true
from resolved_issuers resolved
join ref.exchange exchange on exchange.mic_code = 'ARCX'
where resolved.issuer_id is not null
on conflict (exchange_id, primary_symbol) do update
set
    instrument_type = excluded.instrument_type,
    currency_code = excluded.currency_code,
    name = excluded.name,
    is_active = true;"""


def run_cross_asset_indicator_provider_fetch(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    execute: bool,
    outputsize: str = DEFAULT_PROVIDER_FETCH_OUTPUTSIZE,
    max_requests_per_run: int = DEFAULT_PROVIDER_FETCH_MAX_REQUESTS,
    throttle_seconds: float = DEFAULT_PROVIDER_FETCH_THROTTLE_SECONDS,
    max_rows_per_indicator: int = 400,
    executor: PsqlCommandExecutor | None = None,
    request_executor: Callable[[HttpRequest], Any] = execute_request,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    if max_requests_per_run < 0:
        raise ValueError("max_requests_per_run must be greater than or equal to 0.")
    if throttle_seconds < 0:
        raise ValueError("throttle_seconds must not be negative.")
    if max_rows_per_indicator <= 0:
        raise ValueError("max_rows_per_indicator must be positive.")

    direct_definitions = _provider_fetch_definitions()
    report: dict[str, Any] = {
        "report_name": CROSS_ASSET_INDICATOR_PROVIDER_FETCH_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "registry_version": REGISTRY_VERSION,
        "execute": execute,
        "outputsize": outputsize,
        "max_requests_per_run": max_requests_per_run,
        "throttle_seconds": throttle_seconds,
        "max_rows_per_indicator": max_rows_per_indicator,
        "requested_indicator_count": len(direct_definitions),
        "requested_indicators": [definition.indicator_code for definition in direct_definitions],
        "provider_policy": "free_tier_direct_fetch_for_non_instrument_and_cboe_csv_indicators",
    }
    if not execute:
        report["status"] = "planned"
        return report

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=CROSS_ASSET_INDICATOR_PROVIDER_FETCH_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "registry_version": REGISTRY_VERSION,
            "outputsize": outputsize,
            "max_requests_per_run": max_requests_per_run,
            "throttle_seconds": throttle_seconds,
        },
    )
    observations: list[MarketIndicatorObservationInput] = []
    results: list[dict[str, Any]] = []
    provider_request_count = 0
    throttle_sleep_count = 0
    failed_indicator_count = 0
    skipped_indicator_count = 0

    try:
        sql_executor.execute_non_query(render_market_indicator_registry_upsert_sql(DEFAULT_MARKET_INDICATORS))
        for definition in direct_definitions:
            if provider_request_count >= max_requests_per_run:
                skipped_indicator_count += 1
                results.append(
                    {
                        "indicator_code": definition.indicator_code,
                        "provider": definition.preferred_provider,
                        "status": "skipped",
                        "reason": "request_budget_exhausted",
                    }
                )
                continue
            if provider_request_count > 0 and throttle_seconds > 0:
                sleeper(throttle_seconds)
                throttle_sleep_count += 1
            provider_request_count += 1
            try:
                indicator_observations = fetch_direct_market_indicator_observations(
                    definition,
                    config=config,
                    as_of_date=as_of_date,
                    outputsize=outputsize,
                    max_rows=max_rows_per_indicator,
                    request_executor=request_executor,
                )
            except Exception as exc:
                failed_indicator_count += 1
                results.append(
                    {
                        "indicator_code": definition.indicator_code,
                        "provider": definition.preferred_provider,
                        "status": "failed",
                        "error": str(exc),
                    }
                )
                continue
            observations.extend(indicator_observations)
            results.append(
                {
                    "indicator_code": definition.indicator_code,
                    "provider": definition.preferred_provider,
                    "status": "succeeded",
                    "observation_count": len(indicator_observations),
                    "latest_observation_date": (
                        indicator_observations[-1].observation_date.isoformat()
                        if indicator_observations
                        else ""
                    ),
                }
            )
        sql_executor.execute_non_query(
            render_market_indicator_observation_upsert_sql(
                tuple(observations),
                source_run_id=run_id,
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    report.update(
        {
            "status": "completed_with_failures" if failed_indicator_count else "completed",
            "run_id": run_id,
            "provider_request_count": provider_request_count,
            "throttle_sleep_count": throttle_sleep_count,
            "observation_count": len(observations),
            "failed_indicator_count": failed_indicator_count,
            "skipped_indicator_count": skipped_indicator_count,
            "succeeded_indicator_count": len(direct_definitions) - failed_indicator_count - skipped_indicator_count,
            "results": results,
        }
    )
    return report


def run_cross_asset_indicator_ingest(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    execute: bool,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "report_name": CROSS_ASSET_INDICATOR_INGEST_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "registry_version": REGISTRY_VERSION,
        "fred_indicator_count": sum(1 for item in DEFAULT_MARKET_INDICATORS if item.fred_series_code),
        "price_indicator_count": sum(1 for item in DEFAULT_MARKET_INDICATORS if item.instrument_symbol),
        "execute": execute,
    }
    if not execute:
        report["status"] = "planned"
        return report

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=CROSS_ASSET_INDICATOR_INGEST_PIPELINE_NAME,
        config_json={"as_of_date": as_of_date.isoformat(), "registry_version": REGISTRY_VERSION},
    )
    try:
        sql_executor.execute_non_query(render_market_indicator_registry_upsert_sql(DEFAULT_MARKET_INDICATORS))
        sql_executor.execute_non_query(
            render_cross_asset_indicator_observation_sync_sql(
                as_of_date=as_of_date,
                source_run_id=run_id,
            )
        )
        report["observation_summary"] = _load_json_scalar(
            sql_executor,
            render_cross_asset_observation_summary_sql(as_of_date=as_of_date),
            default={},
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise
    report["status"] = "completed"
    report["run_id"] = run_id
    return report


def run_cross_asset_regime_snapshot(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    execute: bool,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "report_name": CROSS_ASSET_REGIME_SNAPSHOT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "registry_version": REGISTRY_VERSION,
        "execute": execute,
    }
    if not execute:
        report["status"] = "planned"
        report["regime_codes"] = [row.regime_code for row in compute_cross_asset_regimes((), as_of_date=as_of_date)]
        return report

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=CROSS_ASSET_REGIME_SNAPSHOT_PIPELINE_NAME,
        config_json={"as_of_date": as_of_date.isoformat(), "registry_version": REGISTRY_VERSION},
    )
    try:
        sql_executor.execute_non_query(render_market_indicator_registry_upsert_sql(DEFAULT_MARKET_INDICATORS))
        sql_executor.execute_non_query(
            render_market_indicator_snapshot_upsert_sql(as_of_date=as_of_date, source_run_id=run_id)
        )
        snapshots = load_market_indicator_snapshot_inputs(
            executor=sql_executor,
            as_of_date=as_of_date,
        )
        regimes = compute_cross_asset_regimes(snapshots, as_of_date=as_of_date)
        sql_executor.execute_non_query(
            render_cross_asset_regime_upsert_sql(
                regimes=regimes,
                as_of_date=as_of_date,
                source_run_id=run_id,
            )
        )
        sql_executor.execute_non_query(
            render_cross_asset_cycle_impact_upsert_sql(
                regimes=regimes,
                as_of_date=as_of_date,
                source_run_id=run_id,
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise
    report["status"] = "completed"
    report["run_id"] = run_id
    report["snapshot_count"] = len(snapshots)
    report["regime_count"] = len(regimes)
    report["active_regime_count"] = sum(1 for regime in regimes if regime.regime_state == "active")
    report["watch_regime_count"] = sum(1 for regime in regimes if regime.regime_state == "watch")
    report["regime_codes"] = [regime.regime_code for regime in regimes]
    return report


def run_indicator_news_linkage(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    execute: bool,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, Any]:
    if lookback_days < 0 or lookback_days > 14:
        raise ValueError("lookback_days must be between 0 and 14.")
    report: dict[str, Any] = {
        "report_name": INDICATOR_NEWS_LINKAGE_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "lookback_days": lookback_days,
        "linkage_policy": "temporal_evidence_only_not_causal_claim",
        "execute": execute,
    }
    if not execute:
        report["status"] = "planned"
        return report

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=INDICATOR_NEWS_LINKAGE_PIPELINE_NAME,
        config_json={"as_of_date": as_of_date.isoformat(), "lookback_days": lookback_days},
    )
    try:
        sql_executor.execute_non_query(
            render_news_indicator_link_upsert_sql(
                as_of_date=as_of_date,
                lookback_days=lookback_days,
                source_run_id=run_id,
            )
        )
        report["link_summary"] = _load_json_scalar(
            sql_executor,
            render_news_indicator_link_summary_sql(as_of_date=as_of_date, lookback_days=lookback_days),
            default={},
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise
    report["status"] = "completed"
    report["run_id"] = run_id
    return report


def run_recommendation_cross_asset_components(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    execute: bool,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "report_name": RECOMMENDATION_CROSS_ASSET_COMPONENTS_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "component_names": list(RECOMMENDATION_COMPONENT_NAMES),
        "component_weight": "0.0000",
        "recommendation_scoring_mutated": False,
        "automatic_weight_change_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": "read_only_no_order",
        "execute": execute,
    }
    if not execute:
        report["status"] = "planned"
        return report

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=RECOMMENDATION_CROSS_ASSET_COMPONENTS_PIPELINE_NAME,
        config_json={"as_of_date": as_of_date.isoformat(), "component_weight": "0.0000"},
    )
    try:
        sql_executor.execute_non_query(
            render_recommendation_cross_asset_components_upsert_sql(
                as_of_date=as_of_date,
                source_run_id=run_id,
            )
        )
        report["component_summary"] = _load_json_scalar(
            sql_executor,
            render_recommendation_cross_asset_component_summary_sql(as_of_date=as_of_date),
            default={},
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise
    report["status"] = "completed"
    report["run_id"] = run_id
    return report


def render_market_indicator_registry_upsert_sql(definitions: tuple[MarketIndicatorDefinition, ...]) -> str:
    if not definitions:
        raise ValueError("At least one market indicator definition is required.")
    value_rows = ",\n        ".join(_render_indicator_definition_tuple(definition) for definition in definitions)
    return f"""with input_rows (
    indicator_code,
    display_name,
    indicator_type,
    preferred_provider,
    fallback_provider,
    provider_symbol,
    fred_series_code,
    instrument_symbol,
    cboe_csv_url,
    daily_budget_cost,
    freshness_sla_days,
    license_note,
    redistribution_allowed_note,
    stale_policy,
    is_active
) as (
    values
        {value_rows}
)
insert into market.market_indicator (
    indicator_code,
    display_name,
    indicator_type,
    preferred_provider,
    fallback_provider,
    provider_symbol,
    fred_series_code,
    instrument_symbol,
    cboe_csv_url,
    daily_budget_cost,
    freshness_sla_days,
    license_note,
    redistribution_allowed_note,
    stale_policy,
    is_active
)
select *
from input_rows
on conflict (indicator_code) do update
set
    display_name = excluded.display_name,
    indicator_type = excluded.indicator_type,
    preferred_provider = excluded.preferred_provider,
    fallback_provider = excluded.fallback_provider,
    provider_symbol = excluded.provider_symbol,
    fred_series_code = excluded.fred_series_code,
    instrument_symbol = excluded.instrument_symbol,
    cboe_csv_url = excluded.cboe_csv_url,
    daily_budget_cost = excluded.daily_budget_cost,
    freshness_sla_days = excluded.freshness_sla_days,
    license_note = excluded.license_note,
    redistribution_allowed_note = excluded.redistribution_allowed_note,
    stale_policy = excluded.stale_policy,
    is_active = excluded.is_active,
    updated_at = now();"""


def render_cross_asset_indicator_observation_sync_sql(*, as_of_date: date, source_run_id: int) -> str:
    return f"""with fred_rows as (
    select
        indicator.indicator_code,
        observation.observation_date,
        indicator.preferred_provider as provider,
        'macro_series'::text as source_kind,
        observation.value,
        null::numeric as open,
        null::numeric as high,
        null::numeric as low,
        null::numeric as close,
        null::numeric as adjusted_close,
        null::numeric as volume,
        jsonb_build_object(
            'provider_symbol', indicator.provider_symbol,
            'fred_series_code', indicator.fred_series_code
        ) as evidence_json
    from market.market_indicator indicator
    join macro.series series on series.series_code = indicator.fred_series_code
    join macro.observation observation on observation.series_id = series.series_id
    where indicator.is_active = true
      and indicator.fred_series_code is not null
      and observation.observation_date <= {sql_date(as_of_date)}
      and observation.value is not null
),
price_rows as (
    select
        indicator.indicator_code,
        bar.trade_date as observation_date,
        indicator.preferred_provider as provider,
        'price_bar'::text as source_kind,
        coalesce(bar.adjusted_close, bar.close) as value,
        bar.open,
        bar.high,
        bar.low,
        bar.close,
        bar.adjusted_close,
        bar.volume,
        jsonb_build_object(
            'provider_symbol', indicator.provider_symbol,
            'instrument_symbol', instrument.primary_symbol,
            'instrument_id', instrument.instrument_id
        ) as evidence_json
    from market.market_indicator indicator
    join ref.instrument instrument on upper(instrument.primary_symbol) = upper(indicator.instrument_symbol)
    join market.daily_price_bar bar on bar.instrument_id = instrument.instrument_id
    where indicator.is_active = true
      and indicator.instrument_symbol is not null
      and bar.trade_date <= {sql_date(as_of_date)}
      and coalesce(bar.adjusted_close, bar.close) is not null
),
all_source_rows as (
    select * from fred_rows
    union all
    select * from price_rows
),
source_rows as (
    select distinct on (indicator_code, observation_date, provider)
        *
    from all_source_rows
    order by indicator_code, observation_date, provider, source_kind
)
insert into market.market_indicator_observation (
    indicator_code,
    observation_date,
    provider,
    source_kind,
    value,
    open,
    high,
    low,
    close,
    adjusted_close,
    volume,
    source_run_id,
    evidence_json
)
select
    indicator_code,
    observation_date,
    provider,
    source_kind,
    value,
    open,
    high,
    low,
    close,
    adjusted_close,
    volume,
    {source_run_id}::bigint,
    evidence_json
from source_rows
on conflict (indicator_code, observation_date, provider) do update
set
    source_kind = excluded.source_kind,
    value = excluded.value,
    open = excluded.open,
    high = excluded.high,
    low = excluded.low,
    close = excluded.close,
    adjusted_close = excluded.adjusted_close,
    volume = excluded.volume,
    source_run_id = excluded.source_run_id,
    evidence_json = excluded.evidence_json,
    updated_at = now();"""


def render_market_indicator_observation_upsert_sql(
    observations: tuple[MarketIndicatorObservationInput, ...],
    *,
    source_run_id: int,
) -> str:
    if not observations:
        return "select 1;"
    value_rows = ",\n        ".join(_render_indicator_observation_tuple(observation) for observation in observations)
    return f"""with source_rows (
    indicator_code,
    observation_date,
    provider,
    source_kind,
    value,
    open,
    high,
    low,
    close,
    adjusted_close,
    volume,
    evidence_json
) as (
    values
        {value_rows}
),
deduped as (
    select distinct on (indicator_code, observation_date, provider)
        *
    from source_rows
    order by indicator_code, observation_date, provider
)
insert into market.market_indicator_observation (
    indicator_code,
    observation_date,
    provider,
    source_kind,
    value,
    open,
    high,
    low,
    close,
    adjusted_close,
    volume,
    source_run_id,
    evidence_json
)
select
    indicator_code,
    observation_date,
    provider,
    source_kind,
    value,
    open,
    high,
    low,
    close,
    adjusted_close,
    volume,
    {source_run_id}::bigint,
    evidence_json
from deduped
on conflict (indicator_code, observation_date, provider) do update
set
    source_kind = excluded.source_kind,
    value = excluded.value,
    open = excluded.open,
    high = excluded.high,
    low = excluded.low,
    close = excluded.close,
    adjusted_close = excluded.adjusted_close,
    volume = excluded.volume,
    source_run_id = excluded.source_run_id,
    evidence_json = excluded.evidence_json,
    updated_at = now();"""


def fetch_direct_market_indicator_observations(
    definition: MarketIndicatorDefinition,
    *,
    config: RuntimeConfig,
    as_of_date: date,
    outputsize: str,
    max_rows: int,
    request_executor: Callable[[HttpRequest], Any],
) -> tuple[MarketIndicatorObservationInput, ...]:
    if definition.preferred_provider == "twelve_data":
        return fetch_twelve_data_indicator_observations(
            definition,
            config=config,
            as_of_date=as_of_date,
            outputsize=outputsize,
            max_rows=max_rows,
            request_executor=request_executor,
        )
    if definition.preferred_provider == "cboe_csv":
        return fetch_cboe_csv_indicator_observations(
            definition,
            as_of_date=as_of_date,
            max_rows=max_rows,
            request_executor=request_executor,
        )
    raise ValueError(f"Unsupported direct fetch provider `{definition.preferred_provider}`.")


def fetch_twelve_data_indicator_observations(
    definition: MarketIndicatorDefinition,
    *,
    config: RuntimeConfig,
    as_of_date: date,
    outputsize: str,
    max_rows: int,
    request_executor: Callable[[HttpRequest], Any],
) -> tuple[MarketIndicatorObservationInput, ...]:
    if not definition.provider_symbol:
        raise ValueError(f"Missing provider_symbol for `{definition.indicator_code}`.")
    twelve_data = get_source("twelve_data")
    attempts: list[dict[str, str]] = []
    for provider_symbol in twelve_data_symbol_candidates(definition):
        request = twelve_data.build_request(
            "time_series_daily",
            {
                "symbol": provider_symbol,
                "outputsize": outputsize,
            },
            config=config,
            require_credentials=True,
        )
        try:
            payload = request_executor(request).as_json()
            result = normalize_twelve_data_time_series_payload(provider_symbol, payload)
        except Exception as exc:
            attempts.append(
                {
                    "provider_symbol": provider_symbol,
                    "status": "failed",
                    "error": str(exc),
                }
            )
            continue
        attempts.append(
            {
                "provider_symbol": provider_symbol,
                "status": "succeeded",
            }
        )
        return _price_bars_to_indicator_observations(
            definition=definition,
            bars=tuple(bar for bar in result.bars if bar.trade_date <= as_of_date)[-max_rows:],
            provider="twelve_data",
            source_kind="price_bar",
            source_url=request.url,
            provider_symbol=provider_symbol,
            evidence_extra={
                "requested_provider_symbol": definition.provider_symbol,
                "resolved_provider_symbol": provider_symbol,
                "symbol_fallback_attempts": attempts,
                "symbol_fallback_policy": (
                    "bounded_twelve_data_symbol_fallback"
                    if len(twelve_data_symbol_candidates(definition)) > 1
                    else "single_symbol"
                ),
            },
        )
    attempted_symbols = ", ".join(attempt["provider_symbol"] for attempt in attempts)
    last_error = attempts[-1]["error"] if attempts else "unknown"
    raise ValueError(
        f"Twelve Data time_series fetch failed for `{definition.indicator_code}` after candidates "
        f"[{attempted_symbols}]: {last_error}"
    )


def fetch_cboe_csv_indicator_observations(
    definition: MarketIndicatorDefinition,
    *,
    as_of_date: date,
    max_rows: int,
    request_executor: Callable[[HttpRequest], Any],
) -> tuple[MarketIndicatorObservationInput, ...]:
    if not definition.cboe_csv_url:
        raise ValueError(f"Missing CBOE CSV URL for `{definition.indicator_code}`.")
    request = HttpRequest(
        source_name="cboe_csv",
        dataset_name="volatility_index_daily_prices",
        method="GET",
        url=definition.cboe_csv_url,
        headers={"Accept": "text/csv", "User-Agent": "stockanalysis research bot"},
        timeout_seconds=30,
    )
    csv_text = request_executor(request).as_text()
    return parse_cboe_daily_price_csv(
        definition=definition,
        csv_text=csv_text,
        as_of_date=as_of_date,
        max_rows=max_rows,
        source_url=definition.cboe_csv_url,
    )


def parse_cboe_daily_price_csv(
    *,
    definition: MarketIndicatorDefinition,
    csv_text: str,
    as_of_date: date,
    max_rows: int,
    source_url: str,
) -> tuple[MarketIndicatorObservationInput, ...]:
    reader = DictReader(StringIO(csv_text))
    if not reader.fieldnames:
        raise ValueError(f"CBOE CSV for `{definition.indicator_code}` has no header row.")
    observations: list[MarketIndicatorObservationInput] = []
    for raw_row in reader:
        row = {_normalize_csv_header(key): value for key, value in raw_row.items() if key is not None}
        observation_date = _parse_cboe_date(row)
        if observation_date is None or observation_date > as_of_date:
            continue
        close = _csv_decimal(
            row,
            "close",
            "close_price",
            "vix close",
            definition.provider_symbol or "",
            definition.indicator_code,
        )
        if close is None:
            continue
        observations.append(
            MarketIndicatorObservationInput(
                indicator_code=definition.indicator_code,
                observation_date=observation_date,
                provider="cboe_csv",
                source_kind="official_csv",
                value=close,
                open=_csv_decimal(row, "open", "open_price", "vix open"),
                high=_csv_decimal(row, "high", "high_price", "vix high"),
                low=_csv_decimal(row, "low", "low_price", "vix low"),
                close=close,
                adjusted_close=close,
                volume=None,
                evidence_json={
                    "provider_symbol": definition.provider_symbol,
                    "source_url": source_url,
                    "source_page": CBOE_HISTORICAL_DATA_PAGE_URL,
                    "causal_claim": False,
                },
            )
        )
    observations.sort(key=lambda observation: observation.observation_date)
    return tuple(observations[-max_rows:])


def render_market_indicator_snapshot_upsert_sql(*, as_of_date: date, source_run_id: int) -> str:
    return f"""with active_indicators as (
    select *
    from market.market_indicator
    where is_active = true
),
history as (
    select observation.*
    from market.market_indicator_observation observation
    join active_indicators indicator on indicator.indicator_code = observation.indicator_code
    where observation.observation_date <= {sql_date(as_of_date)}
),
latest as (
    select distinct on (indicator.indicator_code)
        indicator.indicator_code,
        indicator.freshness_sla_days,
        indicator.stale_policy,
        history.observation_date as latest_observation_date,
        history.value as latest_value
    from active_indicators indicator
    left join history on history.indicator_code = indicator.indicator_code
    order by indicator.indicator_code, history.observation_date desc
),
prior_values as (
    select
        latest.*,
        p1.value as value_1d,
        p5.value as value_5d,
        p20.value as value_20d,
        p60.value as value_60d,
        p120.value as value_120d
    from latest
    left join lateral (
        select value
        from history
        where history.indicator_code = latest.indicator_code
          and history.observation_date <= latest.latest_observation_date - interval '1 day'
        order by observation_date desc
        limit 1
    ) p1 on true
    left join lateral (
        select value
        from history
        where history.indicator_code = latest.indicator_code
          and history.observation_date <= latest.latest_observation_date - interval '5 days'
        order by observation_date desc
        limit 1
    ) p5 on true
    left join lateral (
        select value
        from history
        where history.indicator_code = latest.indicator_code
          and history.observation_date <= latest.latest_observation_date - interval '20 days'
        order by observation_date desc
        limit 1
    ) p20 on true
    left join lateral (
        select value
        from history
        where history.indicator_code = latest.indicator_code
          and history.observation_date <= latest.latest_observation_date - interval '60 days'
        order by observation_date desc
        limit 1
    ) p60 on true
    left join lateral (
        select value
        from history
        where history.indicator_code = latest.indicator_code
          and history.observation_date <= latest.latest_observation_date - interval '120 days'
        order by observation_date desc
        limit 1
    ) p120 on true
),
window_stats as (
    select
        prior_values.*,
        ma20.moving_average_20d,
        ma50.moving_average_50d,
        ma200.moving_average_200d,
        stats.observation_count_252d,
        stats.average_252d,
        stats.stddev_252d,
        stats.min_252d,
        stats.max_252d
    from prior_values
    left join lateral (
        select avg(value)::numeric(24,8) as moving_average_20d
        from (
            select value
            from history
            where history.indicator_code = prior_values.indicator_code
              and history.observation_date <= prior_values.latest_observation_date
            order by observation_date desc
            limit 20
        ) rows
    ) ma20 on true
    left join lateral (
        select avg(value)::numeric(24,8) as moving_average_50d
        from (
            select value
            from history
            where history.indicator_code = prior_values.indicator_code
              and history.observation_date <= prior_values.latest_observation_date
            order by observation_date desc
            limit 50
        ) rows
    ) ma50 on true
    left join lateral (
        select avg(value)::numeric(24,8) as moving_average_200d
        from (
            select value
            from history
            where history.indicator_code = prior_values.indicator_code
              and history.observation_date <= prior_values.latest_observation_date
            order by observation_date desc
            limit 200
        ) rows
    ) ma200 on true
    left join lateral (
        select
            count(*)::integer as observation_count_252d,
            avg(value)::numeric(24,8) as average_252d,
            stddev_samp(value)::numeric(24,8) as stddev_252d,
            min(value)::numeric(24,8) as min_252d,
            max(value)::numeric(24,8) as max_252d
        from (
            select value
            from history
            where history.indicator_code = prior_values.indicator_code
              and history.observation_date <= prior_values.latest_observation_date
            order by observation_date desc
            limit 252
        ) rows
    ) stats on true
),
scored as (
    select
        *,
        case when value_1d is null or value_1d = 0 then null else ((latest_value - value_1d) / abs(value_1d))::numeric(16,8) end as return_1d,
        case when value_5d is null or value_5d = 0 then null else ((latest_value - value_5d) / abs(value_5d))::numeric(16,8) end as return_5d,
        case when value_20d is null or value_20d = 0 then null else ((latest_value - value_20d) / abs(value_20d))::numeric(16,8) end as return_20d,
        case when value_60d is null or value_60d = 0 then null else ((latest_value - value_60d) / abs(value_60d))::numeric(16,8) end as return_60d,
        case when value_120d is null or value_120d = 0 then null else ((latest_value - value_120d) / abs(value_120d))::numeric(16,8) end as return_120d,
        case
            when max_252d is null or min_252d is null or max_252d = min_252d then null
            else ((latest_value - min_252d) / (max_252d - min_252d))::numeric(8,6)
        end as percentile_252d,
        case
            when stddev_252d is null or stddev_252d = 0 then null
            else ((latest_value - average_252d) / stddev_252d)::numeric(16,8)
        end as z_score_252d,
        case
            when max_252d is null or max_252d = 0 then null
            else ((latest_value - max_252d) / abs(max_252d))::numeric(16,8)
        end as drawdown_252d
    from window_stats
),
classified as (
    select
        *,
        case
            when latest_observation_date is null then 'missing'
            when latest_observation_date < {sql_date(as_of_date)} - (freshness_sla_days || ' days')::interval then 'stale'
            else 'fresh'
        end as freshness_status
    from scored
)
insert into signal.market_indicator_snapshot (
    indicator_code,
    as_of_date,
    latest_observation_date,
    latest_value,
    return_1d,
    return_5d,
    return_20d,
    return_60d,
    return_120d,
    moving_average_20d,
    moving_average_50d,
    moving_average_200d,
    percentile_252d,
    z_score_252d,
    drawdown_252d,
    realized_volatility_20d,
    trend_state,
    shock_direction,
    shock_magnitude,
    confidence,
    freshness_status,
    source_run_id,
    evidence_json
)
select
    indicator_code,
    {sql_date(as_of_date)},
    latest_observation_date,
    latest_value,
    return_1d,
    return_5d,
    return_20d,
    return_60d,
    return_120d,
    moving_average_20d,
    moving_average_50d,
    moving_average_200d,
    percentile_252d,
    z_score_252d,
    drawdown_252d,
    abs(coalesce(return_20d, return_5d, return_1d, 0))::numeric(16,8) as realized_volatility_20d,
    case
        when freshness_status = 'missing' then 'insufficient_history'
        when freshness_status = 'stale' then 'stale'
        when observation_count_252d < 20 then 'insufficient_history'
        when coalesce(return_20d, 0) >= 0.0500 and latest_value >= coalesce(moving_average_50d, latest_value) then 'up'
        when coalesce(return_20d, 0) <= -0.0500 and latest_value <= coalesce(moving_average_50d, latest_value) then 'down'
        else 'flat'
    end as trend_state,
    case
        when freshness_status <> 'fresh' then 'neutral'
        when coalesce(return_5d, 0) >= 0.0300 or coalesce(z_score_252d, 0) >= 1.5000 then 'up'
        when coalesce(return_5d, 0) <= -0.0300 or coalesce(z_score_252d, 0) <= -1.5000 then 'down'
        else 'neutral'
    end as shock_direction,
    least(
        1.0000,
        greatest(abs(coalesce(return_5d, 0)), least(abs(coalesce(z_score_252d, 0)) / 4.0000, 1.0000))
    )::numeric(8,6) as shock_magnitude,
    case
        when freshness_status = 'missing' then 0.0000
        when freshness_status = 'stale' then 0.3500
        when observation_count_252d < 20 then 0.5500
        else 0.8500
    end::numeric(8,6) as confidence,
    freshness_status,
    {source_run_id}::bigint,
    jsonb_build_object(
        'registry_version', {sql_literal(REGISTRY_VERSION)},
        'observation_count_252d', coalesce(observation_count_252d, 0),
        'stale_policy', stale_policy,
        'quality_policy',
            case
                when indicator_code = 'USD_BROAD_INDEX' and freshness_status = 'stale'
                    then 'stale_dollar_index_weakens_dollar_regime_confidence'
                when indicator_code = 'USD_BROAD_INDEX'
                    then 'fred_dollar_index_lag_tolerant_no_imputation'
                when indicator_code = 'XAG_USD'
                    then 'fred_silver_proxy_not_spot_xag_usd'
                else 'standard_indicator_snapshot_policy'
            end,
        'quality_note_ko',
            case
                when indicator_code = 'USD_BROAD_INDEX' and freshness_status = 'stale'
                    then 'FRED 달러 광의 지수가 오래되어 달러 유동성 판단 신뢰도를 낮춘다. 추정값으로 채우지 않는다.'
                when indicator_code = 'USD_BROAD_INDEX'
                    then 'FRED 달러 광의 지수는 공식 공표 지연을 10일까지 허용한다. 최신 관측일을 그대로 표시하고 추정값으로 채우지 않는다.'
                when indicator_code = 'XAG_USD'
                    then '은 지표는 FRED NASDAQQSLVO 일간 silver proxy index를 사용한다. spot XAG/USD 가격이 아니므로 방향성 보조 지표로만 쓴다.'
                else null
            end
    )
from classified
on conflict (indicator_code, as_of_date) do update
set
    latest_observation_date = excluded.latest_observation_date,
    latest_value = excluded.latest_value,
    return_1d = excluded.return_1d,
    return_5d = excluded.return_5d,
    return_20d = excluded.return_20d,
    return_60d = excluded.return_60d,
    return_120d = excluded.return_120d,
    moving_average_20d = excluded.moving_average_20d,
    moving_average_50d = excluded.moving_average_50d,
    moving_average_200d = excluded.moving_average_200d,
    percentile_252d = excluded.percentile_252d,
    z_score_252d = excluded.z_score_252d,
    drawdown_252d = excluded.drawdown_252d,
    realized_volatility_20d = excluded.realized_volatility_20d,
    trend_state = excluded.trend_state,
    shock_direction = excluded.shock_direction,
    shock_magnitude = excluded.shock_magnitude,
    confidence = excluded.confidence,
    freshness_status = excluded.freshness_status,
    source_run_id = excluded.source_run_id,
    evidence_json = excluded.evidence_json,
    updated_at = now();"""


def load_market_indicator_snapshot_inputs(
    *,
    executor: PsqlCommandExecutor,
    as_of_date: date,
) -> tuple[MarketIndicatorSnapshotInput, ...]:
    payload = _load_json_scalar(
        executor,
        f"""select coalesce(
    json_agg(
        json_build_object(
            'indicator_code', indicator_code,
            'latest_observation_date', latest_observation_date,
            'latest_value', latest_value,
            'return_5d', return_5d,
            'return_20d', return_20d,
            'z_score_252d', z_score_252d,
            'shock_direction', shock_direction,
            'shock_magnitude', shock_magnitude,
            'trend_state', trend_state,
            'confidence', confidence,
            'freshness_status', freshness_status
        )
        order by indicator_code
    ),
    '[]'::json
)::text
from signal.market_indicator_snapshot
where as_of_date = {sql_date(as_of_date)};""",
        default=[],
    )
    rows = payload if isinstance(payload, list) else []
    return tuple(_snapshot_input_from_payload(row) for row in rows if isinstance(row, dict))


def compute_cross_asset_regimes(
    snapshots: tuple[MarketIndicatorSnapshotInput, ...],
    *,
    as_of_date: date,
) -> tuple[CrossAssetRegimeOutput, ...]:
    by_code = {snapshot.indicator_code: snapshot for snapshot in snapshots}
    regime_specs = (
        (
            "risk_on",
            (
                ("SPY", "up"),
                ("QQQ", "up"),
                ("IWM", "up"),
                ("HYG", "up"),
                ("VIX", "down"),
            ),
            (),
        ),
        (
            "risk_off",
            (
                ("SPY", "down"),
                ("QQQ", "down"),
                ("IWM", "down"),
                ("VIX", "up"),
                ("USD_BROAD_INDEX", "up"),
            ),
            ("risk_on",),
        ),
        (
            "real_rate_pressure",
            (
                ("US_10Y_REAL_YIELD", "up"),
                ("US_10Y_YIELD", "up"),
                ("TLT", "down"),
                ("QQQ", "down"),
            ),
            (),
        ),
        (
            "dollar_liquidity_tightening",
            (
                ("USD_BROAD_INDEX", "up"),
                ("BTC_USD", "down"),
                ("ETH_USD", "down"),
                ("XAU_USD", "down"),
            ),
            (),
        ),
        (
            "commodity_reflation",
            (
                ("WTI_CRUDE", "up"),
                ("BRENT_CRUDE", "up"),
                ("XAU_USD", "up"),
                ("XAG_USD", "up"),
                ("XLB", "up"),
            ),
            (),
        ),
        (
            "energy_shock",
            (
                ("WTI_CRUDE", "up"),
                ("BRENT_CRUDE", "up"),
                ("HENRY_HUB_GAS", "up"),
                ("OVX", "up"),
                ("VIX", "up"),
            ),
            (),
        ),
        (
            "safe_haven_bid",
            (
                ("XAU_USD", "up"),
                ("TLT", "up"),
                ("VIX", "up"),
                ("SPY", "down"),
            ),
            (),
        ),
        (
            "credit_stress",
            (
                ("US_HIGH_YIELD_SPREAD", "up"),
                ("US_CORPORATE_SPREAD", "up"),
                ("HYG", "down"),
                ("LQD", "down"),
            ),
            (),
        ),
        (
            "volatility_shock",
            (
                ("VIX", "up"),
                ("VIX9D", "up"),
                ("VVIX", "up"),
                ("OVX", "up"),
                ("GVZ", "up"),
            ),
            (),
        ),
        (
            "growth_slowdown",
            (
                ("IWM", "down"),
                ("XLI", "down"),
                ("XLY", "down"),
                ("US_10Y_3M_CURVE", "down"),
                ("US_HIGH_YIELD_SPREAD", "up"),
            ),
            (),
        ),
    )
    outputs: list[CrossAssetRegimeOutput] = []
    scores: dict[str, Decimal] = {}
    for regime_code, drivers, conflict_regimes in regime_specs:
        driver_scores: list[Decimal] = []
        driver_codes: list[str] = []
        for indicator_code, expected_direction in drivers:
            snapshot = by_code.get(indicator_code)
            if snapshot is None:
                continue
            score = _indicator_direction_score(snapshot, expected_direction)
            driver_scores.append(score)
            driver_codes.append(indicator_code)
        if not driver_scores:
            regime_score = Decimal("0")
            confidence = Decimal("0")
            regime_state = "insufficient_data"
        else:
            regime_score = _clamp(sum(driver_scores) / Decimal(len(driver_scores)))
            confidence = _clamp(
                sum(_decimal(snapshot.confidence) for snapshot in by_code.values() if snapshot.indicator_code in driver_codes)
                / Decimal(len(driver_codes))
            )
            regime_state = _regime_state(regime_score, confidence)
        scores[regime_code] = regime_score
        conflict_flags = tuple(
            f"conflicts_with_{conflict_code}"
            for conflict_code in conflict_regimes
            if scores.get(conflict_code, Decimal("0")) >= Decimal("0.6500") and regime_score >= Decimal("0.6500")
        )
        outputs.append(
            CrossAssetRegimeOutput(
                regime_code=regime_code,
                regime_state=regime_state,
                regime_score=regime_score.quantize(Decimal("0.000001")),
                confidence=confidence.quantize(Decimal("0.000001")),
                driver_indicator_codes=tuple(driver_codes),
                conflict_flags=conflict_flags,
                evidence_json={
                    "as_of_date": as_of_date.isoformat(),
                    "policy": "deterministic_cross_asset_regime_v1",
                    "driver_count": len(driver_codes),
                    "causal_claim": False,
                },
            )
        )
    return tuple(outputs)


def render_cross_asset_regime_upsert_sql(
    *,
    regimes: tuple[CrossAssetRegimeOutput, ...],
    as_of_date: date,
    source_run_id: int,
) -> str:
    if not regimes:
        return "select 1;"
    value_rows = ",\n        ".join(_render_regime_tuple(regime) for regime in regimes)
    return f"""with source_rows (
    regime_code,
    regime_state,
    regime_score,
    confidence,
    driver_indicator_codes,
    conflict_flags,
    evidence_json
) as (
    values
        {value_rows}
)
insert into signal.cross_asset_regime_snapshot (
    regime_code,
    as_of_date,
    regime_state,
    regime_score,
    confidence,
    driver_indicator_codes,
    conflict_flags,
    source_run_id,
    evidence_json
)
select
    regime_code,
    {sql_date(as_of_date)},
    regime_state,
    regime_score,
    confidence,
    driver_indicator_codes,
    conflict_flags,
    {source_run_id}::bigint,
    evidence_json
from source_rows
on conflict (regime_code, as_of_date) do update
set
    regime_state = excluded.regime_state,
    regime_score = excluded.regime_score,
    confidence = excluded.confidence,
    driver_indicator_codes = excluded.driver_indicator_codes,
    conflict_flags = excluded.conflict_flags,
    source_run_id = excluded.source_run_id,
    evidence_json = excluded.evidence_json,
    updated_at = now();"""


def render_cross_asset_cycle_impact_upsert_sql(
    *,
    regimes: tuple[CrossAssetRegimeOutput, ...],
    as_of_date: date,
    source_run_id: int,
) -> str:
    active_regimes = tuple(regime for regime in regimes if regime.regime_state in {"active", "watch", "mixed"})
    if not active_regimes:
        return "select 1;"
    value_rows = ",\n        ".join(
        f"({sql_literal(regime.regime_code)}, {sql_numeric(regime.regime_score)}, {sql_numeric(regime.confidence)}, "
        f"{sql_literal(json.dumps(regime.evidence_json, ensure_ascii=False, sort_keys=True))}::jsonb)"
        for regime in active_regimes
    )
    return f"""with regime_rows(regime_code, regime_score, confidence, evidence_json) as (
    values
        {value_rows}
),
mapping(regime_code, node_code, impact_direction, rationale) as (
    values
        ('real_rate_pressure', 'TECH_DOMAIN', 'risk_review', '실질금리 압력은 장기 성장주와 기술주 valuation을 압박할 수 있다.'),
        ('real_rate_pressure', 'AI_SEMICONDUCTOR_CYCLE', 'risk_review', '실질금리 상승은 AI/반도체 duration risk를 높인다.'),
        ('dollar_liquidity_tightening', 'MACRO_LIQUIDITY', 'risk_review', '달러 강세와 유동성 긴축은 위험자산 선호를 낮출 수 있다.'),
        ('commodity_reflation', 'ENERGY_GEOPOLITICS', 'supportive', '원자재 reflation은 에너지/소재 흐름에 우호적일 수 있다.'),
        ('energy_shock', 'ENERGY_GEOPOLITICS', 'risk_review', '에너지 가격 급등은 에너지 수혜와 광범위한 비용 압력을 동시에 만든다.'),
        ('safe_haven_bid', 'MACRO_LIQUIDITY', 'watch', '안전자산 선호는 위험 회피와 유동성 선호를 시사한다.'),
        ('credit_stress', 'MACRO_LIQUIDITY', 'risk_review', '신용 스프레드 확대는 위험자산과 고레버리지 기업에 부담이다.'),
        ('volatility_shock', 'MACRO_LIQUIDITY', 'risk_review', '변동성 급등은 포지션 sizing과 신규 추천을 보수적으로 만든다.'),
        ('growth_slowdown', 'MACRO_GROWTH', 'risk_review', '성장 둔화 신호는 경기민감 섹터와 중장기 thesis를 재점검하게 한다.'),
        ('risk_on', 'MACRO_GROWTH', 'supportive', '주요 위험자산 상승은 위험 선호 개선 신호다.'),
        ('risk_off', 'MACRO_GROWTH', 'risk_review', '위험 회피 체제는 추천과 보유 thesis의 downside를 재검토하게 한다.')
),
source_rows as (
    select
        regime.regime_code,
        node.node_id,
        mapping.impact_direction,
        regime.regime_score as impact_strength,
        regime.confidence,
        mapping.rationale,
        regime.evidence_json || jsonb_build_object('node_code', node.code) as evidence_json
    from regime_rows regime
    join mapping on mapping.regime_code = regime.regime_code
    join ref.classification_node node on node.code = mapping.node_code
     and node.taxonomy_family = 'internal_theme'
)
insert into signal.cross_asset_cycle_impact (
    as_of_date,
    regime_code,
    node_id,
    impact_direction,
    impact_strength,
    confidence,
    rationale,
    source_run_id,
    evidence_json
)
select
    {sql_date(as_of_date)},
    regime_code,
    node_id,
    impact_direction,
    impact_strength,
    confidence,
    rationale,
    {source_run_id}::bigint,
    evidence_json
from source_rows
on conflict (as_of_date, regime_code, node_id) do update
set
    impact_direction = excluded.impact_direction,
    impact_strength = excluded.impact_strength,
    confidence = excluded.confidence,
    rationale = excluded.rationale,
    source_run_id = excluded.source_run_id,
    evidence_json = excluded.evidence_json,
    updated_at = now();"""


def render_news_indicator_link_upsert_sql(*, as_of_date: date, lookback_days: int, source_run_id: int) -> str:
    value_rows = ",\n        ".join(
        f"({sql_literal(node_code)}, {sql_literal(indicator_code)}, {sql_literal(relationship)})"
        for node_code, indicator_code, relationship in NEWS_NODE_INDICATOR_MAP
    )
    return f"""with mapping(node_code, indicator_code, relationship) as (
    values
        {value_rows}
),
recent_news as (
    select distinct
        document.document_id,
        event_row.event_id,
        node.code as node_code,
        document.published_at::date as published_date,
        document.title
    from ingest.source_document document
    join event.event_document_link link on link.document_id = document.document_id
    join event.event event_row on event_row.event_id = link.event_id
    join event.event_classification_impact impact on impact.event_id = event_row.event_id
    join ref.classification_node node on node.node_id = impact.node_id
    where document.published_at::date between {sql_date(as_of_date)} - ({lookback_days} || ' days')::interval
                                      and {sql_date(as_of_date)}
),
indicator_shocks as (
    select snapshot.*
    from signal.market_indicator_snapshot snapshot
    where snapshot.as_of_date between {sql_date(as_of_date)} - ({lookback_days} || ' days')::interval
                                  and {sql_date(as_of_date)}
      and snapshot.shock_direction <> 'neutral'
      and snapshot.freshness_status = 'fresh'
),
source_rows as (
    select distinct on (news.document_id, snapshot.indicator_code, snapshot.as_of_date)
        news.document_id,
        news.event_id,
        snapshot.indicator_code,
        snapshot.as_of_date as link_date,
        case
            when snapshot.shock_direction = 'neutral' then 'temporal_evidence'
            else 'temporal_evidence'
        end as link_type,
        mapping.relationship,
        least(0.8500, greatest(0.3500, snapshot.confidence * greatest(snapshot.shock_magnitude, 0.3500)))::numeric(8,6)
            as confidence,
        (
            '뉴스 분류 ' || mapping.node_code || '와 가격 지표 ' || snapshot.indicator_code ||
            '의 shock이 전후 ' || {lookback_days}::text || '일 창에서 함께 관찰됐다. ' ||
            '이는 인과 확정이 아니라 추천/사이클 검토용 시간상 근거 후보이다.'
        ) as rationale,
        jsonb_build_object(
            'node_code', mapping.node_code,
            'news_title', news.title,
            'indicator_shock_direction', snapshot.shock_direction,
            'indicator_shock_magnitude', snapshot.shock_magnitude,
            'causal_claim', false
        ) as evidence_json
    from recent_news news
    join mapping on mapping.node_code = news.node_code
    join indicator_shocks snapshot on snapshot.indicator_code = mapping.indicator_code
)
insert into event.news_indicator_link (
    document_id,
    event_id,
    indicator_code,
    link_date,
    link_type,
    relationship,
    confidence,
    rationale,
    source_run_id,
    evidence_json
)
select
    document_id,
    event_id,
    indicator_code,
    link_date,
    link_type,
    relationship,
    confidence,
    rationale,
    {source_run_id}::bigint,
    evidence_json
from source_rows
on conflict (document_id, indicator_code, link_date, relationship) do update
set
    event_id = excluded.event_id,
    link_type = excluded.link_type,
    confidence = excluded.confidence,
    rationale = excluded.rationale,
    source_run_id = excluded.source_run_id,
    evidence_json = excluded.evidence_json;"""


def render_recommendation_cross_asset_components_upsert_sql(*, as_of_date: date, source_run_id: int) -> str:
    component_rows = ",\n        ".join(
        f"({sql_literal(component_name)}, 0.0000::numeric, {sql_literal(_component_explanation(component_name))})"
        for component_name in RECOMMENDATION_COMPONENT_NAMES
    )
    return f"""with selected_batch as (
    select batch.*
    from signal.recommendation_batch batch
    where batch.as_of_date <= {sql_date(as_of_date)}
    order by batch.as_of_date desc, batch.batch_id desc
    limit 1
),
active_recommendations as (
    select recommendation.recommendation_id
    from signal.recommendation recommendation
    join selected_batch batch on batch.batch_id = recommendation.batch_id
),
component_templates(component_name, component_weight, explanation) as (
    values
        {component_rows}
),
source_rows as (
    select
        recommendation.recommendation_id,
        template.component_name,
        0.0000::numeric(8,4) as component_score,
        template.component_weight::numeric(8,4) as component_weight,
        template.explanation
    from active_recommendations recommendation
    cross join component_templates template
)
insert into signal.recommendation_score_component (
    recommendation_id,
    component_name,
    component_score,
    component_weight,
    explanation
)
select
    recommendation_id,
    component_name,
    component_score,
    component_weight,
    explanation
from source_rows
on conflict (recommendation_id, component_name) do update
set
    component_score = excluded.component_score,
    component_weight = excluded.component_weight,
    explanation = excluded.explanation;"""


def render_cross_asset_observation_summary_sql(*, as_of_date: date) -> str:
    return f"""with rows as (
    select
        observation.indicator_code,
        observation.observation_date,
        observation.provider
    from market.market_indicator_observation observation
    where observation.observation_date <= {sql_date(as_of_date)}
),
provider_counts as (
    select provider, count(*)::integer as provider_count
    from rows
    group by provider
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'indicator_count', count(distinct rows.indicator_code),
    'observation_count', count(*),
    'latest_observation_date', max(rows.observation_date),
    'provider_counts',
        coalesce(
            (select json_object_agg(provider, provider_count) from provider_counts),
            '{{}}'::json
        )
)::text
from rows;"""


def render_news_indicator_link_summary_sql(*, as_of_date: date, lookback_days: int) -> str:
    return f"""select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'lookback_days', {lookback_days},
    'link_count', count(*),
    'document_count', count(distinct document_id),
    'indicator_count', count(distinct indicator_code)
)::text
from event.news_indicator_link
where link_date between {sql_date(as_of_date)} - ({lookback_days} || ' days')::interval
                    and {sql_date(as_of_date)};"""


def render_recommendation_cross_asset_component_summary_sql(*, as_of_date: date) -> str:
    return f"""with selected_batch as (
    select batch.*
    from signal.recommendation_batch batch
    where batch.as_of_date <= {sql_date(as_of_date)}
    order by batch.as_of_date desc, batch.batch_id desc
    limit 1
),
active_recommendations as (
    select recommendation.recommendation_id
    from signal.recommendation recommendation
    join selected_batch batch on batch.batch_id = recommendation.batch_id
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'recommendation_count', count(distinct component.recommendation_id),
    'component_count', count(*),
    'weighted_component_count', count(*) filter (where component.component_weight <> 0),
    'recommendation_scoring_mutated', false
)::text
from signal.recommendation_score_component component
join active_recommendations recommendation on recommendation.recommendation_id = component.recommendation_id
where component.component_name in ({", ".join(sql_literal(name) for name in RECOMMENDATION_COMPONENT_NAMES)});"""


def _render_indicator_definition_tuple(definition: MarketIndicatorDefinition) -> str:
    return "(" + ", ".join(
        (
            sql_literal(definition.indicator_code),
            sql_literal(definition.display_name),
            sql_literal(definition.indicator_type),
            sql_literal(definition.preferred_provider),
            sql_literal(definition.fallback_provider),
            sql_literal(definition.provider_symbol),
            sql_literal(definition.fred_series_code),
            sql_literal(definition.instrument_symbol),
            sql_literal(definition.cboe_csv_url),
            sql_numeric(definition.daily_budget_cost),
            f"{definition.freshness_sla_days}::integer",
            sql_literal(definition.license_note),
            sql_literal(definition.redistribution_allowed_note),
            sql_literal(definition.stale_policy),
            sql_literal(definition.is_active),
        )
    ) + ")"


def _render_indicator_observation_tuple(observation: MarketIndicatorObservationInput) -> str:
    evidence_json = observation.evidence_json or {}
    return "(" + ", ".join(
        (
            sql_literal(observation.indicator_code),
            sql_date(observation.observation_date),
            sql_literal(observation.provider),
            sql_literal(observation.source_kind),
            sql_numeric(observation.value),
            _nullable_numeric(observation.open),
            _nullable_numeric(observation.high),
            _nullable_numeric(observation.low),
            _nullable_numeric(observation.close),
            _nullable_numeric(observation.adjusted_close),
            _nullable_numeric(observation.volume),
            f"{sql_literal(json.dumps(evidence_json, ensure_ascii=False, sort_keys=True))}::jsonb",
        )
    ) + ")"


def _price_bars_to_indicator_observations(
    *,
    definition: MarketIndicatorDefinition,
    bars: tuple[MarketDailyPriceBarRecord, ...],
    provider: str,
    source_kind: str,
    source_url: str,
    provider_symbol: str | None = None,
    evidence_extra: dict[str, Any] | None = None,
) -> tuple[MarketIndicatorObservationInput, ...]:
    resolved_provider_symbol = provider_symbol or definition.provider_symbol
    extra = evidence_extra or {}
    return tuple(
        MarketIndicatorObservationInput(
            indicator_code=definition.indicator_code,
            observation_date=bar.trade_date,
            provider=provider,
            source_kind=source_kind,
            value=bar.adjusted_close,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            adjusted_close=bar.adjusted_close,
            volume=Decimal(bar.volume),
            evidence_json={
                "provider_symbol": resolved_provider_symbol,
                "source_url": _redact_url_secret(source_url),
                "causal_claim": False,
                **extra,
            },
        )
        for bar in bars
    )


def _parse_cboe_date(row: dict[str, str]) -> date | None:
    value = row.get("date") or row.get("trade_date") or row.get("datetime")
    if not value:
        return None
    cleaned = value.strip()
    for separator in ("-", "/"):
        if separator in cleaned:
            parts = cleaned.split(separator)
            if len(parts) != 3:
                continue
            if len(parts[0]) == 4:
                year, month, day = parts
            else:
                month, day, year = parts
            return date(int(year), int(month), int(day))
    return date.fromisoformat(cleaned)


def _csv_decimal(row: dict[str, str], *keys: str) -> Decimal | None:
    for key in keys:
        value = row.get(_normalize_csv_header(key))
        if value is None:
            continue
        cleaned = str(value).strip().replace(",", "")
        if not cleaned:
            continue
        return Decimal(cleaned)
    return None


def _normalize_csv_header(value: str) -> str:
    return str(value).strip().lower().replace(".", "").replace(" ", "_")


def _snapshot_input_from_payload(payload: dict[str, Any]) -> MarketIndicatorSnapshotInput:
    observation_date = payload.get("latest_observation_date")
    return MarketIndicatorSnapshotInput(
        indicator_code=str(payload.get("indicator_code") or ""),
        latest_observation_date=date.fromisoformat(str(observation_date)) if observation_date else None,
        latest_value=_optional_decimal(payload.get("latest_value")),
        return_5d=_optional_decimal(payload.get("return_5d")),
        return_20d=_optional_decimal(payload.get("return_20d")),
        z_score_252d=_optional_decimal(payload.get("z_score_252d")),
        shock_direction=str(payload.get("shock_direction") or "neutral"),
        shock_magnitude=_decimal(payload.get("shock_magnitude")),
        trend_state=str(payload.get("trend_state") or "insufficient_history"),
        confidence=_decimal(payload.get("confidence")),
        freshness_status=str(payload.get("freshness_status") or "missing"),
    )


def _indicator_direction_score(snapshot: MarketIndicatorSnapshotInput, expected_direction: str) -> Decimal:
    if snapshot.freshness_status != "fresh":
        return Decimal("0")
    trend_score = Decimal("0")
    if expected_direction == "up":
        if snapshot.shock_direction == "up":
            trend_score += Decimal("0.55")
        if snapshot.trend_state == "up":
            trend_score += Decimal("0.25")
        trend_score += max(Decimal("0"), min(Decimal("0.20"), _decimal(snapshot.return_20d) * Decimal("2")))
    elif expected_direction == "down":
        if snapshot.shock_direction == "down":
            trend_score += Decimal("0.55")
        if snapshot.trend_state == "down":
            trend_score += Decimal("0.25")
        trend_score += max(Decimal("0"), min(Decimal("0.20"), -_decimal(snapshot.return_20d) * Decimal("2")))
    else:
        raise ValueError(f"Unsupported expected direction `{expected_direction}`.")
    return _clamp(trend_score * max(snapshot.confidence, Decimal("0.35")))


def _regime_state(score: Decimal, confidence: Decimal) -> str:
    if confidence <= Decimal("0"):
        return "insufficient_data"
    if score >= Decimal("0.6500"):
        return "active"
    if score >= Decimal("0.4000"):
        return "watch"
    return "inactive"


def _render_regime_tuple(regime: CrossAssetRegimeOutput) -> str:
    return "(" + ", ".join(
        (
            sql_literal(regime.regime_code),
            sql_literal(regime.regime_state),
            sql_numeric(regime.regime_score),
            sql_numeric(regime.confidence),
            _render_text_array(regime.driver_indicator_codes),
            _render_text_array(regime.conflict_flags),
            f"{sql_literal(json.dumps(regime.evidence_json, ensure_ascii=False, sort_keys=True))}::jsonb",
        )
    ) + ")"


def _render_text_array(values: tuple[str, ...]) -> str:
    if not values:
        return "'{}'::text[]"
    return "array[" + ", ".join(sql_literal(value) for value in values) + "]::text[]"


def _component_explanation(component_name: str) -> str:
    explanations = {
        "index_regime_score": "SPY/QQQ/IWM 같은 주요 지수 흐름을 추천 근거 후보로 저장한다. 초기 weight는 0이라 총점은 바꾸지 않는다.",
        "cross_asset_regime_score": "금리·달러·원자재·변동성·신용을 묶은 cross-asset regime 후보다. 초기 weight는 0이다.",
        "real_rate_duration_penalty": "실질금리 상승이 장기 성장주 valuation에 주는 압력을 표시한다. 초기 weight는 0이다.",
        "usd_liquidity_pressure": "달러 강세와 유동성 긴축 압력을 표시한다. 초기 weight는 0이다.",
        "commodity_input_cost_score": "원자재 상승이 섹터별 비용/수혜에 주는 영향을 표시한다. 초기 weight는 0이다.",
        "energy_shock_risk": "원유·가스 가격 급등과 에너지 변동성 충격을 표시한다. 초기 weight는 0이다.",
        "volatility_risk_penalty": "VIX 등 변동성 충격이 포지션 sizing과 신규 추천에 주는 위험을 표시한다. 초기 weight는 0이다.",
        "credit_stress_penalty": "신용 스프레드 확대와 회사채 압력이 위험자산에 주는 부담을 표시한다. 초기 weight는 0이다.",
    }
    return explanations[component_name]


def _base_registry_report() -> dict[str, Any]:
    provider_counts: dict[str, int] = {}
    provider_budget: dict[str, str] = {}
    for indicator in DEFAULT_MARKET_INDICATORS:
        provider_counts[indicator.preferred_provider] = provider_counts.get(indicator.preferred_provider, 0) + 1
        provider_budget[indicator.preferred_provider] = str(
            Decimal(provider_budget.get(indicator.preferred_provider, "0")) + indicator.daily_budget_cost
        )
    return {
        "report_name": FREE_PROVIDER_REGISTRY_PIPELINE_NAME,
        "registry_version": REGISTRY_VERSION,
        "indicator_count": len(DEFAULT_MARKET_INDICATORS),
        "provider_counts": provider_counts,
        "provider_daily_budget_cost": provider_budget,
        "excluded_primary_provider": "alpha_vantage",
        "excluded_primary_provider_reason": "free tier 25 calls/day is insufficient for cross-asset plus watchlist sync",
        "twelve_data_soft_budget_credits_per_day": 250,
        "twelve_data_hard_cap_credits_per_day": 700,
        "twelve_data_free_tier_reference_limit": 800,
        "stale_policy": "mark_stale_no_imputation",
    }


def _provider_fetch_definitions() -> tuple[MarketIndicatorDefinition, ...]:
    return tuple(
        definition
        for definition in DEFAULT_MARKET_INDICATORS
        if (
            definition.preferred_provider == "cboe_csv"
            or (
                definition.preferred_provider == "twelve_data"
                and definition.provider_symbol
                and not definition.instrument_symbol
            )
        )
    )


def twelve_data_symbol_candidates(definition: MarketIndicatorDefinition) -> tuple[str, ...]:
    if not definition.provider_symbol:
        return ()
    if definition.indicator_code != "XAG_USD":
        return (definition.provider_symbol,)
    candidates: list[str] = []
    for candidate in (definition.provider_symbol, *XAG_USD_TWELVE_DATA_SYMBOL_CANDIDATES):
        cleaned = str(candidate or "").strip()
        if cleaned and cleaned not in candidates:
            candidates.append(cleaned)
    return tuple(candidates)


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _decimal(value: object) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def _nullable_numeric(value: Decimal | None) -> str:
    if value is None:
        return "null::numeric"
    return sql_numeric(value)


def _redact_url_secret(url: str) -> str:
    if "apikey=" not in url.lower():
        return url
    prefix, _, tail = url.partition("?")
    redacted_parts = []
    for part in tail.split("&"):
        key, separator, value = part.partition("=")
        if key.lower() == "apikey":
            redacted_parts.append(f"{key}{separator}<redacted>")
        else:
            redacted_parts.append(f"{key}{separator}{value}" if separator else key)
    return prefix + "?" + "&".join(redacted_parts)


def _clamp(value: Decimal, *, lower: Decimal = Decimal("0"), upper: Decimal = Decimal("1")) -> Decimal:
    return min(upper, max(lower, value))


def _load_json_scalar(executor: PsqlCommandExecutor, sql: str, *, default: Any) -> Any:
    payload_text = executor.execute_scalar(sql)
    if payload_text is None:
        return default
    return json.loads(str(payload_text))
