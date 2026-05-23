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
_DEFAULT_THESIS_VERSION = "holding-bootstrap-v1"
_DEFAULT_BENCHMARK_BY_MARKET = {"US": "SPY"}


@dataclass(frozen=True)
class PortfolioHoldingThesisCandidate:
    portfolio_id: int
    portfolio_name: str
    snapshot_date: date
    instrument_id: int
    primary_symbol: str
    weight: Decimal | None
    market_value: Decimal
    existing_thesis_id: int | None
    node_id: int | None
    node_code: str | None
    node_name: str | None
    cycle_state: str | None
    cycle_score: Decimal | None
    recommendation_action: str | None
    recommendation_score: Decimal | None


@dataclass(frozen=True)
class PortfolioHoldingThesisRow:
    portfolio_id: int
    portfolio_name: str
    snapshot_date: date
    instrument_id: int
    primary_symbol: str
    existing_thesis_id: int | None
    primary_node_id: int | None
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


def load_portfolio_holding_thesis_candidates(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    as_of_date: date,
    strategy_name: str,
    horizon_type: str,
    market_code: str = _DEFAULT_MARKET_CODE,
    executor: PsqlCommandExecutor | None = None,
) -> tuple[PortfolioHoldingThesisCandidate, ...]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload_text = sql_executor.execute_scalar(
        render_portfolio_holding_thesis_candidate_lookup_sql(
            portfolio_name=portfolio_name,
            as_of_date=as_of_date,
            strategy_name=strategy_name,
            horizon_type=horizon_type,
            market_code=market_code,
        )
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Portfolio holding thesis candidate lookup did not return a JSON array.")

    candidates: list[PortfolioHoldingThesisCandidate] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Portfolio holding thesis candidate lookup returned a non-object row.")
        candidates.append(
            PortfolioHoldingThesisCandidate(
                portfolio_id=int(item["portfolio_id"]),
                portfolio_name=str(item["portfolio_name"]),
                snapshot_date=date.fromisoformat(str(item["snapshot_date"])),
                instrument_id=int(item["instrument_id"]),
                primary_symbol=str(item["primary_symbol"]).upper(),
                weight=Decimal(str(item["weight"])) if item.get("weight") is not None else None,
                market_value=Decimal(str(item["market_value"])),
                existing_thesis_id=int(item["existing_thesis_id"]) if item.get("existing_thesis_id") else None,
                node_id=int(item["node_id"]) if item.get("node_id") else None,
                node_code=str(item["node_code"]) if item.get("node_code") else None,
                node_name=str(item["node_name"]) if item.get("node_name") else None,
                cycle_state=str(item["cycle_state"]) if item.get("cycle_state") else None,
                cycle_score=Decimal(str(item["cycle_score"])) if item.get("cycle_score") is not None else None,
                recommendation_action=str(item["recommendation_action"])
                if item.get("recommendation_action")
                else None,
                recommendation_score=Decimal(str(item["recommendation_score"]))
                if item.get("recommendation_score") is not None
                else None,
            )
        )
    return tuple(candidates)


def render_portfolio_holding_thesis_candidate_lookup_sql(
    *,
    portfolio_name: str,
    as_of_date: date,
    strategy_name: str,
    horizon_type: str,
    market_code: str,
) -> str:
    return f"""-- portfolio holding thesis candidate lookup
with selected_portfolio as (
    select portfolio_id, portfolio_name
    from portfolio.portfolio
    where portfolio_name = {sql_literal(portfolio_name)}
    limit 1
),
latest_snapshot as (
    select max(position.snapshot_date) as snapshot_date
    from portfolio.position_snapshot position
    join selected_portfolio portfolio on portfolio.portfolio_id = position.portfolio_id
    where position.snapshot_date <= {sql_date(as_of_date)}
      and position.quantity <> 0
),
position_rows as (
    select
        portfolio.portfolio_id,
        portfolio.portfolio_name,
        position.snapshot_date,
        position.instrument_id,
        instrument.primary_symbol,
        position.weight,
        position.market_value,
        active_thesis.thesis_id as existing_thesis_id,
        theme.node_id,
        theme.node_code,
        theme.node_name,
        theme.cycle_state,
        theme.cycle_score,
        recommendation.action as recommendation_action,
        recommendation.total_score as recommendation_score
    from selected_portfolio portfolio
    join latest_snapshot snapshot on snapshot.snapshot_date is not null
    join portfolio.position_snapshot position
      on position.portfolio_id = portfolio.portfolio_id
     and position.snapshot_date = snapshot.snapshot_date
    join ref.instrument instrument on instrument.instrument_id = position.instrument_id
    left join lateral (
        select thesis.thesis_id
        from signal.investment_thesis thesis
        where thesis.instrument_id = position.instrument_id
          and thesis.status = 'active'
          and thesis.thesis_type = {sql_literal(strategy_name)}
        order by thesis.thesis_id desc
        limit 1
    ) active_thesis on true
    left join lateral (
        select
            node.node_id,
            node.code as node_code,
            node.name as node_name,
            cycle.cycle_state,
            cycle.cycle_score
        from ref.instrument_classification_membership membership
        join ref.classification_node node on node.node_id = membership.node_id
        left join signal.cycle_state_snapshot cycle
          on cycle.node_id = node.node_id
         and cycle.as_of_date = snapshot.snapshot_date
        where membership.instrument_id = position.instrument_id
          and node.taxonomy_family = 'internal_theme'
          and membership.valid_from <= snapshot.snapshot_date
          and (membership.valid_to is null or membership.valid_to >= snapshot.snapshot_date)
        order by cycle.cycle_score desc nulls last, node.code asc
        limit 1
    ) theme on true
    left join lateral (
        select recommendation.action, recommendation.total_score
        from signal.recommendation recommendation
        join signal.recommendation_batch batch on batch.batch_id = recommendation.batch_id
        where recommendation.instrument_id = position.instrument_id
          and recommendation.status = 'active'
          and batch.as_of_date <= snapshot.snapshot_date
          and batch.market_code = {sql_literal(market_code)}
          and batch.strategy_name = {sql_literal(strategy_name)}
          and batch.horizon_type = {sql_literal(horizon_type)}
        order by batch.as_of_date desc, recommendation.recommendation_id desc
        limit 1
    ) recommendation on true
    where position.quantity <> 0
      and position.linked_thesis_id is null
)
select coalesce(
    json_agg(
        json_build_object(
            'portfolio_id', portfolio_id,
            'portfolio_name', portfolio_name,
            'snapshot_date', snapshot_date,
            'instrument_id', instrument_id,
            'primary_symbol', primary_symbol,
            'weight', weight,
            'market_value', market_value,
            'existing_thesis_id', existing_thesis_id,
            'node_id', node_id,
            'node_code', node_code,
            'node_name', node_name,
            'cycle_state', cycle_state,
            'cycle_score', cycle_score,
            'recommendation_action', recommendation_action,
            'recommendation_score', recommendation_score
        )
        order by weight desc nulls last, primary_symbol
    ),
    '[]'::json
)::text
from position_rows;"""


def build_portfolio_holding_thesis_rows(
    candidates: tuple[PortfolioHoldingThesisCandidate, ...],
    *,
    strategy_name: str,
    horizon_type: str,
    market_code: str = _DEFAULT_MARKET_CODE,
) -> tuple[PortfolioHoldingThesisRow, ...]:
    expected_holding_days = _expected_holding_days(horizon_type)
    benchmark_code = _DEFAULT_BENCHMARK_BY_MARKET.get(market_code.upper())
    rows: list[PortfolioHoldingThesisRow] = []
    for candidate in candidates:
        theme_name = candidate.node_name or "portfolio holding"
        rows.append(
            PortfolioHoldingThesisRow(
                portfolio_id=candidate.portfolio_id,
                portfolio_name=candidate.portfolio_name,
                snapshot_date=candidate.snapshot_date,
                instrument_id=candidate.instrument_id,
                primary_symbol=candidate.primary_symbol,
                existing_thesis_id=candidate.existing_thesis_id,
                primary_node_id=candidate.node_id,
                thesis_type=strategy_name,
                title=f"{candidate.primary_symbol} 보유 검토 thesis via {theme_name}",
                summary=_build_summary(candidate, benchmark_code=benchmark_code),
                status="active",
                conviction_score=_conviction_score(candidate),
                expected_holding_days=expected_holding_days,
                benchmark_code=benchmark_code,
                entry_conditions=_build_entry_conditions(candidate),
                invalidation_conditions=_build_invalidation_conditions(candidate),
                exit_conditions=_build_exit_conditions(benchmark_code=benchmark_code),
            )
        )
    return tuple(rows)


def render_portfolio_holding_thesis_upsert_sql(
    thesis_rows: tuple[PortfolioHoldingThesisRow, ...],
    *,
    source_run_id: int,
) -> str:
    if not thesis_rows:
        raise ValueError("At least one portfolio holding thesis row is required.")
    value_rows = ",\n        ".join(
        _render_portfolio_holding_thesis_value_tuple(row, source_run_id=source_run_id) for row in thesis_rows
    )
    return f"""begin;

with source_rows (
    portfolio_id,
    portfolio_name,
    snapshot_date,
    instrument_id,
    existing_thesis_id,
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
    select distinct on (source_rows.portfolio_id, source_rows.snapshot_date, source_rows.instrument_id)
        source_rows.portfolio_id,
        source_rows.snapshot_date,
        source_rows.instrument_id,
        thesis.thesis_id
    from source_rows
    join signal.investment_thesis thesis
      on thesis.instrument_id = source_rows.instrument_id
     and thesis.thesis_type = source_rows.thesis_type
     and thesis.status = 'active'
     and (
        thesis.thesis_id = source_rows.existing_thesis_id
        or (
            source_rows.existing_thesis_id is null
            and thesis.primary_node_id is not distinct from source_rows.primary_node_id
        )
     )
    order by source_rows.portfolio_id, source_rows.snapshot_date, source_rows.instrument_id, thesis.thesis_id desc
),
to_insert as (
    select source_rows.*
    from source_rows
    where not exists (
        select 1
        from matched_existing
        where matched_existing.portfolio_id = source_rows.portfolio_id
          and matched_existing.snapshot_date = source_rows.snapshot_date
          and matched_existing.instrument_id = source_rows.instrument_id
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
        to_insert.portfolio_id,
        to_insert.snapshot_date,
        to_insert.instrument_id,
        inserted_thesis.thesis_id
    from to_insert
    join inserted_thesis
      on inserted_thesis.instrument_id = to_insert.instrument_id
     and inserted_thesis.primary_node_id is not distinct from to_insert.primary_node_id
     and inserted_thesis.thesis_type = to_insert.thesis_type
),
all_links as (
    select portfolio_id, snapshot_date, instrument_id, thesis_id from matched_existing
    union all
    select portfolio_id, snapshot_date, instrument_id, thesis_id from inserted_links
),
linked_positions as (
    update portfolio.position_snapshot position
    set
        linked_thesis_id = all_links.thesis_id,
        source_run_id = {source_run_id}::bigint
    from all_links
    where position.portfolio_id = all_links.portfolio_id
      and position.snapshot_date = all_links.snapshot_date
      and position.instrument_id = all_links.instrument_id
      and position.linked_thesis_id is null
    returning position.instrument_id
)
select json_build_object(
    'portfolio_id', (select min(portfolio_id) from source_rows),
    'portfolio_name', (select min(portfolio_name) from source_rows),
    'snapshot_date', (select max(snapshot_date)::text from source_rows),
    'source_position_count', (select count(*) from source_rows),
    'inserted_thesis_count', (select count(*) from inserted_thesis),
    'matched_existing_thesis_count', (select count(*) from matched_existing),
    'linked_position_count', (select count(*) from linked_positions)
)::text;

commit;
"""


def run_portfolio_holding_thesis_bootstrap(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    as_of_date: date,
    strategy_name: str,
    horizon_type: str,
    market_code: str = _DEFAULT_MARKET_CODE,
    thesis_version: str = _DEFAULT_THESIS_VERSION,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    candidates = load_portfolio_holding_thesis_candidates(
        config=config,
        portfolio_name=portfolio_name,
        as_of_date=as_of_date,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        market_code=market_code,
        executor=sql_executor,
    )
    thesis_rows = build_portfolio_holding_thesis_rows(
        candidates,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        market_code=market_code,
    )
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="portfolio_holding_thesis_bootstrap",
        config_json={
            "portfolio_name": portfolio_name,
            "as_of_date": as_of_date.isoformat(),
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "thesis_version": thesis_version,
            "candidate_count": len(candidates),
            "thesis_count": len(thesis_rows),
        },
    )
    if not thesis_rows:
        _mark_pipeline_run_succeeded(sql_executor, run_id)
        return {
            "run_id": run_id,
            "portfolio_name": portfolio_name,
            "as_of_date": as_of_date.isoformat(),
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "thesis_version": thesis_version,
            "candidate_count": 0,
            "thesis_count": 0,
            "inserted_thesis_count": 0,
            "matched_existing_thesis_count": 0,
            "linked_position_count": 0,
        }

    try:
        result = json.loads(
            sql_executor.execute_scalar(
                render_portfolio_holding_thesis_upsert_sql(thesis_rows, source_run_id=run_id)
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return {
        "run_id": run_id,
        "portfolio_name": portfolio_name,
        "as_of_date": as_of_date.isoformat(),
        "market_code": market_code,
        "strategy_name": strategy_name,
        "horizon_type": horizon_type,
        "thesis_version": thesis_version,
        "candidate_count": len(candidates),
        "thesis_count": len(thesis_rows),
        "snapshot_date": str(result.get("snapshot_date") or ""),
        "inserted_thesis_count": int(result.get("inserted_thesis_count") or 0),
        "matched_existing_thesis_count": int(result.get("matched_existing_thesis_count") or 0),
        "linked_position_count": int(result.get("linked_position_count") or 0),
    }


def _render_portfolio_holding_thesis_value_tuple(
    row: PortfolioHoldingThesisRow,
    *,
    source_run_id: int,
) -> str:
    return "(" + ", ".join(
        (
            f"{row.portfolio_id}::bigint",
            sql_literal(row.portfolio_name),
            sql_date(row.snapshot_date),
            f"{row.instrument_id}::bigint",
            _sql_bigint_or_null(row.existing_thesis_id),
            _sql_bigint_or_null(row.primary_node_id),
            sql_literal(row.thesis_type),
            sql_literal(row.title),
            sql_literal(row.summary),
            sql_literal(row.status),
            sql_numeric(row.conviction_score),
            f"{row.expected_holding_days}::integer",
            _sql_text_or_null(row.benchmark_code),
            sql_literal(row.entry_conditions),
            sql_literal(row.invalidation_conditions),
            sql_literal(row.exit_conditions),
            f"{source_run_id}::bigint",
        )
    ) + ")"


def _conviction_score(candidate: PortfolioHoldingThesisCandidate) -> Decimal:
    if candidate.recommendation_score is not None:
        return _clamp(candidate.recommendation_score, Decimal("0.1000"), Decimal("0.9000"))
    if candidate.cycle_score is not None:
        return _clamp(candidate.cycle_score, Decimal("0.1000"), Decimal("0.6500"))
    if candidate.weight is not None:
        return _clamp(candidate.weight, Decimal("0.1000"), Decimal("0.5000"))
    return Decimal("0.2500")


def _build_summary(candidate: PortfolioHoldingThesisCandidate, *, benchmark_code: str | None) -> str:
    theme = candidate.node_name or "테마 미분류"
    weight = _format_percent(candidate.weight)
    action = candidate.recommendation_action or "추천 없음"
    benchmark = benchmark_code or "벤치마크 미설정"
    return (
        f"{candidate.primary_symbol}은 현재 포트폴리오에 {weight} 비중으로 보유 중이다. "
        f"이 thesis는 자동 매수 신호가 아니라 보유 커버리지 공백을 막기 위한 장기 검토 기록이다. "
        f"주요 맥락은 {theme}, 최신 추천 조치는 {action}, 비교 기준은 {benchmark}이다."
    )


def _build_entry_conditions(candidate: PortfolioHoldingThesisCandidate) -> str:
    theme = candidate.node_name or "포트폴리오 보유"
    return (
        f"{candidate.primary_symbol} 보유를 계속 검토하려면 {theme} 관련 근거, 가격 데이터, "
        "최근 뉴스/공시 이벤트가 유지되어야 한다."
    )


def _build_invalidation_conditions(candidate: PortfolioHoldingThesisCandidate) -> str:
    theme = candidate.node_name or "보유 근거"
    return (
        f"{candidate.primary_symbol}의 {theme} 근거가 사라지거나, 보유 검토에서 축소/청산 신호가 나오거나, "
        "성과 측정에서 벤치마크 대비 부정적 결과가 누적되면 thesis를 재검토한다."
    )


def _build_exit_conditions(*, benchmark_code: str | None) -> str:
    benchmark = benchmark_code or "벤치마크"
    return f"{benchmark} 대비 성과, thesis 무효화 조건, 포트폴리오 리스크 검토를 함께 확인한 뒤 거래 안전 조건이 통과할 때만 축소/청산한다."


def _expected_holding_days(horizon_type: str) -> int:
    return 365 if horizon_type == "long_term" else 180


def _format_percent(value: Decimal | None) -> str:
    if value is None:
        return "비중 미측정"
    return f"{(value * Decimal('100')).quantize(Decimal('0.1'))}%"


def _clamp(value: Decimal, lower: Decimal, upper: Decimal) -> Decimal:
    return max(lower, min(upper, value)).quantize(Decimal("0.0001"))


def _sql_bigint_or_null(value: int | None) -> str:
    return "null::bigint" if value is None else f"{value}::bigint"


def _sql_text_or_null(value: str | None) -> str:
    return "null::text" if value is None else sql_literal(value)
