from __future__ import annotations

import json
from datetime import date

from stockanalysis.operations.recommendation_weight_review_prospective_evidence_contract import (
    ORDER_BOUNDARY,
    _as_dict,
    _as_list,
    _blocker,
    _canonical_copy,
    _canonical_hash,
    _is_sha256,
    _positive_int,
)


DEFAULT_EVAL_NAME = "recommendation_weight_review_prospective_evidence_live_observation_v1"
DEFAULT_DATASET_VERSION = "recommendation-weight-review-prospective-evidence-live-observation-v1"
DEFAULT_PIPELINE_NAME = "recommendation_weight_review_prospective_evidence_live_observation_v1"
DEFAULT_PROVIDER = "postgres"
DEFAULT_MODEL_NAME = "deterministic-live-observation-v1"
DATABASE_IDENTITY_CONTRACT_VERSION = "stockanalysis-database-identity-v1"
LEGACY_SURFACE_CONTRACT_VERSION = "recommendation-weight-review-legacy-surface-v1"

REQUIRED_RELATIONS = (
    "ai.eval_run",
    "ops.pipeline_run",
    "performance.recommendation_outcome",
    "portfolio.portfolio",
    "signal.recommendation",
    "signal.recommendation_batch",
    "signal.recommendation_score_component",
)

HARD_FALSE_PERMISSION_KEYS = (
    "manual_review_eligible",
    "evidence_sufficient_for_pilot_request",
    "pilot_scope_defined",
    "explicit_user_approval_present",
    "read_only_pilot_start_allowed",
    "proposal_generation_allowed",
    "weight_mutation_allowed",
    "automatic_weight_change_allowed",
    "portfolio_position_mutation_allowed",
    "automatic_rebalance_allowed",
    "recommendation_scoring_mutated",
    "automatic_order_allowed",
    "broker_submit_allowed",
)


class LiveObservationIntegrityError(RuntimeError):
    """Raised when the exact live evidence surface changes during observation."""


def normalize_live_observation_database_identity(
    payload: dict[str, object],
) -> dict[str, object]:
    raw_relations = _as_dict(payload.get("required_relations"))
    relations = {
        relation: raw_relations.get(relation) is True
        for relation in REQUIRED_RELATIONS
    }
    identity = {
        "contract_version": _text(payload.get("contract_version")),
        "database_name": _text(payload.get("database_name")),
        "role_name": _text(payload.get("role_name")),
        "server_version_num": _text(payload.get("server_version_num")),
        "server_address": _optional_text(payload.get("server_address")),
        "server_port": _optional_int(payload.get("server_port")),
        "required_relations": relations,
    }
    missing_fields = [
        key
        for key in ("contract_version", "database_name", "role_name", "server_version_num")
        if not identity[key]
    ]
    missing_relations = [key for key, present in relations.items() if not present]
    contract_matches = (
        identity["contract_version"] == DATABASE_IDENTITY_CONTRACT_VERSION
    )
    return {
        **identity,
        "missing_identity_fields": missing_fields,
        "missing_required_relations": missing_relations,
        "contract_matches": contract_matches,
        "complete": contract_matches and not missing_fields and not missing_relations,
        "sha256": _canonical_hash(identity),
    }


def build_legacy_surface_snapshot(
    *,
    bundle: dict[str, object],
    foundation: dict[str, object],
) -> dict[str, object]:
    source_scores: dict[str, object] = {
        key: _source_score_identity(_as_dict(bundle.get(key)))
        for key in (
            "lineage",
            "referenced_quality",
            "referenced_outcome",
            "feedback_calibration",
        )
    }
    source_scores["feedback_artifacts"] = sorted(
        (_source_score_identity(item) for item in _as_list(bundle.get("feedback_artifacts"))),
        key=lambda item: (int(item.get("eval_run_id") or 0), str(item.get("eval_name") or "")),
    )
    payload = {
        "contract_version": LEGACY_SURFACE_CONTRACT_VERSION,
        "foundation_eval_name": foundation.get("eval_name"),
        "foundation_dataset_version": foundation.get("dataset_version"),
        "foundation_status": foundation.get("status"),
        "source_scores": source_scores,
        "source_selection": _canonical_copy(foundation.get("source_selection")),
        "source_snapshot": _canonical_copy(foundation.get("source_snapshot")),
        "cohort_filters": _canonical_copy(foundation.get("cohort_filters")),
        "recommendation_identity": _canonical_copy(foundation.get("recommendation_identity")),
        "outcome_identity": _canonical_copy(foundation.get("outcome_identity")),
        "feedback_deduplication": _canonical_copy(foundation.get("feedback_deduplication")),
        "cohort_snapshot": _canonical_copy(foundation.get("cohort_snapshot")),
        "freshness": _canonical_copy(foundation.get("freshness")),
        "recommendations": _canonical_rows(foundation.get("recommendations")),
        "outcomes": _canonical_rows(foundation.get("outcomes")),
        "blockers": _canonical_rows(foundation.get("blockers")),
        "mutation_boundary": _canonical_copy(foundation.get("mutation_boundary")),
        "permissions": {
            key: foundation.get(key) for key in HARD_FALSE_PERMISSION_KEYS
        },
        "order_boundary": foundation.get("order_boundary"),
    }
    recommendation_identity = _as_dict(foundation.get("recommendation_identity"))
    outcome_identity = _as_dict(foundation.get("outcome_identity"))
    feedback = _as_dict(foundation.get("feedback_deduplication"))
    return {
        "contract_version": LEGACY_SURFACE_CONTRACT_VERSION,
        "recommendation_count": _first_int(
            recommendation_identity, "recommendation_count", "row_count"
        ),
        "outcome_count": _first_int(
            outcome_identity,
            "outcome_count",
            "outcome_row_count",
            "observation_count",
            "row_count",
        ),
        "deduplicated_feedback_count": _first_int(
            feedback,
            "deduplicated_feedback_count",
            "deduplicated_observation_count",
            "unique_feedback_observation_count",
            "unique_observation_count",
        ),
        "source_eval_run_ids": _source_eval_run_ids(source_scores),
        "payload_sha256": _canonical_hash(payload),
    }


def build_recommendation_weight_review_prospective_evidence_live_observation(
    *,
    as_of_date: date,
    environment_label: str,
    expected_database_identity_sha256: str,
    database_identity_payload: dict[str, object],
    lineage_eval_run_id: int,
    portfolio_feedback_calibration_eval_run_id: int,
    bundle: dict[str, object],
    foundation: dict[str, object],
    legacy_surface_before: dict[str, object],
    legacy_surface_after: dict[str, object] | None = None,
) -> dict[str, object]:
    environment_label = validate_environment_label(environment_label)
    expected_sha = validate_sha256(
        expected_database_identity_sha256,
        field_name="expected_database_identity_sha256",
    )
    lineage_id = require_positive_int(lineage_eval_run_id, field_name="lineage_eval_run_id")
    feedback_id = require_positive_int(
        portfolio_feedback_calibration_eval_run_id,
        field_name="portfolio_feedback_calibration_eval_run_id",
    )
    identity = normalize_live_observation_database_identity(database_identity_payload)
    identity_attested = identity.get("complete") is True and identity.get("sha256") == expected_sha

    actual_lineage_id = _positive_int(_as_dict(bundle.get("lineage")).get("eval_run_id"))
    actual_feedback_id = _positive_int(
        _as_dict(bundle.get("feedback_calibration")).get("eval_run_id")
    )
    exact_sources = actual_lineage_id == lineage_id and actual_feedback_id == feedback_id
    blockers: list[dict[str, object]] = []
    _append_identity_blocker(blockers, identity, expected_sha)
    _append_source_blocker(blockers, "lineage", lineage_id, actual_lineage_id)
    _append_source_blocker(
        blockers, "portfolio_feedback_calibration", feedback_id, actual_feedback_id
    )

    before_sha = _snapshot_sha(legacy_surface_before)
    after_sha = _snapshot_sha(legacy_surface_after) if legacy_surface_after is not None else None
    unchanged = before_sha == after_sha if after_sha is not None else None
    if unchanged is False:
        blockers.append(
            _blocker(
                "legacy_surface_changed_during_observation",
                "The exact recommendation evidence surface changed during observation.",
                category="incoherent",
                before_sha256=before_sha,
                after_sha256=after_sha,
            )
        )

    foundation_status = str(foundation.get("status") or "")
    status = _resolve_status(foundation_status, blockers)
    result = _base_observation(
        as_of_date=as_of_date,
        environment_label=environment_label,
        status=status,
        append_only_eval_allowed=identity_attested,
    )
    result.update(
        {
            "database_identity": {
                **identity,
                "expected_sha256": expected_sha,
                "attested": identity_attested,
            },
            "source_lock": {
                "lineage_eval_run_id": lineage_id,
                "observed_lineage_eval_run_id": actual_lineage_id,
                "portfolio_feedback_calibration_eval_run_id": feedback_id,
                "observed_portfolio_feedback_calibration_eval_run_id": actual_feedback_id,
                "exact_source_ids_attested": exact_sources,
                "independent_latest_replacement_allowed": False,
            },
            "legacy_surface": {
                "contract_version": LEGACY_SURFACE_CONTRACT_VERSION,
                "before": _canonical_copy(legacy_surface_before),
                "after": _canonical_copy(legacy_surface_after),
                "before_sha256": before_sha,
                "after_sha256": after_sha,
                "unchanged": unchanged,
                "stability_attested": unchanged is True,
            },
            "evidence_summary": {
                "foundation_status": foundation_status or None,
                "observed_structural_integrity_attested": foundation.get(
                    "observed_structural_integrity_attested"
                )
                is True,
                "cohort_filters": _canonical_copy(foundation.get("cohort_filters")),
                "recommendation_identity": _canonical_copy(
                    foundation.get("recommendation_identity")
                ),
                "outcome_identity": _canonical_copy(foundation.get("outcome_identity")),
                "feedback_deduplication": _canonical_copy(
                    foundation.get("feedback_deduplication")
                ),
                "cohort_snapshot": _canonical_copy(foundation.get("cohort_snapshot")),
                "freshness": _canonical_copy(foundation.get("freshness")),
                "foundation_blockers": _canonical_copy(foundation.get("blockers")),
            },
            "blockers": blockers,
        }
    )
    return result


def build_environment_blocked_observation(
    *,
    as_of_date: date,
    environment_label: str,
    expected_database_identity_sha256: str,
    database_identity: dict[str, object],
    lineage_eval_run_id: int,
    portfolio_feedback_calibration_eval_run_id: int,
) -> dict[str, object]:
    expected_sha = validate_sha256(
        expected_database_identity_sha256,
        field_name="expected_database_identity_sha256",
    )
    complete = database_identity.get("complete") is True
    status = (
        "live_observation_blocked_environment_mismatch"
        if complete
        else "live_observation_incomplete_fail_closed"
    )
    blockers: list[dict[str, object]] = []
    _append_identity_blocker(blockers, database_identity, expected_sha)
    result = _base_observation(
        as_of_date=as_of_date,
        environment_label=validate_environment_label(environment_label),
        status=status,
        append_only_eval_allowed=False,
    )
    result.update(
        {
            "database_identity": {
                **database_identity,
                "expected_sha256": expected_sha,
                "attested": False,
            },
            "source_lock": {
                "lineage_eval_run_id": lineage_eval_run_id,
                "observed_lineage_eval_run_id": None,
                "portfolio_feedback_calibration_eval_run_id": (
                    portfolio_feedback_calibration_eval_run_id
                ),
                "observed_portfolio_feedback_calibration_eval_run_id": None,
                "exact_source_ids_attested": False,
                "independent_latest_replacement_allowed": False,
            },
            "legacy_surface": {
                "contract_version": LEGACY_SURFACE_CONTRACT_VERSION,
                "before": None,
                "after": None,
                "before_sha256": None,
                "after_sha256": None,
                "unchanged": None,
                "stability_attested": False,
            },
            "evidence_summary": None,
            "blockers": blockers,
        }
    )
    return result


def validate_sha256(value: str, *, field_name: str) -> str:
    normalized = value.strip().lower()
    if not _is_sha256(normalized):
        raise ValueError(f"{field_name} must be a 64-character SHA-256 hex string.")
    return normalized


def require_positive_int(value: object, *, field_name: str) -> int:
    parsed = _positive_int(value)
    if parsed is None:
        raise ValueError(f"{field_name} must be greater than 0.")
    return parsed


def validate_environment_label(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("environment_label must not be empty.")
    if len(normalized) > 128:
        raise ValueError("environment_label must be 128 characters or fewer.")
    return normalized


def _base_observation(
    *,
    as_of_date: date,
    environment_label: str,
    status: str,
    append_only_eval_allowed: bool,
) -> dict[str, object]:
    return {
        "eval_name": DEFAULT_EVAL_NAME,
        "dataset_version": DEFAULT_DATASET_VERSION,
        "as_of_date": as_of_date.isoformat(),
        "environment_label": environment_label,
        "mode": "live_database_append_only_observation",
        "authoritative": False,
        "status": status,
        "decision": status,
        "observation_boundary": {
            "database_identity_required": True,
            "exact_source_ids_required": True,
            "append_only_eval_allowed": append_only_eval_allowed,
            "legacy_surface_mutation_allowed": False,
            "schema_mutation_allowed": False,
            "scheduler_mutation_allowed": False,
            "deployment_allowed": False,
            "order_boundary": ORDER_BOUNDARY,
        },
        "mutation_boundary": {
            "status": "blocked_read_only_observation",
            "weight_mutation_allowed": False,
            "automatic_weight_change_allowed": False,
            "portfolio_position_mutation_allowed": False,
            "automatic_rebalance_allowed": False,
            "recommendation_scoring_mutated": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "order_boundary": ORDER_BOUNDARY,
        },
        **{key: False for key in HARD_FALSE_PERMISSION_KEYS},
        "order_boundary": ORDER_BOUNDARY,
        "next_action": _next_action(status),
    }


def _append_identity_blocker(
    blockers: list[dict[str, object]],
    identity: dict[str, object],
    expected_sha: str,
) -> None:
    if identity.get("complete") is not True:
        blockers.append(
            _blocker(
                "database_identity_incomplete",
                "Target database identity or required relations are incomplete.",
                category="incomplete",
                missing_identity_fields=identity.get("missing_identity_fields"),
                missing_required_relations=identity.get("missing_required_relations"),
            )
        )
    elif identity.get("sha256") != expected_sha:
        blockers.append(
            _blocker(
                "database_identity_mismatch",
                "Observed database identity SHA-256 differs from the expected target.",
                category="environment",
                expected_sha256=expected_sha,
                observed_sha256=identity.get("sha256"),
            )
        )


def _append_source_blocker(
    blockers: list[dict[str, object]],
    source_name: str,
    expected_id: int,
    actual_id: int | None,
) -> None:
    if actual_id is None:
        blockers.append(
            _blocker(
                f"{source_name}_exact_source_missing",
                f"Exact {source_name} eval artifact is missing.",
                category="incomplete",
                expected_eval_run_id=expected_id,
            )
        )
    elif actual_id != expected_id:
        blockers.append(
            _blocker(
                f"{source_name}_exact_source_mismatch",
                f"Resolved {source_name} eval ID differs from the requested exact ID.",
                category="incoherent",
                expected_eval_run_id=expected_id,
                observed_eval_run_id=actual_id,
            )
        )


def _resolve_status(
    foundation_status: str,
    blockers: list[dict[str, object]],
) -> str:
    categories = {str(item.get("category") or "") for item in blockers}
    if "environment" in categories:
        return "live_observation_blocked_environment_mismatch"
    if "incomplete" in categories or foundation_status == "foundation_incomplete_fail_closed":
        return "live_observation_incomplete_fail_closed"
    if blockers or foundation_status == "foundation_incoherent_fail_closed":
        return "live_observation_incoherent_fail_closed"
    if foundation_status == "foundation_complete_fresh_read_only":
        return "live_observation_complete_fresh_read_only"
    if foundation_status == "foundation_complete_stale_read_only":
        return "live_observation_complete_stale_read_only"
    blockers.append(
        _blocker(
            "foundation_status_unrecognized",
            "Foundation status is not a recognized fail-closed state.",
            category="incoherent",
            foundation_status=foundation_status or None,
        )
    )
    return "live_observation_incoherent_fail_closed"


def _source_score_identity(wrapper: dict[str, object]) -> dict[str, object]:
    return {
        "eval_run_id": _positive_int(wrapper.get("eval_run_id")),
        "eval_name": _optional_text(wrapper.get("eval_name")),
        "dataset_version": _optional_text(wrapper.get("dataset_version")),
        "provider": _optional_text(wrapper.get("provider")),
        "model_name": _optional_text(wrapper.get("model_name")),
        "created_at": _optional_text(wrapper.get("created_at")),
        "score_sha256": _canonical_hash(_as_dict(wrapper.get("score_json"))),
    }


def _source_eval_run_ids(source_scores: dict[str, object]) -> list[int]:
    rows = [
        _as_dict(source_scores.get(key))
        for key in (
            "lineage",
            "referenced_quality",
            "referenced_outcome",
            "feedback_calibration",
        )
    ] + _as_list(source_scores.get("feedback_artifacts"))
    return sorted(
        {
            value
            for row in rows
            if (value := _positive_int(row.get("eval_run_id"))) is not None
        }
    )


def _canonical_rows(value: object) -> list[dict[str, object]]:
    rows = [item for item in (_canonical_copy(row) for row in _as_list(value)) if isinstance(item, dict)]
    return sorted(
        rows,
        key=lambda item: json.dumps(
            item, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
        ),
    )


def _first_int(value: dict[str, object], *keys: str) -> int:
    for key in keys:
        parsed = _optional_int(value.get(key))
        if parsed is not None:
            return parsed
    return 0


def _snapshot_sha(value: dict[str, object] | None) -> str:
    if not isinstance(value, dict):
        raise ValueError("legacy surface snapshot must be a JSON object.")
    return validate_sha256(
        str(value.get("payload_sha256") or ""),
        field_name="legacy_surface.payload_sha256",
    )


def _text(value: object) -> str:
    return str(value or "").strip()


def _optional_text(value: object) -> str | None:
    return _text(value) or None


def _optional_int(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _next_action(status: str) -> str:
    return {
        "live_observation_complete_fresh_read_only": (
            "Review the append-only observation in a separate policy packet; do not start a pilot."
        ),
        "live_observation_complete_stale_read_only": (
            "Refresh stale exact sources and rerun; staleness never authorizes a pilot."
        ),
        "live_observation_blocked_environment_mismatch": (
            "Verify the intended PostgreSQL fingerprint before any append-only write."
        ),
        "live_observation_incomplete_fail_closed": (
            "Resolve missing relations or exact sources without rewriting historical evidence."
        ),
    }.get(
        status,
        "Resolve source or legacy-surface inconsistencies and rerun the read-only preflight.",
    )
