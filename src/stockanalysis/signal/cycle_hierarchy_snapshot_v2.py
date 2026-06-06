from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal, sql_numeric
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)

DEFAULT_PIPELINE_NAME = "cycle_hierarchy_snapshot_v2"
_DECIMAL_QUANTIZER = Decimal("0.0001")
_HYSTERESIS_BAND = Decimal("0.0800")


@dataclass(frozen=True)
class CycleHierarchyNodeInput:
    node_id: int
    node_code: str
    node_name: str
    node_type: str
    base_cycle_state: str | None
    base_cycle_score: Decimal | None
    trend_score: Decimal | None
    breadth_score: Decimal | None
    liquidity_score: Decimal | None
    valuation_pressure: Decimal | None
    parent_average_cycle_score: Decimal | None
    direct_event_count_30d: int
    hierarchical_event_count_30d: int
    average_event_confidence: Decimal | None
    previous_cycle_state: str | None
    previous_cycle_score: Decimal | None
    evidence_event_ids: tuple[int, ...]


@dataclass(frozen=True)
class CycleHierarchySnapshotRow:
    node_id: int
    node_code: str
    node_name: str
    cycle_level: str
    cycle_state: str
    cycle_score: Decimal
    trend_score: Decimal
    breadth_score: Decimal
    event_heat_score: Decimal
    liquidity_score: Decimal
    valuation_pressure: Decimal
    parent_alignment_score: Decimal
    conflict_flags: tuple[str, ...]
    evidence_event_ids: tuple[int, ...]
    evidence_json: dict[str, object]


@dataclass(frozen=True)
class CycleHierarchyTransitionRow:
    node_id: int
    from_state: str
    to_state: str
    drivers: tuple[str, ...]
    evidence_event_ids: tuple[int, ...]


def load_cycle_hierarchy_snapshot_inputs(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    executor: PsqlCommandExecutor | None = None,
) -> tuple[CycleHierarchyNodeInput, ...]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload_text = sql_executor.execute_scalar(
        render_cycle_hierarchy_snapshot_input_lookup_sql(as_of_date=as_of_date)
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Cycle hierarchy snapshot lookup did not return a JSON array.")

    rows: list[CycleHierarchyNodeInput] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Cycle hierarchy snapshot lookup returned a non-object row.")
        raw_event_ids = item.get("evidence_event_ids") or []
        if not isinstance(raw_event_ids, list):
            raw_event_ids = []
        rows.append(
            CycleHierarchyNodeInput(
                node_id=int(item["node_id"]),
                node_code=str(item["node_code"]),
                node_name=str(item.get("node_name") or item["node_code"]),
                node_type=str(item.get("node_type") or "unknown"),
                base_cycle_state=_optional_text(item.get("base_cycle_state")),
                base_cycle_score=_optional_decimal(item.get("base_cycle_score")),
                trend_score=_optional_decimal(item.get("trend_score")),
                breadth_score=_optional_decimal(item.get("breadth_score")),
                liquidity_score=_optional_decimal(item.get("liquidity_score")),
                valuation_pressure=_optional_decimal(item.get("valuation_pressure")),
                parent_average_cycle_score=_optional_decimal(item.get("parent_average_cycle_score")),
                direct_event_count_30d=int(item.get("direct_event_count_30d") or 0),
                hierarchical_event_count_30d=int(item.get("hierarchical_event_count_30d") or 0),
                average_event_confidence=_optional_decimal(item.get("average_event_confidence")),
                previous_cycle_state=_optional_text(item.get("previous_cycle_state")),
                previous_cycle_score=_optional_decimal(item.get("previous_cycle_score")),
                evidence_event_ids=tuple(int(event_id) for event_id in raw_event_ids),
            )
        )
    if not rows:
        raise ValueError("No active internal classification nodes are available for cycle hierarchy snapshot v2.")
    return tuple(rows)


def render_cycle_hierarchy_snapshot_input_lookup_sql(*, as_of_date: date) -> str:
    return f"""-- cycle hierarchy snapshot v2 input lookup
with active_nodes as (
    select
        node.node_id,
        node.code as node_code,
        node.name as node_name,
        node.node_type
    from ref.classification_node node
    where node.taxonomy_family = 'internal_theme'
      and node.status = 'active'
),
base_cycle_snapshot as (
    select distinct on (snapshot.node_id)
        snapshot.node_id,
        snapshot.cycle_state,
        snapshot.cycle_score,
        snapshot.trend_score,
        snapshot.breadth_score,
        snapshot.liquidity_score,
        snapshot.valuation_score
    from signal.cycle_state_snapshot snapshot
    where snapshot.as_of_date <= {sql_date(as_of_date)}
    order by snapshot.node_id, snapshot.as_of_date desc
),
previous_v2_snapshot as (
    select distinct on (snapshot.node_id)
        snapshot.node_id,
        snapshot.cycle_state,
        snapshot.cycle_score
    from signal.cycle_hierarchy_state_snapshot snapshot
    where snapshot.as_of_date < {sql_date(as_of_date)}
    order by snapshot.node_id, snapshot.as_of_date desc
),
parent_scores as (
    select
        edge.child_node_id as node_id,
        avg(coalesce(parent_v2.cycle_score, parent_base.cycle_score))::numeric(18,8) as parent_average_cycle_score
    from ref.classification_edge edge
    left join signal.cycle_hierarchy_state_snapshot parent_v2
      on parent_v2.node_id = edge.parent_node_id
     and parent_v2.as_of_date = {sql_date(as_of_date)}
    left join base_cycle_snapshot parent_base on parent_base.node_id = edge.parent_node_id
    where edge.valid_from <= {sql_date(as_of_date)}
      and (edge.valid_to is null or edge.valid_to >= {sql_date(as_of_date)})
    group by edge.child_node_id
),
direct_event_rows as (
    select
        impact.node_id,
        event_row.event_id,
        least(coalesce(impact.confidence, 1.0), coalesce(event_row.confidence, 1.0)) as confidence
    from event.event_classification_impact impact
    join event.event event_row on event_row.event_id = impact.event_id
    where event_row.event_at >= ({sql_date(as_of_date)} - interval '30 days')
      and event_row.event_at < ({sql_date(as_of_date)} + interval '1 day')
),
hierarchical_event_rows as (
    select
        impact.propagated_node_id as node_id,
        impact.event_id,
        coalesce(impact.confidence, 1.0) as confidence
    from signal.hierarchical_propagated_instrument_impact impact
    join event.event event_row on event_row.event_id = impact.event_id
    where event_row.event_at >= ({sql_date(as_of_date)} - interval '30 days')
      and event_row.event_at < ({sql_date(as_of_date)} + interval '1 day')
      and coalesce(impact.confidence, 0) >= 0.3500
      and coalesce(impact.impact_strength, 0) >= 0.0500
      and coalesce(impact.path_weight, 0) >= 0.100000
),
event_rows as (
    select node_id, event_id, confidence, 'direct'::text as source_kind from direct_event_rows
    union all
    select node_id, event_id, confidence, 'hierarchical'::text as source_kind from hierarchical_event_rows
),
event_agg as (
    select
        node_id,
        count(distinct event_id) filter (where source_kind = 'direct')::integer as direct_event_count_30d,
        count(distinct event_id) filter (where source_kind = 'hierarchical')::integer as hierarchical_event_count_30d,
        avg(confidence)::numeric(18,8) as average_event_confidence,
        array_agg(distinct event_id order by event_id) as evidence_event_ids
    from event_rows
    group by node_id
)
select coalesce(
    json_agg(
        json_build_object(
            'node_id', node.node_id,
            'node_code', node.node_code,
            'node_name', node.node_name,
            'node_type', node.node_type,
            'base_cycle_state', base.cycle_state,
            'base_cycle_score', base.cycle_score,
            'trend_score', base.trend_score,
            'breadth_score', base.breadth_score,
            'liquidity_score', base.liquidity_score,
            'valuation_pressure', base.valuation_score,
            'parent_average_cycle_score', parent_scores.parent_average_cycle_score,
            'direct_event_count_30d', coalesce(events.direct_event_count_30d, 0),
            'hierarchical_event_count_30d', coalesce(events.hierarchical_event_count_30d, 0),
            'average_event_confidence', events.average_event_confidence,
            'previous_cycle_state', previous.cycle_state,
            'previous_cycle_score', previous.cycle_score,
            'evidence_event_ids', coalesce(events.evidence_event_ids, array[]::bigint[])
        )
        order by node.node_code
    ),
    '[]'::json
)::text
from active_nodes node
left join base_cycle_snapshot base on base.node_id = node.node_id
left join parent_scores on parent_scores.node_id = node.node_id
left join event_agg events on events.node_id = node.node_id
left join previous_v2_snapshot previous on previous.node_id = node.node_id;"""


def compute_cycle_hierarchy_snapshots(
    rows: tuple[CycleHierarchyNodeInput, ...],
) -> tuple[CycleHierarchySnapshotRow, ...]:
    snapshots: list[CycleHierarchySnapshotRow] = []
    for row in rows:
        cycle_level = _cycle_level(row.node_type, row.node_code)
        trend_score = _score_or_default(row.trend_score, Decimal("0.5000"))
        breadth_score = _score_or_default(row.breadth_score, Decimal("0.5000"))
        liquidity_score = _score_or_default(row.liquidity_score, Decimal("0.5000"))
        valuation_pressure = _score_or_default(row.valuation_pressure, Decimal("0.5000"))
        event_heat_score = _event_heat_score(
            direct_count=row.direct_event_count_30d,
            hierarchical_count=row.hierarchical_event_count_30d,
            average_confidence=row.average_event_confidence,
        )
        parent_alignment_score = _score_or_default(row.parent_average_cycle_score, Decimal("0.5000"))
        raw_cycle_score = _quantize(
            _clamp(
                trend_score * Decimal("0.3000")
                + breadth_score * Decimal("0.1500")
                + event_heat_score * Decimal("0.3000")
                + parent_alignment_score * Decimal("0.1500")
                + (Decimal("1.0000") - valuation_pressure) * Decimal("0.1000")
            )
        )
        raw_state = _state_from_score(raw_cycle_score)
        conflict_flags: list[str] = []
        cycle_state = raw_state
        if row.previous_cycle_state and row.previous_cycle_score is not None:
            score_delta = abs(raw_cycle_score - row.previous_cycle_score)
            if raw_state != row.previous_cycle_state and score_delta < _HYSTERESIS_BAND:
                cycle_state = row.previous_cycle_state
                conflict_flags.append("hysteresis_hold")
        if row.direct_event_count_30d == 0 and row.hierarchical_event_count_30d > 0:
            conflict_flags.append("propagated_only")
        if row.base_cycle_score is None:
            conflict_flags.append("base_cycle_missing")
        snapshots.append(
            CycleHierarchySnapshotRow(
                node_id=row.node_id,
                node_code=row.node_code,
                node_name=row.node_name,
                cycle_level=cycle_level,
                cycle_state=cycle_state,
                cycle_score=raw_cycle_score,
                trend_score=trend_score,
                breadth_score=breadth_score,
                event_heat_score=event_heat_score,
                liquidity_score=liquidity_score,
                valuation_pressure=valuation_pressure,
                parent_alignment_score=parent_alignment_score,
                conflict_flags=tuple(conflict_flags),
                evidence_event_ids=row.evidence_event_ids[:30],
                evidence_json={
                    "node_code": row.node_code,
                    "base_cycle_state": row.base_cycle_state,
                    "base_cycle_score": _decimal_text(row.base_cycle_score),
                    "direct_event_count_30d": row.direct_event_count_30d,
                    "hierarchical_event_count_30d": row.hierarchical_event_count_30d,
                    "average_event_confidence": _decimal_text(row.average_event_confidence),
                    "previous_cycle_state": row.previous_cycle_state,
                    "previous_cycle_score": _decimal_text(row.previous_cycle_score),
                    "score_model": "cycle-hierarchy-v2-bootstrap",
                },
            )
        )
    return tuple(snapshots)


def compute_cycle_hierarchy_transitions(
    inputs: tuple[CycleHierarchyNodeInput, ...],
    snapshots: tuple[CycleHierarchySnapshotRow, ...],
) -> tuple[CycleHierarchyTransitionRow, ...]:
    inputs_by_node = {row.node_id: row for row in inputs}
    transitions: list[CycleHierarchyTransitionRow] = []
    for snapshot in snapshots:
        source = inputs_by_node[snapshot.node_id]
        if not source.previous_cycle_state or source.previous_cycle_state == snapshot.cycle_state:
            continue
        transitions.append(
            CycleHierarchyTransitionRow(
                node_id=snapshot.node_id,
                from_state=source.previous_cycle_state,
                to_state=snapshot.cycle_state,
                drivers=tuple(snapshot.conflict_flags) or ("score_threshold_crossed",),
                evidence_event_ids=snapshot.evidence_event_ids,
            )
        )
    return tuple(transitions)


def render_cycle_hierarchy_snapshot_upsert_sql(
    rows: tuple[CycleHierarchySnapshotRow, ...],
    *,
    as_of_date: date,
    source_run_id: int,
) -> str:
    if not rows:
        raise ValueError("At least one cycle hierarchy snapshot row is required.")
    value_rows = ",\n        ".join(_render_snapshot_value_tuple(row, as_of_date=as_of_date, source_run_id=source_run_id) for row in rows)
    return f"""insert into signal.cycle_hierarchy_state_snapshot (
    node_id,
    as_of_date,
    cycle_level,
    cycle_state,
    cycle_score,
    trend_score,
    breadth_score,
    event_heat_score,
    liquidity_score,
    valuation_pressure,
    parent_alignment_score,
    conflict_flags,
    evidence_event_ids,
    evidence_json,
    source_run_id
)
values
        {value_rows}
on conflict (node_id, as_of_date) do update
set
    cycle_level = excluded.cycle_level,
    cycle_state = excluded.cycle_state,
    cycle_score = excluded.cycle_score,
    trend_score = excluded.trend_score,
    breadth_score = excluded.breadth_score,
    event_heat_score = excluded.event_heat_score,
    liquidity_score = excluded.liquidity_score,
    valuation_pressure = excluded.valuation_pressure,
    parent_alignment_score = excluded.parent_alignment_score,
    conflict_flags = excluded.conflict_flags,
    evidence_event_ids = excluded.evidence_event_ids,
    evidence_json = excluded.evidence_json,
    source_run_id = excluded.source_run_id,
    updated_at = now();"""


def render_cycle_hierarchy_transition_insert_sql(
    rows: tuple[CycleHierarchyTransitionRow, ...],
    *,
    as_of_date: date,
    source_run_id: int,
) -> str:
    if not rows:
        raise ValueError("At least one cycle hierarchy transition row is required.")
    value_rows = ",\n        ".join(_render_transition_value_tuple(row, as_of_date=as_of_date, source_run_id=source_run_id) for row in rows)
    return f"""insert into signal.cycle_hierarchy_transition_log (
    node_id,
    as_of_date,
    from_state,
    to_state,
    drivers,
    evidence_event_ids,
    source_run_id
)
values
        {value_rows}
on conflict (node_id, as_of_date, from_state, to_state) do update
set
    drivers = excluded.drivers,
    evidence_event_ids = excluded.evidence_event_ids,
    source_run_id = excluded.source_run_id;"""


def run_cycle_hierarchy_snapshot_v2(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    inputs = load_cycle_hierarchy_snapshot_inputs(
        config=config,
        as_of_date=as_of_date,
        executor=sql_executor,
    )
    snapshots = compute_cycle_hierarchy_snapshots(inputs)
    transitions = compute_cycle_hierarchy_transitions(inputs, snapshots)
    base_report: dict[str, object] = {
        "report_name": "cycle_hierarchy_snapshot_v2",
        "status": "planned" if not execute else "running",
        "execute": execute,
        "as_of_date": as_of_date.isoformat(),
        "node_count": len(snapshots),
        "transition_count": len(transitions),
        "cycle_state_counts": _state_counts(snapshots),
        "node_code_preview": [row.node_code for row in snapshots[:10]],
    }
    if not execute:
        return base_report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "node_count": len(snapshots),
            "transition_count": len(transitions),
        },
    )
    try:
        sql_executor.execute_non_query(
            render_cycle_hierarchy_snapshot_upsert_sql(
                snapshots,
                as_of_date=as_of_date,
                source_run_id=run_id,
            )
        )
        if transitions:
            sql_executor.execute_non_query(
                render_cycle_hierarchy_transition_insert_sql(
                    transitions,
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


def _render_snapshot_value_tuple(
    row: CycleHierarchySnapshotRow,
    *,
    as_of_date: date,
    source_run_id: int,
) -> str:
    conflict_flags = json.dumps(list(row.conflict_flags), ensure_ascii=False)
    evidence_event_ids = json.dumps(list(row.evidence_event_ids), ensure_ascii=False)
    evidence_json = json.dumps(row.evidence_json, ensure_ascii=False, sort_keys=True)
    return "(" + ", ".join(
        (
            f"{row.node_id}::bigint",
            sql_date(as_of_date),
            sql_literal(row.cycle_level),
            sql_literal(row.cycle_state),
            sql_numeric(row.cycle_score),
            sql_numeric(row.trend_score),
            sql_numeric(row.breadth_score),
            sql_numeric(row.event_heat_score),
            sql_numeric(row.liquidity_score),
            sql_numeric(row.valuation_pressure),
            sql_numeric(row.parent_alignment_score),
            f"{sql_literal(conflict_flags)}::jsonb",
            f"{sql_literal(evidence_event_ids)}::jsonb",
            f"{sql_literal(evidence_json)}::jsonb",
            f"{source_run_id}::bigint",
        )
    ) + ")"


def _render_transition_value_tuple(
    row: CycleHierarchyTransitionRow,
    *,
    as_of_date: date,
    source_run_id: int,
) -> str:
    drivers = json.dumps(list(row.drivers), ensure_ascii=False)
    evidence_event_ids = json.dumps(list(row.evidence_event_ids), ensure_ascii=False)
    return "(" + ", ".join(
        (
            f"{row.node_id}::bigint",
            sql_date(as_of_date),
            sql_literal(row.from_state),
            sql_literal(row.to_state),
            f"{sql_literal(drivers)}::jsonb",
            f"{sql_literal(evidence_event_ids)}::jsonb",
            f"{source_run_id}::bigint",
        )
    ) + ")"


def _cycle_level(node_type: str, node_code: str) -> str:
    if node_code.strip().upper().startswith("MACRO_"):
        return "macro"
    normalized = node_type.strip().lower()
    if normalized == "macro_regime":
        return "macro"
    if normalized == "domain":
        return "domain"
    if normalized == "sector":
        return "sector"
    if normalized in {"theme", "subtheme"}:
        return "theme"
    if normalized == "instrument":
        return "instrument"
    return "unknown"


def _event_heat_score(
    *,
    direct_count: int,
    hierarchical_count: int,
    average_confidence: Decimal | None,
) -> Decimal:
    weighted_count = Decimal(direct_count) + Decimal(hierarchical_count) * Decimal("0.7500")
    volume_score = min(Decimal("1.0000"), weighted_count / Decimal("6.0000"))
    confidence = _score_or_default(average_confidence, Decimal("0.6000"))
    return _quantize(_clamp(volume_score * confidence))


def _state_from_score(score: Decimal) -> str:
    if score >= Decimal("0.7000"):
        return "expanding"
    if score >= Decimal("0.5500"):
        return "forming"
    if score >= Decimal("0.4000"):
        return "neutral"
    if score >= Decimal("0.2500"):
        return "cooling"
    return "structurally_broken"


def _state_counts(rows: tuple[CycleHierarchySnapshotRow, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.cycle_state] = counts.get(row.cycle_state, 0) + 1
    return counts


def _score_or_default(value: Decimal | None, default: Decimal) -> Decimal:
    return _quantize(_clamp(value if value is not None else default))


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _decimal_text(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _clamp(value: Decimal) -> Decimal:
    if value < 0:
        return Decimal("0")
    if value > 1:
        return Decimal("1")
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)
