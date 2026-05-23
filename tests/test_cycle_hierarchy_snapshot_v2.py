from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
import unittest

from stockanalysis.signal.cycle_hierarchy_snapshot_v2 import (
    CycleHierarchyNodeInput,
    compute_cycle_hierarchy_snapshots,
    compute_cycle_hierarchy_transitions,
    load_cycle_hierarchy_snapshot_inputs,
    render_cycle_hierarchy_snapshot_input_lookup_sql,
    render_cycle_hierarchy_snapshot_upsert_sql,
    render_cycle_hierarchy_transition_insert_sql,
    run_cycle_hierarchy_snapshot_v2,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
MIGRATION_PATH = ROOT_DIR / "db" / "migrations" / "0018_cycle_hierarchy_snapshot_v2.sql"


class FakeExecutor:
    def __init__(self, *, run_id: int = 9101, fail_on_upsert: bool = False) -> None:
        self.run_id = run_id
        self.fail_on_upsert = fail_on_upsert
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- cycle hierarchy snapshot v2 input lookup"):
            return json.dumps(
                [
                    {
                        "node_id": 101,
                        "node_code": "MACRO_RATES_FED",
                        "node_name": "Macro Rates and Fed",
                        "node_type": "subtheme",
                        "base_cycle_state": None,
                        "base_cycle_score": None,
                        "trend_score": None,
                        "breadth_score": None,
                        "liquidity_score": None,
                        "valuation_pressure": None,
                        "parent_average_cycle_score": None,
                        "direct_event_count_30d": 2,
                        "hierarchical_event_count_30d": 0,
                        "average_event_confidence": "0.9000",
                        "previous_cycle_state": None,
                        "previous_cycle_score": None,
                        "evidence_event_ids": [11, 12],
                    },
                    {
                        "node_id": 201,
                        "node_code": "TECH_DOMAIN",
                        "node_name": "Technology Domain",
                        "node_type": "domain",
                        "base_cycle_state": "forming",
                        "base_cycle_score": "0.6000",
                        "trend_score": "0.6000",
                        "breadth_score": "0.6000",
                        "liquidity_score": "0.5000",
                        "valuation_pressure": "0.4000",
                        "parent_average_cycle_score": "0.7000",
                        "direct_event_count_30d": 0,
                        "hierarchical_event_count_30d": 4,
                        "average_event_confidence": "0.8000",
                        "previous_cycle_state": "expanding",
                        "previous_cycle_score": "0.6800",
                        "evidence_event_ids": [11, 13, 14, 15],
                    },
                    {
                        "node_id": 301,
                        "node_code": "AI_SEMICONDUCTOR_CYCLE",
                        "node_name": "AI Semiconductor Cycle",
                        "node_type": "subtheme",
                        "base_cycle_state": "neutral",
                        "base_cycle_score": "0.5000",
                        "trend_score": "0.5500",
                        "breadth_score": "0.5500",
                        "liquidity_score": "0.5000",
                        "valuation_pressure": "0.5000",
                        "parent_average_cycle_score": "0.5000",
                        "direct_event_count_30d": 1,
                        "hierarchical_event_count_30d": 0,
                        "average_event_confidence": "0.6000",
                        "previous_cycle_state": "forming",
                        "previous_cycle_score": "0.4600",
                        "evidence_event_ids": [16],
                    },
                ]
            )
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)
        if self.fail_on_upsert and "insert into signal.cycle_hierarchy_state_snapshot" in sql:
            raise RuntimeError("boom")


class EmptyExecutor:
    def execute_scalar(self, sql: str) -> str:
        return "[]"


class CycleHierarchySnapshotV2Tests(unittest.TestCase):
    def test_migration_creates_snapshot_and_transition_tables(self) -> None:
        sql = MIGRATION_PATH.read_text(encoding="utf-8").lower()

        self.assertIn("create table if not exists signal.cycle_hierarchy_state_snapshot", sql)
        self.assertIn("create table if not exists signal.cycle_hierarchy_transition_log", sql)
        self.assertIn("parent_alignment_score", sql)
        self.assertIn("conflict_flags jsonb", sql)
        self.assertIn("evidence_event_ids jsonb", sql)

    def test_input_lookup_uses_base_cycles_and_hierarchical_impacts(self) -> None:
        sql = render_cycle_hierarchy_snapshot_input_lookup_sql(as_of_date=date(2026, 5, 23))

        self.assertIn("signal.cycle_state_snapshot", sql)
        self.assertIn("signal.cycle_hierarchy_state_snapshot", sql)
        self.assertIn("signal.hierarchical_propagated_instrument_impact", sql)
        self.assertIn("parent_scores", sql)
        self.assertIn("previous_v2_snapshot", sql)

    def test_load_inputs(self) -> None:
        rows = load_cycle_hierarchy_snapshot_inputs(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 23),
            executor=FakeExecutor(),
        )

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0].node_code, "MACRO_RATES_FED")
        self.assertEqual(rows[1].hierarchical_event_count_30d, 4)
        self.assertEqual(rows[2].evidence_event_ids, (16,))

    def test_load_inputs_rejects_empty_rows(self) -> None:
        with self.assertRaises(ValueError):
            load_cycle_hierarchy_snapshot_inputs(
                config=type("Config", (), {})(),
                as_of_date=date(2026, 5, 23),
                executor=EmptyExecutor(),
            )

    def test_compute_snapshots_scores_levels_and_hysteresis(self) -> None:
        inputs = load_cycle_hierarchy_snapshot_inputs(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 23),
            executor=FakeExecutor(),
        )
        snapshots = compute_cycle_hierarchy_snapshots(inputs)
        by_code = {row.node_code: row for row in snapshots}

        self.assertEqual(by_code["MACRO_RATES_FED"].cycle_level, "macro")
        self.assertEqual(by_code["MACRO_RATES_FED"].cycle_score, Decimal("0.4400"))
        self.assertEqual(by_code["MACRO_RATES_FED"].cycle_state, "neutral")
        self.assertIn("base_cycle_missing", by_code["MACRO_RATES_FED"].conflict_flags)

        self.assertEqual(by_code["TECH_DOMAIN"].cycle_level, "domain")
        self.assertEqual(by_code["TECH_DOMAIN"].event_heat_score, Decimal("0.4000"))
        self.assertEqual(by_code["TECH_DOMAIN"].cycle_score, Decimal("0.5550"))
        self.assertEqual(by_code["TECH_DOMAIN"].cycle_state, "forming")
        self.assertIn("propagated_only", by_code["TECH_DOMAIN"].conflict_flags)

        self.assertEqual(by_code["AI_SEMICONDUCTOR_CYCLE"].cycle_level, "theme")
        self.assertEqual(by_code["AI_SEMICONDUCTOR_CYCLE"].cycle_score, Decimal("0.4025"))
        self.assertEqual(by_code["AI_SEMICONDUCTOR_CYCLE"].cycle_state, "forming")
        self.assertIn("hysteresis_hold", by_code["AI_SEMICONDUCTOR_CYCLE"].conflict_flags)

    def test_compute_transitions_excludes_hysteresis_hold(self) -> None:
        inputs = load_cycle_hierarchy_snapshot_inputs(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 23),
            executor=FakeExecutor(),
        )
        snapshots = compute_cycle_hierarchy_snapshots(inputs)
        transitions = compute_cycle_hierarchy_transitions(inputs, snapshots)

        self.assertEqual(len(transitions), 1)
        self.assertEqual(transitions[0].node_id, 201)
        self.assertEqual(transitions[0].from_state, "expanding")
        self.assertEqual(transitions[0].to_state, "forming")

    def test_render_upsert_and_transition_sql(self) -> None:
        inputs = load_cycle_hierarchy_snapshot_inputs(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 23),
            executor=FakeExecutor(),
        )
        snapshots = compute_cycle_hierarchy_snapshots(inputs)
        transitions = compute_cycle_hierarchy_transitions(inputs, snapshots)

        upsert_sql = render_cycle_hierarchy_snapshot_upsert_sql(
            snapshots,
            as_of_date=date(2026, 5, 23),
            source_run_id=77,
        )
        transition_sql = render_cycle_hierarchy_transition_insert_sql(
            transitions,
            as_of_date=date(2026, 5, 23),
            source_run_id=77,
        )

        self.assertIn("insert into signal.cycle_hierarchy_state_snapshot", upsert_sql)
        self.assertIn("on conflict (node_id, as_of_date) do update", upsert_sql)
        self.assertIn("hysteresis_hold", upsert_sql)
        self.assertIn("insert into signal.cycle_hierarchy_transition_log", transition_sql)
        self.assertIn("77::bigint", transition_sql)

    def test_run_dry_run_does_not_write(self) -> None:
        executor = FakeExecutor()

        report = run_cycle_hierarchy_snapshot_v2(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 23),
            execute=False,
            executor=executor,
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["node_count"], 3)
        self.assertEqual(report["transition_count"], 1)
        self.assertEqual(executor.non_query_sql, [])

    def test_run_execute_records_pipeline_run_and_writes_rows(self) -> None:
        executor = FakeExecutor(run_id=9102)

        report = run_cycle_hierarchy_snapshot_v2(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 23),
            execute=True,
            executor=executor,
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9102)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("insert into signal.cycle_hierarchy_state_snapshot", executor.non_query_sql[0])
        self.assertIn("insert into signal.cycle_hierarchy_transition_log", executor.non_query_sql[1])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])

    def test_run_execute_marks_pipeline_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=9103, fail_on_upsert=True)

        with self.assertRaises(RuntimeError):
            run_cycle_hierarchy_snapshot_v2(
                config=type("Config", (), {})(),
                as_of_date=date(2026, 5, 23),
                execute=True,
                executor=executor,
            )

        self.assertIn("status = 'failed'", executor.non_query_sql[-1])


if __name__ == "__main__":
    unittest.main()
