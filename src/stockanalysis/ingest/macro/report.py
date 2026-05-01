from __future__ import annotations

import json

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor


def load_macro_run_history(
    *,
    config: RuntimeConfig,
    executor: PsqlCommandExecutor | None = None,
    limit: int = 20,
    status: str | None = None,
) -> dict[str, object]:
    if limit <= 0:
        raise ValueError("limit must be greater than 0")

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(_render_macro_run_history_sql(limit=limit, status=status))
    return json.loads(payload)


def _render_macro_run_history_sql(*, limit: int, status: str | None) -> str:
    status_filter = ""
    if status:
        status_filter = f"and status = {sql_literal(status)}"

    return f"""with recent_runs as (
    select
        run_id,
        pipeline_name,
        status,
        started_at,
        ended_at,
        error_summary,
        config_json ->> 'series_id' as series_id,
        config_json ->> 'region_code' as region_code,
        config_json ->> 'category' as category
    from ops.pipeline_run
    where run_kind = 'ingest'
      and pipeline_name = 'macro_upsert'
      {status_filter}
    order by started_at desc, run_id desc
    limit {limit}
),
run_observations as (
    select
        o.source_run_id as run_id,
        count(*)::int as observation_count,
        min(o.observation_date) as first_observation_date,
        max(o.observation_date) as last_observation_date
    from macro.observation o
    join recent_runs r on r.run_id = o.source_run_id
    group by o.source_run_id
),
run_series as (
    select
        o.source_run_id as run_id,
        string_agg(distinct s.series_code, ',' order by s.series_code) as loaded_series_codes
    from macro.observation o
    join macro.series s on s.series_id = o.series_id
    join recent_runs r on r.run_id = o.source_run_id
    group by o.source_run_id
),
status_counts as (
    select coalesce(jsonb_object_agg(status, run_count), '{{}}'::jsonb) as counts
    from (
        select status, count(*)::int as run_count
        from recent_runs
        group by status
    ) counted
)
select json_build_object(
    'pipeline_name', 'macro_upsert',
    'limit', {limit},
    'status_filter', {sql_literal(status)},
    'run_count', (select count(*) from recent_runs),
    'status_counts', (select counts from status_counts),
    'runs',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'run_id', r.run_id,
                    'pipeline_name', r.pipeline_name,
                    'status', r.status,
                    'series_id', r.series_id,
                    'loaded_series_codes', rs.loaded_series_codes,
                    'region_code', r.region_code,
                    'category', r.category,
                    'started_at', r.started_at,
                    'ended_at', r.ended_at,
                    'observation_count', coalesce(ro.observation_count, 0),
                    'first_observation_date', ro.first_observation_date,
                    'last_observation_date', ro.last_observation_date,
                    'error_summary', r.error_summary
                )
                order by r.started_at desc, r.run_id desc
            )
            from recent_runs r
            left join run_observations ro using (run_id)
            left join run_series rs using (run_id)
        ),
        '[]'::json
    )
)::text;"""
