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
    render_prospective_evidence_bundle_lookup_sql,
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


def render_live_observation_guarded_bundle_lookup_sql(
    *,
    as_of_date: date,
    lineage_eval_run_id: int,
    portfolio_feedback_calibration_eval_run_id: int,
    portfolio_name: str,
    database_identity: dict[str, object],
) -> str:
    base_sql = render_prospective_evidence_bundle_lookup_sql(
        as_of_date=as_of_date,
        lineage_eval_run_id=lineage_eval_run_id,
        portfolio_feedback_calibration_eval_run_id=(
            portfolio_feedback_calibration_eval_run_id
        ),
        portfolio_name=portfolio_name,
    )
    return f"""{_render_identity_guard_block(database_identity)}
{base_sql}"""


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


def render_live_observation_pipeline_run_insert_sql(
    *,
    config_json: dict[str, object],
    database_identity: dict[str, object],
) -> str:
    payload = json.dumps(
        config_json,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    guard = _render_identity_guard_expression(database_identity)
    return f"""insert into ops.pipeline_run (
    run_kind,
    pipeline_name,
    status,
    config_json
)
select
    'signal',
    {sql_literal(DEFAULT_PIPELINE_NAME)},
    'running',
    {sql_literal(payload)}::jsonb
where
    {guard}
returning run_id;"""


def render_live_observation_eval_insert_sql(
    *,
    score_json: dict[str, object],
    database_identity: dict[str, object],
) -> str:
    score_text = json.dumps(
        score_json,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    guard = _render_identity_guard_expression(database_identity)
    return f"""insert into ai.eval_run (
    eval_name,
    dataset_version,
    provider,
    model_name,
    score_json
)
select
    {sql_literal(DEFAULT_EVAL_NAME)},
    {sql_literal(DEFAULT_DATASET_VERSION)},
    {sql_literal(DEFAULT_PROVIDER)},
    {sql_literal(DEFAULT_MODEL_NAME)},
    {sql_literal(score_text)}::jsonb
where
    {guard}
returning eval_run_id;"""


def render_live_observation_pipeline_run_status_sql(
    *,
    run_id: int,
    status: str,
    database_identity: dict[str, object],
    error_summary: str | None = None,
) -> str:
    run_id = require_positive_int(run_id, field_name="run_id")
    if status not in {"succeeded", "failed"}:
        raise ValueError("status must be succeeded or failed.")
    if status == "succeeded":
        error_sql = "null"
    else:
        error_text = str(error_summary or "live observation failed").strip()[:2000]
        error_sql = sql_literal(error_text or "live observation failed")
    guard = _render_identity_guard_expression(database_identity)
    return f"""update ops.pipeline_run
set
    status = {sql_literal(status)},
    ended_at = now(),
    error_summary = {error_sql}
where run_id = {run_id}
  and {guard}
returning run_id;"""


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
    lineage_id = require_positive_int(
        lineage_eval_run_id,
        field_name="lineage_eval_run_id",
    )
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
    identity_attested = (
        identity.get("complete") is True
        and identity.get("sha256") == expected_sha
    )
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
            write_boundary=_write_boundary(),
        )

    bundle_before = _load_exact_bundle(
        executor=sql_executor,
        as_of_date=as_of_date,
        lineage_eval_run_id=lineage_id,
        feedback_eval_run_id=feedback_id,
        portfolio_name=portfolio_name,
        database_identity=identity,
    )
    foundation_before = (
        build_recommendation_weight_review_prospective_evidence_foundation(
            as_of_date=as_of_date,
            bundle=bundle_before,
            portfolio_name=portfolio_name,
        )
    )
    surface_before = build_legacy_surface_snapshot(
        bundle=bundle_before,
        foundation=foundation_before,
    )
    preflight = (
        build_recommendation_weight_review_prospective_evidence_live_observation(
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
    )
    report = _report(
        as_of_date=as_of_date,
        portfolio_name=portfolio_name,
        environment_label=environment_label,
        execute=execute,
        status="planned" if not execute else "running",
        observation=preflight,
        write_boundary=_write_boundary(),
    )
    if not execute:
        return report

    pipeline_config = {
        "as_of_date": as_of_date.isoformat(),
        "portfolio_name": portfolio_name,
        "environment_label": environment_label,
        "database_identity_sha256": identity.get("sha256"),
        "lineage_eval_run_id": lineage_id,
        "portfolio_feedback_calibration_eval_run_id": feedback_id,
        "legacy_surface_before_sha256": surface_before.get("payload_sha256"),
        "mode": "live_database_append_only_observation",
        "authoritative": False,
        "sql_identity_guard_applied": True,
        "weight_mutation_allowed": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": ORDER_BOUNDARY,
    }
    run_id = int(
        sql_executor.execute_scalar(
            render_live_observation_pipeline_run_insert_sql(
                config_json=pipeline_config,
                database_identity=identity,
            )
        )
    )
    try:
        bundle_after = _load_exact_bundle(
            executor=sql_executor,
            as_of_date=as_of_date,
            lineage_eval_run_id=lineage_id,
            feedback_eval_run_id=feedback_id,
            portfolio_name=portfolio_name,
            database_identity=identity,
        )
        foundation_after = (
            build_recommendation_weight_review_prospective_evidence_foundation(
                as_of_date=as_of_date,
                bundle=bundle_after,
                portfolio_name=portfolio_name,
            )
        )
        surface_after = build_legacy_surface_snapshot(
            bundle=bundle_after,
            foundation=foundation_after,
        )
        observation = (
            build_recommendation_weight_review_prospective_evidence_live_observation(
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
        )
        if _as_dict(observation.get("legacy_surface")).get("unchanged") is not True:
            raise LiveObservationIntegrityError(
                "Legacy recommendation evidence surface changed during live observation."
            )
        eval_run_id = int(
            sql_executor.execute_scalar(
                render_live_observation_eval_insert_sql(
                    score_json=observation,
                    database_identity=identity,
                )
            )
        )
        sql_executor.execute_scalar(
            render_live_observation_pipeline_run_status_sql(
                run_id=run_id,
                status="succeeded",
                database_identity=identity,
            )
        )
    except Exception as exc:
        try:
            sql_executor.execute_scalar(
                render_live_observation_pipeline_run_status_sql(
                    run_id=run_id,
                    status="failed",
                    database_identity=identity,
                    error_summary=str(exc),
                )
            )
        except Exception:
            pass
        raise

    return {
        **report,
        "status": "completed",
        "run_id": run_id,
        "eval_run_id": eval_run_id,
        "write_boundary": _write_boundary(
            pipeline_lifecycle_count=1,
            append_only_eval_count=1,
            sql_write_statement_count=3,
        ),
        "observation": observation,
    }


def _load_exact_bundle(
    *,
    executor: PsqlCommandExecutor,
    as_of_date: date,
    lineage_eval_run_id: int,
    feedback_eval_run_id: int,
    portfolio_name: str,
    database_identity: dict[str, object],
) -> dict[str, object]:
    payload = json.loads(
        executor.execute_scalar(
            render_live_observation_guarded_bundle_lookup_sql(
                as_of_date=as_of_date,
                lineage_eval_run_id=lineage_eval_run_id,
                portfolio_feedback_calibration_eval_run_id=feedback_eval_run_id,
                portfolio_name=portfolio_name,
                database_identity=database_identity,
            )
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Guarded prospective evidence lookup did not return a JSON object.")
    return payload


def _render_identity_guard_block(database_identity: dict[str, object]) -> str:
    expression = _render_identity_guard_expression(database_identity)
    return f"""do $stockanalysis_live_observation_guard$
begin
    if not (
        {expression}
    ) then
        raise exception 'stockanalysis live observation database identity guard failed';
    end if;
end
$stockanalysis_live_observation_guard$;"""


def _render_identity_guard_expression(
    database_identity: dict[str, object],
) -> str:
    identity = _require_complete_database_identity(database_identity)
    conditions = [
        f"current_database() = {sql_literal(str(identity['database_name']))}",
        f"current_user::text = {sql_literal(str(identity['role_name']))}",
        (
            "current_setting('server_version_num') = "
            f"{sql_literal(str(identity['server_version_num']))}"
        ),
        (
            "coalesce(inet_server_addr()::text, '') = "
            f"{sql_literal(str(identity.get('server_address') or ''))}"
        ),
        (
            "coalesce(inet_server_port()::text, '') = "
            f"{sql_literal(str(identity.get('server_port') or ''))}"
        ),
    ]
    conditions.extend(
        f"to_regclass({sql_literal(relation)}) is not null"
        for relation in REQUIRED_RELATIONS
    )
    return "\n    and ".join(conditions)


def _require_complete_database_identity(
    database_identity: dict[str, object],
) -> dict[str, object]:
    if database_identity.get("complete") is not True:
        raise ValueError("database_identity must be complete before rendering guarded SQL.")
    for field_name in ("database_name", "role_name", "server_version_num"):
        if not str(database_identity.get(field_name) or "").strip():
            raise ValueError(f"database_identity.{field_name} must not be empty.")
    return database_identity


def _write_boundary(
    *,
    pipeline_lifecycle_count: int = 0,
    append_only_eval_count: int = 0,
    sql_write_statement_count: int = 0,
) -> dict[str, object]:
    return {
        "pipeline_lifecycle_count": pipeline_lifecycle_count,
        "append_only_eval_count": append_only_eval_count,
        "sql_write_statement_count": sql_write_statement_count,
        "allowed_relations": ["ops.pipeline_run", "ai.eval_run"],
        "legacy_domain_write_count": 0,
        "sql_identity_guard_applied": True,
    }


def _report(
    *,
    as_of_date: date,
    portfolio_name: str,
    environment_label: str,
    execute: bool,
    status: str,
    observation: dict[str, object],
    write_boundary: dict[str, object],
) -> dict[str, object]:
    return {
        "report_name": DEFAULT_EVAL_NAME,
        "status": status,
        "execute": execute,
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "portfolio_name": portfolio_name,
        "environment_label": environment_label,
        "mode": "live_database_append_only_observation",
        "authoritative": False,
        "write_boundary": write_boundary,
        "observation": observation,
    }
