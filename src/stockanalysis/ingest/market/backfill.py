from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.market.price import run_market_price_batch_upsert
from stockanalysis.ingest.psql import PsqlCommandExecutor

_DEFAULT_REQUESTED_EXCHANGES = ("Nasdaq", "NYSE")
_EXCHANGE_TO_MIC = {
    "nasdaq": ("Nasdaq", "XNAS"),
    "nyse": ("NYSE", "XNYS"),
}


@dataclass(frozen=True)
class CanonicalUniverseSymbol:
    symbol: str
    mic_code: str
    exchange_name: str


def load_active_universe_symbols(
    *,
    config: RuntimeConfig,
    exchanges: list[str] | None = None,
    limit: int | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> tuple[CanonicalUniverseSymbol, ...]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    mic_codes = _resolve_requested_mic_codes(exchanges)
    payload_text = sql_executor.execute_scalar(
        render_active_universe_symbol_lookup_sql(
            mic_codes=mic_codes,
            limit=limit,
        )
    )
    payload = json.loads(payload_text)
    if not isinstance(payload, list):
        raise ValueError("Canonical universe symbol lookup did not return a JSON array.")
    symbols: list[CanonicalUniverseSymbol] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Canonical universe symbol lookup returned a non-object row.")
        symbol = str(item["symbol"]).strip().upper()
        mic_code = str(item["mic_code"]).strip()
        exchange_name = str(item["exchange_name"]).strip()
        if not symbol or not mic_code or not exchange_name:
            continue
        symbols.append(
            CanonicalUniverseSymbol(
                symbol=symbol,
                mic_code=mic_code,
                exchange_name=exchange_name,
            )
        )
    if not symbols:
        raise ValueError("No active canonical symbols matched the requested universe filters.")
    return tuple(symbols)


def render_active_universe_symbol_lookup_sql(
    *,
    mic_codes: tuple[str, ...],
    limit: int | None = None,
) -> str:
    if limit is not None and limit <= 0:
        raise ValueError("limit must be greater than 0")

    mic_filter = ""
    if mic_codes:
        quoted_mic_codes = ", ".join(sql_literal(mic_code) for mic_code in mic_codes)
        mic_filter = f"\n  and e.mic_code in ({quoted_mic_codes})"
    limit_clause = "" if limit is None else f"\nlimit {limit}"
    return f"""select coalesce(
    json_agg(
        json_build_object(
            'symbol', q.primary_symbol,
            'mic_code', q.mic_code,
            'exchange_name', q.exchange_name
        )
        order by q.primary_symbol
    ),
    '[]'::json
)::text
from (
    select
        i.primary_symbol,
        e.mic_code,
        e.name as exchange_name
    from ref.instrument i
    join ref.exchange e on e.exchange_id = i.exchange_id
    where i.is_active = true
      and i.delisted_at is null{mic_filter}
    order by i.primary_symbol{limit_clause}
) q;"""


def run_market_price_universe_backfill(
    *,
    config: RuntimeConfig,
    exchanges: list[str] | None = None,
    limit: int | None = None,
    fixtures_dir: str | None = None,
    outputsize: str | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    selected_symbols = load_active_universe_symbols(
        config=config,
        exchanges=exchanges,
        limit=limit,
        executor=sql_executor,
    )
    batch_summary = run_market_price_batch_upsert(
        [symbol.symbol for symbol in selected_symbols],
        config=config,
        fixtures_dir=fixtures_dir,
        outputsize=outputsize,
        executor=sql_executor,
    )
    exchange_counts = Counter(symbol.exchange_name for symbol in selected_symbols)
    return {
        "selected_symbol_count": len(selected_symbols),
        "requested_exchanges": list(_resolve_requested_exchange_names(exchanges)),
        "selected_exchange_counts": dict(sorted(exchange_counts.items())),
        "selected_symbol_preview": [symbol.symbol for symbol in selected_symbols[:10]],
        **batch_summary,
    }


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
