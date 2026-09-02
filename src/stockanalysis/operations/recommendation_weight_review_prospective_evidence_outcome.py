from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from stockanalysis.operations.recommendation_weight_review_prospective_evidence_contract import (
    OUTCOME_OBSERVATION_CONTRACT_VERSION,
    _as_dict,
    _as_list,
    _blocker,
    _canonical_decimal_text,
    _canonical_hash,
    _non_negative_int,
    _parse_date,
    _positive_int,
    _strict_positive_int_list,
)


def _build_outcome_manifest(
    *,
    raw_rows: list[dict[str, object]],
    recommendations: list[dict[str, object]],
    quality_score: dict[str, object],
    outcome_score: dict[str, object],
    as_of_date: date,
    blockers: list[dict[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    recommendation_by_id = {
        int(row["recommendation_id"]): row for row in recommendations
    }
    normalized: list[dict[str, object]] = []
    identity_to_outcome_ids: defaultdict[str, set[int]] = defaultdict(set)
    seen_outcome_ids: set[int] = set()
    integrity = True

    for index, raw in enumerate(raw_rows):
        outcome_id = _positive_int(raw.get("outcome_id"))
        recommendation_id = _positive_int(raw.get("recommendation_id"))
        start_text = str(raw.get("measurement_start_date") or "")
        end_text = str(raw.get("measurement_end_date") or "")
        start_date = _parse_date(start_text)
        end_date = _parse_date(end_text)
        horizon_days = _non_negative_int(raw.get("horizon_days"))
        if (
            outcome_id is None
            or recommendation_id is None
            or start_date is None
            or end_date is None
            or horizon_days is None
        ):
            integrity = False
            blockers.append(
                _blocker(
                    "outcome_identity_fields_missing",
                    "Outcome row is missing required identity fields.",
                    category="incomplete",
                    row_index=index,
                )
            )
            continue
        if recommendation_id not in recommendation_by_id:
            integrity = False
            blockers.append(
                _blocker(
                    "outcome_recommendation_reference_unknown",
                    "Outcome references a recommendation outside the canonical cohort.",
                    category="incoherent",
                    outcome_id=outcome_id,
                    recommendation_id=recommendation_id,
                )
            )
            continue
        if end_date < start_date or end_date > as_of_date:
            integrity = False
            blockers.append(
                _blocker(
                    "outcome_measurement_dates_invalid",
                    "Outcome measurement dates are reversed or future-dated.",
                    category="incoherent",
                    outcome_id=outcome_id,
                )
            )
        entry_price = _canonical_decimal_text(raw.get("entry_price"))
        exit_price = _canonical_decimal_text(raw.get("exit_price"))
        absolute_return_pct = _canonical_decimal_text(raw.get("absolute_return_pct"))
        outcome_label = str(raw.get("outcome_label") or "").strip()
        created_at_text = str(raw.get("created_at") or "")
        created_date = _parse_date(created_at_text)
        if (
            entry_price is None
            or exit_price is None
            or absolute_return_pct is None
            or not outcome_label
            or not created_at_text
        ):
            integrity = False
            blockers.append(
                _blocker(
                    "outcome_snapshot_fields_missing",
                    "Outcome snapshot is missing required prices, return, label, or created_at.",
                    category="incomplete",
                    outcome_id=outcome_id,
                )
            )
        elif created_date is None or created_date > as_of_date:
            integrity = False
            blockers.append(
                _blocker(
                    "outcome_created_at_invalid",
                    "Outcome created_at is invalid or future-dated.",
                    category="incoherent",
                    outcome_id=outcome_id,
                )
            )
        recommendation_identity_sha256 = str(
            _as_dict(
                recommendation_by_id[recommendation_id].get(
                    "recommendation_identity"
                )
            ).get("sha256")
            or ""
        )
        identity_payload = {
            "contract_version": OUTCOME_OBSERVATION_CONTRACT_VERSION,
            "recommendation_identity_sha256": recommendation_identity_sha256,
            "measurement_start_date": start_date.isoformat(),
            "measurement_end_date": end_date.isoformat(),
            "horizon_days": horizon_days,
        }
        identity_sha256 = _canonical_hash(identity_payload)
        identity_to_outcome_ids[identity_sha256].add(outcome_id)
        if outcome_id in seen_outcome_ids:
            integrity = False
            blockers.append(
                _blocker(
                    "duplicate_outcome_id",
                    "The source bundle contains the same outcome_id more than once.",
                    category="incoherent",
                    outcome_id=outcome_id,
                )
            )
        seen_outcome_ids.add(outcome_id)
        snapshot_payload = {
            **identity_payload,
            "source_outcome_id": outcome_id,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "absolute_return_pct": absolute_return_pct,
            "benchmark_code": str(raw.get("benchmark_code") or "") or None,
            "benchmark_return_pct": _canonical_decimal_text(
                raw.get("benchmark_return_pct"), allow_none=True
            ),
            "alpha_pct": _canonical_decimal_text(
                raw.get("alpha_pct"), allow_none=True
            ),
            "max_drawdown_pct": _canonical_decimal_text(
                raw.get("max_drawdown_pct"), allow_none=True
            ),
            "outcome_label": outcome_label,
            "source_run_id": _positive_int(raw.get("source_run_id")),
            "created_at": created_at_text or None,
        }
        normalized.append(
            {
                "outcome_id": outcome_id,
                "recommendation_id": recommendation_id,
                "outcome_identity": {
                    **identity_payload,
                    "sha256": identity_sha256,
                },
                "snapshot_sha256": _canonical_hash(snapshot_payload),
                "measurement_start_date": start_date.isoformat(),
                "measurement_end_date": end_date.isoformat(),
                "horizon_days": horizon_days,
                "entry_price": snapshot_payload["entry_price"],
                "exit_price": snapshot_payload["exit_price"],
                "absolute_return_pct": snapshot_payload[
                    "absolute_return_pct"
                ],
                "benchmark_code": snapshot_payload["benchmark_code"],
                "benchmark_return_pct": snapshot_payload[
                    "benchmark_return_pct"
                ],
                "alpha_pct": snapshot_payload["alpha_pct"],
                "max_drawdown_pct": snapshot_payload[
                    "max_drawdown_pct"
                ],
                "outcome_label": snapshot_payload["outcome_label"],
                "source_run_id": snapshot_payload["source_run_id"],
                "created_at": snapshot_payload["created_at"],
            }
        )

    collision_groups = [
        {
            "identity_sha256": identity,
            "outcome_ids": sorted(ids),
        }
        for identity, ids in sorted(identity_to_outcome_ids.items())
        if len(ids) > 1
    ]
    if collision_groups:
        integrity = False
        blockers.append(
            _blocker(
                "outcome_identity_collision",
                "More than one outcome_id maps to the same deterministic observation identity.",
                category="incoherent",
                collision_count=len(collision_groups),
            )
        )

    normalized.sort(
        key=lambda row: (
            str(_as_dict(row.get("outcome_identity")).get("sha256") or ""),
            int(row.get("outcome_id") or 0),
        )
    )
    identity_rows = [
        {
            "outcome_id": row["outcome_id"],
            "identity_sha256": _as_dict(row["outcome_identity"])["sha256"],
            "snapshot_sha256": row["snapshot_sha256"],
        }
        for row in normalized
    ]
    quality_count = _reconstruct_quality_outcome_count(
        recommendations=recommendations,
        outcomes=normalized,
        quality_score=quality_score,
    )
    horizon_counts = _reconstruct_outcome_horizon_counts(
        recommendations=recommendations,
        outcomes=normalized,
        outcome_score=outcome_score,
    )
    manifest_payload = {
        "contract_version": OUTCOME_OBSERVATION_CONTRACT_VERSION,
        "outcome_count": len(normalized),
        "rows": identity_rows,
    }
    return normalized, {
        "contract_version": OUTCOME_OBSERVATION_CONTRACT_VERSION,
        "outcome_row_count": len(normalized),
        "identity_manifest_sha256": _canonical_hash(manifest_payload),
        "outcome_identity_attested": integrity,
        "identity_collision_count": len(collision_groups),
        "identity_collisions": collision_groups,
        "reconstructed_quality_outcome_count": quality_count,
        "reconstructed_horizon_outcome_counts": horizon_counts,
    }


def _validate_source_counts(
    *,
    recommendation_count: int,
    quality_score: dict[str, object],
    outcome_score: dict[str, object],
    outcome_manifest: dict[str, object],
    blockers: list[dict[str, object]],
) -> None:
    expected_quality_recommendations = _non_negative_int(
        quality_score.get("recommendation_count")
    )
    outcome_summary = _as_dict(
        _as_dict(outcome_score.get("sample_audit_after")).get("summary")
    )
    expected_outcome_recommendations = _non_negative_int(
        outcome_summary.get("recommendation_count")
    )
    for code, label, expected in (
        (
            "quality_recommendation_count_mismatch",
            "referenced quality",
            expected_quality_recommendations,
        ),
        (
            "outcome_recommendation_count_mismatch",
            "referenced outcome",
            expected_outcome_recommendations,
        ),
    ):
        if expected is None:
            blockers.append(
                _blocker(
                    f"{code}_expected_missing",
                    f"{label} recommendation_count is missing or invalid.",
                    category="incomplete",
                )
            )
        elif recommendation_count != expected:
            blockers.append(
                _blocker(
                    code,
                    f"Reconstructed recommendation count differs from {label}.",
                    category="incoherent",
                    actual=recommendation_count,
                    expected=expected,
                )
            )

    expected_quality_outcomes = _non_negative_int(quality_score.get("outcome_count"))
    actual_quality_outcomes = _non_negative_int(
        outcome_manifest.get("reconstructed_quality_outcome_count")
    )
    if expected_quality_outcomes is None:
        blockers.append(
            _blocker(
                "quality_outcome_count_expected_missing",
                "Referenced quality outcome_count is missing or invalid.",
                category="incomplete",
            )
        )
    elif actual_quality_outcomes != expected_quality_outcomes:
        blockers.append(
            _blocker(
                "quality_outcome_count_mismatch",
                "Reconstructed quality outcome count differs from the referenced quality artifact.",
                category="incoherent",
                actual=actual_quality_outcomes,
                expected=expected_quality_outcomes,
            )
        )

    expected_horizon_rows = {
        _positive_int(item.get("horizon_day")): _non_negative_int(
            item.get("outcome_count")
        )
        for item in _as_list(
            _as_dict(outcome_score.get("sample_audit_after")).get(
                "horizon_coverage"
            )
        )
    }
    expected_horizon_rows = {
        horizon: count
        for horizon, count in expected_horizon_rows.items()
        if horizon is not None
    }
    actual_horizon_rows = {
        _positive_int(key): _non_negative_int(value)
        for key, value in _as_dict(
            outcome_manifest.get("reconstructed_horizon_outcome_counts")
        ).items()
    }
    actual_horizon_rows = {
        horizon: count
        for horizon, count in actual_horizon_rows.items()
        if horizon is not None
    }
    if not expected_horizon_rows:
        blockers.append(
            _blocker(
                "outcome_horizon_counts_expected_missing",
                "Referenced outcome horizon coverage is missing.",
                category="incomplete",
            )
        )
    elif actual_horizon_rows != expected_horizon_rows:
        blockers.append(
            _blocker(
                "outcome_horizon_counts_mismatch",
                "Reconstructed horizon outcome counts differ from the referenced outcome artifact.",
                category="incoherent",
                actual={str(k): v for k, v in actual_horizon_rows.items()},
                expected={str(k): v for k, v in expected_horizon_rows.items()},
            )
        )

    expected_total_horizon_outcomes = _non_negative_int(
        outcome_summary.get("outcome_count")
    )
    actual_total_horizon_outcomes = sum(
        count or 0 for count in actual_horizon_rows.values()
    )
    if expected_total_horizon_outcomes is None:
        blockers.append(
            _blocker(
                "outcome_total_count_expected_missing",
                "Referenced outcome summary outcome_count is missing.",
                category="incomplete",
            )
        )
    elif actual_total_horizon_outcomes != expected_total_horizon_outcomes:
        blockers.append(
            _blocker(
                "outcome_total_count_mismatch",
                "Reconstructed recommendation×horizon outcome count differs from the referenced outcome summary.",
                category="incoherent",
                actual=actual_total_horizon_outcomes,
                expected=expected_total_horizon_outcomes,
            )
        )


def _reconstruct_quality_outcome_count(
    *,
    recommendations: list[dict[str, object]],
    outcomes: list[dict[str, object]],
    quality_score: dict[str, object],
) -> int:
    cutoff = _parse_date(str(quality_score.get("as_of_date") or ""))
    max_horizon = _positive_int(quality_score.get("horizon_days"))
    if cutoff is None or max_horizon is None:
        return 0
    recommendation_ids = {int(row["recommendation_id"]) for row in recommendations}
    observed: set[int] = set()
    for outcome in outcomes:
        recommendation_id = int(outcome["recommendation_id"])
        end_date = _parse_date(str(outcome.get("measurement_end_date") or ""))
        horizon_days = _non_negative_int(outcome.get("horizon_days"))
        if (
            recommendation_id in recommendation_ids
            and end_date is not None
            and end_date <= cutoff
            and horizon_days is not None
            and horizon_days <= max_horizon
        ):
            observed.add(recommendation_id)
    return len(observed)


def _reconstruct_outcome_horizon_counts(
    *,
    recommendations: list[dict[str, object]],
    outcomes: list[dict[str, object]],
    outcome_score: dict[str, object],
) -> dict[str, int]:
    cutoff = _parse_date(str(outcome_score.get("as_of_date") or ""))
    horizons = _strict_positive_int_list(outcome_score.get("horizon_days"))
    if cutoff is None:
        return {str(horizon): 0 for horizon in horizons}
    outcomes_by_recommendation: defaultdict[int, list[dict[str, object]]] = defaultdict(
        list
    )
    for outcome in outcomes:
        outcomes_by_recommendation[int(outcome["recommendation_id"])].append(outcome)

    counts: dict[str, int] = {str(horizon): 0 for horizon in horizons}
    for recommendation in recommendations:
        recommendation_id = int(recommendation["recommendation_id"])
        start_date = _parse_date(
            str(recommendation.get("batch_as_of_date") or "")
        )
        if start_date is None:
            continue
        for horizon in horizons:
            expected_end = start_date + timedelta(days=horizon)
            latest_allowed = min(expected_end, cutoff)
            candidates: list[tuple[int, int, int, dict[str, object]]] = []
            for outcome in outcomes_by_recommendation.get(recommendation_id, []):
                measurement_end = _parse_date(
                    str(outcome.get("measurement_end_date") or "")
                )
                actual_horizon = _non_negative_int(outcome.get("horizon_days"))
                if measurement_end is None or actual_horizon is None:
                    continue
                if measurement_end < start_date or measurement_end > latest_allowed:
                    continue
                if actual_horizon < max(horizon - 7, 0) or actual_horizon > horizon + 7:
                    continue
                candidates.append(
                    (
                        abs(actual_horizon - horizon),
                        -measurement_end.toordinal(),
                        -int(outcome["outcome_id"]),
                        outcome,
                    )
                )
            if candidates:
                counts[str(horizon)] += 1
    return counts
