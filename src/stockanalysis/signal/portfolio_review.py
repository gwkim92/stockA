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
_DEFAULT_REVIEW_VERSION = "bootstrap-v1"
_DEFAULT_REVIEW_SOURCE = "deterministic_bootstrap"
_DECIMAL_QUANTIZER = Decimal("0.0001")
_TIGHTEN_ACTIONS = {"exit", "reduce"}
_MAX_SINGLE_POSITION_WEIGHT = Decimal("0.2500")
_MIN_REBALANCE_TARGET_WEIGHT = Decimal("0.1000")


@dataclass(frozen=True)
class PortfolioReviewCandidate:
    portfolio_id: int
    portfolio_name: str
    instrument_id: int
    primary_symbol: str
    quantity: Decimal
    market_price: Decimal
    market_value: Decimal
    current_weight: Decimal | None
    unrealized_pnl: Decimal | None
    linked_thesis_id: int | None
    thesis_title: str | None
    thesis_status: str | None
    thesis_review_id: int | None
    thesis_review_action: str | None
    thesis_health_score: Decimal | None
    recommendation_id: int | None
    recommendation_bucket: str | None
    recommendation_action: str | None
    recommendation_total_score: Decimal | None
    recommended_weight: Decimal | None
    coverage_measurement_end_date: date | None
    coverage_status: str
    outcome_id: int | None
    outcome_status: str | None
    outcome_success_grade: str | None


@dataclass(frozen=True)
class PortfolioReviewHeader:
    portfolio_id: int
    portfolio_name: str
    review_date: date
    review_source: str
    overall_summary: str
    cash_weight: Decimal | None
    risk_level: str


@dataclass(frozen=True)
class PortfolioReviewItemRow:
    instrument_id: int
    primary_symbol: str
    thesis_id: int | None
    recommendation_id: int | None
    thesis_review_id: int | None
    action: str
    reason: str
    priority: int
    health_score: Decimal | None
    current_weight: Decimal | None
    recommended_weight: Decimal | None
    weight_gap: Decimal | None
    market_value: Decimal
    unrealized_pnl: Decimal | None


def load_portfolio_review_candidates(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    as_of_date: date,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    market_code: str = _DEFAULT_MARKET_CODE,
    review_source: str = _DEFAULT_REVIEW_SOURCE,
    coverage_measurement_end_date: date | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> tuple[PortfolioReviewCandidate, ...]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload_text = sql_executor.execute_scalar(
        render_portfolio_review_candidate_lookup_sql(
            portfolio_name=portfolio_name,
            as_of_date=as_of_date,
            market_code=market_code,
            strategy_name=strategy_name,
            horizon_type=horizon_type,
            universe_version=universe_version,
            review_source=review_source,
            coverage_measurement_end_date=coverage_measurement_end_date,
        )
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Portfolio review candidate lookup did not return a JSON array.")

    candidates: list[PortfolioReviewCandidate] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Portfolio review candidate lookup returned a non-object row.")
        candidates.append(
            PortfolioReviewCandidate(
                portfolio_id=int(item["portfolio_id"]),
                portfolio_name=str(item["portfolio_name"]),
                instrument_id=int(item["instrument_id"]),
                primary_symbol=str(item["primary_symbol"]).upper(),
                quantity=Decimal(str(item["quantity"])),
                market_price=Decimal(str(item["market_price"])),
                market_value=Decimal(str(item["market_value"])),
                current_weight=_optional_decimal(item.get("current_weight")),
                unrealized_pnl=_optional_decimal(item.get("unrealized_pnl")),
                linked_thesis_id=int(item["linked_thesis_id"]) if item.get("linked_thesis_id") is not None else None,
                thesis_title=str(item["thesis_title"]) if item.get("thesis_title") is not None else None,
                thesis_status=str(item["thesis_status"]) if item.get("thesis_status") is not None else None,
                thesis_review_id=int(item["thesis_review_id"]) if item.get("thesis_review_id") is not None else None,
                thesis_review_action=str(item["thesis_review_action"])
                if item.get("thesis_review_action") is not None
                else None,
                thesis_health_score=_optional_decimal(item.get("thesis_health_score")),
                recommendation_id=int(item["recommendation_id"]) if item.get("recommendation_id") is not None else None,
                recommendation_bucket=str(item["recommendation_bucket"])
                if item.get("recommendation_bucket") is not None
                else None,
                recommendation_action=str(item["recommendation_action"])
                if item.get("recommendation_action") is not None
                else None,
                recommendation_total_score=_optional_decimal(item.get("recommendation_total_score")),
                recommended_weight=_optional_decimal(item.get("recommended_weight")),
                coverage_measurement_end_date=date.fromisoformat(str(item["coverage_measurement_end_date"]))
                if item.get("coverage_measurement_end_date") is not None
                else None,
                coverage_status=str(item.get("coverage_status") or "not_requested"),
                outcome_id=int(item["outcome_id"]) if item.get("outcome_id") is not None else None,
                outcome_status=str(item["outcome_status"]) if item.get("outcome_status") is not None else None,
                outcome_success_grade=str(item["outcome_success_grade"])
                if item.get("outcome_success_grade") is not None
                else None,
            )
        )

    if not candidates:
        raise ValueError("No portfolio review candidates matched the requested portfolio snapshot.")
    return tuple(candidates)


def render_portfolio_review_candidate_lookup_sql(
    *,
    portfolio_name: str,
    as_of_date: date,
    market_code: str,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    review_source: str,
    coverage_measurement_end_date: date | None = None,
) -> str:
    if coverage_measurement_end_date is None:
        coverage_join = ""
        coverage_fields = """null::date as coverage_measurement_end_date,
        'not_requested'::text as coverage_status,
        null::bigint as outcome_id,
        null::text as outcome_status,
        null::text as outcome_success_grade"""
    else:
        coverage_join = f"""
    left join performance.thesis_outcome outcome
      on outcome.thesis_id = position.linked_thesis_id
     and outcome.measurement_start_date = {sql_date(as_of_date)}
     and outcome.measurement_end_date = {sql_date(coverage_measurement_end_date)}"""
        coverage_fields = f"""{sql_date(coverage_measurement_end_date)} as coverage_measurement_end_date,
        case
            when position.linked_thesis_id is null then 'missing_thesis'
            when position.current_weight is null then 'missing_weight'
            when outcome.outcome_id is null then 'missing_outcome'
            else 'covered'
        end as coverage_status,
        outcome.outcome_id,
        outcome.status as outcome_status,
        outcome.success_grade as outcome_success_grade"""

    return f"""-- portfolio review candidate lookup
with selected_portfolio as (
    select portfolio_id, portfolio_name, market_code, strategy_name
    from portfolio.portfolio
    where portfolio_name = {sql_literal(portfolio_name)}
      and market_code = {sql_literal(market_code)}
    limit 1
),
selected_batch as (
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
position_rows as (
    select
        portfolio.portfolio_id,
        portfolio.portfolio_name,
        position.instrument_id,
        instrument.primary_symbol,
        position.quantity,
        position.market_price,
        position.market_value,
        position.weight as current_weight,
        position.unrealized_pnl,
        position.linked_thesis_id
    from selected_portfolio portfolio
    join portfolio.position_snapshot position on position.portfolio_id = portfolio.portfolio_id
    join ref.instrument instrument on instrument.instrument_id = position.instrument_id
    where position.snapshot_date = {sql_date(as_of_date)}
      and position.quantity <> 0
),
candidate_rows as (
    select
        position.portfolio_id,
        position.portfolio_name,
        position.instrument_id,
        position.primary_symbol,
        position.quantity,
        position.market_price,
        position.market_value,
        position.current_weight,
        position.unrealized_pnl,
        thesis.thesis_id as linked_thesis_id,
        thesis.title as thesis_title,
        thesis.status as thesis_status,
        thesis_review.review_id as thesis_review_id,
        thesis_review.action as thesis_review_action,
        thesis_review.health_score as thesis_health_score,
        recommendation.recommendation_id,
        recommendation.bucket as recommendation_bucket,
        recommendation.action as recommendation_action,
        recommendation.total_score as recommendation_total_score,
        recommendation.recommended_weight,
        {coverage_fields}
    from position_rows position
    left join selected_batch batch on true
    left join signal.recommendation recommendation
      on recommendation.batch_id = batch.batch_id
     and recommendation.instrument_id = position.instrument_id
     and recommendation.status = 'active'
    left join signal.investment_thesis thesis
      on thesis.thesis_id = coalesce(position.linked_thesis_id, recommendation.thesis_id)
     and thesis.status = 'active'
    left join signal.thesis_review thesis_review
      on thesis_review.thesis_id = thesis.thesis_id
     and thesis_review.review_date = {sql_date(as_of_date)}
     and thesis_review.review_source = {sql_literal(review_source)}
{coverage_join}
)
select coalesce(
    json_agg(
        json_build_object(
            'portfolio_id', portfolio_id,
            'portfolio_name', portfolio_name,
            'instrument_id', instrument_id,
            'primary_symbol', primary_symbol,
            'quantity', quantity,
            'market_price', market_price,
            'market_value', market_value,
            'current_weight', current_weight,
            'unrealized_pnl', unrealized_pnl,
            'linked_thesis_id', linked_thesis_id,
            'thesis_title', thesis_title,
            'thesis_status', thesis_status,
            'thesis_review_id', thesis_review_id,
            'thesis_review_action', thesis_review_action,
            'thesis_health_score', thesis_health_score,
            'recommendation_id', recommendation_id,
            'recommendation_bucket', recommendation_bucket,
            'recommendation_action', recommendation_action,
            'recommendation_total_score', recommendation_total_score,
            'recommended_weight', recommended_weight,
            'coverage_measurement_end_date', coverage_measurement_end_date,
            'coverage_status', coverage_status,
            'outcome_id', outcome_id,
            'outcome_status', outcome_status,
            'outcome_success_grade', outcome_success_grade
        )
        order by primary_symbol
    ),
    '[]'::json
)::text
from candidate_rows;"""


def build_portfolio_review(
    candidates: tuple[PortfolioReviewCandidate, ...],
    *,
    review_date: date,
    review_source: str = _DEFAULT_REVIEW_SOURCE,
) -> tuple[PortfolioReviewHeader, tuple[PortfolioReviewItemRow, ...]]:
    if not candidates:
        raise ValueError("At least one portfolio review candidate is required.")

    portfolio_id = candidates[0].portfolio_id
    portfolio_name = candidates[0].portfolio_name
    if any(candidate.portfolio_id != portfolio_id for candidate in candidates):
        raise ValueError("Portfolio review candidates must belong to one portfolio.")

    item_rows: list[PortfolioReviewItemRow] = []
    for candidate in candidates:
        action = _portfolio_action(candidate)
        item_rows.append(
            PortfolioReviewItemRow(
                instrument_id=candidate.instrument_id,
                primary_symbol=candidate.primary_symbol,
                thesis_id=candidate.linked_thesis_id,
                recommendation_id=candidate.recommendation_id,
                thesis_review_id=candidate.thesis_review_id,
                action=action,
                reason=_reason(candidate, action=action),
                priority=_priority(action),
                health_score=_health_score(candidate),
                current_weight=_quantize_optional(candidate.current_weight),
                recommended_weight=_quantize_optional(candidate.recommended_weight),
                weight_gap=_weight_gap(candidate),
                market_value=_quantize_money(candidate.market_value),
                unrealized_pnl=_quantize_money_optional(candidate.unrealized_pnl),
            )
        )

    action_counts = _action_counts(tuple(item_rows))
    coverage_status_counts = _coverage_status_counts(candidates)
    header = PortfolioReviewHeader(
        portfolio_id=portfolio_id,
        portfolio_name=portfolio_name,
        review_date=review_date,
        review_source=review_source,
        overall_summary=_overall_summary(
            portfolio_name,
            review_date=review_date,
            action_counts=action_counts,
            coverage_status_counts=coverage_status_counts,
        ),
        cash_weight=_cash_weight(candidates),
        risk_level=_risk_level(tuple(item_rows)),
    )
    return header, tuple(item_rows)


def render_portfolio_review_upsert_sql(
    header: PortfolioReviewHeader,
    item_rows: tuple[PortfolioReviewItemRow, ...],
    *,
    source_run_id: int,
) -> str:
    if not item_rows:
        raise ValueError("At least one portfolio review item row is required.")
    value_rows = ",\n        ".join(_render_item_value_tuple(row) for row in item_rows)
    return f"""begin;

with upsert_review as (
    insert into portfolio.review (
        portfolio_id,
        review_date,
        review_source,
        overall_summary,
        cash_weight,
        risk_level,
        source_run_id
    )
    values (
        {header.portfolio_id}::bigint,
        {sql_date(header.review_date)},
        {_sql_text(header.review_source)},
        {_sql_text(header.overall_summary)},
        {_sql_numeric_or_null(header.cash_weight)},
        {_sql_text(header.risk_level)},
        {source_run_id}::bigint
    )
    on conflict (portfolio_id, review_date, review_source) do update
    set
        overall_summary = excluded.overall_summary,
        cash_weight = excluded.cash_weight,
        risk_level = excluded.risk_level,
        source_run_id = excluded.source_run_id
    returning portfolio_review_id
),
delete_existing_items as (
    delete from portfolio.review_item
    where portfolio_review_id = (select portfolio_review_id from upsert_review)
    returning review_item_id
),
source_items (
    instrument_id,
    thesis_id,
    recommendation_id,
    thesis_review_id,
    action,
    reason,
    priority,
    health_score,
    current_weight,
    recommended_weight,
    weight_gap,
    market_value,
    unrealized_pnl
) as (
    values
        {value_rows}
),
insert_items as (
    insert into portfolio.review_item (
        portfolio_review_id,
        instrument_id,
        thesis_id,
        recommendation_id,
        thesis_review_id,
        action,
        reason,
        priority,
        health_score,
        current_weight,
        recommended_weight,
        weight_gap,
        market_value,
        unrealized_pnl
    )
    select
        upsert_review.portfolio_review_id,
        source_items.instrument_id,
        source_items.thesis_id,
        source_items.recommendation_id,
        source_items.thesis_review_id,
        source_items.action,
        source_items.reason,
        source_items.priority,
        source_items.health_score,
        source_items.current_weight,
        source_items.recommended_weight,
        source_items.weight_gap,
        source_items.market_value,
        source_items.unrealized_pnl
    from upsert_review
    join source_items on true
    returning review_item_id
)
select json_build_object(
    'portfolio_review_id', (select portfolio_review_id from upsert_review),
    'deleted_item_count', (select count(*) from delete_existing_items),
    'item_count', (select count(*) from insert_items)
)::text;

commit;
"""


def run_portfolio_review_bootstrap(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    as_of_date: date,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    market_code: str = _DEFAULT_MARKET_CODE,
    review_version: str = _DEFAULT_REVIEW_VERSION,
    review_source: str = _DEFAULT_REVIEW_SOURCE,
    coverage_measurement_end_date: date | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    candidates = load_portfolio_review_candidates(
        config=config,
        portfolio_name=portfolio_name,
        as_of_date=as_of_date,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        universe_version=universe_version,
        market_code=market_code,
        review_source=review_source,
        coverage_measurement_end_date=coverage_measurement_end_date,
        executor=sql_executor,
    )
    header, item_rows = build_portfolio_review(candidates, review_date=as_of_date, review_source=review_source)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="portfolio_review_bootstrap",
        config_json={
            "portfolio_name": portfolio_name,
            "as_of_date": as_of_date.isoformat(),
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "universe_version": universe_version,
            "review_version": review_version,
            "review_source": review_source,
            "coverage_measurement_end_date": coverage_measurement_end_date.isoformat()
            if coverage_measurement_end_date is not None
            else None,
            "candidate_count": len(candidates),
            "review_item_count": len(item_rows),
            "coverage_status_counts": _coverage_status_counts(candidates),
        },
    )
    try:
        result = json.loads(
            sql_executor.execute_scalar(
                render_portfolio_review_upsert_sql(header, item_rows, source_run_id=run_id)
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    action_counts = _action_counts(item_rows)
    coverage_status_counts = _coverage_status_counts(candidates)
    return {
        "run_id": run_id,
        "portfolio_review_id": int(result["portfolio_review_id"]),
        "portfolio_name": portfolio_name,
        "as_of_date": as_of_date.isoformat(),
        "market_code": market_code,
        "strategy_name": strategy_name,
        "horizon_type": horizon_type,
        "universe_version": universe_version,
        "review_version": review_version,
        "review_source": review_source,
        "coverage_measurement_end_date": coverage_measurement_end_date.isoformat()
        if coverage_measurement_end_date is not None
        else None,
        "candidate_count": len(candidates),
        "review_item_count": int(result["item_count"]),
        "action_counts": action_counts,
        "coverage_status_counts": coverage_status_counts,
        "cash_weight": str(header.cash_weight) if header.cash_weight is not None else None,
        "risk_level": header.risk_level,
        "symbol_preview": [row.primary_symbol for row in item_rows[:10]],
    }


def _portfolio_action(candidate: PortfolioReviewCandidate) -> str:
    if candidate.coverage_status == "missing_thesis":
        return "needs_thesis_review"
    if candidate.coverage_status == "missing_outcome":
        return "needs_outcome_review"
    if candidate.coverage_status == "missing_weight":
        return "needs_weight_review"
    if candidate.thesis_review_action == "exit":
        return "exit_review"
    if candidate.thesis_review_action == "reduce":
        return "reduce_review"
    if candidate.thesis_review_action == "watch":
        return "monitor"
    if candidate.linked_thesis_id is None and candidate.recommendation_id is None:
        return "needs_thesis_review"
    if candidate.current_weight is None or candidate.recommended_weight is None:
        return "hold"

    lower_bound = candidate.recommended_weight * Decimal("0.75")
    if candidate.current_weight < lower_bound:
        return "increase_to_target"
    if candidate.current_weight > _MAX_SINGLE_POSITION_WEIGHT:
        return "trim_to_target"
    if candidate.recommended_weight >= _MIN_REBALANCE_TARGET_WEIGHT:
        upper_bound = candidate.recommended_weight * Decimal("1.25")
        if candidate.current_weight > upper_bound:
            return "trim_to_target"
    return "hold"


def _priority(action: str) -> int:
    if action == "exit_review":
        return 1
    if action == "reduce_review":
        return 2
    if action in {
        "increase_to_target",
        "trim_to_target",
        "needs_thesis_review",
        "needs_outcome_review",
        "needs_weight_review",
    }:
        return 3
    return 4


def _health_score(candidate: PortfolioReviewCandidate) -> Decimal | None:
    if candidate.thesis_health_score is not None:
        return _quantize(candidate.thesis_health_score)
    if candidate.recommendation_total_score is not None:
        return _quantize(candidate.recommendation_total_score)
    return None


def _weight_gap(candidate: PortfolioReviewCandidate) -> Decimal | None:
    if candidate.current_weight is None or candidate.recommended_weight is None:
        return None
    return _quantize(candidate.recommended_weight - candidate.current_weight)


def _reason(candidate: PortfolioReviewCandidate, *, action: str) -> str:
    thesis_action = candidate.thesis_review_action or "unavailable"
    if candidate.recommended_weight is None:
        recommended_weight = "unavailable"
    else:
        recommended_weight = str(_quantize(candidate.recommended_weight))
    current_weight = "unavailable" if candidate.current_weight is None else str(_quantize(candidate.current_weight))
    return (
        f"{candidate.primary_symbol} portfolio review action {action}. "
        f"Thesis review action {thesis_action}; current weight {current_weight}; "
        f"recommended weight {recommended_weight}; coverage status {candidate.coverage_status}; "
        f"single position review cap {_quantize(_MAX_SINGLE_POSITION_WEIGHT)}."
    )


def _overall_summary(
    portfolio_name: str,
    *,
    review_date: date,
    action_counts: dict[str, int],
    coverage_status_counts: dict[str, int],
) -> str:
    action_text = ", ".join(f"{action}:{count}" for action, count in sorted(action_counts.items()))
    summary = f"{portfolio_name} portfolio review on {review_date.isoformat()}: {action_text}."
    if any(status != "not_requested" for status in coverage_status_counts):
        coverage_text = ", ".join(
            f"{status}:{count}" for status, count in sorted(coverage_status_counts.items())
        )
        summary = f"{summary} Coverage status {coverage_text}."
    return summary


def _risk_level(item_rows: tuple[PortfolioReviewItemRow, ...]) -> str:
    if any(row.action == "exit_review" for row in item_rows):
        return "high"
    if any(row.action == "reduce_review" for row in item_rows):
        return "elevated"
    if any(
        row.action in {"monitor", "needs_thesis_review", "needs_outcome_review", "needs_weight_review"}
        for row in item_rows
    ):
        return "watch"
    return "normal"


def _cash_weight(candidates: tuple[PortfolioReviewCandidate, ...]) -> Decimal | None:
    weights = [candidate.current_weight for candidate in candidates]
    if any(weight is None for weight in weights):
        return None
    invested_weight = sum((weight for weight in weights if weight is not None), Decimal("0"))
    return _quantize(max(Decimal("0"), Decimal("1") - invested_weight))


def _action_counts(item_rows: tuple[PortfolioReviewItemRow, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in item_rows:
        counts[row.action] = counts.get(row.action, 0) + 1
    return counts


def _coverage_status_counts(candidates: tuple[PortfolioReviewCandidate, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for candidate in candidates:
        counts[candidate.coverage_status] = counts.get(candidate.coverage_status, 0) + 1
    return counts


def _render_item_value_tuple(row: PortfolioReviewItemRow) -> str:
    return "(" + ", ".join(
        (
            f"{row.instrument_id}::bigint",
            _sql_bigint_or_null(row.thesis_id),
            _sql_bigint_or_null(row.recommendation_id),
            _sql_bigint_or_null(row.thesis_review_id),
            _sql_text(row.action),
            _sql_text(row.reason),
            f"{row.priority}::integer",
            _sql_numeric_or_null(row.health_score),
            _sql_numeric_or_null(row.current_weight),
            _sql_numeric_or_null(row.recommended_weight),
            _sql_numeric_or_null(row.weight_gap),
            sql_numeric(row.market_value),
            _sql_numeric_or_null(row.unrealized_pnl),
        )
    ) + ")"


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _quantize_optional(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return _quantize(value)


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _quantize_money_optional(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return _quantize_money(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)


def _sql_bigint_or_null(value: int | None) -> str:
    if value is None:
        return "null::bigint"
    return f"{value}::bigint"


def _sql_numeric_or_null(value: Decimal | None) -> str:
    if value is None:
        return "null::numeric"
    return sql_numeric(value)


def _sql_text(value: str) -> str:
    return f"{sql_literal(value)}::text"
