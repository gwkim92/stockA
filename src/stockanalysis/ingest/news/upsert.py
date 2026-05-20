from __future__ import annotations

import json

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.news.rss import load_news_rss_sync_result
from stockanalysis.ingest.news.sql import render_news_rss_upsert_sql
from stockanalysis.ingest.psql import PsqlCommandExecutor


def run_news_rss_upsert(
    *,
    feed_name: str,
    feed_url: str,
    config: RuntimeConfig,
    feed_xml_path: str | None = None,
    limit: int | None = None,
    default_language: str | None = "en",
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    result = load_news_rss_sync_result(
        feed_name=feed_name,
        feed_url=feed_url,
        config=config,
        feed_xml_path=feed_xml_path,
        limit=limit,
        default_language=default_language,
    )
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="news_rss_upsert",
        config_json={
            "feed_name": feed_name,
            "feed_url": feed_url,
            "feed_xml_fixture_path": feed_xml_path,
            "limit": limit,
        },
    )
    try:
        upsert_payload = json.loads(
            sql_executor.execute_scalar(
                render_news_rss_upsert_sql(
                    result,
                    ingested_by_run_id=run_id,
                )
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    summary = result.summary()
    summary.update(upsert_payload)
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
    truncated = error_summary.strip()[:2000] or "news RSS upsert failed"
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
