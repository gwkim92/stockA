from __future__ import annotations

import json
import unittest
from datetime import date
from decimal import Decimal

from stockanalysis.signal.cycle import (
    CycleNodeInput,
    compute_cycle_state_snapshots,
    load_cycle_snapshot_inputs,
    render_cycle_snapshot_input_lookup_sql,
    render_cycle_state_snapshot_replace_sql,
    run_cycle_state_snapshot,
)


class FakeExecutor:
    def __init__(self, *, run_id: int = 991, fail_on_upsert: bool = False) -> None:
        self.run_id = run_id
        self.fail_on_upsert = fail_on_upsert
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- cycle snapshot input lookup"):
            return json.dumps(
                [
                    {
                        "universe_batch_id": 1001,
                        "node_id": 11,
                        "node_code": "ANNUAL_REPORTING",
                        "node_name": "Annual Reporting",
                        "member_count": 1,
                        "positive_return_1d_count": 0,
                        "average_return_1d": "-0.01327962",
                        "average_return_since_first": "-0.01327962",
                        "average_return_since_first_zscore": "-1.00000000",
                        "recent_event_count_30d": 1,
                        "recent_event_count_90d": 1,
                        "average_event_confidence": "0.95000000",
                        "latest_event_date": "2024-11-01",
                        "member_symbols": ["AAPL"],
                    }
                ]
            )
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)
        if self.fail_on_upsert and "insert into signal.cycle_state_snapshot" in sql:
            raise RuntimeError("boom")


class EmptyExecutor:
    def execute_scalar(self, sql: str) -> str:
        return "[]"


class CycleStateSnapshotTests(unittest.TestCase):
    def test_render_cycle_snapshot_input_lookup_sql(self) -> None:
        sql = render_cycle_snapshot_input_lookup_sql(
            as_of_date=date(2024, 11, 1),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
        )
        self.assertIn("signal.strategy_universe_batch", sql)
        self.assertIn("ref.instrument_classification_membership", sql)
        self.assertIn("signal.instrument_feature_value", sql)
        self.assertIn("event.event_classification_impact", sql)
        self.assertIn("signal.propagated_instrument_impact", sql)
        self.assertIn("propagated_event_impacts", sql)
        self.assertIn("return_since_first_observation", sql)

    def test_load_cycle_snapshot_inputs(self) -> None:
        rows = load_cycle_snapshot_inputs(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=FakeExecutor(),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].node_code, "ANNUAL_REPORTING")
        self.assertEqual(rows[0].member_symbols, ("AAPL",))
        self.assertEqual(rows[0].average_event_confidence, Decimal("0.95000000"))

    def test_load_cycle_snapshot_inputs_fails_when_empty(self) -> None:
        with self.assertRaises(ValueError):
            load_cycle_snapshot_inputs(
                config=type("Config", (), {})(),
                as_of_date=date(2024, 11, 1),
                strategy_name="long_term_core",
                horizon_type="long_term",
                universe_version="fixture-v1",
                executor=EmptyExecutor(),
            )

    def test_compute_cycle_state_snapshots(self) -> None:
        rows = (
            CycleNodeInput(
                universe_batch_id=1001,
                node_id=11,
                node_code="ANNUAL_REPORTING",
                node_name="Annual Reporting",
                member_count=1,
                positive_return_1d_count=0,
                average_return_1d=Decimal("-0.01327962"),
                average_return_since_first=Decimal("-0.01327962"),
                average_return_since_first_zscore=Decimal("-1.00000000"),
                recent_event_count_30d=1,
                recent_event_count_90d=1,
                average_event_confidence=Decimal("0.95000000"),
                latest_event_date=date(2024, 11, 1),
                member_symbols=("AAPL",),
            ),
            CycleNodeInput(
                universe_batch_id=1001,
                node_id=21,
                node_code="AI_INFRA",
                node_name="AI Infrastructure",
                member_count=3,
                positive_return_1d_count=3,
                average_return_1d=Decimal("0.03100000"),
                average_return_since_first=Decimal("0.18000000"),
                average_return_since_first_zscore=Decimal("1.50000000"),
                recent_event_count_30d=3,
                recent_event_count_90d=4,
                average_event_confidence=Decimal("0.90000000"),
                latest_event_date=date(2024, 11, 1),
                member_symbols=("NVDA", "SMCI", "VRT"),
            ),
        )
        snapshots = compute_cycle_state_snapshots(
            rows,
            as_of_date=date(2024, 11, 1),
            score_version="bootstrap-v1",
        )
        by_code = {row.node_code: row for row in snapshots}
        self.assertEqual(by_code["ANNUAL_REPORTING"].cycle_state, "forming")
        self.assertEqual(by_code["ANNUAL_REPORTING"].trend_score, Decimal("0.25000000"))
        self.assertEqual(by_code["ANNUAL_REPORTING"].event_heat_score, Decimal("0.47500000"))
        self.assertEqual(by_code["ANNUAL_REPORTING"].cycle_score, Decimal("0.20750000"))
        self.assertEqual(by_code["AI_INFRA"].cycle_state, "expanding")
        self.assertEqual(by_code["AI_INFRA"].breadth_score, Decimal("1.00000000"))
        self.assertEqual(by_code["AI_INFRA"].cycle_score, Decimal("0.83375000"))

    def test_render_cycle_state_snapshot_replace_sql(self) -> None:
        snapshots = compute_cycle_state_snapshots(
            (
                CycleNodeInput(
                    universe_batch_id=1001,
                    node_id=11,
                    node_code="ANNUAL_REPORTING",
                    node_name="Annual Reporting",
                    member_count=1,
                    positive_return_1d_count=0,
                    average_return_1d=Decimal("-0.01327962"),
                    average_return_since_first=Decimal("-0.01327962"),
                    average_return_since_first_zscore=Decimal("-1.00000000"),
                    recent_event_count_30d=1,
                    recent_event_count_90d=1,
                    average_event_confidence=Decimal("0.95000000"),
                    latest_event_date=date(2024, 11, 1),
                    member_symbols=("AAPL",),
                ),
            ),
            as_of_date=date(2024, 11, 1),
            score_version="bootstrap-v1",
        )
        sql = render_cycle_state_snapshot_replace_sql(
            snapshots,
            as_of_date=date(2024, 11, 1),
            source_run_id=77,
        )
        self.assertIn("delete from signal.cycle_state_snapshot", sql)
        self.assertIn("insert into signal.cycle_state_snapshot", sql)
        self.assertIn("77::bigint", sql)
        self.assertIn("'forming'", sql)

    def test_run_cycle_state_snapshot_records_pipeline_run_and_summary(self) -> None:
        executor = FakeExecutor(run_id=992)
        summary = run_cycle_state_snapshot(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 992)
        self.assertEqual(summary["universe_batch_id"], 1001)
        self.assertEqual(summary["node_count"], 1)
        self.assertEqual(summary["cycle_state_counts"], {"forming": 1})
        self.assertEqual(summary["node_code_preview"], ["ANNUAL_REPORTING"])
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[1])

    def test_run_cycle_state_snapshot_marks_pipeline_run_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=993, fail_on_upsert=True)
        with self.assertRaises(RuntimeError):
            run_cycle_state_snapshot(
                config=type("Config", (), {})(),
                as_of_date=date(2024, 11, 1),
                strategy_name="long_term_core",
                horizon_type="long_term",
                universe_version="fixture-v1",
                executor=executor,
            )
        self.assertIn("status = 'failed'", executor.non_query_sql[-1])
