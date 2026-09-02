from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date

from stockanalysis.operations.recommendation_weight_review_prospective_evidence_contract import (
    FEEDBACK_DEDUPLICATION_CONTRACT_VERSION,
    SOURCE_FEEDBACK_DATASET_VERSION,
    SOURCE_FEEDBACK_EVAL_NAME,
    _as_dict,
    _as_list,
    _blocker,
    _canonical_copy,
    _canonical_hash,
    _non_negative_int,
    _normalize_required_source,
    _optional_date_text,
    _optional_text,
    _parse_date,
    _positive_int,
)


def _normalize_feedback_artifacts(
    raw_artifacts: list[dict[str, object]],
    *,
    as_of_date: date,
    portfolio_name: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    blockers: list[dict[str, object]] = []
    normalized: list[dict[str, object]] = []
    seen_ids: set[int] = set()
    for index, wrapper in enumerate(raw_artifacts):
        source = _normalize_required_source(
            wrapper,
            source_key="feedback_artifact",
            expected_eval_name=SOURCE_FEEDBACK_EVAL_NAME,
            expected_dataset_version=SOURCE_FEEDBACK_DATASET_VERSION,
            as_of_date=as_of_date,
            score_date_required=True,
            blockers=blockers,
            blocker_suffix=str(index),
        )
        eval_run_id = _positive_int(wrapper.get("eval_run_id"))
        score = _as_dict(wrapper.get("score_json"))
        if eval_run_id is not None and eval_run_id in seen_ids:
            blockers.append(
                _blocker(
                    "duplicate_feedback_artifact_eval_run_id",
                    "The same feedback eval_run_id is present more than once.",
                    category="incoherent",
                    eval_run_id=eval_run_id,
                )
            )
        if eval_run_id is not None:
            seen_ids.add(eval_run_id)
        actual_portfolio = str(score.get("portfolio_name") or portfolio_name)
        if actual_portfolio != portfolio_name:
            blockers.append(
                _blocker(
                    "feedback_artifact_portfolio_mismatch",
                    "Feedback artifact is scoped to a different portfolio.",
                    category="incoherent",
                    eval_run_id=eval_run_id,
                )
            )
        normalized.append(
            {
                "source": source,
                "score_json": score,
            }
        )
    normalized.sort(
        key=lambda item: (
            str(_as_dict(item.get("source")).get("created_at") or ""),
            int(_as_dict(item.get("source")).get("eval_run_id") or 0),
        ),
        reverse=True,
    )
    return normalized, blockers


def _build_feedback_deduplication(
    *,
    calibration_score: dict[str, object],
    feedback_artifacts: list[dict[str, object]],
    portfolio_name: str,
    blockers: list[dict[str, object]],
) -> dict[str, object]:
    reference_rows = _as_list(calibration_score.get("latest_feedback_runs"))
    referenced_ids: list[int] = []
    invalid_reference_count = 0
    for row in reference_rows:
        eval_run_id = _positive_int(row.get("eval_run_id"))
        if eval_run_id is None:
            invalid_reference_count += 1
        else:
            referenced_ids.append(eval_run_id)
    if invalid_reference_count:
        blockers.append(
            _blocker(
                "feedback_run_reference_invalid",
                "Feedback calibration contains invalid latest_feedback_runs references.",
                category="incomplete",
                invalid_reference_count=invalid_reference_count,
            )
        )
    if not referenced_ids:
        blockers.append(
            _blocker(
                "feedback_run_references_missing",
                "Feedback calibration does not reference any feedback runs.",
                category="incomplete",
            )
        )
    if len(referenced_ids) != len(set(referenced_ids)):
        blockers.append(
            _blocker(
                "feedback_run_reference_duplicate",
                "Feedback calibration references the same feedback run more than once.",
                category="incoherent",
            )
        )
    expected_feedback_run_count = _non_negative_int(
        calibration_score.get("feedback_run_count")
    )
    if expected_feedback_run_count is None:
        blockers.append(
            _blocker(
                "feedback_calibration_run_count_missing",
                "Feedback calibration feedback_run_count is missing or invalid.",
                category="incomplete",
            )
        )
    elif expected_feedback_run_count != len(referenced_ids):
        blockers.append(
            _blocker(
                "feedback_calibration_source_lineage_incomplete",
                "Feedback calibration does not preserve one exact source reference per feedback run.",
                category="incomplete",
                referenced_run_count=len(referenced_ids),
                expected_run_count=expected_feedback_run_count,
            )
        )

    actual_ids = [
        int(_as_dict(artifact.get("source"))["eval_run_id"])
        for artifact in feedback_artifacts
        if _positive_int(_as_dict(artifact.get("source")).get("eval_run_id"))
        is not None
    ]
    missing_ids = sorted(set(referenced_ids) - set(actual_ids))
    extra_ids = sorted(set(actual_ids) - set(referenced_ids))
    if missing_ids:
        blockers.append(
            _blocker(
                "referenced_feedback_artifacts_missing",
                "One or more calibration-referenced feedback artifacts are missing.",
                category="incomplete",
                eval_run_ids=missing_ids,
            )
        )
    if extra_ids:
        blockers.append(
            _blocker(
                "unexpected_feedback_artifacts_present",
                "Feedback bundle contains artifacts not referenced by the calibration anchor.",
                category="incoherent",
                eval_run_ids=extra_ids,
            )
        )

    observations: list[dict[str, object]] = []
    identity_complete = True
    for artifact in feedback_artifacts:
        source = _as_dict(artifact.get("source"))
        score = _as_dict(artifact.get("score_json"))
        eval_run_id = _positive_int(source.get("eval_run_id"))
        source_history_eval_run_id = _positive_int(
            score.get("source_history_eval_run_id")
        )
        source_history_as_of_date = str(
            score.get("source_history_as_of_date") or ""
        )
        items = _as_list(score.get("items")) or _as_list(score.get("latest_items"))
        for item_index, item in enumerate(items):
            identity_payload, identity_error = _feedback_identity_payload(
                portfolio_name=portfolio_name,
                source_history_eval_run_id=source_history_eval_run_id,
                source_history_as_of_date=source_history_as_of_date,
                item=item,
            )
            if identity_error:
                identity_complete = False
                blockers.append(
                    _blocker(
                        "feedback_observation_identity_incomplete",
                        identity_error,
                        category="incomplete",
                        feedback_eval_run_id=eval_run_id,
                        item_index=item_index,
                    )
                )
                continue
            identity_sha256 = _canonical_hash(identity_payload)
            snapshot_payload = {
                **identity_payload,
                "feedback_status": str(item.get("feedback_status") or ""),
                "feedback_reason": str(item.get("feedback_reason") or ""),
                "evidence": _canonical_copy(item.get("evidence")),
                "source_decision": _canonical_copy(item.get("source_decision")),
            }
            observations.append(
                {
                    "feedback_eval_run_id": eval_run_id,
                    "feedback_eval_created_at": source.get("created_at"),
                    "feedback_eval_as_of_date": source.get("score_as_of_date"),
                    "identity_sha256": identity_sha256,
                    "snapshot_sha256": _canonical_hash(snapshot_payload),
                    "identity": identity_payload,
                    "feedback_status": str(item.get("feedback_status") or ""),
                    "feedback_reason": str(item.get("feedback_reason") or ""),
                }
            )

    grouped: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
    for observation in observations:
        grouped[str(observation["identity_sha256"])].append(observation)

    duplicate_groups: list[dict[str, object]] = []
    conflicting_groups: list[dict[str, object]] = []
    deduplicated: list[dict[str, object]] = []
    for identity_sha256, group in sorted(grouped.items()):
        group.sort(
            key=lambda item: (
                str(item.get("feedback_eval_as_of_date") or ""),
                str(item.get("feedback_eval_created_at") or ""),
                int(item.get("feedback_eval_run_id") or 0),
            ),
            reverse=True,
        )
        snapshot_hashes = {str(item["snapshot_sha256"]) for item in group}
        if len(snapshot_hashes) > 1:
            conflicting_groups.append(
                {
                    "identity_sha256": identity_sha256,
                    "occurrence_count": len(group),
                    "snapshot_sha256_values": sorted(snapshot_hashes),
                    "feedback_eval_run_ids": sorted(
                        {
                            int(item["feedback_eval_run_id"])
                            for item in group
                            if item.get("feedback_eval_run_id") is not None
                        }
                    ),
                }
            )
        if len(group) > 1:
            duplicate_groups.append(
                {
                    "identity_sha256": identity_sha256,
                    "occurrence_count": len(group),
                    "duplicate_count": len(group) - 1,
                    "feedback_eval_run_ids": sorted(
                        {
                            int(item["feedback_eval_run_id"])
                            for item in group
                            if item.get("feedback_eval_run_id") is not None
                        }
                    ),
                }
            )
        deduplicated.append(group[0])

    if conflicting_groups:
        blockers.append(
            _blocker(
                "feedback_identity_conflicting_payloads",
                "The same feedback observation identity has conflicting payloads.",
                category="incoherent",
                conflict_count=len(conflicting_groups),
            )
        )

    raw_count = len(observations)
    unique_count = len(deduplicated)
    expected_raw_count = _non_negative_int(calibration_score.get("decision_count"))
    if expected_raw_count is None:
        blockers.append(
            _blocker(
                "feedback_calibration_decision_count_missing",
                "Feedback calibration decision_count is missing or invalid.",
                category="incomplete",
            )
        )
    elif raw_count != expected_raw_count:
        blockers.append(
            _blocker(
                "feedback_calibration_raw_count_mismatch",
                "Raw feedback item count differs from the calibration artifact.",
                category="incoherent",
                actual=raw_count,
                expected=expected_raw_count,
            )
        )

    status_counts = Counter(
        str(item.get("feedback_status") or "unknown") for item in deduplicated
    )
    manifest_rows = [
        {
            "identity_sha256": item["identity_sha256"],
            "snapshot_sha256": item["snapshot_sha256"],
        }
        for item in sorted(
            deduplicated, key=lambda item: str(item["identity_sha256"])
        )
    ]
    manifest_payload = {
        "contract_version": FEEDBACK_DEDUPLICATION_CONTRACT_VERSION,
        "portfolio_name": portfolio_name,
        "rows": manifest_rows,
    }
    source_run_manifest_payload = {
        "contract_version": FEEDBACK_DEDUPLICATION_CONTRACT_VERSION,
        "portfolio_name": portfolio_name,
        "referenced_feedback_eval_run_ids": sorted(set(referenced_ids)),
        "resolved_feedback_eval_run_ids": sorted(set(actual_ids)),
    }
    source_run_lineage_complete = (
        expected_feedback_run_count is not None
        and expected_feedback_run_count == len(referenced_ids)
        and not missing_ids
        and not extra_ids
    )
    return {
        "contract_version": FEEDBACK_DEDUPLICATION_CONTRACT_VERSION,
        "referenced_feedback_eval_run_ids": sorted(set(referenced_ids)),
        "resolved_feedback_eval_run_ids": sorted(set(actual_ids)),
        "source_run_manifest_sha256": _canonical_hash(source_run_manifest_payload),
        "source_run_lineage_complete": source_run_lineage_complete,
        "raw_feedback_item_count": raw_count,
        "unique_feedback_observation_count": unique_count,
        "duplicate_feedback_item_count": raw_count - unique_count,
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_groups": duplicate_groups,
        "conflicting_group_count": len(conflicting_groups),
        "conflicting_groups": conflicting_groups,
        "deduplicated_status_counts": dict(sorted(status_counts.items())),
        "deduplicated_mature_decision_count": (
            status_counts.get("validated", 0)
            + status_counts.get("contradicted", 0)
        ),
        "deduplicated_manifest_sha256": _canonical_hash(manifest_payload),
        "identity_complete": identity_complete,
        "deduplication_attested": (
            identity_complete
            and source_run_lineage_complete
            and not conflicting_groups
        ),
        "counting_policy": "one_count_per_feedback_observation_identity",
    }


def _feedback_identity_payload(
    *,
    portfolio_name: str,
    source_history_eval_run_id: int | None,
    source_history_as_of_date: str,
    item: dict[str, object],
) -> tuple[dict[str, object], str | None]:
    source_decision = _as_dict(item.get("source_decision"))
    evidence = _as_dict(item.get("evidence"))
    recommendation_outcome = _as_dict(evidence.get("recommendation_outcome"))
    thesis_outcome = _as_dict(evidence.get("thesis_outcome"))
    price_evidence = _as_dict(evidence.get("price_evidence"))
    paper_validation = _as_dict(evidence.get("paper_validation"))
    decision_index = _positive_int(item.get("decision_index"))
    symbol = str(item.get("symbol") or "").strip().upper()
    decision_type = str(item.get("decision_type") or "").strip()
    decision_family = str(item.get("decision_family") or "").strip()
    if source_history_eval_run_id is None:
        return {}, "Feedback artifact source_history_eval_run_id is missing."
    if not source_history_as_of_date or _parse_date(source_history_as_of_date) is None:
        return {}, "Feedback artifact source_history_as_of_date is missing or invalid."
    if decision_index is None or not symbol or not decision_type:
        return {}, "Feedback item decision index, symbol, or decision type is missing."
    payload = {
        "contract_version": FEEDBACK_DEDUPLICATION_CONTRACT_VERSION,
        "portfolio_name": portfolio_name,
        "source_history_eval_run_id": source_history_eval_run_id,
        "source_history_as_of_date": _parse_date(
            source_history_as_of_date
        ).isoformat(),
        "decision_index": decision_index,
        "symbol": symbol,
        "decision_type": decision_type,
        "decision_family": decision_family or None,
        "related_recommendation_id": _optional_text(
            source_decision.get("related_recommendation_id")
        ),
        "related_thesis_id": _optional_text(
            source_decision.get("related_thesis_id")
        ),
        "recommendation_outcome_id": _positive_int(
            recommendation_outcome.get("outcome_id")
        ),
        "recommendation_outcome_recommendation_id": _positive_int(
            recommendation_outcome.get("recommendation_id")
        ),
        "recommendation_outcome_measurement_end_date": _optional_date_text(
            recommendation_outcome.get("measurement_end_date")
        ),
        "thesis_outcome_id": _positive_int(thesis_outcome.get("outcome_id")),
        "thesis_outcome_thesis_id": _positive_int(thesis_outcome.get("thesis_id")),
        "thesis_outcome_measurement_end_date": _optional_date_text(
            thesis_outcome.get("measurement_end_date")
        ),
        "latest_price_trade_date": _optional_date_text(
            price_evidence.get("latest_trade_date")
        ),
        "paper_validation_run_id": _positive_int(
            paper_validation.get("paper_validation_run_id")
        ),
    }
    return payload, None
