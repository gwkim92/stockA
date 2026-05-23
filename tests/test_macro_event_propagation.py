from __future__ import annotations

import json
import unittest
from datetime import date
from decimal import Decimal

from stockanalysis.signal.macro_event_propagation import (
    MacroEventPropagationCandidate,
    compute_propagated_instrument_impacts,
    load_macro_event_propagation_candidates,
    render_macro_event_propagation_candidate_lookup_sql,
    render_propagated_instrument_impact_upsert_sql,
    run_macro_event_propagation,
)


class FakeExecutor:
    def __init__(self, *, run_id: int = 7001, fail_on_upsert: bool = False) -> None:
        self.run_id = run_id
        self.fail_on_upsert = fail_on_upsert
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- macro event propagation candidate lookup"):
            return json.dumps(
                [
                    {
                        "event_id": 11,
                        "event_title": "Fed signals higher for longer",
                        "event_at": "2026-05-20T12:00:00Z",
                        "node_id": 101,
                        "node_code": "MACRO_RATES_FED",
                        "node_name": "Fed and rates",
                        "theme_impact_direction": "risk_review",
                        "theme_impact_strength": "0.8000",
                        "theme_confidence": "0.9000",
                        "theme_rationale": "Policy rate shock.",
                        "instrument_id": 501,
                        "primary_symbol": "SPY",
                        "exposure_weight": "0.6500",
                        "sensitivity_direction": "negative",
                        "exposure_confidence": "0.7500",
                        "exposure_rationale": "Broad equity duration exposure.",
                    },
                    {
                        "event_id": 11,
                        "event_title": "Fed signals higher for longer",
                        "event_at": "2026-05-20T12:00:00Z",
                        "node_id": 101,
                        "node_code": "MACRO_RATES_FED",
                        "node_name": "Fed and rates",
                        "theme_impact_direction": "risk_review",
                        "theme_impact_strength": "0.8000",
                        "theme_confidence": "0.9000",
                        "theme_rationale": "Policy rate shock.",
                        "instrument_id": 701,
                        "primary_symbol": "TLT",
                        "exposure_weight": "0.9000",
                        "sensitivity_direction": "negative",
                        "exposure_confidence": "0.8500",
                        "exposure_rationale": "Long duration bond exposure.",
                    },
                ]
            )
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)
        if self.fail_on_upsert and "insert into signal.propagated_instrument_impact" in sql:
            raise RuntimeError("boom")


class MacroEventPropagationTests(unittest.TestCase):
    def test_candidate_lookup_uses_theme_impacts_and_factor_exposure(self) -> None:
        sql = render_macro_event_propagation_candidate_lookup_sql(as_of_date=date(2026, 5, 20), limit=25)

        self.assertIn("event.event_classification_impact", sql)
        self.assertIn("ref.instrument_factor_exposure", sql)
        self.assertIn("ref.classification_node", sql)
        self.assertNotIn("event.event_instrument_impact", sql)
        self.assertIn("row_number() over", sql)
        self.assertIn("where exposure_rank = 1", sql)
        self.assertIn("limit 25", sql)

    def test_load_candidates(self) -> None:
        rows = load_macro_event_propagation_candidates(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 20),
            executor=FakeExecutor(),
        )

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].node_code, "MACRO_RATES_FED")
        self.assertEqual(rows[0].primary_symbol, "SPY")
        self.assertEqual(rows[0].exposure_weight, Decimal("0.6500"))

    def test_compute_propagated_impacts_inverts_negative_sensitivity(self) -> None:
        rows = compute_propagated_instrument_impacts(
            (
                MacroEventPropagationCandidate(
                    event_id=11,
                    event_title="Fed cut",
                    event_at="2026-05-20T12:00:00Z",
                    node_id=101,
                    node_code="MACRO_RATES_FED",
                    node_name="Fed and rates",
                    theme_impact_direction="supportive",
                    theme_impact_strength=Decimal("0.8000"),
                    theme_confidence=Decimal("0.9000"),
                    theme_rationale="Lower rates.",
                    instrument_id=501,
                    primary_symbol="TLT",
                    exposure_weight=Decimal("0.9000"),
                    sensitivity_direction="negative",
                    exposure_confidence=Decimal("0.8500"),
                    exposure_rationale="Long-duration exposure.",
                ),
                MacroEventPropagationCandidate(
                    event_id=12,
                    event_title="Energy shock",
                    event_at="2026-05-20T13:00:00Z",
                    node_id=202,
                    node_code="ENERGY_GEOPOLITICS",
                    node_name="Energy geopolitics",
                    theme_impact_direction="supportive",
                    theme_impact_strength=Decimal("0.7000"),
                    theme_confidence=Decimal("0.8000"),
                    theme_rationale="Oil shock.",
                    instrument_id=601,
                    primary_symbol="XOM",
                    exposure_weight=Decimal("0.7500"),
                    sensitivity_direction="positive",
                    exposure_confidence=Decimal("0.8000"),
                    exposure_rationale="Oil leverage.",
                ),
            )
        )

        self.assertEqual(rows[0].impact_direction, "risk_review")
        self.assertEqual(rows[0].impact_strength, Decimal("0.7200"))
        self.assertEqual(rows[0].confidence, Decimal("0.8500"))
        self.assertEqual(rows[1].impact_direction, "supportive")

    def test_compute_propagated_impacts_deduplicates_same_event_node_instrument(self) -> None:
        rows = compute_propagated_instrument_impacts(
            (
                MacroEventPropagationCandidate(
                    event_id=21,
                    event_title="Quantum policy",
                    event_at="2026-05-20T12:00:00Z",
                    node_id=301,
                    node_code="QUANTUM_COMPUTING_POLICY",
                    node_name="Quantum policy",
                    theme_impact_direction="supportive",
                    theme_impact_strength=Decimal("0.6000"),
                    theme_confidence=Decimal("0.6000"),
                    theme_rationale="Policy support.",
                    instrument_id=901,
                    primary_symbol="QUBT",
                    exposure_weight=Decimal("0.6000"),
                    sensitivity_direction="positive",
                    exposure_confidence=Decimal("0.6000"),
                    exposure_rationale="Legacy duplicate.",
                ),
                MacroEventPropagationCandidate(
                    event_id=21,
                    event_title="Quantum policy",
                    event_at="2026-05-20T12:00:00Z",
                    node_id=301,
                    node_code="QUANTUM_COMPUTING_POLICY",
                    node_name="Quantum policy",
                    theme_impact_direction="supportive",
                    theme_impact_strength=Decimal("0.6000"),
                    theme_confidence=Decimal("0.8000"),
                    theme_rationale="Policy support.",
                    instrument_id=901,
                    primary_symbol="QUBT",
                    exposure_weight=Decimal("0.9000"),
                    sensitivity_direction="positive",
                    exposure_confidence=Decimal("0.8000"),
                    exposure_rationale="Preferred theme membership.",
                ),
            )
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].primary_symbol, "QUBT")
        self.assertEqual(rows[0].confidence, Decimal("0.8000"))
        self.assertEqual(rows[0].impact_strength, Decimal("0.5400"))

    def test_upsert_sql_is_idempotent(self) -> None:
        impacts = compute_propagated_instrument_impacts(
            (
                MacroEventPropagationCandidate(
                    event_id=11,
                    event_title="Fed",
                    event_at="2026-05-20T12:00:00Z",
                    node_id=101,
                    node_code="MACRO_RATES_FED",
                    node_name="Fed and rates",
                    theme_impact_direction="risk_review",
                    theme_impact_strength=Decimal("0.8000"),
                    theme_confidence=Decimal("0.9000"),
                    theme_rationale="Rate shock.",
                    instrument_id=501,
                    primary_symbol="SPY",
                    exposure_weight=Decimal("0.6500"),
                    sensitivity_direction="negative",
                    exposure_confidence=Decimal("0.7500"),
                    exposure_rationale="Broad equities.",
                ),
            )
        )
        sql = render_propagated_instrument_impact_upsert_sql(impacts, source_run_id=77)

        self.assertIn("insert into signal.propagated_instrument_impact", sql)
        self.assertIn("on conflict (event_id, node_id, instrument_id, propagation_kind) do update", sql)
        self.assertIn("77::bigint", sql)

    def test_run_dry_run_does_not_write(self) -> None:
        executor = FakeExecutor()

        report = run_macro_event_propagation(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 20),
            execute=False,
            executor=executor,
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["candidate_count"], 2)
        self.assertEqual(report["propagated_impact_count"], 2)
        self.assertEqual(executor.non_query_sql, [])

    def test_run_execute_records_pipeline_run_and_upserts(self) -> None:
        executor = FakeExecutor(run_id=7002)

        report = run_macro_event_propagation(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 20),
            execute=True,
            executor=executor,
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 7002)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("insert into signal.propagated_instrument_impact", executor.non_query_sql[0])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[1])

    def test_run_execute_marks_pipeline_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=7003, fail_on_upsert=True)

        with self.assertRaises(RuntimeError):
            run_macro_event_propagation(
                config=type("Config", (), {})(),
                as_of_date=date(2026, 5, 20),
                execute=True,
                executor=executor,
            )

        self.assertIn("status = 'failed'", executor.non_query_sql[-1])


if __name__ == "__main__":
    unittest.main()
