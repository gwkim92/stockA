from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
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
_DEFAULT_REVIEW_VERSION = "bootstrap-v1"
_DEFAULT_REVIEW_SOURCE = "deterministic_bootstrap"
_DECIMAL_QUANTIZER = Decimal("0.0001")
_EXIT_STATES = {"structurally_broken"}
_REDUCE_STATES = {"correcting"}


@dataclass(frozen=True)
class ThesisReviewCandidate:
    batch_id: int
    recommendation_id: int
    thesis_id: int
    instrument_id: int
    primary_symbol: str
    thesis_type: str
    thesis_title: str
    bucket: str
    action: str
    rank_position: int
    total_score: Decimal
    primary_node_id: int | None
    node_code: str | None
    node_name: str | None
    cycle_state: str | None
    cycle_score: Decimal | None
    return_1d: Decimal | None
    return_since_first: Decimal | None
    latest_adjusted_close: Decimal | None


@dataclass(frozen=True)
class ThesisReviewRow:
    thesis_id: int
    primary_symbol: str
    review_date: date
    review_source: str
    action: str
    health_score: Decimal
    summary: str
    change_notes: str
    next_review_date: date


def load_thesis_review_candidates(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    market_code: str = _DEFAULT_MARKET_CODE,
    executor: PsqlCommandExecutor | None = None,
) -> tuple[ThesisReviewCandidate, ...]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload_text = sql_executor.execute_scalar(
        render_thesis_review_candidate_lookup_sql(
            as_of_date=as_of_date,
            market_code=market_code,
            strategy_name=strategy_name,
            horizon_type=horizon_type,
            universe_version=universe_version,
        )
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Thesis review candidate lookup did not return a JSON array.")

    candidates: list[ThesisReviewCandidate] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Thesis review candidate lookup returned a non-object row.")
        candidates.append(
            ThesisReviewCandidate(
                batch_id=int(item["batch_id"]),
                recommendation_id=int(item["recommendation_id"]),
                thesis_id=int(item["thesis_id"]),
                instrument_id=int(item["instrument_id"]),
                primary_symbol=str(item["primary_symbol"]).upper(),
                thesis_type=str(item["thesis_type"]),
                thesis_title=str(item["thesis_title"]),
                bucket=str(item["bucket"]),
                action=str(item["action"]),
                rank_position=int(item["rank_position"]),
                total_score=Decimal(str(item["total_score"])),
                primary_node_id=int(item["primary_node_id"]) if item.get("primary_node_id") is not None else None,
                node_code=str(item["node_code"]) if item.get("node_code") is not None else None,
                node_name=str(item["node_name"]) if item.get("node_name") is not None else None,
                cycle_state=str(item["cycle_state"]) if item.get("cycle_state") is not None else None,
                cycle_score=Decimal(str(item["cycle_score"])) if item.get("cycle_score") is not None else None,
                return_1d=Decimal(str(item["return_1d"])) if item.get("return_1d") is not None else None,
                return_since_first=Decimal(str(item["return_since_first"]))
                if item.get("return_since_first") is not None
                else None,
                latest_adjusted_close=Decimal(str(item["latest_adjusted_close"]))
                if item.get("latest_adjusted_close") is not None
                else None,
            )
        )

    if not candidates:
        raise ValueError("No thesis review candidates matched the requested recommendation batch identity.")
    return tuple(candidates)


def render_thesis_review_candidate_lookup_sql(
    *,
    as_of_date: date,
    market_code: str,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
) -> str:
    return f"""-- thesis review candidate lookup
with selected_batch as (
    select batch_id
    from signal.recommendation_batch
    where as_of_date = {sql_date(as_of_date)}
      and market_code = {sql_literal(market_code)}
      and strategy_name = {sql_literal(strategy_name)}
      and horizon_type = {sql_literal(horizon_type)}
      and universe_version = {sql_literal(universe_version)}
    order by batch_id desc
    limit 1
),
linked_recommendations as (
    select
        batch.batch_id,
        recommendation.recommendation_id,
        recommendation.instrument_id,
        recommendation.thesis_id,
        instrument.primary_symbol,
        recommendation.bucket,
        recommendation.action,
        recommendation.rank_position,
        recommendation.total_score
    from selected_batch batch
    join signal.recommendation recommendation on recommendation.batch_id = batch.batch_id
    join ref.instrument instrument on instrument.instrument_id = recommendation.instrument_id
    where recommendation.status = 'active'
      and recommendation.thesis_id is not null
),
candidate_rows as (
    select
        recommendation.batch_id,
        recommendation.recommendation_id,
        recommendation.thesis_id,
        recommendation.instrument_id,
        recommendation.primary_symbol,
        thesis.thesis_type,
        thesis.title as thesis_title,
        recommendation.bucket,
        recommendation.action,
        recommendation.rank_position,
        recommendation.total_score,
        thesis.primary_node_id,
        node.code as node_code,
        node.name as node_name,
        cycle.cycle_state,
        cycle.cycle_score,
        return_1d.feature_value as return_1d,
        return_since_first.feature_value as return_since_first,
        latest_close.feature_value as latest_adjusted_close
    from linked_recommendations recommendation
    join signal.investment_thesis thesis
      on thesis.thesis_id = recommendation.thesis_id
     and thesis.status = 'active'
    left join ref.classification_node node on node.node_id = thesis.primary_node_id
    left join signal.cycle_state_snapshot cycle
      on cycle.node_id = thesis.primary_node_id
     and cycle.as_of_date = {sql_date(as_of_date)}
    left join signal.instrument_feature_value return_1d
      on return_1d.instrument_id = recommendation.instrument_id
     and return_1d.as_of_date = {sql_date(as_of_date)}
     and return_1d.feature_code = 'return_1d'
    left join signal.instrument_feature_value return_since_first
      on return_since_first.instrument_id = recommendation.instrument_id
     and return_since_first.as_of_date = {sql_date(as_of_date)}
     and return_since_first.feature_code = 'return_since_first_observation'
    left join signal.instrument_feature_value latest_close
      on latest_close.instrument_id = recommendation.instrument_id
     and latest_close.as_of_date = {sql_date(as_of_date)}
     and latest_close.feature_code = 'latest_adjusted_close'
)
select coalesce(
    json_agg(
        json_build_object(
            'batch_id', batch_id,
            'recommendation_id', recommendation_id,
            'thesis_id', thesis_id,
            'instrument_id', instrument_id,
            'primary_symbol', primary_symbol,
            'thesis_type', thesis_type,
            'thesis_title', thesis_title,
            'bucket', bucket,
            'action', action,
            'rank_position', rank_position,
            'total_score', total_score,
            'primary_node_id', primary_node_id,
            'node_code', node_code,
            'node_name', node_name,
            'cycle_state', cycle_state,
            'cycle_score', cycle_score,
            'return_1d', return_1d,
            'return_since_first', return_since_first,
            'latest_adjusted_close', latest_adjusted_close
        )
        order by rank_position, primary_symbol
    ),
    '[]'::json
)::text
from candidate_rows;"""


def build_thesis_review_rows(
    candidates: tuple[ThesisReviewCandidate, ...],
    *,
    review_date: date,
    review_source: str = _DEFAULT_REVIEW_SOURCE,
) -> tuple[ThesisReviewRow, ...]:
    if not candidates:
        raise ValueError("At least one thesis review candidate is required.")

    rows: list[ThesisReviewRow] = []
    for candidate in candidates:
        review_action = _review_action(candidate)
        health_score = _health_score(candidate, review_action=review_action)
        summary = _review_summary(candidate, review_action=review_action)
        rows.append(
            ThesisReviewRow(
                thesis_id=candidate.thesis_id,
                primary_symbol=candidate.primary_symbol,
                review_date=review_date,
                review_source=review_source,
                action=review_action,
                health_score=health_score,
                summary=summary,
                change_notes="Deterministic bootstrap review from linked recommendation and current cycle evidence.",
                next_review_date=_next_review_date(review_date, review_action=review_action),
            )
        )
    return tuple(rows)


def render_thesis_review_upsert_sql(
    review_rows: tuple[ThesisReviewRow, ...],
    *,
    source_run_id: int,
) -> str:
    if not review_rows:
        raise ValueError("At least one thesis review row is required.")
    value_rows = ",\n        ".join(_render_review_value_tuple(row, source_run_id=source_run_id) for row in review_rows)
    return f"""begin;

with source_rows (
    thesis_id,
    review_date,
    review_source,
    action,
    health_score,
    summary,
    change_notes,
    next_review_date,
    source_run_id
) as (
    values
        {value_rows}
),
upserted_reviews as (
    insert into signal.thesis_review (
        thesis_id,
        review_date,
        review_source,
        action,
        health_score,
        summary,
        change_notes,
        next_review_date,
        source_run_id
    )
    select
        thesis_id,
        review_date,
        review_source,
        action,
        health_score,
        summary,
        change_notes,
        next_review_date,
        source_run_id
    from source_rows
    on conflict (thesis_id, review_date, review_source) do update
    set
        action = excluded.action,
        health_score = excluded.health_score,
        summary = excluded.summary,
        change_notes = excluded.change_notes,
        next_review_date = excluded.next_review_date,
        source_run_id = excluded.source_run_id
    returning review_id
)
select count(*) from upserted_reviews;

commit;
"""


def run_thesis_review_bootstrap(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    market_code: str = _DEFAULT_MARKET_CODE,
    review_version: str = _DEFAULT_REVIEW_VERSION,
    review_source: str = _DEFAULT_REVIEW_SOURCE,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    candidates = load_thesis_review_candidates(
        config=config,
        as_of_date=as_of_date,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        universe_version=universe_version,
        market_code=market_code,
        executor=sql_executor,
    )
    review_rows = build_thesis_review_rows(
        candidates,
        review_date=as_of_date,
        review_source=review_source,
    )
    batch_id = candidates[0].batch_id
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="thesis_review_bootstrap",
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "universe_version": universe_version,
            "review_version": review_version,
            "review_source": review_source,
            "candidate_count": len(candidates),
            "review_count": len(review_rows),
        },
    )
    try:
        review_count = int(
            sql_executor.execute_scalar(
                render_thesis_review_upsert_sql(
                    review_rows,
                    source_run_id=run_id,
                )
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    action_counts: dict[str, int] = {}
    for row in review_rows:
        action_counts[row.action] = action_counts.get(row.action, 0) + 1

    return {
        "run_id": run_id,
        "batch_id": batch_id,
        "as_of_date": as_of_date.isoformat(),
        "market_code": market_code,
        "strategy_name": strategy_name,
        "horizon_type": horizon_type,
        "universe_version": universe_version,
        "review_version": review_version,
        "review_source": review_source,
        "candidate_count": len(candidates),
        "review_count": review_count,
        "action_counts": action_counts,
        "symbol_preview": [row.primary_symbol for row in review_rows[:10]],
    }


def _review_action(candidate: ThesisReviewCandidate) -> str:
    if candidate.cycle_state in _EXIT_STATES:
        return "exit"
    if candidate.bucket == "avoid" or candidate.action == "exclude" or candidate.total_score < Decimal("0.3500"):
        return "exit"
    if candidate.cycle_state in _REDUCE_STATES:
        return "reduce"
    if candidate.bucket == "watch" or candidate.action == "watch":
        return "watch"
    return "keep"


def _health_score(candidate: ThesisReviewCandidate, *, review_action: str) -> Decimal:
    score = _clamp_decimal(candidate.total_score)
    if review_action == "exit":
        score = min(score, Decimal("0.2500"))
    elif review_action == "reduce":
        score = min(score, Decimal("0.4500"))
    return _quantize(score)


def _review_summary(candidate: ThesisReviewCandidate, *, review_action: str) -> str:
    if candidate.cycle_state is None:
        cycle_text = "cycle state unavailable"
    else:
        cycle_text = f"cycle state {candidate.cycle_state} score {candidate.cycle_score}"
    return (
        f"{candidate.primary_symbol} thesis review action {review_action}. "
        f"Recommendation bucket {candidate.bucket} score {candidate.total_score}; {cycle_text}."
    )


def _next_review_date(review_date: date, *, review_action: str) -> date:
    if review_action in {"exit", "reduce"}:
        return review_date + timedelta(days=7)
    if review_action == "watch":
        return review_date + timedelta(days=30)
    return review_date + timedelta(days=90)


def _render_review_value_tuple(row: ThesisReviewRow, *, source_run_id: int) -> str:
    return "(" + ", ".join(
        (
            f"{row.thesis_id}::bigint",
            sql_date(row.review_date),
            _sql_text(row.review_source),
            _sql_text(row.action),
            sql_numeric(row.health_score),
            _sql_text(row.summary),
            _sql_text(row.change_notes),
            sql_date(row.next_review_date),
            f"{source_run_id}::bigint",
        )
    ) + ")"


def _clamp_decimal(value: Decimal) -> Decimal:
    if value < 0:
        return Decimal("0")
    if value > 1:
        return Decimal("1")
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)


def _sql_text(value: str) -> str:
    return f"{sql_literal(value)}::text"
