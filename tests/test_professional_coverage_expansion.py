from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from stockanalysis.ingest.market.universe import load_market_universe_records
from stockanalysis.operations.professional_coverage_expansion import (
    ProfessionalCoverageGapCandidate,
    render_active_recommendation_professional_gap_symbols_sql,
    resolve_professional_coverage_targets,
    run_professional_coverage_expansion,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class FakeCoverageExpansionExecutor:
    def __init__(self, *, run_id: int = 9901) -> None:
        self.run_id = run_id
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- active recommendation professional coverage gap lookup"):
            return json.dumps(
                [
                    {
                        "instrument_id": 501,
                        "primary_symbol": "AAPL",
                        "missing_layers": ["financial_metric_normalized", "valuation_snapshot"],
                    },
                    {
                        "instrument_id": 502,
                        "primary_symbol": "BABA",
                        "missing_layers": ["equity_research_artifact"],
                    },
                    {
                        "instrument_id": 503,
                        "primary_symbol": "MISSING",
                        "missing_layers": ["financial_metric_normalized"],
                    },
                ]
            )
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class ProfessionalCoverageExpansionTests(unittest.TestCase):
    def test_gap_lookup_sql_tracks_all_professional_layers_without_weight_changes(self) -> None:
        sql = render_active_recommendation_professional_gap_symbols_sql(as_of_date=date(2026, 5, 25), limit=25)

        self.assertIn("market.financial_metric_normalized", sql)
        self.assertIn("market.peer_relative_snapshot", sql)
        self.assertIn("research.segment_footnote_evidence", sql)
        self.assertIn("market.sum_of_parts_component", sql)
        self.assertIn("market.valuation_snapshot", sql)
        self.assertIn("research.industry_competitive_position", sql)
        self.assertIn("research.equity_research_artifact", sql)
        self.assertIn("signal.investment_thesis", sql)
        self.assertNotIn("component_weight", sql)

    def test_resolve_professional_coverage_targets_uses_sec_ticker_mapping(self) -> None:
        records = load_market_universe_records(
            config=type("Config", (), {})(),
            company_tickers_json_path=str(FIXTURES_DIR / "sec_company_tickers_exchange_sample.json"),
        )
        targets = resolve_professional_coverage_targets(
            (
                ProfessionalCoverageGapCandidate(
                    instrument_id=501,
                    primary_symbol="AAPL",
                    missing_layers=("financial_metric_normalized",),
                ),
                ProfessionalCoverageGapCandidate(
                    instrument_id=502,
                    primary_symbol="BABA",
                    missing_layers=("equity_research_artifact",),
                ),
            ),
            company_ticker_records=records,
        )

        self.assertEqual([target.primary_symbol for target in targets], ["AAPL", "BABA"])
        self.assertEqual(targets[0].cik, "0000320193")
        self.assertEqual(targets[1].exchange_name, "NYSE")

    def test_dry_run_reports_targets_without_mutating(self) -> None:
        executor = FakeCoverageExpansionExecutor()

        report = run_professional_coverage_expansion(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 25),
            limit=3,
            companyfacts_limit=1,
            research_limit=2,
            company_tickers_json_path=str(FIXTURES_DIR / "sec_company_tickers_exchange_sample.json"),
            execute=False,
            executor=executor,
        )

        self.assertEqual(report["status"], "planned")
        self.assertIsNone(report["run_id"])
        self.assertEqual(report["candidate_symbol_count"], 3)
        self.assertEqual(report["resolved_target_count"], 2)
        self.assertEqual(report["companyfacts_targets"][0]["symbol"], "AAPL")
        self.assertEqual(report["research_symbols"], ["AAPL", "BABA"])
        self.assertEqual(report["unmatched_symbols"], ["MISSING"])
        self.assertEqual(executor.non_query_sql, [])

    def test_execute_runs_companyfacts_and_downstream_professional_steps(self) -> None:
        executor = FakeCoverageExpansionExecutor(run_id=9909)

        with (
            patch("stockanalysis.operations.professional_coverage_expansion.run_sec_companyfacts_upsert") as companyfacts,
            patch(
                "stockanalysis.operations.professional_coverage_expansion.run_financial_metric_normalization"
            ) as normalization,
            patch("stockanalysis.operations.professional_coverage_expansion.run_peer_relative_analysis") as peer,
            patch("stockanalysis.operations.professional_coverage_expansion.run_financial_forecast_inputs") as forecast,
            patch(
                "stockanalysis.operations.professional_coverage_expansion.run_reported_segment_footnote_parser"
            ) as segment_parser,
            patch("stockanalysis.operations.professional_coverage_expansion.run_segment_footnote_evidence") as segment,
            patch("stockanalysis.operations.professional_coverage_expansion.run_sum_of_parts_valuation") as sotp,
            patch("stockanalysis.operations.professional_coverage_expansion.run_valuation_snapshot") as valuation,
            patch(
                "stockanalysis.operations.professional_coverage_expansion.run_industry_competitive_positioning"
            ) as positioning,
            patch("stockanalysis.operations.professional_coverage_expansion.run_equity_research_reporting") as research,
        ):
            companyfacts.return_value = {"instrument_symbol": "AAPL", "fact_count": 6}
            normalization.return_value = {"report_name": "financial_metric_normalization"}
            peer.return_value = {"report_name": "peer_relative_analysis"}
            forecast.return_value = {"report_name": "financial_forecast_inputs"}
            segment_parser.return_value = {"report_name": "reported_segment_footnote_parser"}
            segment.return_value = {"report_name": "segment_footnote_evidence"}
            sotp.return_value = {"report_name": "sum_of_parts_valuation"}
            valuation.return_value = {"report_name": "valuation_snapshot"}
            positioning.return_value = {"report_name": "industry_competitive_positioning"}
            research.return_value = {"report_name": "equity_research_reporting"}

            report = run_professional_coverage_expansion(
                config=type("Config", (), {})(),
                as_of_date=date(2026, 5, 25),
                limit=3,
                companyfacts_limit=1,
                research_limit=2,
                research_provider="fixture",
                company_tickers_json_path=str(FIXTURES_DIR / "sec_company_tickers_exchange_sample.json"),
                execute=True,
                executor=executor,
            )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9909)
        self.assertEqual(report["companyfacts_failed_count"], 0)
        companyfacts.assert_called_once()
        self.assertEqual(companyfacts.call_args.args[0], "0000320193")
        self.assertEqual(companyfacts.call_args.kwargs["fallback_symbol"], "AAPL")
        normalization.assert_called_once()
        peer.assert_called_once()
        forecast.assert_called_once()
        segment_parser.assert_called_once()
        segment.assert_called_once()
        sotp.assert_called_once()
        valuation.assert_called_once()
        positioning.assert_called_once()
        research.assert_called_once()
        self.assertEqual(research.call_args.kwargs["symbols"], ("AAPL", "BABA"))
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])

    def test_execute_keeps_downstream_running_when_one_companyfacts_target_fails(self) -> None:
        executor = FakeCoverageExpansionExecutor(run_id=9910)

        with (
            patch("stockanalysis.operations.professional_coverage_expansion.run_sec_companyfacts_upsert") as companyfacts,
            patch(
                "stockanalysis.operations.professional_coverage_expansion.run_financial_metric_normalization"
            ) as normalization,
            patch("stockanalysis.operations.professional_coverage_expansion.run_peer_relative_analysis") as peer,
            patch("stockanalysis.operations.professional_coverage_expansion.run_financial_forecast_inputs") as forecast,
            patch(
                "stockanalysis.operations.professional_coverage_expansion.run_reported_segment_footnote_parser"
            ) as segment_parser,
            patch("stockanalysis.operations.professional_coverage_expansion.run_segment_footnote_evidence") as segment,
            patch("stockanalysis.operations.professional_coverage_expansion.run_sum_of_parts_valuation") as sotp,
            patch("stockanalysis.operations.professional_coverage_expansion.run_valuation_snapshot") as valuation,
            patch(
                "stockanalysis.operations.professional_coverage_expansion.run_industry_competitive_positioning"
            ) as positioning,
            patch("stockanalysis.operations.professional_coverage_expansion.run_equity_research_reporting") as research,
        ):
            companyfacts.side_effect = [
                {"instrument_symbol": "AAPL", "fact_count": 6},
                ValueError("SEC companyfacts payload for `0001577552` does not contain supported facts"),
            ]
            normalization.return_value = {"report_name": "financial_metric_normalization"}
            peer.return_value = {"report_name": "peer_relative_analysis"}
            forecast.return_value = {"report_name": "financial_forecast_inputs"}
            segment_parser.return_value = {"report_name": "reported_segment_footnote_parser"}
            segment.return_value = {"report_name": "segment_footnote_evidence"}
            sotp.return_value = {"report_name": "sum_of_parts_valuation"}
            valuation.return_value = {"report_name": "valuation_snapshot"}
            positioning.return_value = {"report_name": "industry_competitive_positioning"}
            research.return_value = {"report_name": "equity_research_reporting"}

            report = run_professional_coverage_expansion(
                config=type("Config", (), {})(),
                as_of_date=date(2026, 5, 25),
                limit=3,
                companyfacts_limit=2,
                research_limit=2,
                research_provider="fixture",
                company_tickers_json_path=str(FIXTURES_DIR / "sec_company_tickers_exchange_sample.json"),
                execute=True,
                executor=executor,
            )

        self.assertEqual(report["status"], "completed_with_failures")
        self.assertEqual(report["companyfacts_success_count"], 1)
        self.assertEqual(report["companyfacts_failed_count"], 1)
        self.assertEqual(report["failed_companyfacts_reports"][0]["symbol"], "BABA")
        normalization.assert_called_once()
        peer.assert_called_once()
        forecast.assert_called_once()
        segment.assert_called_once()
        sotp.assert_called_once()
        valuation.assert_called_once()
        positioning.assert_called_once()
        research.assert_called_once()
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])


if __name__ == "__main__":
    unittest.main()
