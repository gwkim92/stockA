from __future__ import annotations

import json
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

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
        self.assertNotIn("client-secret-test", dumped)
        self.assertNotIn("account-seq-secret-test", dumped)
        self.assertNotIn("1234567890", dumped)
        self.assertTrue(any("config_json" in sql and "succeeded" in sql for sql in executor.non_query_sql))

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
