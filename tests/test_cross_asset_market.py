from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from stockanalysis.operations.cross_asset_market import (
    DEFAULT_MARKET_INDICATORS,
    RECOMMENDATION_COMPONENT_NAMES,
    CrossAssetRegimeOutput,
    MarketIndicatorSnapshotInput,
    MarketIndicatorDefinition,
    compute_cross_asset_regimes,
    cross_asset_instrument_price_symbols,
    fetch_twelve_data_indicator_observations,
    parse_cboe_daily_price_csv,
    render_cross_asset_instrument_bootstrap_sql,
    render_cross_asset_cycle_impact_upsert_sql,
    render_cross_asset_indicator_observation_sync_sql,
    render_market_indicator_registry_upsert_sql,
    render_market_indicator_observation_upsert_sql,
    render_news_indicator_link_upsert_sql,
    render_recommendation_cross_asset_components_upsert_sql,
    render_market_indicator_snapshot_upsert_sql,
    twelve_data_symbol_candidates,
)
from stockanalysis.ingest.config import RuntimeConfig


class CrossAssetMarketTest(unittest.TestCase):
    def test_registry_excludes_alpha_vantage_primary_provider(self) -> None:
        providers = {indicator.preferred_provider for indicator in DEFAULT_MARKET_INDICATORS}
        self.assertNotIn("alpha_vantage", providers)
        self.assertIn("fred", providers)
        self.assertIn("twelve_data", providers)
        self.assertIn("cboe_csv", providers)

    def test_registry_contains_core_free_cross_asset_indicators(self) -> None:
        codes = {indicator.indicator_code for indicator in DEFAULT_MARKET_INDICATORS}
        for expected in {
            "US_10Y_YIELD",
            "US_10Y_REAL_YIELD",
            "USD_BROAD_INDEX",
            "WTI_CRUDE",
            "VIX",
            "US_HIGH_YIELD_SPREAD",
            "SPY",
            "QQQ",
            "XAU_USD",
            "XAG_USD",
            "BTC_USD",
        }:
            self.assertIn(expected, codes)

    def test_xag_uses_fred_silver_proxy_not_twelve_data_spot_by_default(self) -> None:
        by_code = {indicator.indicator_code: indicator for indicator in DEFAULT_MARKET_INDICATORS}
        xag = by_code["XAG_USD"]

        self.assertEqual(xag.preferred_provider, "fred")
        self.assertEqual(xag.provider_symbol, "NASDAQQSLVO")
        self.assertEqual(xag.fred_series_code, "NASDAQQSLVO")
        self.assertIn("프록시", xag.display_name)
        self.assertIn("Do not label as spot XAG/USD", xag.redistribution_allowed_note)

    def test_cross_asset_instrument_price_symbols_returns_etf_watchlist_only(self) -> None:
        symbols = cross_asset_instrument_price_symbols()
        for expected in {"SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "TLT", "HYG", "LQD"}:
            self.assertIn(expected, symbols)
        self.assertNotIn("XAU/USD", symbols)
        self.assertNotIn("XAG/USD", symbols)
        self.assertEqual(len(symbols), len(set(symbols)))

    def test_cross_asset_instrument_bootstrap_sql_inserts_missing_etfs_only(self) -> None:
        sql = render_cross_asset_instrument_bootstrap_sql()
        self.assertIn("missing_seed as", sql)
        self.assertIn("lower(instrument.primary_symbol) = lower(seed.symbol)", sql)
        self.assertIn("join ref.exchange exchange on exchange.mic_code = 'ARCX'", sql)
        self.assertIn("'SPY'", sql)
        self.assertIn("'QQQ'", sql)
        self.assertIn("'etf'", sql)
        self.assertNotIn("'XAU/USD'", sql)

    def test_observation_sync_reads_macro_and_price_sources(self) -> None:
        sql = render_cross_asset_indicator_observation_sync_sql(
            as_of_date=date(2026, 6, 5),
            source_run_id=123,
        )
        self.assertIn("macro.observation", sql)
        self.assertIn("market.daily_price_bar", sql)
        self.assertIn("market.market_indicator_observation", sql)
        self.assertIn("select distinct on (indicator_code, observation_date, provider)", sql)
        self.assertIn("on conflict (indicator_code, observation_date, provider)", sql)

    def test_recommendation_components_are_zero_weight(self) -> None:
        sql = render_recommendation_cross_asset_components_upsert_sql(
            as_of_date=date(2026, 6, 5),
            source_run_id=123,
        )
        for component_name in RECOMMENDATION_COMPONENT_NAMES:
            self.assertIn(component_name, sql)
        self.assertIn("0.0000::numeric", sql)
        self.assertIn("recommendation_scoring_mutated", "recommendation_scoring_mutated")

    def test_safe_haven_bid_from_gold_vix_and_spy_down(self) -> None:
        regimes = compute_cross_asset_regimes(
            (
                _snapshot("XAU_USD", shock_direction="up", trend_state="up", return_20d="0.10"),
                _snapshot("VIX", shock_direction="up", trend_state="up", return_20d="0.30"),
                _snapshot("SPY", shock_direction="down", trend_state="down", return_20d="-0.08"),
            ),
            as_of_date=date(2026, 6, 5),
        )
        by_code = {regime.regime_code: regime for regime in regimes}
        self.assertEqual(by_code["safe_haven_bid"].regime_state, "active")

    def test_energy_shock_from_wti_brent_vix_up(self) -> None:
        regimes = compute_cross_asset_regimes(
            (
                _snapshot("WTI_CRUDE", shock_direction="up", trend_state="up", return_20d="0.12"),
                _snapshot("BRENT_CRUDE", shock_direction="up", trend_state="up", return_20d="0.10"),
                _snapshot("VIX", shock_direction="up", trend_state="up", return_20d="0.22"),
            ),
            as_of_date=date(2026, 6, 5),
        )
        by_code = {regime.regime_code: regime for regime in regimes}
        self.assertEqual(by_code["energy_shock"].regime_state, "active")

    def test_registry_sql_records_stale_policy_without_imputation(self) -> None:
        sql = render_market_indicator_registry_upsert_sql(DEFAULT_MARKET_INDICATORS)
        self.assertIn("mark_stale_no_imputation", sql)
        self.assertIn("fred_lag_tolerant_no_imputation_weaken_dollar_regime_after_sla", sql)
        self.assertIn("daily_budget_cost", sql)
        dollar = next(item for item in DEFAULT_MARKET_INDICATORS if item.indicator_code == "USD_BROAD_INDEX")
        self.assertEqual(dollar.freshness_sla_days, 10)

    def test_usd_broad_index_stale_policy_is_explicit_in_snapshot_evidence(self) -> None:
        sql = render_market_indicator_snapshot_upsert_sql(
            as_of_date=date(2026, 6, 5),
            source_run_id=77,
        )
        self.assertIn("indicator.stale_policy", sql)
        self.assertIn("stale_dollar_index_weakens_dollar_regime_confidence", sql)
        self.assertIn("fred_dollar_index_lag_tolerant_no_imputation", sql)
        self.assertIn("공식 공표 지연을 10일까지 허용", sql)
        self.assertIn("fred_silver_proxy_not_spot_xag_usd", sql)
        self.assertIn("spot XAG/USD 가격이 아니므로 방향성 보조 지표", sql)
        self.assertIn("추정값으로 채우지 않는다", sql)

    def test_parse_cboe_daily_price_csv_normalizes_rows(self) -> None:
        definition = MarketIndicatorDefinition(
            indicator_code="VIX9D",
            display_name="9일 VIX",
            indicator_type="volatility",
            preferred_provider="cboe_csv",
            provider_symbol="VIX9D",
            cboe_csv_url="https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX9D_History.csv",
        )
        observations = parse_cboe_daily_price_csv(
            definition=definition,
            csv_text="DATE,OPEN,HIGH,LOW,CLOSE\n06/03/2026,10,12,9,11\n06/04/2026,11,14,10,13\n",
            as_of_date=date(2026, 6, 4),
            max_rows=10,
            source_url=definition.cboe_csv_url or "",
        )
        self.assertEqual(len(observations), 2)
        self.assertEqual(observations[-1].indicator_code, "VIX9D")
        self.assertEqual(observations[-1].value, Decimal("13"))
        self.assertEqual(observations[-1].source_kind, "official_csv")

    def test_parse_cboe_daily_price_csv_accepts_single_value_symbol_column(self) -> None:
        definition = MarketIndicatorDefinition(
            indicator_code="VVIX",
            display_name="VVIX",
            indicator_type="volatility",
            preferred_provider="cboe_csv",
            provider_symbol="VVIX",
            cboe_csv_url="https://cdn.cboe.com/api/global/us_indices/daily_prices/VVIX_History.csv",
        )
        observations = parse_cboe_daily_price_csv(
            definition=definition,
            csv_text="DATE,VVIX\n06/03/2026,80.5\n06/04/2026,82.25\n",
            as_of_date=date(2026, 6, 4),
            max_rows=10,
            source_url=definition.cboe_csv_url or "",
        )
        self.assertEqual(len(observations), 2)
        self.assertEqual(observations[-1].value, Decimal("82.25"))
        self.assertEqual(observations[-1].close, Decimal("82.25"))

    def test_twelve_data_direct_indicator_fetch_redacts_api_key(self) -> None:
        definition = MarketIndicatorDefinition(
            indicator_code="XAU_USD",
            display_name="금 현물 달러",
            indicator_type="precious_metals",
            preferred_provider="twelve_data",
            provider_symbol="XAU/USD",
        )
        observations = fetch_twelve_data_indicator_observations(
            definition,
            config=RuntimeConfig(twelve_data_api_key="secret-key"),
            as_of_date=date(2026, 6, 4),
            outputsize="2",
            max_rows=10,
            request_executor=_FakeTwelveDataResponse(),
        )
        self.assertEqual(len(observations), 2)
        self.assertEqual(observations[-1].indicator_code, "XAU_USD")
        self.assertEqual(observations[-1].value, Decimal("2360.1"))
        source_url = str((observations[-1].evidence_json or {}).get("source_url") or "")
        self.assertIn("apikey=<redacted>", source_url)
        self.assertNotIn("secret-key", source_url)

    def test_xag_usd_twelve_data_fetch_tries_bounded_symbol_fallbacks(self) -> None:
        definition = MarketIndicatorDefinition(
            indicator_code="XAG_USD",
            display_name="은 현물 달러",
            indicator_type="precious_metals",
            preferred_provider="twelve_data",
            provider_symbol="XAG/USD",
        )
        self.assertEqual(twelve_data_symbol_candidates(definition), ("XAG/USD", "XAGUSD", "SILVER"))
        fake_response = _FallbackTwelveDataResponse(fail_first_count=1)
        observations = fetch_twelve_data_indicator_observations(
            definition,
            config=RuntimeConfig(twelve_data_api_key="secret-key"),
            as_of_date=date(2026, 6, 4),
            outputsize="2",
            max_rows=10,
            request_executor=fake_response,
        )
        self.assertEqual(len(observations), 2)
        self.assertEqual(len(fake_response.request_urls), 2)
        evidence = observations[-1].evidence_json or {}
        self.assertEqual(evidence["requested_provider_symbol"], "XAG/USD")
        self.assertEqual(evidence["resolved_provider_symbol"], "XAGUSD")
        self.assertEqual(evidence["symbol_fallback_policy"], "bounded_twelve_data_symbol_fallback")
        self.assertNotIn("secret-key", str(evidence))

    def test_direct_observation_upsert_sql_uses_deduped_conflict_boundary(self) -> None:
        definition = MarketIndicatorDefinition(
            indicator_code="VVIX",
            display_name="VVIX",
            indicator_type="volatility",
            preferred_provider="cboe_csv",
            provider_symbol="VVIX",
        )
        observations = parse_cboe_daily_price_csv(
            definition=definition,
            csv_text="Date,Open,High,Low,Close\n2026-06-04,90,95,88,92\n",
            as_of_date=date(2026, 6, 4),
            max_rows=10,
            source_url="https://example.com/VVIX.csv",
        )
        sql = render_market_indicator_observation_upsert_sql(observations, source_run_id=77)
        self.assertIn("deduped as", sql)
        self.assertIn("on conflict (indicator_code, observation_date, provider)", sql)
        self.assertIn("'VVIX'", sql)

    def test_cycle_impact_sql_uses_actual_classification_node_code_column(self) -> None:
        sql = render_cross_asset_cycle_impact_upsert_sql(
            regimes=(
                CrossAssetRegimeOutput(
                    regime_code="real_rate_pressure",
                    regime_state="active",
                    regime_score=Decimal("0.75"),
                    confidence=Decimal("0.90"),
                    driver_indicator_codes=("US_10Y_REAL_YIELD",),
                    conflict_flags=(),
                    evidence_json={"source": "unit"},
                ),
            ),
            as_of_date=date(2026, 6, 5),
            source_run_id=123,
        )
        self.assertIn("node.code = mapping.node_code", sql)
        self.assertIn("node.taxonomy_family = 'internal_theme'", sql)
        self.assertNotIn("node.node_code", sql)

    def test_news_indicator_link_sql_uses_actual_classification_node_code_column(self) -> None:
        sql = render_news_indicator_link_upsert_sql(
            as_of_date=date(2026, 6, 5),
            lookback_days=2,
            source_run_id=123,
        )
        self.assertIn("node.code as node_code", sql)
        self.assertNotIn("node.node_code", sql)


def _snapshot(
    indicator_code: str,
    *,
    shock_direction: str,
    trend_state: str,
    return_20d: str,
) -> MarketIndicatorSnapshotInput:
    return MarketIndicatorSnapshotInput(
        indicator_code=indicator_code,
        latest_observation_date=date(2026, 6, 5),
        latest_value=Decimal("100"),
        return_5d=Decimal("0.05") if shock_direction == "up" else Decimal("-0.05"),
        return_20d=Decimal(return_20d),
        z_score_252d=Decimal("2.0") if shock_direction == "up" else Decimal("-2.0"),
        shock_direction=shock_direction,
        shock_magnitude=Decimal("0.60"),
        trend_state=trend_state,
        confidence=Decimal("0.90"),
        freshness_status="fresh",
    )


class _FakeTwelveDataResponse:
    def __call__(self, request: object) -> "_FakeTwelveDataResponse":
        self.request = request
        return self

    def as_json(self) -> dict[str, object]:
        return {
            "status": "ok",
            "values": [
                {
                    "datetime": "2026-06-04",
                    "open": "2350.0",
                    "high": "2365.0",
                    "low": "2345.0",
                    "close": "2360.1",
                    "volume": "0",
                },
                {
                    "datetime": "2026-06-03",
                    "open": "2330.0",
                    "high": "2355.0",
                    "low": "2325.0",
                    "close": "2348.4",
                    "volume": "0",
                },
            ],
        }


class _FallbackTwelveDataResponse:
    def __init__(self, *, fail_first_count: int) -> None:
        self.fail_first_count = fail_first_count
        self.request_urls: list[str] = []

    def __call__(self, request: object) -> "_FallbackTwelveDataResponse":
        self.request_urls.append(str(getattr(request, "url", "")))
        return self

    def as_json(self) -> dict[str, object]:
        if len(self.request_urls) <= self.fail_first_count:
            return {
                "status": "error",
                "message": "symbol not found",
            }
        return {
            "status": "ok",
            "values": [
                {
                    "datetime": "2026-06-04",
                    "open": "30.10",
                    "high": "30.40",
                    "low": "29.90",
                    "close": "30.25",
                    "volume": "0",
                },
                {
                    "datetime": "2026-06-03",
                    "open": "29.70",
                    "high": "30.05",
                    "low": "29.50",
                    "close": "29.95",
                    "volume": "0",
                },
            ],
        }


if __name__ == "__main__":
    unittest.main()
