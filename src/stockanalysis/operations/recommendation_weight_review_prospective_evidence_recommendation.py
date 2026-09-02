from __future__ import annotations

from collections import defaultdict
from datetime import date

from stockanalysis.operations.recommendation_weight_review_prospective_evidence_contract import (
    COHORT_FILTER_KEYS,
    COMPONENT_SNAPSHOT_CONTRACT_VERSION,
    RECOMMENDATION_ROW_IDENTITY_CONTRACT_VERSION,
    _as_dict,
    _as_list,
    _blocker,
    _canonical_decimal_text,
    _canonical_hash,
    _decimal_between_zero_and_one,
    _parse_date,
    _positive_int,
)


def _build_recommendation_manifest(
    *,
    raw_rows: list[dict[str, object]],
    cohort_filters: dict[str, object],
    quality_cutoff: date | None,
    as_of_date: date,
    blockers: list[dict[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    if not raw_rows:
        blockers.append(
            _blocker(
                "recommendation_rows_missing",
                "The reconstructed recommendation cohort is empty.",
                category="incomplete",
            )
        )

    normalized: list[dict[str, object]] = []
    seen_ids: dict[int, str] = {}
    identity_to_ids: defaultdict[str, set[int]] = defaultdict(set)
    component_hash_rows: list[dict[str, object]] = []
    row_identity_rows: list[dict[str, object]] = []
    component_integrity = True
    row_integrity = True

    for index, raw in enumerate(raw_rows):
        recommendation_id = _positive_int(raw.get("recommendation_id"))
        batch_id = _positive_int(raw.get("batch_id"))
        instrument_id = _positive_int(raw.get("instrument_id"))
        symbol = str(raw.get("primary_symbol") or "").strip().upper()
        batch_as_of_text = str(raw.get("batch_as_of_date") or "")
        batch_as_of_date = _parse_date(batch_as_of_text)
        market_code = str(raw.get("market_code") or "")
        strategy_name = str(raw.get("strategy_name") or "")
        horizon_type = str(raw.get("horizon_type") or "")
        universe_version = str(raw.get("universe_version") or "")

        missing_fields = [
            name
            for name, value in (
                ("recommendation_id", recommendation_id),
                ("batch_id", batch_id),
                ("instrument_id", instrument_id),
                ("primary_symbol", symbol),
                ("batch_as_of_date", batch_as_of_date),
                ("market_code", market_code),
                ("strategy_name", strategy_name),
                ("horizon_type", horizon_type),
                ("universe_version", universe_version),
            )
            if value in (None, "")
        ]
        if missing_fields:
            row_integrity = False
            blockers.append(
                _blocker(
                    "recommendation_identity_fields_missing",
                    "Recommendation row is missing required identity fields.",
                    category="incomplete",
                    row_index=index,
                    fields=missing_fields,
                )
            )
            continue

        assert recommendation_id is not None
        assert batch_id is not None
        assert instrument_id is not None
        assert batch_as_of_date is not None

        if batch_as_of_date > as_of_date or (
            quality_cutoff is not None and batch_as_of_date > quality_cutoff
        ):
            row_integrity = False
            blockers.append(
                _blocker(
                    "recommendation_batch_after_cutoff",
                    "Recommendation batch date is after the quality/audit cutoff.",
                    category="incoherent",
                    recommendation_id=recommendation_id,
                )
            )

        bucket = str(raw.get("bucket") or "").strip()
        action = str(raw.get("action") or "").strip()
        rank_position = _positive_int(raw.get("rank_position"))
        total_score = _canonical_decimal_text(raw.get("total_score"))
        recommended_weight = _canonical_decimal_text(
            raw.get("recommended_weight"), allow_none=True
        )
        status = str(raw.get("status") or "").strip()
        batch_created_at_text = str(raw.get("batch_created_at") or "")
        batch_created_date = _parse_date(batch_created_at_text)
        row_value_errors: list[str] = []
        if not bucket:
            row_value_errors.append("bucket")
        if not action:
            row_value_errors.append("action")
        if rank_position is None:
            row_value_errors.append("rank_position")
        if total_score is None:
            row_value_errors.append("total_score")
        if status != "active":
            row_value_errors.append("status")
        if not batch_created_at_text:
            row_value_errors.append("batch_created_at")
        if row_value_errors:
            row_integrity = False
            blockers.append(
                _blocker(
                    "recommendation_snapshot_fields_invalid",
                    "Recommendation row snapshot fields are missing or invalid.",
                    category="incomplete",
                    recommendation_id=recommendation_id,
                    fields=row_value_errors,
                )
            )
        elif batch_created_date is None or batch_created_date > as_of_date:
            row_integrity = False
            blockers.append(
                _blocker(
                    "recommendation_batch_created_at_invalid",
                    "Recommendation batch created_at is invalid or future-dated.",
                    category="incoherent",
                    recommendation_id=recommendation_id,
                )
            )

        actual_filters = {
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "universe_version": universe_version,
        }
        if actual_filters != {
            key: str(cohort_filters.get(key) or "") for key in COHORT_FILTER_KEYS
        }:
            row_integrity = False
            blockers.append(
                _blocker(
                    "recommendation_cohort_filter_mismatch",
                    "Recommendation row does not match the canonical cohort filters.",
                    category="incoherent",
                    recommendation_id=recommendation_id,
                )
            )

        identity_payload = {
            "contract_version": RECOMMENDATION_ROW_IDENTITY_CONTRACT_VERSION,
            "source_batch_id": batch_id,
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "universe_version": universe_version,
            "batch_as_of_date": batch_as_of_date.isoformat(),
            "instrument_id": instrument_id,
            "primary_symbol": symbol,
        }
        identity_sha256 = _canonical_hash(identity_payload)
        identity_to_ids[identity_sha256].add(recommendation_id)
        if recommendation_id in seen_ids:
            row_integrity = False
            blockers.append(
                _blocker(
                    "duplicate_recommendation_id",
                    "The source bundle contains the same recommendation_id more than once.",
                    category="incoherent",
                    recommendation_id=recommendation_id,
                )
            )
        else:
            seen_ids[recommendation_id] = identity_sha256

        components, component_snapshot, component_ok = _build_component_snapshot(
            recommendation_id=recommendation_id,
            recommendation_identity_sha256=identity_sha256,
            raw_components=_as_list(raw.get("components")),
            as_of_date=as_of_date,
            blockers=blockers,
        )
        component_integrity = component_integrity and component_ok
        row_snapshot_payload = {
            "recommendation_identity_sha256": identity_sha256,
            "source_recommendation_id": recommendation_id,
            "source_batch_id": batch_id,
            "thesis_id": _positive_int(raw.get("thesis_id")),
            "bucket": bucket,
            "action": action,
            "rank_position": rank_position,
            "total_score": total_score,
            "recommended_weight": recommended_weight,
            "status": status,
            "batch_source_run_id": _positive_int(raw.get("batch_source_run_id")),
            "batch_created_at": batch_created_at_text or None,
            "component_snapshot_sha256": component_snapshot["sha256"],
        }
        row_snapshot_sha256 = _canonical_hash(row_snapshot_payload)

        normalized_row = {
            "recommendation_id": recommendation_id,
            "recommendation_identity": {
                **identity_payload,
                "sha256": identity_sha256,
            },
            "row_snapshot_sha256": row_snapshot_sha256,
            "batch_id": batch_id,
            "instrument_id": instrument_id,
            "primary_symbol": symbol,
            "thesis_id": _positive_int(raw.get("thesis_id")),
            "bucket": bucket,
            "action": action,
            "rank_position": rank_position,
            "total_score": total_score,
            "recommended_weight": recommended_weight,
            "status": status,
            "batch_as_of_date": batch_as_of_date.isoformat(),
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "universe_version": universe_version,
            "batch_source_run_id": _positive_int(raw.get("batch_source_run_id")),
            "batch_created_at": batch_created_at_text or None,
            "component_snapshot": component_snapshot,
            "components": components,
        }
        normalized.append(normalized_row)
        row_identity_rows.append(
            {
                "recommendation_id": recommendation_id,
                "identity_sha256": identity_sha256,
                "row_snapshot_sha256": row_snapshot_sha256,
            }
        )
        component_hash_rows.append(
            {
                "recommendation_identity_sha256": identity_sha256,
                "component_snapshot_sha256": component_snapshot["sha256"],
            }
        )

    collision_groups = [
        {
            "identity_sha256": identity,
            "recommendation_ids": sorted(ids),
        }
        for identity, ids in sorted(identity_to_ids.items())
        if len(ids) > 1
    ]
    if collision_groups:
        row_integrity = False
        blockers.append(
            _blocker(
                "recommendation_natural_identity_collision",
                "More than one source recommendation_id maps to the same deterministic identity.",
                category="incoherent",
                collision_count=len(collision_groups),
            )
        )

    normalized.sort(
        key=lambda row: (
            str(_as_dict(row.get("recommendation_identity")).get("sha256") or ""),
            int(row.get("recommendation_id") or 0),
        )
    )
    row_identity_rows.sort(key=lambda item: str(item["identity_sha256"]))
    component_hash_rows.sort(
        key=lambda item: str(item["recommendation_identity_sha256"])
    )
    manifest_payload = {
        "contract_version": RECOMMENDATION_ROW_IDENTITY_CONTRACT_VERSION,
        "recommendation_count": len(normalized),
        "rows": row_identity_rows,
    }
    component_manifest_payload = {
        "contract_version": COMPONENT_SNAPSHOT_CONTRACT_VERSION,
        "recommendation_count": len(normalized),
        "snapshots": component_hash_rows,
    }
    manifest = {
        "contract_version": RECOMMENDATION_ROW_IDENTITY_CONTRACT_VERSION,
        "component_contract_version": COMPONENT_SNAPSHOT_CONTRACT_VERSION,
        "recommendation_count": len(normalized),
        "identity_manifest_sha256": _canonical_hash(manifest_payload),
        "component_snapshot_manifest_sha256": _canonical_hash(
            component_manifest_payload
        ),
        "stable_row_identity_attested": bool(normalized) and row_integrity,
        "component_snapshot_integrity_attested": (
            bool(normalized) and component_integrity
        ),
        "identity_collision_count": len(collision_groups),
        "identity_collisions": collision_groups,
    }
    return normalized, manifest


def _build_component_snapshot(
    *,
    recommendation_id: int,
    recommendation_identity_sha256: str,
    raw_components: list[dict[str, object]],
    as_of_date: date,
    blockers: list[dict[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object], bool]:
    if not raw_components:
        blockers.append(
            _blocker(
                "recommendation_components_missing",
                "Recommendation has no component rows.",
                category="incomplete",
                recommendation_id=recommendation_id,
            )
        )
    normalized: list[dict[str, object]] = []
    names: set[str] = set()
    integrity = bool(raw_components)
    for index, raw in enumerate(raw_components):
        name = str(raw.get("component_name") or "").strip()
        score = _canonical_decimal_text(raw.get("component_score"))
        weight = _canonical_decimal_text(raw.get("component_weight"), allow_none=True)
        created_at_text = str(raw.get("created_at") or "")
        created_date = _parse_date(created_at_text)
        if not name or score is None:
            integrity = False
            blockers.append(
                _blocker(
                    "component_identity_fields_missing",
                    "Component row is missing component_name or component_score.",
                    category="incomplete",
                    recommendation_id=recommendation_id,
                    component_index=index,
                )
            )
            continue
        if name in names:
            integrity = False
            blockers.append(
                _blocker(
                    "duplicate_component_name",
                    "Recommendation contains duplicate component_name rows.",
                    category="incoherent",
                    recommendation_id=recommendation_id,
                    component_name=name,
                )
            )
        names.add(name)
        if not _decimal_between_zero_and_one(score):
            integrity = False
            blockers.append(
                _blocker(
                    "component_score_out_of_range",
                    "Component score must be between 0 and 1.",
                    category="incoherent",
                    recommendation_id=recommendation_id,
                    component_name=name,
                )
            )
        if weight is not None and not _decimal_between_zero_and_one(weight):
            integrity = False
            blockers.append(
                _blocker(
                    "component_weight_out_of_range",
                    "Component weight must be null or between 0 and 1.",
                    category="incoherent",
                    recommendation_id=recommendation_id,
                    component_name=name,
                )
            )
        if not created_at_text:
            integrity = False
            blockers.append(
                _blocker(
                    "component_created_at_missing",
                    "Component row created_at is missing.",
                    category="incomplete",
                    recommendation_id=recommendation_id,
                    component_name=name,
                )
            )
        elif created_date is None or created_date > as_of_date:
            integrity = False
            blockers.append(
                _blocker(
                    "component_created_at_invalid",
                    "Component row created_at is invalid or future-dated.",
                    category="incoherent",
                    recommendation_id=recommendation_id,
                    component_name=name,
                )
            )
        normalized.append(
            {
                "component_name": name,
                "component_score": score,
                "component_weight": weight,
                "explanation": str(raw.get("explanation") or "") or None,
                "created_at": created_at_text or None,
            }
        )
    normalized.sort(key=lambda item: str(item["component_name"]))
    snapshot_payload = {
        "contract_version": COMPONENT_SNAPSHOT_CONTRACT_VERSION,
        "recommendation_identity_sha256": recommendation_identity_sha256,
        "source_recommendation_id": recommendation_id,
        "components": normalized,
    }
    snapshot = {
        "contract_version": COMPONENT_SNAPSHOT_CONTRACT_VERSION,
        "component_count": len(normalized),
        "sha256": _canonical_hash(snapshot_payload),
    }
    return normalized, snapshot, integrity
