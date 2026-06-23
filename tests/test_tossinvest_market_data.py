from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from stockanalysis.ingest.models import FetchResponse
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.cli import main
from stockanalysis.operations.cli import _load_symbol_file
from stockanalysis.operations.tossinvest_market_data import (
    normalize_tossinvest_market_data_payload,
    render_tossinvest_market_data_upsert_sql,
    render_tossinvest_provider_comparison_sql,
    run_tossinvest_market_data_sync,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"
ROOT_DIR = Path(__file__).resolve().parents[1]


class FakeExecutor:
    def __init__(self) -> None:
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "insert into ops.pipeline_run" in sql:
            return "808"
        if "market.tossinvest_daily_candle_snapshot" in sql:
            return json.dumps(
                {
                    "calendar_count": 1,
                    "candle_bar_count": 2,
                    "stock_warning_count": 1,
                    "market_microdata_count": 1,
                    "canonical_kr_candle_count": 0,
                }
            )
        raise AssertionError(f"Unexpected SQL: {sql[:120]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


def sample_payload() -> dict[str, object]:
    return {
        "market_calendars": {
            "US": {
                "result": {
                    "date": "2026-06-23",
                    "isOpen": True,
                    "nextBusinessDay": "2026-06-24",
                }
            }
        },
        "candles": {
            "AAPL": json.loads((FIXTURES_DIR / "tossinvest_candles_1d_AAPL.json").read_text(encoding="utf-8"))
        },
        "stock_warnings": {
            "AAPL": {
                "result": {
                    "warnings": [
                        {"warningType": "VI_STATIC"},
                        {"warningType": "INVESTMENT_CAUTION"},
                    ]
                }
            }
        },
        "market_microdata": {
            "orderbooks": {
                "AAPL": {
                    "result": {
                        "currency": "USD",
                        "bestBidPrice": "199.90",
                        "bestAskPrice": "200.10",
                    }
                }
            },
            "trades": {
                "AAPL": {
                    "result": {
                        "trades": [
                            {"price": "200.00", "timestamp": "2026-06-23T15:30:00Z"},
                            {"price": "199.95", "timestamp": "2026-06-23T15:29:59Z"},
                        ]
                    }
                }
            },
            "price_limits": {
                "AAPL": {
                    "result": {
                        "upperLimitPrice": "260.00",
                        "lowerLimitPrice": "140.00",
                    }
                }
            },
        },
    }


class TossInvestMarketDataTests(unittest.TestCase):
    def test_normalizer_handles_candles_warnings_microdata_and_calendar(self) -> None:
        result = normalize_tossinvest_market_data_payload(
            sample_payload(),
            symbols=("AAPL",),
            market_code="US",
            sync_mode="all",
            as_of_date=date(2026, 6, 23),
            credentials_configured=True,
        )

        self.assertEqual(result.market_code, "US")
        self.assertEqual(len(result.calendars), 1)
        self.assertEqual(result.calendars[0].next_business_day.isoformat(), "2026-06-24")
        self.assertEqual(len(result.candles), 2)
        self.assertEqual(result.candles[0].currency_code, "USD")
        self.assertEqual(result.warnings[0].warning_count, 2)
        self.assertEqual(result.microdata[0].trade_count, 2)
        self.assertEqual(str(result.microdata[0].best_bid_price), "199.90")
        dumped = json.dumps(result.report(), sort_keys=True)
        self.assertNotIn("Authorization", dumped)
        self.assertIn("read_only_no_order", dumped)

    def test_normalizer_handles_live_market_calendar_object_dates(self) -> None:
        payload = sample_payload()
        payload["market_calendars"] = {
            "US": {
                "result": {
                    "today": {
                        "date": "2026-06-23",
                        "dayMarket": {
                            "startTime": "2026-06-23T09:00:00.000+09:00",
                            "endTime": "2026-06-23T17:00:00.000+09:00",
                        },
                    },
                    "nextBusinessDay": {
                        "date": "2026-06-24",
                        "dayMarket": {
                            "startTime": "2026-06-24T09:00:00.000+09:00",
                            "endTime": "2026-06-24T17:00:00.000+09:00",
                        },
                    },
                    "previousBusinessDay": {"date": "2026-06-22"},
                }
            }
        }

        result = normalize_tossinvest_market_data_payload(
            payload,
            symbols=("AAPL",),
            market_code="US",
            sync_mode="daily_candles",
            as_of_date=date(2026, 6, 23),
            credentials_configured=True,
        )

        self.assertEqual(result.calendars[0].calendar_date.isoformat(), "2026-06-23")
        self.assertEqual(result.calendars[0].next_business_day.isoformat(), "2026-06-24")
        self.assertEqual(len(result.candles), 2)

    def test_render_upsert_writes_snapshots_and_only_kr_canonical_prices(self) -> None:
        result = normalize_tossinvest_market_data_payload(
            sample_payload(),
            symbols=("AAPL",),
            market_code="US",
            sync_mode="all",
            as_of_date=date(2026, 6, 23),
            credentials_configured=True,
        )

        sql = render_tossinvest_market_data_upsert_sql(result, source_run_id=808)

        self.assertIn("market.tossinvest_daily_candle_snapshot", sql)
        self.assertIn("market.tossinvest_stock_warning_snapshot", sql)
        self.assertIn("market.tossinvest_market_microdata_snapshot", sql)
        self.assertIn("market.daily_price_bar", sql)
        self.assertIn("where input_candles.market_code = 'KR'", sql)
        self.assertIn("'tossinvest'", sql)

    def test_execute_fixture_report_is_secret_free_and_does_not_submit_orders(self) -> None:
        executor = FakeExecutor()
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_path = Path(temp_dir) / "tossinvest_market_data_AAPL.json"
            fixture_path.write_text(json.dumps(sample_payload()), encoding="utf-8")
            report = run_tossinvest_market_data_sync(
                config=RuntimeConfig(
                    tossinvest_client_id="client-id-test",
                    tossinvest_client_secret="client-secret-test",
                    psql_command="psql",
                ),
                symbols=["AAPL"],
                market_code="US",
                sync_mode="all",
                as_of_date=date(2026, 6, 23),
                fixture_json_path=str(fixture_path),
                execute=True,
                dry_run=False,
                executor=executor,
            )

        dumped = json.dumps(report, sort_keys=True)
        self.assertEqual(report["status"], "succeeded")
        self.assertEqual(report["write_result"]["candle_bar_count"], 2)
        self.assertFalse(report["broker_submit_allowed"])
        self.assertFalse(report["submitted_to_broker"])
        self.assertNotIn("client-secret-test", dumped)
        self.assertNotIn("Authorization", dumped)

    def test_live_sync_skips_symbol_requests_when_toss_calendar_is_closed(self) -> None:
        calls: list[str] = []

        def fake_request_executor(request):
            calls.append(request.dataset_name)
            if request.dataset_name == "oauth_token":
                return FetchResponse(
                    status_code=200,
                    content_type="application/json",
                    body=json.dumps({"access_token": "access-token-test"}).encode("utf-8"),
                )
            self.assertEqual(request.dataset_name, "market_calendar_us")
            return FetchResponse(
                status_code=200,
                content_type="application/json",
                body=json.dumps({"result": {"date": "2026-06-23", "isOpen": False}}).encode("utf-8"),
            )

        report = run_tossinvest_market_data_sync(
            config=RuntimeConfig(
                tossinvest_client_id="client-id-test",
                tossinvest_client_secret="client-secret-test",
                psql_command="psql",
            ),
            symbols=["AAPL"],
            market_code="US",
            sync_mode="microdata",
            as_of_date=date(2026, 6, 23),
            dry_run=True,
            execute=False,
            request_executor=fake_request_executor,
        )

        self.assertEqual(calls, ["oauth_token", "market_calendar_us"])
        self.assertEqual(report["status"], "skipped_market_closed")
        self.assertEqual(report["provider_skip_reason"], "market_closed_by_toss_calendar")
        self.assertEqual(report["market_microdata_symbol_count"], 0)
        self.assertFalse(report["broker_submit_allowed"])

    def test_provider_comparison_sql_keeps_toss_as_shadow_until_threshold_passes(self) -> None:
        sql = render_tossinvest_provider_comparison_sql(
            symbols=("AAPL", "NVDA"),
            comparison_date=date(2026, 6, 23),
            lookback_days=5,
            max_diff_bps=__import__("decimal").Decimal("50"),
            source_run_id=909,
        )

        self.assertIn("market.tossinvest_daily_candle_snapshot", sql)
        self.assertIn("market.tossinvest_provider_comparison_snapshot", sql)
        self.assertIn("upserted as", sql)
        self.assertIn("'written_count'", sql)
        self.assertIn("candidate_ready", sql)
        self.assertIn("conflict_review_required", sql)

    def test_cli_dry_run_is_secret_free_and_accepts_fixture(self) -> None:
        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_path = Path(temp_dir) / "tossinvest_market_data_AAPL.json"
            fixture_path.write_text(json.dumps(sample_payload()), encoding="utf-8")
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "tossinvest-market-data-sync-run",
                        "--symbol",
                        "AAPL",
                        "--market-code",
                        "US",
                        "--sync-mode",
                        "all",
                        "--as-of-date",
                        "2026-06-23",
                        "--fixture-json",
                        str(fixture_path),
                        "--dry-run",
                    ]
                )

        payload = json.loads(stdout.getvalue())
        dumped = json.dumps(payload, sort_keys=True)
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["report_name"], "tossinvest_market_data_sync")
        self.assertFalse(payload["broker_submit_allowed"])
        self.assertNotIn("client-secret", dumped)

    def test_provider_comparison_cli_dry_run_keeps_canonical_promotion_blocked(self) -> None:
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main(
                [
                    "tossinvest-provider-comparison-run",
                    "--symbol",
                    "AAPL",
                    "--comparison-date",
                    "2026-06-23",
                ]
            )

        payload = json.loads(stdout.getvalue())
        dumped = json.dumps(payload, sort_keys=True)
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["report_name"], "tossinvest_provider_comparison")
        self.assertEqual(payload["status"], "not_executed")
        self.assertTrue(payload["canonical_promotion_blocked"])
        self.assertFalse(payload["broker_submit_allowed"])
        self.assertNotIn("Authorization", dumped)

    def test_symbol_file_loader_skips_newline_header(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            symbols_file = Path(temp_dir) / "symbols.txt"
            symbols_file.write_text("symbol\nAAPL\nNVDA\n", encoding="utf-8")

            symbols = _load_symbol_file(symbols_file)

        self.assertEqual(symbols, ["AAPL", "NVDA"])

    def test_migration_adds_toss_market_data_tables_and_provider_provenance(self) -> None:
        migration = (ROOT_DIR / "db" / "migrations" / "0034_tossinvest_market_data_agent_context.sql").read_text(
            encoding="utf-8"
        )

        self.assertIn("add column if not exists provider", migration)
        self.assertIn("market.tossinvest_daily_candle_snapshot", migration)
        self.assertIn("market.tossinvest_market_microdata_snapshot", migration)
        self.assertIn("market.tossinvest_provider_comparison_snapshot", migration)


if __name__ == "__main__":
    unittest.main()
