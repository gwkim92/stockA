from __future__ import annotations

import json
import unittest

from stockanalysis.ingest.sec.instrument_impact import (
    extract_company_name_from_event,
    load_pending_sec_event_instrument_candidates,
    resolve_instrument_for_company,
    run_event_instrument_impact_bootstrap,
)
from stockanalysis.ingest.sec.models import SecEventInstrumentImpactCandidate
from stockanalysis.ingest.sec.sql import (
    render_event_instrument_impact_upsert_sql,
    render_instrument_lookup_by_company_name_sql,
    render_pending_sec_event_instrument_candidates_sql,
)


class FakeExecutor:
    def __init__(self, *, run_id: int = 1001, fail_on_impact: bool = False, missing_instrument: bool = False) -> None:
        self.run_id = run_id
        self.fail_on_impact = fail_on_impact
        self.missing_instrument = missing_instrument
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []
        self.pending_candidates = [
            {
                "event_id": 21,
                "event_type": "sec_annual_report_filed",
                "dedupe_key": "sec_edgar:0000320193-24-000123:sec_annual_report_filed",
                "title": "Annual report filed: Apple Inc.",
                "summary": "Apple Inc. filed SEC Form 10-K. Excerpt: Annual Report.",
            },
            {
                "event_id": 22,
                "event_type": "sec_quarterly_report_filed",
                "dedupe_key": "sec_edgar:0000320193-24-000101:sec_quarterly_report_filed",
                "title": "Quarterly report filed: Apple Inc.",
                "summary": "Apple Inc. filed SEC Form 10-Q. Excerpt: Quarterly Report.",
            },
        ]
        self.instrument_payload = {
            "instrument_id": 501,
            "primary_symbol": "AAPL",
            "instrument_name": "Apple Inc. Common Stock",
            "issuer_display_name": "Apple Inc.",
            "issuer_legal_name": "Apple Inc.",
        }

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "from event.event e" in sql:
            return json.dumps(self.pending_candidates)
        if "from ref.instrument i" in sql:
            if self.missing_instrument:
                raise RuntimeError("no rows")
            return json.dumps(self.instrument_payload)
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)
        if self.fail_on_impact and "insert into event.event_instrument_impact" in sql and "22" in sql:
            raise RuntimeError("boom")


class SecInstrumentImpactTests(unittest.TestCase):
    def test_render_pending_sec_event_instrument_candidates_sql(self) -> None:
        sql = render_pending_sec_event_instrument_candidates_sql(limit=9)
        self.assertIn("event.event_instrument_impact", sql)
        self.assertIn("limit 9", sql)
        self.assertIn("sec_edgar:%", sql)

    def test_render_instrument_lookup_by_company_name_sql(self) -> None:
        sql = render_instrument_lookup_by_company_name_sql("Apple Inc.")
        self.assertIn("from ref.instrument i", sql)
        self.assertIn("Apple Inc.", sql)

    def test_render_event_instrument_impact_upsert_sql(self) -> None:
        sql = render_event_instrument_impact_upsert_sql(
            event_id=21,
            instrument_id=501,
            impact_direction="neutral",
            impact_strength=0.75,
            confidence=0.95,
            rationale="SEC annual report maps to AAPL.",
        )
        self.assertIn("insert into event.event_instrument_impact", sql)
        self.assertIn("501", sql)
        self.assertIn("0.75", sql)

    def test_load_pending_sec_event_instrument_candidates(self) -> None:
        executor = FakeExecutor()
        candidates = load_pending_sec_event_instrument_candidates(limit=5, executor=executor)
        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0].event_id, 21)
        self.assertEqual(candidates[1].event_type, "sec_quarterly_report_filed")

    def test_extract_company_name_from_event(self) -> None:
        candidate = SecEventInstrumentImpactCandidate(
            event_id=21,
            event_type="sec_annual_report_filed",
            dedupe_key="x",
            title="Annual report filed: Apple Inc.",
            summary="Apple Inc. filed SEC Form 10-K.",
        )
        self.assertEqual(extract_company_name_from_event(candidate), "Apple Inc.")

    def test_resolve_instrument_for_company(self) -> None:
        executor = FakeExecutor()
        instrument = resolve_instrument_for_company("Apple Inc.", executor=executor)
        self.assertEqual(instrument.instrument_id, 501)
        self.assertEqual(instrument.primary_symbol, "AAPL")

    def test_run_event_instrument_impact_bootstrap(self) -> None:
        executor = FakeExecutor(run_id=1101)
        summary = run_event_instrument_impact_bootstrap(
            config=type("Config", (), {})(),
            limit=10,
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 1101)
        self.assertEqual(summary["requested_event_count"], 2)
        self.assertEqual(summary["succeeded_event_count"], 2)
        self.assertEqual(summary["failed_event_count"], 0)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("insert into event.event_instrument_impact", executor.non_query_sql[0])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])

    def test_run_event_instrument_impact_bootstrap_continues_after_failure(self) -> None:
        executor = FakeExecutor(run_id=1102, fail_on_impact=True)
        summary = run_event_instrument_impact_bootstrap(
            config=type("Config", (), {})(),
            limit=10,
            executor=executor,
        )
        self.assertEqual(summary["requested_event_count"], 2)
        self.assertEqual(summary["succeeded_event_count"], 1)
        self.assertEqual(summary["failed_event_count"], 1)
        self.assertEqual(summary["results"][1]["status"], "failed")
        self.assertIn("status = 'failed'", executor.non_query_sql[-1])

    def test_run_event_instrument_impact_bootstrap_fails_when_instrument_missing(self) -> None:
        executor = FakeExecutor(run_id=1103, missing_instrument=True)
        summary = run_event_instrument_impact_bootstrap(
            config=type("Config", (), {})(),
            limit=10,
            executor=executor,
        )
        self.assertEqual(summary["requested_event_count"], 2)
        self.assertEqual(summary["succeeded_event_count"], 0)
        self.assertEqual(summary["failed_event_count"], 2)
