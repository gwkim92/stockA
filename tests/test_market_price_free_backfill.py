from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

from stockanalysis.operations.market_price_free_backfill import (
    load_market_price_provider_budget_status,
    load_market_price_watchlist,
    resolve_latest_completed_us_market_day,
    resolve_market_price_freshness_date,
    run_market_price_daily_from_env,
    run_market_price_free_backfill,
)


class MarketPriceFreeBackfillTests(unittest.TestCase):
    def test_load_market_price_watchlist_deduplicates_and_preserves_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            watchlist = Path(tmpdir) / "watchlist.csv"
            watchlist.write_text(
                "symbol,note\n aapl ,core\nMSFT,core\nAAPL,duplicate\nnvda,ai\n",
                encoding="utf-8",
            )

            symbols = load_market_price_watchlist(watchlist)

        self.assertEqual([symbol.symbol for symbol in symbols], ["AAPL", "MSFT", "NVDA"])

    def test_load_market_price_watchlist_rejects_missing_symbol_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            watchlist = Path(tmpdir) / "watchlist.csv"
            watchlist.write_text("ticker\nAAPL\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "symbol"):
                load_market_price_watchlist(watchlist)

    def test_load_market_price_provider_budget_status_returns_not_configured_without_path(self) -> None:
        status = load_market_price_provider_budget_status(
            ledger_path=None,
            budget_date=date(2026, 5, 17),
        )

        self.assertEqual(status["status"], "not_configured")
        self.assertEqual(status["provider"], "alpha_vantage")
        self.assertNotIn("ledger_path", status)

    def test_load_market_price_provider_budget_status_returns_valid_ledger_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = Path(tmpdir) / "ledger.json"
            ledger.write_text(
                json.dumps(
                    {
                        "version": "market-price-provider-budget-v1",
                        "provider": "alpha_vantage",
                        "days": {
                            "2026-05-17": {
                                "daily_budget": 25,
                                "used_request_count": 3,
                                "runs": [
                                    {
                                        "started_at": "2026-05-17T05:46:37Z",
                                        "status": "completed",
                                        "requested_symbol_count": 5,
                                        "provider_request_count": 3,
                                        "budget_remaining_after": 22,
                                    }
                                ],
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            status = load_market_price_provider_budget_status(
                ledger_path=ledger,
                budget_date=date(2026, 5, 17),
            )

        self.assertEqual(status["status"], "configured")
        self.assertEqual(status["daily_budget"], 25)
        self.assertEqual(status["used_request_count"], 3)
        self.assertEqual(status["remaining_request_count"], 22)
        self.assertEqual(status["latest_run"]["status"], "completed")
        self.assertEqual(status["latest_run"]["provider_request_count"], 3)
        self.assertNotIn("ledger_path", status)

    def test_run_market_price_free_backfill_skips_without_calling_batch_when_budget_exhausted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            watchlist = tmp_path / "watchlist.csv"
            ledger = tmp_path / "ledger.json"
            watchlist.write_text("symbol\nAAPL\nMSFT\n", encoding="utf-8")
            ledger.write_text(
                json.dumps(
                    {
                        "version": "market-price-provider-budget-v1",
                        "provider": "alpha_vantage",
                        "days": {
                            "2026-05-17": {
                                "daily_budget": 1,
                                "used_request_count": 1,
                                "runs": [],
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            with patch("stockanalysis.operations.market_price_free_backfill.run_market_price_batch_upsert") as batch_mock:
                summary = run_market_price_free_backfill(
                    config=object(),
                    watchlist_path=watchlist,
                    ledger_path=ledger,
                    budget_date=date(2026, 5, 17),
                    daily_budget=1,
                    max_requests_per_run=25,
                )

        batch_mock.assert_not_called()
        self.assertEqual(summary["status"], "no_provider_request_budget")
        self.assertEqual(summary["budget_block_reason"], "daily_provider_budget_exhausted")
        self.assertEqual(summary["provider_request_count"], 0)
        self.assertEqual(summary["budget_remaining_before"], 0)
        self.assertEqual(summary["budget_remaining_after"], 0)
        self.assertEqual(summary["skipped_symbol_count"], 2)

    def test_run_market_price_free_backfill_caps_batch_by_remaining_budget_and_updates_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            watchlist = tmp_path / "watchlist.csv"
            ledger = tmp_path / "ledger.json"
            watchlist.write_text("symbol\nAAPL\nMSFT\nNVDA\n", encoding="utf-8")
            ledger.write_text(
                json.dumps(
                    {
                        "version": "market-price-provider-budget-v1",
                        "provider": "alpha_vantage",
                        "days": {
                            "2026-05-17": {
                                "daily_budget": 3,
                                "used_request_count": 2,
                                "runs": [],
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            with patch("stockanalysis.operations.market_price_free_backfill.run_market_price_batch_upsert") as batch_mock:
                batch_mock.return_value = {
                    "requested_symbol_count": 3,
                    "succeeded_symbol_count": 1,
                    "failed_symbol_count": 0,
                    "skipped_symbol_count": 2,
                    "provider_request_count": 1,
                    "total_bar_count": 100,
                    "results": [
                        {"symbol": "AAPL", "status": "succeeded", "bar_count": 100},
                        {"symbol": "MSFT", "status": "skipped", "reason": "request_budget_exhausted"},
                        {"symbol": "NVDA", "status": "skipped", "reason": "request_budget_exhausted"},
                    ],
                }

                summary = run_market_price_free_backfill(
                    config=object(),
                    watchlist_path=watchlist,
                    ledger_path=ledger,
                    budget_date=date(2026, 5, 17),
                    daily_budget=3,
                    max_requests_per_run=25,
                    throttle_seconds=1.0,
                    outputsize="compact",
                )
            persisted = json.loads(ledger.read_text(encoding="utf-8"))

        batch_mock.assert_called_once_with(
            ["AAPL", "MSFT", "NVDA"],
            config=unittest.mock.ANY,
            fixtures_dir=None,
            outputsize="compact",
            provider="alpha_vantage",
            throttle_seconds=1.0,
            max_requests_per_run=1,
            skip_if_fresh=False,
            freshness_date=None,
        )
        self.assertEqual(summary["status"], "completed")
        self.assertEqual(summary["provider_request_count"], 1)
        self.assertEqual(summary["budget_remaining_before"], 1)
        self.assertEqual(summary["budget_remaining_after"], 0)
        self.assertEqual(persisted["days"]["2026-05-17"]["used_request_count"], 3)
        self.assertEqual(len(persisted["days"]["2026-05-17"]["runs"]), 1)

    def test_run_market_price_free_backfill_passes_provider_to_batch_and_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            watchlist = tmp_path / "watchlist.csv"
            ledger = tmp_path / "twelve-ledger.json"
            watchlist.write_text("symbol\nAAPL\nMSFT\n", encoding="utf-8")

            with patch("stockanalysis.operations.market_price_free_backfill.run_market_price_batch_upsert") as batch_mock:
                batch_mock.return_value = {
                    "requested_symbol_count": 2,
                    "provider": "twelve_data",
                    "succeeded_symbol_count": 2,
                    "failed_symbol_count": 0,
                    "skipped_symbol_count": 0,
                    "provider_request_count": 2,
                    "total_bar_count": 4,
                    "results": [],
                }

                summary = run_market_price_free_backfill(
                    config=object(),
                    watchlist_path=watchlist,
                    ledger_path=ledger,
                    provider="twelvedata",
                    budget_date=date(2026, 5, 17),
                    daily_budget=800,
                    max_requests_per_run=10,
                    skip_if_fresh=True,
                    freshness_date=date(2026, 5, 15),
                )
            persisted = json.loads(ledger.read_text(encoding="utf-8"))

        batch_mock.assert_called_once_with(
            ["AAPL", "MSFT"],
            config=unittest.mock.ANY,
            fixtures_dir=None,
            outputsize=None,
            provider="twelve_data",
            throttle_seconds=1.0,
            max_requests_per_run=10,
            skip_if_fresh=True,
            freshness_date=date(2026, 5, 15),
        )
        self.assertEqual(summary["provider"], "twelve_data")
        self.assertEqual(summary["budget_remaining_after"], 798)
        self.assertEqual(persisted["provider"], "twelve_data")

    def test_budget_status_normalizes_provider_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = Path(tmpdir) / "twelve-ledger.json"
            ledger.write_text(
                json.dumps(
                    {
                        "version": "market-price-provider-budget-v1",
                        "provider": "twelve_data",
                        "days": {
                            "2026-05-17": {
                                "daily_budget": 800,
                                "used_request_count": 10,
                                "runs": [],
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            status = load_market_price_provider_budget_status(
                ledger_path=ledger,
                provider="12data",
                budget_date=date(2026, 5, 17),
            )

        self.assertEqual(status["status"], "configured")
        self.assertEqual(status["provider"], "twelve_data")
        self.assertEqual(status["remaining_request_count"], 790)

    def test_run_market_price_daily_from_env_uses_scheduler_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            watchlist = tmp_path / "watchlist.csv"
            ledger = tmp_path / "twelve-ledger.json"
            watchlist.write_text("symbol\nAAPL\nMSFT\n", encoding="utf-8")
            env = {
                "STOCKANALYSIS_MARKET_PRICE_PROVIDER": "12data",
                "STOCKANALYSIS_MARKET_PRICE_WATCHLIST_CSV": str(watchlist),
                "STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH": str(ledger),
                "STOCKANALYSIS_MARKET_PRICE_DAILY_BUDGET": "800",
                "STOCKANALYSIS_MARKET_PRICE_MAX_REQUESTS_PER_RUN": "50",
                "STOCKANALYSIS_MARKET_PRICE_THROTTLE_SECONDS": "8",
                "STOCKANALYSIS_MARKET_PRICE_OUTPUTSIZE": "100",
                "DATA_OPERATIONS_SCHEDULER_RUN_DATE": "2026-05-18",
            }

            with patch("stockanalysis.operations.market_price_free_backfill.run_market_price_free_backfill") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "market_price_free_backfill_run",
                    "status": "completed",
                    "failed_symbol_count": 0,
                    "provider_request_count": 0,
                }
                summary = run_market_price_daily_from_env(config=object(), env=env)

        self.assertEqual(summary["report_name"], "market_price_free_backfill_run")
        call_kwargs = runner_mock.call_args.kwargs
        self.assertEqual(call_kwargs["watchlist_path"], str(watchlist))
        self.assertEqual(call_kwargs["ledger_path"], str(ledger))
        self.assertEqual(call_kwargs["provider"], "twelve_data")
        self.assertEqual(call_kwargs["budget_date"], date(2026, 5, 18))
        self.assertEqual(call_kwargs["daily_budget"], 800)
        self.assertEqual(call_kwargs["max_requests_per_run"], 50)
        self.assertEqual(call_kwargs["throttle_seconds"], 8.0)
        self.assertEqual(call_kwargs["outputsize"], "100")
        self.assertTrue(call_kwargs["skip_if_fresh"])
        self.assertEqual(call_kwargs["freshness_date"], date(2026, 5, 18))
        self.assertEqual(summary["freshness_policy"], "latest_completed_us_market_day")
        self.assertEqual(summary["freshness_date_source"], "DATA_OPERATIONS_SCHEDULER_RUN_DATE")
        self.assertEqual(summary["freshness_date"], "2026-05-18")

    def test_resolve_latest_completed_us_market_day_uses_new_york_after_ready_time(self) -> None:
        target = resolve_latest_completed_us_market_day(
            reference_datetime=datetime(2026, 5, 19, 0, 30, tzinfo=timezone.utc),
        )

        self.assertEqual(target, date(2026, 5, 18))

    def test_resolve_latest_completed_us_market_day_backs_up_before_ready_and_weekends(self) -> None:
        target = resolve_latest_completed_us_market_day(
            reference_datetime=datetime(2026, 5, 18, 13, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(target, date(2026, 5, 15))

    def test_resolve_market_price_freshness_date_respects_explicit_env_override(self) -> None:
        resolved = resolve_market_price_freshness_date(
            env={
                "DATA_OPERATIONS_SCHEDULER_RUN_DATE": "2026-05-19",
                "DATA_OPERATIONS_SCHEDULER_MARKET_PRICE_FRESHNESS_DATE": "2026-05-18",
            }
        )

        self.assertEqual(resolved.freshness_date, date(2026, 5, 18))
        self.assertEqual(resolved.source, "DATA_OPERATIONS_SCHEDULER_MARKET_PRICE_FRESHNESS_DATE")

    def test_resolve_market_price_freshness_date_backs_up_configured_non_trading_date(self) -> None:
        resolved = resolve_market_price_freshness_date(
            env={
                "DATA_OPERATIONS_SCHEDULER_RUN_DATE": "2026-05-25",
                "DATA_OPERATIONS_SCHEDULER_MARKET_PRICE_NON_TRADING_DATES": "2026-05-25",
            }
        )

        self.assertEqual(resolved.freshness_date, date(2026, 5, 22))
        self.assertEqual(resolved.policy, "latest_completed_us_market_day")
        self.assertEqual(resolved.non_trading_dates, (date(2026, 5, 25),))

    def test_run_market_price_daily_from_env_without_run_date_uses_latest_completed_market_day(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            watchlist = tmp_path / "watchlist.csv"
            ledger = tmp_path / "twelve-ledger.json"
            watchlist.write_text("symbol\nAAPL\n", encoding="utf-8")
            env = {
                "STOCKANALYSIS_MARKET_PRICE_PROVIDER": "12data",
                "STOCKANALYSIS_MARKET_PRICE_WATCHLIST_CSV": str(watchlist),
                "STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH": str(ledger),
                "STOCKANALYSIS_MARKET_PRICE_DAILY_BUDGET": "800",
            }

            with patch("stockanalysis.operations.market_price_free_backfill.run_market_price_free_backfill") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "market_price_free_backfill_run",
                    "status": "completed",
                    "failed_symbol_count": 0,
                    "provider_request_count": 0,
                }
                summary = run_market_price_daily_from_env(
                    config=object(),
                    env=env,
                    reference_datetime=datetime(2026, 5, 19, 0, 30, tzinfo=timezone.utc),
                )

        call_kwargs = runner_mock.call_args.kwargs
        self.assertIsNone(call_kwargs["budget_date"])
        self.assertEqual(call_kwargs["freshness_date"], date(2026, 5, 18))
        self.assertEqual(summary["freshness_date_source"], "market_timezone_now")


if __name__ == "__main__":
    unittest.main()
