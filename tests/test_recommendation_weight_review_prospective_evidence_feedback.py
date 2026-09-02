from __future__ import annotations

import copy
import unittest

from tests.recommendation_weight_review_prospective_evidence_fixtures import (
    _blocker_codes,
    _build,
    _bundle,
)


class ProspectiveEvidenceFeedbackTests(unittest.TestCase):
    def test_missing_or_unexpected_feedback_reference_fails_closed(self) -> None:
        missing = _bundle()
        missing["feedback_artifacts"] = missing["feedback_artifacts"][:1]
        missing_result = _build(missing)
        self.assertEqual(missing_result["status"], "foundation_incomplete_fail_closed")
        self.assertIn("referenced_feedback_artifacts_missing", _blocker_codes(missing_result))

        extra = _bundle()
        extra_artifact = copy.deepcopy(extra["feedback_artifacts"][0])
        extra_artifact["eval_run_id"] = 7003
        extra["feedback_artifacts"].append(extra_artifact)
        extra_result = _build(extra)
        self.assertEqual(extra_result["status"], "foundation_incoherent_fail_closed")
        self.assertIn("unexpected_feedback_artifacts_present", _blocker_codes(extra_result))

    def test_feedback_calibration_truncated_source_lineage_fails_incomplete(self) -> None:
        bundle = _bundle()
        bundle["feedback_calibration"]["score_json"]["feedback_run_count"] = 3

        result = _build(bundle)

        self.assertEqual(result["status"], "foundation_incomplete_fail_closed")
        self.assertIn(
            "feedback_calibration_source_lineage_incomplete",
            _blocker_codes(result),
        )
        self.assertFalse(
            result["feedback_deduplication"]["source_run_lineage_complete"]
        )
        self.assertFalse(
            result["feedback_deduplication"]["deduplication_attested"]
        )

    def test_same_decision_with_changed_evidence_is_not_deduplicated(self) -> None:
        bundle = _bundle()
        second_run = bundle["feedback_artifacts"][0]
        second_run["score_json"]["items"][0]["evidence"]["recommendation_outcome"][
            "outcome_id"
        ] = 102

        result = _build(bundle)

        self.assertEqual(result["status"], "foundation_complete_fresh_read_only")
        self.assertEqual(
            result["feedback_deduplication"]["unique_feedback_observation_count"], 4
        )
        self.assertEqual(
            result["feedback_deduplication"]["duplicate_feedback_item_count"], 0
        )

    def test_same_feedback_identity_with_conflicting_payload_fails_closed(self) -> None:
        bundle = _bundle()
        bundle["feedback_artifacts"][0]["score_json"]["items"][0][
            "feedback_status"
        ] = "contradicted"

        result = _build(bundle)

        self.assertEqual(result["status"], "foundation_incoherent_fail_closed")
        self.assertIn("feedback_identity_conflicting_payloads", _blocker_codes(result))
        self.assertFalse(result["feedback_deduplication"]["deduplication_attested"])

    def test_stale_sources_are_explicit_but_do_not_authorize_anything(self) -> None:
        bundle = _bundle()
        bundle["lineage"]["created_at"] = "2026-05-01T00:00:00Z"
        bundle["referenced_quality"]["score_json"]["as_of_date"] = "2026-05-01"
        bundle["referenced_outcome"]["score_json"]["as_of_date"] = "2026-05-01"
        bundle["feedback_calibration"]["score_json"]["as_of_date"] = "2026-05-01"
        for artifact in bundle["feedback_artifacts"]:
            artifact["score_json"]["as_of_date"] = "2026-05-01"
        for recommendation in bundle["recommendations"]:
            recommendation["batch_as_of_date"] = "2026-04-01"
        for outcome in bundle["outcomes"]:
            outcome["measurement_start_date"] = "2026-04-01"
            outcome["measurement_end_date"] = "2026-05-01"
        bundle["referenced_outcome"]["score_json"]["sample_audit_after"][
            "horizon_coverage"
        ] = [
            {"horizon_day": 30, "outcome_count": 2},
            {"horizon_day": 90, "outcome_count": 0},
        ]

        result = _build(bundle)

        self.assertEqual(result["status"], "foundation_complete_stale_read_only")
        self.assertTrue(result["observed_structural_integrity_attested"])
        self.assertFalse(result["freshness"]["candidate_policy_passed"])
        self.assertGreater(result["freshness"]["stale_source_count"], 0)
        self.assertFalse(result["manual_review_eligible"])
        self.assertFalse(result["weight_mutation_allowed"])

    def test_future_source_date_fails_incoherent(self) -> None:
        bundle = _bundle()
        bundle["referenced_quality"]["created_at"] = "2026-07-16T00:00:00Z"

        result = _build(bundle)

        self.assertEqual(result["status"], "foundation_incoherent_fail_closed")
        self.assertIn("referenced_quality_created_after_as_of", _blocker_codes(result))
        statuses = {
            row["source_role"]: row["status"]
            for row in result["freshness"]["observations"]
        }
        self.assertEqual(statuses["referenced_quality"], "fresh")

    def test_exact_duplicate_in_newer_feedback_run_does_not_change_deduplicated_manifest(self) -> None:
        original = _build(_bundle())
        expanded = _bundle()
        newer = copy.deepcopy(expanded["feedback_artifacts"][0])
        newer["eval_run_id"] = 7003
        newer["created_at"] = "2026-07-15T14:00:00Z"
        expanded["feedback_artifacts"].insert(0, newer)
        calibration = expanded["feedback_calibration"]["score_json"]
        calibration["latest_feedback_runs"].insert(0, {"eval_run_id": 7003})
        calibration["feedback_run_count"] = 3
        calibration["decision_count"] = 6

        rebuilt = _build(expanded)

        self.assertEqual(rebuilt["status"], "foundation_complete_fresh_read_only")
        self.assertEqual(
            original["feedback_deduplication"]["deduplicated_manifest_sha256"],
            rebuilt["feedback_deduplication"]["deduplicated_manifest_sha256"],
        )
        self.assertGreater(
            rebuilt["feedback_deduplication"]["duplicate_feedback_item_count"],
            original["feedback_deduplication"]["duplicate_feedback_item_count"],
        )

    def test_tampered_lineage_canonical_chain_hash_fails_closed(self) -> None:
        bundle = _bundle()
        bundle["lineage"]["score_json"]["canonical_chain"]["quality"][
            "eval_run_id"
        ] = 999

        result = _build(bundle)

        self.assertEqual(result["status"], "foundation_incoherent_fail_closed")
        self.assertIn("lineage_canonical_chain_hash_mismatch", _blocker_codes(result))
        self.assertIn("lineage_quality_reference_mismatch", _blocker_codes(result))

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
            "automatic_rebalance_allowed": True,
            "recommendation_scoring_mutated": True,
            "automatic_order_allowed": True,
            "broker_submit_allowed": True,
        }
        for key in (
            "lineage",
            "referenced_quality",
            "referenced_outcome",
            "feedback_calibration",
        ):
            bundle[key]["score_json"].update(adversarial)
        for artifact in bundle["feedback_artifacts"]:
            artifact["score_json"].update(adversarial)

        result = _build(bundle)

        self.assertFalse(result["authoritative"])
        for key in adversarial:
            with self.subTest(key=key):
                self.assertFalse(result[key])
        self.assertEqual(result["order_boundary"], "read_only_no_order")
        self.assertEqual(result["mutation_boundary"]["status"], "blocked_read_only_shadow")


if __name__ == "__main__":
    unittest.main()
