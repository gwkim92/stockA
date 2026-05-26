from __future__ import annotations

import json
import unittest
from datetime import date
from unittest.mock import patch

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.sec.models import SecFilingRecord, SecFilingsSyncResult
from stockanalysis.operations.professional_source_blocker_raw_filing_remediation import (
    build_professional_source_blocker_raw_filing_decision,
    render_professional_source_blocker_raw_filing_decision_insert_sql,
    run_professional_source_blocker_raw_filing_remediation,
)


class FakeRawFilingDecisionExecutor:
    def __init__(self, *, run_id: int = 9101, eval_run_id: int = 8101) -> None:
        self.run_id = run_id
        self.eval_run_id = eval_run_id
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        lowered = sql.lower()
        if "insert into ops.pipeline_run" in lowered:
            return str(self.run_id)
        if "insert into ai.eval_run" in lowered:
            return str(self.eval_run_id)
        raise AssertionError(f"unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class ProfessionalSourceBlockerRawFilingRemediationTests(unittest.TestCase):
    def test_prospectus_only_companyfacts_ffd_records_durable_exclusion(self) -> None:
        decision = build_professional_source_blocker_raw_filing_decision(
            symbol="EROK",
            cik="0002104882",
            as_of_date=date(2026, 5, 26),
            filings=_erok_like_filings(),
            companyfacts_payload={
                "cik": 2104882,
                "entityName": "EagleRock Land, LLC",
                "facts": {
                    "ffd": {
                        "TtlOfferingAmt": {
                            "units": {"USD": [{"val": 1, "fy": 2026, "form": "S-1"}]}
                        }
                    }
                },
            },
        )

        self.assertEqual(decision["decision_status"], "durable_exclusion_until_periodic_filing")
        self.assertEqual(decision["blocker_code"], "ipo_prospectus_without_standard_periodic_financials")
        self.assertTrue(decision["durable_exclusion"])
        self.assertFalse(decision["remediation_allowed"])
        self.assertEqual(decision["latest_prospectus_filing"]["form_type"], "424B4")
        self.assertIsNone(decision["latest_supported_periodic_filing"])
        self.assertEqual(decision["companyfacts"]["namespaces"], ["ffd"])
        self.assertFalse(decision["companyfacts"]["has_us_gaap"])
        self.assertFalse(decision["guardrails"]["recommendation_scoring_mutated"])
        self.assertFalse(decision["guardrails"]["automatic_order_allowed"])
        self.assertEqual(decision["guardrails"]["order_boundary"], "read_only_no_order")

    def test_periodic_xbrl_candidate_is_not_auto_inserted_as_financial_facts(self) -> None:
        filings = SecFilingsSyncResult(
            cik="0000000001",
            company_name="Periodic Candidate Inc.",
            filings=(
                _filing("10-K", "2026-03-01", "0000000001-26-000001", is_xbrl=True, is_inline_xbrl=True),
            ),
        )

        decision = build_professional_source_blocker_raw_filing_decision(
            symbol="TEST",
            cik="1",
            as_of_date=date(2026, 5, 26),
            filings=filings,
            companyfacts_payload={"cik": 1, "entityName": "Periodic Candidate Inc.", "facts": {"ffd": {}}},
        )

        self.assertEqual(decision["decision_status"], "periodic_raw_xbrl_candidate")
        self.assertEqual(decision["blocker_code"], "raw_periodic_xbrl_parser_required")
        self.assertFalse(decision["durable_exclusion"])
        self.assertFalse(decision["remediation_allowed"])
        self.assertEqual(decision["latest_supported_periodic_filing"]["form_type"], "10-K")
        self.assertEqual(decision["guardrails"]["synthetic_financial_facts_allowed"], False)

    def test_standard_companyfacts_available_points_to_existing_source_linkage(self) -> None:
        decision = build_professional_source_blocker_raw_filing_decision(
            symbol="AAPL",
            cik="0000320193",
            as_of_date=date(2026, 5, 26),
            filings=SecFilingsSyncResult(cik="0000320193", company_name="Apple Inc.", filings=tuple()),
            companyfacts_payload={
                "cik": 320193,
                "entityName": "Apple Inc.",
                "facts": {"us-gaap": {"Revenues": {"units": {"USD": []}}}},
            },
        )

        self.assertEqual(decision["decision_status"], "standard_companyfacts_available")
        self.assertTrue(decision["remediation_allowed"])
        self.assertIn("financial-period-source-linkage-run", decision["remediation_command"])

    def test_render_insert_records_eval_without_financial_writes(self) -> None:
        sql = render_professional_source_blocker_raw_filing_decision_insert_sql(
            score_json={
                "symbol": "EROK",
                "decision_status": "durable_exclusion_until_periodic_filing",
                "guardrails": {"recommendation_scoring_mutated": False},
            }
        )

        self.assertIn("insert into ai.eval_run", sql)
        self.assertIn("professional_source_blocker_raw_filing_remediation", sql)
        self.assertIn("professional-source-blocker-raw-filing-remediation-v1", sql)
        self.assertNotIn("insert into market.financial_statement", sql.lower())
        self.assertNotIn("update signal.recommendation", sql.lower())

    def test_execute_records_pipeline_and_eval_run(self) -> None:
        executor = FakeRawFilingDecisionExecutor(run_id=9102, eval_run_id=8102)
        with patch(
            "stockanalysis.operations.professional_source_blocker_raw_filing_remediation.load_sec_filings_sync_result",
            return_value=_erok_like_filings(),
        ), patch(
            "stockanalysis.operations.professional_source_blocker_raw_filing_remediation._load_companyfacts_payload",
            return_value={"cik": 2104882, "entityName": "EagleRock Land, LLC", "facts": {"ffd": {}}},
        ):
            report = run_professional_source_blocker_raw_filing_remediation(
                config=RuntimeConfig(psql_command="docker exec psql"),
                as_of_date=date(2026, 5, 26),
                cik="0002104882",
                fallback_symbol="EROK",
                execute=True,
                executor=executor,
            )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9102)
        self.assertEqual(report["eval_run_id"], 8102)
        self.assertEqual(report["decision"]["decision_status"], "durable_exclusion_until_periodic_filing")
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[0].lower())
        self.assertIn("insert into ai.eval_run", executor.scalar_sql[1].lower())
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])


def _erok_like_filings() -> SecFilingsSyncResult:
    return SecFilingsSyncResult(
        cik="0002104882",
        company_name="EagleRock Land, LLC",
        filings=(
            _filing("S-8", "2026-05-22", "0002104882-26-000010", is_xbrl=True, is_inline_xbrl=True),
            _filing("8-K", "2026-05-21", "0002104882-26-000009"),
            _filing("424B4", "2026-05-14", "0001193125-26-224302", primary_document="d37594d424b4.htm"),
        ),
    )


def _filing(
    form_type: str,
    filing_date: str,
    accession_number: str,
    *,
    primary_document: str = "index.htm",
    is_xbrl: bool | None = False,
    is_inline_xbrl: bool | None = False,
) -> SecFilingRecord:
    cik = "0002104882"
    return SecFilingRecord(
        cik=cik,
        company_name="EagleRock Land, LLC",
        accession_number=accession_number,
        form_type=form_type,
        filing_date=date.fromisoformat(filing_date),
        primary_document=primary_document,
        primary_doc_description=form_type,
        filing_url=f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number.replace('-', '')}/{primary_document}",
        filing_index_url=f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}-index.html",
        items=None,
        file_number=None,
        film_number=None,
        is_xbrl=is_xbrl,
        is_inline_xbrl=is_inline_xbrl,
    )


if __name__ == "__main__":
    unittest.main()
