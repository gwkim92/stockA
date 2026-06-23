from __future__ import annotations

import json
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from stockanalysis.ingest.market.price import (
    MarketDailyPriceBarRecord,
    MarketPriceSyncResult,
    load_market_price_sync_result,
    load_latest_market_price_trade_date,
    render_latest_market_price_trade_date_sql,
    render_instrument_lookup_by_symbol_sql,
    render_market_price_upsert_sql,
    resolve_market_price_provider,
    run_market_price_batch_upsert,
    run_market_price_upsert,
)
from stockanalysis.ingest.models import FetchResponse
from stockanalysis.ingest.psql import PsqlExecutionError


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class FakeExecutor:
    def __init__(
        self,
        *,
        run_id: int = 401,
        run_ids: list[int] | None = None,
        fail_on_upsert: bool = False,
        fail_on_upsert_calls: set[int] | None = None,
        missing_instrument: bool = False,
        latest_trade_dates: dict[str, str | None] | None = None,
    ) -> None:
        self.run_id = run_id
        self.run_ids = list(run_ids) if run_ids is not None else None
        self.fail_on_upsert = fail_on_upsert
        self.fail_on_upsert_calls = set(fail_on_upsert_calls or set())
        self.missing_instrument = missing_instrument
        self.latest_trade_dates = dict(latest_trade_dates or {})
        self.instrument_lookup_error: str | None = None
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []
        self.instrument_payload = {
            "instrument_id": 501,
            "primary_symbol": "AAPL",
            "instrument_name": "Apple Inc. Common Stock",
        }
        self._upsert_call_count = 0

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "select max(b.trade_date)::text" in sql:
            for symbol, latest_trade_date in self.latest_trade_dates.items():
                if symbol in sql:
                    if latest_trade_date is None:
                        raise PsqlExecutionError("psql returned no rows for scalar query")
                    return latest_trade_date
            raise PsqlExecutionError("psql returned no rows for scalar query")
        if "from ref.instrument i" in sql:
            if self.instrument_lookup_error is not None:
                raise PsqlExecutionError(self.instrument_lookup_error)
            if self.missing_instrument:
                raise PsqlExecutionError("psql returned no rows for scalar query")
            if "MSFT" in sql:
                return json.dumps(
                    {
                        "instrument_id": 601,
                        "primary_symbol": "MSFT",
                        "instrument_name": "Microsoft Corporation Common Stock",
                    }
                )
            return json.dumps(self.instrument_payload)
        if "insert into ops.pipeline_run" in sql:
            if self.run_ids is not None:
                if not self.run_ids:
                    raise RuntimeError("no remaining run ids")
                return str(self.run_ids.pop(0))
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)
        if "insert into market.daily_price_bar" in sql:
            self._upsert_call_count += 1
        if self.fail_on_upsert and "insert into market.daily_price_bar" in sql:
            raise RuntimeError("boom")
        if self._upsert_call_count in self.fail_on_upsert_calls and "insert into market.daily_price_bar" in sql:
            raise RuntimeError("boom")


class MarketPriceTests(unittest.TestCase):
    def test_load_market_price_sync_result_from_fixture(self) -> None:
        result = load_market_price_sync_result(
            "AAPL",
            config=type("Config", (), {})(),
            prices_json_path=str(FIXTURES_DIR / "alpha_vantage_daily_adjusted_AAPL.json"),
        )
        self.assertEqual(result.symbol, "AAPL")
        self.assertEqual(len(result.bars), 2)
        self.assertEqual(result.bars[0].trade_date.isoformat(), "2024-10-31")
        self.assertEqual(result.bars[1].adjusted_close, result.bars[1].close)
        self.assertEqual(result.price_adjustment_mode, "adjusted")

    def test_load_market_price_sync_result_from_free_daily_payload(self) -> None:
        result = load_market_price_sync_result(
            "AAPL",
            config=type("Config", (), {})(),
            prices_json_path=str(FIXTURES_DIR / "alpha_vantage_daily_AAPL.json"),
        )
        self.assertEqual(result.symbol, "AAPL")
        self.assertEqual(len(result.bars), 2)
        self.assertEqual(result.bars[1].adjusted_close, result.bars[1].close)
        self.assertEqual(result.price_adjustment_mode, "unadjusted_fallback")

    def test_load_market_price_sync_result_from_twelve_data_payload(self) -> None:
        result = load_market_price_sync_result(
            "AAPL",
            config=type("Config", (), {})(),
            prices_json_path=str(FIXTURES_DIR / "twelve_data_time_series_daily_AAPL.json"),
            provider="twelve_data",
        )
        self.assertEqual(result.symbol, "AAPL")
        self.assertEqual(result.provider, "twelve_data")
        self.assertEqual(len(result.bars), 2)
        self.assertEqual(result.bars[0].trade_date.isoformat(), "2026-05-14")
        self.assertEqual(result.bars[1].close, Decimal("211.26000"))
        self.assertEqual(result.bars[1].adjusted_close, result.bars[1].close)
        self.assertEqual(result.price_adjustment_mode, "split_adjusted_provider")

    def test_load_market_price_sync_result_from_tossinvest_candles_payload(self) -> None:
        result = load_market_price_sync_result(
            "AAPL",
            config=type("Config", (), {})(),
            prices_json_path=str(FIXTURES_DIR / "tossinvest_candles_1d_AAPL.json"),
            provider="tossinvest",
        )

        self.assertEqual(result.symbol, "AAPL")
        self.assertEqual(result.provider, "tossinvest")
        self.assertEqual(len(result.bars), 2)
        self.assertEqual(result.bars[0].trade_date.isoformat(), "2026-03-24")
        self.assertEqual(result.bars[0].close, Decimal("185.10"))
        self.assertEqual(result.bars[1].volume, 3521000)
        self.assertEqual(result.bars[1].adjusted_close, result.bars[1].close)
        self.assertEqual(result.price_adjustment_mode, "adjusted_provider")

    def test_resolve_market_price_provider_accepts_aliases(self) -> None:
        self.assertEqual(resolve_market_price_provider("twelvedata"), "twelve_data")
        self.assertEqual(resolve_market_price_provider("12data"), "twelve_data")
        self.assertEqual(resolve_market_price_provider("av"), "alpha_vantage")
        self.assertEqual(resolve_market_price_provider("toss"), "tossinvest")

    def test_load_market_price_sync_result_uses_free_daily_endpoint_by_default(self) -> None:
        calls: list[str] = []

        def fake_execute_request(request):
            calls.append(request.url)
            return FetchResponse(
                status_code=200,
                content_type="application/json",
                body=(FIXTURES_DIR / "alpha_vantage_daily_AAPL.json").read_bytes(),
            )

        config = type(
            "Config",
            (),
            {"resolve": lambda self, env_name, required: "alpha-demo-key"},
        )()
        with patch("stockanalysis.ingest.market.price.execute_request", side_effect=fake_execute_request):
            result = load_market_price_sync_result("AAPL", config=config)

        self.assertEqual(len(calls), 1)
        self.assertIn("TIME_SERIES_DAILY", calls[0])
        self.assertNotIn("TIME_SERIES_DAILY_ADJUSTED", calls[0])
        self.assertEqual(result.price_adjustment_mode, "unadjusted_fallback")

    def test_load_market_price_sync_result_falls_back_to_free_daily_endpoint_in_adjusted_mode(self) -> None:
        calls: list[str] = []

        def fake_execute_request(request):
            calls.append(request.url)
            if "TIME_SERIES_DAILY_ADJUSTED" in request.url:
                return FetchResponse(
                    status_code=200,
                    content_type="application/json",
                    body=json.dumps(
                        {"Information": "This is a premium endpoint."},
                    ).encode("utf-8"),
                )
            return FetchResponse(
                status_code=200,
                content_type="application/json",
                body=(FIXTURES_DIR / "alpha_vantage_daily_AAPL.json").read_bytes(),
            )

        config = type(
            "Config",
            (),
            {"resolve": lambda self, env_name, required: "alpha-demo-key"},
        )()
        with patch.dict("os.environ", {"STOCKANALYSIS_ALPHA_VANTAGE_PRICE_MODE": "adjusted"}):
            with patch("stockanalysis.ingest.market.price.execute_request", side_effect=fake_execute_request):
                result = load_market_price_sync_result("AAPL", config=config)

        self.assertEqual(len(calls), 2)
        self.assertIn("TIME_SERIES_DAILY_ADJUSTED", calls[0])
        self.assertIn("TIME_SERIES_DAILY", calls[1])
        self.assertEqual(result.price_adjustment_mode, "unadjusted_fallback")

    def test_load_market_price_sync_result_uses_twelve_data_endpoint(self) -> None:
        calls: list[str] = []

        def fake_execute_request(request):
            calls.append(request.url)
            return FetchResponse(
                status_code=200,
                content_type="application/json",
                body=(FIXTURES_DIR / "twelve_data_time_series_daily_AAPL.json").read_bytes(),
            )

        config = type(
            "Config",
            (),
            {"resolve": lambda self, env_name, required: "twelve-demo-key"},
        )()
        with patch("stockanalysis.ingest.market.price.execute_request", side_effect=fake_execute_request):
            result = load_market_price_sync_result("AAPL", config=config, provider="twelve_data", outputsize="120")

        self.assertEqual(len(calls), 1)
        self.assertIn("api.twelvedata.com/time_series", calls[0])
        self.assertIn("interval=1day", calls[0])
        self.assertIn("outputsize=120", calls[0])
        self.assertEqual(result.provider, "twelve_data")

    def test_load_market_price_sync_result_uses_tossinvest_candles_endpoint(self) -> None:
        calls: list[object] = []

        def fake_execute_request(request):
            calls.append(request)
            if request.dataset_name == "oauth_token":
                return FetchResponse(
                    status_code=200,
                    content_type="application/json",
                    body=json.dumps({"access_token": "access-token-test", "token_type": "Bearer"}).encode("utf-8"),
                )
            return FetchResponse(
                status_code=200,
                content_type="application/json",
                body=(FIXTURES_DIR / "tossinvest_candles_1d_AAPL.json").read_bytes(),
            )

        config = type(
            "Config",
            (),
            {"resolve": lambda self, env_name, required: "toss-secret-placeholder"},
        )()
        with patch("stockanalysis.ingest.market.price.execute_request", side_effect=fake_execute_request):
            result = load_market_price_sync_result("AAPL", config=config, provider="tossinvest", outputsize="120")

        self.assertEqual(len(calls), 2)
        self.assertIn("/oauth2/token", calls[0].url)
        self.assertIn("/api/v1/candles", calls[1].url)
        self.assertIn("interval=1d", calls[1].url)
        self.assertIn("count=120", calls[1].url)
        self.assertEqual(calls[1].as_dict()["headers"]["Authorization"], "<redacted>")
        self.assertEqual(result.provider, "tossinvest")

    def test_render_instrument_lookup_by_symbol_sql(self) -> None:
        sql = render_instrument_lookup_by_symbol_sql("AAPL")
        self.assertIn("from ref.instrument i", sql)
        self.assertIn("AAPL", sql)

    def test_render_latest_market_price_trade_date_sql(self) -> None:
        sql = render_latest_market_price_trade_date_sql("AAPL")
        self.assertIn("select max(b.trade_date)::text", sql)
        self.assertIn("from ref.instrument i", sql)
        self.assertIn("join market.daily_price_bar b", sql)
        self.assertIn("AAPL", sql)

    def test_load_latest_market_price_trade_date(self) -> None:
        executor = FakeExecutor(latest_trade_dates={"AAPL": "2026-05-15"})

        latest_trade_date = load_latest_market_price_trade_date("AAPL", executor=executor)

        self.assertEqual(latest_trade_date, date(2026, 5, 15))

    def test_load_latest_market_price_trade_date_returns_none_when_absent(self) -> None:
        executor = FakeExecutor(latest_trade_dates={"AAPL": None})

        latest_trade_date = load_latest_market_price_trade_date("AAPL", executor=executor)

        self.assertIsNone(latest_trade_date)

    def test_render_market_price_upsert_sql(self) -> None:
        result = load_market_price_sync_result(
            "AAPL",
            config=type("Config", (), {})(),
            prices_json_path=str(FIXTURES_DIR / "alpha_vantage_daily_adjusted_AAPL.json"),
        )
        sql = render_market_price_upsert_sql(result, instrument_id=501, source_run_id=901)
        self.assertIn("insert into market.daily_price_bar", sql)
        self.assertIn("501", sql)
        self.assertIn("901::bigint", sql)
        self.assertIn("2024-11-01", sql)

    def test_run_market_price_upsert_records_pipeline_run_and_source_run_id(self) -> None:
        executor = FakeExecutor(run_id=77)
        summary = run_market_price_upsert(
            "AAPL",
            config=type("Config", (), {})(),
            prices_json_path=str(FIXTURES_DIR / "alpha_vantage_daily_adjusted_AAPL.json"),
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 77)
        self.assertEqual(summary["bar_count"], 2)
        self.assertEqual(summary["price_adjustment_mode"], "adjusted")
        self.assertEqual(summary["provider"], "alpha_vantage")
        self.assertEqual(summary["instrument_symbol"], "AAPL")
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("77::bigint", executor.non_query_sql[0])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[1])

    def test_run_market_price_upsert_records_twelve_data_provider_metadata(self) -> None:
        executor = FakeExecutor(run_id=81)
        summary = run_market_price_upsert(
            "AAPL",
            config=type("Config", (), {})(),
            prices_json_path=str(FIXTURES_DIR / "twelve_data_time_series_daily_AAPL.json"),
            provider="twelve_data",
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 81)
        self.assertEqual(summary["provider"], "twelve_data")
        self.assertEqual(summary["price_adjustment_mode"], "split_adjusted_provider")
        self.assertIn('"provider": "twelve_data"', executor.scalar_sql[1])

    def test_run_market_price_upsert_marks_pipeline_run_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=78, fail_on_upsert=True)
        with self.assertRaises(RuntimeError):
            run_market_price_upsert(
                "AAPL",
                config=type("Config", (), {})(),
                prices_json_path=str(FIXTURES_DIR / "alpha_vantage_daily_adjusted_AAPL.json"),
                executor=executor,
            )
        self.assertEqual(len(executor.non_query_sql), 2)
        self.assertIn("status = 'failed'", executor.non_query_sql[1])

    def test_run_market_price_upsert_fails_when_instrument_missing(self) -> None:
        executor = FakeExecutor(run_id=79, missing_instrument=True)
        with self.assertRaises(ValueError):
            run_market_price_upsert(
                "AAPL",
                config=type("Config", (), {})(),
                prices_json_path=str(FIXTURES_DIR / "alpha_vantage_daily_adjusted_AAPL.json"),
                executor=executor,
            )

    def test_run_market_price_upsert_preserves_psql_lookup_errors(self) -> None:
        executor = FakeExecutor(run_id=80)
        executor.instrument_lookup_error = "permission denied while trying to connect to Docker"
        with self.assertRaises(PsqlExecutionError):
            run_market_price_upsert(
                "AAPL",
                config=type("Config", (), {})(),
                prices_json_path=str(FIXTURES_DIR / "alpha_vantage_daily_adjusted_AAPL.json"),
                executor=executor,
            )

    def test_run_market_price_batch_upsert_uses_fixture_directory(self) -> None:
        executor = FakeExecutor(run_ids=[301, 302])
        summary = run_market_price_batch_upsert(
            ["AAPL", "MSFT"],
            config=type("Config", (), {})(),
            fixtures_dir=str(FIXTURES_DIR),
            executor=executor,
        )
        self.assertEqual(summary["requested_symbol_count"], 2)
        self.assertEqual(summary["succeeded_symbol_count"], 2)
        self.assertEqual(summary["failed_symbol_count"], 0)
        self.assertEqual(summary["skipped_symbol_count"], 0)
        self.assertEqual(summary["provider_request_count"], 0)
        self.assertEqual(summary["total_bar_count"], 4)
        self.assertEqual(summary["results"][0]["run_id"], 301)
        self.assertEqual(summary["results"][1]["run_id"], 302)

    def test_run_market_price_batch_upsert_uses_twelve_data_fixture_directory(self) -> None:
        executor = FakeExecutor(run_ids=[303, 304])
        summary = run_market_price_batch_upsert(
            ["AAPL", "MSFT"],
            config=type("Config", (), {})(),
            fixtures_dir=str(FIXTURES_DIR),
            provider="twelve_data",
            executor=executor,
        )
        self.assertEqual(summary["provider"], "twelve_data")
        self.assertEqual(summary["requested_symbol_count"], 2)
        self.assertEqual(summary["succeeded_symbol_count"], 2)
        self.assertEqual(summary["provider_request_count"], 0)
        self.assertEqual(summary["total_bar_count"], 4)

    def test_run_market_price_batch_upsert_continues_after_failure(self) -> None:
        executor = FakeExecutor(run_ids=[401, 402], fail_on_upsert_calls={2})
        summary = run_market_price_batch_upsert(
            ["AAPL", "MSFT"],
            config=type("Config", (), {})(),
            fixtures_dir=str(FIXTURES_DIR),
            executor=executor,
        )
        self.assertEqual(summary["requested_symbol_count"], 2)
        self.assertEqual(summary["succeeded_symbol_count"], 1)
        self.assertEqual(summary["failed_symbol_count"], 1)
        self.assertEqual(summary["results"][0]["status"], "succeeded")
        self.assertEqual(summary["results"][1]["status"], "failed")

    def test_run_market_price_batch_upsert_throttles_provider_requests_and_skips_budget(self) -> None:
        executor = FakeExecutor(run_ids=[501, 502])
        sleep_calls: list[float] = []

        def fake_sleep(seconds: float) -> None:
            sleep_calls.append(seconds)

        def fake_load_market_price_sync_result(symbol: str, **kwargs) -> MarketPriceSyncResult:
            return _market_price_result(symbol)

        with patch(
            "stockanalysis.ingest.market.price.load_market_price_sync_result",
            side_effect=fake_load_market_price_sync_result,
        ):
            summary = run_market_price_batch_upsert(
                ["AAPL", "MSFT", "NVDA"],
                config=type("Config", (), {})(),
                throttle_seconds=1.0,
                max_requests_per_run=2,
                executor=executor,
                sleeper=fake_sleep,
            )

        self.assertEqual(summary["requested_symbol_count"], 3)
        self.assertEqual(summary["succeeded_symbol_count"], 2)
        self.assertEqual(summary["failed_symbol_count"], 0)
        self.assertEqual(summary["skipped_symbol_count"], 1)
        self.assertEqual(summary["provider_request_count"], 2)
        self.assertEqual(summary["throttle_sleep_count"], 1)
        self.assertEqual(sleep_calls, [1.0])
        self.assertEqual(summary["results"][2]["status"], "skipped")
        self.assertEqual(summary["results"][2]["reason"], "request_budget_exhausted")

    def test_run_market_price_batch_upsert_skips_fresh_symbols_before_provider_request(self) -> None:
        executor = FakeExecutor(run_ids=[601], latest_trade_dates={"AAPL": "2026-05-15", "MSFT": None})
        loaded_symbols: list[str] = []

        def fake_load_market_price_sync_result(symbol: str, **kwargs) -> MarketPriceSyncResult:
            loaded_symbols.append(symbol)
            return _market_price_result(symbol)

        with patch(
            "stockanalysis.ingest.market.price.load_market_price_sync_result",
            side_effect=fake_load_market_price_sync_result,
        ):
            summary = run_market_price_batch_upsert(
                ["AAPL", "MSFT"],
                config=type("Config", (), {})(),
                provider="twelve_data",
                throttle_seconds=1.0,
                max_requests_per_run=2,
                skip_if_fresh=True,
                freshness_date=date(2026, 5, 15),
                executor=executor,
            )

        self.assertEqual(loaded_symbols, ["MSFT"])
        self.assertEqual(summary["requested_symbol_count"], 2)
        self.assertEqual(summary["succeeded_symbol_count"], 1)
        self.assertEqual(summary["skipped_symbol_count"], 1)
        self.assertEqual(summary["provider_request_count"], 1)
        self.assertEqual(summary["throttle_sleep_count"], 0)
        self.assertTrue(summary["skip_if_fresh"])
        self.assertEqual(summary["freshness_date"], "2026-05-15")
        self.assertEqual(summary["results"][0]["status"], "skipped")
        self.assertEqual(summary["results"][0]["reason"], "fresh_price_data_exists")
        self.assertEqual(summary["results"][0]["latest_trade_date"], "2026-05-15")
        self.assertEqual(summary["results"][1]["status"], "succeeded")

    def test_run_market_price_batch_upsert_reuses_tossinvest_oauth_token(self) -> None:
        executor = FakeExecutor(run_ids=[701, 702])
        calls: list[str] = []

        def fake_execute_request(request):
            calls.append(request.dataset_name)
            if request.dataset_name == "oauth_token":
                return FetchResponse(
                    status_code=200,
                    content_type="application/json",
                    body=json.dumps({"access_token": "access-token-test", "token_type": "Bearer"}).encode("utf-8"),
                )
            return FetchResponse(
                status_code=200,
                content_type="application/json",
                body=(FIXTURES_DIR / "tossinvest_candles_1d_AAPL.json").read_bytes(),
            )

        config = type(
            "Config",
            (),
            {"resolve": lambda self, env_name, required: "toss-secret-placeholder"},
        )()
        with patch("stockanalysis.ingest.market.price.execute_request", side_effect=fake_execute_request):
            summary = run_market_price_batch_upsert(
                ["AAPL", "MSFT"],
                config=config,
                provider="tossinvest",
                outputsize="200",
                max_requests_per_run=2,
                executor=executor,
            )

        self.assertEqual(calls, ["oauth_token", "candles", "candles"])
        self.assertEqual(summary["provider"], "tossinvest")
        self.assertEqual(summary["provider_request_count"], 2)
        self.assertEqual(summary["provider_auth_request_count"], 1)
        self.assertEqual(summary["succeeded_symbol_count"], 2)


def _market_price_result(symbol: str) -> MarketPriceSyncResult:
    return MarketPriceSyncResult(
        symbol=symbol.upper(),
        price_adjustment_mode="unadjusted_fallback",
        provider="alpha_vantage",
        bars=(
            MarketDailyPriceBarRecord(
                trade_date=date(2026, 5, 15),
                open=Decimal("100.00"),
                high=Decimal("101.00"),
                low=Decimal("99.00"),
                close=Decimal("100.50"),
                adjusted_close=Decimal("100.50"),
                volume=1000,
            ),
        ),
    )
