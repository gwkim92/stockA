from __future__ import annotations

import hashlib
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

DEFAULT_PIPELINE_NAME = "hierarchical_impact_propagation"
_DECIMAL_QUANTIZER = Decimal("0.0001")
_DEFAULT_EVENT_STRENGTH = Decimal("0.5500")
_DEFAULT_EVENT_CONFIDENCE = Decimal("0.6000")
_DEFAULT_EXPOSURE_CONFIDENCE = Decimal("0.6000")
_DEFAULT_DECAY_PER_HOP = Decimal("0.8500")


@dataclass(frozen=True)
class HierarchicalImpactPropagationCandidate:
    event_id: int
    event_title: str
    event_at: str
    source_node_id: int
    source_node_code: str
    source_node_name: str
    propagated_node_id: int
    propagated_node_code: str
    propagated_node_name: str
    node_path_codes: tuple[str, ...]
    path_depth: int
    path_weight: Decimal
    decay: Decimal
    source_impact_direction: str
    source_impact_strength: Decimal | None
    source_confidence: Decimal | None
    source_rationale: str
    instrument_id: int
    primary_symbol: str
    exposure_weight: Decimal
    sensitivity_direction: str
    exposure_confidence: Decimal | None
    exposure_rationale: str


@dataclass(frozen=True)
class HierarchicalPropagatedInstrumentImpact:
    event_id: int
    source_node_id: int
    propagated_node_id: int
    instrument_id: int
    primary_symbol: str
    node_path_codes: tuple[str, ...]
    path_hash: str
    path_depth: int
    path_weight: Decimal
    decay: Decimal
    impact_direction: str
    impact_strength: Decimal
    confidence: Decimal
    exposure_weight: Decimal
    rationale: str


def load_hierarchical_impact_propagation_candidates(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    limit: int = 200,
    max_depth: int = 3,
    decay_per_hop: Decimal = _DEFAULT_DECAY_PER_HOP,
    executor: PsqlCommandExecutor | None = None,
) -> tuple[HierarchicalImpactPropagationCandidate, ...]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    if max_depth < 0 or max_depth > 10:
        raise ValueError("max_depth must be between 0 and 10")
    if decay_per_hop <= 0 or decay_per_hop > 1:
        raise ValueError("decay_per_hop must be greater than 0 and less than or equal to 1")
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload_text = sql_executor.execute_scalar(
        render_hierarchical_impact_propagation_candidate_lookup_sql(
            as_of_date=as_of_date,
            limit=limit,
            max_depth=max_depth,
            decay_per_hop=decay_per_hop,
        )
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Hierarchical impact propagation lookup did not return a JSON array.")

    candidates: list[HierarchicalImpactPropagationCandidate] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Hierarchical impact propagation lookup returned a non-object row.")
        candidates.append(
            HierarchicalImpactPropagationCandidate(
                event_id=int(item["event_id"]),
                event_title=str(item.get("event_title") or ""),
                event_at=str(item.get("event_at") or ""),
                source_node_id=int(item["source_node_id"]),
                source_node_code=str(item["source_node_code"]),
                source_node_name=str(item.get("source_node_name") or item["source_node_code"]),
                propagated_node_id=int(item["propagated_node_id"]),
                propagated_node_code=str(item["propagated_node_code"]),
                propagated_node_name=str(item.get("propagated_node_name") or item["propagated_node_code"]),
                node_path_codes=tuple(str(code) for code in item.get("node_path_codes", [])),
                path_depth=int(item["path_depth"]),
                path_weight=Decimal(str(item["path_weight"])),
                decay=Decimal(str(item["decay"])),
                source_impact_direction=str(item.get("source_impact_direction") or "watch"),
                source_impact_strength=_optional_decimal(item.get("source_impact_strength")),
                source_confidence=_optional_decimal(item.get("source_confidence")),
                source_rationale=str(item.get("source_rationale") or ""),
                instrument_id=int(item["instrument_id"]),
                primary_symbol=str(item["primary_symbol"]).upper(),
                exposure_weight=Decimal(str(item["exposure_weight"])),
                sensitivity_direction=str(item.get("sensitivity_direction") or "neutral"),
                exposure_confidence=_optional_decimal(item.get("exposure_confidence")),
                exposure_rationale=str(item.get("exposure_rationale") or ""),
            )
        )
    return tuple(candidates)


def render_hierarchical_impact_propagation_candidate_lookup_sql(
    *,
    as_of_date: date,
    limit: int = 200,
    max_depth: int = 3,
    decay_per_hop: Decimal = _DEFAULT_DECAY_PER_HOP,
) -> str:
    if limit <= 0:
        raise ValueError("limit must be positive")
    if max_depth < 0 or max_depth > 10:
        raise ValueError("max_depth must be between 0 and 10")
    if decay_per_hop <= 0 or decay_per_hop > 1:
        raise ValueError("decay_per_hop must be greater than 0 and less than or equal to 1")
    return f"""-- hierarchical impact propagation candidate lookup
with recursive recent_source_events as (
    select
        event_row.event_id,
        event_row.title as event_title,
        event_row.event_at,
        classification_impact.node_id as source_node_id,
        source_node.code as source_node_code,
        source_node.name as source_node_name,
        coalesce(classification_impact.impact_direction, event_row.impact_polarity, 'watch') as source_impact_direction,
        coalesce(classification_impact.impact_strength, event_row.significance_score) as source_impact_strength,
        least(
            coalesce(classification_impact.confidence, 1.0),
            coalesce(event_row.confidence, 1.0)
        ) as source_confidence,
        coalesce(classification_impact.rationale, event_row.summary, '') as source_rationale
    from event.event_classification_impact classification_impact
    join event.event event_row on event_row.event_id = classification_impact.event_id
    join ref.classification_node source_node on source_node.node_id = classification_impact.node_id
    where source_node.taxonomy_family = 'internal_theme'
      and event_row.event_at < ({sql_date(as_of_date)} + interval '1 day')
    order by event_row.event_at desc, event_row.event_id desc, source_node.code
    limit {int(limit)}
),
graph_paths as (
    select
        recent.event_id,
        recent.event_title,
        recent.event_at,
        recent.source_node_id,
        recent.source_node_code,
        recent.source_node_name,
        recent.source_node_id as propagated_node_id,
        recent.source_node_code as propagated_node_code,
        recent.source_node_name as propagated_node_name,
        array[recent.source_node_id]::bigint[] as node_path_ids,
        array[recent.source_node_code]::text[] as node_path_codes,
        0::integer as path_depth,
        1.000000::numeric as path_weight,
        1.0000::numeric as decay,
        recent.source_impact_direction,
        recent.source_impact_strength,
        recent.source_confidence,
        recent.source_rationale
    from recent_source_events recent

    union all

    select
        path.event_id,
        path.event_title,
        path.event_at,
        path.source_node_id,
        path.source_node_code,
        path.source_node_name,
        child.node_id as propagated_node_id,
        child.code as propagated_node_code,
        child.name as propagated_node_name,
        path.node_path_ids || child.node_id,
        path.node_path_codes || child.code,
        path.path_depth + 1,
        (path.path_weight * coalesce(edge.weight, 1.0000))::numeric,
        (path.decay * {sql_numeric(decay_per_hop)})::numeric,
        path.source_impact_direction,
        path.source_impact_strength,
        path.source_confidence,
        path.source_rationale
    from graph_paths path
    join ref.classification_edge edge
      on edge.parent_node_id = path.propagated_node_id
     and edge.valid_from <= {sql_date(as_of_date)}
     and (edge.valid_to is null or edge.valid_to >= {sql_date(as_of_date)})
    join ref.classification_node child
      on child.node_id = edge.child_node_id
     and child.taxonomy_family = 'internal_theme'
     and child.status = 'active'
    where path.path_depth < {int(max_depth)}
      and not child.node_id = any(path.node_path_ids)
),
exposed_paths as (
    select *
    from (
        select
            path.event_id,
            path.event_title,
            path.event_at,
            path.source_node_id,
            path.source_node_code,
            path.source_node_name,
            path.propagated_node_id,
            path.propagated_node_code,
            path.propagated_node_name,
            path.node_path_codes,
            path.path_depth,
            path.path_weight,
            path.decay,
            path.source_impact_direction,
            path.source_impact_strength,
            path.source_confidence,
            path.source_rationale,
            instrument.instrument_id,
            instrument.primary_symbol,
            exposure.exposure_weight,
            exposure.sensitivity_direction,
            exposure.confidence as exposure_confidence,
            exposure.rationale as exposure_rationale,
            row_number() over (
                partition by
                    path.event_id,
                    path.source_node_id,
                    path.propagated_node_id,
                    instrument.instrument_id,
                    array_to_string(path.node_path_codes, '>')
                order by
                    case
                        when path.propagated_node_code like 'MACRO_%'
                         and exposure.exposure_type = 'macro_sensitivity' then 1
                        when path.propagated_node_code not like 'MACRO_%'
                         and exposure.exposure_type = 'theme_membership' then 1
                        when exposure.exposure_type = 'macro_sensitivity' then 2
                        when exposure.exposure_type = 'sector_proxy' then 3
                        when exposure.exposure_type = 'manual_seed' then 4
                        else 5
                    end,
                    exposure.confidence desc nulls last,
                    exposure.exposure_weight desc,
                    exposure.valid_from desc
            ) as exposure_rank
        from graph_paths path
        join ref.instrument_factor_exposure exposure
          on exposure.node_id = path.propagated_node_id
         and exposure.valid_from <= {sql_date(as_of_date)}
         and (exposure.valid_to is null or exposure.valid_to >= {sql_date(as_of_date)})
        join ref.instrument instrument
          on instrument.instrument_id = exposure.instrument_id
         and instrument.is_active
    ) ranked_exposures
    where exposure_rank = 1
)
select coalesce(
    json_agg(
        json_build_object(
            'event_id', event_id,
            'event_title', event_title,
            'event_at', event_at,
            'source_node_id', source_node_id,
            'source_node_code', source_node_code,
            'source_node_name', source_node_name,
            'propagated_node_id', propagated_node_id,
            'propagated_node_code', propagated_node_code,
            'propagated_node_name', propagated_node_name,
            'node_path_codes', node_path_codes,
            'path_depth', path_depth,
            'path_weight', path_weight,
            'decay', decay,
            'source_impact_direction', source_impact_direction,
            'source_impact_strength', source_impact_strength,
            'source_confidence', source_confidence,
            'source_rationale', source_rationale,
            'instrument_id', instrument_id,
            'primary_symbol', primary_symbol,
            'exposure_weight', exposure_weight,
            'sensitivity_direction', sensitivity_direction,
            'exposure_confidence', exposure_confidence,
            'exposure_rationale', exposure_rationale
        )
        order by event_at desc, event_id desc, path_depth, source_node_code, propagated_node_code, primary_symbol
    ),
    '[]'::json
)::text
from exposed_paths;"""


def compute_hierarchical_propagated_impacts(
    candidates: tuple[HierarchicalImpactPropagationCandidate, ...],
) -> tuple[HierarchicalPropagatedInstrumentImpact, ...]:
    rows_by_key: dict[tuple[int, int, int, int, str], HierarchicalPropagatedInstrumentImpact] = {}
    for candidate in candidates:
        path_hash = _path_hash(candidate.node_path_codes)
        strength = _quantize(
            _clamp_decimal(
                (candidate.source_impact_strength or _DEFAULT_EVENT_STRENGTH)
                * candidate.path_weight
                * candidate.decay
                * candidate.exposure_weight
            )
        )
        confidence = _quantize(
            _clamp_decimal(
                min(
                    candidate.source_confidence or _DEFAULT_EVENT_CONFIDENCE,
                    candidate.exposure_confidence or _DEFAULT_EXPOSURE_CONFIDENCE,
                )
                * candidate.path_weight
                * candidate.decay
            )
        )
        direction = _propagate_direction(
            event_direction=candidate.source_impact_direction,
            sensitivity_direction=candidate.sensitivity_direction,
        )
        path_label = " -> ".join(candidate.node_path_codes)
        rationale_parts = [
            f"path={path_label}",
            f"source={candidate.source_node_code}",
            f"target_node={candidate.propagated_node_code}",
            f"instrument={candidate.primary_symbol}",
            f"depth={candidate.path_depth}",
            f"path_weight={candidate.path_weight}",
            f"decay={candidate.decay}",
            f"sensitivity={candidate.sensitivity_direction}",
            f"exposure={candidate.exposure_weight}",
        ]
        if candidate.source_rationale:
            rationale_parts.append(f"event={candidate.source_rationale[:240]}")
        if candidate.exposure_rationale:
            rationale_parts.append(f"exposure_rationale={candidate.exposure_rationale[:240]}")
        row = HierarchicalPropagatedInstrumentImpact(
            event_id=candidate.event_id,
            source_node_id=candidate.source_node_id,
            propagated_node_id=candidate.propagated_node_id,
            instrument_id=candidate.instrument_id,
            primary_symbol=candidate.primary_symbol,
            node_path_codes=candidate.node_path_codes,
            path_hash=path_hash,
            path_depth=candidate.path_depth,
            path_weight=_quantize_six(candidate.path_weight),
            decay=_quantize(candidate.decay),
            impact_direction=direction,
            impact_strength=strength,
            confidence=confidence,
            exposure_weight=_quantize(candidate.exposure_weight),
            rationale="; ".join(rationale_parts),
        )
        key = (row.event_id, row.source_node_id, row.propagated_node_id, row.instrument_id, row.path_hash)
        existing = rows_by_key.get(key)
        if existing is None or (row.confidence, row.impact_strength) > (existing.confidence, existing.impact_strength):
            rows_by_key[key] = row
    return tuple(rows_by_key.values())


def render_hierarchical_propagated_impact_upsert_sql(
    rows: tuple[HierarchicalPropagatedInstrumentImpact, ...],
    *,
    source_run_id: int,
) -> str:
    if not rows:
        raise ValueError("At least one hierarchical propagated impact row is required.")
    value_rows = ",\n        ".join(
        _render_hierarchical_impact_value_tuple(row, source_run_id=source_run_id) for row in rows
    )
    return f"""insert into signal.hierarchical_propagated_instrument_impact (
    event_id,
    source_node_id,
    propagated_node_id,
    instrument_id,
    propagation_kind,
    node_path_codes,
    path_hash,
    path_depth,
    path_weight,
    decay,
    impact_direction,
    impact_strength,
    confidence,
    exposure_weight,
    rationale,
    source_run_id
)
values
        {value_rows}
on conflict (
    event_id,
    source_node_id,
    propagated_node_id,
    instrument_id,
    propagation_kind,
    path_hash
) do update
set
    node_path_codes = excluded.node_path_codes,
    path_depth = excluded.path_depth,
    path_weight = excluded.path_weight,
    decay = excluded.decay,
    impact_direction = excluded.impact_direction,
    impact_strength = excluded.impact_strength,
    confidence = excluded.confidence,
    exposure_weight = excluded.exposure_weight,
    rationale = excluded.rationale,
    source_run_id = excluded.source_run_id,
    updated_at = now();"""


def run_hierarchical_impact_propagation(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    limit: int = 200,
    max_depth: int = 3,
    decay_per_hop: Decimal = _DEFAULT_DECAY_PER_HOP,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    candidates = load_hierarchical_impact_propagation_candidates(
        config=config,
        as_of_date=as_of_date,
        limit=limit,
        max_depth=max_depth,
        decay_per_hop=decay_per_hop,
        executor=sql_executor,
    )
    impacts = compute_hierarchical_propagated_impacts(candidates)
    base_report: dict[str, object] = {
        "report_name": "hierarchical_impact_propagation",
        "status": "planned" if not execute else "running",
        "execute": execute,
        "as_of_date": as_of_date.isoformat(),
        "limit": limit,
        "max_depth": max_depth,
        "decay_per_hop": str(decay_per_hop),
        "candidate_count": len(candidates),
        "propagated_impact_count": len(impacts),
        "event_count": len({row.event_id for row in impacts}),
        "instrument_count": len({row.instrument_id for row in impacts}),
        "source_node_preview": sorted({candidate.source_node_code for candidate in candidates})[:10],
        "propagated_node_preview": sorted({candidate.propagated_node_code for candidate in candidates})[:10],
        "symbol_preview": sorted({row.primary_symbol for row in impacts})[:10],
    }
    if not execute:
        return base_report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "limit": limit,
            "max_depth": max_depth,
            "decay_per_hop": str(decay_per_hop),
            "candidate_count": len(candidates),
            "propagated_impact_count": len(impacts),
        },
    )
    try:
        if impacts:
            sql_executor.execute_non_query(
                render_hierarchical_propagated_impact_upsert_sql(impacts, source_run_id=run_id)
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


def _render_hierarchical_impact_value_tuple(
    row: HierarchicalPropagatedInstrumentImpact,
    *,
    source_run_id: int,
) -> str:
    node_path_json = json.dumps(list(row.node_path_codes), ensure_ascii=False)
    return "(" + ", ".join(
        (
            f"{row.event_id}::bigint",
            f"{row.source_node_id}::bigint",
            f"{row.propagated_node_id}::bigint",
            f"{row.instrument_id}::bigint",
            sql_literal("hierarchical_factor_exposure"),
            f"{sql_literal(node_path_json)}::jsonb",
            sql_literal(row.path_hash),
            f"{row.path_depth}::integer",
            f"{row.path_weight}::numeric",
            sql_numeric(row.decay),
            sql_literal(row.impact_direction),
            sql_numeric(row.impact_strength),
            sql_numeric(row.confidence),
            sql_numeric(row.exposure_weight),
            sql_literal(row.rationale),
            f"{source_run_id}::bigint",
        )
    ) + ")"


def _propagate_direction(*, event_direction: str, sensitivity_direction: str) -> str:
    normalized_event = _normalize_event_direction(event_direction)
    normalized_sensitivity = sensitivity_direction.strip().lower()
    if normalized_sensitivity == "positive":
        return normalized_event
    if normalized_sensitivity == "negative":
        if normalized_event == "supportive":
            return "risk_review"
        if normalized_event == "risk_review":
            return "supportive"
        return "watch"
    return "watch"


def _normalize_event_direction(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"supportive", "positive", "bullish", "up"}:
        return "supportive"
    if normalized in {"risk_review", "negative", "bearish", "down", "risk"}:
        return "risk_review"
    if normalized in {"mixed", "unknown"}:
        return normalized
    return "watch"


def _path_hash(node_path_codes: tuple[str, ...]) -> str:
    payload = json.dumps(list(node_path_codes), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _clamp_decimal(value: Decimal) -> Decimal:
    if value < 0:
        return Decimal("0")
    if value > 1:
        return Decimal("1")
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)


def _quantize_six(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
