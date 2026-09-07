from __future__ import annotations

import json
from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations import recommendation_quality_eval_legacy as _legacy
from stockanalysis.operations.recommendation_eval_persistence import (
    SNAPSHOT_SCHEMA_VERSION,
    build_recommendation_eval_snapshots,
    render_recommendation_quality_eval_persist_sql,
    render_recommendation_snapshot_projection_sql,
)
from stockanalysis.operations.recommendation_quality_eval_legacy import *  # noqa: F401,F403


# Keep the established evaluator/scoring contract while adding source-state
# persistence around it.  The legacy module is an exact blob copy of the
# pre-persistence implementation, so this wrapper does not silently alter
# recommendation scoring semantics.


def render_recommendation_quality_eval_sql(*, as_of_date: date, horizon_days: int) -> str:
    base_sql = _legacy.render_recommendation_quality_eval_sql(
        as_of_date=as_of_date,
        horizon_days=horizon_days,
    )
    suffix = ")::text;"
    if not base_sql.endswith(suffix):
        raise ValueError("Recommendation quality eval SQL contract changed: final JSON marker missing.")
    projection = render_recommendation_snapshot_projection_sql(
        as_of_date=as_of_date,
        horizon_days=horizon_days,
    )
    return (
        base_sql[: -len(suffix)]
        + ",\n    'recommendation_snapshots',\n        "
        + projection
        + "\n"
        + suffix
    )


def render_recommendation_quality_eval_insert_sql(
    *,
    eval_name: str,
    dataset_version: str,
    provider: str,
    model_name: str,
    score_json: dict[str, object],
    pipeline_run_id: int | None = None,
    as_of_date: date | None = None,
    horizon_days: int | None = None,
    config_json: dict[str, object] | None = None,
    snapshots=(),
) -> str:
    """Render the eval write.

    The optional lineage arguments preserve compatibility for callers that only
    render the historical ai.eval_run insert.  The executed runner below always
    supplies the full lineage and immutable snapshots.
    """
    if pipeline_run_id is None:
        return _legacy.render_recommendation_quality_eval_insert_sql(
            eval_name=eval_name,
            dataset_version=dataset_version,
            provider=provider,
            model_name=model_name,
            score_json=score_json,
        )
    if as_of_date is None or horizon_days is None or config_json is None:
        raise ValueError("Executed recommendation eval persistence requires as_of_date, horizon_days and config_json.")
    return render_recommendation_quality_eval_persist_sql(
        eval_name=eval_name,
        dataset_version=dataset_version,
        provider=provider,
        model_name=model_name,
        score_json=score_json,
        pipeline_run_id=pipeline_run_id,
        as_of_date=as_of_date,
        horizon_days=horizon_days,
        config_json=config_json,
        snapshots=tuple(snapshots),
    )


def load_recommendation_quality_eval_payload(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    horizon_days: int,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_recommendation_quality_eval_sql(
                as_of_date=as_of_date,
                horizon_days=horizon_days,
            )
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Recommendation quality eval lookup did not return a JSON object.")
    return payload


def run_recommendation_quality_eval(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    horizon_days: int,
    min_sample_size: int = _legacy.DEFAULT_MIN_SAMPLE_SIZE,
    min_professional_coverage_rate: float = _legacy.DEFAULT_MIN_PROFESSIONAL_COVERAGE_RATE,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = load_recommendation_quality_eval_payload(
        config=config,
        as_of_date=as_of_date,
        horizon_days=horizon_days,
        executor=sql_executor,
    )
    score = _legacy.score_recommendation_quality_eval_payload(
        payload,
        min_sample_size=min_sample_size,
        min_professional_coverage_rate=min_professional_coverage_rate,
    )
    snapshots = build_recommendation_eval_snapshots(payload)
    report: dict[str, object] = {
        "report_name": "recommendation_quality_calibration",
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": _legacy.DEFAULT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "horizon_days": horizon_days,
        "provider": _legacy.DEFAULT_PROVIDER,
        "model_name": _legacy.DEFAULT_MODEL_NAME,
        "snapshot_schema_version": SNAPSHOT_SCHEMA_VERSION,
        "snapshot_count": len(snapshots),
        "score": score,
    }
    if not execute:
        return report

    execution_config: dict[str, object] = {
        "as_of_date": as_of_date.isoformat(),
        "horizon_days": horizon_days,
        "min_sample_size": min_sample_size,
        "min_professional_coverage_rate": min_professional_coverage_rate,
        "evaluation_only": True,
        "recommendation_scoring_mutated": False,
        "snapshot_schema_version": SNAPSHOT_SCHEMA_VERSION,
        "snapshot_count": len(snapshots),
    }
    run_id = _legacy._create_pipeline_run(
        sql_executor,
        pipeline_name=_legacy.DEFAULT_PIPELINE_NAME,
        config_json=execution_config,
    )
    try:
        eval_run_id = int(
            sql_executor.execute_scalar(
                render_recommendation_quality_eval_insert_sql(
                    eval_name=_legacy.DEFAULT_EVAL_NAME,
                    dataset_version=_legacy.DEFAULT_DATASET_VERSION,
                    provider=_legacy.DEFAULT_PROVIDER,
                    model_name=_legacy.DEFAULT_MODEL_NAME,
                    score_json=score,
                    pipeline_run_id=run_id,
                    as_of_date=as_of_date,
                    horizon_days=horizon_days,
                    config_json=execution_config,
                    snapshots=snapshots,
                )
            )
        )
        _legacy._mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _legacy._mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise
    return {
        **report,
        "status": "completed",
        "run_id": run_id,
        "eval_run_id": eval_run_id,
    }
