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
_DEFAULT_MEMBERSHIP_TYPE = "derived_theme"


@dataclass(frozen=True)
class SelectedUniverseInstrument:
    universe_batch_id: int
    instrument_id: int
    primary_symbol: str


@dataclass(frozen=True)
class InstrumentThemeMembershipCandidate:
    instrument_id: int
    primary_symbol: str
    node_id: int
    node_code: str
    node_name: str
    membership_type: str
    confidence: Decimal | None
    supporting_event_count: int
    first_event_date: date
    latest_event_date: date
    source_document_id: int | None


def load_selected_universe_instruments(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    market_code: str = _DEFAULT_MARKET_CODE,
    executor: PsqlCommandExecutor | None = None,
) -> tuple[SelectedUniverseInstrument, ...]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload_text = sql_executor.execute_scalar(
        render_selected_universe_instruments_lookup_sql(
            as_of_date=as_of_date,
            market_code=market_code,
            strategy_name=strategy_name,
            horizon_type=horizon_type,
            universe_version=universe_version,
        )
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Selected universe lookup did not return a JSON array.")

    rows = tuple(
        SelectedUniverseInstrument(
            universe_batch_id=int(item["universe_batch_id"]),
            instrument_id=int(item["instrument_id"]),
            primary_symbol=str(item["primary_symbol"]).upper(),
        )
        for item in payload
    )
    if not rows:
        raise ValueError("No strategy universe instruments matched the requested snapshot identity.")
    return rows


def load_instrument_theme_membership_candidates(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    market_code: str = _DEFAULT_MARKET_CODE,
    executor: PsqlCommandExecutor | None = None,
) -> tuple[InstrumentThemeMembershipCandidate, ...]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload_text = sql_executor.execute_scalar(
        render_instrument_theme_membership_candidate_lookup_sql(
            as_of_date=as_of_date,
            market_code=market_code,
            strategy_name=strategy_name,
            horizon_type=horizon_type,
            universe_version=universe_version,
        )
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Instrument theme membership lookup did not return a JSON array.")

    return tuple(
        InstrumentThemeMembershipCandidate(
            instrument_id=int(item["instrument_id"]),
            primary_symbol=str(item["primary_symbol"]).upper(),
            node_id=int(item["node_id"]),
            node_code=str(item["node_code"]),
            node_name=str(item["node_name"]),
            membership_type=str(item["membership_type"]),
            confidence=Decimal(str(item["confidence"])) if item.get("confidence") is not None else None,
            supporting_event_count=int(item["supporting_event_count"]),
            first_event_date=date.fromisoformat(str(item["first_event_date"])),
            latest_event_date=date.fromisoformat(str(item["latest_event_date"])),
            source_document_id=int(item["source_document_id"]) if item.get("source_document_id") is not None else None,
        )
        for item in payload
    )


def render_selected_universe_instruments_lookup_sql(
    *,
    as_of_date: date,
    market_code: str,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
) -> str:
    return f"""-- instrument theme selected instruments lookup
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
)
select coalesce(
    json_agg(
        json_build_object(
            'universe_batch_id', m.universe_batch_id,
            'instrument_id', m.instrument_id,
            'primary_symbol', i.primary_symbol
        )
        order by m.rank_position
    ),
    '[]'::json
)::text
from selected_batch sb
join signal.strategy_universe_member m on m.universe_batch_id = sb.universe_batch_id
join ref.instrument i on i.instrument_id = m.instrument_id;"""


def render_instrument_theme_membership_candidate_lookup_sql(
    *,
    as_of_date: date,
    market_code: str,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
) -> str:
    return f"""-- instrument theme membership candidate lookup
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
        m.instrument_id,
        i.primary_symbol
    from selected_batch sb
    join signal.strategy_universe_member m on m.universe_batch_id = sb.universe_batch_id
    join ref.instrument i on i.instrument_id = m.instrument_id
),
candidate_rows as (
    select
        si.instrument_id,
        si.primary_symbol,
        n.node_id,
        n.code as node_code,
        n.name as node_name,
        {sql_literal(_DEFAULT_MEMBERSHIP_TYPE)} as membership_type,
        count(distinct e.event_id)::integer as supporting_event_count,
        min((e.event_at at time zone 'UTC')::date) as first_event_date,
        max((e.event_at at time zone 'UTC')::date) as latest_event_date,
        max(least(
            coalesce(ei.confidence, 1.0),
            coalesce(ec.confidence, 1.0),
            coalesce(e.confidence, 1.0)
        ))::numeric(5,4) as confidence,
        max(l.document_id) as source_document_id
    from selected_instruments si
    join event.event_instrument_impact ei on ei.instrument_id = si.instrument_id
    join event.event_classification_impact ec on ec.event_id = ei.event_id
    join event.event e on e.event_id = ei.event_id
    join ref.classification_node n on n.node_id = ec.node_id
    left join event.event_document_link l
      on l.event_id = e.event_id
     and l.link_type = 'source'
    where n.taxonomy_family = 'internal_theme'
      and e.event_at < ({sql_date(as_of_date)} + interval '1 day')
    group by
        si.instrument_id,
        si.primary_symbol,
        n.node_id,
        n.code,
        n.name
)
select coalesce(
    json_agg(
        json_build_object(
            'instrument_id', instrument_id,
            'primary_symbol', primary_symbol,
            'node_id', node_id,
            'node_code', node_code,
            'node_name', node_name,
            'membership_type', membership_type,
            'confidence', confidence,
            'supporting_event_count', supporting_event_count,
            'first_event_date', first_event_date,
            'latest_event_date', latest_event_date,
            'source_document_id', source_document_id
        )
        order by primary_symbol, node_code
    ),
    '[]'::json
)::text
from candidate_rows;"""


def render_instrument_theme_membership_replace_sql(
    selected_instruments: tuple[SelectedUniverseInstrument, ...],
    candidates: tuple[InstrumentThemeMembershipCandidate, ...],
) -> str:
    if not selected_instruments:
        raise ValueError("At least one selected universe instrument is required.")
    selected_instrument_ids = ", ".join(f"{row.instrument_id}::bigint" for row in selected_instruments)
    lines = [
        "begin;",
        "",
        f"""delete from ref.instrument_classification_membership m
using ref.classification_node n
where m.node_id = n.node_id
  and m.instrument_id in ({selected_instrument_ids})
  and m.membership_type = {sql_literal(_DEFAULT_MEMBERSHIP_TYPE)}
  and n.taxonomy_family = 'internal_theme';""",
    ]

    if candidates:
        value_rows = ",\n        ".join(_render_membership_value_tuple(candidate) for candidate in candidates)
        lines.extend(
            [
                "",
                f"""insert into ref.instrument_classification_membership (
    instrument_id,
    node_id,
    membership_type,
    confidence,
    source_document_id,
    valid_from,
    valid_to
)
values
        {value_rows};""",
            ]
        )

    lines.extend(["", "commit;"])
    return "\n".join(lines) + "\n"


def run_instrument_theme_enrichment(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    market_code: str = _DEFAULT_MARKET_CODE,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    selected_instruments = load_selected_universe_instruments(
        config=config,
        as_of_date=as_of_date,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        universe_version=universe_version,
        market_code=market_code,
        executor=sql_executor,
    )
    candidates = load_instrument_theme_membership_candidates(
        config=config,
        as_of_date=as_of_date,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        universe_version=universe_version,
        market_code=market_code,
        executor=sql_executor,
    )
    universe_batch_id = selected_instruments[0].universe_batch_id
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="instrument_theme_enrichment",
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "universe_version": universe_version,
            "selected_instrument_count": len(selected_instruments),
            "candidate_membership_count": len(candidates),
        },
    )
    try:
        sql_executor.execute_non_query(
            render_instrument_theme_membership_replace_sql(
                selected_instruments,
                candidates,
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
        "selected_instrument_count": len(selected_instruments),
        "membership_count": len(candidates),
        "selected_symbol_preview": [row.primary_symbol for row in selected_instruments[:10]],
        "node_code_preview": sorted({candidate.node_code for candidate in candidates})[:10],
    }


def _render_membership_value_tuple(candidate: InstrumentThemeMembershipCandidate) -> str:
    return "(" + ", ".join(
        (
            f"{candidate.instrument_id}::bigint",
            f"{candidate.node_id}::bigint",
            sql_literal(candidate.membership_type),
            sql_numeric(candidate.confidence) if candidate.confidence is not None else "null::numeric",
            f"{candidate.source_document_id}::bigint" if candidate.source_document_id is not None else "null::bigint",
            sql_date(candidate.first_event_date),
            "null::date",
        )
    ) + ")"
