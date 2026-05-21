from __future__ import annotations

import json
import os
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

_DEFAULT_MARKET_CODE = "US"
_DEFAULT_SCORE_VERSION = "bootstrap-v1"
_DECIMAL_QUANTIZER = Decimal("0.0001")
_ZSCORE_MIN = Decimal("-2")
_ZSCORE_MAX = Decimal("2")
_RETURN_MEDIUM_MIN = Decimal("-0.20")
_RETURN_MEDIUM_MAX = Decimal("0.20")
_RETURN_SHORT_MIN = Decimal("-0.05")
_RETURN_SHORT_MAX = Decimal("0.05")
_CYCLE_WEIGHT = Decimal("0.45")
_MOMENTUM_WEIGHT = Decimal("0.25")
_SHORT_TERM_WEIGHT = Decimal("0.15")
_RANK_WEIGHT = Decimal("0.15")
_MACRO_FLOW_WEIGHT_DEFAULT = Decimal("0.10")
MACRO_FLOW_WEIGHT_ENV = "STOCKANALYSIS_RECOMMENDATION_MACRO_FLOW_WEIGHT"
_COMPONENT_ORDER = ("cycle_score", "momentum_score", "short_term_score", "rank_score", "macro_flow_score")
_COMPONENT_WEIGHTS = {
    "cycle_score": _CYCLE_WEIGHT,
    "momentum_score": _MOMENTUM_WEIGHT,
    "short_term_score": _SHORT_TERM_WEIGHT,
    "rank_score": _RANK_WEIGHT,
}
_COMPONENT_EXPLANATIONS = {
    "cycle_score": "Normalized current cycle state score from the linked internal theme.",
    "momentum_score": "Medium-term price momentum from return_since_first_observation.",
    "short_term_score": "Short-term price move from return_1d.",
    "rank_score": "Relative rank inside the selected strategy universe.",
    "macro_flow_score": "Propagated macro/theme news impact for this instrument and linked theme.",
}


@dataclass(frozen=True)
class RecommendationCandidate:
    universe_batch_id: int
    instrument_id: int
    primary_symbol: str
    universe_rank_position: int
    universe_member_count: int
    node_id: int
    node_code: str
    node_name: str
    cycle_state: str
    cycle_score: Decimal
    return_1d: Decimal | None
    return_since_first: Decimal | None
    return_since_first_zscore: Decimal | None
    latest_adjusted_close: Decimal | None
    macro_flow_score: Decimal | None


@dataclass(frozen=True)
class RecommendationRow:
    instrument_id: int
    primary_symbol: str
    node_id: int
    node_code: str
    bucket: str
    action: str
    rank_position: int
    total_score: Decimal
    recommended_weight: Decimal | None
    component_scores: dict[str, str]


def load_recommendation_candidates(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    market_code: str = _DEFAULT_MARKET_CODE,
    executor: PsqlCommandExecutor | None = None,
) -> tuple[RecommendationCandidate, ...]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload_text = sql_executor.execute_scalar(
        render_recommendation_candidate_lookup_sql(
            as_of_date=as_of_date,
            market_code=market_code,
            strategy_name=strategy_name,
            horizon_type=horizon_type,
            universe_version=universe_version,
        )
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Recommendation candidate lookup did not return a JSON array.")

    candidates: list[RecommendationCandidate] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Recommendation candidate lookup returned a non-object row.")
        candidates.append(
            RecommendationCandidate(
                universe_batch_id=int(item["universe_batch_id"]),
                instrument_id=int(item["instrument_id"]),
                primary_symbol=str(item["primary_symbol"]).upper(),
                universe_rank_position=int(item["universe_rank_position"]),
                universe_member_count=int(item["universe_member_count"]),
                node_id=int(item["node_id"]),
                node_code=str(item["node_code"]),
                node_name=str(item["node_name"]),
                cycle_state=str(item["cycle_state"]),
                cycle_score=Decimal(str(item["cycle_score"])),
                return_1d=Decimal(str(item["return_1d"])) if item.get("return_1d") is not None else None,
                return_since_first=Decimal(str(item["return_since_first"])) if item.get("return_since_first") is not None else None,
                return_since_first_zscore=Decimal(str(item["return_since_first_zscore"]))
                if item.get("return_since_first_zscore") is not None
                else None,
                latest_adjusted_close=Decimal(str(item["latest_adjusted_close"]))
                if item.get("latest_adjusted_close") is not None
                else None,
                macro_flow_score=Decimal(str(item["macro_flow_score"])) if item.get("macro_flow_score") is not None else None,
            )
        )

    if not candidates:
        raise ValueError("No recommendation candidates matched the requested snapshot identity.")
    return tuple(candidates)


def render_recommendation_candidate_lookup_sql(
    *,
    as_of_date: date,
    market_code: str,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
) -> str:
    return f"""-- recommendation candidate lookup
with selected_batch as (
    select universe_batch_id
    from signal.strategy_universe_batch
    where as_of_date = {sql_date(as_of_date)}
      and market_code = {sql_literal(market_code)}
      and strategy_name = {sql_literal(strategy_name)}
      and horizon_type = {sql_literal(horizon_type)}
      and universe_version = {sql_literal(universe_version)}
    order by universe_batch_id desc
    limit 1
),
selected_members as (
    select
        m.universe_batch_id,
        m.instrument_id,
        i.primary_symbol,
        m.rank_position as universe_rank_position,
        count(*) over ()::integer as universe_member_count
    from selected_batch sb
    join signal.strategy_universe_member m on m.universe_batch_id = sb.universe_batch_id
    join ref.instrument i on i.instrument_id = m.instrument_id
),
macro_flow_rows as (
    select
        selected_members.instrument_id,
        propagated_impact.node_id,
        avg(
            (
                case propagated_impact.impact_direction
                    when 'supportive' then 1.0
                    when 'watch' then 0.5
                    when 'mixed' then 0.5
                    when 'risk_review' then 0.0
                    else 0.25
                end
            )
            * coalesce(propagated_impact.impact_strength, 0.55)
            * coalesce(propagated_impact.confidence, 0.60)
        )::numeric(18,8) as macro_flow_score
    from selected_members
    join signal.propagated_instrument_impact propagated_impact
      on propagated_impact.instrument_id = selected_members.instrument_id
    join event.event event_row on event_row.event_id = propagated_impact.event_id
    where event_row.event_at >= ({sql_date(as_of_date)} - interval '30 day')
      and event_row.event_at < ({sql_date(as_of_date)} + interval '1 day')
    group by selected_members.instrument_id, propagated_impact.node_id
),
evidence_rows as (
    select
        selected_members.universe_batch_id,
        selected_members.instrument_id,
        selected_members.primary_symbol,
        selected_members.universe_rank_position,
        selected_members.universe_member_count,
        node.node_id,
        node.code as node_code,
        node.name as node_name,
        cycle.cycle_state,
        cycle.cycle_score,
        return_1d.feature_value as return_1d,
        return_since_first.feature_value as return_since_first,
        return_since_first.zscore as return_since_first_zscore,
        latest_close.feature_value as latest_adjusted_close,
        coalesce(macro_flow.macro_flow_score, 0)::numeric(18,8) as macro_flow_score
    from selected_members
    join ref.instrument_classification_membership membership
      on membership.instrument_id = selected_members.instrument_id
    join ref.classification_node node on node.node_id = membership.node_id
    join signal.cycle_state_snapshot cycle
      on cycle.node_id = node.node_id
     and cycle.as_of_date = {sql_date(as_of_date)}
    left join signal.instrument_feature_value return_1d
      on return_1d.instrument_id = selected_members.instrument_id
     and return_1d.as_of_date = {sql_date(as_of_date)}
     and return_1d.feature_code = 'return_1d'
    left join signal.instrument_feature_value return_since_first
      on return_since_first.instrument_id = selected_members.instrument_id
     and return_since_first.as_of_date = {sql_date(as_of_date)}
     and return_since_first.feature_code = 'return_since_first_observation'
    left join signal.instrument_feature_value latest_close
      on latest_close.instrument_id = selected_members.instrument_id
     and latest_close.as_of_date = {sql_date(as_of_date)}
     and latest_close.feature_code = 'latest_adjusted_close'
    left join macro_flow_rows macro_flow
      on macro_flow.instrument_id = selected_members.instrument_id
     and macro_flow.node_id = node.node_id
    where node.taxonomy_family = 'internal_theme'
      and membership.membership_type = 'derived_theme'
      and membership.valid_from <= {sql_date(as_of_date)}
      and (membership.valid_to is null or membership.valid_to >= {sql_date(as_of_date)})
)
select coalesce(
    json_agg(
        json_build_object(
            'universe_batch_id', universe_batch_id,
            'instrument_id', instrument_id,
            'primary_symbol', primary_symbol,
            'universe_rank_position', universe_rank_position,
            'universe_member_count', universe_member_count,
            'node_id', node_id,
            'node_code', node_code,
            'node_name', node_name,
            'cycle_state', cycle_state,
            'cycle_score', cycle_score,
            'return_1d', return_1d,
            'return_since_first', return_since_first,
            'return_since_first_zscore', return_since_first_zscore,
            'latest_adjusted_close', latest_adjusted_close,
            'macro_flow_score', macro_flow_score
        )
        order by primary_symbol, node_code
    ),
    '[]'::json
)::text
from evidence_rows;"""


def compute_recommendation_rows(
    candidates: tuple[RecommendationCandidate, ...],
) -> tuple[RecommendationRow, ...]:
    if not candidates:
        raise ValueError("At least one recommendation candidate is required.")

    best_by_instrument: dict[int, tuple[RecommendationCandidate, Decimal, dict[str, Decimal]]] = {}
    for candidate in candidates:
        component_scores = _compute_component_scores(candidate)
        total_score = _quantize(
            (component_scores["cycle_score"] * _CYCLE_WEIGHT)
            + (component_scores["momentum_score"] * _MOMENTUM_WEIGHT)
            + (component_scores["short_term_score"] * _SHORT_TERM_WEIGHT)
            + (component_scores["rank_score"] * _RANK_WEIGHT)
            + (component_scores["macro_flow_score"] * _macro_flow_weight())
        )
        current = best_by_instrument.get(candidate.instrument_id)
        if current is None or total_score > current[1] or (
            total_score == current[1] and candidate.node_code < current[0].node_code
        ):
            best_by_instrument[candidate.instrument_id] = (candidate, total_score, component_scores)

    ranked_items = sorted(
        best_by_instrument.values(),
        key=lambda item: (-item[1], item[0].primary_symbol),
    )

    rows: list[RecommendationRow] = []
    for index, (candidate, total_score, component_scores) in enumerate(ranked_items, start=1):
        bucket, action, recommended_weight = _bucket_action_and_weight(total_score)
        rows.append(
            RecommendationRow(
                instrument_id=candidate.instrument_id,
                primary_symbol=candidate.primary_symbol,
                node_id=candidate.node_id,
                node_code=candidate.node_code,
                bucket=bucket,
                action=action,
                rank_position=index,
                total_score=total_score,
                recommended_weight=recommended_weight,
                component_scores={name: str(_quantize(value)) for name, value in component_scores.items()},
            )
        )
    return tuple(rows)


def render_recommendation_upsert_sql(
    recommendation_rows: tuple[RecommendationRow, ...],
    *,
    as_of_date: date,
    market_code: str,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    score_version: str,
    source_run_id: int,
) -> str:
    if not recommendation_rows:
        raise ValueError("At least one recommendation row is required.")
    value_rows = ",\n        ".join(_render_recommendation_value_tuple(row) for row in recommendation_rows)
    component_value_rows = ",\n        ".join(_render_score_component_value_tuple(row) for row in recommendation_rows)
    notes = {
        "score_version": score_version,
        "score_weights": {
            "cycle_score": str(_CYCLE_WEIGHT),
            "momentum_score": str(_MOMENTUM_WEIGHT),
            "short_term_score": str(_SHORT_TERM_WEIGHT),
            "rank_score": str(_RANK_WEIGHT),
            "macro_flow_score": str(_macro_flow_weight()),
        },
        "scope": "direct_internal_theme_membership_plus_macro_flow_propagation",
        "thesis_id": None,
    }
    notes_json = json.dumps(notes, ensure_ascii=False, sort_keys=True)
    return f"""begin;

with upsert_batch as (
    insert into signal.recommendation_batch (
        as_of_date,
        market_code,
        strategy_name,
        horizon_type,
        universe_version,
        notes,
        source_run_id
    )
    values (
        {sql_date(as_of_date)},
        {sql_literal(market_code)},
        {sql_literal(strategy_name)},
        {sql_literal(horizon_type)},
        {sql_literal(universe_version)},
        {sql_literal(notes_json)},
        {source_run_id}::bigint
    )
    on conflict (as_of_date, market_code, strategy_name, horizon_type) do update
    set
        universe_version = excluded.universe_version,
        notes = excluded.notes,
        source_run_id = excluded.source_run_id
    returning batch_id
),
delete_existing as (
    delete from signal.recommendation
    where batch_id = (select batch_id from upsert_batch)
    returning 1
),
source_rows (
    instrument_id,
    bucket,
    action,
    rank_position,
    total_score,
    recommended_weight
) as (
    values
        {value_rows}
),
source_components (
    instrument_id,
    component_name,
    component_score,
    component_weight,
    explanation
) as (
    values
        {component_value_rows}
),
insert_recommendations as (
    insert into signal.recommendation (
        batch_id,
        instrument_id,
        thesis_id,
        bucket,
        action,
        rank_position,
        total_score,
        recommended_weight,
        status
    )
    select
        upsert_batch.batch_id,
        source_rows.instrument_id,
        null::bigint,
        source_rows.bucket,
        source_rows.action,
        source_rows.rank_position,
        source_rows.total_score,
        source_rows.recommended_weight,
        'active'
    from upsert_batch
    cross join (select count(*) from delete_existing) deleted
    join source_rows on true
    returning recommendation_id, instrument_id
),
insert_score_components as (
    insert into signal.recommendation_score_component (
        recommendation_id,
        component_name,
        component_score,
        component_weight,
        explanation
    )
    select
        insert_recommendations.recommendation_id,
        source_components.component_name,
        source_components.component_score,
        source_components.component_weight,
        source_components.explanation
    from insert_recommendations
    join source_components on source_components.instrument_id = insert_recommendations.instrument_id
)
select batch_id from upsert_batch;

commit;
"""


def run_recommendation_bootstrap(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    market_code: str = _DEFAULT_MARKET_CODE,
    score_version: str = _DEFAULT_SCORE_VERSION,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    candidates = load_recommendation_candidates(
        config=config,
        as_of_date=as_of_date,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        universe_version=universe_version,
        market_code=market_code,
        executor=sql_executor,
    )
    recommendation_rows = compute_recommendation_rows(candidates)
    universe_batch_id = candidates[0].universe_batch_id
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="recommendation_bootstrap",
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "universe_version": universe_version,
            "score_version": score_version,
            "candidate_count": len(candidates),
            "recommendation_count": len(recommendation_rows),
            "score_component_count": _score_component_row_count(recommendation_rows),
        },
    )
    try:
        batch_id = int(
            sql_executor.execute_scalar(
                render_recommendation_upsert_sql(
                    recommendation_rows,
                    as_of_date=as_of_date,
                    market_code=market_code,
                    strategy_name=strategy_name,
                    horizon_type=horizon_type,
                    universe_version=universe_version,
                    score_version=score_version,
                    source_run_id=run_id,
                )
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    bucket_counts: dict[str, int] = {}
    for row in recommendation_rows:
        bucket_counts[row.bucket] = bucket_counts.get(row.bucket, 0) + 1

    return {
        "run_id": run_id,
        "batch_id": batch_id,
        "universe_batch_id": universe_batch_id,
        "as_of_date": as_of_date.isoformat(),
        "market_code": market_code,
        "strategy_name": strategy_name,
        "horizon_type": horizon_type,
        "universe_version": universe_version,
        "score_version": score_version,
        "candidate_count": len(candidates),
        "recommendation_count": len(recommendation_rows),
        "score_component_count": _score_component_row_count(recommendation_rows),
        "bucket_counts": bucket_counts,
        "recommended_symbol_preview": [row.primary_symbol for row in recommendation_rows[:10]],
        "node_code_preview": [row.node_code for row in recommendation_rows[:10]],
    }


def _compute_component_scores(candidate: RecommendationCandidate) -> dict[str, Decimal]:
    return {
        "cycle_score": _clamp_decimal(candidate.cycle_score),
        "momentum_score": _compute_medium_momentum_score(candidate),
        "short_term_score": _normalize_return(
            candidate.return_1d,
            minimum=_RETURN_SHORT_MIN,
            maximum=_RETURN_SHORT_MAX,
            default=Decimal("0.5"),
        ),
        "rank_score": _compute_rank_score(candidate),
        "macro_flow_score": _clamp_decimal(candidate.macro_flow_score or Decimal("0")),
    }


def _compute_medium_momentum_score(candidate: RecommendationCandidate) -> Decimal:
    if candidate.return_since_first_zscore is not None:
        return _normalize_decimal(
            candidate.return_since_first_zscore,
            minimum=_ZSCORE_MIN,
            maximum=_ZSCORE_MAX,
        )
    return _normalize_return(
        candidate.return_since_first,
        minimum=_RETURN_MEDIUM_MIN,
        maximum=_RETURN_MEDIUM_MAX,
        default=Decimal("0.5"),
    )


def _compute_rank_score(candidate: RecommendationCandidate) -> Decimal:
    if candidate.universe_member_count <= 1:
        return Decimal("1")
    numerator = Decimal(candidate.universe_member_count - candidate.universe_rank_position)
    denominator = Decimal(candidate.universe_member_count - 1)
    return _clamp_decimal(numerator / denominator)


def _bucket_action_and_weight(total_score: Decimal) -> tuple[str, str, Decimal | None]:
    if total_score >= Decimal("0.7500"):
        return "core", "buy_candidate", Decimal("0.0800")
    if total_score >= Decimal("0.5500"):
        return "cycle", "accumulate_candidate", Decimal("0.0400")
    if total_score >= Decimal("0.3500"):
        return "watch", "watch", None
    return "avoid", "exclude", None


def _render_recommendation_value_tuple(row: RecommendationRow) -> str:
    return "(" + ", ".join(
        (
            f"{row.instrument_id}::bigint",
            sql_literal(row.bucket),
            sql_literal(row.action),
            f"{row.rank_position}::integer",
            sql_numeric(row.total_score),
            sql_numeric(row.recommended_weight) if row.recommended_weight is not None else "null::numeric",
        )
    ) + ")"


def _render_score_component_value_tuple(row: RecommendationRow) -> str:
    tuples = []
    for component_name in _COMPONENT_ORDER:
        component_score = Decimal(str(row.component_scores[component_name]))
        tuples.append(
            "(" + ", ".join(
                (
                    f"{row.instrument_id}::bigint",
                    sql_literal(component_name),
                    sql_numeric(component_score),
                    sql_numeric(_component_weight(component_name)),
                    sql_literal(_COMPONENT_EXPLANATIONS[component_name]),
                )
            ) + ")"
        )
    return ",\n        ".join(tuples)


def _score_component_row_count(rows: tuple[RecommendationRow, ...]) -> int:
    return sum(len(row.component_scores) for row in rows)


def _normalize_return(
    value: Decimal | None,
    *,
    minimum: Decimal,
    maximum: Decimal,
    default: Decimal,
) -> Decimal:
    if value is None:
        return default
    return _normalize_decimal(value, minimum=minimum, maximum=maximum)


def _normalize_decimal(value: Decimal, *, minimum: Decimal, maximum: Decimal) -> Decimal:
    if maximum <= minimum:
        raise ValueError("maximum must be greater than minimum")
    return _clamp_decimal((value - minimum) / (maximum - minimum))


def _clamp_decimal(value: Decimal) -> Decimal:
    if value < 0:
        return Decimal("0")
    if value > 1:
        return Decimal("1")
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)


def _macro_flow_weight() -> Decimal:
    raw = os.environ.get(MACRO_FLOW_WEIGHT_ENV, "").strip()
    if not raw:
        return _MACRO_FLOW_WEIGHT_DEFAULT
    try:
        return _clamp_decimal(Decimal(raw))
    except Exception:
        return _MACRO_FLOW_WEIGHT_DEFAULT


def _component_weight(component_name: str) -> Decimal:
    if component_name == "macro_flow_score":
        return _macro_flow_weight()
    return _COMPONENT_WEIGHTS[component_name]
