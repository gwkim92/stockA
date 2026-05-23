from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
import unittest

from stockanalysis.signal.hierarchical_impact_propagation import (
    HierarchicalImpactPropagationCandidate,
    compute_hierarchical_propagated_impacts,
    load_hierarchical_impact_propagation_candidates,
    render_hierarchical_impact_propagation_candidate_lookup_sql,
    render_hierarchical_propagated_impact_upsert_sql,
    run_hierarchical_impact_propagation,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
MIGRATION_PATH = ROOT_DIR / "db" / "migrations" / "0017_hierarchical_impact_propagation.sql"


class FakeExecutor:
    def __init__(self, *, run_id: int = 8101, fail_on_upsert: bool = False) -> None:
        self.run_id = run_id
        self.fail_on_upsert = fail_on_upsert
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- hierarchical impact propagation candidate lookup"):
            return json.dumps(
                [
                    {
                        "event_id": 11,
                        "event_title": "Fed signals higher for longer",
                        "event_at": "2026-05-20T12:00:00Z",
                        "source_node_id": 101,
                        "source_node_code": "MACRO_RATES_FED",
                        "source_node_name": "Fed and rates",
                        "propagated_node_id": 201,
                        "propagated_node_code": "TECH_DOMAIN",
                        "propagated_node_name": "Technology Domain",
                        "node_path_codes": ["MACRO_RATES_FED", "TECH_DOMAIN"],
                        "path_depth": 1,
                        "path_weight": "0.750000",
                        "decay": "0.8500",
                        "source_impact_direction": "risk_review",
                        "source_impact_strength": "0.8000",
                        "source_confidence": "0.9000",
                        "source_rationale": "Policy rate shock.",
                        "instrument_id": 601,
                        "primary_symbol": "NVDA",
                        "exposure_weight": "0.8500",
                        "sensitivity_direction": "positive",
                        "exposure_confidence": "0.8200",
                        "exposure_rationale": "Core technology exposure.",
                    },
                    {
                        "event_id": 11,
                        "event_title": "Fed signals higher for longer",
                        "event_at": "2026-05-20T12:00:00Z",
                        "source_node_id": 101,
                        "source_node_code": "MACRO_RATES_FED",
                        "source_node_name": "Fed and rates",
                        "propagated_node_id": 101,
                        "propagated_node_code": "MACRO_RATES_FED",
                        "propagated_node_name": "Fed and rates",
                        "node_path_codes": ["MACRO_RATES_FED"],
                        "path_depth": 0,
                        "path_weight": "1.000000",
                        "decay": "1.0000",
                        "source_impact_direction": "risk_review",
                        "source_impact_strength": "0.8000",
                        "source_confidence": "0.9000",
                        "source_rationale": "Policy rate shock.",
                        "instrument_id": 701,
                        "primary_symbol": "TLT",
                        "exposure_weight": "0.9000",
                        "sensitivity_direction": "negative",
                        "exposure_confidence": "0.8500",
                        "exposure_rationale": "Long-duration bond exposure.",
                    },
                ]
            )
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)
        if self.fail_on_upsert and "insert into signal.hierarchical_propagated_instrument_impact" in sql:
            raise RuntimeError("boom")


class HierarchicalImpactPropagationTests(unittest.TestCase):
    def test_migration_creates_v2_path_table(self) -> None:
        sql = MIGRATION_PATH.read_text(encoding="utf-8").lower()

        self.assertIn("create table if not exists signal.hierarchical_propagated_instrument_impact", sql)
        self.assertIn("source_node_id", sql)
        self.assertIn("propagated_node_id", sql)
        self.assertIn("node_path_codes jsonb not null", sql)
        self.assertIn("path_hash text not null", sql)
        self.assertIn("path_depth integer not null", sql)

    def test_candidate_lookup_uses_recursive_edges_and_exposures(self) -> None:
        sql = render_hierarchical_impact_propagation_candidate_lookup_sql(
            as_of_date=date(2026, 5, 20),
            limit=25,
            max_depth=3,
            decay_per_hop=Decimal("0.8500"),
        )

        self.assertIn("with recursive recent_source_events", sql)
        self.assertIn("graph_paths as", sql)
        self.assertIn("ref.classification_edge", sql)
        self.assertIn("ref.instrument_factor_exposure", sql)
        self.assertIn("path.path_depth < 3", sql)
        self.assertIn("not child.node_id = any(path.node_path_ids)", sql)
        self.assertIn("array_to_string(path.node_path_codes, '>')", sql)
        self.assertIn("limit 25", sql)

    def test_load_candidates(self) -> None:
        rows = load_hierarchical_impact_propagation_candidates(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 20),
            executor=FakeExecutor(),
        )

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].source_node_code, "MACRO_RATES_FED")
        self.assertEqual(rows[0].propagated_node_code, "TECH_DOMAIN")
        self.assertEqual(rows[0].node_path_codes, ("MACRO_RATES_FED", "TECH_DOMAIN"))
        self.assertEqual(rows[0].path_depth, 1)

    def test_compute_hierarchical_impacts_uses_path_weight_decay_and_sensitivity(self) -> None:
        rows = compute_hierarchical_propagated_impacts(
            load_hierarchical_impact_propagation_candidates(
                config=type("Config", (), {})(),
                as_of_date=date(2026, 5, 20),
                executor=FakeExecutor(),
            )
        )

        self.assertEqual(len(rows), 2)
        tech_row = rows[0]
        self.assertEqual(tech_row.primary_symbol, "NVDA")
        self.assertEqual(tech_row.impact_direction, "risk_review")
        self.assertEqual(tech_row.impact_strength, Decimal("0.4335"))
        self.assertEqual(tech_row.confidence, Decimal("0.5228"))
        self.assertEqual(tech_row.path_depth, 1)
        self.assertEqual(tech_row.path_weight, Decimal("0.750000"))
        self.assertEqual(tech_row.decay, Decimal("0.8500"))
        self.assertEqual(len(tech_row.path_hash), 64)

        tlt_row = rows[1]
        self.assertEqual(tlt_row.primary_symbol, "TLT")
        self.assertEqual(tlt_row.impact_direction, "supportive")
        self.assertEqual(tlt_row.impact_strength, Decimal("0.7200"))

    def test_upsert_sql_is_idempotent_by_path_hash(self) -> None:
        rows = compute_hierarchical_propagated_impacts(
            load_hierarchical_impact_propagation_candidates(
                config=type("Config", (), {})(),
                as_of_date=date(2026, 5, 20),
                executor=FakeExecutor(),
            )
        )
        sql = render_hierarchical_propagated_impact_upsert_sql(rows, source_run_id=77)

        self.assertIn("insert into signal.hierarchical_propagated_instrument_impact", sql)
        self.assertIn("path_hash", sql)
        self.assertIn("on conflict (", sql.lower())
        self.assertIn("77::bigint", sql)

    def test_run_dry_run_does_not_write(self) -> None:
        executor = FakeExecutor()

        report = run_hierarchical_impact_propagation(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 20),
            execute=False,
            executor=executor,
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["candidate_count"], 2)
        self.assertEqual(report["propagated_impact_count"], 2)
        self.assertEqual(report["max_depth"], 3)
        self.assertEqual(executor.non_query_sql, [])

    def test_run_execute_records_pipeline_run_and_upserts(self) -> None:
        executor = FakeExecutor(run_id=8102)

        report = run_hierarchical_impact_propagation(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 20),
            execute=True,
            executor=executor,
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 8102)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("insert into signal.hierarchical_propagated_instrument_impact", executor.non_query_sql[0])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[1])

    def test_run_execute_marks_pipeline_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=8103, fail_on_upsert=True)

        with self.assertRaises(RuntimeError):
            run_hierarchical_impact_propagation(
                config=type("Config", (), {})(),
                as_of_date=date(2026, 5, 20),
                execute=True,
                executor=executor,
            )

        self.assertIn("status = 'failed'", executor.non_query_sql[-1])


if __name__ == "__main__":
    unittest.main()
