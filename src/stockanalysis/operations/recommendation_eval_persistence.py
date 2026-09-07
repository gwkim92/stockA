from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from stockanalysis.ingest.macro.sql import sql_literal


SNAPSHOT_SCHEMA_VERSION = "recommendation-eval-snapshot-v1"


@dataclass(frozen=True)
class RecommendationEvalSnapshot:
    source_recommendation_id: int
    source_batch_id: int
    source_thesis_id: int | None
    source_outcome_id: int | None
    primary_symbol: str
    recommendation_action: str
    recommendation_total_score: Decimal
    selected_outcome_alpha_pct: Decimal | None
    snapshot_json: dict[str, object]
    snapshot_sha256: str


def render_recommendation_snapshot_projection_sql(*, as_of_date: date, horizon_days: int) -> str:
    if horizon_days < 1 or horizon_days > 3650:
        raise ValueError("horizon_days must be between 1 and 3650.")
    target_date = sql_literal(as_of_date.isoformat())
    schema_version = sql_literal(SNAPSHOT_SCHEMA_VERSION)
    return f"""coalesce(
        (
            select json_agg(snapshot_row.snapshot_json order by snapshot_row.source_recommendation_id)
            from (
                select
                    recommendation.recommendation_id as source_recommendation_id,
                    json_build_object(
                        'snapshot_schema_version', {schema_version},
                        'recommendation', json_build_object(
                            'recommendation_id', recommendation.recommendation_id,
                            'batch_id', recommendation.batch_id,
                            'instrument_id', recommendation.instrument_id,
                            'thesis_id', recommendation.thesis_id,
                            'bucket', recommendation.bucket,
                            'action', recommendation.action,
                            'rank_position', recommendation.rank_position,
                            'total_score', recommendation.total_score,
                            'recommended_weight', recommendation.recommended_weight,
                            'status', recommendation.status
                        ),
                        'batch', json_build_object(
                            'batch_id', batch.batch_id,
                            'as_of_date', batch.as_of_date,
                            'market_code', batch.market_code,
                            'strategy_name', batch.strategy_name,
                            'horizon_type', batch.horizon_type,
                            'universe_version', batch.universe_version,
                            'notes', batch.notes,
                            'source_run_id', batch.source_run_id,
                            'created_at', batch.created_at
                        ),
                        'instrument', json_build_object(
                            'instrument_id', instrument.instrument_id,
                            'primary_symbol', instrument.primary_symbol
                        ),
                        'thesis', case
                            when thesis.thesis_id is null then null
                            else json_build_object(
                                'thesis_id', thesis.thesis_id,
                                'instrument_id', thesis.instrument_id,
                                'primary_node_id', thesis.primary_node_id,
                                'thesis_type', thesis.thesis_type,
                                'title', thesis.title,
                                'summary', thesis.summary,
                                'status', thesis.status,
                                'conviction_score', thesis.conviction_score,
                                'expected_holding_days', thesis.expected_holding_days,
                                'benchmark_code', thesis.benchmark_code,
                                'entry_conditions', thesis.entry_conditions,
                                'invalidation_conditions', thesis.invalidation_conditions,
                                'exit_conditions', thesis.exit_conditions,
                                'created_at', thesis.created_at,
                                'closed_at', thesis.closed_at,
                                'created_by_run_id', thesis.created_by_run_id
                            )
                        end,
                        'score_components', coalesce(components.component_json, '[]'::json),
                        'selected_outcome', case
                            when selected_outcome.outcome_id is null then null
                            else json_build_object(
                                'outcome_id', selected_outcome.outcome_id,
                                'recommendation_id', selected_outcome.recommendation_id,
                                'measurement_start_date', selected_outcome.measurement_start_date,
                                'measurement_end_date', selected_outcome.measurement_end_date,
                                'horizon_days', selected_outcome.horizon_days,
                                'entry_price', selected_outcome.entry_price,
                                'exit_price', selected_outcome.exit_price,
                                'absolute_return_pct', selected_outcome.absolute_return_pct,
                                'benchmark_code', selected_outcome.benchmark_code,
                                'benchmark_return_pct', selected_outcome.benchmark_return_pct,
                                'alpha_pct', selected_outcome.alpha_pct,
                                'max_drawdown_pct', selected_outcome.max_drawdown_pct,
                                'outcome_label', selected_outcome.outcome_label,
                                'source_run_id', selected_outcome.source_run_id,
                                'created_at', selected_outcome.created_at
                            )
                        end
                    ) as snapshot_json
                from signal.recommendation recommendation
                join signal.recommendation_batch batch on batch.batch_id = recommendation.batch_id
                join ref.instrument instrument on instrument.instrument_id = recommendation.instrument_id
                left join signal.investment_thesis thesis on thesis.thesis_id = recommendation.thesis_id
                left join lateral (
                    select json_agg(
                        json_build_object(
                            'component_name', component.component_name,
                            'component_score', component.component_score,
                            'component_weight', component.component_weight,
                            'explanation', component.explanation,
                            'created_at', component.created_at
                        )
                        order by component.component_name
                    ) as component_json
                    from signal.recommendation_score_component component
                    where component.recommendation_id = recommendation.recommendation_id
                ) components on true
                left join lateral (
                    select outcome.*
                    from performance.recommendation_outcome outcome
                    where outcome.recommendation_id = recommendation.recommendation_id
                      and outcome.measurement_end_date <= {target_date}::date
                      and outcome.horizon_days <= {horizon_days}
                    order by outcome.measurement_end_date desc, outcome.outcome_id desc
                    limit 1
                ) selected_outcome on true
                where batch.as_of_date <= {target_date}::date
                  and recommendation.status = 'active'
            ) snapshot_row
        ),
        '[]'::json
    )"""


def build_recommendation_eval_snapshots(payload: dict[str, object]) -> tuple[RecommendationEvalSnapshot, ...]:
    raw_rows = payload.get("recommendation_snapshots")
    if raw_rows is None:
        raise ValueError("Recommendation quality eval payload is missing recommendation_snapshots.")
    if not isinstance(raw_rows, list):
        raise ValueError("recommendation_snapshots must be a JSON array.")

    snapshots: list[RecommendationEvalSnapshot] = []
    seen_recommendation_ids: set[int] = set()
    for raw in raw_rows:
        if not isinstance(raw, dict):
            raise ValueError("recommendation_snapshots contains a non-object row.")
        if raw.get("snapshot_schema_version") != SNAPSHOT_SCHEMA_VERSION:
            raise ValueError("Recommendation snapshot schema version is missing or unsupported.")
        recommendation = _required_dict(raw, "recommendation")
        batch = _required_dict(raw, "batch")
        instrument = _required_dict(raw, "instrument")
        outcome = raw.get("selected_outcome")
        if outcome is not None and not isinstance(outcome, dict):
            raise ValueError("selected_outcome must be an object or null.")

        recommendation_id = _positive_int(recommendation.get("recommendation_id"), "recommendation_id")
        if recommendation_id in seen_recommendation_ids:
            raise ValueError(f"Duplicate recommendation snapshot: {recommendation_id}.")
        seen_recommendation_ids.add(recommendation_id)
        batch_id = _positive_int(batch.get("batch_id"), "batch_id")
        thesis_id = _optional_positive_int(recommendation.get("thesis_id"), "thesis_id")
        outcome_id = _optional_positive_int(outcome.get("outcome_id"), "outcome_id") if outcome else None
        primary_symbol = str(instrument.get("primary_symbol") or "").strip().upper()
        action = str(recommendation.get("action") or "").strip()
        if not primary_symbol:
            raise ValueError("Recommendation snapshot primary_symbol is required.")
        if not action:
            raise ValueError("Recommendation snapshot action is required.")
        total_score = Decimal(str(recommendation.get("total_score")))
        alpha = _optional_decimal(outcome.get("alpha_pct")) if outcome else None

        canonical = canonical_snapshot_json(raw)
        snapshots.append(
            RecommendationEvalSnapshot(
                source_recommendation_id=recommendation_id,
                source_batch_id=batch_id,
                source_thesis_id=thesis_id,
                source_outcome_id=outcome_id,
                primary_symbol=primary_symbol,
                recommendation_action=action,
                recommendation_total_score=total_score,
                selected_outcome_alpha_pct=alpha,
                snapshot_json=raw,
                snapshot_sha256=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            )
        )
    return tuple(snapshots)


def canonical_snapshot_json(snapshot: dict[str, object]) -> str:
    return json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def render_recommendation_quality_eval_persist_sql(
    *,
    eval_name: str,
    dataset_version: str,
    provider: str,
    model_name: str,
    score_json: dict[str, object],
    pipeline_run_id: int,
    as_of_date: date,
    horizon_days: int,
    config_json: dict[str, object],
    snapshots: tuple[RecommendationEvalSnapshot, ...],
) -> str:
    if pipeline_run_id <= 0:
        raise ValueError("pipeline_run_id must be greater than zero.")
    if horizon_days < 1 or horizon_days > 3650:
        raise ValueError("horizon_days must be between 1 and 3650.")
    score_text = json.dumps(score_json, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    config_text = json.dumps(config_json, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    snapshot_source = _render_snapshot_source_cte(snapshots)
    return f"""with inserted_eval as (
    insert into ai.eval_run (
        eval_name,
        dataset_version,
        provider,
        model_name,
        score_json,
        pipeline_run_id,
        as_of_date,
        horizon_days,
        config_json
    )
    values (
        {sql_literal(eval_name)},
        {sql_literal(dataset_version)},
        {sql_literal(provider)},
        {sql_literal(model_name)},
        {sql_literal(score_text)}::jsonb,
        {pipeline_run_id},
        {sql_literal(as_of_date.isoformat())}::date,
        {horizon_days},
        {sql_literal(config_text)}::jsonb
    )
    returning eval_run_id
),
{snapshot_source},
inserted_snapshots as (
    insert into ai.recommendation_eval_snapshot (
        eval_run_id,
        snapshot_schema_version,
        source_recommendation_id,
        source_batch_id,
        source_thesis_id,
        source_outcome_id,
        primary_symbol,
        recommendation_action,
        recommendation_total_score,
        selected_outcome_alpha_pct,
        snapshot_json,
        snapshot_sha256
    )
    select
        inserted_eval.eval_run_id,
        snapshot_source.snapshot_schema_version,
        snapshot_source.source_recommendation_id,
        snapshot_source.source_batch_id,
        snapshot_source.source_thesis_id,
        snapshot_source.source_outcome_id,
        snapshot_source.primary_symbol,
        snapshot_source.recommendation_action,
        snapshot_source.recommendation_total_score,
        snapshot_source.selected_outcome_alpha_pct,
        snapshot_source.snapshot_json,
        snapshot_source.snapshot_sha256
    from snapshot_source
    cross join inserted_eval
    returning snapshot_id
),
snapshot_count as (
    select count(*)::integer as persisted_snapshot_count from inserted_snapshots
)
select inserted_eval.eval_run_id::text
from inserted_eval
cross join snapshot_count;"""


def _render_snapshot_source_cte(snapshots: tuple[RecommendationEvalSnapshot, ...]) -> str:
    columns = """snapshot_source (
    snapshot_schema_version,
    source_recommendation_id,
    source_batch_id,
    source_thesis_id,
    source_outcome_id,
    primary_symbol,
    recommendation_action,
    recommendation_total_score,
    selected_outcome_alpha_pct,
    snapshot_json,
    snapshot_sha256
) as"""
    if not snapshots:
        return f"""{columns} (
    select
        null::text,
        null::bigint,
        null::bigint,
        null::bigint,
        null::bigint,
        null::text,
        null::text,
        null::numeric(8,4),
        null::numeric(12,6),
        null::jsonb,
        null::text
    where false
)"""
    values = ",\n        ".join(_render_snapshot_value(snapshot) for snapshot in snapshots)
    return f"""{columns} (
    values
        {values}
)"""


def _render_snapshot_value(snapshot: RecommendationEvalSnapshot) -> str:
    thesis_id = "null" if snapshot.source_thesis_id is None else str(snapshot.source_thesis_id)
    outcome_id = "null" if snapshot.source_outcome_id is None else str(snapshot.source_outcome_id)
    alpha = "null" if snapshot.selected_outcome_alpha_pct is None else str(snapshot.selected_outcome_alpha_pct)
    snapshot_text = canonical_snapshot_json(snapshot.snapshot_json)
    return (
        f"({sql_literal(SNAPSHOT_SCHEMA_VERSION)}, {snapshot.source_recommendation_id}, "
        f"{snapshot.source_batch_id}, {thesis_id}, {outcome_id}, {sql_literal(snapshot.primary_symbol)}, "
        f"{sql_literal(snapshot.recommendation_action)}, {snapshot.recommendation_total_score}, {alpha}, "
        f"{sql_literal(snapshot_text)}::jsonb, {sql_literal(snapshot.snapshot_sha256)})"
    )


def _required_dict(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Recommendation snapshot {key} must be an object.")
    return value


def _positive_int(value: object, name: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a positive integer.") from exc
    if result <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return result


def _optional_positive_int(value: object, name: str) -> int | None:
    if value is None:
        return None
    return _positive_int(value, name)


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))
