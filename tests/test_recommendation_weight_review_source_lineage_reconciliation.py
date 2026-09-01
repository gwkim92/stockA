from __future__ import annotations

import copy
import json
import re
import unittest
from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.recommendation_weight_review_source_lineage_reconciliation import (
    build_recommendation_weight_review_source_lineage_reconciliation,
    render_source_lineage_bundle_lookup_sql,
    render_source_lineage_reconciliation_eval_insert_sql,
    run_recommendation_weight_review_source_lineage_reconciliation,
)


AUDIT_DATE = date(2026, 7, 11)


class FakeExecutor:
    def __init__(self, bundle: dict[str, object] | None = None) -> None:
        self.bundle = copy.deepcopy(bundle or _bundle())
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        lowered = sql.lower()
        if "insert into ops.pipeline_run" in lowered:
            return "9101"
        if "insert into ai.eval_run" in lowered:
            return "8101"
        if "source lineage reconciliation v1 atomic lookup" in lowered:
            return json.dumps(self.bundle)
        raise AssertionError(f"Unexpected scalar SQL: {sql[:160]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class SourceLineageReconciliationTests(unittest.TestCase):
    def test_reconciles_readiness_referenced_chain_even_when_latest_has_drifted(self) -> None:
        result = _build(_bundle(latest_drift=True))

        self.assertEqual(result["status"], "reconciled_read_only")
        self.assertTrue(result["lineage_reconciled"])
        self.assertTrue(result["lineage_ready_for_prospective_identity_work"])
        self.assertEqual(result["canonical_chain"]["quality_reference_eval_run_id"], 301)
        self.assertEqual(result["canonical_chain"]["outcome_reference_eval_run_id"], 201)
        self.assertEqual(
            result["canonical_chain"]["status_snapshot"]["readiness_decision"],
            "ready_for_manual_weight_review",
        )
        self.assertEqual(
            result["source_snapshot"]["referenced_quality"]["legacy_status"],
            "ready_for_weight_review",
        )
        self.assertTrue(result["cohort_filter_identity"]["attested"])
        self.assertTrue(result["nested_quality_identity"]["attested"])
        self.assertTrue(result["nested_quality_identity"]["hashes_match"])
        self.assertTrue(result["latest_drift_observation"]["drift_detected"])
        self.assertEqual(
            result["latest_drift_observation"]["quality"]["status"],
            "different_latest_observation",
        )
        self.assertEqual(
            result["latest_drift_observation"]["outcome"]["status"],
            "different_latest_observation",
        )
        self.assertFalse(result["latest_drift_observation"]["quality"]["may_replace_canonical_reference"])

    def test_latest_drift_does_not_change_canonical_chain_hash(self) -> None:
        stable = _build(_bundle(latest_drift=False))
        drifted = _build(_bundle(latest_drift=True))

        self.assertEqual(stable["canonical_chain"]["sha256"], drifted["canonical_chain"]["sha256"])
        self.assertNotEqual(
            stable["latest_drift_observation"],
            drifted["latest_drift_observation"],
        )

    def test_exact_referenced_source_change_changes_canonical_chain_hash(self) -> None:
        original_bundle = _bundle()
        changed_bundle = copy.deepcopy(original_bundle)
        changed_quality = changed_bundle["referenced_quality"]["score_json"]
        changed_outcome = changed_bundle["referenced_outcome"]["score_json"]
        assert isinstance(changed_quality, dict)
        assert isinstance(changed_outcome, dict)
        changed_quality["positive_outcome_count"] = 16
        changed_outcome["quality_eval_score"] = copy.deepcopy(changed_quality)

        original = _build(original_bundle)
        changed = _build(changed_bundle)

        self.assertEqual(changed["status"], "reconciled_read_only")
        self.assertNotEqual(original["canonical_chain"]["sha256"], changed["canonical_chain"]["sha256"])

    def test_missing_anchor_reference_or_resolved_source_fails_incomplete(self) -> None:
        cases = (
            ("anchor", lambda bundle: bundle.update(readiness={})),
            (
                "quality_reference",
                lambda bundle: bundle["readiness"]["score_json"].pop("source_eval_run_id"),
            ),
            ("quality_source", lambda bundle: bundle.update(referenced_quality={})),
            ("outcome_source", lambda bundle: bundle.update(referenced_outcome={})),
        )
        for name, mutate in cases:
            with self.subTest(case=name):
                bundle = _bundle()
                mutate(bundle)
                result = _build(bundle)

                self.assertEqual(result["status"], "lineage_incomplete_fail_closed")
                self.assertFalse(result["lineage_reconciled"])
                self.assertTrue(any(item["category"] == "incomplete" for item in result["blockers"]))

    def test_wrong_source_identity_fails_incoherent(self) -> None:
        bundle = _bundle()
        bundle["referenced_quality"]["eval_name"] = "unrelated_eval"

        result = _build(bundle)

        self.assertEqual(result["status"], "lineage_incoherent_fail_closed")
        self.assertIn("referenced_quality_eval_name_mismatch", _blocker_codes(result))

    def test_resolved_eval_id_or_status_mismatch_fails_incoherent(self) -> None:
        for name, mutate, expected_code in (
            (
                "quality_id",
                lambda bundle: bundle["referenced_quality"].update(eval_run_id=302),
                "resolved_quality_reference_mismatch",
            ),
            (
                "quality_status",
                lambda bundle: bundle["referenced_quality"]["score_json"].update(
                    quality_status="collect_more_outcomes"
                ),
                "readiness_quality_status_mismatch",
            ),
            (
                "sample_status",
                lambda bundle: bundle["readiness"]["score_json"]["outcome_calibration_gate"].update(
                    sample_status="thin_sample"
                ),
                "readiness_gate_sample_status_mismatch",
            ),
            (
                "readiness_boolean",
                lambda bundle: bundle["readiness"]["score_json"].update(
                    manual_weight_review_allowed=False
                ),
                "readiness_decision_boolean_mismatch",
            ),
        ):
            with self.subTest(case=name):
                bundle = _bundle()
                mutate(bundle)
                result = _build(bundle)

                self.assertEqual(result["status"], "lineage_incoherent_fail_closed")
                self.assertIn(expected_code, _blocker_codes(result))

    def test_cohort_filters_are_versioned_hashed_and_must_match(self) -> None:
        good = _build(_bundle())
        identity = good["cohort_filter_identity"]
        self.assertEqual(
            identity["contract_version"],
            "recommendation-weight-review-cohort-filter-v1",
        )
        self.assertEqual(
            identity["required_filters"],
            {
                "market_code": "US",
                "strategy_name": "long_term",
                "horizon_type": "calendar_days",
                "universe_version": "professional-us-v1",
            },
        )
        self.assertRegex(identity["identity_sha256"], r"^[0-9a-f]{64}$")

        mismatch = _bundle()
        mismatch["referenced_outcome"]["score_json"]["sample_audit_after"]["filters"][
            "market_code"
        ] = "KR"
        bad = _build(mismatch)
        self.assertEqual(bad["status"], "lineage_incoherent_fail_closed")
        self.assertIn("outcome_filter_market_code_mismatch", _blocker_codes(bad))

        missing = _bundle()
        missing["referenced_outcome"]["score_json"]["filters"].pop("universe_version")
        incomplete = _build(missing)
        self.assertEqual(incomplete["status"], "lineage_incomplete_fail_closed")
        self.assertIn("outcome_top_filter_universe_version_missing", _blocker_codes(incomplete))

    def test_nested_quality_identity_must_hash_to_exact_referenced_quality(self) -> None:
        bundle = _bundle()
        nested = bundle["referenced_outcome"]["score_json"]["quality_eval_score"]
        nested["recommendation_count"] = 999

        result = _build(bundle)

        self.assertEqual(result["status"], "lineage_incoherent_fail_closed")
        self.assertFalse(result["nested_quality_identity"]["hashes_match"])
        self.assertIn("outcome_nested_quality_mismatch", _blocker_codes(result))

    def test_future_source_date_fails_incoherent_in_pure_builder(self) -> None:
        bundle = _bundle()
        bundle["referenced_outcome"]["created_at"] = "2026-07-12T00:00:00Z"

        result = _build(bundle)

        self.assertEqual(result["status"], "lineage_incoherent_fail_closed")
        self.assertIn("referenced_outcome_created_after_as_of", _blocker_codes(result))

    def test_adversarial_permission_flags_never_escalate_output(self) -> None:
        bundle = _bundle()
        adversarial = {
            "authoritative": True,
            "manual_review_eligible": True,
            "evidence_sufficient_for_pilot_request": True,
            "pilot_scope_defined": True,
            "explicit_user_approval_present": True,
            "read_only_pilot_start_allowed": True,
            "proposal_generation_allowed": True,
            "weight_mutation_allowed": True,
            "automatic_weight_change_allowed": True,
            "portfolio_position_mutation_allowed": True,
            "recommendation_scoring_mutated": True,
            "automatic_order_allowed": True,
            "broker_submit_allowed": True,
        }
        for key in (
            "readiness",
            "referenced_quality",
            "referenced_outcome",
            "latest_quality",
            "latest_outcome",
        ):
            score = bundle[key]["score_json"]
            score.update(adversarial)
        bundle["referenced_outcome"]["score_json"]["quality_eval_score"] = copy.deepcopy(
            bundle["referenced_quality"]["score_json"]
        )

        result = _build(bundle)

        self.assertFalse(result["authoritative"])
        for key in adversarial:
            with self.subTest(key=key):
                self.assertFalse(result[key])
        self.assertEqual(result["order_boundary"], "read_only_no_order")
        self.assertEqual(result["mutation_boundary"]["status"], "blocked_read_only_shadow")

    def test_atomic_lookup_is_read_only_and_separates_references_from_latest(self) -> None:
        sql = render_source_lineage_bundle_lookup_sql(
            as_of_date=AUDIT_DATE,
            readiness_eval_run_id=401,
        )
        lowered = sql.lower()

        self.assertIn("readiness_candidates", lowered)
        self.assertIn("lineage_refs", lowered)
        self.assertIn("referenced_quality", lowered)
        self.assertIn("referenced_outcome", lowered)
        self.assertIn("latest_quality", lowered)
        self.assertIn("latest_outcome", lowered)
        self.assertIn("eval_run.eval_run_id = 401", lowered)
        self.assertIn("source_eval_run_id", sql)
        self.assertIn("outcome_calibration_gate,eval_run_id", sql)
        self.assertIn("recommendation_weight_review_readiness_audit", sql)
        self.assertIn("recommendation_quality_calibration", sql)
        self.assertIn("recommendation_outcome_calibration_sample_expansion", sql)
        self.assertRegex(sql, r"'2026-07-11'::date")
        self.assertNotRegex(lowered, r"\b(insert\s+into|update\s+|delete\s+from)\b")

    def test_insert_sql_is_append_only_to_new_eval_dataset(self) -> None:
        sql = render_source_lineage_reconciliation_eval_insert_sql(
            score_json={"status": "reconciled_read_only", "weight_mutation_allowed": False}
        )
        lowered = sql.lower()

        self.assertEqual(lowered.count("insert into"), 1)
        self.assertIn("insert into ai.eval_run", lowered)
        self.assertIn("recommendation_weight_review_source_lineage_reconciliation_v1", sql)
        self.assertIn("recommendation-weight-review-source-lineage-reconciliation-v1", sql)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)
        self.assertNotIn("signal.recommendation", lowered)
        self.assertNotIn("portfolio.position", lowered)
        self.assertNotIn("broker.", lowered)

    def test_dry_run_performs_one_atomic_read_and_no_write(self) -> None:
        executor = FakeExecutor()

        report = run_recommendation_weight_review_source_lineage_reconciliation(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=AUDIT_DATE,
            readiness_eval_run_id=401,
            execute=False,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(len(executor.scalar_sql), 1)
        self.assertEqual(executor.non_query_sql, [])
        self.assertFalse(_contains_write(executor.scalar_sql[0]))
        self.assertTrue(report["reconciliation"]["lineage_reconciled"])
        self.assertFalse(report["reconciliation"]["weight_mutation_allowed"])

    def test_execute_writes_only_pipeline_lifecycle_and_one_eval(self) -> None:
        executor = FakeExecutor()

        report = run_recommendation_weight_review_source_lineage_reconciliation(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=AUDIT_DATE,
            execute=True,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9101)
        self.assertEqual(report["eval_run_id"], 8101)
        self.assertEqual(len(executor.scalar_sql), 3)
        self.assertEqual(sum("insert into ops.pipeline_run" in sql.lower() for sql in executor.scalar_sql), 1)
        self.assertEqual(sum("insert into ai.eval_run" in sql.lower() for sql in executor.scalar_sql), 1)
        self.assertEqual(len(executor.non_query_sql), 1)
        all_writes = [
            sql
            for sql in (*executor.scalar_sql, *executor.non_query_sql)
            if _contains_write(sql)
        ]
        self.assertTrue(all("ops.pipeline_run" in sql or "ai.eval_run" in sql for sql in all_writes))
        self.assertFalse(report["reconciliation"]["automatic_order_allowed"])
        self.assertFalse(report["reconciliation"]["broker_submit_allowed"])


def _build(bundle: dict[str, object]) -> dict[str, object]:
    return build_recommendation_weight_review_source_lineage_reconciliation(
        as_of_date=AUDIT_DATE,
        bundle=bundle,
    )


def _bundle(*, latest_drift: bool = False) -> dict[str, object]:
    quality_score = _quality_score()
    outcome_score = _outcome_score(quality_score)
    quality = _wrapper(
        301,
        "recommendation_quality_calibration",
        "recommendation-quality-live-v1",
        quality_score,
    )
    outcome = _wrapper(
        201,
        "recommendation_outcome_calibration_sample_expansion",
        "recommendation-outcome-calibration-sample-expansion-v1",
        outcome_score,
    )
    if latest_drift:
        latest_quality_score = copy.deepcopy(quality_score)
        latest_quality_score["recommendation_count"] = 52
        latest_outcome_score = copy.deepcopy(outcome_score)
        latest_outcome_score["quality_eval_score"] = copy.deepcopy(latest_quality_score)
        latest_quality = _wrapper(
            801,
            "recommendation_quality_calibration",
            "recommendation-quality-live-v1",
            latest_quality_score,
            created_at="2026-07-10T12:00:00Z",
        )
        latest_outcome = _wrapper(
            692,
            "recommendation_outcome_calibration_sample_expansion",
            "recommendation-outcome-calibration-sample-expansion-v1",
            latest_outcome_score,
            created_at="2026-07-10T12:00:00Z",
        )
    else:
        latest_quality = copy.deepcopy(quality)
        latest_outcome = copy.deepcopy(outcome)
    return {
        "readiness": _wrapper(
            401,
            "recommendation_weight_review_readiness_audit",
            "recommendation-weight-review-readiness-v1",
            {
                "decision": "ready_for_manual_weight_review",
                "manual_weight_review_allowed": True,
                "source_eval_run_id": 301,
                "source_quality_status": "ready_for_weight_review",
                "outcome_calibration_gate": {
                    "eval_run_id": 201,
                    "status": "ready_for_manual_weight_review",
                    "quality_status": "ready_for_weight_review",
                    "sample_status": "sufficient_sample",
                },
                "automatic_weight_change_allowed": False,
                "automatic_order_allowed": False,
                "broker_submit_allowed": False,
            },
        ),
        "referenced_quality": quality,
        "referenced_outcome": outcome,
        "latest_quality": latest_quality,
        "latest_outcome": latest_outcome,
    }


def _quality_score() -> dict[str, object]:
    return {
        "eval_name": "recommendation_quality_calibration",
        "dataset_version": "recommendation-quality-live-v1",
        "as_of_date": "2026-07-04",
        "quality_status": "ready_for_weight_review",
        "sample_status": "sufficient_sample",
        "recommendation_count": 45,
        "outcome_count": 45,
        "positive_outcome_count": 15,
        "component_metrics": [
            {
                "component_name": "momentum_score",
                "outcome_count": 45,
                "positive_score_spread": "0.19",
                "avg_component_weight": "0.25",
            }
        ],
    }


def _outcome_score(quality_score: dict[str, object]) -> dict[str, object]:
    required_filters = {
        "market_code": "US",
        "strategy_name": "long_term",
        "horizon_type": "calendar_days",
        "universe_version": "professional-us-v1",
    }
    return {
        "eval_name": "recommendation_outcome_calibration_sample_expansion",
        "dataset_version": "recommendation-outcome-calibration-sample-expansion-v1",
        "as_of_date": "2026-07-04",
        "status": "ready_for_manual_weight_review",
        "quality_status": "ready_for_weight_review",
        "sample_status": "sufficient_sample",
        "filters": {
            **required_filters,
            "outcome_version": "price-based-v1",
            "limit": None,
        },
        "sample_audit_after": {
            "as_of_date": "2026-07-04",
            "horizon_days": [30, 90, 180, 365],
            "filters": copy.deepcopy(required_filters),
        },
        "quality_eval_score": copy.deepcopy(quality_score),
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
    }


def _wrapper(
    eval_run_id: int,
    eval_name: str,
    dataset_version: str,
    score_json: dict[str, object],
    *,
    created_at: str = "2026-07-04T12:00:00Z",
) -> dict[str, object]:
    return {
        "eval_run_id": eval_run_id,
        "eval_name": eval_name,
        "dataset_version": dataset_version,
        "provider": "postgres",
        "model_name": "deterministic-test-v1",
        "score_json": copy.deepcopy(score_json),
        "created_at": created_at,
    }


def _blocker_codes(result: dict[str, object]) -> set[str]:
    blockers = result["blockers"]
    assert isinstance(blockers, list)
    return {
        str(item.get("code"))
        for item in blockers
        if isinstance(item, dict)
    }


def _contains_write(sql: str) -> bool:
    return bool(re.search(r"\b(insert\s+into|update\s+|delete\s+from)\b", sql, flags=re.IGNORECASE))


if __name__ == "__main__":
    unittest.main()
