from __future__ import annotations

import json
import unittest
from datetime import date
from unittest.mock import patch

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.financial_period_source_linkage import (
    DEFAULT_MODEL_NAME,
    render_financial_period_source_linkage_backfill_sql,
    render_financial_period_source_linkage_preview_sql,
    render_financial_period_source_raw_fetch_candidates_sql,
    run_financial_period_source_linkage,
)


class FakeSourceLinkageExecutor:
    def __init__(self, *, run_id: int = 1040) -> None:
        self.run_id = run_id
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- financial period source linkage preview"):
            return json.dumps(
                {
                    "as_of_date": "2026-05-26",
                    "model_name": DEFAULT_MODEL_NAME,
                    "statement_scope": "annual",
                    "symbol": "AAPL",
                    "source_period_count": 4,
                    "linked_period_count": 1,
                    "unlinked_period_count": 3,
                    "sec_source_document_count": 2,
                    "sec_raw_document_count": 0,
                    "link_candidate_count": 2,
                    "raw_fetch_candidate_count": 1,
                    "post_backfill_raw_fetch_candidate_count": 1,
                }
            )
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if sql.startswith("-- financial period source linkage backfill"):
            return json.dumps(
                {
                    "as_of_date": "2026-05-26",
                    "source_run_id": self.run_id,
                    "statement_scope": "annual",
                    "symbol": "AAPL",
                    "linked_period_count": 2,
                    "linked_instrument_count": 1,
                    "source_document_count": 2,
                    "sample_links": [],
                    "recommendation_scoring_mutated": False,
                }
            )
        if sql.startswith("-- financial period source raw fetch candidates"):
            return json.dumps(
                [
                    {
                        "document_id": 77,
                        "external_document_id": "0000320193-24-000123",
                        "title": "10-K - Apple Inc.",
                        "url": "https://www.sec.gov/Archives/edgar/data/320193/example.htm",
                        "primary_symbol": "AAPL",
                        "period_end": "2024-09-28",
                        "report_date": "2024-11-01",
                    }
                ]
            )
        raise AssertionError(f"Unexpected SQL: {sql[:160]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class FinancialPeriodSourceLinkageTests(unittest.TestCase):
    def test_preview_sql_is_read_only_and_reports_coverage(self) -> None:
        sql = render_financial_period_source_linkage_preview_sql(
            as_of_date=date(2026, 5, 26),
            statement_scope="annual",
            symbol="AAPL",
        )
        lowered = sql.lower()

        self.assertIn("-- financial period source linkage preview", sql)
        self.assertIn("market.financial_statement_period", sql)
        self.assertIn("ingest.source_document", sql)
        self.assertIn("source_period_count", sql)
        self.assertIn("linked_period_count", sql)
        self.assertIn("raw_fetch_candidate_count", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_backfill_sql_links_null_source_document_periods_without_scoring_mutation(self) -> None:
        sql = render_financial_period_source_linkage_backfill_sql(
            as_of_date=date(2026, 5, 26),
            source_run_id=1041,
            statement_scope="annual",
            symbol="AAPL",
        )

        self.assertIn("-- financial period source linkage backfill", sql)
        self.assertIn("update market.financial_statement_period", sql)
        self.assertIn("set source_document_id = candidate.document_id", sql)
        self.assertIn("period.source_document_id is null", sql)
        self.assertIn("recommendation_scoring_mutated", sql)
        self.assertNotIn("signal.recommendation_score_component", sql)
        self.assertIn("1041", sql)

    def test_raw_fetch_candidates_sql_is_bounded(self) -> None:
        sql = render_financial_period_source_raw_fetch_candidates_sql(
            as_of_date=date(2026, 5, 26),
            statement_scope="annual",
            symbol="AAPL",
            limit=2,
        )
        lowered = sql.lower()

        self.assertIn("-- financial period source raw fetch candidates", sql)
        self.assertIn("doc.raw_storage_uri is null", sql)
        self.assertIn("limit 2", lowered)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_dry_run_reads_preview_without_external_sec_calls_or_writes(self) -> None:
        executor = FakeSourceLinkageExecutor()

        report = run_financial_period_source_linkage(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 26),
            statement_scope="annual",
            cik="320193",
            fallback_symbol="AAPL",
            execute=False,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["report_name"], "financial_period_source_linkage")
        self.assertEqual(report["preview"]["link_candidate_count"], 2)  # type: ignore[index]
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertEqual(executor.non_query_sql, [])
        self.assertEqual(len(executor.scalar_sql), 1)

    def test_execute_refreshes_sec_data_backfills_links_and_fetches_bounded_raw_docs(self) -> None:
        executor = FakeSourceLinkageExecutor(run_id=1042)

        with (
            patch("stockanalysis.operations.financial_period_source_linkage.run_sec_filings_upsert") as filings,
            patch("stockanalysis.operations.financial_period_source_linkage.run_sec_companyfacts_upsert") as companyfacts,
            patch("stockanalysis.operations.financial_period_source_linkage.run_sec_filing_raw_fetch") as raw_fetch,
        ):
            filings.return_value = {"run_id": 201, "filing_count": 3}
            companyfacts.return_value = {"run_id": 202, "fact_count": 9}
            raw_fetch.return_value = {
                "run_id": 203,
                "status": "succeeded",
                "external_document_id": "0000320193-24-000123",
            }

            report = run_financial_period_source_linkage(
                config=RuntimeConfig(psql_command="psql"),
                as_of_date=date(2026, 5, 26),
                statement_scope="annual",
                cik="320193",
                fallback_symbol="AAPL",
                max_filings=3,
                raw_fetch_limit=1,
                raw_artifact_root="/tmp/sec-raw",
                execute=True,
                executor=executor,  # type: ignore[arg-type]
            )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 1042)
        self.assertEqual(report["backfill"]["linked_period_count"], 2)  # type: ignore[index]
        self.assertEqual(report["raw_fetch_success_count"], 1)
        self.assertFalse(report["recommendation_scoring_mutated"])
        filings.assert_called_once()
        companyfacts.assert_called_once()
        raw_fetch.assert_called_once()
        self.assertEqual(raw_fetch.call_args.args[0], "0000320193-24-000123")
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("-- financial period source linkage backfill", executor.scalar_sql[2])
        self.assertIn("-- financial period source raw fetch candidates", executor.scalar_sql[3])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])


if __name__ == "__main__":
    unittest.main()
