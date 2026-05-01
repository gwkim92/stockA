from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal, sql_numeric
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)

_DEFAULT_MARKET_CODE = "US"
_DEFAULT_THESIS_VERSION = "bootstrap-v1"
_DEFAULT_BENCHMARK_BY_MARKET = {"US": "SPY"}


@dataclass(frozen=True)
class ThesisCandidate:
    batch_id: int
    recommendation_id: int
    instrument_id: int
    primary_symbol: str
    bucket: str
    action: str
    rank_position: int
    total_score: Decimal
    node_id: int
    node_code: str
    node_name: str
    cycle_state: str
    cycle_score: Decimal
    return_1d: Decimal | None
    return_since_first: Decimal | None
    latest_adjusted_close: Decimal | None


@dataclass(frozen=True)
class ThesisRow:
    recommendation_id: int
    instrument_id: int
    primary_symbol: str
    primary_node_id: int
    node_code: str
    node_name: str
    thesis_type: str
    title: str
    summary: str
    status: str
    conviction_score: Decimal
    expected_holding_days: int
    benchmark_code: str | None
    entry_conditions: str
    invalidation_conditions: str
    exit_conditions: str


def load_thesis_candidates(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    market_code: str = _DEFAULT_MARKET_CODE,
    executor: PsqlCommandExecutor | None = None,
) -> tuple[ThesisCandidate, ...]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload_text = sql_executor.execute_scalar(
        render_thesis_candidate_lookup_sql(
            as_of_date=as_of_date,
            market_code=market_code,
            strategy_name=strategy_name,
            horizon_type=horizon_type,
            universe_version=universe_version,
        )
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Thesis candidate lookup did not return a JSON array.")

    candidates: list[ThesisCandidate] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Thesis candidate lookup returned a non-object row.")
        candidates.append(
            ThesisCandidate(
                batch_id=int(item["batch_id"]),
                recommendation_id=int(item["recommendation_id"]),
                instrument_id=int(item["instrument_id"]),
                primary_symbol=str(item["primary_symbol"]).upper(),
                bucket=str(item["bucket"]),
                action=str(item["action"]),
                rank_position=int(item["rank_position"]),
                total_score=Decimal(str(item["total_score"])),
                node_id=int(item["node_id"]),
                node_code=str(item["node_code"]),
                node_name=str(item["node_name"]),
                cycle_state=str(item["cycle_state"]),
                cycle_score=Decimal(str(item["cycle_score"])),
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
        raise ValueError("No thesis candidates matched the requested recommendation batch identity.")
    return tuple(candidates)


def render_thesis_candidate_lookup_sql(
    *,
    as_of_date: date,
    market_code: str,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
) -> str:
    return f"""-- thesis bootstrap candidate lookup
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
active_recommendations as (
    select
        batch.batch_id,
        recommendation.recommendation_id,
        recommendation.instrument_id,
        instrument.primary_symbol,
        recommendation.bucket,
        recommendation.action,
        recommendation.rank_position,
        recommendation.total_score
    from selected_batch batch
    join signal.recommendation recommendation on recommendation.batch_id = batch.batch_id
    join ref.instrument instrument on instrument.instrument_id = recommendation.instrument_id
    where recommendation.status = 'active'
),
evidence_rows as (
    select
        recommendation.batch_id,
        recommendation.recommendation_id,
        recommendation.instrument_id,
        recommendation.primary_symbol,
        recommendation.bucket,
        recommendation.action,
        recommendation.rank_position,
        recommendation.total_score,
        node.node_id,
        node.code as node_code,
        node.name as node_name,
        cycle.cycle_state,
        cycle.cycle_score,
        return_1d.feature_value as return_1d,
        return_since_first.feature_value as return_since_first,
        latest_close.feature_value as latest_adjusted_close,
        row_number() over (
            partition by recommendation.recommendation_id
            order by cycle.cycle_score desc, node.code asc
        )::integer as node_rank
    from active_recommendations recommendation
    join ref.instrument_classification_membership membership
      on membership.instrument_id = recommendation.instrument_id
    join ref.classification_node node on node.node_id = membership.node_id
    join signal.cycle_state_snapshot cycle
      on cycle.node_id = node.node_id
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
    where node.taxonomy_family = 'internal_theme'
      and membership.membership_type = 'derived_theme'
      and membership.valid_from <= {sql_date(as_of_date)}
      and (membership.valid_to is null or membership.valid_to >= {sql_date(as_of_date)})
)
select coalesce(
    json_agg(
        json_build_object(
            'batch_id', batch_id,
            'recommendation_id', recommendation_id,
            'instrument_id', instrument_id,
            'primary_symbol', primary_symbol,
            'bucket', bucket,
            'action', action,
            'rank_position', rank_position,
            'total_score', total_score,
            'node_id', node_id,
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
from evidence_rows
where node_rank = 1;"""


def build_thesis_rows(
    candidates: tuple[ThesisCandidate, ...],
    *,
    strategy_name: str,
    horizon_type: str,
    market_code: str = _DEFAULT_MARKET_CODE,
) -> tuple[ThesisRow, ...]:
    if not candidates:
        raise ValueError("At least one thesis candidate is required.")

    expected_holding_days = _expected_holding_days(horizon_type)
    benchmark_code = _DEFAULT_BENCHMARK_BY_MARKET.get(market_code.upper())
    rows: list[ThesisRow] = []
    for candidate in candidates:
        title = f"{candidate.primary_symbol} {candidate.bucket} thesis via {candidate.node_name}"
        summary = (
            f"{candidate.primary_symbol} is an active {candidate.bucket} recommendation linked to "
            f"{candidate.node_name}. Cycle state is {candidate.cycle_state}; recommendation score is "
            f"{candidate.total_score}."
        )
        rows.append(
            ThesisRow(
                recommendation_id=candidate.recommendation_id,
                instrument_id=candidate.instrument_id,
                primary_symbol=candidate.primary_symbol,
                primary_node_id=candidate.node_id,
                node_code=candidate.node_code,
                node_name=candidate.node_name,
                thesis_type=strategy_name,
                title=title,
                summary=summary,
                status="active",
                conviction_score=candidate.total_score,
                expected_holding_days=expected_holding_days,
                benchmark_code=benchmark_code,
                entry_conditions=(
                    "Keep active recommendation status, selected universe membership, and direct theme/cycle evidence."
                ),
                invalidation_conditions=(
                    "Invalidate if recommendation score falls below 0.3500, cycle state weakens to correcting "
                    "or structurally_broken, or direct theme evidence is removed."
                ),
                exit_conditions="Reduce or exit if invalidation conditions are triggered during review.",
            )
        )
    return tuple(rows)


def render_thesis_upsert_sql(
    thesis_rows: tuple[ThesisRow, ...],
    *,
    source_run_id: int,
) -> str:
    if not thesis_rows:
        raise ValueError("At least one thesis row is required.")
    value_rows = ",\n        ".join(_render_thesis_value_tuple(row, source_run_id=source_run_id) for row in thesis_rows)
    return f"""begin;

with source_rows (
    recommendation_id,
    instrument_id,
    primary_node_id,
    thesis_type,
    title,
    summary,
    status,
    conviction_score,
    expected_holding_days,
    benchmark_code,
    entry_conditions,
    invalidation_conditions,
    exit_conditions,
    created_by_run_id
) as (
    values
        {value_rows}
),
matched_existing as (
    select distinct on (source_rows.recommendation_id)
        source_rows.recommendation_id,
        thesis.thesis_id
    from source_rows
    join signal.investment_thesis thesis
      on thesis.instrument_id = source_rows.instrument_id
     and thesis.primary_node_id is not distinct from source_rows.primary_node_id
     and thesis.thesis_type = source_rows.thesis_type
     and thesis.status = 'active'
    order by source_rows.recommendation_id, thesis.thesis_id desc
),
updated_existing as (
    update signal.investment_thesis thesis
    set
        title = source_rows.title,
        summary = source_rows.summary,
        conviction_score = source_rows.conviction_score,
        expected_holding_days = source_rows.expected_holding_days,
        benchmark_code = source_rows.benchmark_code,
        entry_conditions = source_rows.entry_conditions,
        invalidation_conditions = source_rows.invalidation_conditions,
        exit_conditions = source_rows.exit_conditions,
        created_by_run_id = source_rows.created_by_run_id
    from source_rows
    join matched_existing on matched_existing.recommendation_id = source_rows.recommendation_id
    where thesis.thesis_id = matched_existing.thesis_id
    returning source_rows.recommendation_id, thesis.thesis_id
),
to_insert as (
    select source_rows.*
    from source_rows
    where not exists (
        select 1
        from updated_existing
        where updated_existing.recommendation_id = source_rows.recommendation_id
    )
),
inserted_thesis as (
    insert into signal.investment_thesis (
        instrument_id,
        primary_node_id,
        thesis_type,
        title,
        summary,
        status,
        conviction_score,
        expected_holding_days,
        benchmark_code,
        entry_conditions,
        invalidation_conditions,
        exit_conditions,
        created_by_run_id
    )
    select
        instrument_id,
        primary_node_id,
        thesis_type,
        title,
        summary,
        status,
        conviction_score,
        expected_holding_days,
        benchmark_code,
        entry_conditions,
        invalidation_conditions,
        exit_conditions,
        created_by_run_id
    from to_insert
    returning thesis_id, instrument_id, primary_node_id, thesis_type
),
inserted_links as (
    select
        to_insert.recommendation_id,
        inserted_thesis.thesis_id
    from to_insert
    join inserted_thesis
      on inserted_thesis.instrument_id = to_insert.instrument_id
     and inserted_thesis.primary_node_id is not distinct from to_insert.primary_node_id
     and inserted_thesis.thesis_type = to_insert.thesis_type
),
all_links as (
    select recommendation_id, thesis_id from updated_existing
    union all
    select recommendation_id, thesis_id from inserted_links
),
linked_recommendations as (
    update signal.recommendation recommendation
    set thesis_id = all_links.thesis_id
    from all_links
    where recommendation.recommendation_id = all_links.recommendation_id
    returning recommendation.recommendation_id
)
select count(*) from linked_recommendations;

commit;
"""


def run_thesis_bootstrap(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    market_code: str = _DEFAULT_MARKET_CODE,
    thesis_version: str = _DEFAULT_THESIS_VERSION,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    candidates = load_thesis_candidates(
        config=config,
        as_of_date=as_of_date,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        universe_version=universe_version,
        market_code=market_code,
        executor=sql_executor,
    )
    thesis_rows = build_thesis_rows(
        candidates,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        market_code=market_code,
    )
    batch_id = candidates[0].batch_id
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="thesis_bootstrap",
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "universe_version": universe_version,
            "thesis_version": thesis_version,
            "candidate_count": len(candidates),
            "thesis_count": len(thesis_rows),
        },
    )
    try:
        linked_recommendation_count = int(
            sql_executor.execute_scalar(
                render_thesis_upsert_sql(
                    thesis_rows,
                    source_run_id=run_id,
                )
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return {
        "run_id": run_id,
        "batch_id": batch_id,
        "as_of_date": as_of_date.isoformat(),
        "market_code": market_code,
        "strategy_name": strategy_name,
        "horizon_type": horizon_type,
        "universe_version": universe_version,
        "thesis_version": thesis_version,
        "candidate_count": len(candidates),
        "thesis_count": len(thesis_rows),
        "linked_recommendation_count": linked_recommendation_count,
        "symbol_preview": [row.primary_symbol for row in thesis_rows[:10]],
        "node_code_preview": [row.node_code for row in thesis_rows[:10]],
    }


def _render_thesis_value_tuple(row: ThesisRow, *, source_run_id: int) -> str:
    return "(" + ", ".join(
        (
            f"{row.recommendation_id}::bigint",
            f"{row.instrument_id}::bigint",
            f"{row.primary_node_id}::bigint",
            _sql_text(row.thesis_type),
            _sql_text(row.title),
            _sql_text(row.summary),
            _sql_text(row.status),
            sql_numeric(row.conviction_score),
            f"{row.expected_holding_days}::integer",
            _sql_text_or_null(row.benchmark_code),
            _sql_text(row.entry_conditions),
            _sql_text(row.invalidation_conditions),
            _sql_text(row.exit_conditions),
            f"{source_run_id}::bigint",
        )
    ) + ")"


def _expected_holding_days(horizon_type: str) -> int:
    normalized = horizon_type.lower()
    if "long" in normalized:
        return 365
    if "medium" in normalized:
        return 180
    return 180


def _sql_text(value: str) -> str:
    return f"{sql_literal(value)}::text"


def _sql_text_or_null(value: str | None) -> str:
    if value is None:
        return "null::text"
    return _sql_text(value)
