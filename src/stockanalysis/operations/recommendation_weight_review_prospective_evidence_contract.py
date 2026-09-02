from __future__ import annotations

import hashlib
import json
from collections import Counter
from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation


DEFAULT_EVAL_NAME = "recommendation_weight_review_prospective_evidence_foundation_v1"
DEFAULT_DATASET_VERSION = "recommendation-weight-review-prospective-evidence-foundation-v1"
DEFAULT_PIPELINE_NAME = "recommendation_weight_review_prospective_evidence_foundation_v1"
DEFAULT_PROVIDER = "postgres"
DEFAULT_MODEL_NAME = "deterministic-prospective-evidence-v1"
DEFAULT_PORTFOLIO_NAME = "Long Term Paper"

SOURCE_LINEAGE_EVAL_NAME = "recommendation_weight_review_source_lineage_reconciliation_v1"
SOURCE_LINEAGE_DATASET_VERSION = "recommendation-weight-review-source-lineage-reconciliation-v1"
SOURCE_QUALITY_EVAL_NAME = "recommendation_quality_calibration"
SOURCE_QUALITY_DATASET_VERSION = "recommendation-quality-live-v1"
SOURCE_OUTCOME_EVAL_NAME = "recommendation_outcome_calibration_sample_expansion"
SOURCE_OUTCOME_DATASET_VERSION = "recommendation-outcome-calibration-sample-expansion-v1"
SOURCE_FEEDBACK_CALIBRATION_EVAL_NAME = "portfolio_review_feedback_calibration"
SOURCE_FEEDBACK_CALIBRATION_DATASET_VERSION = "portfolio-review-feedback-calibration-v1"
SOURCE_FEEDBACK_EVAL_NAME = "portfolio_review_decision_outcome_feedback"
SOURCE_FEEDBACK_DATASET_VERSION = "portfolio-review-decision-outcome-feedback-v1"

RECOMMENDATION_ROW_IDENTITY_CONTRACT_VERSION = "recommendation-row-identity-v1"
COMPONENT_SNAPSHOT_CONTRACT_VERSION = "recommendation-component-snapshot-v1"
OUTCOME_OBSERVATION_CONTRACT_VERSION = "recommendation-outcome-observation-v1"
FEEDBACK_DEDUPLICATION_CONTRACT_VERSION = "portfolio-feedback-deduplication-v1"
COHORT_SNAPSHOT_CONTRACT_VERSION = "recommendation-cohort-snapshot-v1"
FRESHNESS_POLICY_VERSION = "recommendation-weight-review-conservative-freshness-v1"
ORDER_BOUNDARY = "read_only_no_order"

COHORT_FILTER_KEYS = (
    "market_code",
    "strategy_name",
    "horizon_type",
    "universe_version",
)
FRESHNESS_MAX_AGE_DAYS = {
    "lineage_reconciliation": 14,
    "referenced_quality": 31,
    "referenced_outcome": 31,
    "portfolio_feedback_calibration": 31,
    "referenced_feedback_run": 31,
}


def _build_freshness_evaluation(
    *,
    as_of_date: date,
    lineage_wrapper: dict[str, object],
    quality_wrapper: dict[str, object],
    outcome_wrapper: dict[str, object],
    feedback_calibration_wrapper: dict[str, object],
    feedback_artifacts: list[dict[str, object]],
) -> dict[str, object]:
    policy_payload = {
        "version": FRESHNESS_POLICY_VERSION,
        "max_age_days": dict(sorted(FRESHNESS_MAX_AGE_DAYS.items())),
        "future_tolerance_days": 0,
        "approval_status": "candidate_not_approved",
        "rejection_only": True,
    }
    observations: list[dict[str, object]] = []
    observations.append(
        _freshness_observation(
            as_of_date=as_of_date,
            source_role="lineage_reconciliation",
            source_id=_positive_int(lineage_wrapper.get("eval_run_id")),
            effective_date=_parse_date(str(lineage_wrapper.get("created_at") or "")),
        )
    )
    observations.append(
        _freshness_observation(
            as_of_date=as_of_date,
            source_role="referenced_quality",
            source_id=_positive_int(quality_wrapper.get("eval_run_id")),
            effective_date=_parse_date(
                str(_as_dict(quality_wrapper.get("score_json")).get("as_of_date") or "")
            ),
        )
    )
    observations.append(
        _freshness_observation(
            as_of_date=as_of_date,
            source_role="referenced_outcome",
            source_id=_positive_int(outcome_wrapper.get("eval_run_id")),
            effective_date=_parse_date(
                str(_as_dict(outcome_wrapper.get("score_json")).get("as_of_date") or "")
            ),
        )
    )
    observations.append(
        _freshness_observation(
            as_of_date=as_of_date,
            source_role="portfolio_feedback_calibration",
            source_id=_positive_int(feedback_calibration_wrapper.get("eval_run_id")),
            effective_date=_parse_date(
                str(
                    _as_dict(feedback_calibration_wrapper.get("score_json")).get(
                        "as_of_date"
                    )
                    or ""
                )
            ),
        )
    )
    for artifact in feedback_artifacts:
        source = _as_dict(artifact.get("source"))
        observations.append(
            _freshness_observation(
                as_of_date=as_of_date,
                source_role="referenced_feedback_run",
                source_id=_positive_int(source.get("eval_run_id")),
                effective_date=_parse_date(str(source.get("score_as_of_date") or "")),
            )
        )

    status_counts = Counter(str(item["status"]) for item in observations)
    candidate_policy_passed = bool(observations) and all(
        item["status"] == "fresh" for item in observations
    )
    return {
        "policy": {
            **policy_payload,
            "sha256": _canonical_hash(policy_payload),
            "defined": True,
            "approved": False,
            "approval_reference": None,
        },
        "observations": observations,
        "status_counts": dict(sorted(status_counts.items())),
        "candidate_policy_passed": candidate_policy_passed,
        "stale_source_count": status_counts.get("stale", 0),
        "missing_source_date_count": status_counts.get("missing", 0),
        "future_source_count": status_counts.get("future", 0),
        "freshness_policy_attested": False,
        "limitation": (
            "The conservative policy is defined and evaluated but is not an "
            "approved eligibility or pilot policy."
        ),
    }


def _freshness_observation(
    *,
    as_of_date: date,
    source_role: str,
    source_id: int | None,
    effective_date: date | None,
) -> dict[str, object]:
    max_age_days = FRESHNESS_MAX_AGE_DAYS[source_role]
    if effective_date is None:
        status = "missing"
        age_days = None
    else:
        age_days = (as_of_date - effective_date).days
        if age_days < 0:
            status = "future"
        elif age_days > max_age_days:
            status = "stale"
        else:
            status = "fresh"
    return {
        "source_role": source_role,
        "source_id": source_id,
        "effective_date": effective_date.isoformat() if effective_date else None,
        "age_days": age_days,
        "max_age_days": max_age_days,
        "status": status,
    }


def _validate_lineage_anchor(
    *,
    lineage_score: dict[str, object],
    quality_eval_run_id: int | None,
    outcome_eval_run_id: int | None,
    blockers: list[dict[str, object]],
) -> None:
    if str(lineage_score.get("status") or "") != "reconciled_read_only":
        blockers.append(
            _blocker(
                "lineage_not_reconciled",
                "Selected lineage artifact is not reconciled_read_only.",
                category="incoherent",
            )
        )
    if lineage_score.get("lineage_reconciled") is not True:
        blockers.append(
            _blocker(
                "lineage_reconciled_flag_missing",
                "Selected lineage artifact does not attest lineage_reconciled=true.",
                category="incomplete",
            )
        )
    canonical_chain = _as_dict(lineage_score.get("canonical_chain"))
    chain_sha = str(canonical_chain.get("sha256") or "")
    if not _is_sha256(chain_sha):
        blockers.append(
            _blocker(
                "lineage_canonical_chain_hash_missing",
                "Lineage canonical-chain SHA-256 is missing or invalid.",
                category="incomplete",
            )
        )
    else:
        chain_payload = {
            key: _canonical_copy(value)
            for key, value in canonical_chain.items()
            if key != "sha256"
        }
        if _canonical_hash(chain_payload) != chain_sha:
            blockers.append(
                _blocker(
                    "lineage_canonical_chain_hash_mismatch",
                    "Lineage canonical-chain payload does not match its SHA-256.",
                    category="incoherent",
                )
            )
    expected_quality_id = _positive_int(
        _as_dict(canonical_chain.get("quality")).get("eval_run_id")
    )
    expected_outcome_id = _positive_int(
        _as_dict(canonical_chain.get("outcome")).get("eval_run_id")
    )
    for code, label, actual, expected in (
        (
            "lineage_quality_reference_mismatch",
            "quality",
            quality_eval_run_id,
            expected_quality_id,
        ),
        (
            "lineage_outcome_reference_mismatch",
            "outcome",
            outcome_eval_run_id,
            expected_outcome_id,
        ),
    ):
        if expected is None:
            blockers.append(
                _blocker(
                    f"{code}_expected_missing",
                    f"Lineage {label} reference is missing.",
                    category="incomplete",
                )
            )
        elif actual != expected:
            blockers.append(
                _blocker(
                    code,
                    f"Resolved {label} eval ID differs from the lineage anchor.",
                    category="incoherent",
                    actual=actual,
                    expected=expected,
                )
            )


def _validate_cohort_filters(
    lineage_score: dict[str, object],
    blockers: list[dict[str, object]],
) -> dict[str, object]:
    filters = _as_dict(
        _as_dict(lineage_score.get("cohort_filter_identity")).get(
            "required_filters"
        )
    )
    normalized: dict[str, object] = {}
    for key in COHORT_FILTER_KEYS:
        value = filters.get(key)
        if value in (None, ""):
            blockers.append(
                _blocker(
                    f"cohort_filter_{key}_missing",
                    f"Canonical cohort filter {key} is missing.",
                    category="incomplete",
                )
            )
        else:
            normalized[key] = _canonical_copy(value)
    return normalized


def _validate_feedback_calibration_scope(
    score: dict[str, object],
    *,
    portfolio_name: str,
    blockers: list[dict[str, object]],
) -> None:
    actual_portfolio = str(score.get("portfolio_name") or "")
    if not actual_portfolio:
        blockers.append(
            _blocker(
                "feedback_calibration_portfolio_missing",
                "Feedback calibration portfolio_name is missing.",
                category="incomplete",
            )
        )
    elif actual_portfolio != portfolio_name:
        blockers.append(
            _blocker(
                "feedback_calibration_portfolio_mismatch",
                "Feedback calibration is scoped to a different portfolio.",
                category="incoherent",
            )
        )


def _normalize_required_source(
    wrapper: dict[str, object],
    *,
    source_key: str,
    expected_eval_name: str,
    expected_dataset_version: str,
    as_of_date: date,
    score_date_required: bool,
    blockers: list[dict[str, object]],
    blocker_suffix: str | None = None,
) -> dict[str, object]:
    suffix = f"_{blocker_suffix}" if blocker_suffix else ""
    eval_run_id = _positive_int(wrapper.get("eval_run_id"))
    eval_name = str(wrapper.get("eval_name") or "")
    dataset_version = str(wrapper.get("dataset_version") or "")
    score = _as_dict(wrapper.get("score_json"))
    created_at_text = str(wrapper.get("created_at") or "")
    created_date = _parse_date(created_at_text)
    score_date_text = str(score.get("as_of_date") or "")
    score_date = _parse_date(score_date_text)

    if not wrapper:
        blockers.append(
            _blocker(
                f"{source_key}_source_missing{suffix}",
                "Required source artifact is missing.",
                category="incomplete",
            )
        )
    if eval_run_id is None:
        blockers.append(
            _blocker(
                f"{source_key}_eval_run_id_missing{suffix}",
                "Source eval_run_id is missing or invalid.",
                category="incomplete",
            )
        )
    if not eval_name:
        blockers.append(
            _blocker(
                f"{source_key}_eval_name_missing{suffix}",
                "Source eval_name is missing.",
                category="incomplete",
            )
        )
    elif eval_name != expected_eval_name:
        blockers.append(
            _blocker(
                f"{source_key}_eval_name_mismatch{suffix}",
                "Source eval_name does not match the required artifact.",
                category="incoherent",
            )
        )
    if not dataset_version:
        blockers.append(
            _blocker(
                f"{source_key}_dataset_version_missing{suffix}",
                "Source dataset_version is missing.",
                category="incomplete",
            )
        )
    elif dataset_version != expected_dataset_version:
        blockers.append(
            _blocker(
                f"{source_key}_dataset_version_mismatch{suffix}",
                "Source dataset_version does not match the required artifact.",
                category="incoherent",
            )
        )
    if not score:
        blockers.append(
            _blocker(
                f"{source_key}_score_missing{suffix}",
                "Source score_json is missing or empty.",
                category="incomplete",
            )
        )
    if not created_at_text:
        blockers.append(
            _blocker(
                f"{source_key}_created_at_missing{suffix}",
                "Source created_at is missing.",
                category="incomplete",
            )
        )
    elif created_date is None:
        blockers.append(
            _blocker(
                f"{source_key}_created_at_invalid{suffix}",
                "Source created_at is invalid.",
                category="incoherent",
            )
        )
    elif created_date > as_of_date:
        blockers.append(
            _blocker(
                f"{source_key}_created_after_as_of{suffix}",
                "Source was created after the audit date.",
                category="incoherent",
            )
        )
    if score_date_required:
        if not score_date_text:
            blockers.append(
                _blocker(
                    f"{source_key}_score_date_missing{suffix}",
                    "Source score as_of_date is missing.",
                    category="incomplete",
                )
            )
        elif score_date is None:
            blockers.append(
                _blocker(
                    f"{source_key}_score_date_invalid{suffix}",
                    "Source score as_of_date is invalid.",
                    category="incoherent",
                )
            )
        elif score_date > as_of_date:
            blockers.append(
                _blocker(
                    f"{source_key}_score_after_as_of{suffix}",
                    "Source score is dated after the audit date.",
                    category="incoherent",
                )
            )

    return {
        "eval_run_id": eval_run_id,
        "eval_name": eval_name or None,
        "dataset_version": dataset_version or None,
        "provider": wrapper.get("provider"),
        "model_name": wrapper.get("model_name"),
        "score_as_of_date": score_date_text or None,
        "created_at": created_at_text or None,
        "score_sha256": _canonical_hash(score),
    }


def _blocker(
    code: str,
    message: str,
    *,
    category: str,
    **details: object,
) -> dict[str, object]:
    result: dict[str, object] = {
        "code": code,
        "message": message,
        "category": category,
    }
    if details:
        result["details"] = details
    return result


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _positive_int(value: object) -> int | None:
    parsed = _non_negative_int(value)
    return parsed if parsed is not None and parsed > 0 else None


def _non_negative_int(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _strict_positive_int_list(value: object) -> list[int]:
    if not isinstance(value, list):
        return []
    result: list[int] = []
    for item in value:
        parsed = _positive_int(item)
        if parsed is not None:
            result.append(parsed)
    return result


def _parse_date(value: str) -> date | None:
    text = value.strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        pass
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc)
    return parsed.date()


def _optional_date_text(value: object) -> str | None:
    parsed = _parse_date(str(value or ""))
    return parsed.isoformat() if parsed is not None else None


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _canonical_decimal_text(
    value: object,
    *,
    allow_none: bool = False,
) -> str | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None if allow_none else None
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    if not decimal_value.is_finite():
        return None
    normalized = decimal_value.normalize()
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in {"-0", ""}:
        return "0"
    return text


def _decimal_between_zero_and_one(value: str) -> bool:
    try:
        decimal_value = Decimal(value)
    except InvalidOperation:
        return False
    return Decimal("0") <= decimal_value <= Decimal("1")


def _canonical_hash(value: object) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _canonical_copy(value: object) -> object:
    try:
        return json.loads(
            json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        )
    except (TypeError, ValueError):
        return deepcopy(value)


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)
