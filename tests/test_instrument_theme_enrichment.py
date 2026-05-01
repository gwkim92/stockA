from __future__ import annotations

import json
import unittest
from datetime import date

from stockanalysis.signal.theme_enrichment import (
    load_instrument_theme_membership_candidates,
    load_selected_universe_instruments,
    render_instrument_theme_membership_candidate_lookup_sql,
    render_instrument_theme_membership_replace_sql,
    render_selected_universe_instruments_lookup_sql,
    run_instrument_theme_enrichment,
)


class FakeExecutor:
    def __init__(self, *, run_id: int = 971, fail_on_replace: bool = False) -> None:
        self.run_id = run_id
        self.fail_on_replace = fail_on_replace
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- instrument theme selected instruments lookup"):
            return json.dumps(
                [
                    {
                        "universe_batch_id": 1001,
                        "instrument_id": 501,
                        "primary_symbol": "AAPL",
                    },
                    {
                        "universe_batch_id": 1001,
                        "instrument_id": 601,
                        "primary_symbol": "BABA",
                    },
                ]
            )
        if sql.startswith("-- instrument theme membership candidate lookup"):
            return json.dumps(
                [
                    {
                        "instrument_id": 501,
                        "primary_symbol": "AAPL",
                        "node_id": 11,
                        "node_code": "ANNUAL_REPORTING",
                        "node_name": "Annual Reporting",
                        "membership_type": "derived_theme",
                        "confidence": "0.9500",
                        "supporting_event_count": 1,
                        "first_event_date": "2024-11-01",
                        "latest_event_date": "2024-11-01",
                        "source_document_id": 71,
                    }
                ]
            )
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)
        if self.fail_on_replace and "insert into ref.instrument_classification_membership" in sql:
            raise RuntimeError("boom")


class InstrumentThemeEnrichmentTests(unittest.TestCase):
    def test_render_selected_universe_instruments_lookup_sql(self) -> None:
        sql = render_selected_universe_instruments_lookup_sql(
            as_of_date=date(2024, 11, 1),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
        )
        self.assertIn("signal.strategy_universe_batch", sql)
        self.assertIn("signal.strategy_universe_member", sql)
        self.assertIn("fixture-v1", sql)

    def test_render_instrument_theme_membership_candidate_lookup_sql(self) -> None:
        sql = render_instrument_theme_membership_candidate_lookup_sql(
            as_of_date=date(2024, 11, 1),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
        )
        self.assertIn("event.event_instrument_impact", sql)
        self.assertIn("event.event_classification_impact", sql)
        self.assertIn("internal_theme", sql)

    def test_load_selected_universe_instruments(self) -> None:
        rows = load_selected_universe_instruments(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=FakeExecutor(),
        )
        self.assertEqual([row.primary_symbol for row in rows], ["AAPL", "BABA"])
        self.assertEqual(rows[0].universe_batch_id, 1001)

    def test_load_instrument_theme_membership_candidates(self) -> None:
        rows = load_instrument_theme_membership_candidates(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=FakeExecutor(),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].primary_symbol, "AAPL")
        self.assertEqual(rows[0].node_code, "ANNUAL_REPORTING")
        self.assertEqual(str(rows[0].confidence), "0.9500")

    def test_render_instrument_theme_membership_replace_sql(self) -> None:
        executor = FakeExecutor()
        selected = load_selected_universe_instruments(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=executor,
        )
        candidates = load_instrument_theme_membership_candidates(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=executor,
        )
        sql = render_instrument_theme_membership_replace_sql(selected, candidates)
        self.assertIn("delete from ref.instrument_classification_membership", sql)
        self.assertIn("insert into ref.instrument_classification_membership", sql)
        self.assertIn("11::bigint", sql)
        self.assertIn("'derived_theme'", sql)

    def test_run_instrument_theme_enrichment_records_pipeline_run_and_summary(self) -> None:
        executor = FakeExecutor(run_id=981)
        summary = run_instrument_theme_enrichment(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 981)
        self.assertEqual(summary["universe_batch_id"], 1001)
        self.assertEqual(summary["selected_instrument_count"], 2)
        self.assertEqual(summary["membership_count"], 1)
        self.assertEqual(summary["node_code_preview"], ["ANNUAL_REPORTING"])
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[1])

    def test_run_instrument_theme_enrichment_marks_pipeline_run_failed_when_replace_errors(self) -> None:
        executor = FakeExecutor(run_id=982, fail_on_replace=True)
        with self.assertRaises(RuntimeError):
            run_instrument_theme_enrichment(
                config=type("Config", (), {})(),
                as_of_date=date(2024, 11, 1),
                strategy_name="long_term_core",
                horizon_type="long_term",
                universe_version="fixture-v1",
                executor=executor,
            )
        self.assertIn("status = 'failed'", executor.non_query_sql[-1])
