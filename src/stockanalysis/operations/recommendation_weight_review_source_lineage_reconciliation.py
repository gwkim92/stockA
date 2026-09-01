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


DEFAULT_EVAL_NAME = "recommendation_weight_review_source_lineage_reconciliation_v1"
DEFAULT_DATASET_VERSION = "recommendation-weight-review-source-lineage-reconciliation-v1"
DEFAULT_PIPELINE_NAME = "recommendation_weight_review_source_lineage_reconciliation_v1"
DEFAULT_PROVIDER = "postgres"
DEFAULT_MODEL_NAME = "deterministic-source-lineage-v1"

SOURCE_READINESS_EVAL_NAME = "recommendation_weight_review_readiness_audit"
SOURCE_READINESS_DATASET_VERSION = "recommendation-weight-review-readiness-v1"
SOURCE_QUALITY_EVAL_NAME = "recommendation_quality_calibration"
SOURCE_QUALITY_DATASET_VERSION = "recommendation-quality-live-v1"
SOURCE_OUTCOME_EVAL_NAME = "recommendation_outcome_calibration_sample_expansion"
SOURCE_OUTCOME_DATASET_VERSION = "recommendation-outcome-calibration-sample-expansion-v1"

SOURCE_LINEAGE_CONTRACT_VERSION = "recommendation-weight-review-source-lineage-v1"
COHORT_FILTER_CONTRACT_VERSION = "recommendation-weight-review-cohort-filter-v1"
NESTED_QUALITY_CONTRACT_VERSION = "recommendation-weight-review-nested-quality-v1"
ORDER_BOUNDARY = "read_only_no_order"
COHORT_FILTER_KEYS = (
    "market_code",
    "strategy_name",
    "horizon_type",
    "universe_version",
)


def render_source_lineage_bundle_lookup_sql(
    *,
    as_of_date: date,
    readiness_eval_run_id: int | None = None,
) -> str:
    readiness_id_filter = ""
    if readiness_eval_run_id is not None:
        if readiness_eval_run_id <= 0:
            raise ValueError("readiness_eval_run_id must be greater than 0.")
        readiness_id_filter = f"\n      and eval_run.eval_run_id = {readiness_eval_run_id}"

    score_date_guard = _render_score_date_guard(alias="eval_run", as_of_date=as_of_date)
    referenced_score_date_guard = _render_score_date_guard(alias="referenced_eval", as_of_date=as_of_date)
    return f"""-- recommendation weight review source lineage reconciliation v1 atomic lookup
with readiness_candidates as (
    select
        eval_run.eval_run_id,
        eval_run.eval_name,
        eval_run.dataset_version,
        eval_run.provider,
        eval_run.model_name,
        eval_run.score_json,
        eval_run.created_at
    from ai.eval_run eval_run
    where eval_run.eval_name = {sql_literal(SOURCE_READINESS_EVAL_NAME)}
      and eval_run.dataset_version = {sql_literal(SOURCE_READINESS_DATASET_VERSION)}
      and eval_run.created_at::date <= {sql_date(as_of_date)}{readiness_id_filter}
    order by eval_run.created_at desc, eval_run.eval_run_id desc
    limit 1
),
selected_readiness as (
    select * from readiness_candidates
),
lineage_refs as (
    select
        case
            when coalesce(selected_readiness.score_json->>'source_eval_run_id', '') ~ '^[1-9][0-9]*$'
                then (selected_readiness.score_json->>'source_eval_run_id')::bigint
            else null::bigint
        end as quality_eval_run_id,
        case
            when coalesce(selected_readiness.score_json #>> '{{outcome_calibration_gate,eval_run_id}}', '') ~ '^[1-9][0-9]*$'
                then (selected_readiness.score_json #>> '{{outcome_calibration_gate,eval_run_id}}')::bigint
            else null::bigint
        end as outcome_eval_run_id
    from selected_readiness
),
referenced_quality as (
    select
        referenced_eval.eval_run_id,
        referenced_eval.eval_name,
        referenced_eval.dataset_version,
        referenced_eval.provider,
        referenced_eval.model_name,
        referenced_eval.score_json,
        referenced_eval.created_at
    from ai.eval_run referenced_eval
    join lineage_refs refs on referenced_eval.eval_run_id = refs.quality_eval_run_id
    where referenced_eval.created_at::date <= {sql_date(as_of_date)}
      and {referenced_score_date_guard}
    limit 1
),
referenced_outcome as (
    select
        referenced_eval.eval_run_id,
        referenced_eval.eval_name,
        referenced_eval.dataset_version,
        referenced_eval.provider,
        referenced_eval.model_name,
        referenced_eval.score_json,
        referenced_eval.created_at
    from ai.eval_run referenced_eval
    join lineage_refs refs on referenced_eval.eval_run_id = refs.outcome_eval_run_id
    where referenced_eval.created_at::date <= {sql_date(as_of_date)}
      and {referenced_score_date_guard}
    limit 1
),
latest_quality as (
    select
        eval_run.eval_run_id,
        eval_run.eval_name,
        eval_run.dataset_version,
        eval_run.provider,
        eval_run.model_name,
        eval_run.score_json,
        eval_run.created_at
    from ai.eval_run eval_run
    where eval_run.eval_name = {sql_literal(SOURCE_QUALITY_EVAL_NAME)}
      and eval_run.dataset_version = {sql_literal(SOURCE_QUALITY_DATASET_VERSION)}
      and eval_run.created_at::date <= {sql_date(as_of_date)}
      and {score_date_guard}
    order by
        (eval_run.score_json->>'as_of_date')::date desc,
        eval_run.created_at desc,
        eval_run.eval_run_id desc
    limit 1
),
latest_outcome as (
    select
        eval_run.eval_run_id,
        eval_run.eval_name,
        eval_run.dataset_version,
        eval_run.provider,
        eval_run.model_name,
        eval_run.score_json,
        eval_run.created_at
    from ai.eval_run eval_run
    where eval_run.eval_name = {sql_literal(SOURCE_OUTCOME_EVAL_NAME)}
      and eval_run.dataset_version = {sql_literal(SOURCE_OUTCOME_DATASET_VERSION)}
      and eval_run.created_at::date <= {sql_date(as_of_date)}
      and {score_date_guard}
    order by
        (eval_run.score_json->>'as_of_date')::date desc,
        eval_run.created_at desc,
        eval_run.eval_run_id desc
    limit 1
)
select json_build_object(
    'readiness', { _render_selected_eval_json('selected_readiness') },
    'referenced_quality', { _render_selected_eval_json('referenced_quality') },
    'referenced_outcome', { _render_selected_eval_json('referenced_outcome') },
    'latest_quality', { _render_selected_eval_json('latest_quality') },
    'latest_outcome', { _render_selected_eval_json('latest_outcome') }
)::text;"""


def render_source_lineage_reconciliation_eval_insert_sql(
    *,
    score_json: dict[str, object],
) -> str:
    score_text = json.dumps(
        score_json,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
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


def load_source_lineage_bundle(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    readiness_eval_run_id: int | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_source_lineage_bundle_lookup_sql(
                as_of_date=as_of_date,
                readiness_eval_run_id=readiness_eval_run_id,
            )
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Source-lineage lookup did not return a JSON object.")
    return payload


def build_recommendation_weight_review_source_lineage_reconciliation(
    *,
    as_of_date: date,
    bundle: dict[str, object],
) -> dict[str, object]:
    blockers: list[dict[str, object]] = []

    readiness, readiness_blockers = _normalize_required_source(
        _as_dict(bundle.get("readiness")),
        source_key="readiness",
        expected_eval_name=SOURCE_READINESS_EVAL_NAME,
        expected_dataset_version=SOURCE_READINESS_DATASET_VERSION,
        as_of_date=as_of_date,
        score_date_required=False,
    )
    referenced_quality, quality_blockers = _normalize_required_source(
        _as_dict(bundle.get("referenced_quality")),
        source_key="referenced_quality",
        expected_eval_name=SOURCE_QUALITY_EVAL_NAME,
        expected_dataset_version=SOURCE_QUALITY_DATASET_VERSION,
        as_of_date=as_of_date,
        score_date_required=True,
    )
    referenced_outcome, outcome_blockers = _normalize_required_source(
        _as_dict(bundle.get("referenced_outcome")),
        source_key="referenced_outcome",
        expected_eval_name=SOURCE_OUTCOME_EVAL_NAME,
        expected_dataset_version=SOURCE_OUTCOME_DATASET_VERSION,
        as_of_date=as_of_date,
        score_date_required=True,
    )
    blockers.extend(readiness_blockers)
    blockers.extend(quality_blockers)
    blockers.extend(outcome_blockers)

    readiness_score = _as_dict(_as_dict(bundle.get("readiness")).get("score_json"))
    quality_score = _as_dict(_as_dict(bundle.get("referenced_quality")).get("score_json"))
    outcome_score = _as_dict(_as_dict(bundle.get("referenced_outcome")).get("score_json"))

    quality_reference_id = _positive_int(readiness_score.get("source_eval_run_id"))
    outcome_gate = _as_dict(readiness_score.get("outcome_calibration_gate"))
    outcome_reference_id = _positive_int(outcome_gate.get("eval_run_id"))
    if quality_reference_id is None:
        blockers.append(
            _blocker(
                "readiness_quality_reference_missing",
                "Readiness source_eval_run_id is missing or invalid.",
                category="incomplete",
            )
        )
    if outcome_reference_id is None:
        blockers.append(
            _blocker(
                "readiness_outcome_reference_missing",
                "Readiness outcome_calibration_gate.eval_run_id is missing or invalid.",
                category="incomplete",
            )
        )

    _require_equal(
        blockers,
        code="resolved_quality_reference_mismatch",
        message="Resolved quality eval ID does not equal readiness source_eval_run_id.",
        actual=referenced_quality.get("eval_run_id"),
        expected=quality_reference_id,
    )
    _require_equal(
        blockers,
        code="resolved_outcome_reference_mismatch",
        message="Resolved outcome eval ID does not equal readiness outcome reference.",
        actual=referenced_outcome.get("eval_run_id"),
        expected=outcome_reference_id,
    )

    readiness_decision = str(readiness_score.get("decision") or "")
    readiness_allowed = readiness_score.get("manual_weight_review_allowed")
    if not readiness_decision:
        blockers.append(
            _blocker(
                "readiness_decision_missing",
                "Readiness decision is missing.",
                category="incomplete",
            )
        )
    if not isinstance(readiness_allowed, bool):
        blockers.append(
            _blocker(
                "readiness_manual_review_boolean_missing",
                "Readiness manual_weight_review_allowed must be an explicit boolean.",
                category="incomplete",
            )
        )
    elif readiness_decision and readiness_allowed != (
        readiness_decision == "ready_for_manual_weight_review"
    ):
        blockers.append(
            _blocker(
                "readiness_decision_boolean_mismatch",
                "Readiness decision and manual_weight_review_allowed are internally inconsistent.",
                category="incoherent",
            )
        )

    quality_status = str(quality_score.get("quality_status") or "")
    readiness_quality_status = str(readiness_score.get("source_quality_status") or "")
    outcome_status = str(outcome_score.get("status") or "")
    readiness_outcome_status = str(outcome_gate.get("status") or "")
    outcome_quality_status = str(outcome_score.get("quality_status") or "")
    gate_quality_status = str(outcome_gate.get("quality_status") or "")
    outcome_sample_status = str(outcome_score.get("sample_status") or "")
    gate_sample_status = str(outcome_gate.get("sample_status") or "")

    for code, message, actual, expected in (
        (
            "readiness_quality_status_mismatch",
            "Readiness quality status differs from the exact referenced quality artifact.",
            readiness_quality_status,
            quality_status,
        ),
        (
            "readiness_outcome_status_mismatch",
            "Readiness outcome status differs from the exact referenced outcome artifact.",
            readiness_outcome_status,
            outcome_status,
        ),
        (
            "readiness_gate_quality_status_mismatch",
            "Readiness outcome gate quality status differs from the exact referenced quality artifact.",
            gate_quality_status,
            quality_status,
        ),
        (
            "outcome_quality_status_mismatch",
            "Referenced outcome quality status differs from the exact referenced quality artifact.",
            outcome_quality_status,
            quality_status,
        ),
        (
            "readiness_gate_sample_status_mismatch",
            "Readiness outcome gate sample status differs from the exact referenced outcome artifact.",
            gate_sample_status,
            outcome_sample_status,
        ),
    ):
        if not actual or not expected:
            blockers.append(
                _blocker(
                    f"{code}_missing",
                    f"{message} One or both statuses are missing.",
                    category="incomplete",
                )
            )
        elif actual != expected:
            blockers.append(_blocker(code, message, category="incoherent"))

    cohort_identity, cohort_blockers = _build_cohort_filter_identity(
        outcome_score=outcome_score,
        outcome_eval_run_id=_positive_int(referenced_outcome.get("eval_run_id")),
    )
    nested_quality_identity, nested_quality_blockers = _build_nested_quality_identity(
        quality_score=quality_score,
        outcome_score=outcome_score,
        quality_eval_run_id=_positive_int(referenced_quality.get("eval_run_id")),
    )
    blockers.extend(cohort_blockers)
    blockers.extend(nested_quality_blockers)

    canonical_chain_payload = {
        "contract_version": SOURCE_LINEAGE_CONTRACT_VERSION,
        "as_of_date": as_of_date.isoformat(),
        "readiness": _chain_source_identity(readiness),
        "quality": _chain_source_identity(referenced_quality),
        "outcome": _chain_source_identity(referenced_outcome),
        "quality_reference_eval_run_id": quality_reference_id,
        "outcome_reference_eval_run_id": outcome_reference_id,
        "cohort_filter_identity_sha256": cohort_identity.get("identity_sha256"),
        "nested_quality_identity_sha256": nested_quality_identity.get("identity_sha256"),
        "status_snapshot": {
            "readiness_decision": readiness_decision or None,
            "readiness_manual_weight_review_allowed": (
                readiness_allowed if isinstance(readiness_allowed, bool) else None
            ),
            "quality_status": quality_status or None,
            "outcome_status": outcome_status or None,
            "outcome_sample_status": outcome_sample_status or None,
        },
    }
    canonical_chain_sha256 = _canonical_hash(canonical_chain_payload)
    canonical_chain = {
        **canonical_chain_payload,
        "sha256": canonical_chain_sha256,
    }

    latest_quality = _normalize_diagnostic_source(_as_dict(bundle.get("latest_quality")))
    latest_outcome = _normalize_diagnostic_source(_as_dict(bundle.get("latest_outcome")))
    latest_drift = {
        "authoritative": False,
        "selection_role": "diagnostic_latest_observation_only",
        "quality": _build_latest_drift_item(referenced_quality, latest_quality),
        "outcome": _build_latest_drift_item(referenced_outcome, latest_outcome),
    }
    latest_drift["drift_detected"] = any(
        _as_dict(latest_drift[key]).get("status") == "different_latest_observation"
        for key in ("quality", "outcome")
    )

    blocker_categories = {str(item.get("category") or "incoherent") for item in blockers}
    if "incomplete" in blocker_categories:
        status = "lineage_incomplete_fail_closed"
    elif blockers:
        status = "lineage_incoherent_fail_closed"
    else:
        status = "reconciled_read_only"
    lineage_reconciled = not blockers

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
        "recommendation_scoring_mutated": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
    }
    return {
        "eval_name": DEFAULT_EVAL_NAME,
        "dataset_version": DEFAULT_DATASET_VERSION,
        "as_of_date": as_of_date.isoformat(),
        "mode": "shadow_read_only",
        "authoritative": False,
        "status": status,
        "decision": status,
        "lineage_reconciled": lineage_reconciled,
        "lineage_ready_for_prospective_identity_work": lineage_reconciled,
        "selection_policy": {
            "contract_version": SOURCE_LINEAGE_CONTRACT_VERSION,
            "anchor": "readiness_eval",
            "quality_selection": "exact_readiness_source_eval_run_id",
            "outcome_selection": "exact_readiness_outcome_calibration_gate_eval_run_id",
            "latest_selection_role": "drift_diagnostic_only",
            "latest_may_replace_reference": False,
        },
        "source_snapshot": {
            "readiness": readiness,
            "referenced_quality": referenced_quality,
            "referenced_outcome": referenced_outcome,
        },
        "canonical_chain": canonical_chain,
        "cohort_filter_identity": cohort_identity,
        "nested_quality_identity": nested_quality_identity,
        "latest_drift_observation": latest_drift,
        "blockers": blockers,
        "next_action": _next_action(status),
        "authorization_boundary": {
            "status": "not_requested_not_present",
            "explicit_user_approval_present": False,
            "pilot_scope_defined": False,
            "reason": "Lineage reconciliation is evidence plumbing only and cannot authorize a pilot or mutation.",
        },
        "mutation_boundary": {
            "status": "blocked_read_only_shadow",
            "weight_mutation_allowed": False,
            "automatic_weight_change_allowed": False,
            "portfolio_position_mutation_allowed": False,
            "recommendation_scoring_mutated": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "order_boundary": ORDER_BOUNDARY,
        },
        **hard_false_permissions,
        "order_boundary": ORDER_BOUNDARY,
    }


def run_recommendation_weight_review_source_lineage_reconciliation(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    readiness_eval_run_id: int | None = None,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    bundle = load_source_lineage_bundle(
        config=config,
        as_of_date=as_of_date,
        readiness_eval_run_id=readiness_eval_run_id,
        executor=sql_executor,
    )
    reconciliation = build_recommendation_weight_review_source_lineage_reconciliation(
        as_of_date=as_of_date,
        bundle=bundle,
    )
    report: dict[str, object] = {
        "report_name": DEFAULT_EVAL_NAME,
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "mode": "shadow_read_only",
        "authoritative": False,
        "reconciliation": reconciliation,
    }
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "readiness_eval_run_id": _positive_int(
                _as_dict(bundle.get("readiness")).get("eval_run_id")
            ),
            "quality_eval_run_id": _positive_int(
                _as_dict(bundle.get("referenced_quality")).get("eval_run_id")
            ),
            "outcome_eval_run_id": _positive_int(
                _as_dict(bundle.get("referenced_outcome")).get("eval_run_id")
            ),
            "decision": reconciliation["decision"],
            "canonical_chain_sha256": _as_dict(reconciliation.get("canonical_chain")).get("sha256"),
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
                render_source_lineage_reconciliation_eval_insert_sql(
                    score_json=reconciliation,
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


def _render_score_date_guard(*, alias: str, as_of_date: date) -> str:
    date_expression = f"{alias}.score_json->>'as_of_date'"
    return (
        "case "
        f"when coalesce({date_expression}, '') ~ "
        "'^[0-9]{4}-(0[1-9]|1[0-2])-([0-2][0-9]|3[0-1])$' "
        "then case "
        f"when to_char(to_date({date_expression}, 'YYYY-MM-DD'), 'YYYY-MM-DD') = {date_expression} "
        f"then to_date({date_expression}, 'YYYY-MM-DD') <= {sql_date(as_of_date)} "
        "else false end "
        "else false end"
    )


def _render_selected_eval_json(cte_name: str) -> str:
    return f"""coalesce(
        (
            select json_build_object(
                'eval_run_id', {cte_name}.eval_run_id,
                'eval_name', {cte_name}.eval_name,
                'dataset_version', {cte_name}.dataset_version,
                'provider', {cte_name}.provider,
                'model_name', {cte_name}.model_name,
                'score_json', {cte_name}.score_json,
                'created_at', {cte_name}.created_at
            )
            from {cte_name}
        ),
        '{{}}'::json
    )"""


def _normalize_required_source(
    wrapper: dict[str, object],
    *,
    source_key: str,
    expected_eval_name: str,
    expected_dataset_version: str,
    as_of_date: date,
    score_date_required: bool,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    blockers: list[dict[str, object]] = []
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
                f"{source_key}_source_missing",
                "Required source artifact is missing.",
                category="incomplete",
            )
        )
    if eval_run_id is None:
        blockers.append(
            _blocker(
                f"{source_key}_eval_run_id_missing",
                "Source eval_run_id is missing or invalid.",
                category="incomplete",
            )
        )
    if not eval_name:
        blockers.append(
            _blocker(
                f"{source_key}_eval_name_missing",
                "Source eval_name is missing.",
                category="incomplete",
            )
        )
    elif eval_name != expected_eval_name:
        blockers.append(
            _blocker(
                f"{source_key}_eval_name_mismatch",
                "Source eval_name does not match the required artifact.",
                category="incoherent",
            )
        )
    if not dataset_version:
        blockers.append(
            _blocker(
                f"{source_key}_dataset_version_missing",
                "Source dataset_version is missing.",
                category="incomplete",
            )
        )
    elif dataset_version != expected_dataset_version:
        blockers.append(
            _blocker(
                f"{source_key}_dataset_version_mismatch",
                "Source dataset_version does not match the required artifact.",
                category="incoherent",
            )
        )
    if not score:
        blockers.append(
            _blocker(
                f"{source_key}_score_missing",
                "Source score_json is missing or empty.",
                category="incomplete",
            )
        )
    if not created_at_text:
        blockers.append(
            _blocker(
                f"{source_key}_created_at_missing",
                "Source created_at is missing.",
                category="incomplete",
            )
        )
    elif created_date is None:
        blockers.append(
            _blocker(
                f"{source_key}_created_at_invalid",
                "Source created_at is invalid.",
                category="incoherent",
            )
        )
    elif created_date > as_of_date:
        blockers.append(
            _blocker(
                f"{source_key}_created_after_as_of",
                "Source was created after the reconciliation as-of date.",
                category="incoherent",
            )
        )
    if score_date_required:
        if not score_date_text:
            blockers.append(
                _blocker(
                    f"{source_key}_score_date_missing",
                    "Source score as_of_date is missing.",
                    category="incomplete",
                )
            )
        elif score_date is None:
            blockers.append(
                _blocker(
                    f"{source_key}_score_date_invalid",
                    "Source score as_of_date is invalid.",
                    category="incoherent",
                )
            )
        elif score_date > as_of_date:
            blockers.append(
                _blocker(
                    f"{source_key}_score_after_as_of",
                    "Source score is dated after the reconciliation as-of date.",
                    category="incoherent",
                )
            )

    return (
        {
            "eval_run_id": eval_run_id,
            "eval_name": eval_name or None,
            "dataset_version": dataset_version or None,
            "provider": wrapper.get("provider"),
            "model_name": wrapper.get("model_name"),
            "score_as_of_date": score_date_text or None,
            "created_at": created_at_text or None,
            "legacy_status": _legacy_status(source_key, score),
            "score_sha256": _canonical_hash(score),
        },
        blockers,
    )


def _normalize_diagnostic_source(wrapper: dict[str, object]) -> dict[str, object]:
    score = _as_dict(wrapper.get("score_json"))
    return {
        "eval_run_id": _positive_int(wrapper.get("eval_run_id")),
        "eval_name": wrapper.get("eval_name"),
        "dataset_version": wrapper.get("dataset_version"),
        "score_as_of_date": score.get("as_of_date"),
        "created_at": wrapper.get("created_at"),
        "score_sha256": _canonical_hash(score) if score else None,
    }


def _build_cohort_filter_identity(
    *,
    outcome_score: dict[str, object],
    outcome_eval_run_id: int | None,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    blockers: list[dict[str, object]] = []
    top_filters = _as_dict(outcome_score.get("filters"))
    nested_filters = _as_dict(_as_dict(outcome_score.get("sample_audit_after")).get("filters"))
    if not top_filters:
        blockers.append(
            _blocker(
                "outcome_top_level_filters_missing",
                "Referenced outcome top-level cohort filters are missing.",
                category="incomplete",
            )
        )
    if not nested_filters:
        blockers.append(
            _blocker(
                "outcome_nested_filters_missing",
                "Referenced outcome sample-audit cohort filters are missing.",
                category="incomplete",
            )
        )

    required_identity: dict[str, object] = {}
    for key in COHORT_FILTER_KEYS:
        top_value = top_filters.get(key)
        nested_value = nested_filters.get(key)
        if top_value in (None, ""):
            blockers.append(
                _blocker(
                    f"outcome_top_filter_{key}_missing",
                    f"Referenced outcome top-level filter {key} is missing.",
                    category="incomplete",
                )
            )
        if nested_value in (None, ""):
            blockers.append(
                _blocker(
                    f"outcome_nested_filter_{key}_missing",
                    f"Referenced outcome nested filter {key} is missing.",
                    category="incomplete",
                )
            )
        if top_value not in (None, "") and nested_value not in (None, ""):
            if top_value != nested_value:
                blockers.append(
                    _blocker(
                        f"outcome_filter_{key}_mismatch",
                        f"Referenced outcome top-level and nested filter {key} differ.",
                        category="incoherent",
                    )
                )
            else:
                required_identity[key] = _canonical_copy(top_value)

    identity_payload = {
        "contract_version": COHORT_FILTER_CONTRACT_VERSION,
        "outcome_eval_run_id": outcome_eval_run_id,
        "required_filters": required_identity,
    }
    return (
        {
            **identity_payload,
            "top_level_filters": _canonical_copy(top_filters),
            "nested_filters": _canonical_copy(nested_filters),
            "top_level_filters_sha256": _canonical_hash(top_filters),
            "nested_filters_sha256": _canonical_hash(nested_filters),
            "identity_sha256": _canonical_hash(identity_payload),
            "attested": not blockers,
        },
        blockers,
    )


def _build_nested_quality_identity(
    *,
    quality_score: dict[str, object],
    outcome_score: dict[str, object],
    quality_eval_run_id: int | None,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    blockers: list[dict[str, object]] = []
    nested_quality = _as_dict(outcome_score.get("quality_eval_score"))
    if not quality_score:
        blockers.append(
            _blocker(
                "referenced_quality_score_missing",
                "Exact referenced quality score is missing.",
                category="incomplete",
            )
        )
    if not nested_quality:
        blockers.append(
            _blocker(
                "outcome_nested_quality_missing",
                "Referenced outcome nested quality score is missing.",
                category="incomplete",
            )
        )
    quality_sha256 = _canonical_hash(quality_score)
    nested_sha256 = _canonical_hash(nested_quality)
    hashes_match = bool(quality_score and nested_quality and quality_sha256 == nested_sha256)
    if quality_score and nested_quality and not hashes_match:
        blockers.append(
            _blocker(
                "outcome_nested_quality_mismatch",
                "Referenced outcome nested quality score differs from the exact referenced quality artifact.",
                category="incoherent",
            )
        )
    identity_payload = {
        "contract_version": NESTED_QUALITY_CONTRACT_VERSION,
        "quality_eval_run_id": quality_eval_run_id,
        "referenced_quality_score_sha256": quality_sha256,
        "outcome_nested_quality_score_sha256": nested_sha256,
    }
    return (
        {
            **identity_payload,
            "identity_sha256": _canonical_hash(identity_payload),
            "hashes_match": hashes_match,
            "attested": not blockers,
        },
        blockers,
    )


def _legacy_status(source_key: str, score: dict[str, object]) -> str | None:
    if source_key == "readiness":
        return str(score.get("decision") or "") or None
    if source_key == "referenced_quality":
        return str(score.get("quality_status") or "") or None
    if source_key == "referenced_outcome":
        return str(score.get("status") or "") or None
    return None


def _chain_source_identity(source: dict[str, object]) -> dict[str, object]:
    return {
        "eval_run_id": source.get("eval_run_id"),
        "eval_name": source.get("eval_name"),
        "dataset_version": source.get("dataset_version"),
        "score_as_of_date": source.get("score_as_of_date"),
        "created_at": source.get("created_at"),
        "score_sha256": source.get("score_sha256"),
    }


def _build_latest_drift_item(
    referenced: dict[str, object],
    latest: dict[str, object],
) -> dict[str, object]:
    referenced_id = _positive_int(referenced.get("eval_run_id"))
    latest_id = _positive_int(latest.get("eval_run_id"))
    if latest_id is None:
        status = "latest_observation_missing"
    elif (
        referenced_id == latest_id
        and referenced.get("score_sha256") == latest.get("score_sha256")
    ):
        status = "same_as_referenced"
    else:
        status = "different_latest_observation"
    return {
        "status": status,
        "referenced_eval_run_id": referenced_id,
        "referenced_score_sha256": referenced.get("score_sha256"),
        "latest_eval_run_id": latest_id,
        "latest_score_sha256": latest.get("score_sha256"),
        "latest_score_as_of_date": latest.get("score_as_of_date"),
        "latest_created_at": latest.get("created_at"),
        "may_replace_canonical_reference": False,
    }


def _require_equal(
    blockers: list[dict[str, object]],
    *,
    code: str,
    message: str,
    actual: object,
    expected: object,
) -> None:
    if actual is None or expected is None:
        return
    if actual != expected:
        blockers.append(_blocker(code, message, category="incoherent"))


def _next_action(status: str) -> str:
    if status == "reconciled_read_only":
        return (
            "Use the canonical lineage only as input to prospective row-identity, component-snapshot, "
            "feedback-deduplication, and freshness-policy work. Do not start a weight pilot."
        )
    if status == "lineage_incomplete_fail_closed":
        return "Locate the missing readiness-referenced artifact or reference field without rewriting legacy evidence."
    return "Resolve the identified lineage inconsistency without substituting independently selected latest artifacts."


def _blocker(code: str, message: str, *, category: str) -> dict[str, object]:
    return {"code": code, "message": message, "category": category}


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _positive_int(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


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
        return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str))
    except (TypeError, ValueError):
        return deepcopy(value)
