from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal, sql_numeric
from stockanalysis.ingest.psql import PsqlCommandExecutor

_DEFAULT_MARKET_CODE = "US"
_DEFAULT_REQUESTED_EXCHANGES = ("Nasdaq", "NYSE")
_EXCHANGE_TO_MIC = {
    "nasdaq": ("Nasdaq", "XNAS"),
    "nyse": ("NYSE", "XNYS"),
}


@dataclass(frozen=True)
class StrategyUniverseCandidate:
    instrument_id: int
    primary_symbol: str
    exchange_name: str
    latest_trade_date: date
    latest_adjusted_close: Decimal
    observation_count: int
    selection_score: Decimal
    rank_position: int


def load_strategy_universe_candidates(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    market_code: str = _DEFAULT_MARKET_CODE,
    exchanges: list[str] | None = None,
    min_observation_count: int = 1,
    min_adjusted_close: Decimal = Decimal("0"),
    limit: int | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> tuple[StrategyUniverseCandidate, ...]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload_text = sql_executor.execute_scalar(
        render_strategy_universe_candidate_lookup_sql(
            as_of_date=as_of_date,
            market_code=market_code,
            mic_codes=_resolve_requested_mic_codes(exchanges),
            min_observation_count=min_observation_count,
            min_adjusted_close=min_adjusted_close,
            limit=limit,
        )
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Strategy universe candidate lookup did not return a JSON array.")

    candidates: list[StrategyUniverseCandidate] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Strategy universe candidate lookup returned a non-object row.")
        candidates.append(
            StrategyUniverseCandidate(
                instrument_id=int(item["instrument_id"]),
                primary_symbol=str(item["primary_symbol"]).upper(),
                exchange_name=str(item["exchange_name"]),
                latest_trade_date=date.fromisoformat(str(item["latest_trade_date"])),
                latest_adjusted_close=Decimal(str(item["latest_adjusted_close"])),
                observation_count=int(item["observation_count"]),
                selection_score=Decimal(str(item["selection_score"])),
                rank_position=int(item["rank_position"]),
            )
        )

    if not candidates:
        raise ValueError("No strategy universe candidates matched the requested filters.")
    return tuple(candidates)


def render_strategy_universe_candidate_lookup_sql(
    *,
    as_of_date: date,
    market_code: str,
    mic_codes: tuple[str, ...],
    min_observation_count: int,
    min_adjusted_close: Decimal,
    limit: int | None,
) -> str:
    if min_observation_count <= 0:
        raise ValueError("min_observation_count must be greater than 0")
    if min_adjusted_close < 0:
        raise ValueError("min_adjusted_close must be greater than or equal to 0")
    if limit is not None and limit <= 0:
        raise ValueError("limit must be greater than 0")

    mic_filter = ""
    if mic_codes:
        quoted_mic_codes = ", ".join(sql_literal(mic_code) for mic_code in mic_codes)
        mic_filter = f"\n      and e.mic_code in ({quoted_mic_codes})"
    limit_clause = "" if limit is None else f"\nlimit {limit}"
    return f"""with latest_bar as (
    select distinct on (b.instrument_id)
        b.instrument_id,
        b.trade_date,
        b.adjusted_close
    from market.daily_price_bar b
    where b.trade_date <= {sql_date(as_of_date)}
    order by b.instrument_id, b.trade_date desc
),
price_counts as (
    select
        b.instrument_id,
        count(*)::integer as observation_count
    from market.daily_price_bar b
    where b.trade_date <= {sql_date(as_of_date)}
    group by b.instrument_id
),
candidate_rows as (
    select
        i.instrument_id,
        i.primary_symbol,
        e.name as exchange_name,
        lb.trade_date as latest_trade_date,
        lb.adjusted_close as latest_adjusted_close,
        pc.observation_count,
        (pc.observation_count::numeric + (lb.adjusted_close / 1000.0))::numeric(10,4) as selection_score
    from ref.instrument i
    join ref.exchange e on e.exchange_id = i.exchange_id
    join latest_bar lb on lb.instrument_id = i.instrument_id
    join price_counts pc on pc.instrument_id = i.instrument_id
    where i.market_code = {sql_literal(market_code)}
      and i.is_active = true
      and i.delisted_at is null{mic_filter}
      and pc.observation_count >= {min_observation_count}
      and lb.adjusted_close >= {sql_numeric(min_adjusted_close)}
),
ranked_rows as (
    select
        row_number() over (order by selection_score desc, primary_symbol asc)::integer as rank_position,
        *
    from candidate_rows
    order by selection_score desc, primary_symbol asc{limit_clause}
)
select coalesce(
    json_agg(
        json_build_object(
            'instrument_id', r.instrument_id,
            'primary_symbol', r.primary_symbol,
            'exchange_name', r.exchange_name,
            'latest_trade_date', r.latest_trade_date,
            'latest_adjusted_close', r.latest_adjusted_close,
            'observation_count', r.observation_count,
            'selection_score', r.selection_score,
            'rank_position', r.rank_position
        )
        order by r.rank_position
    ),
    '[]'::json
)::text
from ranked_rows r;"""


def render_strategy_universe_upsert_sql(
    candidates: tuple[StrategyUniverseCandidate, ...],
    *,
    as_of_date: date,
    market_code: str,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    selection_rule: str,
    source_run_id: int,
) -> str:
    if not candidates:
        raise ValueError("At least one strategy universe candidate is required.")
    value_rows = ",\n        ".join(_render_candidate_value_tuple(candidate) for candidate in candidates)
    return f"""with upsert_batch as (
    insert into signal.strategy_universe_batch (
        as_of_date,
        market_code,
        strategy_name,
        horizon_type,
        universe_version,
        selection_rule,
        source_run_id
    )
    values (
        {sql_date(as_of_date)},
        {sql_literal(market_code)},
        {sql_literal(strategy_name)},
        {sql_literal(horizon_type)},
        {sql_literal(universe_version)},
        {sql_literal(selection_rule)},
        {source_run_id}::bigint
    )
    on conflict (as_of_date, market_code, strategy_name, horizon_type, universe_version) do update
    set
        selection_rule = excluded.selection_rule,
        source_run_id = excluded.source_run_id
    returning universe_batch_id
),
delete_existing as (
    delete from signal.strategy_universe_member
    where universe_batch_id = (select universe_batch_id from upsert_batch)
),
source_rows (
    instrument_id,
    rank_position,
    selection_score,
    latest_trade_date,
    latest_adjusted_close,
    observation_count,
    inclusion_reason
) as (
    values
        {value_rows}
),
insert_members as (
    insert into signal.strategy_universe_member (
        universe_batch_id,
        instrument_id,
        rank_position,
        selection_score,
        latest_trade_date,
        latest_adjusted_close,
        observation_count,
        inclusion_reason
    )
    select
        ub.universe_batch_id,
        sr.instrument_id,
        sr.rank_position,
        sr.selection_score,
        sr.latest_trade_date,
        sr.latest_adjusted_close,
        sr.observation_count,
        sr.inclusion_reason
    from upsert_batch ub
    cross join (select count(*) from delete_existing) deleted
    join source_rows sr on true
    on conflict (universe_batch_id, instrument_id) do update
    set
        rank_position = excluded.rank_position,
        selection_score = excluded.selection_score,
        latest_trade_date = excluded.latest_trade_date,
        latest_adjusted_close = excluded.latest_adjusted_close,
        observation_count = excluded.observation_count,
        inclusion_reason = excluded.inclusion_reason
)
select universe_batch_id from upsert_batch;"""


def run_strategy_universe_slice(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    market_code: str = _DEFAULT_MARKET_CODE,
    exchanges: list[str] | None = None,
    min_observation_count: int = 1,
    min_adjusted_close: Decimal = Decimal("0"),
    limit: int | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    candidates = load_strategy_universe_candidates(
        config=config,
        as_of_date=as_of_date,
        market_code=market_code,
        exchanges=exchanges,
        min_observation_count=min_observation_count,
        min_adjusted_close=min_adjusted_close,
        limit=limit,
        executor=sql_executor,
    )
    selection_rule = _selection_rule(
        market_code=market_code,
        exchanges=exchanges,
        min_observation_count=min_observation_count,
        min_adjusted_close=min_adjusted_close,
        limit=limit,
    )
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="strategy_universe_slice",
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "universe_version": universe_version,
            "selection_rule": selection_rule,
        },
    )
    try:
        universe_batch_id = int(
            sql_executor.execute_scalar(
                render_strategy_universe_upsert_sql(
                    candidates,
                    as_of_date=as_of_date,
                    market_code=market_code,
                    strategy_name=strategy_name,
                    horizon_type=horizon_type,
                    universe_version=universe_version,
                    selection_rule=selection_rule,
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
        "universe_batch_id": universe_batch_id,
        "as_of_date": as_of_date.isoformat(),
        "market_code": market_code,
        "strategy_name": strategy_name,
        "horizon_type": horizon_type,
        "universe_version": universe_version,
        "member_count": len(candidates),
        "selected_symbol_preview": [candidate.primary_symbol for candidate in candidates[:10]],
    }


def _selection_rule(
    *,
    market_code: str,
    exchanges: list[str] | None,
    min_observation_count: int,
    min_adjusted_close: Decimal,
    limit: int | None,
) -> str:
    return json.dumps(
        {
            "market_code": market_code,
            "exchanges": list(_resolve_requested_exchange_names(exchanges)),
            "min_observation_count": min_observation_count,
            "min_adjusted_close": str(min_adjusted_close),
            "limit": limit,
            "ranking": "observation_count + latest_adjusted_close / 1000, then symbol",
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _render_candidate_value_tuple(candidate: StrategyUniverseCandidate) -> str:
    reason = (
        f"Active instrument with {candidate.observation_count} price observations "
        f"through {candidate.latest_trade_date.isoformat()}."
    )
    return "(" + ", ".join(
        (
            f"{candidate.instrument_id}::bigint",
            str(candidate.rank_position),
            sql_numeric(candidate.selection_score),
            sql_date(candidate.latest_trade_date),
            sql_numeric(candidate.latest_adjusted_close),
            str(candidate.observation_count),
            sql_literal(reason),
        )
    ) + ")"


def _resolve_requested_exchange_names(exchanges: list[str] | None) -> tuple[str, ...]:
    requested = exchanges or list(_DEFAULT_REQUESTED_EXCHANGES)
    resolved: list[str] = []
    seen: set[str] = set()
    for exchange_name in requested:
        normalized = exchange_name.strip().lower()
        if not normalized:
            raise ValueError("Requested exchange names must not be empty.")
        supported = _EXCHANGE_TO_MIC.get(normalized)
        if supported is None:
            raise ValueError(f"Unsupported requested exchange `{exchange_name}`.")
        display_name, _ = supported
        if normalized in seen:
            continue
        seen.add(normalized)
        resolved.append(display_name)
    return tuple(resolved)


def _resolve_requested_mic_codes(exchanges: list[str] | None) -> tuple[str, ...]:
    return tuple(
        _EXCHANGE_TO_MIC[name.lower()][1]
        for name in _resolve_requested_exchange_names(exchanges)
    )


def _create_pipeline_run(
    executor: PsqlCommandExecutor,
    *,
    pipeline_name: str,
    config_json: dict[str, object],
) -> int:
    payload = json.dumps(config_json, ensure_ascii=False, sort_keys=True)
    sql = f"""insert into ops.pipeline_run (
    run_kind,
    pipeline_name,
    status,
    config_json
)
values (
    'signal',
    {sql_literal(pipeline_name)},
    'running',
    {sql_literal(payload)}::jsonb
)
returning run_id;"""
    return int(executor.execute_scalar(sql))


def _mark_pipeline_run_succeeded(executor: PsqlCommandExecutor, run_id: int) -> None:
    executor.execute_non_query(
        f"""update ops.pipeline_run
set
    status = 'succeeded',
    ended_at = now(),
    error_summary = null
where run_id = {run_id};"""
    )


def _mark_pipeline_run_failed(executor: PsqlCommandExecutor, run_id: int, error_summary: str) -> None:
    truncated = error_summary.strip()[:2000] or "strategy universe slice failed"
    try:
        executor.execute_non_query(
            f"""update ops.pipeline_run
set
    status = 'failed',
    ended_at = now(),
    error_summary = {sql_literal(truncated)}
where run_id = {run_id};"""
        )
    except Exception:
        return
