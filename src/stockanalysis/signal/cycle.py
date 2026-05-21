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

_DEFAULT_MARKET_CODE = "US"
_DEFAULT_SCORE_VERSION = "bootstrap-v1"
_DECIMAL_QUANTIZER = Decimal("0.00000001")
_TREND_ZSCORE_MIN = Decimal("-2")
_TREND_ZSCORE_MAX = Decimal("2")
_RETURN_FALLBACK_MIN = Decimal("-0.20")
_RETURN_FALLBACK_MAX = Decimal("0.20")
_EVENT_HEAT_MEMBER_DENOMINATOR = Decimal("2")
_TREND_WEIGHT = Decimal("0.45")
_BREADTH_WEIGHT = Decimal("0.35")
_EVENT_HEAT_WEIGHT = Decimal("0.20")


@dataclass(frozen=True)
class CycleNodeInput:
    universe_batch_id: int
    node_id: int
    node_code: str
    node_name: str
    member_count: int
    positive_return_1d_count: int
    average_return_1d: Decimal | None
    average_return_since_first: Decimal | None
    average_return_since_first_zscore: Decimal | None
    recent_event_count_30d: int
    recent_event_count_90d: int
    average_event_confidence: Decimal | None
    latest_event_date: date | None
    member_symbols: tuple[str, ...]


@dataclass(frozen=True)
class CycleStateSnapshotRow:
    node_id: int
    node_code: str
    node_name: str
    cycle_state: str
    cycle_score: Decimal
    trend_score: Decimal
    event_heat_score: Decimal
    breadth_score: Decimal
    evidence_json: dict[str, object]


def load_cycle_snapshot_inputs(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    market_code: str = _DEFAULT_MARKET_CODE,
    executor: PsqlCommandExecutor | None = None,
) -> tuple[CycleNodeInput, ...]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload_text = sql_executor.execute_scalar(
        render_cycle_snapshot_input_lookup_sql(
            as_of_date=as_of_date,
            market_code=market_code,
            strategy_name=strategy_name,
            horizon_type=horizon_type,
            universe_version=universe_version,
        )
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Cycle snapshot lookup did not return a JSON array.")

    rows: list[CycleNodeInput] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Cycle snapshot lookup returned a non-object row.")
        member_symbols = item.get("member_symbols")
        if not isinstance(member_symbols, list) or not member_symbols:
            raise ValueError("Cycle snapshot lookup returned an empty member symbol list.")
        rows.append(
            CycleNodeInput(
                universe_batch_id=int(item["universe_batch_id"]),
                node_id=int(item["node_id"]),
                node_code=str(item["node_code"]),
                node_name=str(item["node_name"]),
                member_count=int(item["member_count"]),
                positive_return_1d_count=int(item["positive_return_1d_count"]),
                average_return_1d=Decimal(str(item["average_return_1d"])) if item.get("average_return_1d") is not None else None,
                average_return_since_first=Decimal(str(item["average_return_since_first"]))
                if item.get("average_return_since_first") is not None
                else None,
                average_return_since_first_zscore=Decimal(str(item["average_return_since_first_zscore"]))
                if item.get("average_return_since_first_zscore") is not None
                else None,
                recent_event_count_30d=int(item["recent_event_count_30d"]),
                recent_event_count_90d=int(item["recent_event_count_90d"]),
                average_event_confidence=Decimal(str(item["average_event_confidence"]))
                if item.get("average_event_confidence") is not None
                else None,
                latest_event_date=date.fromisoformat(str(item["latest_event_date"]))
                if item.get("latest_event_date") is not None
                else None,
                member_symbols=tuple(str(symbol).upper() for symbol in member_symbols),
            )
        )

    if not rows:
        raise ValueError("No cycle snapshot inputs matched the requested snapshot identity.")
    return tuple(rows)


def render_cycle_snapshot_input_lookup_sql(
    *,
    as_of_date: date,
    market_code: str,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
) -> str:
    return f"""-- cycle snapshot input lookup
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
selected_instruments as (
    select
        m.universe_batch_id,
        m.instrument_id,
        i.primary_symbol
    from selected_batch sb
    join signal.strategy_universe_member m on m.universe_batch_id = sb.universe_batch_id
    join ref.instrument i on i.instrument_id = m.instrument_id
),
selected_node_members as (
    select distinct
        si.universe_batch_id,
        si.instrument_id,
        si.primary_symbol,
        membership.node_id,
        node.code as node_code,
        node.name as node_name
    from selected_instruments si
    join ref.instrument_classification_membership membership on membership.instrument_id = si.instrument_id
    join ref.classification_node node on node.node_id = membership.node_id
    where node.taxonomy_family = 'internal_theme'
      and membership.membership_type = 'derived_theme'
      and membership.valid_from <= {sql_date(as_of_date)}
      and (membership.valid_to is null or membership.valid_to >= {sql_date(as_of_date)})
),
feature_rows as (
    select
        node_members.universe_batch_id,
        node_members.node_id,
        node_members.node_code,
        node_members.node_name,
        node_members.instrument_id,
        node_members.primary_symbol,
        short_term.feature_value as return_1d_value,
        medium_term.feature_value as return_since_first_value,
        medium_term.zscore as return_since_first_zscore
    from selected_node_members node_members
    left join signal.instrument_feature_value short_term
      on short_term.instrument_id = node_members.instrument_id
     and short_term.as_of_date = {sql_date(as_of_date)}
     and short_term.feature_code = 'return_1d'
    left join signal.instrument_feature_value medium_term
      on medium_term.instrument_id = node_members.instrument_id
     and medium_term.as_of_date = {sql_date(as_of_date)}
     and medium_term.feature_code = 'return_since_first_observation'
),
direct_event_impacts as (
    select
        node_members.node_id,
        event_row.event_id,
        event_row.event_at,
        least(
            coalesce(classification_impact.confidence, 1.0),
            coalesce(instrument_impact.confidence, 1.0),
            coalesce(event_row.confidence, 1.0)
        ) as confidence
    from selected_node_members node_members
    join event.event_instrument_impact instrument_impact on instrument_impact.instrument_id = node_members.instrument_id
    join event.event_classification_impact classification_impact
      on classification_impact.event_id = instrument_impact.event_id
     and classification_impact.node_id = node_members.node_id
    join event.event event_row on event_row.event_id = instrument_impact.event_id
    where event_row.event_at < ({sql_date(as_of_date)} + interval '1 day')
),
propagated_event_impacts as (
    select
        node_members.node_id,
        event_row.event_id,
        event_row.event_at,
        least(
            coalesce(propagated_impact.confidence, 1.0),
            coalesce(event_row.confidence, 1.0)
        ) as confidence
    from selected_node_members node_members
    join signal.propagated_instrument_impact propagated_impact
      on propagated_impact.instrument_id = node_members.instrument_id
     and propagated_impact.node_id = node_members.node_id
    join event.event event_row on event_row.event_id = propagated_impact.event_id
    where event_row.event_at < ({sql_date(as_of_date)} + interval '1 day')
),
event_impact_rows as (
    select * from direct_event_impacts
    union all
    select * from propagated_event_impacts
),
event_rows as (
    select
        node_id,
        count(distinct event_id) filter (
            where event_at >= ({sql_date(as_of_date)} - interval '30 day')
              and event_at < ({sql_date(as_of_date)} + interval '1 day')
        )::integer as recent_event_count_30d,
        count(distinct event_id) filter (
            where event_at >= ({sql_date(as_of_date)} - interval '90 day')
              and event_at < ({sql_date(as_of_date)} + interval '1 day')
        )::integer as recent_event_count_90d,
        avg(confidence)::numeric(18,8) as average_event_confidence,
        max((event_at at time zone 'UTC')::date) as latest_event_date
    from event_impact_rows
    group by node_id
)
select coalesce(
    json_agg(
        json_build_object(
            'universe_batch_id', grouped_rows.universe_batch_id,
            'node_id', grouped_rows.node_id,
            'node_code', grouped_rows.node_code,
            'node_name', grouped_rows.node_name,
            'member_count', grouped_rows.member_count,
            'positive_return_1d_count', grouped_rows.positive_return_1d_count,
            'average_return_1d', grouped_rows.average_return_1d,
            'average_return_since_first', grouped_rows.average_return_since_first,
            'average_return_since_first_zscore', grouped_rows.average_return_since_first_zscore,
            'recent_event_count_30d', coalesce(grouped_rows.recent_event_count_30d, 0),
            'recent_event_count_90d', coalesce(grouped_rows.recent_event_count_90d, 0),
            'average_event_confidence', grouped_rows.average_event_confidence,
            'latest_event_date', grouped_rows.latest_event_date,
            'member_symbols', grouped_rows.member_symbols
        )
        order by grouped_rows.node_code
    ),
    '[]'::json
)::text
from (
    select
        feature_rows.universe_batch_id,
        feature_rows.node_id,
        feature_rows.node_code,
        feature_rows.node_name,
        count(*)::integer as member_count,
        count(*) filter (where coalesce(feature_rows.return_1d_value, 0) > 0)::integer as positive_return_1d_count,
        avg(feature_rows.return_1d_value)::numeric(18,8) as average_return_1d,
        avg(feature_rows.return_since_first_value)::numeric(18,8) as average_return_since_first,
        avg(feature_rows.return_since_first_zscore)::numeric(18,8) as average_return_since_first_zscore,
        event_rows.recent_event_count_30d,
        event_rows.recent_event_count_90d,
        event_rows.average_event_confidence,
        event_rows.latest_event_date,
        json_agg(feature_rows.primary_symbol order by feature_rows.primary_symbol) as member_symbols
    from feature_rows
    left join event_rows on event_rows.node_id = feature_rows.node_id
    group by
        feature_rows.universe_batch_id,
        feature_rows.node_id,
        feature_rows.node_code,
        feature_rows.node_name,
        event_rows.recent_event_count_30d,
        event_rows.recent_event_count_90d,
        event_rows.average_event_confidence,
        event_rows.latest_event_date
) grouped_rows;"""


def compute_cycle_state_snapshots(
    rows: tuple[CycleNodeInput, ...],
    *,
    as_of_date: date,
    score_version: str,
) -> tuple[CycleStateSnapshotRow, ...]:
    if not rows:
        raise ValueError("At least one cycle node input is required.")

    output_rows: list[CycleStateSnapshotRow] = []
    for row in rows:
        if row.member_count <= 0:
            raise ValueError("Cycle node input member_count must be greater than 0.")
        trend_score = _compute_trend_score(row)
        breadth_score = _quantize(Decimal(row.positive_return_1d_count) / Decimal(row.member_count))
        event_heat_score = _compute_event_heat_score(row)
        cycle_score = _quantize(
            (trend_score * _TREND_WEIGHT)
            + (breadth_score * _BREADTH_WEIGHT)
            + (event_heat_score * _EVENT_HEAT_WEIGHT)
        )
        cycle_state = _determine_cycle_state(
            cycle_score=cycle_score,
            trend_score=trend_score,
            breadth_score=breadth_score,
            event_heat_score=event_heat_score,
        )
        evidence_json = {
            "score_version": score_version,
            "as_of_date": as_of_date.isoformat(),
            "universe_batch_id": row.universe_batch_id,
            "member_count": row.member_count,
            "positive_return_1d_count": row.positive_return_1d_count,
            "member_symbols": list(row.member_symbols[:10]),
            "average_return_1d": _serialize_decimal(row.average_return_1d),
            "average_return_since_first": _serialize_decimal(row.average_return_since_first),
            "average_return_since_first_zscore": _serialize_decimal(row.average_return_since_first_zscore),
            "recent_event_count_30d": row.recent_event_count_30d,
            "recent_event_count_90d": row.recent_event_count_90d,
            "average_event_confidence": _serialize_decimal(row.average_event_confidence),
            "latest_event_date": row.latest_event_date.isoformat() if row.latest_event_date is not None else None,
            "trend_score": _serialize_decimal(trend_score),
            "breadth_score": _serialize_decimal(breadth_score),
            "event_heat_score": _serialize_decimal(event_heat_score),
            "cycle_score": _serialize_decimal(cycle_score),
        }
        output_rows.append(
            CycleStateSnapshotRow(
                node_id=row.node_id,
                node_code=row.node_code,
                node_name=row.node_name,
                cycle_state=cycle_state,
                cycle_score=cycle_score,
                trend_score=trend_score,
                event_heat_score=event_heat_score,
                breadth_score=breadth_score,
                evidence_json=evidence_json,
            )
        )
    return tuple(output_rows)


def render_cycle_state_snapshot_replace_sql(
    snapshot_rows: tuple[CycleStateSnapshotRow, ...],
    *,
    as_of_date: date,
    source_run_id: int,
) -> str:
    if not snapshot_rows:
        raise ValueError("At least one cycle state snapshot row is required.")
    node_ids = ", ".join(f"{row.node_id}::bigint" for row in snapshot_rows)
    value_rows = ",\n        ".join(
        _render_cycle_state_value_tuple(row, as_of_date=as_of_date, source_run_id=source_run_id) for row in snapshot_rows
    )
    return f"""begin;

delete from signal.cycle_state_snapshot
where as_of_date = {sql_date(as_of_date)}
  and node_id in ({node_ids});

insert into signal.cycle_state_snapshot (
    node_id,
    as_of_date,
    cycle_state,
    cycle_score,
    trend_score,
    earnings_revision_score,
    liquidity_score,
    valuation_score,
    event_heat_score,
    breadth_score,
    source_run_id,
    evidence_json
)
values
        {value_rows};

commit;
"""


def run_cycle_state_snapshot(
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
    inputs = load_cycle_snapshot_inputs(
        config=config,
        as_of_date=as_of_date,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        universe_version=universe_version,
        market_code=market_code,
        executor=sql_executor,
    )
    snapshot_rows = compute_cycle_state_snapshots(
        inputs,
        as_of_date=as_of_date,
        score_version=score_version,
    )
    universe_batch_id = inputs[0].universe_batch_id
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="cycle_state_snapshot",
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "universe_version": universe_version,
            "score_version": score_version,
            "input_node_count": len(inputs),
        },
    )
    try:
        sql_executor.execute_non_query(
            render_cycle_state_snapshot_replace_sql(
                snapshot_rows,
                as_of_date=as_of_date,
                source_run_id=run_id,
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    cycle_state_counts: dict[str, int] = {}
    for row in snapshot_rows:
        cycle_state_counts[row.cycle_state] = cycle_state_counts.get(row.cycle_state, 0) + 1

    return {
        "run_id": run_id,
        "universe_batch_id": universe_batch_id,
        "as_of_date": as_of_date.isoformat(),
        "market_code": market_code,
        "strategy_name": strategy_name,
        "horizon_type": horizon_type,
        "universe_version": universe_version,
        "score_version": score_version,
        "node_count": len(snapshot_rows),
        "node_code_preview": [row.node_code for row in snapshot_rows[:10]],
        "cycle_state_counts": cycle_state_counts,
    }


def _render_cycle_state_value_tuple(
    row: CycleStateSnapshotRow,
    *,
    as_of_date: date,
    source_run_id: int,
) -> str:
    evidence_json = json.dumps(row.evidence_json, ensure_ascii=False, sort_keys=True)
    return "(" + ", ".join(
        (
            f"{row.node_id}::bigint",
            sql_date(as_of_date),
            sql_literal(row.cycle_state),
            sql_numeric(row.cycle_score),
            sql_numeric(row.trend_score),
            "null::numeric",
            "null::numeric",
            "null::numeric",
            sql_numeric(row.event_heat_score),
            sql_numeric(row.breadth_score),
            f"{source_run_id}::bigint",
            f"{sql_literal(evidence_json)}::jsonb",
        )
    ) + ")"


def _compute_trend_score(row: CycleNodeInput) -> Decimal:
    if row.average_return_since_first_zscore is not None:
        span = _TREND_ZSCORE_MAX - _TREND_ZSCORE_MIN
        scaled = (row.average_return_since_first_zscore - _TREND_ZSCORE_MIN) / span
        return _quantize(_clamp_decimal(scaled))
    if row.average_return_since_first is not None:
        span = _RETURN_FALLBACK_MAX - _RETURN_FALLBACK_MIN
        scaled = (row.average_return_since_first - _RETURN_FALLBACK_MIN) / span
        return _quantize(_clamp_decimal(scaled))
    return _quantize(Decimal("0.5"))


def _compute_event_heat_score(row: CycleNodeInput) -> Decimal:
    event_count_basis = Decimal(row.recent_event_count_30d)
    if event_count_basis == 0 and row.recent_event_count_90d > 0:
        event_count_basis = Decimal(row.recent_event_count_90d) / Decimal("3")
    if event_count_basis == 0:
        return _quantize(Decimal("0"))
    confidence = row.average_event_confidence if row.average_event_confidence is not None else Decimal("1")
    denominator = Decimal(row.member_count) * _EVENT_HEAT_MEMBER_DENOMINATOR
    score = (event_count_basis * confidence) / denominator
    return _quantize(_clamp_decimal(score))


def _determine_cycle_state(
    *,
    cycle_score: Decimal,
    trend_score: Decimal,
    breadth_score: Decimal,
    event_heat_score: Decimal,
) -> str:
    if trend_score >= Decimal("0.75") and breadth_score >= Decimal("0.70"):
        if event_heat_score >= Decimal("0.40"):
            return "expanding"
        return "confirming"
    if (
        event_heat_score >= Decimal("0.45")
        and trend_score < Decimal("0.55")
        and breadth_score < Decimal("0.55")
    ):
        return "forming"
    if trend_score <= Decimal("0.25") and breadth_score <= Decimal("0.25"):
        return "correcting"
    if cycle_score >= Decimal("0.65"):
        return "confirming"
    if cycle_score <= Decimal("0.30"):
        return "basing"
    return "forming"


def _clamp_decimal(value: Decimal) -> Decimal:
    if value < 0:
        return Decimal("0")
    if value > 1:
        return Decimal("1")
    return value


def _serialize_decimal(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)
