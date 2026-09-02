from __future__ import annotations

import unittest

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.recommendation_weight_review_prospective_evidence_lookup import (
    render_prospective_evidence_bundle_lookup_sql,
    render_prospective_evidence_foundation_eval_insert_sql,
)
from stockanalysis.operations.recommendation_weight_review_prospective_evidence_foundation import (
    run_recommendation_weight_review_prospective_evidence_foundation,
)
from tests.recommendation_weight_review_prospective_evidence_fixtures import (
    AUDIT_DATE,
    FakeExecutor,
    _contains_write,
)


class ProspectiveEvidenceRuntimeTests(unittest.TestCase):
    def test_atomic_lookup_is_read_only_and_exact_reference_scoped(self) -> None:
        sql = render_prospective_evidence_bundle_lookup_sql(
            as_of_date=AUDIT_DATE,
            lineage_eval_run_id=501,
            portfolio_feedback_calibration_eval_run_id=601,
            portfolio_name="Long Term Paper",
        )
        lowered = sql.lower()

        self.assertIn("prospective evidence foundation v1 atomic lookup", lowered)
        self.assertIn("eval_run.eval_run_id = 501", lowered)
        self.assertIn("eval_run.eval_run_id = 601", lowered)
        self.assertIn("recommendation_weight_review_source_lineage_reconciliation_v1", sql)
        self.assertIn("canonical_chain,quality,eval_run_id", sql)
        self.assertIn("canonical_chain,outcome,eval_run_id", sql)
        self.assertIn("signal.recommendation_score_component", lowered)
        self.assertIn("performance.recommendation_outcome", lowered)
        self.assertIn("latest_feedback_runs", lowered)
        self.assertIn("portfolio_review_decision_outcome_feedback", lowered)
        self.assertNotRegex(
            lowered,
            r"\b(insert\s+into|update\s+|delete\s+from|truncate\s+)\b",
        )

    def test_insert_sql_is_append_only_to_new_eval_dataset(self) -> None:
        sql = render_prospective_evidence_foundation_eval_insert_sql(
            score_json={"status": "foundation_complete_fresh_read_only"}
        )
        lowered = sql.lower()

        self.assertEqual(lowered.count("insert into"), 1)
        self.assertIn("insert into ai.eval_run", lowered)
        self.assertIn("recommendation_weight_review_prospective_evidence_foundation_v1", sql)
        self.assertIn("recommendation-weight-review-prospective-evidence-foundation-v1", sql)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)
        self.assertNotIn("signal.recommendation", lowered)
        self.assertNotIn("portfolio.position", lowered)
        self.assertNotIn("broker.", lowered)

    def test_dry_run_performs_one_atomic_read_and_no_write(self) -> None:
        executor = FakeExecutor()

        report = run_recommendation_weight_review_prospective_evidence_foundation(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=AUDIT_DATE,
            lineage_eval_run_id=501,
            portfolio_feedback_calibration_eval_run_id=601,
            execute=False,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(len(executor.scalar_sql), 1)
        self.assertEqual(executor.non_query_sql, [])
        self.assertFalse(_contains_write(executor.scalar_sql[0]))
        self.assertTrue(report["foundation"]["observed_structural_integrity_attested"])
        self.assertFalse(report["foundation"]["weight_mutation_allowed"])

    def test_execute_writes_only_pipeline_lifecycle_and_one_eval(self) -> None:
        executor = FakeExecutor()

        report = run_recommendation_weight_review_prospective_evidence_foundation(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=AUDIT_DATE,
            execute=True,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9901)
        self.assertEqual(report["eval_run_id"], 8901)
        self.assertEqual(len(executor.scalar_sql), 3)
        self.assertEqual(
            sum(
                "insert into ops.pipeline_run" in sql.lower()
                for sql in executor.scalar_sql
            ),
            1,
        )
        self.assertEqual(
            sum("insert into ai.eval_run" in sql.lower() for sql in executor.scalar_sql),
            1,
        )
        self.assertEqual(len(executor.non_query_sql), 1)
        all_writes = [
            sql
            for sql in (*executor.scalar_sql, *executor.non_query_sql)
            if _contains_write(sql)
        ]
        self.assertTrue(
            all("ops.pipeline_run" in sql or "ai.eval_run" in sql for sql in all_writes)
        )
        self.assertFalse(report["foundation"]["automatic_order_allowed"])
        self.assertFalse(report["foundation"]["broker_submit_allowed"])


if __name__ == "__main__":
    unittest.main()
