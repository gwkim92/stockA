from __future__ import annotations

import copy
import json
import re
import unittest
from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.recommendation_weight_review_readiness_semantics import (
    build_recommendation_weight_review_readiness_semantics_v2,
    render_outcome_calibration_eval_lookup_sql,
    render_portfolio_feedback_eval_lookup_sql,
    render_quality_eval_lookup_sql,
    render_readiness_audit_eval_lookup_sql,
    render_readiness_semantics_eval_insert_sql,
    run_recommendation_weight_review_readiness_semantics_v2,
)


AUDIT_DATE = date(2026, 7, 11)
AUDIT_DATE_TEXT = AUDIT_DATE.isoformat()


class FakeReadinessSemanticsExecutor:
    def __init__(
        self,
        *,
        sources: dict[str, dict[str, object]] | None = None,
        run_id: int = 9801,
        eval_run_id: int = 8801,
    ) -> None:
        self.sources = copy.deepcopy(sources or _coherent_sources(portfolio_status="manual_review_ready"))
        self.run_id = run_id
        self.eval_run_id = eval_run_id
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        lowered = sql.lower()
        if "insert into ops.pipeline_run" in lowered:
            return str(self.run_id)
        if "insert into ai.eval_run" in lowered:
            return str(self.eval_run_id)
        if "recommendation_weight_review_readiness_audit" in sql:
            return json.dumps(self.sources["readiness"])
        if "recommendation_quality_calibration" in sql:
            return json.dumps(self.sources["quality"])
        if "recommendation_outcome_calibration_sample_expansion" in sql:
            return json.dumps(self.sources["outcome"])
        if "portfolio_review_feedback_calibration" in sql:
            return json.dumps(self.sources["portfolio_feedback"])
        raise AssertionError(f"Unexpected scalar SQL: {sql[:200]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class RecommendationWeightReviewReadinessSemanticsTests(unittest.TestCase):
    def test_legacy_thresholds_can_be_ready_but_integrity_keeps_review_ineligible(self) -> None:
        semantics = _build(_coherent_sources(portfolio_status="manual_review_ready"))

        self.assertEqual(semantics["mode"], "shadow_read_only")
        self.assertFalse(semantics["authoritative"])
        self.assertTrue(semantics["legacy_comparison"]["manual_weight_review_allowed"])
        self.assertTrue(semantics["evidence_readiness"]["threshold_evidence_ready"])
        self.assertTrue(semantics["evidence_readiness"]["portfolio_feedback_ready"])
        self.assertFalse(semantics["evidence_readiness"]["legacy_integrity_attested"])
        self.assertFalse(semantics["manual_review_eligible"])
        self.assertFalse(semantics["manual_review_eligibility"]["eligible"])
        self.assertEqual(semantics["manual_review_eligibility"]["scope"], "read_only_human_evidence_review")
        self.assertEqual(semantics["decision"], "legacy_thresholds_met_integrity_not_attested")
        self.assertFalse(semantics["sample_identity"]["freshness_policy_attested"])
        self.assertEqual(
            semantics["sample_identity"]["temporal_freshness_status"],
            "policy_not_defined",
        )

        # Evidence thresholds and human review eligibility are deliberately not pilot authority.
        self.assertFalse(semantics["evidence_sufficient_for_pilot_request"])
        self.assertFalse(semantics["pilot_scope_defined"])
        self.assertFalse(semantics["explicit_user_approval_present"])
        self.assertFalse(semantics["read_only_pilot_start_allowed"])
        self.assertFalse(semantics["proposal_generation_allowed"])
        self.assertFalse(semantics["weight_mutation_allowed"])
        self.assertFalse(semantics["automatic_weight_change_allowed"])
        self.assertFalse(semantics["portfolio_position_mutation_allowed"])
        self.assertFalse(semantics["automatic_order_allowed"])
        self.assertFalse(semantics["broker_submit_allowed"])
        self.assertEqual(semantics["order_boundary"], "read_only_no_order")
        self.assertEqual(semantics["explicit_user_authorization"]["status"], "explicit_approval_required")
        self.assertTrue(semantics["explicit_user_authorization"]["required"])
        self.assertFalse(semantics["explicit_user_authorization"]["present"])
        self.assertFalse(semantics["explicit_user_authorization"]["scope_defined"])
        self.assertEqual(semantics["pilot"]["status"], "not_started_not_authorized")
        self.assertFalse(semantics["pilot"]["started"])
        self.assertEqual(semantics["mutation_boundary"]["status"], "blocked_read_only_shadow")

    def test_adversarial_true_flags_in_every_source_never_escalate_permissions(self) -> None:
        sources = _coherent_sources(portfolio_status="manual_review_ready")
        adversarial_flags = {
            "authoritative": True,
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
        for source in sources.values():
            score = source["score_json"]
            assert isinstance(score, dict)
            score.update(adversarial_flags)
            score["guardrails"] = dict(adversarial_flags)
            score["mutation_boundary"] = dict(adversarial_flags)
        outcome_score = sources["outcome"]["score_json"]
        quality_score = sources["quality"]["score_json"]
        assert isinstance(outcome_score, dict)
        assert isinstance(quality_score, dict)
        outcome_score["quality_eval_score"] = copy.deepcopy(quality_score)

        semantics = _build(sources)

        self.assertTrue(semantics["evidence_readiness"]["source_coherent"])
        self.assertTrue(semantics["evidence_readiness"]["threshold_evidence_ready"])
        self.assertFalse(semantics["manual_review_eligible"])
        self.assertFalse(semantics["authoritative"])
        for key in (
            "pilot_scope_defined",
            "explicit_user_approval_present",
            "read_only_pilot_start_allowed",
            "proposal_generation_allowed",
            "weight_mutation_allowed",
            "automatic_weight_change_allowed",
            "portfolio_position_mutation_allowed",
            "automatic_order_allowed",
            "broker_submit_allowed",
        ):
            with self.subTest(key=key):
                self.assertFalse(semantics[key])

        mutation_boundary = semantics["mutation_boundary"]
        for key in (
            "recommendation_scoring_mutated",
            "weight_mutation_allowed",
            "automatic_weight_change_allowed",
            "portfolio_position_mutation_allowed",
            "automatic_order_allowed",
            "broker_submit_allowed",
        ):
            with self.subTest(nested_key=key):
                self.assertFalse(mutation_boundary[key])

    def test_source_snapshot_preserves_lineage_filters_horizons_counts_and_hashes(self) -> None:
        sources = _coherent_sources(portfolio_status="manual_review_ready")
        semantics = _build(sources)

        self.assertEqual(semantics["eval_name"], "recommendation_weight_review_readiness_semantics_v2")
        self.assertEqual(semantics["dataset_version"], "recommendation-weight-review-readiness-semantics-v2")
        self.assertEqual(semantics["as_of_date"], AUDIT_DATE_TEXT)

        expected_ids = {
            "readiness": 401,
            "quality": 301,
            "outcome": 201,
            "portfolio_feedback": 101,
        }
        for source_name, expected_id in expected_ids.items():
            with self.subTest(source=source_name):
                snapshot = semantics["source_snapshot"][source_name]
                source = sources[source_name]
                self.assertEqual(snapshot["eval_run_id"], expected_id)
                self.assertEqual(snapshot["eval_name"], source["eval_name"])
                self.assertEqual(snapshot["dataset_version"], source["dataset_version"])
                self.assertEqual(snapshot["score_as_of_date"], "2026-07-04")
                self.assertEqual(snapshot["created_at"], source["created_at"])
                self.assertRegex(snapshot["score_sha256"], r"^[0-9a-f]{64}$")

        self.assertEqual(
            semantics["source_snapshot"]["readiness"]["legacy_status"],
            "ready_for_manual_weight_review",
        )
        self.assertEqual(
            semantics["source_snapshot"]["quality"]["legacy_status"],
            "ready_for_weight_review",
        )
        self.assertEqual(
            semantics["source_snapshot"]["outcome"]["legacy_status"],
            "ready_for_manual_weight_review",
        )
        self.assertEqual(
            semantics["source_snapshot"]["portfolio_feedback"]["legacy_status"],
            "manual_review_ready",
        )
        self.assertEqual(
            semantics["source_snapshot"]["outcome"]["source_filters"],
            {
                "market_code": "US",
                "strategy_name": "long_term",
                "horizon_type": "calendar_days",
                "universe_version": "professional-us-v1",
                "outcome_version": "price-based-v1",
                "limit": None,
            },
        )

        sample_identity = semantics["sample_identity"]
        self.assertEqual(sample_identity["status"], "legacy_aggregate_only_not_attested")
        self.assertFalse(sample_identity["identity_attested"])
        self.assertEqual(
            sample_identity["quality_observation_unit"],
            "distinct_recommendation_latest_outcome_within_max_horizon",
        )
        self.assertEqual(sample_identity["quality_recommendation_count"], 45)
        self.assertEqual(sample_identity["quality_outcome_count"], 45)
        self.assertEqual(sample_identity["horizon_observation_unit"], "recommendation_x_horizon")
        self.assertEqual(sample_identity["recommendation_horizon_observation_count"], 180)
        self.assertEqual(sample_identity["horizon_outcome_observation_count"], 95)
        self.assertEqual(
            sample_identity["portfolio_feedback_observation_unit"],
            "legacy_feedback_item_aggregate",
        )
        self.assertEqual(sample_identity["portfolio_feedback_run_count"], 3)
        self.assertEqual(sample_identity["portfolio_feedback_decision_count"], 12)
        self.assertEqual(sample_identity["portfolio_feedback_mature_decision_count"], 12)
        self.assertFalse(sample_identity["stable_row_level_sample_identity_attested"])
        self.assertFalse(sample_identity["feedback_deduplication_attested"])
        self.assertFalse(sample_identity["versioned_component_snapshot_integrity_attested"])
        self.assertGreaterEqual(len(sample_identity["limitations"]), 3)
        for hash_key in (
            "quality_component_metrics_sha256",
            "outcome_horizon_coverage_sha256",
            "portfolio_feedback_evidence_sha256",
        ):
            with self.subTest(hash_key=hash_key):
                self.assertRegex(sample_identity[hash_key], r"^[0-9a-f]{64}$")

        horizon = semantics["horizon_evidence"]
        self.assertEqual(horizon["horizon_days"], [30, 90, 180, 365])
        self.assertEqual(horizon["observation_unit"], "recommendation_x_horizon")
        self.assertEqual(
            horizon["filters"],
            {
                "market_code": "US",
                "strategy_name": "long_term",
                "horizon_type": "calendar_days",
                "universe_version": "professional-us-v1",
            },
        )
        self.assertEqual([row["horizon_day"] for row in horizon["rows"]], [30, 90, 180, 365])
        self.assertEqual(
            [row["recommendation_horizon_count"] for row in horizon["rows"]],
            [45, 45, 45, 45],
        )
        self.assertEqual([row["outcome_count"] for row in horizon["rows"]], [45, 30, 15, 5])
        self.assertEqual(horizon["aggregate_summary"]["recommendation_count"], 45)
        self.assertEqual(horizon["aggregate_summary"]["recommendation_horizon_count"], 180)
        self.assertEqual(horizon["aggregate_summary"]["outcome_count"], 95)
        self.assertTrue(horizon["aggregate_consistent"])
        self.assertFalse(horizon["approved_horizon_policy_attested"])

        # The source hash is canonical and changes only when the source score changes.
        rebuilt = _build(copy.deepcopy(sources))
        self.assertEqual(semantics["source_snapshot"], rebuilt["source_snapshot"])
        changed = copy.deepcopy(sources)
        changed_quality = changed["quality"]["score_json"]
        assert isinstance(changed_quality, dict)
        changed_quality["recommendation_count"] = 46
        changed_semantics = _build(changed)
        self.assertNotEqual(
            semantics["source_snapshot"]["quality"]["score_sha256"],
            changed_semantics["source_snapshot"]["quality"]["score_sha256"],
        )

    def test_future_source_score_or_created_timestamp_fails_closed(self) -> None:
        for source_name, field, future_value in (
            ("quality", "score_json.as_of_date", "2026-07-12"),
            ("outcome", "created_at", "2026-07-12T00:00:00Z"),
        ):
            with self.subTest(source=source_name, field=field):
                sources = _coherent_sources(portfolio_status="manual_review_ready")
                if field == "created_at":
                    sources[source_name][field] = future_value
                else:
                    score = sources[source_name]["score_json"]
                    assert isinstance(score, dict)
                    score["as_of_date"] = future_value

                semantics = _build(sources)

                self._assert_fail_closed(semantics)
                self.assertIn("future_source_evidence", _blocker_codes(semantics))

    def test_source_reference_mismatch_fails_closed(self) -> None:
        mismatch_mutations = (
            ("quality", lambda sources: sources["readiness"]["score_json"].update(source_eval_run_id=999)),
            (
                "outcome",
                lambda sources: sources["readiness"]["score_json"]["outcome_calibration_gate"].update(
                    eval_run_id=999
                ),
            ),
        )
        for expected_source, mutate in mismatch_mutations:
            with self.subTest(source=expected_source):
                sources = _coherent_sources(portfolio_status="manual_review_ready")
                mutate(sources)
                semantics = _build(sources)

                self._assert_fail_closed(semantics)
                expected_code = (
                    "readiness_quality_eval_reference_mismatch"
                    if expected_source == "quality"
                    else "readiness_outcome_eval_reference_mismatch"
                )
                self.assertIn(expected_code, _blocker_codes(semantics))

    def test_nested_quality_content_mismatch_fails_closed(self) -> None:
        sources = _coherent_sources(portfolio_status="manual_review_ready")
        outcome_score = sources["outcome"]["score_json"]
        assert isinstance(outcome_score, dict)
        nested_quality = outcome_score["quality_eval_score"]
        assert isinstance(nested_quality, dict)
        nested_quality["quality_status"] = "collect_more_outcomes"

        semantics = _build(sources)

        self._assert_fail_closed(semantics)
        self.assertIn("outcome_nested_quality_mismatch", _blocker_codes(semantics))

    def test_horizon_set_or_aggregate_mismatch_fails_closed(self) -> None:
        for mismatch_name, mutate in (
            (
                "set",
                lambda score: score.update(horizon_days=[30, 90, 180]),
            ),
            (
                "aggregate",
                lambda score: score["sample_audit_after"]["summary"].update(
                    recommendation_horizon_count=179
                ),
            ),
        ):
            with self.subTest(mismatch=mismatch_name):
                sources = _coherent_sources(portfolio_status="manual_review_ready")
                score = sources["outcome"]["score_json"]
                assert isinstance(score, dict)
                mutate(score)

                semantics = _build(sources)

                self._assert_fail_closed(semantics)
                expected_code = (
                    "outcome_nested_horizon_set_mismatch"
                    if mismatch_name == "set"
                    else "outcome_recommendation_horizon_count_aggregate_mismatch"
                )
                self.assertIn(expected_code, _blocker_codes(semantics))
                if mismatch_name == "aggregate":
                    self.assertFalse(semantics["horizon_evidence"]["aggregate_consistent"])

    def test_required_quality_and_feedback_counts_fail_closed_when_missing(self) -> None:
        quality_fields = {
            "recommendation_count": "quality_recommendation_count_invalid",
            "outcome_count": "quality_outcome_count_invalid",
            "positive_outcome_count": "quality_positive_outcome_count_invalid",
        }
        for field, expected_code in quality_fields.items():
            with self.subTest(source="quality", field=field):
                sources = _coherent_sources(portfolio_status="manual_review_ready")
                quality = sources["quality"]["score_json"]
                assert isinstance(quality, dict)
                quality.pop(field)
                _sync_nested_quality(sources)

                semantics = _build(sources)

                self._assert_fail_closed(semantics)
                self.assertIn(expected_code, _blocker_codes(semantics))

        feedback_fields = {
            "feedback_run_count": "portfolio_feedback_run_count_invalid",
            "decision_count": "portfolio_feedback_decision_count_invalid",
            "mature_decision_count": "portfolio_feedback_mature_decision_count_invalid",
        }
        for field, expected_code in feedback_fields.items():
            with self.subTest(source="portfolio_feedback", field=field):
                sources = _coherent_sources(portfolio_status="manual_review_ready")
                feedback = sources["portfolio_feedback"]["score_json"]
                assert isinstance(feedback, dict)
                feedback.pop(field)

                semantics = _build(sources)

                self._assert_fail_closed(semantics)
                self.assertIn(expected_code, _blocker_codes(semantics))

    def test_impossible_quality_and_feedback_count_relationships_fail_closed(self) -> None:
        cases = (
            (
                "quality_outcomes",
                lambda sources: sources["quality"]["score_json"].update(outcome_count=46),
                "quality_outcome_count_exceeds_recommendation_count",
                True,
            ),
            (
                "quality_positive",
                lambda sources: sources["quality"]["score_json"].update(positive_outcome_count=46),
                "quality_positive_count_exceeds_outcome_count",
                True,
            ),
            (
                "feedback_mature",
                lambda sources: sources["portfolio_feedback"]["score_json"].update(
                    mature_decision_count=13
                ),
                "portfolio_feedback_mature_count_exceeds_decision_count",
                False,
            ),
            (
                "feedback_zero_ready",
                lambda sources: sources["portfolio_feedback"]["score_json"].update(
                    feedback_run_count=0
                ),
                "portfolio_feedback_ready_counts_empty",
                False,
            ),
        )
        for name, mutate, expected_code, sync_quality in cases:
            with self.subTest(case=name):
                sources = _coherent_sources(portfolio_status="manual_review_ready")
                mutate(sources)
                if sync_quality:
                    _sync_nested_quality(sources)

                semantics = _build(sources)

                self._assert_fail_closed(semantics)
                self.assertIn(expected_code, _blocker_codes(semantics))

    def test_horizon_row_partition_shape_and_price_fields_fail_closed(self) -> None:
        cases = (
            (
                "partition",
                lambda score: (
                    score["sample_audit_after"]["horizon_coverage"][0].update(outcome_count=44),
                    score["sample_audit_after"]["horizon_coverage"][1].update(outcome_count=31),
                ),
                "outcome_horizon_row_partition_mismatch",
            ),
            (
                "shape",
                lambda score: score["sample_audit_after"]["summary"].update(
                    recommendation_count=44
                ),
                "outcome_recommendation_horizon_shape_mismatch",
            ),
            (
                "missing_summary_price",
                lambda score: score["sample_audit_after"]["summary"].pop(
                    "missing_entry_price_count"
                ),
                "outcome_missing_entry_price_count_missing_or_invalid",
            ),
            (
                "missing_row_price",
                lambda score: score["sample_audit_after"]["horizon_coverage"][0].pop(
                    "price_gap_count"
                ),
                "outcome_horizon_row_price_gap_count_missing_or_invalid",
            ),
        )
        for name, mutate, expected_code in cases:
            with self.subTest(case=name):
                sources = _coherent_sources(portfolio_status="manual_review_ready")
                outcome = sources["outcome"]["score_json"]
                assert isinstance(outcome, dict)
                mutate(outcome)

                semantics = _build(sources)

                self._assert_fail_closed(semantics)
                self.assertIn(expected_code, _blocker_codes(semantics))

    def test_top_and_nested_cohort_filters_must_match(self) -> None:
        for name, mutate, expected_code in (
            (
                "mismatch",
                lambda score: score["filters"].update(market_code="KR"),
                "outcome_filter_market_code_mismatch",
            ),
            (
                "missing",
                lambda score: score["sample_audit_after"]["filters"].pop("universe_version"),
                "outcome_filter_universe_version_missing",
            ),
        ):
            with self.subTest(case=name):
                sources = _coherent_sources(portfolio_status="manual_review_ready")
                outcome = sources["outcome"]["score_json"]
                assert isinstance(outcome, dict)
                mutate(outcome)

                semantics = _build(sources)

                self._assert_fail_closed(semantics)
                self.assertIn(expected_code, _blocker_codes(semantics))

    def test_portfolio_feedback_must_match_required_paper_portfolio(self) -> None:
        sources = _coherent_sources(portfolio_status="manual_review_ready")
        feedback = sources["portfolio_feedback"]["score_json"]
        assert isinstance(feedback, dict)
        feedback["portfolio_name"] = "Unrelated Portfolio"

        semantics = _build(sources)

        self._assert_fail_closed(semantics)
        self.assertIn("portfolio_feedback_scope_mismatch", _blocker_codes(semantics))

    def test_old_coherent_sources_remain_threshold_ready_but_freshness_is_unattested(self) -> None:
        sources = _coherent_sources(portfolio_status="manual_review_ready")
        for source in sources.values():
            source["created_at"] = "2020-01-02T12:00:00Z"
            score = source["score_json"]
            assert isinstance(score, dict)
            score["as_of_date"] = "2020-01-01"
        outcome = sources["outcome"]["score_json"]
        assert isinstance(outcome, dict)
        for audit_key in ("sample_audit_before", "sample_audit_after"):
            audit = outcome[audit_key]
            assert isinstance(audit, dict)
            audit["as_of_date"] = "2020-01-01"
        _sync_nested_quality(sources)

        semantics = _build(sources)

        self.assertTrue(semantics["evidence_readiness"]["source_coherent"])
        self.assertTrue(semantics["evidence_readiness"]["threshold_evidence_ready"])
        self.assertTrue(semantics["evidence_readiness"]["portfolio_feedback_ready"])
        self.assertFalse(semantics["sample_identity"]["freshness_policy_attested"])
        self.assertEqual(
            semantics["sample_identity"]["temporal_freshness_status"],
            "policy_not_defined",
        )
        self.assertGreater(semantics["sample_identity"]["source_age_days"]["quality"], 2000)
        self.assertFalse(semantics["manual_review_eligible"])
        self.assertEqual(semantics["decision"], "legacy_thresholds_met_integrity_not_attested")

    def test_portfolio_feedback_ready_still_requires_integrity_attestation(self) -> None:
        blocked = _build(_coherent_sources(portfolio_status="collect_more_feedback"))
        eligible = _build(_coherent_sources(portfolio_status="manual_review_ready"))

        self.assertFalse(blocked["evidence_readiness"]["portfolio_feedback_ready"])
        self.assertFalse(blocked["manual_review_eligible"])
        self.assertFalse(blocked["manual_review_eligibility"]["eligible"])
        self.assertEqual(blocked["decision"], "wait_for_portfolio_feedback")
        self.assertIn("Portfolio feedback", blocked["manual_review_eligibility"]["reason"])

        self.assertTrue(eligible["evidence_readiness"]["portfolio_feedback_ready"])
        self.assertTrue(eligible["evidence_readiness"]["threshold_evidence_ready"])
        self.assertFalse(eligible["evidence_readiness"]["legacy_integrity_attested"])
        self.assertFalse(eligible["manual_review_eligible"])
        self.assertFalse(eligible["manual_review_eligibility"]["eligible"])
        self.assertEqual(eligible["decision"], "legacy_thresholds_met_integrity_not_attested")
        self.assertIn("not attested", eligible["manual_review_eligibility"]["reason"])
        self.assertFalse(eligible["evidence_sufficient_for_pilot_request"])
        self.assertFalse(eligible["read_only_pilot_start_allowed"])
        self.assertFalse(eligible["proposal_generation_allowed"])

    def test_missing_any_source_fails_closed_without_raising(self) -> None:
        for missing_source in ("readiness", "quality", "outcome", "portfolio_feedback"):
            with self.subTest(source=missing_source):
                sources = _coherent_sources(portfolio_status="manual_review_ready")
                sources[missing_source] = {}

                semantics = _build(sources)

                self._assert_fail_closed(semantics)
                self.assertIn(f"{missing_source}_source_missing", _blocker_codes(semantics))

    def test_lookup_sql_is_as_of_constrained_and_read_only_even_with_explicit_ids(self) -> None:
        cases = (
            (
                render_readiness_audit_eval_lookup_sql,
                401,
                "recommendation_weight_review_readiness_audit",
                "recommendation-weight-review-readiness-v1",
            ),
            (
                render_quality_eval_lookup_sql,
                301,
                "recommendation_quality_calibration",
                "recommendation-quality-live-v1",
            ),
            (
                render_outcome_calibration_eval_lookup_sql,
                201,
                "recommendation_outcome_calibration_sample_expansion",
                "recommendation-outcome-calibration-sample-expansion-v1",
            ),
            (
                render_portfolio_feedback_eval_lookup_sql,
                101,
                "portfolio_review_feedback_calibration",
                "portfolio-review-feedback-calibration-v1",
            ),
        )
        for renderer, eval_run_id, eval_name, dataset_version in cases:
            with self.subTest(eval_name=eval_name):
                sql = renderer(as_of_date=AUDIT_DATE, eval_run_id=eval_run_id)
                lowered = sql.lower()
                self.assertIn(f"eval_run.eval_run_id = {eval_run_id}", sql)
                self.assertRegex(sql, rf"(?:date\s+)?'{AUDIT_DATE_TEXT}'(?:::date)?")
                self.assertIn(eval_name, sql)
                self.assertIn(dataset_version, sql)
                self.assertIn("score_json", lowered)
                self.assertIn("created_at", lowered)
                self.assertNotIn("insert into", lowered)
                self.assertNotIn("update ", lowered)
                self.assertNotIn("delete from", lowered)
                if eval_name == "portfolio_review_feedback_calibration":
                    self.assertIn("score_json->>'portfolio_name' = 'Long Term Paper'", sql)

    def test_insert_sql_is_append_only_to_the_new_eval_dataset(self) -> None:
        sql = render_readiness_semantics_eval_insert_sql(
            score_json={
                "mode": "shadow_read_only",
                "authoritative": False,
                "weight_mutation_allowed": False,
            }
        )
        lowered = sql.lower()

        self.assertEqual(lowered.count("insert into"), 1)
        self.assertIn("insert into ai.eval_run", lowered)
        self.assertIn("recommendation_weight_review_readiness_semantics_v2", sql)
        self.assertIn("recommendation-weight-review-readiness-semantics-v2", sql)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)
        for prohibited_table in (
            "signal.recommendation_score_component",
            "signal.recommendation",
            "portfolio.position_snapshot",
            "broker.",
        ):
            with self.subTest(table=prohibited_table):
                self.assertNotIn(prohibited_table, lowered)

    def test_dry_run_performs_four_source_reads_and_no_writes(self) -> None:
        executor = FakeReadinessSemanticsExecutor()

        report = run_recommendation_weight_review_readiness_semantics_v2(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=AUDIT_DATE,
            readiness_eval_run_id=401,
            quality_eval_run_id=301,
            outcome_eval_run_id=201,
            portfolio_feedback_eval_run_id=101,
            execute=False,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "planned")
        self.assertFalse(report["execute"])
        self.assertEqual(len(executor.scalar_sql), 4)
        self.assertEqual(executor.non_query_sql, [])
        self.assertTrue(all(not _contains_write(sql) for sql in executor.scalar_sql))
        self.assertFalse(report["semantics"]["read_only_pilot_start_allowed"])
        self.assertFalse(report["semantics"]["weight_mutation_allowed"])

    def test_execute_writes_only_one_pipeline_run_and_one_eval_artifact(self) -> None:
        executor = FakeReadinessSemanticsExecutor(run_id=9802, eval_run_id=8802)

        report = run_recommendation_weight_review_readiness_semantics_v2(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=AUDIT_DATE,
            execute=True,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9802)
        self.assertEqual(report["eval_run_id"], 8802)
        self.assertEqual(len(executor.scalar_sql), 6)
        self.assertEqual(sum("insert into ops.pipeline_run" in sql.lower() for sql in executor.scalar_sql), 1)
        self.assertEqual(sum("insert into ai.eval_run" in sql.lower() for sql in executor.scalar_sql), 1)
        self.assertEqual(len(executor.non_query_sql), 1)
        self.assertIn("update ops.pipeline_run", executor.non_query_sql[0].lower())

        all_write_sql = [
            sql
            for sql in (*executor.scalar_sql, *executor.non_query_sql)
            if _contains_write(sql)
        ]
        self.assertTrue(all("ops.pipeline_run" in sql or "ai.eval_run" in sql for sql in all_write_sql))
        self.assertFalse(report["semantics"]["proposal_generation_allowed"])
        self.assertFalse(report["semantics"]["automatic_weight_change_allowed"])
        self.assertFalse(report["semantics"]["automatic_order_allowed"])
        self.assertFalse(report["semantics"]["broker_submit_allowed"])

    def _assert_fail_closed(self, semantics: dict[str, object]) -> None:
        self.assertEqual(semantics["evidence_readiness"]["status"], "incoherent_fail_closed")
        self.assertFalse(semantics["evidence_readiness"]["source_coherent"])
        self.assertFalse(semantics["manual_review_eligible"])
        self.assertFalse(semantics["manual_review_eligibility"]["eligible"])
        self.assertFalse(semantics["evidence_sufficient_for_pilot_request"])
        self.assertFalse(semantics["read_only_pilot_start_allowed"])
        self.assertFalse(semantics["proposal_generation_allowed"])
        self.assertFalse(semantics["weight_mutation_allowed"])


def _build(sources: dict[str, dict[str, object]]) -> dict[str, object]:
    return build_recommendation_weight_review_readiness_semantics_v2(
        as_of_date=AUDIT_DATE,
        readiness_eval=sources["readiness"],
        quality_eval=sources["quality"],
        outcome_eval=sources["outcome"],
        portfolio_feedback_eval=sources["portfolio_feedback"],
    )


def _coherent_sources(*, portfolio_status: str) -> dict[str, dict[str, object]]:
    quality_score = _quality_score()
    outcome_score = _outcome_score(quality_score=quality_score)
    return {
        "readiness": _eval_wrapper(
            eval_run_id=401,
            eval_name="recommendation_weight_review_readiness_audit",
            dataset_version="recommendation-weight-review-readiness-v1",
            model_name="deterministic-guardrail-v1",
            score_json={
                "as_of_date": "2026-07-04",
                "decision": "ready_for_manual_weight_review",
                "manual_weight_review_allowed": True,
                "source_eval_run_id": 301,
                "source_quality_status": "ready_for_weight_review",
                "outcome_calibration_gate": {
                    "eval_run_id": 201,
                    "status": "ready_for_manual_weight_review",
                    "quality_status": "ready_for_weight_review",
                    "sample_status": "sufficient_sample",
                    "outcome_count": 95,
                },
                "automatic_weight_change_allowed": False,
                "automatic_order_allowed": False,
                "broker_submit_allowed": False,
                "recommendation_scoring_mutated": False,
            },
        ),
        "quality": _eval_wrapper(
            eval_run_id=301,
            eval_name="recommendation_quality_calibration",
            dataset_version="recommendation-quality-live-v1",
            model_name="deterministic-quality-v1",
            score_json=quality_score,
        ),
        "outcome": _eval_wrapper(
            eval_run_id=201,
            eval_name="recommendation_outcome_calibration_sample_expansion",
            dataset_version="recommendation-outcome-calibration-sample-expansion-v1",
            model_name="deterministic-outcome-calibration-v1",
            score_json=outcome_score,
        ),
        "portfolio_feedback": _eval_wrapper(
            eval_run_id=101,
            eval_name="portfolio_review_feedback_calibration",
            dataset_version="portfolio-review-feedback-calibration-v1",
            model_name="portfolio-review-feedback-calibration-v1",
            score_json={
                "as_of_date": "2026-07-04",
                "portfolio_name": "Long Term Paper",
                "calibration_status": portfolio_status,
                "feedback_run_count": 3,
                "decision_count": 12,
                "mature_decision_count": 12,
                "validated_count": 12 if portfolio_status == "manual_review_ready" else 8,
                "contradicted_count": 0,
                "too_early_count": 0 if portfolio_status == "manual_review_ready" else 4,
                "needs_more_data_count": 0,
                "guardrails": {
                    "recommendation_scoring_mutated": False,
                    "portfolio_position_mutated": False,
                    "automatic_order_allowed": False,
                    "broker_submit_allowed": False,
                    "order_boundary": "read_only_no_order",
                },
            },
        ),
    }


def _eval_wrapper(
    *,
    eval_run_id: int,
    eval_name: str,
    dataset_version: str,
    model_name: str,
    score_json: dict[str, object],
) -> dict[str, object]:
    return {
        "eval_run_id": eval_run_id,
        "eval_name": eval_name,
        "dataset_version": dataset_version,
        "provider": "postgres",
        "model_name": model_name,
        "created_at": "2026-07-04T12:00:00Z",
        "score_json": copy.deepcopy(score_json),
    }


def _quality_score() -> dict[str, object]:
    return {
        "eval_name": "recommendation_quality_calibration",
        "dataset_version": "recommendation-quality-live-v1",
        "as_of_date": "2026-07-04",
        "horizon_days": 365,
        "quality_status": "ready_for_weight_review",
        "sample_status": "sufficient_sample",
        "recommendation_count": 45,
        "outcome_count": 45,
        "outcome_coverage_rate": 1.0,
        "positive_outcome_count": 15,
        "positive_outcome_rate": 0.333333,
        "professional_analysis_coverage": {
            "status": "sufficient_coverage",
            "recommendation_count": 45,
            "complete_professional_coverage_count": 44,
            "complete_professional_coverage_rate": 0.977778,
        },
        "cycle_weight_guardrail": {
            "cycle_weight_unchanged": True,
            "recommendation_scoring_mutated": False,
        },
        "fundamental_weight_guardrail": {
            "fundamental_weight_unchanged": True,
            "recommendation_scoring_mutated": False,
        },
        "component_metrics": [
            {
                "component_name": "momentum_score",
                "outcome_count": 45,
                "positive_score_spread": "0.19",
                "avg_component_weight": "0.25",
            }
        ],
    }


def _sync_nested_quality(sources: dict[str, dict[str, object]]) -> None:
    quality = sources["quality"]["score_json"]
    outcome = sources["outcome"]["score_json"]
    assert isinstance(quality, dict)
    assert isinstance(outcome, dict)
    outcome["quality_eval_score"] = copy.deepcopy(quality)


def _outcome_score(*, quality_score: dict[str, object]) -> dict[str, object]:
    horizon_rows = [
        {
            "horizon_day": 30,
            "recommendation_horizon_count": 45,
            "outcome_count": 45,
            "ready_for_backfill_count": 0,
            "not_due_count": 0,
            "price_gap_count": 0,
        },
        {
            "horizon_day": 90,
            "recommendation_horizon_count": 45,
            "outcome_count": 30,
            "ready_for_backfill_count": 0,
            "not_due_count": 15,
            "price_gap_count": 0,
        },
        {
            "horizon_day": 180,
            "recommendation_horizon_count": 45,
            "outcome_count": 15,
            "ready_for_backfill_count": 0,
            "not_due_count": 30,
            "price_gap_count": 0,
        },
        {
            "horizon_day": 365,
            "recommendation_horizon_count": 45,
            "outcome_count": 5,
            "ready_for_backfill_count": 0,
            "not_due_count": 40,
            "price_gap_count": 0,
        },
    ]
    filters = {
        "market_code": "US",
        "strategy_name": "long_term",
        "horizon_type": "calendar_days",
        "universe_version": "professional-us-v1",
    }
    sample_audit = {
        "as_of_date": "2026-07-04",
        "horizon_days": [30, 90, 180, 365],
        "filters": filters,
        "summary": {
            "recommendation_horizon_count": 180,
            "recommendation_count": 45,
            "outcome_count": 95,
            "ready_for_backfill_count": 0,
            "not_due_count": 85,
            "missing_entry_price_count": 0,
            "missing_exit_price_count": 0,
            "benchmark_warning_count": 0,
            "outcome_coverage_rate": 0.527778,
        },
        "horizon_coverage": horizon_rows,
        "missing_reason_counts": {"not_due": 85, "outcome_recorded": 95},
        "component_calibration_diagnostics": [],
    }
    return {
        "eval_name": "recommendation_outcome_calibration_sample_expansion",
        "dataset_version": "recommendation-outcome-calibration-sample-expansion-v1",
        "as_of_date": "2026-07-04",
        "horizon_days": [30, 90, 180, 365],
        "filters": {**filters, "outcome_version": "price-based-v1", "limit": None},
        "status": "ready_for_manual_weight_review",
        "quality_status": "ready_for_weight_review",
        "sample_status": "sufficient_sample",
        "sample_audit_before": copy.deepcopy(sample_audit),
        "sample_audit_after": sample_audit,
        "quality_eval_score": copy.deepcopy(quality_score),
        "outcome_delta": {
            "outcome_count_before": 95,
            "outcome_count_after": 95,
            "outcome_count_added_or_found": 0,
            "ready_for_backfill_count_after": 0,
        },
        "recommendation_scoring_mutated": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": "read_only_no_order",
    }


def _blocker_codes(semantics: dict[str, object]) -> set[str]:
    readiness = semantics["evidence_readiness"]
    assert isinstance(readiness, dict)
    blockers = readiness["blockers"]
    assert isinstance(blockers, list)
    return {
        str(blocker.get("code"))
        for blocker in blockers
        if isinstance(blocker, dict)
    }


def _contains_write(sql: str) -> bool:
    return bool(re.search(r"\b(insert\s+into|update|delete\s+from)\b", sql, flags=re.IGNORECASE))


if __name__ == "__main__":
    unittest.main()
