from __future__ import annotations

import json
import unittest
from datetime import date
from unittest.mock import patch

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.market.universe import MarketUniverseRecord
from stockanalysis.operations.segment_history_coverage_expansion import (
    DEFAULT_SEGMENT_HISTORY_COVERAGE_MODEL_NAME,
    _apply_parser_skip_reason_overrides,
    _apply_target_failure_overrides,
    load_active_segment_history_coverage_candidates,
    render_segment_history_coverage_report_sql,
    run_segment_history_coverage_expansion,
)


class FakeSegmentHistoryCoverageExecutor:
    def __init__(self, *, run_id: int = 1100) -> None:
        self.run_id = run_id
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- segment history coverage active targets"):
            return json.dumps(
                [
                    {
                        "instrument_id": 3,
                        "primary_symbol": "AAPL",
                        "source_kinds": ["active_recommendation", "portfolio_holding"],
                    },
                    {
                        "instrument_id": 4,
                        "primary_symbol": "MSFT",
                        "source_kinds": ["portfolio_holding"],
                    },
                    {
                        "instrument_id": 5,
                        "primary_symbol": "SPY",
                        "source_kinds": ["portfolio_holding"],
                    },
                ]
            )
        if sql.startswith("-- segment history coverage report"):
            return json.dumps(
                [
                    {
                        "symbol": "AAPL",
                        "coverage_status": "trend_backed",
                        "parsed_period_count": 4,
                        "parsed_segment_count": 5,
                        "bad_segment_count": 0,
                        "trend_backed_assumption_count": 5,
                        "max_history_period_count": 4,
                    },
                    {
                        "symbol": "MSFT",
                        "coverage_status": "unsupported_layout",
                        "parsed_period_count": 0,
                        "parsed_segment_count": 0,
                        "bad_segment_count": 0,
                        "trend_backed_assumption_count": 0,
                        "max_history_period_count": 0,
                    },
                ]
            )
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected SQL: {sql[:160]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class SegmentHistoryCoverageExpansionTests(unittest.TestCase):
    def test_load_active_targets_parses_source_kinds(self) -> None:
        executor = FakeSegmentHistoryCoverageExecutor()

        candidates = load_active_segment_history_coverage_candidates(
            executor=executor,  # type: ignore[arg-type]
            as_of_date=date(2026, 5, 26),
            portfolio_name="Long Term Paper",
            limit=25,
        )

        self.assertEqual([candidate.primary_symbol for candidate in candidates], ["AAPL", "MSFT", "SPY"])
        self.assertEqual(candidates[0].source_kinds, ("active_recommendation", "portfolio_holding"))

    def test_report_sql_surfaces_unsupported_and_bad_label_checks(self) -> None:
        sql = render_segment_history_coverage_report_sql(
            as_of_date=date(2026, 5, 26),
            statement_scope="annual",
            periods_per_instrument=4,
            targets=tuple(),
        )
        self.assertEqual(sql, "select '[]'::json::text;")

        records = (
            MarketUniverseRecord(cik="0000320193", company_name="Apple Inc.", symbol="AAPL", exchange_name="Nasdaq"),
        )
        with patch(
            "stockanalysis.operations.segment_history_coverage_expansion.load_market_universe_records",
            return_value=records,
        ):
            report = run_segment_history_coverage_expansion(
                config=RuntimeConfig(psql_command="psql"),
                as_of_date=date(2026, 5, 26),
                target_limit=1,
                execute=False,
                executor=FakeSegmentHistoryCoverageExecutor(),  # type: ignore[arg-type]
            )
        self.assertEqual(report["coverage_before"][0]["coverage_status"], "trend_backed")

    def test_dry_run_resolves_active_targets_without_parent_write(self) -> None:
        executor = FakeSegmentHistoryCoverageExecutor()
        records = (
            MarketUniverseRecord(cik="0000320193", company_name="Apple Inc.", symbol="AAPL", exchange_name="Nasdaq"),
            MarketUniverseRecord(cik="0000789019", company_name="Microsoft Corp.", symbol="MSFT", exchange_name="Nasdaq"),
        )

        with patch(
            "stockanalysis.operations.segment_history_coverage_expansion.load_market_universe_records",
            return_value=records,
        ):
            report = run_segment_history_coverage_expansion(
                config=RuntimeConfig(psql_command="psql"),
                as_of_date=date(2026, 5, 26),
                portfolio_name="Long Term Paper",
                limit=25,
                target_limit=2,
                execute=False,
                executor=executor,  # type: ignore[arg-type]
            )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["report_name"], "segment_history_coverage_expansion")
        self.assertEqual(report["model_name"], DEFAULT_SEGMENT_HISTORY_COVERAGE_MODEL_NAME)
        self.assertEqual(report["candidate_symbol_count"], 3)
        self.assertEqual(report["resolved_target_count"], 2)
        self.assertEqual(report["selected_target_count"], 2)
        self.assertEqual(report["unmatched_symbols"], ["SPY"])
        self.assertEqual([target["symbol"] for target in report["selected_targets"]], ["AAPL", "MSFT"])
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertFalse(report["automatic_order_allowed"])
        self.assertFalse(report["broker_submit_allowed"])
        self.assertEqual(report["order_boundary"], "read_only_no_order")
        self.assertEqual(executor.non_query_sql, [])

    def test_execute_runs_backfill_per_resolved_target_and_reports_coverage(self) -> None:
        executor = FakeSegmentHistoryCoverageExecutor(run_id=1200)
        records = (
            MarketUniverseRecord(cik="0000320193", company_name="Apple Inc.", symbol="AAPL", exchange_name="Nasdaq"),
            MarketUniverseRecord(cik="0000789019", company_name="Microsoft Corp.", symbol="MSFT", exchange_name="Nasdaq"),
        )

        with (
            patch(
                "stockanalysis.operations.segment_history_coverage_expansion.load_market_universe_records",
                return_value=records,
            ),
            patch("stockanalysis.operations.segment_history_coverage_expansion.run_segment_history_backfill") as backfill,
        ):
            backfill.side_effect = [
                {"report_name": "segment_history_backfill", "status": "completed", "run_id": 1201},
                {
                    "report_name": "segment_history_backfill",
                    "status": "completed",
                    "run_id": 1202,
                    "reported_segment_parser": {
                        "preview": {
                            "skipped_candidates": [
                                {
                                    "primary_symbol": "MSFT",
                                    "reason": "single_reportable_segment_no_disaggregated_segment_table",
                                }
                            ]
                        }
                    },
                },
            ]
            report = run_segment_history_coverage_expansion(
                config=RuntimeConfig(psql_command="psql"),
                as_of_date=date(2026, 5, 26),
                portfolio_name="Long Term Paper",
                limit=25,
                target_limit=2,
                periods_per_instrument=4,
                execute=True,
                executor=executor,  # type: ignore[arg-type]
            )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 1200)
        self.assertEqual(report["target_success_count"], 2)
        self.assertEqual(report["target_failed_count"], 0)
        self.assertEqual(report["coverage_summary"]["trend_backed_count"], 1)
        self.assertEqual(report["coverage_summary"]["unsupported_layout_count"], 0)
        self.assertEqual(report["coverage_summary"]["single_reportable_segment_no_detail_count"], 1)
        self.assertNotIn("segment_parser_skip_reasons", report["coverage_after"][0])
        self.assertEqual(
            report["coverage_after"][1]["coverage_status"],
            "single_reportable_segment_no_disaggregated_segment_table",
        )
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])
        self.assertEqual(backfill.call_count, 2)
        self.assertEqual(backfill.call_args_list[0].kwargs["cik"], "0000320193")
        self.assertEqual(backfill.call_args_list[0].kwargs["fallback_symbol"], "AAPL")
        self.assertEqual(backfill.call_args_list[1].kwargs["cik"], "0000789019")
        self.assertEqual(backfill.call_args_list[1].kwargs["fallback_symbol"], "MSFT")
        self.assertTrue(backfill.call_args_list[0].kwargs["execute"])
        self.assertEqual(backfill.call_args_list[0].kwargs["periods_per_instrument"], 4)

    def test_skip_reason_override_does_not_hide_mixed_unsupported_layouts(self) -> None:
        rows = [
            {
                "symbol": "AEIS",
                "coverage_status": "unsupported_layout",
                "parsed_period_count": 0,
            }
        ]
        reports = [
            {
                "reported_segment_parser": {
                    "preview": {
                        "skipped_candidates": [
                            {
                                "primary_symbol": "AEIS",
                                "reason": "unsupported_segment_table_layout",
                            },
                            {
                                "primary_symbol": "AEIS",
                                "reason": "single_reportable_segment_no_disaggregated_segment_table",
                            },
                        ]
                    }
                }
            }
        ]

        updated = _apply_parser_skip_reason_overrides(rows, reports)

        self.assertEqual(updated[0]["coverage_status"], "unsupported_layout")
        self.assertEqual(
            updated[0]["segment_parser_skip_reasons"],
            ["unsupported_segment_table_layout", "single_reportable_segment_no_disaggregated_segment_table"],
        )

    def test_target_failure_override_classifies_missing_us_gaap_companyfacts(self) -> None:
        rows = [
            {
                "symbol": "EROK",
                "coverage_status": "missing_source_document_linkage",
            }
        ]
        failed_reports = [
            {
                "symbol": "EROK",
                "error_summary": "SEC companyfacts payload for `0002104882` does not contain `facts.us-gaap`",
            }
        ]

        updated = _apply_target_failure_overrides(rows, failed_reports)

        self.assertEqual(updated[0]["coverage_status"], "sec_companyfacts_missing_us_gaap_facts")
        self.assertEqual(updated[0]["source_linkage_blocker"], "sec_companyfacts_missing_us_gaap_facts")
        self.assertIn("0002104882", updated[0]["source_linkage_error_summary"])


if __name__ == "__main__":
    unittest.main()
