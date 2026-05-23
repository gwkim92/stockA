from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)

DEFAULT_PIPELINE_NAME = "cycle_graph_context_summary"
SUMMARY_TYPE = "cycle_graph_context_v1"


@dataclass(frozen=True)
class CycleCommunitySummaryRow:
    node_id: int
    node_code: str
    summary_json: dict[str, object]


def render_cycle_graph_context_sql(*, node_code: str, as_of_date: date, limit: int = 12) -> str:
    code = node_code.strip().upper()
    if not code:
        raise ValueError("node_code must not be empty.")
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")
    node_literal = sql_literal(code)
    target_date_sql = sql_date(as_of_date)
    return f"""-- cycle graph context lookup
with target_node as (
    select
        node.node_id,
        node.code,
        node.name,
        node.node_type,
        node.description
    from ref.classification_node node
    where node.taxonomy_family = 'internal_theme'
      and upper(node.code) = upper({node_literal})
      and node.status = 'active'
    limit 1
),
latest_snapshot as (
    select distinct on (snapshot.node_id)
        snapshot.node_id,
        snapshot.as_of_date,
        snapshot.cycle_level,
        snapshot.cycle_state,
        snapshot.cycle_score,
        snapshot.trend_score,
        snapshot.breadth_score,
        snapshot.event_heat_score,
        snapshot.parent_alignment_score,
        snapshot.conflict_flags,
        snapshot.evidence_event_ids
    from signal.cycle_hierarchy_state_snapshot snapshot
    join target_node target on target.node_id = snapshot.node_id
    where snapshot.as_of_date <= {target_date_sql}
    order by snapshot.node_id, snapshot.as_of_date desc
),
parent_edges as (
    select
        parent.node_id,
        parent.code,
        parent.name,
        parent.node_type,
        edge.relation_type,
        edge.weight
    from target_node target
    join ref.classification_edge edge on edge.child_node_id = target.node_id
    join ref.classification_node parent on parent.node_id = edge.parent_node_id
    where edge.valid_from <= {target_date_sql}
      and (edge.valid_to is null or edge.valid_to >= {target_date_sql})
    order by edge.weight desc, parent.code
    limit {limit}
),
child_edges as (
    select
        child.node_id,
        child.code,
        child.name,
        child.node_type,
        edge.relation_type,
        edge.weight
    from target_node target
    join ref.classification_edge edge on edge.parent_node_id = target.node_id
    join ref.classification_node child on child.node_id = edge.child_node_id
    where edge.valid_from <= {target_date_sql}
      and (edge.valid_to is null or edge.valid_to >= {target_date_sql})
    order by edge.weight desc, child.code
    limit {limit}
),
direct_event_rows as (
    select distinct on (event_row.event_id)
        event_row.event_id,
        event_row.title,
        event_row.summary,
        event_row.event_at,
        classification_impact.impact_direction,
        classification_impact.impact_strength,
        classification_impact.confidence,
        classification_impact.rationale,
        document.document_id,
        document.korean_title,
        document.korean_summary,
        document.translation_confidence,
        document.url as source_url
    from target_node target
    join event.event_classification_impact classification_impact
      on classification_impact.node_id = target.node_id
    join event.event event_row on event_row.event_id = classification_impact.event_id
    left join event.event_document_link document_link
      on document_link.event_id = event_row.event_id
     and document_link.link_type = 'source'
    left join ingest.source_document document on document.document_id = document_link.document_id
    where event_row.event_at >= ({target_date_sql} - interval '30 days')
      and event_row.event_at < ({target_date_sql} + interval '1 day')
    order by event_row.event_id, event_row.event_at desc
    limit {limit}
),
propagated_rows as (
    select
        propagated.event_id,
        event_row.title,
        event_row.event_at,
        source_node.code as source_node_code,
        propagated_node.code as propagated_node_code,
        instrument.primary_symbol,
        propagated.impact_direction,
        propagated.impact_strength,
        propagated.confidence,
        propagated.path_depth,
        propagated.path_weight,
        propagated.node_path_codes,
        propagated.rationale
    from target_node target
    join signal.hierarchical_propagated_instrument_impact propagated
      on propagated.source_node_id = target.node_id
      or propagated.propagated_node_id = target.node_id
    join event.event event_row on event_row.event_id = propagated.event_id
    join ref.classification_node source_node on source_node.node_id = propagated.source_node_id
    join ref.classification_node propagated_node on propagated_node.node_id = propagated.propagated_node_id
    join ref.instrument instrument on instrument.instrument_id = propagated.instrument_id
    where event_row.event_at >= ({target_date_sql} - interval '30 days')
      and event_row.event_at < ({target_date_sql} + interval '1 day')
    order by event_row.event_at desc, propagated.confidence desc nulls last, instrument.primary_symbol
    limit {limit}
),
exposed_instruments as (
    select
        instrument.instrument_id,
        instrument.primary_symbol,
        instrument.name,
        exposure.exposure_weight,
        exposure.sensitivity_direction,
        exposure.confidence,
        exposure.rationale,
        'factor_exposure'::text as link_type
    from target_node target
    join ref.instrument_factor_exposure exposure on exposure.node_id = target.node_id
    join ref.instrument instrument on instrument.instrument_id = exposure.instrument_id
    where exposure.valid_from <= {target_date_sql}
      and (exposure.valid_to is null or exposure.valid_to >= {target_date_sql})

    union all

    select
        instrument.instrument_id,
        instrument.primary_symbol,
        instrument.name,
        membership.confidence as exposure_weight,
        'positive'::text as sensitivity_direction,
        membership.confidence,
        membership.membership_type as rationale,
        'classification_membership'::text as link_type
    from target_node target
    join ref.instrument_classification_membership membership on membership.node_id = target.node_id
    join ref.instrument instrument on instrument.instrument_id = membership.instrument_id
    where membership.valid_from <= {target_date_sql}
      and (membership.valid_to is null or membership.valid_to >= {target_date_sql})
    order by exposure_weight desc nulls last, primary_symbol
    limit {limit}
),
recent_ai_artifacts as (
    select
        artifact.artifact_id,
        artifact.artifact_type,
        artifact.event_id,
        artifact.document_id,
        artifact.confidence,
        invocation.provider,
        invocation.model_name,
        invocation.status,
        artifact.created_at
    from ai.extraction_artifact artifact
    join ai.model_invocation invocation on invocation.invocation_id = artifact.invocation_id
    where artifact.event_id in (select event_id from direct_event_rows)
       or artifact.event_id in (select event_id from propagated_rows)
       or artifact.document_id in (select document_id from direct_event_rows where document_id is not null)
    order by artifact.created_at desc, artifact.artifact_id desc
    limit {limit}
),
linked_recommendations as (
    select
        recommendation.recommendation_id,
        batch.as_of_date,
        instrument.primary_symbol,
        recommendation.action,
        recommendation.bucket,
        recommendation.total_score,
        recommendation.thesis_id
    from exposed_instruments exposed
    join signal.recommendation recommendation on recommendation.instrument_id = exposed.instrument_id
    join signal.recommendation_batch batch on batch.batch_id = recommendation.batch_id
    join ref.instrument instrument on instrument.instrument_id = recommendation.instrument_id
    where batch.as_of_date <= {target_date_sql}
    order by batch.as_of_date desc, recommendation.total_score desc, instrument.primary_symbol
    limit {limit}
),
linked_theses as (
    select
        thesis.thesis_id,
        instrument.primary_symbol,
        thesis.title,
        thesis.status,
        thesis.conviction_score,
        thesis.invalidation_conditions
    from exposed_instruments exposed
    join signal.investment_thesis thesis on thesis.instrument_id = exposed.instrument_id
    join ref.instrument instrument on instrument.instrument_id = thesis.instrument_id
    where thesis.created_at < ({target_date_sql} + interval '1 day')
      and (thesis.closed_at is null or thesis.closed_at >= {target_date_sql})
    order by thesis.created_at desc, thesis.thesis_id desc
    limit {limit}
),
previous_summary as (
    select
        summary.summary_json,
        summary.as_of_date
    from target_node target
    join ai.cycle_community_summary summary on summary.node_id = target.node_id
    where summary.summary_type = {sql_literal(SUMMARY_TYPE)}
      and summary.as_of_date < {target_date_sql}
    order by summary.as_of_date desc
    limit 1
)
select json_build_object(
    'query',
    json_build_object(
        'node_code', {node_literal},
        'as_of_date', {sql_literal(as_of_date.isoformat())},
        'limit', {limit}
    ),
    'target_node', (select row_to_json(target_node) from target_node),
    'latest_snapshot', (select row_to_json(latest_snapshot) from latest_snapshot),
    'parent_edges', coalesce((select json_agg(row_to_json(parent_edges)) from parent_edges), '[]'::json),
    'child_edges', coalesce((select json_agg(row_to_json(child_edges)) from child_edges), '[]'::json),
    'direct_events', coalesce((select json_agg(row_to_json(direct_event_rows)) from direct_event_rows), '[]'::json),
    'propagated_impacts', coalesce((select json_agg(row_to_json(propagated_rows)) from propagated_rows), '[]'::json),
    'exposed_instruments', coalesce((select json_agg(row_to_json(exposed_instruments)) from exposed_instruments), '[]'::json),
    'ai_artifacts', coalesce((select json_agg(row_to_json(recent_ai_artifacts)) from recent_ai_artifacts), '[]'::json),
    'recommendations', coalesce((select json_agg(row_to_json(linked_recommendations)) from linked_recommendations), '[]'::json),
    'theses', coalesce((select json_agg(row_to_json(linked_theses)) from linked_theses), '[]'::json),
    'previous_summary', (select row_to_json(previous_summary) from previous_summary)
)::text;"""


def render_cycle_graph_context_node_codes_sql(*, as_of_date: date, limit: int = 50) -> str:
    if limit < 1 or limit > 200:
        raise ValueError("limit must be between 1 and 200.")
    return f"""-- cycle graph context node code lookup
with ranked_nodes as (
    select
        node.code,
        coalesce(snapshot.cycle_score, 0) as cycle_score,
        coalesce(snapshot.event_heat_score, 0) as event_heat_score
    from ref.classification_node node
    left join signal.cycle_hierarchy_state_snapshot snapshot
      on snapshot.node_id = node.node_id
     and snapshot.as_of_date = {sql_date(as_of_date)}
    where node.taxonomy_family = 'internal_theme'
      and node.status = 'active'
)
select coalesce(
    json_agg(code order by cycle_score desc, event_heat_score desc, code),
    '[]'::json
)::text
from (
    select code, cycle_score, event_heat_score
    from ranked_nodes
    order by cycle_score desc, event_heat_score desc, code
    limit {limit}
) selected_nodes;"""


def load_cycle_graph_context(
    *,
    config: RuntimeConfig,
    node_code: str,
    as_of_date: date,
    limit: int = 12,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_cycle_graph_context_sql(node_code=node_code, as_of_date=as_of_date, limit=limit)
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Cycle graph context lookup did not return a JSON object.")
    if not isinstance(payload.get("target_node"), dict):
        raise ValueError(f"Cycle graph context target node `{node_code}` was not found.")
    return payload


def load_cycle_graph_context_node_codes(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    limit: int = 50,
    executor: PsqlCommandExecutor | None = None,
) -> tuple[str, ...]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(sql_executor.execute_scalar(render_cycle_graph_context_node_codes_sql(as_of_date=as_of_date, limit=limit)))
    if not isinstance(payload, list):
        raise ValueError("Cycle graph context node code lookup did not return a JSON array.")
    return tuple(str(code).upper() for code in payload if str(code).strip())


def build_cycle_community_summary(context: dict[str, object]) -> CycleCommunitySummaryRow:
    target_node = _as_dict(context.get("target_node"))
    snapshot = _as_dict(context.get("latest_snapshot"))
    if not target_node:
        raise ValueError("Cycle graph context cannot be summarized without a target_node.")
    node_id = int(target_node["node_id"])
    node_code = str(target_node["code"]).upper()
    direct_events = _as_list(context.get("direct_events"))
    propagated_impacts = _as_list(context.get("propagated_impacts"))
    exposed_instruments = _as_list(context.get("exposed_instruments"))
    ai_artifacts = _as_list(context.get("ai_artifacts"))
    recommendations = _as_list(context.get("recommendations"))
    theses = _as_list(context.get("theses"))
    parent_edges = _as_list(context.get("parent_edges"))
    child_edges = _as_list(context.get("child_edges"))
    as_of_date = _as_dict(context.get("query")).get("as_of_date")
    cycle_state = str(snapshot.get("cycle_state") or "unknown")
    cycle_score = _optional_text(snapshot.get("cycle_score"))
    event_titles = _unique_strings(
        [_best_event_title(row) for row in direct_events]
        + [_best_event_title(row) for row in propagated_impacts]
    )[:5]
    symbols = _unique_strings(
        [str(row.get("primary_symbol") or "") for row in exposed_instruments]
        + [str(row.get("primary_symbol") or "") for row in propagated_impacts]
        + [str(row.get("primary_symbol") or "") for row in recommendations]
    )[:10]
    summary_text = _render_korean_summary(
        node_code=node_code,
        cycle_state=cycle_state,
        cycle_score=cycle_score,
        direct_event_count=len(direct_events),
        propagated_impact_count=len(propagated_impacts),
        instrument_count=len(symbols),
    )
    summary_json: dict[str, object] = {
        "summary_type": SUMMARY_TYPE,
        "as_of_date": as_of_date,
        "node": {
            "node_id": node_id,
            "code": node_code,
            "name": target_node.get("name"),
            "node_type": target_node.get("node_type"),
        },
        "cycle_state": cycle_state,
        "cycle_score": cycle_score,
        "cycle_level": snapshot.get("cycle_level") or "unknown",
        "event_heat_score": _optional_text(snapshot.get("event_heat_score")),
        "parent_alignment_score": _optional_text(snapshot.get("parent_alignment_score")),
        "counts": {
            "parent_edge_count": len(parent_edges),
            "child_edge_count": len(child_edges),
            "direct_event_count": len(direct_events),
            "propagated_impact_count": len(propagated_impacts),
            "exposed_instrument_count": len(exposed_instruments),
            "ai_artifact_count": len(ai_artifacts),
            "recommendation_count": len(recommendations),
            "thesis_count": len(theses),
        },
        "parent_codes": _unique_strings(str(row.get("code") or "") for row in parent_edges)[:10],
        "child_codes": _unique_strings(str(row.get("code") or "") for row in child_edges)[:10],
        "top_symbols": symbols,
        "recent_event_titles": event_titles,
        "summary_text_ko": summary_text,
        "generation_method": "postgres_graph_context_v1",
        "llm_used": False,
    }
    return CycleCommunitySummaryRow(node_id=node_id, node_code=node_code, summary_json=summary_json)


def render_cycle_community_summary_upsert_sql(
    rows: tuple[CycleCommunitySummaryRow, ...],
    *,
    as_of_date: date,
    source_run_id: int,
) -> str:
    if not rows:
        raise ValueError("At least one cycle community summary row is required.")
    value_rows = ",\n        ".join(_render_summary_value_tuple(row, as_of_date=as_of_date, source_run_id=source_run_id) for row in rows)
    return f"""insert into ai.cycle_community_summary (
    node_id,
    as_of_date,
    summary_type,
    summary_json,
    source_run_id
)
values
        {value_rows}
on conflict (node_id, as_of_date, summary_type) do update
set
    summary_json = excluded.summary_json,
    source_run_id = excluded.source_run_id,
    updated_at = now();"""


def run_cycle_graph_context_summary(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    node_codes: Iterable[str] = (),
    limit: int = 12,
    max_nodes: int = 50,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")
    if max_nodes < 1 or max_nodes > 200:
        raise ValueError("max_nodes must be between 1 and 200.")
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    selected_codes = _normalize_node_codes(node_codes)
    if not selected_codes:
        selected_codes = load_cycle_graph_context_node_codes(
            config=config,
            as_of_date=as_of_date,
            limit=max_nodes,
            executor=sql_executor,
        )
    contexts = tuple(
        load_cycle_graph_context(
            config=config,
            node_code=node_code,
            as_of_date=as_of_date,
            limit=limit,
            executor=sql_executor,
        )
        for node_code in selected_codes[:max_nodes]
    )
    summaries = tuple(build_cycle_community_summary(context) for context in contexts)
    base_report: dict[str, object] = {
        "report_name": "cycle_graph_context_summary",
        "status": "planned" if not execute else "running",
        "execute": execute,
        "as_of_date": as_of_date.isoformat(),
        "summary_type": SUMMARY_TYPE,
        "node_count": len(summaries),
        "node_code_preview": [row.node_code for row in summaries[:10]],
        "summary_preview": [row.summary_json for row in summaries[:3]],
    }
    if not execute:
        return base_report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "summary_type": SUMMARY_TYPE,
            "node_count": len(summaries),
            "limit": limit,
            "max_nodes": max_nodes,
        },
    )
    try:
        sql_executor.execute_non_query(
            render_cycle_community_summary_upsert_sql(
                summaries,
                as_of_date=as_of_date,
                source_run_id=run_id,
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise
    return {
        **base_report,
        "status": "completed",
        "run_id": run_id,
    }


def _render_summary_value_tuple(
    row: CycleCommunitySummaryRow,
    *,
    as_of_date: date,
    source_run_id: int,
) -> str:
    summary_json = json.dumps(row.summary_json, ensure_ascii=False, sort_keys=True)
    return "(" + ", ".join(
        (
            f"{row.node_id}::bigint",
            sql_date(as_of_date),
            sql_literal(SUMMARY_TYPE),
            f"{sql_literal(summary_json)}::jsonb",
            f"{source_run_id}::bigint",
        )
    ) + ")"


def _normalize_node_codes(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    codes: list[str] = []
    for value in values:
        code = str(value).strip().upper()
        if not code or code in seen:
            continue
        seen.add(code)
        codes.append(code)
    return tuple(codes)


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value)
    text = str(value).strip()
    return text or None


def _best_event_title(row: dict[str, object]) -> str:
    return str(row.get("korean_title") or row.get("title") or "").strip()


def _unique_strings(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _render_korean_summary(
    *,
    node_code: str,
    cycle_state: str,
    cycle_score: str | None,
    direct_event_count: int,
    propagated_impact_count: int,
    instrument_count: int,
) -> str:
    score_part = f", 점수 {cycle_score}" if cycle_score else ""
    return (
        f"{node_code} 흐름은 현재 {cycle_state}{score_part} 상태다. "
        f"최근 직접 뉴스 {direct_event_count}건, 전파 영향 {propagated_impact_count}건, "
        f"연결 종목 {instrument_count}개를 근거로 다음 AI/추천 context에 제공된다."
    )
