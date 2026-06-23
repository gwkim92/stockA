from __future__ import annotations

import json
from datetime import date
from typing import Any, Mapping, Sequence

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor


DEFAULT_PAPER_PORTFOLIO_NAME = "Long Term Paper"
DEFAULT_LIVE_TOSS_PORTFOLIO_NAME = "Toss Real Readonly"


def load_agent_market_context(
    *,
    config: RuntimeConfig,
    symbols: Sequence[str],
    as_of_date: date,
    include_live_account: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, Any]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(
        render_agent_market_context_sql(
            symbols=symbols,
            as_of_date=as_of_date,
            include_live_account=include_live_account,
        )
    )
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise ValueError("Agent market context query must return a JSON object.")
    return parsed


def render_agent_market_context_sql(
    *,
    symbols: Sequence[str],
    as_of_date: date,
    include_live_account: bool = False,
) -> str:
    normalized_symbols = tuple(_normalize_symbol(symbol) for symbol in symbols if str(symbol).strip())
    if not normalized_symbols:
        raise ValueError("Agent market context requires at least one symbol.")
    symbol_values = ",\n        ".join(f"({sql_literal(symbol)})" for symbol in normalized_symbols)
    live_account_filter = (
        f"portfolio.portfolio_name = {sql_literal(DEFAULT_LIVE_TOSS_PORTFOLIO_NAME)}"
        if include_live_account
        else "false"
    )
    return f"""-- agent market context read model
with requested_symbols(symbol) as (
    values
        {symbol_values}
),
target_instruments as (
    select instrument.instrument_id, instrument.primary_symbol as symbol, instrument.name, instrument.market_code, instrument.currency_code
    from ref.instrument instrument
    join requested_symbols requested on requested.symbol = upper(instrument.primary_symbol)
    where instrument.is_active = true
),
canonical_market as (
    select distinct on (instrument.instrument_id)
        instrument.symbol,
        price.trade_date,
        price.open,
        price.high,
        price.low,
        price.close,
        price.adjusted_close,
        price.volume,
        coalesce(nullif(price.provider, ''), 'unknown') as provider,
        price.source_run_id
    from target_instruments instrument
    join market.daily_price_bar price on price.instrument_id = instrument.instrument_id
    where price.trade_date <= {sql_date(as_of_date)}
    order by instrument.instrument_id, price.trade_date desc
),
toss_provider_evidence as (
    select distinct on (instrument.instrument_id)
        instrument.symbol,
        candle.trade_date,
        candle.close,
        candle.adjusted_close,
        candle.volume,
        candle.source_run_id,
        candle.observed_at
    from target_instruments instrument
    join market.tossinvest_daily_candle_snapshot candle on candle.instrument_id = instrument.instrument_id
    where candle.trade_date <= {sql_date(as_of_date)}
    order by instrument.instrument_id, candle.trade_date desc, candle.observed_at desc
),
toss_microdata as (
    select distinct on (instrument.instrument_id)
        instrument.symbol,
        micro.microdata_status,
        micro.currency_code,
        micro.best_bid_price,
        micro.best_ask_price,
        micro.latest_trade_price,
        micro.latest_trade_timestamp,
        micro.trade_count,
        micro.upper_limit_price,
        micro.lower_limit_price,
        micro.observed_at
    from target_instruments instrument
    join market.tossinvest_market_microdata_snapshot micro on micro.instrument_id = instrument.instrument_id
    order by instrument.instrument_id, micro.observed_at desc
),
paper_portfolio as (
    select distinct on (instrument.instrument_id)
        instrument.symbol,
        portfolio.portfolio_name,
        position.snapshot_date,
        position.quantity,
        position.weight,
        position.market_price,
        position.market_value
    from target_instruments instrument
    join portfolio.position_snapshot position on position.instrument_id = instrument.instrument_id
    join portfolio.portfolio portfolio on portfolio.portfolio_id = position.portfolio_id
    where portfolio.portfolio_name = {sql_literal(DEFAULT_PAPER_PORTFOLIO_NAME)}
      and position.snapshot_date <= {sql_date(as_of_date)}
    order by instrument.instrument_id, position.snapshot_date desc
),
live_account_readonly as (
    select distinct on (instrument.instrument_id)
        instrument.symbol,
        portfolio.portfolio_name,
        position.snapshot_date,
        position.quantity,
        position.market_price,
        position.market_value,
        position.native_currency_code,
        position.market_value_native,
        position.fx_rate_to_base
    from target_instruments instrument
    join portfolio.position_snapshot position on position.instrument_id = instrument.instrument_id
    join portfolio.portfolio portfolio on portfolio.portfolio_id = position.portfolio_id
    where {live_account_filter}
      and position.snapshot_date <= {sql_date(as_of_date)}
    order by instrument.instrument_id, position.snapshot_date desc
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'requested_symbols', (select json_agg(symbol order by symbol) from requested_symbols),
    'context_sections', json_build_object(
        'canonical_market', true,
        'toss_provider_evidence', true,
        'toss_microdata', true,
        'paper_portfolio', true,
        'live_account_readonly', {sql_literal(include_live_account)}
    ),
    'canonical_market', coalesce((select json_agg(row_to_json(canonical_market) order by symbol) from canonical_market), '[]'::json),
    'toss_provider_evidence', coalesce((select json_agg(row_to_json(toss_provider_evidence) order by symbol) from toss_provider_evidence), '[]'::json),
    'toss_microdata', coalesce((select json_agg(row_to_json(toss_microdata) order by symbol) from toss_microdata), '[]'::json),
    'paper_portfolio', coalesce((select json_agg(row_to_json(paper_portfolio) order by symbol) from paper_portfolio), '[]'::json),
    'live_account_readonly', coalesce((select json_agg(row_to_json(live_account_readonly) order by symbol) from live_account_readonly), '[]'::json),
    'agent_boundary', json_build_object(
        'source', 'postgres_read_model',
        'direct_tossinvest_http_allowed', false,
        'recommendation_scoring_uses_live_account_by_default', false,
        'broker_submit_allowed', false,
        'order_boundary', 'read_only_no_order'
    )
)::text;"""


def agent_market_context_contract() -> Mapping[str, object]:
    return {
        "sections": (
            "canonical_market",
            "toss_provider_evidence",
            "toss_microdata",
            "paper_portfolio",
            "live_account_readonly",
        ),
        "source": "postgres_read_model",
        "direct_tossinvest_http_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": "read_only_no_order",
    }


def _normalize_symbol(value: str) -> str:
    symbol = str(value).strip().upper()
    if not symbol:
        raise ValueError("Agent market context symbol must not be empty.")
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-")
    if any(char not in allowed for char in symbol):
        raise ValueError("Agent market context symbol may only contain letters, digits, '.', or '-'.")
    return symbol
