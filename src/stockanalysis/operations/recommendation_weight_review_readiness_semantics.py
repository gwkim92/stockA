from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import date, datetime, timezone

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_EVAL_NAME = "recommendation_weight_review_readiness_semantics_v2"
DEFAULT_DATASET_VERSION = "recommendation-weight-review-readiness-semantics-v2"
DEFAULT_PIPELINE_NAME = "recommendation_weight_review_readiness_semantics_v2"
DEFAULT_PROVIDER = "postgres"
DEFAULT_MODEL_NAME = "deterministic-readiness-semantics-v2"

SOURCE_READINESS_EVAL_NAME = "recommendation_weight_review_readiness_audit"
SOURCE_READINESS_DATASET_VERSION = "recommendation-weight-review-readiness-v1"
SOURCE_QUALITY_EVAL_NAME = "recommendation_quality_calibration"
SOURCE_QUALITY_DATASET_VERSION = "recommendation-quality-live-v1"
SOURCE_OUTCOME_EVAL_NAME = "recommendation_outcome_calibration_sample_expansion"
SOURCE_OUTCOME_DATASET_VERSION = "recommendation-outcome-calibration-sample-expansion-v1"
SOURCE_PORTFOLIO_FEEDBACK_EVAL_NAME = "portfolio_review_feedback_calibration"
SOURCE_PORTFOLIO_FEEDBACK_DATASET_VERSION = "portfolio-review-feedback-calibration-v1"

LEGACY_READINESS_DECISION = "ready_for_manual_weight_review"
LEGACY_QUALITY_READY_STATUS = "ready_for_weight_review"
LEGACY_OUTCOME_READY_STATUS = "ready_for_manual_weight_review"
LEGACY_PORTFOLIO_FEEDBACK_READY_STATUS = "manual_review_ready"
ORDER_BOUNDARY = "read_only_no_order"
DEFAULT_PORTFOLIO_NAME = "Long Term Paper"
COHORT_FILTER_KEYS = (
    "market_code",
    "strategy_name",
    "horizon_type",
    "universe_version",
)


def render_readiness_audit_eval_lookup_sql(
    *,
    as_of_date: date,
    eval_run_id: int | None = None,
) -> str:
    return _render_eval_lookup_sql(
        comment="recommendation weight review readiness semantics v2 readiness audit lookup",
        as_of_date=as_of_date,
        eval_name=SOURCE_READINESS_EVAL_NAME,
        dataset_version=SOURCE_READINESS_DATASET_VERSION,
        eval_run_id=eval_run_id,
        score_date_required=False,
    )


def render_quality_eval_lookup_sql(
    *,
    as_of_date: date,
    eval_run_id: int | None = None,
) -> str:
    return _render_eval_lookup_sql(
        comment="recommendation weight review readiness semantics v2 quality eval lookup",
        as_of_date=as_of_date,
        eval_name=SOURCE_QUALITY_EVAL_NAME,
        dataset_version=SOURCE_QUALITY_DATASET_VERSION,
        eval_run_id=eval_run_id,
        score_date_required=True,
    )


def render_outcome_calibration_eval_lookup_sql(
    *,
    as_of_date: date,
    eval_run_id: int | None = None,
) -> str:
    return _render_eval_lookup_sql(
        comment="recommendation weight review readiness semantics v2 outcome calibration lookup",
        as_of_date=as_of_date,
        eval_name=SOURCE_OUTCOME_EVAL_NAME,
        dataset_version=SOURCE_OUTCOME_DATASET_VERSION,
        eval_run_id=eval_run_id,
        score_date_required=True,
    )


def render_portfolio_feedback_eval_lookup_sql(
    *,
    as_of_date: date,
    eval_run_id: int | None = None,
) -> str:
    return _render_eval_lookup_sql(
        comment="recommendation weight review readiness semantics v2 portfolio feedback lookup",
        as_of_date=as_of_date,
        eval_name=SOURCE_PORTFOLIO_FEEDBACK_EVAL_NAME,
        dataset_version=SOURCE_PORTFOLIO_FEEDBACK_DATASET_VERSION,
        eval_run_id=eval_run_id,
        score_date_required=True,
        additional_filter=(
            "\n      and score_json->>'portfolio_name' = "
            f"{sql_literal(DEFAULT_PORTFOLIO_NAME)}"
        ),
    )


def render_readiness_semantics_eval_insert_sql(*, score_json: dict[str, object]) -> str:
    score_text = json.dumps(score_json, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"""insert into ai.eval_run (
    eval_name,
    dataset_version,
    provider,
    model_name,
    score_json
)
values (
    {sql_literal(DEFAULT_EVAL_NAME)},
    {sql_literal(DEFAULT_DATASET_VERSION)},
    {sql_literal(DEFAULT_PROVIDER)},
    {sql_literal(DEFAULT_MODEL_NAME)},
    {sql_literal(score_text)}::jsonb
)
returning eval_run_id;"""


def load_readiness_audit_eval(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    eval_run_id: int | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    return _load_eval(
        config=config,
        sql=render_readiness_audit_eval_lookup_sql(
            as_of_date=as_of_date,
            eval_run_id=eval_run_id,
        ),
        source_label="readiness audit",
        executor=executor,
    )


def load_quality_eval(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    eval_run_id: int | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    return _load_eval(
        config=config,
        sql=render_quality_eval_lookup_sql(as_of_date=as_of_date, eval_run_id=eval_run_id),
        source_label="quality eval",
        executor=executor,
    )


def load_outcome_calibration_eval(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    eval_run_id: int | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    return _load_eval(
        config=config,
        sql=render_outcome_calibration_eval_lookup_sql(
            as_of_date=as_of_date,
            eval_run_id=eval_run_id,
        ),
        source_label="outcome calibration eval",
        executor=executor,
    )


def load_portfolio_feedback_eval(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    eval_run_id: int | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    return _load_eval(
        config=config,
        sql=render_portfolio_feedback_eval_lookup_sql(
            as_of_date=as_of_date,
            eval_run_id=eval_run_id,
        ),
        source_label="portfolio feedback eval",
        executor=executor,
    )


def build_recommendation_weight_review_readiness_semantics_v2(
    *,
    as_of_date: date,
    readiness_eval: dict[str, object],
    quality_eval: dict[str, object],
    outcome_eval: dict[str, object],
    portfolio_feedback_eval: dict[str, object],
) -> dict[str, object]:
    """Build a non-authoritative, fail-closed semantic snapshot of legacy evidence.

    The result deliberately separates threshold evidence, read-only review eligibility,
    user authorization, pilot state, and mutation authority.  It is an audit artifact;
    none of its booleans can authorize a scoring or trading action.
    """

    sources = {
        "readiness": _normalize_source(
            readiness_eval,
            source_key="readiness",
            expected_eval_name=SOURCE_READINESS_EVAL_NAME,
            expected_dataset_version=SOURCE_READINESS_DATASET_VERSION,
            as_of_date=as_of_date,
            score_date_required=False,
        ),
        "quality": _normalize_source(
            quality_eval,
            source_key="quality",
            expected_eval_name=SOURCE_QUALITY_EVAL_NAME,
            expected_dataset_version=SOURCE_QUALITY_DATASET_VERSION,
            as_of_date=as_of_date,
            score_date_required=True,
        ),
        "outcome": _normalize_source(
            outcome_eval,
            source_key="outcome",
            expected_eval_name=SOURCE_OUTCOME_EVAL_NAME,
            expected_dataset_version=SOURCE_OUTCOME_DATASET_VERSION,
            as_of_date=as_of_date,
            score_date_required=True,
        ),
        "portfolio_feedback": _normalize_source(
            portfolio_feedback_eval,
            source_key="portfolio_feedback",
            expected_eval_name=SOURCE_PORTFOLIO_FEEDBACK_EVAL_NAME,
            expected_dataset_version=SOURCE_PORTFOLIO_FEEDBACK_DATASET_VERSION,
            as_of_date=as_of_date,
            score_date_required=True,
        ),
    }

    readiness_score = _as_dict(readiness_eval.get("score_json"))
    quality_score = _as_dict(quality_eval.get("score_json"))
    outcome_score = _as_dict(outcome_eval.get("score_json"))
    portfolio_feedback_score = _as_dict(portfolio_feedback_eval.get("score_json"))

    blockers: list[dict[str, object]] = []
    for source in sources.values():
        blockers.extend(_as_blocker_list(source.pop("validation_blockers", [])))

    readiness_eval_id = _positive_int(readiness_eval.get("eval_run_id"))
    quality_eval_id = _positive_int(quality_eval.get("eval_run_id"))
    outcome_eval_id = _positive_int(outcome_eval.get("eval_run_id"))

    quality_counts = _validate_quality_counts(quality_score, blockers)
    portfolio_feedback_counts = _validate_portfolio_feedback_counts(
        portfolio_feedback_score,
        blockers,
    )
    portfolio_name = str(portfolio_feedback_score.get("portfolio_name") or "")
    if portfolio_name != DEFAULT_PORTFOLIO_NAME:
        blockers.append(
            _blocker(
                "portfolio_feedback_scope_mismatch",
                "Portfolio feedback evidence is not scoped to the required paper portfolio.",
            )
        )

    _require_equal(
        blockers,
        code="readiness_quality_eval_reference_mismatch",
        message="Legacy readiness source_eval_run_id does not identify the selected quality eval.",
        actual=_positive_int(readiness_score.get("source_eval_run_id")),
        expected=quality_eval_id,
    )
    outcome_gate = _as_dict(readiness_score.get("outcome_calibration_gate"))
    _require_equal(
        blockers,
        code="readiness_outcome_eval_reference_mismatch",
        message="Legacy readiness outcome gate does not identify the selected outcome calibration eval.",
        actual=_positive_int(outcome_gate.get("eval_run_id")),
        expected=outcome_eval_id,
    )
    _require_equal(
        blockers,
        code="readiness_quality_status_mismatch",
        message="Legacy readiness and quality artifacts report different quality statuses.",
        actual=str(readiness_score.get("source_quality_status") or "unknown"),
        expected=str(quality_score.get("quality_status") or "unknown"),
    )
    _require_equal(
        blockers,
        code="readiness_outcome_status_mismatch",
        message="Legacy readiness and outcome artifacts report different calibration statuses.",
        actual=str(outcome_gate.get("status") or "missing"),
        expected=str(outcome_score.get("status") or "missing"),
    )

    nested_quality = _as_dict(outcome_score.get("quality_eval_score"))
    if not nested_quality:
        blockers.append(
            _blocker(
                "outcome_nested_quality_missing",
                "Outcome calibration does not contain its canonical nested quality score.",
            )
        )
    elif _canonical_hash(nested_quality) != _canonical_hash(quality_score):
        blockers.append(
            _blocker(
                "outcome_nested_quality_mismatch",
                "Outcome calibration nested quality content differs from the selected quality eval.",
            )
        )

    legacy_allowed = readiness_score.get("manual_weight_review_allowed") is True
    readiness_decision = str(readiness_score.get("decision") or "missing")
    if legacy_allowed != (readiness_decision == LEGACY_READINESS_DECISION):
        blockers.append(
            _blocker(
                "legacy_readiness_boolean_decision_mismatch",
                "Legacy manual_weight_review_allowed and readiness decision are internally inconsistent.",
            )
        )

    horizon_evidence, horizon_blockers = _build_horizon_evidence(outcome_score)
    blockers.extend(horizon_blockers)
    sample_identity = _build_sample_identity(
        quality_score=quality_score,
        outcome_score=outcome_score,
        portfolio_feedback_score=portfolio_feedback_score,
        sources=sources,
        as_of_date=as_of_date,
    )
    source_chain_sha256 = _canonical_hash(
        {
            key: {
                "eval_run_id": source.get("eval_run_id"),
                "eval_name": source.get("eval_name"),
                "dataset_version": source.get("dataset_version"),
                "score_as_of_date": source.get("score_as_of_date"),
                "created_at": source.get("created_at"),
                "score_sha256": source.get("score_sha256"),
            }
            for key, source in sources.items()
        }
    )

    quality_ready = str(quality_score.get("quality_status") or "unknown") == LEGACY_QUALITY_READY_STATUS
    outcome_ready = str(outcome_score.get("status") or "missing") == LEGACY_OUTCOME_READY_STATUS
    readiness_ready = legacy_allowed and readiness_decision == LEGACY_READINESS_DECISION
    feedback_status = str(portfolio_feedback_score.get("calibration_status") or "missing")
    portfolio_feedback_ready = feedback_status == LEGACY_PORTFOLIO_FEEDBACK_READY_STATUS
    source_coherent = not blockers
    threshold_evidence_ready = source_coherent and readiness_ready and quality_ready and outcome_ready
    legacy_integrity_attested = (
        all(
            sample_identity.get(key) is True
            for key in (
                "stable_row_level_sample_identity_attested",
                "feedback_deduplication_attested",
                "versioned_component_snapshot_integrity_attested",
                "freshness_policy_attested",
            )
        )
        and horizon_evidence.get("approved_horizon_policy_attested") is True
    )
    read_only_review_eligible = (
        threshold_evidence_ready
        and portfolio_feedback_ready
        and legacy_integrity_attested
    )

    if blockers:
        evidence_status = "incoherent_fail_closed"
        decision = "evidence_incoherent_fail_closed"
    elif not threshold_evidence_ready:
        evidence_status = "thresholds_not_met"
        decision = "read_only_manual_review_not_eligible"
    elif not portfolio_feedback_ready:
        evidence_status = "coherent_thresholds_met"
        decision = "wait_for_portfolio_feedback"
    elif not legacy_integrity_attested:
        evidence_status = "coherent_thresholds_met_integrity_not_attested"
        decision = "legacy_thresholds_met_integrity_not_attested"
    else:
        evidence_status = "coherent_thresholds_met"
        decision = "eligible_for_read_only_manual_review_no_authorization"

    hard_false_permissions = {
        "pilot_scope_defined": False,
        "explicit_user_approval_present": False,
        "read_only_pilot_start_allowed": False,
        "proposal_generation_allowed": False,
        "weight_mutation_allowed": False,
        "automatic_weight_change_allowed": False,
        "portfolio_position_mutation_allowed": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
    }
    return {
        "eval_name": DEFAULT_EVAL_NAME,
        "dataset_version": DEFAULT_DATASET_VERSION,
        "as_of_date": as_of_date.isoformat(),
        "mode": "shadow_read_only",
        "authoritative": False,
        "decision": decision,
        "source_chain_sha256": source_chain_sha256,
        "source_snapshot": sources,
        "sample_identity": sample_identity,
        "horizon_evidence": horizon_evidence,
        "evidence_readiness": {
            "status": evidence_status,
            "source_coherent": source_coherent,
            "legacy_readiness_ready": readiness_ready,
            "quality_threshold_ready": quality_ready,
            "outcome_calibration_ready": outcome_ready,
            "threshold_evidence_ready": threshold_evidence_ready,
            "portfolio_feedback_ready": portfolio_feedback_ready,
            "legacy_integrity_attested": legacy_integrity_attested,
            "quality_counts": quality_counts,
            "portfolio_feedback_counts": portfolio_feedback_counts,
            "blockers": blockers,
        },
        "manual_review_eligibility": {
            "eligible": read_only_review_eligible,
            "scope": "read_only_human_evidence_review",
            "requires_source_coherence": True,
            "requires_legacy_readiness": True,
            "requires_portfolio_feedback": True,
            "requires_attested_sample_integrity": True,
            "requires_approved_horizon_policy": True,
            "reason": _eligibility_reason(
                source_coherent=source_coherent,
                threshold_evidence_ready=threshold_evidence_ready,
                portfolio_feedback_ready=portfolio_feedback_ready,
                legacy_integrity_attested=legacy_integrity_attested,
            ),
        },
        "explicit_user_authorization": {
            "status": "explicit_approval_required",
            "required": True,
            "present": False,
            "scope_defined": False,
            "approval_reference": None,
            "reason": "This shadow audit cannot record or infer scoped user approval.",
        },
        "pilot": {
            "status": "not_started_not_authorized",
            "pilot_scope_defined": False,
            "read_only_pilot_start_allowed": False,
            "proposal_generation_allowed": False,
            "started": False,
            "reason": "No pilot is authorized or started by this audit.",
        },
        "mutation_boundary": {
            "status": "blocked_read_only_shadow",
            "recommendation_scoring_mutated": False,
            "weight_mutation_allowed": False,
            "automatic_weight_change_allowed": False,
            "portfolio_position_mutation_allowed": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "order_boundary": ORDER_BOUNDARY,
        },
        "legacy_comparison": {
            "readiness_eval_run_id": readiness_eval_id,
            "readiness_decision": readiness_decision,
            "manual_weight_review_allowed": legacy_allowed,
            "quality_eval_run_id": quality_eval_id,
            "quality_status": str(quality_score.get("quality_status") or "unknown"),
            "outcome_eval_run_id": outcome_eval_id,
            "outcome_status": str(outcome_score.get("status") or "missing"),
            "portfolio_feedback_eval_run_id": _positive_int(portfolio_feedback_eval.get("eval_run_id")),
            "portfolio_feedback_status": feedback_status,
            "interpretation": "Legacy evidence readiness is not explicit authorization or mutation permission.",
        },
        **hard_false_permissions,
        "manual_review_eligible": read_only_review_eligible,
        "evidence_sufficient_for_pilot_request": False,
        "recommendation_scoring_mutated": False,
        "order_boundary": ORDER_BOUNDARY,
    }


def run_recommendation_weight_review_readiness_semantics_v2(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    readiness_eval_run_id: int | None = None,
    quality_eval_run_id: int | None = None,
    outcome_eval_run_id: int | None = None,
    portfolio_feedback_eval_run_id: int | None = None,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    readiness_eval = load_readiness_audit_eval(
        config=config,
        as_of_date=as_of_date,
        eval_run_id=readiness_eval_run_id,
        executor=sql_executor,
    )
    quality_eval = load_quality_eval(
        config=config,
        as_of_date=as_of_date,
        eval_run_id=quality_eval_run_id,
        executor=sql_executor,
    )
    outcome_eval = load_outcome_calibration_eval(
        config=config,
        as_of_date=as_of_date,
        eval_run_id=outcome_eval_run_id,
        executor=sql_executor,
    )
    portfolio_feedback_eval = load_portfolio_feedback_eval(
        config=config,
        as_of_date=as_of_date,
        eval_run_id=portfolio_feedback_eval_run_id,
        executor=sql_executor,
    )
    semantics = build_recommendation_weight_review_readiness_semantics_v2(
        as_of_date=as_of_date,
        readiness_eval=readiness_eval,
        quality_eval=quality_eval,
        outcome_eval=outcome_eval,
        portfolio_feedback_eval=portfolio_feedback_eval,
    )
    report: dict[str, object] = {
        "report_name": DEFAULT_EVAL_NAME,
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "mode": "shadow_read_only",
        "authoritative": False,
        "semantics": semantics,
    }
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "mode": "shadow_read_only",
            "authoritative": False,
            "decision": semantics["decision"],
            "readiness_eval_run_id": _positive_int(readiness_eval.get("eval_run_id")),
            "quality_eval_run_id": _positive_int(quality_eval.get("eval_run_id")),
            "outcome_eval_run_id": _positive_int(outcome_eval.get("eval_run_id")),
            "portfolio_feedback_eval_run_id": _positive_int(portfolio_feedback_eval.get("eval_run_id")),
            "explicit_user_approval_present": False,
            "proposal_generation_allowed": False,
            "weight_mutation_allowed": False,
            "automatic_weight_change_allowed": False,
            "portfolio_position_mutation_allowed": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "order_boundary": ORDER_BOUNDARY,
        },
    )
    try:
        eval_run_id = int(
            sql_executor.execute_scalar(
                render_readiness_semantics_eval_insert_sql(score_json=semantics)
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


def _render_eval_lookup_sql(
    *,
    comment: str,
    as_of_date: date,
    eval_name: str,
    dataset_version: str,
    eval_run_id: int | None,
    score_date_required: bool,
    additional_filter: str = "",
) -> str:
    eval_id_filter = ""
    if eval_run_id is not None:
        if eval_run_id <= 0:
            raise ValueError("eval_run_id must be greater than 0.")
        eval_id_filter = f"\n      and eval_run.eval_run_id = {eval_run_id}"
    score_date_filter = ""
    score_date_order = ""
    if score_date_required:
        score_date_filter = (
            "\n      and nullif(eval_run.score_json->>'as_of_date', '')::date"
            f" <= {sql_date(as_of_date)}"
        )
        score_date_order = "\n        nullif(eval_run.score_json->>'as_of_date', '')::date desc nulls last,"
    else:
        score_date_filter = (
            "\n      and (nullif(eval_run.score_json->>'as_of_date', '') is null"
            " or nullif(eval_run.score_json->>'as_of_date', '')::date"
            f" <= {sql_date(as_of_date)})"
        )
    return f"""-- {comment}
with selected_eval as (
    select
        eval_run.eval_run_id,
        eval_run.eval_name,
        eval_run.dataset_version,
        eval_run.provider,
        eval_run.model_name,
        eval_run.score_json,
        eval_run.created_at
    from ai.eval_run eval_run
    where eval_run.eval_name = {sql_literal(eval_name)}
      and eval_run.dataset_version = {sql_literal(dataset_version)}
      and eval_run.created_at::date <= {sql_date(as_of_date)}{score_date_filter}{additional_filter}{eval_id_filter}
    order by{score_date_order}
        eval_run.created_at desc,
        eval_run.eval_run_id desc
    limit 1
)
select coalesce(
    (
        select json_build_object(
            'eval_run_id', selected_eval.eval_run_id,
            'eval_name', selected_eval.eval_name,
            'dataset_version', selected_eval.dataset_version,
            'provider', selected_eval.provider,
            'model_name', selected_eval.model_name,
            'score_json', selected_eval.score_json,
            'created_at', selected_eval.created_at
        )
        from selected_eval
    ),
    '{{}}'::json
)::text;"""


def _load_eval(
    *,
    config: RuntimeConfig,
    sql: str,
    source_label: str,
    executor: PsqlCommandExecutor | None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(sql_executor.execute_scalar(sql))
    if not isinstance(payload, dict):
        raise ValueError(f"{source_label.title()} lookup did not return a JSON object.")
    # An absent source is evidence, not a transport error.  Returning the empty
    # object lets the pure builder record a durable fail-closed shadow artifact.
    return payload


def _normalize_source(
    value: dict[str, object],
    *,
    source_key: str,
    expected_eval_name: str,
    expected_dataset_version: str,
    as_of_date: date,
    score_date_required: bool,
) -> dict[str, object]:
    blockers: list[dict[str, object]] = []
    eval_run_id = _positive_int(value.get("eval_run_id"))
    eval_name = str(value.get("eval_name") or "")
    dataset_version = str(value.get("dataset_version") or "")
    score = _as_dict(value.get("score_json"))
    created_at_text = str(value.get("created_at") or "")
    created_date = _parse_date(created_at_text)
    score_date_text = str(score.get("as_of_date") or "")
    score_date = _parse_date(score_date_text)
    source_filters = _as_dict(score.get("filters"))
    if not source_filters:
        source_filters = _as_dict(_as_dict(score.get("sample_audit_after")).get("filters"))
    if source_key == "portfolio_feedback":
        source_filters = {"portfolio_name": score.get("portfolio_name")}
    legacy_status = _legacy_source_status(source_key, score)

    if not value:
        blockers.append(
            _blocker(
                f"{source_key}_source_missing",
                "Required source eval artifact is missing.",
            )
        )
    if eval_run_id is None:
        blockers.append(_blocker(f"{source_key}_eval_run_id_missing", "Source eval_run_id is missing or invalid."))
    if eval_name != expected_eval_name:
        blockers.append(
            _blocker(
                f"{source_key}_eval_name_mismatch",
                "Source eval_name does not match the required artifact.",
            )
        )
    if dataset_version != expected_dataset_version:
        blockers.append(
            _blocker(
                f"{source_key}_dataset_version_mismatch",
                "Source dataset_version does not match the required artifact.",
            )
        )
    if not score:
        blockers.append(_blocker(f"{source_key}_score_missing", "Source score_json is missing or empty."))
    if created_date is None:
        blockers.append(_blocker(f"{source_key}_created_at_invalid", "Source created_at is missing or invalid."))
    elif created_date > as_of_date:
        blockers.append(_blocker(f"{source_key}_created_after_as_of", "Source was created after the audit as-of date."))
    if score_date_required and score_date is None:
        blockers.append(
            _blocker(
                f"{source_key}_score_date_invalid",
                "Source score as_of_date is missing or invalid.",
            )
        )
    elif score_date is not None and score_date > as_of_date:
        blockers.append(
            _blocker(
                f"{source_key}_score_after_as_of",
                "Source score is dated after the audit as-of date.",
            )
        )

    if (created_date is not None and created_date > as_of_date) or (
        score_date is not None and score_date > as_of_date
    ):
        blockers.append(
            _blocker(
                "future_source_evidence",
                f"{source_key} evidence is dated after the audit as-of date.",
            )
        )

    return {
        "eval_run_id": eval_run_id,
        "eval_name": eval_name or None,
        "dataset_version": dataset_version or None,
        "provider": value.get("provider"),
        "model_name": value.get("model_name"),
        "score_as_of_date": score_date_text or None,
        "created_at": created_at_text or None,
        "legacy_status": legacy_status,
        "source_filters": _canonical_copy(source_filters),
        "score_sha256": _canonical_hash(score),
        "validation_blockers": blockers,
    }


def _validate_quality_counts(
    quality_score: dict[str, object],
    blockers: list[dict[str, object]],
) -> dict[str, int | None]:
    fields = (
        "recommendation_count",
        "outcome_count",
        "positive_outcome_count",
    )
    counts = {key: _non_negative_int(quality_score.get(key)) for key in fields}
    for key, value in counts.items():
        if value is None:
            blockers.append(
                _blocker(
                    f"quality_{key}_invalid",
                    f"Quality {key} is required and must be a non-negative integer.",
                )
            )

    recommendation_count = counts["recommendation_count"]
    outcome_count = counts["outcome_count"]
    positive_outcome_count = counts["positive_outcome_count"]
    if (
        recommendation_count is not None
        and outcome_count is not None
        and outcome_count > recommendation_count
    ):
        blockers.append(
            _blocker(
                "quality_outcome_count_exceeds_recommendation_count",
                "Quality outcome_count cannot exceed recommendation_count.",
            )
        )
    if (
        outcome_count is not None
        and positive_outcome_count is not None
        and positive_outcome_count > outcome_count
    ):
        blockers.append(
            _blocker(
                "quality_positive_count_exceeds_outcome_count",
                "Quality positive_outcome_count cannot exceed outcome_count.",
            )
        )
    if str(quality_score.get("quality_status") or "") == LEGACY_QUALITY_READY_STATUS and (
        not recommendation_count or not outcome_count
    ):
        blockers.append(
            _blocker(
                "quality_ready_counts_empty",
                "A ready quality artifact must contain non-zero recommendation and outcome counts.",
            )
        )
    return counts


def _validate_portfolio_feedback_counts(
    portfolio_feedback_score: dict[str, object],
    blockers: list[dict[str, object]],
) -> dict[str, int | None]:
    fields = (
        "feedback_run_count",
        "decision_count",
        "mature_decision_count",
    )
    counts = {
        key: _non_negative_int(portfolio_feedback_score.get(key))
        for key in fields
    }
    invalid_codes = {
        "feedback_run_count": "portfolio_feedback_run_count_invalid",
        "decision_count": "portfolio_feedback_decision_count_invalid",
        "mature_decision_count": "portfolio_feedback_mature_decision_count_invalid",
    }
    for key, value in counts.items():
        if value is None:
            blockers.append(
                _blocker(
                    invalid_codes[key],
                    f"Portfolio feedback {key} is required and must be a non-negative integer.",
                )
            )

    decision_count = counts["decision_count"]
    mature_decision_count = counts["mature_decision_count"]
    if (
        decision_count is not None
        and mature_decision_count is not None
        and mature_decision_count > decision_count
    ):
        blockers.append(
            _blocker(
                "portfolio_feedback_mature_count_exceeds_decision_count",
                "Portfolio feedback mature_decision_count cannot exceed decision_count.",
            )
        )
    if (
        str(portfolio_feedback_score.get("calibration_status") or "")
        == LEGACY_PORTFOLIO_FEEDBACK_READY_STATUS
        and any(not counts[key] for key in fields)
    ):
        blockers.append(
            _blocker(
                "portfolio_feedback_ready_counts_empty",
                "A ready portfolio feedback artifact must contain non-zero run, decision, and mature-decision counts.",
            )
        )
    return counts


def _build_horizon_evidence(
    outcome_score: dict[str, object],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    blockers: list[dict[str, object]] = []
    declared_raw = outcome_score.get("horizon_days")
    declared = _strict_positive_int_list(declared_raw)
    if not declared or len(declared) != len(_as_raw_list(declared_raw)) or len(set(declared)) != len(declared):
        blockers.append(
            _blocker(
                "outcome_horizon_set_invalid",
                "Outcome calibration horizon_days must be a non-empty set of unique positive integers.",
            )
        )

    sample_after = _as_dict(outcome_score.get("sample_audit_after"))
    nested_horizons_raw = sample_after.get("horizon_days")
    nested_horizons = _strict_positive_int_list(nested_horizons_raw)
    raw_rows = _as_raw_list(sample_after.get("horizon_coverage"))
    rows = _as_list(sample_after.get("horizon_coverage"))
    if len(rows) != len(raw_rows):
        blockers.append(
            _blocker(
                "outcome_horizon_rows_invalid",
                "Every horizon coverage item must be an object.",
            )
        )
    row_horizons = [_positive_int(row.get("horizon_day")) for row in rows]
    valid_row_horizons = [item for item in row_horizons if item is not None]

    if declared != nested_horizons:
        blockers.append(
            _blocker(
                "outcome_nested_horizon_set_mismatch",
                "Outcome top-level and sample-audit horizon sets differ.",
            )
        )
    if sorted(declared) != sorted(valid_row_horizons) or len(valid_row_horizons) != len(rows):
        blockers.append(
            _blocker(
                "outcome_horizon_row_set_mismatch",
                "Horizon coverage rows do not exactly represent the declared horizon set.",
            )
        )

    score_date = str(outcome_score.get("as_of_date") or "")
    nested_score_date = str(sample_after.get("as_of_date") or "")
    if score_date != nested_score_date:
        blockers.append(
            _blocker(
                "outcome_nested_as_of_date_mismatch",
                "Outcome top-level and sample-audit as-of dates differ.",
            )
        )

    summary = _as_dict(sample_after.get("summary"))
    required_summary_keys = (
        "recommendation_horizon_count",
        "recommendation_count",
        "outcome_count",
        "ready_for_backfill_count",
        "not_due_count",
        "missing_entry_price_count",
        "missing_exit_price_count",
    )
    summary_counts: dict[str, int | None] = {}
    for key in required_summary_keys:
        summary_counts[key] = _non_negative_int(summary.get(key))
        if summary_counts[key] is None:
            blockers.append(
                _blocker(
                    f"outcome_{key}_missing_or_invalid",
                    f"Outcome summary {key} is required and must be a non-negative integer.",
                )
            )

    required_row_count_keys = (
        "recommendation_horizon_count",
        "outcome_count",
        "ready_for_backfill_count",
        "not_due_count",
        "price_gap_count",
    )
    parsed_rows: list[dict[str, int | None]] = []
    for index, row in enumerate(rows):
        parsed_row = {
            key: _non_negative_int(row.get(key))
            for key in required_row_count_keys
        }
        parsed_rows.append(parsed_row)
        for key, value in parsed_row.items():
            if value is None:
                blockers.append(
                    _blocker(
                        f"outcome_horizon_row_{key}_missing_or_invalid",
                        f"Horizon row {index} field {key} is required and must be non-negative.",
                    )
                )
        if all(value is not None for value in parsed_row.values()):
            recommendation_horizon_count = parsed_row["recommendation_horizon_count"]
            partition_count = sum(
                parsed_row[key] or 0
                for key in (
                    "outcome_count",
                    "ready_for_backfill_count",
                    "not_due_count",
                    "price_gap_count",
                )
            )
            if recommendation_horizon_count != partition_count:
                blockers.append(
                    _blocker(
                        "outcome_horizon_row_partition_mismatch",
                        "Each horizon row must partition every recommendation into exactly one outcome state.",
                    )
                )
            summary_recommendation_count = summary_counts.get("recommendation_count")
            if (
                summary_recommendation_count is not None
                and recommendation_horizon_count != summary_recommendation_count
            ):
                blockers.append(
                    _blocker(
                        "outcome_horizon_row_recommendation_count_mismatch",
                        "Each horizon row must represent the summary recommendation cohort exactly once.",
                    )
                )

    recommendation_count = summary_counts.get("recommendation_count")
    recommendation_horizon_count = summary_counts.get("recommendation_horizon_count")
    if recommendation_count is not None and recommendation_horizon_count is not None:
        expected_observation_count = recommendation_count * len(declared)
        if recommendation_horizon_count != expected_observation_count:
            blockers.append(
                _blocker(
                    "outcome_recommendation_horizon_shape_mismatch",
                    "Recommendation×horizon observations do not match recommendation_count times horizon count.",
                )
            )

    aggregate_pairs = (
        ("recommendation_horizon_count", "recommendation_horizon_count"),
        ("outcome_count", "outcome_count"),
        ("ready_for_backfill_count", "ready_for_backfill_count"),
        ("not_due_count", "not_due_count"),
    )
    for summary_key, row_key in aggregate_pairs:
        summary_value = summary_counts.get(summary_key)
        row_values = [row.get(row_key) for row in parsed_rows]
        if summary_value is not None and all(value is not None for value in row_values):
            row_value = sum(value or 0 for value in row_values)
        else:
            row_value = None
        if summary_value is None or row_value is None or summary_value != row_value:
            blockers.append(
                _blocker(
                    f"outcome_{summary_key}_aggregate_mismatch",
                    f"Outcome {summary_key} does not equal the preserved horizon-row aggregate.",
                )
            )
    missing_entry_count = summary_counts.get("missing_entry_price_count")
    missing_exit_count = summary_counts.get("missing_exit_price_count")
    row_price_gaps = [row.get("price_gap_count") for row in parsed_rows]
    price_gap_summary = (
        missing_entry_count + missing_exit_count
        if missing_entry_count is not None and missing_exit_count is not None
        else None
    )
    price_gap_rows = (
        sum(value or 0 for value in row_price_gaps)
        if all(value is not None for value in row_price_gaps)
        else None
    )
    if price_gap_summary is None or price_gap_rows is None or price_gap_summary != price_gap_rows:
        blockers.append(
            _blocker(
                "outcome_price_gap_aggregate_mismatch",
                "Outcome price-gap summary does not equal the preserved horizon-row aggregate.",
            )
        )

    top_filters = _as_dict(outcome_score.get("filters"))
    nested_filters = _as_dict(sample_after.get("filters"))
    if not top_filters or not nested_filters:
        blockers.append(
            _blocker(
                "outcome_filters_missing",
                "Outcome top-level and sample audit must both preserve cohort filters.",
            )
        )
    for key in COHORT_FILTER_KEYS:
        top_value = top_filters.get(key)
        nested_value = nested_filters.get(key)
        if top_value in (None, "") or nested_value in (None, ""):
            blockers.append(
                _blocker(
                    f"outcome_filter_{key}_missing",
                    f"Outcome cohort filter {key} is required at both levels.",
                )
            )
        elif top_value != nested_value:
            blockers.append(
                _blocker(
                    f"outcome_filter_{key}_mismatch",
                    f"Outcome top-level and sample-audit filter {key} differ.",
                )
            )
    filters = _canonical_copy(nested_filters)
    normalized_rows = [_canonical_copy(row) for row in rows]
    normalized_rows.sort(key=lambda row: _positive_int(_as_dict(row).get("horizon_day")) or 0)
    return (
        {
            "horizon_days": declared,
            "observation_unit": "recommendation_x_horizon",
            "filters": filters,
            "rows": normalized_rows,
            "aggregate_summary": _canonical_copy(summary),
            "aggregate_consistent": not blockers,
            "approved_horizon_policy_attested": False,
            "policy_limitation": (
                "Legacy artifacts report horizons but do not attest an approved authoritative horizon policy."
            ),
        },
        blockers,
    )


def _build_sample_identity(
    *,
    quality_score: dict[str, object],
    outcome_score: dict[str, object],
    portfolio_feedback_score: dict[str, object],
    sources: dict[str, dict[str, object]],
    as_of_date: date,
) -> dict[str, object]:
    sample_after = _as_dict(outcome_score.get("sample_audit_after"))
    summary = _as_dict(sample_after.get("summary"))
    horizon_rows = _as_list(sample_after.get("horizon_coverage"))
    portfolio_feedback_evidence = {
        "latest_feedback_runs": _canonical_copy(portfolio_feedback_score.get("latest_feedback_runs")),
        "status_counts": _canonical_copy(portfolio_feedback_score.get("status_counts")),
        "family_summaries": _canonical_copy(portfolio_feedback_score.get("family_summaries")),
        "decision_type_summaries": _canonical_copy(
            portfolio_feedback_score.get("decision_type_summaries")
        ),
        "symbol_summaries": _canonical_copy(portfolio_feedback_score.get("symbol_summaries")),
    }
    source_age_days: dict[str, int | None] = {}
    for source_name, source in sources.items():
        effective_date = _parse_date(str(source.get("score_as_of_date") or ""))
        if effective_date is None:
            effective_date = _parse_date(str(source.get("created_at") or ""))
        source_age_days[source_name] = (
            (as_of_date - effective_date).days
            if effective_date is not None and effective_date <= as_of_date
            else None
        )
    return {
        "status": "legacy_aggregate_only_not_attested",
        "identity_attested": False,
        "quality_observation_unit": "distinct_recommendation_latest_outcome_within_max_horizon",
        "quality_recommendation_count": _non_negative_int(quality_score.get("recommendation_count")),
        "quality_outcome_count": _non_negative_int(quality_score.get("outcome_count")),
        "horizon_observation_unit": "recommendation_x_horizon",
        "recommendation_horizon_observation_count": _non_negative_int(
            summary.get("recommendation_horizon_count")
        ),
        "horizon_outcome_observation_count": _non_negative_int(summary.get("outcome_count")),
        "portfolio_feedback_observation_unit": "legacy_feedback_item_aggregate",
        "portfolio_feedback_run_count": _non_negative_int(
            portfolio_feedback_score.get("feedback_run_count")
        ),
        "portfolio_feedback_decision_count": _non_negative_int(
            portfolio_feedback_score.get("decision_count")
        ),
        "portfolio_feedback_mature_decision_count": _non_negative_int(
            portfolio_feedback_score.get("mature_decision_count")
        ),
        "quality_component_metrics_sha256": _canonical_hash(
            _as_list(quality_score.get("component_metrics"))
        ),
        "outcome_horizon_coverage_sha256": _canonical_hash(horizon_rows),
        "portfolio_feedback_evidence_sha256": _canonical_hash(portfolio_feedback_evidence),
        "stable_row_level_sample_identity_attested": False,
        "feedback_deduplication_attested": False,
        "versioned_component_snapshot_integrity_attested": False,
        "freshness_policy_attested": False,
        "temporal_freshness_status": "policy_not_defined",
        "source_age_days": source_age_days,
        "limitations": [
            "Legacy recommendation and horizon aggregates do not expose a stable row-level cohort identity.",
            "Legacy portfolio feedback aggregates do not attest deduplication across feedback runs.",
            "Legacy component metrics do not attest a versioned component snapshot identity.",
            "No approved maximum-age or source-freshness policy is attested by legacy artifacts.",
        ],
    }


def _eligibility_reason(
    *,
    source_coherent: bool,
    threshold_evidence_ready: bool,
    portfolio_feedback_ready: bool,
    legacy_integrity_attested: bool,
) -> str:
    if not source_coherent:
        return "Source lineage or aggregate evidence is incoherent; eligibility fails closed."
    if not threshold_evidence_ready:
        return "Legacy readiness, quality, or outcome thresholds are not all met."
    if not portfolio_feedback_ready:
        return "Portfolio feedback is not mature enough for read-only manual review."
    if not legacy_integrity_attested:
        return (
            "Legacy thresholds are met, but stable sample identity, feedback deduplication, "
            "versioned component snapshots, an approved horizon policy, and a freshness policy "
            "are not attested."
        )
    return "Evidence is eligible for read-only human review only; no authorization is implied."


def _legacy_source_status(source_key: str, score: dict[str, object]) -> str:
    if source_key == "readiness":
        return str(score.get("decision") or "missing")
    if source_key == "quality":
        return str(score.get("quality_status") or "unknown")
    if source_key == "outcome":
        return str(score.get("status") or "missing")
    if source_key == "portfolio_feedback":
        return str(score.get("calibration_status") or "missing")
    return "unknown"


def _require_equal(
    blockers: list[dict[str, object]],
    *,
    code: str,
    message: str,
    actual: object,
    expected: object,
) -> None:
    if actual != expected:
        blockers.append(_blocker(code, message))


def _blocker(code: str, message: str) -> dict[str, object]:
    return {"code": code, "message": message}


def _as_blocker_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _as_raw_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _strict_positive_int_list(value: object) -> list[int]:
    if not isinstance(value, list):
        return []
    result: list[int] = []
    for item in value:
        parsed = _positive_int(item)
        if parsed is None:
            continue
        result.append(parsed)
    return result


def _positive_int(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _non_negative_int(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


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


def _canonical_hash(value: object) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _canonical_copy(value: object) -> object:
    try:
        return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str))
    except (TypeError, ValueError):
        return deepcopy(value)
