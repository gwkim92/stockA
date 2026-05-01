from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.defaults import get_default_series, list_default_series
from stockanalysis.ingest.macro.fred import load_macro_sync_result
from stockanalysis.ingest.macro.models import MacroSeriesSpec
from stockanalysis.ingest.macro.sql import render_macro_sync_sql, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor


def run_macro_upsert(
    spec: MacroSeriesSpec,
    *,
    config: RuntimeConfig,
    series_json_path: str | None = None,
    observations_json_path: str | None = None,
    observation_start: str | None = None,
    observation_end: str | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    result = load_macro_sync_result(
        spec,
        config=config,
        series_json_path=series_json_path,
        observations_json_path=observations_json_path,
        observation_start=observation_start,
        observation_end=observation_end,
    )
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="macro_upsert",
        config_json={
            "series_id": spec.series_id,
            "region_code": spec.region_code,
            "category": spec.category,
            "observation_start": observation_start,
            "observation_end": observation_end,
            "series_fixture_path": series_json_path,
            "observations_fixture_path": observations_json_path,
        },
    )
    try:
        sql_executor.execute_non_query(
            render_macro_sync_sql(
                result,
                source_run_id=run_id,
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    summary = result.summary()
    summary["run_id"] = run_id
    return summary


def run_macro_batch_upsert(
    specs: Iterable[MacroSeriesSpec],
    *,
    config: RuntimeConfig,
    fixtures_dir: str | None = None,
    observation_start: str | None = None,
    observation_end: str | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    requested_specs = tuple(specs)
    results: list[dict[str, object]] = []
    succeeded = 0
    failed = 0
    total_observations = 0

    for spec in requested_specs:
        series_json_path, observations_json_path = _resolve_fixture_paths(spec, fixtures_dir)
        try:
            summary = run_macro_upsert(
                spec,
                config=config,
                series_json_path=series_json_path,
                observations_json_path=observations_json_path,
                observation_start=observation_start,
                observation_end=observation_end,
                executor=sql_executor,
            )
        except Exception as exc:
            failed += 1
            results.append(
                {
                    "series_id": spec.series_id,
                    "status": "failed",
                    "error": str(exc),
                }
            )
            continue

        succeeded += 1
        total_observations += int(summary["observation_count"])
        results.append(
            {
                "series_id": spec.series_id,
                "status": "succeeded",
                **summary,
            }
        )

    return {
        "requested_series_count": len(requested_specs),
        "succeeded_series_count": succeeded,
        "failed_series_count": failed,
        "total_observation_count": total_observations,
        "results": results,
    }


def resolve_default_macro_specs(series_ids: list[str] | None = None) -> tuple[MacroSeriesSpec, ...]:
    if not series_ids:
        return list_default_series()

    resolved: list[MacroSeriesSpec] = []
    for series_id in series_ids:
        spec = get_default_series(series_id)
        if spec is None:
            raise ValueError(f"Unknown default macro series `{series_id}`.")
        resolved.append(spec)
    return tuple(resolved)


def _create_pipeline_run(
    executor: PsqlCommandExecutor,
    *,
    pipeline_name: str,
    config_json: dict[str, object],
) -> int:
    payload = json.dumps(config_json, ensure_ascii=False, sort_keys=True)
    sql = f"""insert into ops.pipeline_run (
    run_kind,
    pipeline_name,
    status,
    config_json
)
values (
    'ingest',
    {sql_literal(pipeline_name)},
    'running',
    {sql_literal(payload)}::jsonb
)
returning run_id;"""
    return int(executor.execute_scalar(sql))


def _mark_pipeline_run_succeeded(executor: PsqlCommandExecutor, run_id: int) -> None:
    executor.execute_non_query(
        f"""update ops.pipeline_run
set
    status = 'succeeded',
    ended_at = now(),
    error_summary = null
where run_id = {run_id};"""
    )


def _mark_pipeline_run_failed(executor: PsqlCommandExecutor, run_id: int, error_summary: str) -> None:
    truncated = error_summary.strip()[:2000] or "macro upsert failed"
    try:
        executor.execute_non_query(
            f"""update ops.pipeline_run
set
    status = 'failed',
    ended_at = now(),
    error_summary = {sql_literal(truncated)}
where run_id = {run_id};"""
        )
    except Exception:
        return


def _resolve_fixture_paths(spec: MacroSeriesSpec, fixtures_dir: str | None) -> tuple[str | None, str | None]:
    if not fixtures_dir:
        return None, None

    base_dir = Path(fixtures_dir)
    series_path = base_dir / f"fred_series_{spec.series_id}.json"
    observations_path = base_dir / f"fred_observations_{spec.series_id}.json"
    if not series_path.exists():
        raise FileNotFoundError(f"Missing fixture file: {series_path}")
    if not observations_path.exists():
        raise FileNotFoundError(f"Missing fixture file: {observations_path}")
    return str(series_path), str(observations_path)
