from __future__ import annotations

import json

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.ingest.sec.sql import render_sec_filings_upsert_sql
from stockanalysis.ingest.sec.submissions import load_sec_filings_sync_result


def run_sec_filings_upsert(
    cik: str,
    *,
    config: RuntimeConfig,
    submissions_json_path: str | None = None,
    max_filings: int | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    result = load_sec_filings_sync_result(
        cik,
        config=config,
        submissions_json_path=submissions_json_path,
        max_filings=max_filings,
    )
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="sec_filings_upsert",
        config_json={
            "cik": result.cik,
            "company_name": result.company_name,
            "max_filings": max_filings,
            "submissions_fixture_path": submissions_json_path,
        },
    )
    try:
        sql_executor.execute_non_query(
            render_sec_filings_upsert_sql(
                result,
                ingested_by_run_id=run_id,
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    summary = result.summary()
    summary["run_id"] = run_id
    return summary


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
    truncated = error_summary.strip()[:2000] or "sec filings upsert failed"
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
