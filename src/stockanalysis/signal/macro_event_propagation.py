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

DEFAULT_PIPELINE_NAME = "macro_event_propagation"
_DECIMAL_QUANTIZER = Decimal("0.0001")
_DEFAULT_EVENT_STRENGTH = Decimal("0.5500")
_DEFAULT_EVENT_CONFIDENCE = Decimal("0.6000")
_DEFAULT_EXPOSURE_CONFIDENCE = Decimal("0.6000")


@dataclass(frozen=True)
class MacroEventPropagationCandidate:
    event_id: int
    event_title: str
    event_at: str
    node_id: int
    node_code: str
    node_name: str
    theme_impact_direction: str
    theme_impact_strength: Decimal | None
    theme_confidence: Decimal | None
    theme_rationale: str
    instrument_id: int
    primary_symbol: str
    exposure_weight: Decimal
    sensitivity_direction: str
    exposure_confidence: Decimal | None
    exposure_rationale: str


@dataclass(frozen=True)
class PropagatedInstrumentImpact:
    event_id: int
    node_id: int
    instrument_id: int
    primary_symbol: str
    impact_direction: str
    impact_strength: Decimal
    confidence: Decimal
    exposure_weight: Decimal
    rationale: str


def load_macro_event_propagation_candidates(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    limit: int = 200,
    executor: PsqlCommandExecutor | None = None,
) -> tuple[MacroEventPropagationCandidate, ...]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload_text = sql_executor.execute_scalar(
        render_macro_event_propagation_candidate_lookup_sql(as_of_date=as_of_date, limit=limit)
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Macro event propagation lookup did not return a JSON array.")

    candidates: list[MacroEventPropagationCandidate] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Macro event propagation lookup returned a non-object row.")
        candidates.append(
            MacroEventPropagationCandidate(
                event_id=int(item["event_id"]),
                event_title=str(item.get("event_title") or ""),
                event_at=str(item.get("event_at") or ""),
                node_id=int(item["node_id"]),
                node_code=str(item["node_code"]),
                node_name=str(item.get("node_name") or item["node_code"]),
                theme_impact_direction=str(item.get("theme_impact_direction") or "watch"),
                theme_impact_strength=_optional_decimal(item.get("theme_impact_strength")),
                theme_confidence=_optional_decimal(item.get("theme_confidence")),
                theme_rationale=str(item.get("theme_rationale") or ""),
                instrument_id=int(item["instrument_id"]),
                primary_symbol=str(item["primary_symbol"]).upper(),
                exposure_weight=Decimal(str(item["exposure_weight"])),
                sensitivity_direction=str(item.get("sensitivity_direction") or "neutral"),
                exposure_confidence=_optional_decimal(item.get("exposure_confidence")),
                exposure_rationale=str(item.get("exposure_rationale") or ""),
            )
        )
    return tuple(candidates)


def render_macro_event_propagation_candidate_lookup_sql(*, as_of_date: date, limit: int = 200) -> str:
    if limit <= 0:
        raise ValueError("limit must be positive")
    return f"""-- macro event propagation candidate lookup
with recent_macro_events as (
    select
        event_row.event_id,
        event_row.title as event_title,
        event_row.event_at,
        classification_impact.node_id,
        node.code as node_code,
        node.name as node_name,
        coalesce(classification_impact.impact_direction, event_row.impact_polarity, 'watch') as theme_impact_direction,
        coalesce(classification_impact.impact_strength, event_row.significance_score) as theme_impact_strength,
        least(
            coalesce(classification_impact.confidence, 1.0),
            coalesce(event_row.confidence, 1.0)
        ) as theme_confidence,
        coalesce(classification_impact.rationale, event_row.summary, '') as theme_rationale
    from event.event_classification_impact classification_impact
    join event.event event_row on event_row.event_id = classification_impact.event_id
    join ref.classification_node node on node.node_id = classification_impact.node_id
    where node.taxonomy_family = 'internal_theme'
      and event_row.event_at < ({sql_date(as_of_date)} + interval '1 day')
    order by event_row.event_at desc, event_row.event_id desc, node.code
    limit {int(limit)}
),
exposed_rows as (
    select
        recent.event_id,
        recent.event_title,
        recent.event_at,
        recent.node_id,
        recent.node_code,
        recent.node_name,
        recent.theme_impact_direction,
        recent.theme_impact_strength,
        recent.theme_confidence,
        recent.theme_rationale,
        instrument.instrument_id,
        instrument.primary_symbol,
        exposure.exposure_weight,
        exposure.sensitivity_direction,
        exposure.confidence as exposure_confidence,
        exposure.rationale as exposure_rationale
    from recent_macro_events recent
    join ref.instrument_factor_exposure exposure
      on exposure.node_id = recent.node_id
     and exposure.valid_from <= {sql_date(as_of_date)}
     and (exposure.valid_to is null or exposure.valid_to >= {sql_date(as_of_date)})
    join ref.instrument instrument
      on instrument.instrument_id = exposure.instrument_id
     and instrument.is_active
)
select coalesce(
    json_agg(
        json_build_object(
            'event_id', event_id,
            'event_title', event_title,
            'event_at', event_at,
            'node_id', node_id,
            'node_code', node_code,
            'node_name', node_name,
            'theme_impact_direction', theme_impact_direction,
            'theme_impact_strength', theme_impact_strength,
            'theme_confidence', theme_confidence,
            'theme_rationale', theme_rationale,
            'instrument_id', instrument_id,
            'primary_symbol', primary_symbol,
            'exposure_weight', exposure_weight,
            'sensitivity_direction', sensitivity_direction,
            'exposure_confidence', exposure_confidence,
            'exposure_rationale', exposure_rationale
        )
        order by event_at desc, event_id desc, node_code, primary_symbol
    ),
    '[]'::json
)::text
from exposed_rows;"""


def compute_propagated_instrument_impacts(
    candidates: tuple[MacroEventPropagationCandidate, ...],
) -> tuple[PropagatedInstrumentImpact, ...]:
    rows: list[PropagatedInstrumentImpact] = []
    for candidate in candidates:
        strength = _quantize(_clamp_decimal((candidate.theme_impact_strength or _DEFAULT_EVENT_STRENGTH) * candidate.exposure_weight))
        confidence = _quantize(
            min(
                candidate.theme_confidence or _DEFAULT_EVENT_CONFIDENCE,
                candidate.exposure_confidence or _DEFAULT_EXPOSURE_CONFIDENCE,
            )
        )
        direction = _propagate_direction(
            event_direction=candidate.theme_impact_direction,
            sensitivity_direction=candidate.sensitivity_direction,
        )
        rationale_parts = [
            f"{candidate.node_code} flow propagated to {candidate.primary_symbol}",
            f"sensitivity={candidate.sensitivity_direction}",
            f"exposure={candidate.exposure_weight}",
        ]
        if candidate.theme_rationale:
            rationale_parts.append(f"event={candidate.theme_rationale[:240]}")
        if candidate.exposure_rationale:
            rationale_parts.append(f"exposure_rationale={candidate.exposure_rationale[:240]}")
        rows.append(
            PropagatedInstrumentImpact(
                event_id=candidate.event_id,
                node_id=candidate.node_id,
                instrument_id=candidate.instrument_id,
                primary_symbol=candidate.primary_symbol,
                impact_direction=direction,
                impact_strength=strength,
                confidence=confidence,
                exposure_weight=_quantize(candidate.exposure_weight),
                rationale="; ".join(rationale_parts),
            )
        )
    return tuple(rows)


def render_propagated_instrument_impact_upsert_sql(
    rows: tuple[PropagatedInstrumentImpact, ...],
    *,
    source_run_id: int,
) -> str:
    if not rows:
        raise ValueError("At least one propagated instrument impact row is required.")
    value_rows = ",\n        ".join(
        _render_propagated_impact_value_tuple(row, source_run_id=source_run_id) for row in rows
    )
    return f"""insert into signal.propagated_instrument_impact (
    event_id,
    node_id,
    instrument_id,
    propagation_kind,
    impact_direction,
    impact_strength,
    confidence,
    exposure_weight,
    rationale,
    source_run_id
)
values
        {value_rows}
on conflict (event_id, node_id, instrument_id, propagation_kind) do update
set
    impact_direction = excluded.impact_direction,
    impact_strength = excluded.impact_strength,
    confidence = excluded.confidence,
    exposure_weight = excluded.exposure_weight,
    rationale = excluded.rationale,
    source_run_id = excluded.source_run_id,
    updated_at = now();"""


def run_macro_event_propagation(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    limit: int = 200,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    candidates = load_macro_event_propagation_candidates(
        config=config,
        as_of_date=as_of_date,
        limit=limit,
        executor=sql_executor,
    )
    impacts = compute_propagated_instrument_impacts(candidates)
    base_report: dict[str, object] = {
        "report_name": "macro_event_propagation",
        "status": "planned" if not execute else "running",
        "execute": execute,
        "as_of_date": as_of_date.isoformat(),
        "candidate_count": len(candidates),
        "propagated_impact_count": len(impacts),
        "event_count": len({row.event_id for row in impacts}),
        "instrument_count": len({row.instrument_id for row in impacts}),
        "theme_code_preview": sorted({candidate.node_code for candidate in candidates})[:10],
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
            "candidate_count": len(candidates),
            "propagated_impact_count": len(impacts),
        },
    )
    try:
        if impacts:
            sql_executor.execute_non_query(render_propagated_instrument_impact_upsert_sql(impacts, source_run_id=run_id))
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return {
        **base_report,
        "status": "completed",
        "run_id": run_id,
    }


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


def _render_propagated_impact_value_tuple(row: PropagatedInstrumentImpact, *, source_run_id: int) -> str:
    return "(" + ", ".join(
        (
            f"{row.event_id}::bigint",
            f"{row.node_id}::bigint",
            f"{row.instrument_id}::bigint",
            sql_literal("factor_exposure"),
            sql_literal(row.impact_direction),
            sql_numeric(row.impact_strength),
            sql_numeric(row.confidence),
            sql_numeric(row.exposure_weight),
            sql_literal(row.rationale),
            f"{source_run_id}::bigint",
        )
    ) + ")"


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
