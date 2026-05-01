from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from datetime import date
from urllib.parse import unquote
from unittest.mock import patch

from stockanalysis.ingest.cli import main


class IngestCliTests(unittest.TestCase):
    def test_list_sources(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["list-sources"])
        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("sec:", output)
        self.assertIn("fred:", output)
        self.assertIn("alpha_vantage:", output)

    def test_build_request_allows_placeholder_credentials(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(
                [
                    "build-request",
                    "fred",
                    "series_observations",
                    "--param",
                    "series_id=CPIAUCSL",
                ]
            )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertIn("<env:STOCKANALYSIS_FRED_API_KEY>", unquote(payload["url"]))

    def test_fetch_requires_credentials(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(
                [
                    "fetch",
                    "fred",
                    "series_observations",
                    "--param",
                    "series_id=CPIAUCSL",
                ]
            )
        self.assertEqual(exit_code, 1)
        self.assertIn("Missing required environment variable", stdout.getvalue())

    def test_build_request_can_use_supplied_env(self) -> None:
        stdout = io.StringIO()
        with patch.dict(
            "os.environ",
            {"STOCKANALYSIS_SEC_USER_AGENT": "stockanalysis-test contact@example.com"},
            clear=False,
        ):
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "build-request",
                        "sec",
                        "submissions",
                        "--param",
                        "cik=320193",
                        "--require-credentials",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertIn("CIK0000320193.json", payload["url"])
        self.assertEqual(payload["headers"]["User-Agent"], "stockanalysis-test contact@example.com")

    def test_macro_upsert_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_macro_upsert") as run_macro_upsert_mock:
            run_macro_upsert_mock.return_value = {
                "run_id": 42,
                "series_code": "CPIAUCSL",
                "observation_count": 2,
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "macro-upsert",
                        "--series-id",
                        "CPIAUCSL",
                        "--series-json",
                        "tests/fixtures/fred_series_CPIAUCSL.json",
                        "--observations-json",
                        "tests/fixtures/fred_observations_CPIAUCSL.json",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 42)
        self.assertEqual(payload["series_code"], "CPIAUCSL")

    def test_macro_batch_upsert_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_macro_batch_upsert") as batch_mock:
            batch_mock.return_value = {
                "requested_series_count": 2,
                "succeeded_series_count": 2,
                "failed_series_count": 0,
                "results": [],
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "macro-batch-upsert",
                        "--series-id",
                        "CPIAUCSL",
                        "--series-id",
                        "FEDFUNDS",
                        "--fixtures-dir",
                        "tests/fixtures",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["requested_series_count"], 2)
        self.assertEqual(payload["failed_series_count"], 0)

    def test_macro_run_history_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.load_macro_run_history") as history_mock:
            history_mock.return_value = {
                "pipeline_name": "macro_upsert",
                "run_count": 2,
                "status_counts": {"succeeded": 2},
                "runs": [],
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "macro-run-history",
                        "--limit",
                        "5",
                        "--status",
                        "succeeded",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["pipeline_name"], "macro_upsert")
        self.assertEqual(payload["run_count"], 2)

    def test_market_price_upsert_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_market_price_upsert") as upsert_mock:
            upsert_mock.return_value = {
                "run_id": 88,
                "symbol": "AAPL",
                "bar_count": 2,
                "instrument_symbol": "AAPL",
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "market-price-upsert",
                        "--symbol",
                        "AAPL",
                        "--prices-json",
                        "tests/fixtures/alpha_vantage_daily_adjusted_AAPL.json",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 88)
        self.assertEqual(payload["bar_count"], 2)

    def test_market_price_batch_upsert_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_market_price_batch_upsert") as upsert_mock:
            upsert_mock.return_value = {
                "requested_symbol_count": 2,
                "succeeded_symbol_count": 2,
                "failed_symbol_count": 0,
                "results": [],
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "market-price-batch-upsert",
                        "--symbol",
                        "AAPL",
                        "--symbol",
                        "MSFT",
                        "--fixtures-dir",
                        "tests/fixtures",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["requested_symbol_count"], 2)
        self.assertEqual(payload["failed_symbol_count"], 0)

    def test_market_universe_bootstrap_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_market_universe_bootstrap") as bootstrap_mock:
            bootstrap_mock.return_value = {
                "run_id": 118,
                "selected_record_count": 2,
                "requested_exchanges": ["Nasdaq", "NYSE"],
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "market-universe-bootstrap",
                        "--company-tickers-json",
                        "tests/fixtures/sec_company_tickers_exchange_sample.json",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 118)
        self.assertEqual(payload["selected_record_count"], 2)

    def test_market_price_universe_backfill_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_market_price_universe_backfill") as backfill_mock:
            backfill_mock.return_value = {
                "selected_symbol_count": 2,
                "requested_symbol_count": 2,
                "failed_symbol_count": 0,
                "results": [],
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "market-price-universe-backfill",
                        "--fixtures-dir",
                        "tests/fixtures",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["selected_symbol_count"], 2)
        self.assertEqual(payload["failed_symbol_count"], 0)

    def test_portfolio_position_snapshot_upsert_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_position_snapshot_upsert") as upsert_mock:
            upsert_mock.return_value = {
                "run_id": 181,
                "portfolio_id": 3001,
                "position_count": 1,
                "linked_thesis_count": 1,
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "portfolio-position-snapshot-upsert",
                        "--positions-csv",
                        "tests/fixtures/portfolio_positions_long_term_paper.csv",
                        "--portfolio-name",
                        "Long Term Paper",
                        "--snapshot-date",
                        "2024-11-01",
                        "--strategy-name",
                        "long_term_core",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 181)
        self.assertEqual(payload["portfolio_id"], 3001)
        self.assertEqual(payload["position_count"], 1)
        self.assertEqual(payload["linked_thesis_count"], 1)

    def test_strategy_universe_slice_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_strategy_universe_slice") as slice_mock:
            slice_mock.return_value = {
                "run_id": 119,
                "universe_batch_id": 1001,
                "member_count": 2,
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "strategy-universe-slice",
                        "--as-of-date",
                        "2024-11-01",
                        "--strategy-name",
                        "long_term_core",
                        "--horizon-type",
                        "long_term",
                        "--universe-version",
                        "fixture-v1",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 119)
        self.assertEqual(payload["member_count"], 2)

    def test_market_feature_snapshot_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_market_feature_snapshot") as snapshot_mock:
            snapshot_mock.return_value = {
                "run_id": 129,
                "universe_batch_id": 1001,
                "instrument_count": 2,
                "feature_row_count": 10,
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "market-feature-snapshot",
                        "--as-of-date",
                        "2024-11-01",
                        "--strategy-name",
                        "long_term_core",
                        "--horizon-type",
                        "long_term",
                        "--universe-version",
                        "fixture-v1",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 129)
        self.assertEqual(payload["feature_row_count"], 10)

    def test_instrument_theme_enrichment_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_instrument_theme_enrichment") as enrichment_mock:
            enrichment_mock.return_value = {
                "run_id": 139,
                "universe_batch_id": 1001,
                "selected_instrument_count": 2,
                "membership_count": 1,
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "instrument-theme-enrichment",
                        "--as-of-date",
                        "2024-11-01",
                        "--strategy-name",
                        "long_term_core",
                        "--horizon-type",
                        "long_term",
                        "--universe-version",
                        "fixture-v1",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 139)
        self.assertEqual(payload["membership_count"], 1)

    def test_cycle_state_snapshot_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_cycle_state_snapshot") as snapshot_mock:
            snapshot_mock.return_value = {
                "run_id": 149,
                "universe_batch_id": 1001,
                "node_count": 1,
                "cycle_state_counts": {"forming": 1},
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "cycle-state-snapshot",
                        "--as-of-date",
                        "2024-11-01",
                        "--strategy-name",
                        "long_term_core",
                        "--horizon-type",
                        "long_term",
                        "--universe-version",
                        "fixture-v1",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 149)
        self.assertEqual(payload["node_count"], 1)

    def test_recommendation_bootstrap_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_recommendation_bootstrap") as bootstrap_mock:
            bootstrap_mock.return_value = {
                "run_id": 159,
                "batch_id": 2001,
                "recommendation_count": 1,
                "bucket_counts": {"watch": 1},
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "recommendation-bootstrap",
                        "--as-of-date",
                        "2024-11-01",
                        "--strategy-name",
                        "long_term_core",
                        "--horizon-type",
                        "long_term",
                        "--universe-version",
                        "fixture-v1",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 159)
        self.assertEqual(payload["recommendation_count"], 1)

    def test_thesis_bootstrap_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_thesis_bootstrap") as bootstrap_mock:
            bootstrap_mock.return_value = {
                "run_id": 169,
                "batch_id": 2001,
                "thesis_count": 1,
                "linked_recommendation_count": 1,
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "thesis-bootstrap",
                        "--as-of-date",
                        "2024-11-01",
                        "--strategy-name",
                        "long_term_core",
                        "--horizon-type",
                        "long_term",
                        "--universe-version",
                        "fixture-v1",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 169)
        self.assertEqual(payload["thesis_count"], 1)
        self.assertEqual(payload["linked_recommendation_count"], 1)

    def test_thesis_review_bootstrap_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_thesis_review_bootstrap") as bootstrap_mock:
            bootstrap_mock.return_value = {
                "run_id": 179,
                "batch_id": 2001,
                "review_count": 1,
                "action_counts": {"watch": 1},
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "thesis-review-bootstrap",
                        "--as-of-date",
                        "2024-11-01",
                        "--strategy-name",
                        "long_term_core",
                        "--horizon-type",
                        "long_term",
                        "--universe-version",
                        "fixture-v1",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 179)
        self.assertEqual(payload["review_count"], 1)
        self.assertEqual(payload["action_counts"], {"watch": 1})

    def test_portfolio_review_bootstrap_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_portfolio_review_bootstrap") as bootstrap_mock:
            bootstrap_mock.return_value = {
                "run_id": 189,
                "portfolio_review_id": 6001,
                "review_item_count": 1,
                "action_counts": {"monitor": 1},
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "portfolio-review-bootstrap",
                        "--portfolio-name",
                        "Long Term Paper",
                        "--as-of-date",
                        "2024-11-01",
                        "--strategy-name",
                        "long_term_core",
                        "--horizon-type",
                        "long_term",
                        "--universe-version",
                        "fixture-v1",
                        "--coverage-measurement-end-date",
                        "2024-12-02",
                    ]
                )
        self.assertEqual(exit_code, 0)
        self.assertEqual(bootstrap_mock.call_args.kwargs["coverage_measurement_end_date"], date(2024, 12, 2))
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 189)
        self.assertEqual(payload["portfolio_review_id"], 6001)
        self.assertEqual(payload["review_item_count"], 1)
        self.assertEqual(payload["action_counts"], {"monitor": 1})

    def test_portfolio_review_run_history_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.load_portfolio_review_run_history") as history_mock:
            history_mock.return_value = {
                "report_name": "portfolio_review_run_history",
                "portfolio_name": "Long Term Paper",
                "review_count": 1,
                "action_counts": {"needs_thesis_review": 1},
                "reviews": [],
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "portfolio-review-run-history",
                        "--portfolio-name",
                        "Long Term Paper",
                        "--limit",
                        "5",
                        "--review-source",
                        "deterministic_bootstrap",
                        "--risk-level",
                        "watch",
                        "--action",
                        "needs_thesis_review",
                    ]
                )
        self.assertEqual(exit_code, 0)
        self.assertEqual(history_mock.call_args.kwargs["portfolio_name"], "Long Term Paper")
        self.assertEqual(history_mock.call_args.kwargs["limit"], 5)
        self.assertEqual(history_mock.call_args.kwargs["review_source"], "deterministic_bootstrap")
        self.assertEqual(history_mock.call_args.kwargs["risk_level"], "watch")
        self.assertEqual(history_mock.call_args.kwargs["action"], "needs_thesis_review")
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["report_name"], "portfolio_review_run_history")
        self.assertEqual(payload["review_count"], 1)

    def test_portfolio_remediation_queue_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.load_portfolio_remediation_queue") as queue_mock:
            queue_mock.return_value = {
                "report_name": "portfolio_remediation_queue",
                "portfolio_name": "Long Term Paper",
                "queue_item_count": 1,
                "remediation_type_counts": {"thesis_remediation": 1},
                "items": [],
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "portfolio-remediation-queue",
                        "--portfolio-name",
                        "Long Term Paper",
                        "--limit",
                        "5",
                        "--review-source",
                        "deterministic_bootstrap",
                        "--action",
                        "needs_thesis_review",
                        "--remediation-type",
                        "thesis_remediation",
                    ]
                )
        self.assertEqual(exit_code, 0)
        self.assertEqual(queue_mock.call_args.kwargs["portfolio_name"], "Long Term Paper")
        self.assertEqual(queue_mock.call_args.kwargs["limit"], 5)
        self.assertEqual(queue_mock.call_args.kwargs["review_source"], "deterministic_bootstrap")
        self.assertEqual(queue_mock.call_args.kwargs["action"], "needs_thesis_review")
        self.assertEqual(queue_mock.call_args.kwargs["remediation_type"], "thesis_remediation")
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["report_name"], "portfolio_remediation_queue")
        self.assertEqual(payload["queue_item_count"], 1)

    def test_portfolio_remediation_ticket_bootstrap_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_portfolio_remediation_ticket_bootstrap") as ticket_mock:
            ticket_mock.return_value = {
                "report_name": "portfolio_remediation_ticket_bootstrap",
                "portfolio_name": "Long Term Paper",
                "ticket_count": 1,
                "remediation_type_counts": {"thesis_remediation": 1},
                "tickets": [],
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "portfolio-remediation-ticket-bootstrap",
                        "--portfolio-name",
                        "Long Term Paper",
                        "--limit",
                        "5",
                        "--review-source",
                        "deterministic_bootstrap",
                        "--action",
                        "needs_thesis_review",
                        "--remediation-type",
                        "thesis_remediation",
                    ]
                )
        self.assertEqual(exit_code, 0)
        self.assertEqual(ticket_mock.call_args.kwargs["portfolio_name"], "Long Term Paper")
        self.assertEqual(ticket_mock.call_args.kwargs["limit"], 5)
        self.assertEqual(ticket_mock.call_args.kwargs["review_source"], "deterministic_bootstrap")
        self.assertEqual(ticket_mock.call_args.kwargs["action"], "needs_thesis_review")
        self.assertEqual(ticket_mock.call_args.kwargs["remediation_type"], "thesis_remediation")
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["report_name"], "portfolio_remediation_ticket_bootstrap")
        self.assertEqual(payload["ticket_count"], 1)

    def test_portfolio_remediation_ticket_report_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.load_portfolio_remediation_ticket_report") as report_mock:
            report_mock.return_value = {
                "report_name": "portfolio_remediation_ticket_report",
                "portfolio_name": "Long Term Paper",
                "ticket_count": 1,
                "status_counts": {"open": 1},
                "tickets": [],
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "portfolio-remediation-ticket-report",
                        "--portfolio-name",
                        "Long Term Paper",
                        "--limit",
                        "5",
                        "--status",
                        "open",
                        "--action",
                        "needs_thesis_review",
                        "--remediation-type",
                        "thesis_remediation",
                        "--suggested-runner",
                        "thesis_or_position_link_review",
                    ]
                )
        self.assertEqual(exit_code, 0)
        self.assertEqual(report_mock.call_args.kwargs["portfolio_name"], "Long Term Paper")
        self.assertEqual(report_mock.call_args.kwargs["limit"], 5)
        self.assertEqual(report_mock.call_args.kwargs["status"], "open")
        self.assertEqual(report_mock.call_args.kwargs["action"], "needs_thesis_review")
        self.assertEqual(report_mock.call_args.kwargs["remediation_type"], "thesis_remediation")
        self.assertEqual(report_mock.call_args.kwargs["suggested_runner"], "thesis_or_position_link_review")
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["report_name"], "portfolio_remediation_ticket_report")
        self.assertEqual(payload["ticket_count"], 1)

    def test_portfolio_remediation_ticket_update_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_portfolio_remediation_ticket_update") as update_mock:
            update_mock.return_value = {
                "report_name": "portfolio_remediation_ticket_update",
                "portfolio_name": "Long Term Paper",
                "ticket_id": 7001,
                "status": "resolved",
                "updated_count": 1,
                "ticket": {"symbol": "BABA", "status": "resolved"},
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "portfolio-remediation-ticket-update",
                        "--portfolio-name",
                        "Long Term Paper",
                        "--ticket-id",
                        "7001",
                        "--status",
                        "resolved",
                    ]
                )
        self.assertEqual(exit_code, 0)
        self.assertEqual(update_mock.call_args.kwargs["portfolio_name"], "Long Term Paper")
        self.assertEqual(update_mock.call_args.kwargs["ticket_id"], 7001)
        self.assertEqual(update_mock.call_args.kwargs["status"], "resolved")
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["report_name"], "portfolio_remediation_ticket_update")
        self.assertEqual(payload["updated_count"], 1)

    def test_portfolio_remediation_daily_run_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_portfolio_remediation_daily_automation") as daily_mock:
            daily_mock.return_value = {
                "report_name": "portfolio_remediation_daily_automation",
                "portfolio_name": "Long Term Paper",
                "ticket_report": {"ticket_count": 1},
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "portfolio-remediation-daily-run",
                        "--portfolio-name",
                        "Long Term Paper",
                        "--as-of-date",
                        "2024-11-01",
                        "--strategy-name",
                        "long_term_core",
                        "--horizon-type",
                        "long_term",
                        "--universe-version",
                        "fixture-v1",
                        "--coverage-measurement-end-date",
                        "2024-12-02",
                        "--ticket-limit",
                        "5",
                        "--ticket-status",
                        "open",
                    ]
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(daily_mock.call_args.kwargs["portfolio_name"], "Long Term Paper")
        self.assertEqual(daily_mock.call_args.kwargs["as_of_date"], date(2024, 11, 1))
        self.assertEqual(daily_mock.call_args.kwargs["coverage_measurement_end_date"], date(2024, 12, 2))
        self.assertEqual(daily_mock.call_args.kwargs["ticket_limit"], 5)
        self.assertEqual(daily_mock.call_args.kwargs["ticket_status"], "open")
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["report_name"], "portfolio_remediation_daily_automation")
        self.assertEqual(payload["ticket_report"]["ticket_count"], 1)

    def test_performance_outcome_bootstrap_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_performance_outcome_bootstrap") as bootstrap_mock:
            bootstrap_mock.return_value = {
                "run_id": 199,
                "batch_id": 2001,
                "recommendation_outcome_count": 1,
                "thesis_outcome_count": 1,
                "label_counts": {"positive": 1},
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "performance-outcome-bootstrap",
                        "--as-of-date",
                        "2024-11-01",
                        "--measurement-end-date",
                        "2024-11-04",
                        "--strategy-name",
                        "long_term_core",
                        "--horizon-type",
                        "long_term",
                        "--universe-version",
                        "fixture-v1",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 199)
        self.assertEqual(payload["recommendation_outcome_count"], 1)
        self.assertEqual(payload["thesis_outcome_count"], 1)
        self.assertEqual(payload["label_counts"], {"positive": 1})

    def test_performance_outcome_batch_bootstrap_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_performance_outcome_batch_bootstrap") as bootstrap_mock:
            bootstrap_mock.return_value = {
                "measurement_end_dates": ["2024-11-04", "2024-12-02"],
                "requested_measurement_count": 2,
                "succeeded_measurement_count": 2,
                "recommendation_outcome_count": 2,
                "thesis_outcome_count": 2,
                "label_counts": {"outperform": 2},
                "results": [],
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "performance-outcome-batch-bootstrap",
                        "--as-of-date",
                        "2024-11-01",
                        "--measurement-end-date",
                        "2024-11-04",
                        "--horizon-day",
                        "31",
                        "--strategy-name",
                        "long_term_core",
                        "--horizon-type",
                        "long_term",
                        "--universe-version",
                        "fixture-v1",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["requested_measurement_count"], 2)
        self.assertEqual(payload["succeeded_measurement_count"], 2)
        self.assertEqual(payload["recommendation_outcome_count"], 2)
        self.assertEqual(payload["label_counts"], {"outperform": 2})

    def test_performance_outcome_schedule_bootstrap_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_performance_outcome_schedule_bootstrap") as bootstrap_mock:
            bootstrap_mock.return_value = {
                "run_id": 205,
                "candidate_count": 2,
                "succeeded_candidate_count": 2,
                "failed_candidate_count": 0,
                "recommendation_outcome_count": 2,
                "thesis_outcome_count": 2,
                "results": [],
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "performance-outcome-schedule-bootstrap",
                        "--due-on-date",
                        "2024-12-02",
                        "--horizon-day",
                        "3",
                        "--horizon-day",
                        "31",
                        "--strategy-name",
                        "long_term_core",
                        "--horizon-type",
                        "long_term",
                        "--universe-version",
                        "fixture-v1",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 205)
        self.assertEqual(payload["candidate_count"], 2)
        self.assertEqual(payload["succeeded_candidate_count"], 2)
        self.assertEqual(payload["failed_candidate_count"], 0)

    def test_performance_outcome_schedule_bootstrap_cli_returns_failure_when_candidates_fail(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_performance_outcome_schedule_bootstrap") as bootstrap_mock:
            bootstrap_mock.return_value = {
                "run_id": 206,
                "candidate_count": 1,
                "succeeded_candidate_count": 0,
                "failed_candidate_count": 1,
                "results": [{"status": "failed"}],
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "performance-outcome-schedule-bootstrap",
                        "--due-on-date",
                        "2024-12-02",
                    ]
                )
        self.assertEqual(exit_code, 1)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["failed_candidate_count"], 1)

    def test_portfolio_attribution_bootstrap_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_portfolio_attribution_bootstrap") as bootstrap_mock:
            bootstrap_mock.return_value = {
                "run_id": 209,
                "attribution_run_id": 6101,
                "component_count": 3,
                "component_type_counts": {"security_selection": 1, "theme_exposure": 1, "cash_timing": 1},
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "portfolio-attribution-bootstrap",
                        "--portfolio-name",
                        "Long Term Paper",
                        "--snapshot-date",
                        "2024-11-01",
                        "--measurement-end-date",
                        "2024-12-02",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 209)
        self.assertEqual(payload["attribution_run_id"], 6101)
        self.assertEqual(payload["component_count"], 3)

    def test_portfolio_outcome_coverage_report_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.load_portfolio_outcome_coverage_report") as report_mock:
            report_mock.return_value = {
                "portfolio_name": "Long Term Paper",
                "position_count": 2,
                "status_counts": {"covered": 1, "missing_outcome": 0, "missing_thesis": 1, "missing_weight": 0},
                "covered_weight": "0.0500",
                "cash_weight": "0.9200",
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "portfolio-outcome-coverage-report",
                        "--portfolio-name",
                        "Long Term Paper",
                        "--snapshot-date",
                        "2024-11-01",
                        "--measurement-end-date",
                        "2024-12-02",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["portfolio_name"], "Long Term Paper")
        self.assertEqual(payload["position_count"], 2)
        self.assertEqual(payload["status_counts"]["covered"], 1)

    def test_sec_filings_upsert_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_sec_filings_upsert") as upsert_mock:
            upsert_mock.return_value = {
                "run_id": 91,
                "cik": "0000320193",
                "filing_count": 2,
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "sec-filings-upsert",
                        "--cik",
                        "320193",
                        "--submissions-json",
                        "tests/fixtures/sec_submissions_CIK0000320193.json",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 91)
        self.assertEqual(payload["filing_count"], 2)

    def test_sec_companyfacts_upsert_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_sec_companyfacts_upsert") as upsert_mock:
            upsert_mock.return_value = {
                "run_id": 92,
                "cik": "0000320193",
                "fact_count": 4,
                "instrument_symbol": "AAPL",
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "sec-companyfacts-upsert",
                        "--cik",
                        "320193",
                        "--companyfacts-json",
                        "tests/fixtures/sec_companyfacts_CIK0000320193.json",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 92)
        self.assertEqual(payload["fact_count"], 4)

    def test_sec_filing_raw_fetch_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_sec_filing_raw_fetch") as fetch_mock:
            fetch_mock.return_value = {
                "run_id": 144,
                "document_id": 55,
                "status": "succeeded",
                "artifact_path": "/tmp/sec/aapl-20240928.htm",
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "sec-filing-raw-fetch",
                        "--external-document-id",
                        "0000320193-24-000123",
                        "--body-file",
                        "tests/fixtures/sec_filing_aapl_20240928_10k.html",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 144)
        self.assertEqual(payload["status"], "succeeded")

    def test_sec_filings_event_extract_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_sec_filings_event_extract") as extract_mock:
            extract_mock.return_value = {
                "run_id": 188,
                "event_type": "sec_annual_report_filed",
                "external_document_id": "0000320193-24-000123",
                "status": "succeeded",
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "sec-filings-event-extract",
                        "--external-document-id",
                        "0000320193-24-000123",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 188)
        self.assertEqual(payload["event_type"], "sec_annual_report_filed")

    def test_sec_filings_event_batch_extract_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_sec_filings_event_batch_extract") as batch_mock:
            batch_mock.return_value = {
                "requested_document_count": 2,
                "succeeded_document_count": 2,
                "failed_document_count": 0,
                "results": [],
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "sec-filings-event-batch-extract",
                        "--limit",
                        "5",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["requested_document_count"], 2)
        self.assertEqual(payload["failed_document_count"], 0)

    def test_event_intelligence_llm_extract_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_event_intelligence_llm_extract") as extract_mock:
            extract_mock.return_value = {
                "run_id": 199,
                "event_type": "sec_annual_report_filed",
                "model_invocation_id": 501,
                "artifact_id": 601,
                "status": "succeeded",
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "event-intelligence-llm-extract",
                        "--external-document-id",
                        "0000320193-24-000123",
                        "--llm-output-json",
                        "tests/fixtures/llm_sec_event_aapl_10k_structured.json",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 199)
        self.assertEqual(payload["model_invocation_id"], 501)

    def test_event_classification_impact_bootstrap_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_event_classification_impact_bootstrap") as bootstrap_mock:
            bootstrap_mock.return_value = {
                "run_id": 233,
                "requested_event_count": 2,
                "succeeded_event_count": 2,
                "failed_event_count": 0,
                "results": [],
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "event-classification-impact-bootstrap",
                        "--limit",
                        "10",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 233)
        self.assertEqual(payload["failed_event_count"], 0)

    def test_event_instrument_impact_bootstrap_cli_prints_summary(self) -> None:
        stdout = io.StringIO()
        with patch("stockanalysis.ingest.cli.run_event_instrument_impact_bootstrap") as bootstrap_mock:
            bootstrap_mock.return_value = {
                "run_id": 244,
                "requested_event_count": 2,
                "succeeded_event_count": 2,
                "failed_event_count": 0,
                "results": [],
            }
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "event-instrument-impact-bootstrap",
                        "--limit",
                        "10",
                    ]
                )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], 244)
        self.assertEqual(payload["failed_event_count"], 0)
