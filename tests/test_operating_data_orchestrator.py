from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from stockanalysis.operations.operating_data_orchestrator import build_operating_data_run_report


class FakeOperatingDataExecutor:
    def __init__(self) -> None:
        self.scalar_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- operating data context lookup"):
            if "instrument.primary_symbol" not in sql:
                raise AssertionError(sql)
            return json.dumps(
                {
                    "latest_price_date": "2026-05-19",
                    "latest_event_date": "2026-05-20",
                    "event_impacted_symbols": ["AAPL", "TSLA"],
                    "active_recommendation_symbols": ["AAPL", "NVDA"],
                    "paper_portfolio_symbols": ["MSFT"],
                    "toss_live_position_symbols": ["TSLA"],
                    "missing_event_price_symbols": ["TSLA"],
                }
            )
        if sql.startswith("-- operating data latest price lookup"):
            if "instrument.primary_symbol" not in sql:
                raise AssertionError(sql)
            return json.dumps(
                [
                    {
                        "symbol": "AAPL",
                        "trade_date": "2026-05-19",
                        "adjusted_close": "200.000000",
                        "close": "200.000000",
                    },
                    {
                        "symbol": "TSLA",
                        "trade_date": "2026-05-19",
                        "adjusted_close": "400.000000",
                        "close": "400.000000",
                    },
                ]
            )
        raise AssertionError(f"Unexpected SQL: {sql}")


class FakeArtifactRunner:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def __call__(self, **kwargs: object) -> dict[str, object]:
        self.calls.append(kwargs)
        index = len(self.calls)
        return {
            "status": "succeeded",
            "exit_code": 0,
            "artifact_dir": f"/tmp/artifact-{index}",
            "metadata_path": f"/tmp/artifact-{index}/metadata.json",
            "stdout_path": f"/tmp/artifact-{index}/stdout.txt",
            "stderr_path": f"/tmp/artifact-{index}/stderr.log",
        }


class OperatingDataOrchestratorTests(unittest.TestCase):
    def test_preview_builds_secret_free_full_plan_without_running_steps(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            runtime_root, env_file = _write_runtime_files(Path(outside_root))
            runner = FakeArtifactRunner()

            report = build_operating_data_run_report(
                repo_root=repo_root,
                runtime_root=runtime_root,
                data_operations_env_file=env_file,
                execute=False,
                python_executable="/usr/bin/python3",
                executor=FakeOperatingDataExecutor(),
                runner=runner,
                generated_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
            )

        self.assertEqual(report["run_status"], "preview_not_executed")
        self.assertEqual(report["profile"], "full-recovery")
        self.assertEqual(report["profile_cadence"], "ad_hoc")
        self.assertFalse(report["execute"])
        self.assertEqual(runner.calls, [])
        self.assertEqual(report["derived_inputs"]["as_of_date"], "2026-05-20")
        self.assertIn("TSLA", report["derived_inputs"]["missing_price_symbols"])
        step_ids = [step["step_id"] for step in report["planned_steps"]]
        self.assertEqual(step_ids[0], "market-universe-weekly")
        self.assertEqual(step_ids[1], "sec-filings-weekly")
        self.assertIn("sec-companyfacts-weekly", step_ids)
        self.assertIn("professional-coverage-expansion", step_ids)
        self.assertIn("financial-metric-normalization", step_ids)
        self.assertIn("peer-relative-analysis", step_ids)
        self.assertIn("financial-forecast-inputs", step_ids)
        self.assertIn("financial-period-source-linkage", step_ids)
        self.assertIn("reported-segment-footnote-parser", step_ids)
        self.assertIn("segment-footnote-evidence", step_ids)
        self.assertIn("sum-of-parts-valuation", step_ids)
        self.assertIn("industry-competitive-positioning", step_ids)
        self.assertIn("market-price-daily", step_ids)
        self.assertIn("portfolio-position-snapshot", step_ids)
        self.assertIn("portfolio-holding-thesis-bootstrap", step_ids)
        self.assertIn("paper-validation-audit", step_ids)
        self.assertIn("recommendation-fundamental-components", step_ids)
        self.assertIn("equity-research-reporting", step_ids)
        self.assertIn("recommendation-outcome-backfill", step_ids)
        self.assertIn("recommendation-outcome-due-action-router", step_ids)
        self.assertIn("recommendation-quality-eval", step_ids)
        self.assertIn("portfolio-review-feedback-cadence", step_ids)
        self.assertIn("portfolio-review-feedback-action-router", step_ids)
        self.assertIn("portfolio-attribution-monthly", step_ids)
        self.assertLess(
            step_ids.index("portfolio-position-snapshot"),
            step_ids.index("portfolio-holding-thesis-bootstrap"),
        )
        self.assertLess(
            step_ids.index("portfolio-holding-thesis-bootstrap"),
            step_ids.index("portfolio-remediation-daily"),
        )
        macro_step = next(step for step in report["planned_steps"] if step["step_id"] == "macro-weekly")
        macro_command = " ".join(macro_step["command_argv"])
        self.assertIn("--series-id NASDAQQSLVO", macro_command)
        self.assertLess(
            step_ids.index("paper-validation-audit"),
            step_ids.index("recommendation-outcome-backfill"),
        )
        self.assertLess(
            step_ids.index("sec-companyfacts-weekly"),
            step_ids.index("financial-period-source-linkage"),
        )
        self.assertLess(
            step_ids.index("financial-period-source-linkage"),
            step_ids.index("professional-coverage-expansion"),
        )
        self.assertLess(
            step_ids.index("financial-forecast-inputs"),
            step_ids.index("reported-segment-footnote-parser"),
        )
        self.assertLess(
            step_ids.index("reported-segment-footnote-parser"),
            step_ids.index("segment-footnote-evidence"),
        )
        self.assertLess(
            step_ids.index("segment-footnote-evidence"),
            step_ids.index("sum-of-parts-valuation"),
        )
        self.assertLess(
            step_ids.index("sum-of-parts-valuation"),
            step_ids.index("valuation-snapshot"),
        )
        self.assertLess(
            step_ids.index("valuation-snapshot"),
            step_ids.index("industry-competitive-positioning"),
        )
        self.assertLess(
            step_ids.index("recommendation-outcome-backfill"),
            step_ids.index("recommendation-outcome-due-action-router"),
        )
        self.assertLess(
            step_ids.index("recommendation-outcome-due-action-router"),
            step_ids.index("recommendation-quality-eval"),
        )
        self.assertLess(
            step_ids.index("recommendation-quality-eval"),
            step_ids.index("portfolio-review-feedback-cadence"),
        )
        self.assertLess(
            step_ids.index("portfolio-review-feedback-cadence"),
            step_ids.index("portfolio-review-feedback-action-router"),
        )
        self.assertLess(
            step_ids.index("performance-outcome-monthly"),
            step_ids.index("portfolio-attribution-monthly"),
        )
        self.assertEqual(report["derived_inputs"]["sec_filings_cik"], "320193")
        self.assertEqual(report["derived_inputs"]["sec_filings_max_filings"], 3)
        self.assertTrue(report["derived_inputs"]["source_positions_required"])
        self.assertIn("news-intraday", [profile["profile"] for profile in report["profile_catalog"]])
        self.assertNotIn("postgresql://", json.dumps(report))
        self.assertNotIn("secret-token", json.dumps(report))

    def test_news_intraday_profile_does_not_require_portfolio_positions(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            runtime_root, env_file = _write_runtime_files_without_positions(Path(outside_root))
            runner = FakeArtifactRunner()

            report = build_operating_data_run_report(
                repo_root=repo_root,
                runtime_root=runtime_root,
                data_operations_env_file=env_file,
                profile="news-intraday",
                execute=False,
                python_executable="/usr/bin/python3",
                runner=runner,
                generated_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
            )

        self.assertEqual(report["profile"], "news-intraday")
        self.assertEqual(report["profile_cadence"], "intraday")
        self.assertFalse(report["derived_inputs"]["source_positions_required"])
        self.assertEqual(report["derived_inputs"]["source_position_count"], 0)
        self.assertEqual(report["generated_files"]["missing_price_watchlist"], "")
        self.assertEqual(report["generated_files"]["position_snapshot_csv"], "")
        self.assertEqual(
            [step["step_id"] for step in report["planned_steps"]],
            [
                "news-rss-ingest",
                "news-missing-instrument-bootstrap",
                "news-rss-enrichment",
                "news-korean-translation",
                "news-cluster-evidence",
                "news-ai-evidence",
                "cycle-ai-duplicate-title-cleanup",
                "news-ai-eval",
                "macro-event-propagation",
                "hierarchical-impact-propagation",
            ],
        )
        bootstrap_command = " ".join(report["planned_steps"][1]["command_argv"])
        self.assertIn("news-missing-instrument-bootstrap-run", bootstrap_command)
        translation_command = " ".join(report["planned_steps"][3]["command_argv"])
        self.assertIn("news-rss-translation-run", translation_command)
        self.assertIn("--provider codex_oauth", translation_command)
        self.assertIn("--execute", translation_command)
        cluster_command = " ".join(report["planned_steps"][4]["command_argv"])
        self.assertIn("news-rss-cluster-evidence-run", cluster_command)
        self.assertIn("--as-of-date 2026-05-20", cluster_command)
        ai_command = " ".join(report["planned_steps"][5]["command_argv"])
        self.assertIn("news-rss-ai-extract-run", ai_command)
        self.assertIn("--provider codex_oauth", ai_command)
        self.assertIn("--execute", ai_command)
        duplicate_cleanup_command = " ".join(report["planned_steps"][6]["command_argv"])
        self.assertIn("cycle-ai-duplicate-title-cleanup-run", duplicate_cleanup_command)
        self.assertIn("--lookback-days 3", duplicate_cleanup_command)
        self.assertIn("--execute", duplicate_cleanup_command)
        eval_command = " ".join(report["planned_steps"][7]["command_argv"])
        self.assertIn("news-ai-eval-run", eval_command)
        self.assertIn("--provider fixture", eval_command)
        self.assertIn("--execute", eval_command)
        propagation_command = " ".join(report["planned_steps"][8]["command_argv"])
        self.assertIn("macro-event-propagation-run", propagation_command)
        self.assertIn("--as-of-date 2026-05-20", propagation_command)
        self.assertIn("--execute", propagation_command)
        hierarchical_command = " ".join(report["planned_steps"][9]["command_argv"])
        self.assertIn("hierarchical-impact-propagation-run", hierarchical_command)
        self.assertIn("--max-depth 3", hierarchical_command)
        self.assertIn("--execute", hierarchical_command)
        self.assertEqual(runner.calls, [])

    def test_cross_asset_daily_profile_generates_etf_price_watchlist_before_indicator_sync(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            runtime_root, env_file = _write_runtime_files_without_positions(Path(outside_root))

            report = build_operating_data_run_report(
                repo_root=repo_root,
                runtime_root=runtime_root,
                data_operations_env_file=env_file,
                profile="cross-asset-daily",
                execute=True,
                python_executable="/usr/bin/python3",
                executor=FakeOperatingDataExecutor(),
                runner=FakeArtifactRunner(),
                generated_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
            )

            cross_asset_watchlist_path = Path(report["generated_files"]["cross_asset_price_watchlist"])
            with cross_asset_watchlist_path.open(encoding="utf-8") as stream:
                watchlist_rows = list(csv.DictReader(stream))

        step_ids = [step["step_id"] for step in report["planned_steps"]]
        self.assertEqual(report["profile"], "cross-asset-daily")
        self.assertFalse(report["derived_inputs"]["source_positions_required"])
        self.assertIn("SPY", report["derived_inputs"]["cross_asset_price_symbols"])
        self.assertIn("QQQ", report["derived_inputs"]["cross_asset_price_symbols"])
        self.assertIn("XLE", report["derived_inputs"]["cross_asset_price_symbols"])
        self.assertEqual(watchlist_rows[0], {"symbol": "SPY"})
        self.assertIn({"symbol": "TLT"}, watchlist_rows)
        self.assertLess(
            step_ids.index("free-provider-capacity-registry"),
            step_ids.index("cross-asset-market-price-refresh"),
        )
        self.assertLess(
            step_ids.index("cross-asset-market-price-refresh"),
            step_ids.index("cross-asset-indicator-provider-fetch"),
        )
        self.assertLess(
            step_ids.index("cross-asset-indicator-provider-fetch"),
            step_ids.index("cross-asset-indicator-ingest"),
        )
        self.assertLess(
            step_ids.index("cross-asset-regime-snapshot"),
            step_ids.index("asset-correlation-analysis"),
        )
        self.assertLess(
            step_ids.index("indicator-news-linkage"),
            step_ids.index("asset-correlation-analysis"),
        )
        self.assertLess(
            step_ids.index("asset-correlation-analysis"),
            step_ids.index("recommendation-cross-asset-components"),
        )
        correlation_step = next(
            step for step in report["planned_steps"] if step["step_id"] == "asset-correlation-analysis"
        )
        correlation_command = " ".join(correlation_step["command_argv"])
        self.assertIn("correlation-analysis-run", correlation_command)
        self.assertIn("--as-of-date 2026-05-20", correlation_command)
        self.assertIn("--execute", correlation_command)
        refresh_step = next(
            step for step in report["planned_steps"] if step["step_id"] == "cross-asset-market-price-refresh"
        )
        refresh_command = " ".join(refresh_step["command_argv"])
        self.assertIn("market-price-free-backfill-run", refresh_command)
        self.assertIn("--daily-budget 80", refresh_command)
        self.assertIn("--max-requests-per-run 24", refresh_command)
        self.assertIn("--throttle-seconds 8.0", refresh_command)
        self.assertIn("--allow-symbol-failures", refresh_command)

    def test_toss_us_profile_generates_tracked_symbols_beyond_cross_asset_only(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            runtime_root, env_file = _write_runtime_files_without_positions(Path(outside_root))
            market_watchlist = Path(outside_root) / "market-watchlist.csv"
            market_watchlist.write_text("symbol,role\nAMZN,core\nAAPL,duplicate\n", encoding="utf-8")
            with env_file.open("a", encoding="utf-8") as stream:
                stream.write(f'STOCKANALYSIS_MARKET_PRICE_WATCHLIST_CSV="{market_watchlist}"\n')
            runner = FakeArtifactRunner()

            report = build_operating_data_run_report(
                repo_root=repo_root,
                runtime_root=runtime_root,
                data_operations_env_file=env_file,
                profile="toss-candles-us-shadow-daily",
                execute=True,
                python_executable="/usr/bin/python3",
                executor=FakeOperatingDataExecutor(),
                runner=runner,
                generated_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
            )

            toss_symbols_path = Path(report["generated_files"]["tossinvest_us_symbols"])
            with toss_symbols_path.open(encoding="utf-8") as stream:
                watchlist_rows = list(csv.DictReader(stream))

        symbols = [row["symbol"] for row in watchlist_rows]
        self.assertIn("SPY", symbols)
        self.assertIn("AMZN", symbols)
        self.assertIn("AAPL", symbols)
        self.assertIn("NVDA", symbols)
        self.assertIn("MSFT", symbols)
        self.assertIn("TSLA", symbols)
        self.assertEqual(len(symbols), len(set(symbols)))
        self.assertEqual(report["generated_files"]["cross_asset_price_watchlist"], "")
        self.assertIn("AMZN", report["derived_inputs"]["market_price_watchlist_symbols"])
        self.assertIn("NVDA", report["derived_inputs"]["tossinvest_us_symbols"])
        rendered_commands = [" ".join(call["command_argv"]) for call in runner.calls]
        self.assertIn(str(toss_symbols_path), rendered_commands[0])
        self.assertIn("--outputsize 30", rendered_commands[0])
        self.assertIn("--max-symbols-per-run 10", rendered_commands[0])

    def test_weekly_reference_profiles_do_not_require_portfolio_positions(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            runtime_root, env_file = _write_runtime_files_without_positions(Path(outside_root))

            universe_report = build_operating_data_run_report(
                repo_root=repo_root,
                runtime_root=runtime_root,
                data_operations_env_file=env_file,
                profile="market-universe-weekly",
                execute=False,
                python_executable="/usr/bin/python3",
                runner=FakeArtifactRunner(),
                generated_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
            )
            sec_report = build_operating_data_run_report(
                repo_root=repo_root,
                runtime_root=runtime_root,
                data_operations_env_file=env_file,
                profile="sec-filings-weekly",
                execute=False,
                python_executable="/usr/bin/python3",
                runner=FakeArtifactRunner(),
                generated_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
            )

        self.assertEqual([step["step_id"] for step in universe_report["planned_steps"]], ["market-universe-weekly"])
        self.assertEqual(
            [step["step_id"] for step in sec_report["planned_steps"]],
            [
                "sec-filings-weekly",
                "sec-companyfacts-weekly",
                "financial-period-source-linkage",
                "professional-coverage-expansion",
                "financial-metric-normalization",
                "peer-relative-analysis",
                "financial-forecast-inputs",
                "reported-segment-footnote-parser",
                "segment-footnote-evidence",
                "sum-of-parts-valuation",
                "valuation-snapshot",
                "industry-competitive-positioning",
            ],
        )
        self.assertFalse(universe_report["derived_inputs"]["source_positions_required"])
        self.assertFalse(sec_report["derived_inputs"]["source_positions_required"])
        sec_command = " ".join(sec_report["planned_steps"][0]["command_argv"])
        self.assertIn("sec-filings-upsert", sec_command)
        self.assertIn("--max-filings 3", sec_command)
        companyfacts_command = " ".join(sec_report["planned_steps"][1]["command_argv"])
        self.assertIn("sec-companyfacts-upsert", companyfacts_command)
        source_linkage_command = " ".join(sec_report["planned_steps"][2]["command_argv"])
        self.assertIn("financial-period-source-linkage-run", source_linkage_command)
        self.assertIn("--statement-scope annual", source_linkage_command)
        self.assertIn("--max-filings 200", source_linkage_command)
        self.assertIn("--raw-fetch-limit 4", source_linkage_command)
        coverage_command = " ".join(sec_report["planned_steps"][3]["command_argv"])
        self.assertIn("professional-coverage-expansion-run", coverage_command)
        self.assertIn("--research-provider fixture", coverage_command)
        financial_command = " ".join(sec_report["planned_steps"][4]["command_argv"])
        self.assertIn("financial-metric-normalization-run", financial_command)
        peer_command = " ".join(sec_report["planned_steps"][5]["command_argv"])
        self.assertIn("peer-relative-analysis-run", peer_command)
        forecast_command = " ".join(sec_report["planned_steps"][6]["command_argv"])
        self.assertIn("financial-forecast-inputs-run", forecast_command)
        reported_segment_command = " ".join(sec_report["planned_steps"][7]["command_argv"])
        self.assertIn("reported-segment-footnote-parser-run", reported_segment_command)
        self.assertIn("--periods-per-instrument 4", reported_segment_command)
        segment_command = " ".join(sec_report["planned_steps"][8]["command_argv"])
        self.assertIn("segment-footnote-evidence-run", segment_command)
        sotp_command = " ".join(sec_report["planned_steps"][9]["command_argv"])
        self.assertIn("sum-of-parts-valuation-run", sotp_command)
        valuation_command = " ".join(sec_report["planned_steps"][10]["command_argv"])
        self.assertIn("valuation-snapshot-run", valuation_command)
        competitive_command = " ".join(sec_report["planned_steps"][11]["command_argv"])
        self.assertIn("industry-competitive-positioning-run", competitive_command)

    def test_decision_daily_profile_runs_decision_steps_without_news_or_macro(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            runtime_root, env_file = _write_runtime_files(Path(outside_root))

            report = build_operating_data_run_report(
                repo_root=repo_root,
                runtime_root=runtime_root,
                data_operations_env_file=env_file,
                profile="decision-daily",
                execute=False,
                python_executable="/usr/bin/python3",
                executor=FakeOperatingDataExecutor(),
                runner=FakeArtifactRunner(),
                generated_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
            )

        step_ids = [step["step_id"] for step in report["planned_steps"]]
        self.assertEqual(report["profile"], "decision-daily")
        self.assertEqual(step_ids[0], "missing-symbol-price-backfill")
        self.assertIn("cycle-hierarchy-snapshot-v2", step_ids)
        self.assertIn("cycle-graph-context-summary", step_ids)
        self.assertIn("cycle-community-ai-summary-v2", step_ids)
        self.assertIn("recommendation-bootstrap", step_ids)
        self.assertIn("recommendation-fundamental-components", step_ids)
        self.assertIn("equity-research-reporting", step_ids)
        self.assertIn("portfolio-holding-thesis-bootstrap", step_ids)
        self.assertIn("paper-validation-audit", step_ids)
        self.assertIn("recommendation-outcome-backfill", step_ids)
        self.assertIn("recommendation-outcome-due-action-router", step_ids)
        self.assertIn("portfolio-review-feedback-cadence", step_ids)
        self.assertIn("portfolio-review-feedback-action-router", step_ids)
        self.assertNotIn("news-rss-ingest", step_ids)
        self.assertNotIn("macro-weekly", step_ids)
        self.assertLess(
            step_ids.index("cycle-state-snapshot"),
            step_ids.index("cycle-hierarchy-snapshot-v2"),
        )
        self.assertLess(
            step_ids.index("cycle-hierarchy-snapshot-v2"),
            step_ids.index("cycle-graph-context-summary"),
        )
        self.assertLess(
            step_ids.index("cycle-graph-context-summary"),
            step_ids.index("cycle-community-ai-summary-v2"),
        )
        self.assertLess(
            step_ids.index("cycle-community-ai-summary-v2"),
            step_ids.index("recommendation-bootstrap"),
        )
        self.assertLess(
            step_ids.index("recommendation-bootstrap"),
            step_ids.index("recommendation-fundamental-components"),
        )
        self.assertLess(
            step_ids.index("recommendation-fundamental-components"),
            step_ids.index("thesis-bootstrap"),
        )
        self.assertLess(
            step_ids.index("thesis-review-bootstrap"),
            step_ids.index("equity-research-reporting"),
        )
        self.assertLess(
            step_ids.index("equity-research-reporting"),
            step_ids.index("portfolio-position-snapshot"),
        )
        self.assertLess(
            step_ids.index("portfolio-position-snapshot"),
            step_ids.index("portfolio-holding-thesis-bootstrap"),
        )
        self.assertLess(
            step_ids.index("portfolio-holding-thesis-bootstrap"),
            step_ids.index("portfolio-remediation-daily"),
        )
        self.assertLess(
            step_ids.index("recommendation-outcome-backfill"),
            step_ids.index("recommendation-outcome-due-action-router"),
        )
        self.assertLess(
            step_ids.index("recommendation-outcome-due-action-router"),
            step_ids.index("recommendation-quality-eval"),
        )
        self.assertLess(
            step_ids.index("recommendation-quality-eval"),
            step_ids.index("portfolio-review-feedback-cadence"),
        )
        self.assertLess(
            step_ids.index("portfolio-review-feedback-cadence"),
            step_ids.index("portfolio-review-feedback-action-router"),
        )

    def test_performance_monthly_profile_runs_outcome_then_attribution_without_positions(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            runtime_root, env_file = _write_runtime_files_without_positions(Path(outside_root))

            report = build_operating_data_run_report(
                repo_root=repo_root,
                runtime_root=runtime_root,
                data_operations_env_file=env_file,
                profile="performance-monthly",
                execute=False,
                python_executable="/usr/bin/python3",
                runner=FakeArtifactRunner(),
                generated_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
            )

        step_ids = [step["step_id"] for step in report["planned_steps"]]
        self.assertEqual(report["profile"], "performance-monthly")
        self.assertEqual(step_ids, ["performance-outcome-monthly", "portfolio-attribution-monthly"])
        self.assertFalse(report["derived_inputs"]["source_positions_required"])
        outcome_command = " ".join(report["planned_steps"][0]["command_argv"])
        attribution_command = " ".join(report["planned_steps"][1]["command_argv"])
        self.assertIn("recommendation-outcome-backfill-run", outcome_command)
        self.assertIn("portfolio-attribution-run", attribution_command)
        self.assertIn("--portfolio-name Long Term Paper", attribution_command)
        self.assertIn("--as-of-date 2026-05-20", attribution_command)
        self.assertIn("--execute", attribution_command)

    def test_execute_runs_backfill_before_signal_and_generates_position_csv(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            runtime_root, env_file = _write_runtime_files(Path(outside_root))
            runner = FakeArtifactRunner()

            report = build_operating_data_run_report(
                repo_root=repo_root,
                runtime_root=runtime_root,
                data_operations_env_file=env_file,
                execute=True,
                python_executable="/usr/bin/python3",
                executor=FakeOperatingDataExecutor(),
                runner=runner,
                generated_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
            )

            watchlist_path = Path(report["generated_files"]["missing_price_watchlist"])
            positions_path = Path(report["generated_files"]["position_snapshot_csv"])
            with watchlist_path.open(encoding="utf-8") as stream:
                watchlist_rows = list(csv.DictReader(stream))
            with positions_path.open(encoding="utf-8") as stream:
                position_rows = list(csv.DictReader(stream))

        self.assertEqual(report["run_status"], "completed")
        self.assertGreater(len(runner.calls), 8)
        rendered_commands = [" ".join(call["command_argv"]) for call in runner.calls]
        backfill_index = next(index for index, command in enumerate(rendered_commands) if "market-price-free-backfill-run" in command)
        signal_index = next(index for index, command in enumerate(rendered_commands) if "strategy-universe-slice" in command)
        position_snapshot_index = next(
            index for index, command in enumerate(rendered_commands) if "portfolio-position-snapshot-upsert" in command
        )
        holding_thesis_index = next(
            index for index, command in enumerate(rendered_commands) if "portfolio-holding-thesis-bootstrap" in command
        )
        remediation_index = next(
            index for index, command in enumerate(rendered_commands) if "portfolio-remediation-daily-run" in command
        )
        self.assertLess(backfill_index, signal_index)
        self.assertIn("--allow-symbol-failures", rendered_commands[backfill_index])
        self.assertLess(position_snapshot_index, holding_thesis_index)
        self.assertLess(holding_thesis_index, remediation_index)
        self.assertEqual(watchlist_rows, [{"symbol": "TSLA"}])
        self.assertEqual([row["symbol"] for row in position_rows], ["AAPL", "TSLA"])
        self.assertEqual(position_rows[0]["market_price"], "200.000000")
        self.assertEqual(position_rows[1]["market_price"], "400.000000")
        self.assertEqual(position_rows[0]["weight"], "0.3333")
        self.assertEqual(position_rows[1]["weight"], "0.6667")


def _write_runtime_files(root: Path) -> tuple[Path, Path]:
    runtime_root = root / "runtime"
    runtime_root.mkdir()
    artifact_root = root / "artifacts"
    positions_csv = root / "portfolio-source.csv"
    positions_csv.write_text(
        "symbol,quantity,cost_basis\nAAPL,10,150\nTSLA,10,250\n",
        encoding="utf-8",
    )
    env_file = root / "data-operations.env"
    env_file.write_text(
        "\n".join(
            [
                f'STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="{artifact_root}"',
                f'STOCKANALYSIS_PORTFOLIO_POSITIONS_CSV="{positions_csv}"',
                f'STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH="{root / "ledger.json"}"',
                'STOCKANALYSIS_MARKET_PRICE_PROVIDER="twelve_data"',
                'STOCKANALYSIS_PSQL_COMMAND="psql postgresql://operator:secret-token@db.internal/stockanalysis"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return runtime_root, env_file


def _write_runtime_files_without_positions(root: Path) -> tuple[Path, Path]:
    runtime_root = root / "runtime"
    runtime_root.mkdir()
    artifact_root = root / "artifacts"
    env_file = root / "data-operations.env"
    env_file.write_text(
        "\n".join(
            [
                f'STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="{artifact_root}"',
                f'STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH="{root / "ledger.json"}"',
                'STOCKANALYSIS_MARKET_PRICE_PROVIDER="twelve_data"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return runtime_root, env_file


if __name__ == "__main__":
    unittest.main()
