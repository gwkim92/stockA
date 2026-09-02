from __future__ import annotations

from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.recommendation_weight_review_prospective_evidence_contract import (
    COHORT_SNAPSHOT_CONTRACT_VERSION,
    DEFAULT_DATASET_VERSION,
    DEFAULT_EVAL_NAME,
    DEFAULT_PIPELINE_NAME,
    DEFAULT_PORTFOLIO_NAME,
    ORDER_BOUNDARY,
    SOURCE_FEEDBACK_CALIBRATION_DATASET_VERSION,
    SOURCE_FEEDBACK_CALIBRATION_EVAL_NAME,
    SOURCE_LINEAGE_DATASET_VERSION,
    SOURCE_LINEAGE_EVAL_NAME,
    SOURCE_OUTCOME_DATASET_VERSION,
    SOURCE_OUTCOME_EVAL_NAME,
    SOURCE_QUALITY_DATASET_VERSION,
    SOURCE_QUALITY_EVAL_NAME,
    _as_dict,
    _as_list,
    _build_freshness_evaluation,
    _canonical_copy,
    _canonical_hash,
    _normalize_required_source,
    _parse_date,
    _positive_int,
    _validate_cohort_filters,
    _validate_feedback_calibration_scope,
    _validate_lineage_anchor,
)
from stockanalysis.operations.recommendation_weight_review_prospective_evidence_feedback import (
    _build_feedback_deduplication,
    _normalize_feedback_artifacts,
)
from stockanalysis.operations.recommendation_weight_review_prospective_evidence_lookup import (
    load_prospective_evidence_bundle,
    render_prospective_evidence_foundation_eval_insert_sql,
)
from stockanalysis.operations.recommendation_weight_review_prospective_evidence_outcome import (
    _build_outcome_manifest,
    _validate_source_counts,
)
from stockanalysis.operations.recommendation_weight_review_prospective_evidence_recommendation import (
    _build_recommendation_manifest,
)
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


def build_recommendation_weight_review_prospective_evidence_foundation(
    *,
    as_of_date: date,
    bundle: dict[str, object],
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
) -> dict[str, object]:
    clean_portfolio_name = portfolio_name.strip()
    if not clean_portfolio_name:
        raise ValueError("portfolio_name must not be empty.")

    blockers: list[dict[str, object]] = []
    lineage_wrapper = _as_dict(bundle.get("lineage"))
    quality_wrapper = _as_dict(bundle.get("referenced_quality"))
    outcome_wrapper = _as_dict(bundle.get("referenced_outcome"))
    feedback_calibration_wrapper = _as_dict(bundle.get("feedback_calibration"))
    feedback_artifact_wrappers = _as_list(bundle.get("feedback_artifacts"))

    lineage = _normalize_required_source(
        lineage_wrapper,
        source_key="lineage",
        expected_eval_name=SOURCE_LINEAGE_EVAL_NAME,
        expected_dataset_version=SOURCE_LINEAGE_DATASET_VERSION,
        as_of_date=as_of_date,
        score_date_required=False,
        blockers=blockers,
    )
    quality = _normalize_required_source(
        quality_wrapper,
        source_key="referenced_quality",
        expected_eval_name=SOURCE_QUALITY_EVAL_NAME,
        expected_dataset_version=SOURCE_QUALITY_DATASET_VERSION,
        as_of_date=as_of_date,
        score_date_required=True,
        blockers=blockers,
    )
    outcome = _normalize_required_source(
        outcome_wrapper,
        source_key="referenced_outcome",
        expected_eval_name=SOURCE_OUTCOME_EVAL_NAME,
        expected_dataset_version=SOURCE_OUTCOME_DATASET_VERSION,
        as_of_date=as_of_date,
        score_date_required=True,
        blockers=blockers,
    )
    feedback_calibration = _normalize_required_source(
        feedback_calibration_wrapper,
        source_key="feedback_calibration",
        expected_eval_name=SOURCE_FEEDBACK_CALIBRATION_EVAL_NAME,
        expected_dataset_version=SOURCE_FEEDBACK_CALIBRATION_DATASET_VERSION,
        as_of_date=as_of_date,
        score_date_required=True,
        blockers=blockers,
    )

    lineage_score = _as_dict(lineage_wrapper.get("score_json"))
    quality_score = _as_dict(quality_wrapper.get("score_json"))
    outcome_score = _as_dict(outcome_wrapper.get("score_json"))
    feedback_calibration_score = _as_dict(
        feedback_calibration_wrapper.get("score_json")
    )

    _validate_lineage_anchor(
        lineage_score=lineage_score,
        quality_eval_run_id=_positive_int(quality_wrapper.get("eval_run_id")),
        outcome_eval_run_id=_positive_int(outcome_wrapper.get("eval_run_id")),
        blockers=blockers,
    )
    cohort_filters = _validate_cohort_filters(lineage_score, blockers)
    _validate_feedback_calibration_scope(
        feedback_calibration_score,
        portfolio_name=clean_portfolio_name,
        blockers=blockers,
    )

    recommendations, recommendation_manifest = _build_recommendation_manifest(
        raw_rows=_as_list(bundle.get("recommendations")),
        cohort_filters=cohort_filters,
        quality_cutoff=_parse_date(str(quality_score.get("as_of_date") or "")),
        as_of_date=as_of_date,
        blockers=blockers,
    )
    outcomes, outcome_manifest = _build_outcome_manifest(
        raw_rows=_as_list(bundle.get("outcomes")),
        recommendations=recommendations,
        quality_score=quality_score,
        outcome_score=outcome_score,
        as_of_date=as_of_date,
        blockers=blockers,
    )

    _validate_source_counts(
        recommendation_count=len(recommendations),
        quality_score=quality_score,
        outcome_score=outcome_score,
        outcome_manifest=outcome_manifest,
        blockers=blockers,
    )

    feedback_artifacts, feedback_source_blockers = _normalize_feedback_artifacts(
        feedback_artifact_wrappers,
        as_of_date=as_of_date,
        portfolio_name=clean_portfolio_name,
    )
    blockers.extend(feedback_source_blockers)
    feedback_deduplication = _build_feedback_deduplication(
        calibration_score=feedback_calibration_score,
        feedback_artifacts=feedback_artifacts,
        portfolio_name=clean_portfolio_name,
        blockers=blockers,
    )

    lineage_chain_sha256 = str(
        _as_dict(lineage_score.get("canonical_chain")).get("sha256") or ""
    )
    cohort_snapshot_payload = {
        "contract_version": COHORT_SNAPSHOT_CONTRACT_VERSION,
        "as_of_date": as_of_date.isoformat(),
        "lineage_eval_run_id": lineage.get("eval_run_id"),
        "lineage_chain_sha256": lineage_chain_sha256 or None,
        "quality_eval_run_id": quality.get("eval_run_id"),
        "outcome_eval_run_id": outcome.get("eval_run_id"),
        "cohort_filters": _canonical_copy(cohort_filters),
        "quality_cutoff": quality.get("score_as_of_date"),
        "outcome_cutoff": outcome.get("score_as_of_date"),
        "recommendation_identity_manifest_sha256": recommendation_manifest.get(
            "identity_manifest_sha256"
        ),
        "component_snapshot_manifest_sha256": recommendation_manifest.get(
            "component_snapshot_manifest_sha256"
        ),
        "outcome_identity_manifest_sha256": outcome_manifest.get(
            "identity_manifest_sha256"
        ),
        "feedback_deduplicated_manifest_sha256": feedback_deduplication.get(
            "deduplicated_manifest_sha256"
        ),
    }
    cohort_snapshot = {
        **cohort_snapshot_payload,
        "sha256": _canonical_hash(cohort_snapshot_payload),
    }

    freshness = _build_freshness_evaluation(
        as_of_date=as_of_date,
        lineage_wrapper=lineage_wrapper,
        quality_wrapper=quality_wrapper,
        outcome_wrapper=outcome_wrapper,
        feedback_calibration_wrapper=feedback_calibration_wrapper,
        feedback_artifacts=feedback_artifacts,
    )

    blocker_categories = {
        str(item.get("category") or "incoherent") for item in blockers
    }
    if "incomplete" in blocker_categories:
        status = "foundation_incomplete_fail_closed"
    elif blockers:
        status = "foundation_incoherent_fail_closed"
    elif freshness.get("candidate_policy_passed") is True:
        status = "foundation_complete_fresh_read_only"
    else:
        status = "foundation_complete_stale_read_only"

    structurally_attested = not blockers
    stable_row_identity_attested = (
        structurally_attested
        and recommendation_manifest.get("stable_row_identity_attested") is True
    )
    component_snapshot_attested = (
        structurally_attested
        and recommendation_manifest.get("component_snapshot_integrity_attested")
        is True
    )
    outcome_identity_attested = (
        structurally_attested
        and outcome_manifest.get("outcome_identity_attested") is True
    )
    feedback_deduplication_attested = (
        structurally_attested
        and feedback_deduplication.get("deduplication_attested") is True
    )

    hard_false_permissions = {
        "manual_review_eligible": False,
        "evidence_sufficient_for_pilot_request": False,
        "pilot_scope_defined": False,
        "explicit_user_approval_present": False,
        "read_only_pilot_start_allowed": False,
        "proposal_generation_allowed": False,
        "weight_mutation_allowed": False,
        "automatic_weight_change_allowed": False,
        "portfolio_position_mutation_allowed": False,
        "automatic_rebalance_allowed": False,
        "recommendation_scoring_mutated": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
    }

    return {
        "eval_name": DEFAULT_EVAL_NAME,
        "dataset_version": DEFAULT_DATASET_VERSION,
        "as_of_date": as_of_date.isoformat(),
        "portfolio_name": clean_portfolio_name,
        "mode": "shadow_read_only",
        "authoritative": False,
        "status": status,
        "decision": status,
        "observed_structural_integrity_attested": structurally_attested,
        "eligibility_integrity_attested": False,
        "source_selection": {
            "lineage_anchor": "exact_reconciled_lineage_eval",
            "quality_selection": "exact_lineage_quality_eval_run_id",
            "outcome_selection": "exact_lineage_outcome_eval_run_id",
            "feedback_calibration_selection": (
                "explicit_or_latest_valid_long_term_paper_calibration"
            ),
            "feedback_run_selection": "exact_calibration_latest_feedback_run_ids",
            "independent_latest_replacement_allowed": False,
        },
        "source_snapshot": {
            "lineage": lineage,
            "referenced_quality": quality,
            "referenced_outcome": outcome,
            "feedback_calibration": feedback_calibration,
            "feedback_artifacts": [
                artifact["source"] for artifact in feedback_artifacts
            ],
        },
        "cohort_filters": _canonical_copy(cohort_filters),
        "recommendation_identity": recommendation_manifest,
        "outcome_identity": outcome_manifest,
        "feedback_deduplication": feedback_deduplication,
        "cohort_snapshot": cohort_snapshot,
        "freshness": freshness,
        "attestations": {
            "stable_row_level_sample_identity_attested": (
                stable_row_identity_attested
            ),
            "versioned_component_snapshot_integrity_attested": (
                component_snapshot_attested
            ),
            "outcome_observation_identity_attested": outcome_identity_attested,
            "feedback_deduplication_attested": feedback_deduplication_attested,
            "freshness_policy_defined": True,
            "freshness_candidate_policy_passed": freshness.get(
                "candidate_policy_passed"
            )
            is True,
            "freshness_policy_approved": False,
            "freshness_policy_attested": False,
            "approved_horizon_policy_attested": False,
            "explicit_user_authorization_attested": False,
        },
        "recommendations": recommendations,
        "outcomes": outcomes,
        "blockers": blockers,
        "next_action": _next_action(status),
        "authorization_boundary": {
            "status": "not_requested_not_present",
            "explicit_user_approval_present": False,
            "pilot_scope_defined": False,
            "reason": (
                "Observed identities and deduplicated evidence do not authorize "
                "a pilot or a scoring mutation."
            ),
        },
        "mutation_boundary": {
            "status": "blocked_read_only_shadow",
            "weight_mutation_allowed": False,
            "automatic_weight_change_allowed": False,
            "portfolio_position_mutation_allowed": False,
            "automatic_rebalance_allowed": False,
            "recommendation_scoring_mutated": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "order_boundary": ORDER_BOUNDARY,
        },
        **hard_false_permissions,
        "order_boundary": ORDER_BOUNDARY,
    }


def run_recommendation_weight_review_prospective_evidence_foundation(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    lineage_eval_run_id: int | None = None,
    portfolio_feedback_calibration_eval_run_id: int | None = None,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    bundle = load_prospective_evidence_bundle(
        config=config,
        as_of_date=as_of_date,
        lineage_eval_run_id=lineage_eval_run_id,
        portfolio_feedback_calibration_eval_run_id=(
            portfolio_feedback_calibration_eval_run_id
        ),
        portfolio_name=portfolio_name,
        executor=sql_executor,
    )
    foundation = build_recommendation_weight_review_prospective_evidence_foundation(
        as_of_date=as_of_date,
        bundle=bundle,
        portfolio_name=portfolio_name,
    )
    report: dict[str, object] = {
        "report_name": DEFAULT_EVAL_NAME,
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "portfolio_name": portfolio_name,
        "mode": "shadow_read_only",
        "authoritative": False,
        "foundation": foundation,
    }
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "portfolio_name": portfolio_name,
            "lineage_eval_run_id": _positive_int(
                _as_dict(bundle.get("lineage")).get("eval_run_id")
            ),
            "feedback_calibration_eval_run_id": _positive_int(
                _as_dict(bundle.get("feedback_calibration")).get("eval_run_id")
            ),
            "decision": foundation["decision"],
            "cohort_snapshot_sha256": _as_dict(
                foundation.get("cohort_snapshot")
            ).get("sha256"),
            "mode": "shadow_read_only",
            "authoritative": False,
            "explicit_user_approval_present": False,
            "weight_mutation_allowed": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "order_boundary": ORDER_BOUNDARY,
        },
    )
    try:
        eval_run_id = int(
            sql_executor.execute_scalar(
                render_prospective_evidence_foundation_eval_insert_sql(
                    score_json=foundation
                )
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise
    return {
        **report,
        "status": "completed",
        "run_id": run_id,
        "eval_run_id": eval_run_id,
    }


def _next_action(status: str) -> str:
    if status == "foundation_complete_fresh_read_only":
        return (
            "Use the stable identities, component snapshots, deduplicated feedback set, "
            "and candidate freshness result to draft a separate horizon/freshness approval packet. "
            "Do not start a weight pilot."
        )
    if status == "foundation_complete_stale_read_only":
        return (
            "Refresh the stale source artifacts, then rebuild this read-only foundation. "
            "The candidate policy is not pilot authorization."
        )
    if status == "foundation_incomplete_fail_closed":
        return (
            "Resolve missing lineage, cohort, component, outcome, or feedback references "
            "without rewriting historical evidence."
        )
    return (
        "Resolve the identity, count, reference, or payload inconsistency while preserving "
        "the exact canonical source chain."
    )
