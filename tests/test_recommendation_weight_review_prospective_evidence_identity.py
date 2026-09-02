from __future__ import annotations

import copy
import unittest

from tests.recommendation_weight_review_prospective_evidence_fixtures import (
    _blocker_codes,
    _build,
    _bundle,
)


class ProspectiveEvidenceIdentityTests(unittest.TestCase):
    def test_complete_fresh_foundation_builds_stable_identities_and_deduplicates(self) -> None:
        result = _build(_bundle())

        self.assertEqual(result["status"], "foundation_complete_fresh_read_only")
        self.assertTrue(result["observed_structural_integrity_attested"])
        self.assertFalse(result["eligibility_integrity_attested"])
        self.assertTrue(
            result["attestations"]["stable_row_level_sample_identity_attested"]
        )
        self.assertTrue(
            result["attestations"][
                "versioned_component_snapshot_integrity_attested"
            ]
        )
        self.assertTrue(
            result["attestations"]["outcome_observation_identity_attested"]
        )
        self.assertTrue(result["attestations"]["feedback_deduplication_attested"])
        self.assertTrue(result["attestations"]["freshness_policy_defined"])
        self.assertFalse(result["attestations"]["freshness_policy_approved"])
        self.assertFalse(result["attestations"]["freshness_policy_attested"])
        self.assertFalse(result["attestations"]["approved_horizon_policy_attested"])

        self.assertEqual(result["recommendation_identity"]["recommendation_count"], 2)
        self.assertRegex(
            result["recommendation_identity"]["identity_manifest_sha256"],
            r"^[0-9a-f]{64}$",
        )
        self.assertRegex(
            result["recommendation_identity"][
                "component_snapshot_manifest_sha256"
            ],
            r"^[0-9a-f]{64}$",
        )
        self.assertEqual(
            result["outcome_identity"]["reconstructed_quality_outcome_count"], 2
        )
        self.assertEqual(
            result["outcome_identity"]["reconstructed_horizon_outcome_counts"],
            {"30": 2, "90": 0},
        )

        dedup = result["feedback_deduplication"]
        self.assertEqual(dedup["raw_feedback_item_count"], 4)
        self.assertEqual(dedup["unique_feedback_observation_count"], 3)
        self.assertEqual(dedup["duplicate_feedback_item_count"], 1)
        self.assertEqual(dedup["duplicate_group_count"], 1)
        self.assertEqual(dedup["conflicting_group_count"], 0)
        self.assertTrue(dedup["deduplication_attested"])
        self.assertTrue(dedup["source_run_lineage_complete"])
        self.assertRegex(dedup["source_run_manifest_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            dedup["counting_policy"],
            "one_count_per_feedback_observation_identity",
        )
        self.assertRegex(dedup["deduplicated_manifest_sha256"], r"^[0-9a-f]{64}$")

        freshness = result["freshness"]
        self.assertTrue(freshness["candidate_policy_passed"])
        self.assertFalse(freshness["policy"]["approved"])
        self.assertEqual(
            freshness["policy"]["version"],
            "recommendation-weight-review-conservative-freshness-v1",
        )
        self.assertTrue(
            all(row["status"] == "fresh" for row in freshness["observations"])
        )

    def test_input_order_does_not_change_identity_or_cohort_hashes(self) -> None:
        original = _build(_bundle())
        reordered_bundle = _bundle()
        reordered_bundle["recommendations"].reverse()
        for recommendation in reordered_bundle["recommendations"]:
            recommendation["components"].reverse()
        reordered_bundle["outcomes"].reverse()
        reordered_bundle["feedback_artifacts"].reverse()
        for artifact in reordered_bundle["feedback_artifacts"]:
            artifact["score_json"]["items"].reverse()
        reordered = _build(reordered_bundle)

        self.assertEqual(reordered["status"], "foundation_complete_fresh_read_only")
        self.assertEqual(
            original["recommendation_identity"]["identity_manifest_sha256"],
            reordered["recommendation_identity"]["identity_manifest_sha256"],
        )
        self.assertEqual(
            original["recommendation_identity"][
                "component_snapshot_manifest_sha256"
            ],
            reordered["recommendation_identity"][
                "component_snapshot_manifest_sha256"
            ],
        )
        self.assertEqual(
            original["outcome_identity"]["identity_manifest_sha256"],
            reordered["outcome_identity"]["identity_manifest_sha256"],
        )
        self.assertEqual(
            original["feedback_deduplication"]["deduplicated_manifest_sha256"],
            reordered["feedback_deduplication"]["deduplicated_manifest_sha256"],
        )
        self.assertEqual(
            original["cohort_snapshot"]["sha256"],
            reordered["cohort_snapshot"]["sha256"],
        )

    def test_component_change_changes_component_and_cohort_hashes(self) -> None:
        original = _build(_bundle())
        changed_bundle = _bundle()
        changed_bundle["recommendations"][0]["components"][0][
            "component_score"
        ] = "0.61"
        changed = _build(changed_bundle)

        self.assertEqual(changed["status"], "foundation_complete_fresh_read_only")
        self.assertNotEqual(
            original["recommendation_identity"][
                "component_snapshot_manifest_sha256"
            ],
            changed["recommendation_identity"][
                "component_snapshot_manifest_sha256"
            ],
        )
        self.assertNotEqual(
            original["cohort_snapshot"]["sha256"], changed["cohort_snapshot"]["sha256"]
        )

    def test_recommendation_natural_identity_collision_fails_closed(self) -> None:
        bundle = _bundle()
        duplicate = copy.deepcopy(bundle["recommendations"][0])
        duplicate["recommendation_id"] = 3
        bundle["recommendations"].append(duplicate)
        bundle["referenced_quality"]["score_json"]["recommendation_count"] = 3
        bundle["referenced_outcome"]["score_json"]["sample_audit_after"]["summary"][
            "recommendation_count"
        ] = 3

        result = _build(bundle)

        self.assertEqual(result["status"], "foundation_incoherent_fail_closed")
        self.assertIn("recommendation_natural_identity_collision", _blocker_codes(result))
        self.assertFalse(result["observed_structural_integrity_attested"])

    def test_duplicate_recommendation_id_fails_closed(self) -> None:
        bundle = _bundle()
        duplicate = copy.deepcopy(bundle["recommendations"][0])
        bundle["recommendations"].append(duplicate)
        bundle["referenced_quality"]["score_json"]["recommendation_count"] = 3
        bundle["referenced_outcome"]["score_json"]["sample_audit_after"]["summary"][
            "recommendation_count"
        ] = 3

        result = _build(bundle)

        self.assertEqual(result["status"], "foundation_incoherent_fail_closed")
        self.assertIn("duplicate_recommendation_id", _blocker_codes(result))

    def test_missing_component_rows_fails_incomplete(self) -> None:
        bundle = _bundle()
        bundle["recommendations"][0]["components"] = []

        result = _build(bundle)

        self.assertEqual(result["status"], "foundation_incomplete_fail_closed")
        self.assertIn("recommendation_components_missing", _blocker_codes(result))
        self.assertFalse(
            result["attestations"][
                "versioned_component_snapshot_integrity_attested"
            ]
        )

    def test_duplicate_component_name_fails_incoherent(self) -> None:
        bundle = _bundle()
        duplicate = copy.deepcopy(bundle["recommendations"][0]["components"][0])
        bundle["recommendations"][0]["components"].append(duplicate)

        result = _build(bundle)

        self.assertEqual(result["status"], "foundation_incoherent_fail_closed")
        self.assertIn("duplicate_component_name", _blocker_codes(result))

    def test_source_recommendation_count_mismatch_fails_incoherent(self) -> None:
        for source_name, mutate, expected_code in (
            (
                "quality",
                lambda bundle: bundle["referenced_quality"]["score_json"].update(
                    recommendation_count=3
                ),
                "quality_recommendation_count_mismatch",
            ),
            (
                "outcome",
                lambda bundle: bundle["referenced_outcome"]["score_json"][
                    "sample_audit_after"
                ]["summary"].update(recommendation_count=3),
                "outcome_recommendation_count_mismatch",
            ),
        ):
            with self.subTest(source=source_name):
                bundle = _bundle()
                mutate(bundle)
                result = _build(bundle)
                self.assertEqual(result["status"], "foundation_incoherent_fail_closed")
                self.assertIn(expected_code, _blocker_codes(result))

    def test_quality_and_horizon_outcome_count_mismatch_fail_closed(self) -> None:
        cases = (
            (
                "quality",
                lambda bundle: bundle["referenced_quality"]["score_json"].update(
                    outcome_count=1
                ),
                "quality_outcome_count_mismatch",
            ),
            (
                "horizon",
                lambda bundle: bundle["referenced_outcome"]["score_json"][
                    "sample_audit_after"
                ]["horizon_coverage"][0].update(outcome_count=1),
                "outcome_horizon_counts_mismatch",
            ),
        )
        for name, mutate, expected_code in cases:
            with self.subTest(case=name):
                bundle = _bundle()
                mutate(bundle)
                result = _build(bundle)
                self.assertEqual(result["status"], "foundation_incoherent_fail_closed")
                self.assertIn(expected_code, _blocker_codes(result))

    def test_unknown_outcome_recommendation_fails_incoherent(self) -> None:
        bundle = _bundle()
        bundle["outcomes"][0]["recommendation_id"] = 999

        result = _build(bundle)

        self.assertEqual(result["status"], "foundation_incoherent_fail_closed")
        self.assertIn("outcome_recommendation_reference_unknown", _blocker_codes(result))


if __name__ == "__main__":
    unittest.main()
