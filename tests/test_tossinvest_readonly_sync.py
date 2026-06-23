from __future__ import annotations

import json
import unittest
from io import BytesIO
from datetime import date
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.portfolio.position import (
    PositionSnapshotRecord,
    PositionSnapshotSyncResult,
    render_position_snapshot_upsert_sql,
)
from stockanalysis.operations.tossinvest_readonly_sync import (
    DEFAULT_TOSSINVEST_PORTFOLIO_NAME,
    normalize_tossinvest_readonly_payload,
    render_tossinvest_readonly_sync_upsert_sql,
    run_tossinvest_readonly_sync,
)


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "tossinvest_readonly_mixed_holdings.json"
ROOT_DIR = Path(__file__).resolve().parents[1]


class FakeExecutor:
    def __init__(self) -> None:
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "insert into ops.pipeline_run" in sql:
            return "901"
        if sql.startswith("begin;") and "market.fx_rate_snapshot" in sql:
            return json.dumps(
                {
                    "portfolio_id": 3009,
                    "source_position_count": 2,
                    "resolved_position_count": 2,
                    "position_count": 2,
                    "fx_rate_snapshot_id": 7001,
                    "fx_linked_position_count": 1,
                }
            )
        raise AssertionError(f"Unexpected SQL: {sql[:120]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class TossInvestReadonlySyncTests(unittest.TestCase):
    def test_normalizer_handles_mixed_krw_usd_holdings_with_mid_rate(self) -> None:
        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

        result = normalize_tossinvest_readonly_payload(
            payload,
            portfolio_name=DEFAULT_TOSSINVEST_PORTFOLIO_NAME,
            base_currency="KRW",
            snapshot_date=date(2026, 6, 23),
            credentials_configured=True,
            selected_account_seq="account-seq-secret-test",
        )

        self.assertEqual(result.base_currency, "KRW")
        self.assertEqual(len(result.holdings), 2)
        samsung = result.holdings[0]
        apple = result.holdings[1]
        self.assertEqual(samsung.native_currency, "KRW")
        self.assertEqual(str(samsung.market_value_base), "70000.00")
        self.assertEqual(samsung.conversion_note, "native_equals_base_currency")
        self.assertEqual(apple.native_currency, "USD")
        self.assertEqual(str(apple.fx_rate_to_base), "1390.00000000")
        self.assertEqual(str(apple.market_value_base), "556000.00")
        self.assertEqual(str(apple.cost_basis_base), "250200.000000")
        self.assertEqual(apple.conversion_note, "tossinvest_mid_rate")
        self.assertEqual(result.buying_power[0]["cash_buying_power"], "1000000.00")
        self.assertEqual(result.sellable_quantities[1]["sellable_quantity"], "2")
        self.assertEqual(result.commissions[1]["commission_rate"], "0.0007")
        self.assertTrue(result.market_calendars["KR"]["today_is_open"])
        self.assertEqual(result.market_calendars["US"]["next_business_day"], "2026-06-24")
        self.assertEqual(result.stock_warnings[1]["symbol"], "AAPL")
        self.assertEqual(result.stock_warnings[1]["warning_types"], ["VI_STATIC"])
        self.assertEqual(result.market_microdata[1]["symbol"], "AAPL")
        self.assertEqual(result.market_microdata[1]["best_bid_price"], "200.00")
        self.assertEqual(result.order_history["open_order_count"], 1)
        self.assertEqual(result.order_history["closed_order_count"], 1)
        self.assertEqual(result.order_history["order_detail_loaded_count"], 1)

        dumped_report = json.dumps(result.report(), sort_keys=True)
        self.assertNotIn("order-open-secret-test-001", dumped_report)
        self.assertNotIn("order-closed-secret-test-002", dumped_report)
        self.assertNotIn("cursor-secret-test", dumped_report)

    def test_render_upsert_sql_writes_fx_and_native_values_without_long_term_paper(self) -> None:
        result = normalize_tossinvest_readonly_payload(
            json.loads(FIXTURE_PATH.read_text(encoding="utf-8")),
            portfolio_name=DEFAULT_TOSSINVEST_PORTFOLIO_NAME,
            base_currency="KRW",
            snapshot_date=date(2026, 6, 23),
            credentials_configured=True,
            selected_account_seq=None,
        )

        sql = render_tossinvest_readonly_sync_upsert_sql(result, source_run_id=901)

        self.assertIn("market.fx_rate_snapshot", sql)
        self.assertIn("native_currency_code", sql)
        self.assertIn("market_price_native", sql)
        self.assertIn("fx_rate_snapshot_id", sql)
        self.assertIn("Toss Real Readonly", sql)
        self.assertNotIn("Long Term Paper", sql)
        self.assertIn("1390.00000000", sql)
        self.assertIn(") existing_issuer", sql)

    def test_run_fixture_execute_produces_deterministic_secret_free_report(self) -> None:
        executor = FakeExecutor()
        report = run_tossinvest_readonly_sync(
            config=RuntimeConfig(
                tossinvest_client_id="client-id-test",
                tossinvest_client_secret="client-secret-test",
                tossinvest_account_seq="account-seq-secret-test",
                psql_command="psql",
            ),
            fixture_json_path=str(FIXTURE_PATH),
            as_of_date=date(2026, 6, 23),
            execute=True,
            executor=executor,
        )

        dumped = json.dumps(report, sort_keys=True)
        self.assertEqual(report["status"], "succeeded")
        self.assertEqual(report["run_id"], 901)
        self.assertEqual(report["write_result"]["position_count"], 2)
        self.assertEqual(report["submit_adapter_status"], "disabled_stub")
        self.assertFalse(report["broker_submit_allowed"])
        self.assertFalse(report["submitted_to_broker"])
        self.assertEqual(report["order_history"]["order_count"], 2)
        self.assertEqual(report["market_microdata_symbol_count"], 2)
        self.assertEqual(report["stock_warning_symbol_count"], 2)
        self.assertNotIn("client-secret-test", dumped)
        self.assertNotIn("account-seq-secret-test", dumped)
        self.assertNotIn("1234567890", dumped)
        self.assertNotIn("order-open-secret-test-001", dumped)
        self.assertNotIn("order-closed-secret-test-002", dumped)
        self.assertTrue(any("config_json" in sql and "succeeded" in sql for sql in executor.non_query_sql))

    def test_live_dry_run_fetches_remaining_readonly_endpoints_without_order_submit(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        calls: list[str] = []

        def fake_request(request):
            calls.append(request.dataset_name)
            if request.dataset_name == "oauth_token":
                payload = {"access_token": "access-token-test"}
            elif request.dataset_name == "accounts":
                payload = fixture["accounts"]
            elif request.dataset_name == "holdings":
                payload = fixture["holdings"]
            elif request.dataset_name == "exchange_rate":
                payload = fixture["exchange_rate"]
            elif request.dataset_name == "stocks":
                payload = fixture["stocks"]
            elif request.dataset_name == "prices":
                payload = fixture["prices"]
            elif request.dataset_name == "buying_power":
                payload = fixture["buying_power"][0] if "currency=KRW" in request.url else fixture["buying_power"][1]
            elif request.dataset_name == "sellable_quantity":
                payload = fixture["sellable_quantities"][0] if "005930" in request.url else fixture["sellable_quantities"][1]
            elif request.dataset_name == "commissions":
                payload = fixture["commissions"]
            elif request.dataset_name == "market_calendar_kr":
                payload = fixture["market_calendars"]["KR"]
            elif request.dataset_name == "market_calendar_us":
                payload = fixture["market_calendars"]["US"]
            elif request.dataset_name == "stock_warnings":
                payload = fixture["stock_warnings"]["005930"] if "005930" in request.url else fixture["stock_warnings"]["AAPL"]
            elif request.dataset_name == "orderbook":
                payload = fixture["market_microdata"]["orderbooks"]["005930"] if "005930" in request.url else fixture["market_microdata"]["orderbooks"]["AAPL"]
            elif request.dataset_name == "trades":
                payload = fixture["market_microdata"]["trades"]["005930"] if "005930" in request.url else fixture["market_microdata"]["trades"]["AAPL"]
            elif request.dataset_name == "price_limits":
                payload = fixture["market_microdata"]["price_limits"]["005930"] if "005930" in request.url else fixture["market_microdata"]["price_limits"]["AAPL"]
            elif request.dataset_name == "orders":
                payload = fixture["order_history"]["open_orders"] if "status=OPEN" in request.url else fixture["order_history"]["closed_orders"]
            elif request.dataset_name == "order_detail":
                payload = fixture["order_history"]["order_details"][0]
            else:
                raise AssertionError(f"Unexpected Toss request: {request.dataset_name}")
            return type(
                "Response",
                (),
                {"as_json": lambda self, payload=payload: payload},
            )()

        report = run_tossinvest_readonly_sync(
            config=RuntimeConfig(
                tossinvest_client_id="client-id-test",
                tossinvest_client_secret="client-secret-test",
                psql_command="psql",
            ),
            as_of_date=date(2026, 6, 23),
            dry_run=True,
            request_executor=fake_request,
        )

        self.assertEqual(report["status"], "loaded")
        self.assertIn("market_calendar_kr", calls)
        self.assertIn("market_calendar_us", calls)
        self.assertEqual(calls.count("stock_warnings"), 2)
        self.assertEqual(calls.count("orderbook"), 2)
        self.assertEqual(calls.count("trades"), 2)
        self.assertEqual(calls.count("price_limits"), 2)
        self.assertEqual(calls.count("orders"), 2)
        self.assertEqual(calls.count("order_detail"), 2)
        self.assertNotIn("orders_submit", calls)
        self.assertFalse(report["submitted_to_broker"])

    def test_live_http_403_reports_provider_access_block_without_secret(self) -> None:
        def blocked_request(_request):
            raise HTTPError(
                url="https://openapi.tossinvest.com/oauth2/token",
                code=403,
                msg="Forbidden",
                hdrs={},
                fp=BytesIO(b'{"error":"access_denied","error_description":"IP address not allowed"}'),
            )

        report = run_tossinvest_readonly_sync(
            config=RuntimeConfig(
                tossinvest_client_id="client-id-test",
                tossinvest_client_secret="client-secret-test",
                psql_command="psql",
            ),
            as_of_date=date(2026, 6, 23),
            dry_run=True,
            request_executor=blocked_request,
        )

        dumped = json.dumps(report, sort_keys=True)
        self.assertEqual(report["status"], "blocked_provider_access")
        self.assertEqual(report["provider_http_status"], 403)
        self.assertEqual(report["provider_error"], "access_denied")
        self.assertEqual(report["provider_error_description"], "IP address not allowed")
        self.assertEqual(report["config_gap"], "ip_address_not_allowed")
        self.assertFalse(report["submitted_to_broker"])
        self.assertNotIn("client-secret-test", dumped)

    def test_execute_http_403_records_failed_pipeline_without_position_write(self) -> None:
        def blocked_request(_request):
            raise HTTPError(
                url="https://openapi.tossinvest.com/oauth2/token",
                code=403,
                msg="Forbidden",
                hdrs={},
                fp=BytesIO(b'{"error":"access_denied","error_description":"IP address not allowed"}'),
            )

        executor = FakeExecutor()
        report = run_tossinvest_readonly_sync(
            config=RuntimeConfig(
                tossinvest_client_id="client-id-test",
                tossinvest_client_secret="client-secret-test",
                psql_command="psql",
            ),
            as_of_date=date(2026, 6, 23),
            execute=True,
            executor=executor,
            request_executor=blocked_request,
        )

        self.assertEqual(report["status"], "blocked_provider_access")
        self.assertEqual(report["run_id"], 901)
        self.assertFalse(report["submitted_to_broker"])
        self.assertFalse(any("market.fx_rate_snapshot" in sql for sql in executor.scalar_sql))
        self.assertTrue(any("ip_address_not_allowed" in sql and "failed" in sql for sql in executor.non_query_sql))

    def test_legacy_usd_position_snapshot_sql_stays_on_existing_columns(self) -> None:
        result = PositionSnapshotSyncResult(
            portfolio_name="Long Term Paper",
            base_currency="USD",
            market_code="US",
            strategy_name="long_term_core",
            snapshot_date=date(2026, 6, 23),
            is_paper=True,
            positions=(
                PositionSnapshotRecord(
                    symbol="AAPL",
                    quantity=Decimal("1"),
                    market_price=Decimal("200"),
                    market_value=Decimal("200"),
                    cost_basis=Decimal("180"),
                    weight=Decimal("0.1"),
                    unrealized_pnl=Decimal("20"),
                    linked_thesis_id=None,
                ),
            ),
        )

        sql = render_position_snapshot_upsert_sql(result, source_run_id=900)

        self.assertIn("insert into portfolio.position_snapshot", sql)
        self.assertNotIn("native_currency_code", sql)
        self.assertNotIn("fx_rate_snapshot_id", sql)
        self.assertIn("Long Term Paper", sql)

    def test_migration_and_seed_define_currency_foundation(self) -> None:
        migration = (ROOT_DIR / "db" / "migrations" / "0033_tossinvest_currency_foundation.sql").read_text(
            encoding="utf-8"
        )
        seed = (ROOT_DIR / "db" / "seeds" / "0001_reference_seed.sql").read_text(encoding="utf-8")

        self.assertIn("create table if not exists market.fx_rate_snapshot", migration)
        self.assertIn("native_currency_code", migration)
        self.assertIn("market_value_native", migration)
        self.assertIn("fx_rate_to_base", migration)
        self.assertIn("fx_rate_snapshot_id", migration)
        self.assertIn("('KR', 'Korea Equities', 'KR', 'KRW', 'Asia/Seoul', true)", seed)
        self.assertIn("('KR', 'XKRX', 'Korea Exchange', 'Asia/Seoul', true)", seed)


if __name__ == "__main__":
    unittest.main()
