"""Opt-in daily price coverage for active recommendations within existing budgets."""
from __future__ import annotations

import csv
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def prepare_priority_watchlist(*, source_path: str, destination: Path, executor: Any) -> dict[str, object]:
    # Import here because the daily runner is the caller and owns the CSV contract.
    from stockanalysis.operations.market_price_free_backfill import load_market_price_watchlist

    configured = load_market_price_watchlist(source_path)
    metadata = {item.symbol: item.metadata for item in configured}
    symbols_json = json.dumps(list(metadata)).replace("'", "''")
    sql = f"""
with requested as (
    select jsonb_array_elements_text('{symbols_json}'::jsonb) as symbol
    union
    select i.primary_symbol from signal.recommendation r
    join ref.instrument i on i.instrument_id = r.instrument_id
    where r.status = 'active'
), dated as (
    select requested.symbol, max(b.trade_date) as latest_trade_date
    from requested
    left join ref.instrument i on i.primary_symbol = requested.symbol
    left join market.daily_price_bar b on b.instrument_id = i.instrument_id
    group by requested.symbol
)
select coalesce(json_agg(json_build_object('symbol', symbol, 'latest_trade_date', latest_trade_date)
    order by latest_trade_date asc nulls first, symbol), '[]'::json)::text from dated;
"""
    rows = json.loads(executor.execute_scalar(sql))
    if not isinstance(rows, list) or not 1 <= len(rows) <= 500:
        raise ValueError("Active price watchlist must contain between 1 and 500 symbols.")
    seen: set[str] = set()
    for row in rows:
        symbol = row.get("symbol") if isinstance(row, dict) else None
        if not isinstance(symbol, str) or not symbol.strip() or symbol != symbol.strip().upper() or symbol in seen:
            raise ValueError("Invalid active price watchlist symbol.")
        seen.add(symbol)
    if not set(metadata).issubset(seen):
        raise ValueError("Active price watchlist lost configured symbols.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=destination.parent, delete=False) as stream:
            temporary = Path(stream.name)
            writer = csv.DictWriter(stream, fieldnames=["symbol", "role"])
            writer.writeheader()
            for row in rows:
                symbol = row["symbol"]
                writer.writerow({"symbol": symbol, "role": metadata.get(symbol, {}).get("role", "active_recommendation")})
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return {"policy": "configured_and_active_oldest_first", "configured_symbol_count": len(metadata),
            "selected_symbol_count": len(rows), "generated_watchlist_path": str(destination)}
