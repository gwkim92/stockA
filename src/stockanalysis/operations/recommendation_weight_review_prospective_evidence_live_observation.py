from __future__ import annotations

import json
from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.recommendation_weight_review_prospective_evidence_contract import (
    DEFAULT_PORTFOLIO_NAME,
    ORDER_BOUNDARY,
    _as_dict,
)
from stockanalysis.operations.recommendation_weight_review_prospective_evidence_foundation import (
    build_recommendation_weight_review_prospective_evidence_foundation,
)
from stockanalysis.operations.recommendation_weight_review_prospective_evidence_live_observation_contract import (
    DATABASE_IDENTITY_CONTRACT_VERSION,
    DEFAULT_DATASET_VERSION,
    DEFAULT_EVAL_NAME,
    DEFAULT_MODEL_NAME,
    DEFAULT_PIPELINE_NAME,
    DEFAULT_PROVIDER,
    LEGACY_SURFACE_CONTRACT_VERSION,
    REQUIRED_RELATIONS,
    LiveObservationIntegrityError,
    build_environment_blocked_observation,
    build_legacy_surface_snapshot,
    build_recommendation_weight_review_prospective_evidence_live_observation,
    normalize_live_observation_database_identity,
    require_positive_int,
    validate_environment_label,
    validate_sha256,
)
from stockanalysis.operations.recommendation_weight_review_prospective_evidence_lookup import (
    load_prospective_evidence_bundle,
)
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


def render_live_observation_database_identity_sql() -> str:
    relation_pairs = ",\n        ".join(
        f"{sql_literal(relation)}, to_regclass({sql_literal(relation)}) is not null"
        for relation in REQUIRED_RELATIONS
    )
    return f"""-- recommendation weight review live observation database identity v1
select json_build_object(
    'contract_version', {sql_literal(DATABASE_IDENTITY_CONTRACT_VERSION)},
    'database_name', current_database(),
    'role_name', current_user,
    'server_version_num', current_setting('server_version_num'),
    'server_address', inet_server_addr()::text,
    'server_port', inet_server_port(),
    'required_relations', json_build_object(
        {relation_pairs}
    )
)::text;"""


def load_live_observation_database_identity(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(render_live_observation_database_identity_sql())
    )
    if not isinstance(payload, dict):
        raise ValueError("Live observation database identity did not return a JSON object.")
    return payload


def render_live_observation_eval_insert_sql(
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


def run_recommendation_weight_review_prospective_evidence_live_observation(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    lineage_eval_run_id: int,
    portfolio_feedback_calibration_eval_run_id: int,
    environment_label: str,
    expected_database_identity_sha256: str,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    lineage_id = require_positive_int(lineage_eval_run_id, field_name="lineage_eval_run_id")
    feedback_id = require_positive_int(
        portfolio_feedback_calibration_eval_run_id,
        field_name="portfolio_feedback_calibration_eval_run_id",
    )
    environment_label = validate_environment_label(environment_label)
    expected_sha = validate_sha256(
        expected_database_identity_sha256,
        field_name="expected_database_identity_sha256",
    )
    portfolio_name = portfolio_name.strip()
    if not portfolio_name:
        raise ValueError("portfolio_name must not be empty.")

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    identity_payload = load_live_observation_database_identity(
        config=config,
        executor=sql_executor,
    )
    identity = normalize_live_observation_database_identity(identity_payload)
    identity_attested = identity.get("complete") is True and identity.get("sha256") == expected_sha
    if not identity_attested:
        observation = build_environment_blocked_observation(
            as_of_date=as_of_date,
            environment_label=environment_label,
            expected_database_identity_sha256=expected_sha,
            database_identity=identity,
            lineage_eval_run_id=lineage_id,
            portfolio_feedback_calibration_eval_run_id=feedback_id,
        )
        return _report(
            as_of_date=as_of_date,
            portfolio_name=portfolio_name,
            environment_label=environment_label,
            execute=execute,
            status="blocked",
            observation=observation,
            write_count=0,
        )

    bundle_before = _load_exact_bundle(
        config=config,
        executor=sql_executor,
        as_of_date=as_of_date,
        lineage_eval_run_id=lineage_id,
        feedback_eval_run_id=feedback_id,
        portfolio_name=portfolio_name,
    )
    foundation_before = build_recommendation_weight_review_prospective_evidence_foundation(
        as_of_date=as_of_date,
        bundle=bundle_before,
        portfolio_name=portfolio_name,
    )
    surface_before = build_legacy_surface_snapshot(
        bundle=bundle_before,
        foundation=foundation_before,
    )
    preflight = build_recommendation_weight_review_prospective_evidence_live_observation(
        as_of_date=as_of_date,
        environment_label=environment_label,
        expected_database_identity_sha256=expected_sha,
        database_identity_payload=identity_payload,
        lineage_eval_run_id=lineage_id,
        portfolio_feedback_calibration_eval_run_id=feedback_id,
        bundle=bundle_before,
        foundation=foundation_before,
        legacy_surface_before=surface_before,
    )
    report = _report(
        as_of_date=as_of_date,
        portfolio_name=portfolio_name,
        environment_label=environment_label,
        execute=execute,
        status="planned" if not execute else "running",
        observation=preflight,
    )
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "portfolio_name": portfolio_name,
            "environment_label": environment_label,
            "database_identity_sha256": identity.get("sha256"),
            "lineage_eval_run_id": lineage_id,
            "portfolio_feedback_calibration_eval_run_id": feedback_id,
            "legacy_surface_before_sha256": surface_before.get("payload_sha256"),
            "mode": "live_database_append_only_observation",
            "authoritative": False,
            "weight_mutation_allowed": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "order_boundary": ORDER_BOUNDARY,
        },
    )
    try:
        bundle_after = _load_exact_bundle(
            config=config,
            executor=sql_executor,
            as_of_date=as_of_date,
            lineage_eval_run_id=lineage_id,
            feedback_eval_run_id=feedback_id,
            portfolio_name=portfolio_name,
        )
        foundation_after = build_recommendation_weight_review_prospective_evidence_foundation(
            as_of_date=as_of_date,
            bundle=bundle_after,
            portfolio_name=portfolio_name,
        )
        surface_after = build_legacy_surface_snapshot(
            bundle=bundle_after,
            foundation=foundation_after,
        )
        observation = build_recommendation_weight_review_prospective_evidence_live_observation(
            as_of_date=as_of_date,
            environment_label=environment_label,
            expected_database_identity_sha256=expected_sha,
            database_identity_payload=identity_payload,
            lineage_eval_run_id=lineage_id,
            portfolio_feedback_calibration_eval_run_id=feedback_id,
            bundle=bundle_after,
            foundation=foundation_after,
            legacy_surface_before=surface_before,
            legacy_surface_after=surface_after,
        )
        if _as_dict(observation.get("legacy_surface")).get("unchanged") is not True:
            raise LiveObservationIntegrityError(
                "Legacy recommendation evidence surface changed during live observation."
            )
        eval_run_id = int(
            sql_executor.execute_scalar(
                render_live_observation_eval_insert_sql(score_json=observation)
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
        "write_count": 2,
        "observation": observation,
    }


def _load_exact_bundle(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor,
    as_of_date: date,
    lineage_eval_run_id: int,
    feedback_eval_run_id: int,
    portfolio_name: str,
) -> dict[str, object]:
    return load_prospective_evidence_bundle(
        config=config,
        as_of_date=as_of_date,
        lineage_eval_run_id=lineage_eval_run_id,
        portfolio_feedback_calibration_eval_run_id=feedback_eval_run_id,
        portfolio_name=portfolio_name,
        executor=executor,
    )


def _report(
    *,
    as_of_date: date,
    portfolio_name: str,
    environment_label: str,
    execute: bool,
    status: str,
    observation: dict[str, object],
    write_count: int | None = None,
) -> dict[str, object]:
    report: dict[str, object] = {
        "report_name": DEFAULT_EVAL_NAME,
        "status": status,
        "execute": execute,
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "portfolio_name": portfolio_name,
        "environment_label": environment_label,
        "mode": "live_database_append_only_observation",
        "authoritative": False,
        "observation": observation,
    }
    if write_count is not None:
        report["write_count"] = write_count
    return report
