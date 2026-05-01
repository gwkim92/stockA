from __future__ import annotations

import json
import unittest

from stockanalysis.ingest.sec.classification_impact import (
    load_pending_sec_event_impact_candidates,
    run_event_classification_impact_bootstrap,
)
from stockanalysis.ingest.sec.sql import (
    render_event_classification_impact_upsert_sql,
    render_pending_sec_event_impact_candidates_sql,
    render_reporting_classification_bootstrap_sql,
)


class FakeExecutor:
    def __init__(self, *, run_id: int = 801, fail_on_impact: bool = False) -> None:
        self.run_id = run_id
        self.fail_on_impact = fail_on_impact
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []
        self.pending_candidates = [
            {
                "event_id": 11,
                "event_type": "sec_annual_report_filed",
                "dedupe_key": "sec_edgar:0000320193-24-000123:sec_annual_report_filed",
                "title": "Annual report filed: Apple Inc.",
            },
            {
                "event_id": 12,
                "event_type": "sec_quarterly_report_filed",
                "dedupe_key": "sec_edgar:0000320193-24-000101:sec_quarterly_report_filed",
                "title": "Quarterly report filed: Apple Inc.",
            },
        ]

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "from event.event e" in sql:
            return json.dumps(self.pending_candidates)
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)
        if self.fail_on_impact and "insert into event.event_classification_impact" in sql and "QUARTERLY_REPORTING" in sql:
            raise RuntimeError("boom")


class SecClassificationImpactTests(unittest.TestCase):
    def test_render_pending_sec_event_impact_candidates_sql(self) -> None:
        sql = render_pending_sec_event_impact_candidates_sql(limit=7)
        self.assertIn("event.event_classification_impact", sql)
        self.assertIn("limit 7", sql)
        self.assertIn("sec_edgar:%", sql)

    def test_render_reporting_classification_bootstrap_sql(self) -> None:
        sql = render_reporting_classification_bootstrap_sql()
        self.assertIn("insert into ref.classification_node", sql)
        self.assertIn("PUBLIC_COMPANY_REPORTING", sql)
        self.assertIn("insert into ref.classification_edge", sql)

    def test_render_event_classification_impact_upsert_sql(self) -> None:
        sql = render_event_classification_impact_upsert_sql(
            event_id=11,
            node_code="ANNUAL_REPORTING",
            node_type="subtheme",
            impact_direction="neutral",
            impact_strength=0.75,
            confidence=0.95,
            rationale="Annual report filings are direct evidence for the annual reporting cycle.",
        )
        self.assertIn("insert into event.event_classification_impact", sql)
        self.assertIn("ANNUAL_REPORTING", sql)
        self.assertIn("0.75", sql)

    def test_load_pending_sec_event_impact_candidates(self) -> None:
        executor = FakeExecutor()
        candidates = load_pending_sec_event_impact_candidates(limit=5, executor=executor)
        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0].event_id, 11)
        self.assertEqual(candidates[1].event_type, "sec_quarterly_report_filed")

    def test_run_event_classification_impact_bootstrap(self) -> None:
        executor = FakeExecutor(run_id=901)
        summary = run_event_classification_impact_bootstrap(
            config=type("Config", (), {})(),
            limit=10,
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 901)
        self.assertEqual(summary["requested_event_count"], 2)
        self.assertEqual(summary["succeeded_event_count"], 2)
        self.assertEqual(summary["failed_event_count"], 0)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("insert into ref.classification_node", executor.non_query_sql[0])
        self.assertIn("insert into event.event_classification_impact", executor.non_query_sql[1])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])

    def test_run_event_classification_impact_bootstrap_continues_after_failure(self) -> None:
        executor = FakeExecutor(run_id=902, fail_on_impact=True)
        summary = run_event_classification_impact_bootstrap(
            config=type("Config", (), {})(),
            limit=10,
            executor=executor,
        )
        self.assertEqual(summary["requested_event_count"], 2)
        self.assertEqual(summary["succeeded_event_count"], 1)
        self.assertEqual(summary["failed_event_count"], 1)
        self.assertEqual(summary["results"][1]["status"], "failed")
        self.assertIn("status = 'failed'", executor.non_query_sql[-1])
