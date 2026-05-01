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
_DEFAULT_FEATURE_SET_VERSION = "bootstrap-v1"
_FEATURE_OWNER = "market_feature_snapshot"
_DECIMAL_QUANTIZER = Decimal("0.00000001")

_FEATURE_DEFINITIONS = (
    {
        "feature_code": "latest_adjusted_close",
        "feature_name": "Latest Adjusted Close",
        "description": "Latest adjusted close on or before the snapshot date.",
        "default_horizon": "spot",
    },
    {
        "feature_code": "return_1d",
        "feature_name": "One Day Return",
        "description": "Latest adjusted close divided by previous adjusted close minus one.",
        "default_horizon": "short_term",
    },
    {
        "feature_code": "return_since_first_observation",
        "feature_name": "Return Since First Observation",
        "description": "Latest adjusted close divided by first observed adjusted close minus one.",
        "default_horizon": "medium_term",
    },
    {
        "feature_code": "realized_volatility_bootstrap",
        "feature_name": "Bootstrap Realized Volatility",
        "description": "Population volatility of available daily returns with single-return fallback to absolute return.",
        "default_horizon": "medium_term",
    },
    {
        "feature_code": "observation_count",
        "feature_name": "Observation Count",
        "description": "Number of daily adjusted close observations used for the snapshot.",
        "default_horizon": "spot",
    },
)


@dataclass(frozen=True)
class InstrumentPriceHistory:
    universe_batch_id: int
    instrument_id: int
    primary_symbol: str
    rank_position: int
    price_history: tuple[Decimal, ...]
    trade_dates: tuple[date, ...]


@dataclass(frozen=True)
class InstrumentFeatureValue:
    instrument_id: int
    primary_symbol: str
    feature_code: str
    feature_value: Decimal | None
    zscore: Decimal | None
    evidence_json: dict[str, object]


def load_market_feature_inputs(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    market_code: str = _DEFAULT_MARKET_CODE,
    executor: PsqlCommandExecutor | None = None,
) -> tuple[InstrumentPriceHistory, ...]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload_text = sql_executor.execute_scalar(
        render_market_feature_input_lookup_sql(
            as_of_date=as_of_date,
            market_code=market_code,
            strategy_name=strategy_name,
            horizon_type=horizon_type,
            universe_version=universe_version,
        )
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Market feature input lookup did not return a JSON array.")

    rows: list[InstrumentPriceHistory] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Market feature input lookup returned a non-object row.")
        price_rows = item.get("price_history")
        if not isinstance(price_rows, list) or not price_rows:
            raise ValueError("Market feature input lookup returned an empty price history.")
        prices: list[Decimal] = []
        trade_dates: list[date] = []
        for price_row in price_rows:
            if not isinstance(price_row, dict):
                raise ValueError("Market feature input lookup returned a non-object price row.")
            prices.append(Decimal(str(price_row["adjusted_close"])))
            trade_dates.append(date.fromisoformat(str(price_row["trade_date"])))
        rows.append(
            InstrumentPriceHistory(
                universe_batch_id=int(item["universe_batch_id"]),
                instrument_id=int(item["instrument_id"]),
                primary_symbol=str(item["primary_symbol"]).upper(),
                rank_position=int(item["rank_position"]),
                price_history=tuple(prices),
                trade_dates=tuple(trade_dates),
            )
        )

    if not rows:
        raise ValueError("No strategy universe members matched the requested snapshot identity.")
    return tuple(rows)


def render_market_feature_input_lookup_sql(
    *,
    as_of_date: date,
    market_code: str,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
) -> str:
    return f"""with selected_batch as (
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
price_rows as (
    select
        m.universe_batch_id,
        m.instrument_id,
        i.primary_symbol,
        m.rank_position,
        b.trade_date,
        b.adjusted_close
    from signal.strategy_universe_member m
    join selected_batch sb on sb.universe_batch_id = m.universe_batch_id
    join ref.instrument i on i.instrument_id = m.instrument_id
    join market.daily_price_bar b on b.instrument_id = m.instrument_id
    where b.trade_date <= {sql_date(as_of_date)}
)
select coalesce(
    json_agg(
        json_build_object(
            'universe_batch_id', universe_batch_id,
            'instrument_id', instrument_id,
            'primary_symbol', primary_symbol,
            'rank_position', rank_position,
            'price_history', price_history
        )
        order by rank_position
    ),
    '[]'::json
)::text
from (
    select
        universe_batch_id,
        instrument_id,
        primary_symbol,
        rank_position,
        json_agg(
            json_build_object(
                'trade_date', trade_date,
                'adjusted_close', adjusted_close
            )
            order by trade_date
        ) as price_history
    from price_rows
    group by universe_batch_id, instrument_id, primary_symbol, rank_position
) grouped_rows;"""


def compute_market_feature_values(
    rows: tuple[InstrumentPriceHistory, ...],
    *,
    as_of_date: date,
    feature_set_version: str,
) -> tuple[InstrumentFeatureValue, ...]:
    if not rows:
        raise ValueError("At least one instrument price history is required.")

    raw_values_by_feature: dict[str, dict[int, Decimal | None]] = {definition["feature_code"]: {} for definition in _FEATURE_DEFINITIONS}
    evidence_by_feature: dict[tuple[int, str], dict[str, object]] = {}
    symbol_by_instrument: dict[int, str] = {}

    for row in rows:
        symbol_by_instrument[row.instrument_id] = row.primary_symbol
        latest_adjusted_close = _quantize(row.price_history[-1])
        observation_count = Decimal(len(row.price_history))
        return_1d = _quantize((row.price_history[-1] / row.price_history[-2]) - Decimal("1")) if len(row.price_history) >= 2 else None
        return_since_first = _quantize((row.price_history[-1] / row.price_history[0]) - Decimal("1")) if len(row.price_history) >= 2 else None
        realized_volatility = _calculate_realized_volatility(row.price_history)

        feature_map = {
            "latest_adjusted_close": latest_adjusted_close,
            "return_1d": return_1d,
            "return_since_first_observation": return_since_first,
            "realized_volatility_bootstrap": realized_volatility,
            "observation_count": _quantize(observation_count),
        }
        for feature_code, feature_value in feature_map.items():
            raw_values_by_feature[feature_code][row.instrument_id] = feature_value
            evidence_by_feature[(row.instrument_id, feature_code)] = {
                "feature_set_version": feature_set_version,
                "universe_batch_id": row.universe_batch_id,
                "rank_position": row.rank_position,
                "observation_count": len(row.price_history),
                "first_trade_date": row.trade_dates[0].isoformat(),
                "latest_trade_date": row.trade_dates[-1].isoformat(),
                "as_of_date": as_of_date.isoformat(),
            }

    zscore_by_feature = {
        feature_code: _calculate_feature_zscores(feature_values)
        for feature_code, feature_values in raw_values_by_feature.items()
    }

    output_rows: list[InstrumentFeatureValue] = []
    for row in rows:
        for definition in _FEATURE_DEFINITIONS:
            feature_code = str(definition["feature_code"])
            output_rows.append(
                InstrumentFeatureValue(
                    instrument_id=row.instrument_id,
                    primary_symbol=symbol_by_instrument[row.instrument_id],
                    feature_code=feature_code,
                    feature_value=raw_values_by_feature[feature_code][row.instrument_id],
                    zscore=zscore_by_feature[feature_code][row.instrument_id],
                    evidence_json=evidence_by_feature[(row.instrument_id, feature_code)],
                )
            )
    return tuple(output_rows)


def render_feature_definition_upsert_sql() -> str:
    value_rows = ",\n    ".join(
        "(" + ", ".join(
            (
                sql_literal(str(definition["feature_code"])),
                "'instrument'",
                sql_literal(str(definition["feature_name"])),
                sql_literal(str(definition["description"])),
                "'numeric'",
                sql_literal(definition["default_horizon"]),
                sql_literal(_FEATURE_OWNER),
                "true",
            )
        ) + ")"
        for definition in _FEATURE_DEFINITIONS
    )
    return f"""insert into signal.feature_definition (
    feature_code,
    subject_kind,
    feature_name,
    description,
    value_type,
    default_horizon,
    owner,
    is_active
)
values
    {value_rows}
on conflict (feature_code) do update
set
    subject_kind = excluded.subject_kind,
    feature_name = excluded.feature_name,
    description = excluded.description,
    value_type = excluded.value_type,
    default_horizon = excluded.default_horizon,
    owner = excluded.owner,
    is_active = excluded.is_active;"""


def render_instrument_feature_upsert_sql(
    feature_rows: tuple[InstrumentFeatureValue, ...],
    *,
    as_of_date: date,
    source_run_id: int,
) -> str:
    if not feature_rows:
        raise ValueError("At least one feature row is required.")
    value_rows = ",\n        ".join(_render_feature_value_tuple(row, as_of_date=as_of_date, source_run_id=source_run_id) for row in feature_rows)
    return f"""with source_rows (
    instrument_id,
    as_of_date,
    feature_code,
    feature_value,
    feature_text,
    zscore,
    source_run_id,
    evidence_json
) as (
    values
        {value_rows}
)
insert into signal.instrument_feature_value (
    instrument_id,
    as_of_date,
    feature_code,
    feature_value,
    feature_text,
    zscore,
    source_run_id,
    evidence_json
)
select
    instrument_id,
    as_of_date,
    feature_code,
    feature_value,
    feature_text,
    zscore,
    source_run_id,
    evidence_json
from source_rows
on conflict (instrument_id, as_of_date, feature_code) do update
set
    feature_value = excluded.feature_value,
    feature_text = excluded.feature_text,
    zscore = excluded.zscore,
    source_run_id = excluded.source_run_id,
    evidence_json = excluded.evidence_json;"""


def run_market_feature_snapshot(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    market_code: str = _DEFAULT_MARKET_CODE,
    feature_set_version: str = _DEFAULT_FEATURE_SET_VERSION,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    inputs = load_market_feature_inputs(
        config=config,
        as_of_date=as_of_date,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        universe_version=universe_version,
        market_code=market_code,
        executor=sql_executor,
    )
    feature_rows = compute_market_feature_values(
        inputs,
        as_of_date=as_of_date,
        feature_set_version=feature_set_version,
    )
    universe_batch_id = inputs[0].universe_batch_id
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="market_feature_snapshot",
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "universe_version": universe_version,
            "feature_set_version": feature_set_version,
            "feature_codes": [definition["feature_code"] for definition in _FEATURE_DEFINITIONS],
        },
    )
    try:
        sql_executor.execute_non_query(render_feature_definition_upsert_sql())
        sql_executor.execute_non_query(
            render_instrument_feature_upsert_sql(
                feature_rows,
                as_of_date=as_of_date,
                source_run_id=run_id,
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
        "feature_set_version": feature_set_version,
        "instrument_count": len(inputs),
        "feature_definition_count": len(_FEATURE_DEFINITIONS),
        "feature_row_count": len(feature_rows),
        "selected_symbol_preview": [row.primary_symbol for row in inputs[:10]],
        "feature_code_preview": [definition["feature_code"] for definition in _FEATURE_DEFINITIONS],
    }


def _render_feature_value_tuple(
    row: InstrumentFeatureValue,
    *,
    as_of_date: date,
    source_run_id: int,
) -> str:
    evidence_json = json.dumps(row.evidence_json, ensure_ascii=False, sort_keys=True)
    return "(" + ", ".join(
        (
            f"{row.instrument_id}::bigint",
            sql_date(as_of_date),
            sql_literal(row.feature_code),
            sql_numeric(row.feature_value) if row.feature_value is not None else "null::numeric",
            "null::text",
            sql_numeric(row.zscore) if row.zscore is not None else "null::numeric",
            f"{source_run_id}::bigint",
            f"{sql_literal(evidence_json)}::jsonb",
        )
    ) + ")"


def _calculate_realized_volatility(price_history: tuple[Decimal, ...]) -> Decimal | None:
    if len(price_history) < 2:
        return None
    returns = [
        (current_price / previous_price) - Decimal("1")
        for previous_price, current_price in zip(price_history[:-1], price_history[1:])
    ]
    if len(returns) == 1:
        return _quantize(abs(returns[0]))
    mean_value = sum(returns, Decimal("0")) / Decimal(len(returns))
    variance = sum((value - mean_value) ** 2 for value in returns) / Decimal(len(returns))
    return _quantize(variance.sqrt())


def _calculate_feature_zscores(values_by_instrument: dict[int, Decimal | None]) -> dict[int, Decimal | None]:
    non_null_values = [value for value in values_by_instrument.values() if value is not None]
    if len(non_null_values) < 2:
        return {instrument_id: None for instrument_id in values_by_instrument}
    mean_value = sum(non_null_values, Decimal("0")) / Decimal(len(non_null_values))
    variance = sum((value - mean_value) ** 2 for value in non_null_values) / Decimal(len(non_null_values))
    if variance == 0:
        return {instrument_id: None for instrument_id in values_by_instrument}
    stddev = variance.sqrt()
    return {
        instrument_id: (
            _quantize((value - mean_value) / stddev) if value is not None else None
        )
        for instrument_id, value in values_by_instrument.items()
    }


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)
