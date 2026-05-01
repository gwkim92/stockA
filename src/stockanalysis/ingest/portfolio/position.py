from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal, sql_numeric
from stockanalysis.ingest.psql import PsqlCommandExecutor

_DEFAULT_BASE_CURRENCY = "USD"
_DEFAULT_MARKET_CODE = "US"


@dataclass(frozen=True)
class PositionSnapshotRecord:
    symbol: str
    quantity: Decimal
    market_price: Decimal
    market_value: Decimal
    cost_basis: Decimal | None
    weight: Decimal | None
    unrealized_pnl: Decimal | None
    linked_thesis_id: int | None


@dataclass(frozen=True)
class PositionSnapshotSyncResult:
    portfolio_name: str
    base_currency: str
    market_code: str
    strategy_name: str
    snapshot_date: date
    is_paper: bool
    positions: tuple[PositionSnapshotRecord, ...]

    def summary(self) -> dict[str, object]:
        return {
            "portfolio_name": self.portfolio_name,
            "base_currency": self.base_currency,
            "market_code": self.market_code,
            "strategy_name": self.strategy_name,
            "snapshot_date": self.snapshot_date.isoformat(),
            "is_paper": self.is_paper,
            "position_count": len(self.positions),
            "symbol_preview": [record.symbol for record in self.positions[:10]],
        }


def load_position_snapshot_sync_result(
    *,
    positions_csv_path: str,
    portfolio_name: str,
    strategy_name: str,
    snapshot_date: date,
    base_currency: str = _DEFAULT_BASE_CURRENCY,
    market_code: str = _DEFAULT_MARKET_CODE,
    is_paper: bool = True,
) -> PositionSnapshotSyncResult:
    csv_path = Path(positions_csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing position snapshot CSV: {csv_path}")

    records: list[PositionSnapshotRecord] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("Position snapshot CSV must include a header row.")
        _validate_required_columns(reader.fieldnames)
        for row_number, raw_row in enumerate(reader, start=2):
            records.append(_parse_position_row(raw_row, row_number=row_number))

    if not records:
        raise ValueError("Position snapshot CSV must include at least one row.")

    return PositionSnapshotSyncResult(
        portfolio_name=portfolio_name,
        base_currency=base_currency.upper(),
        market_code=market_code.upper(),
        strategy_name=strategy_name,
        snapshot_date=snapshot_date,
        is_paper=is_paper,
        positions=tuple(records),
    )


def render_position_snapshot_upsert_sql(
    result: PositionSnapshotSyncResult,
    *,
    source_run_id: int | None = None,
) -> str:
    run_literal = "null::bigint" if source_run_id is None else f"{source_run_id}::bigint"
    value_rows = ",\n        ".join(_render_position_value_tuple(record) for record in result.positions)
    return f"""begin;

with upsert_portfolio as (
    insert into portfolio.portfolio (
        portfolio_name,
        base_currency,
        market_code,
        strategy_name,
        is_paper
    )
    values (
        {sql_literal(result.portfolio_name)},
        {sql_literal(result.base_currency)},
        {sql_literal(result.market_code)},
        {sql_literal(result.strategy_name)},
        {sql_literal(result.is_paper)}
    )
    on conflict (portfolio_name) do update
    set
        base_currency = excluded.base_currency,
        market_code = excluded.market_code,
        strategy_name = excluded.strategy_name,
        is_paper = excluded.is_paper
    returning portfolio_id
),
source_rows (
    symbol,
    quantity,
    cost_basis,
    market_price,
    market_value,
    weight,
    unrealized_pnl,
    linked_thesis_id
) as (
    values
        {value_rows}
),
resolved_rows as (
    select
        upsert_portfolio.portfolio_id,
        instrument.instrument_id,
        source_rows.symbol,
        source_rows.quantity,
        source_rows.cost_basis,
        source_rows.market_price,
        source_rows.market_value,
        source_rows.weight,
        source_rows.unrealized_pnl,
        coalesce(source_rows.linked_thesis_id, active_thesis.thesis_id) as linked_thesis_id
    from source_rows
    join ref.instrument instrument
      on instrument.is_active = true
     and lower(instrument.primary_symbol) = lower(source_rows.symbol)
    join upsert_portfolio on true
    left join lateral (
        select thesis.thesis_id
        from signal.investment_thesis thesis
        where thesis.instrument_id = instrument.instrument_id
          and thesis.status = 'active'
        order by thesis.thesis_id desc
        limit 1
    ) active_thesis on true
),
upsert_positions as (
    insert into portfolio.position_snapshot (
        portfolio_id,
        instrument_id,
        snapshot_date,
        quantity,
        cost_basis,
        market_price,
        market_value,
        weight,
        unrealized_pnl,
        linked_thesis_id,
        source_run_id
    )
    select
        portfolio_id,
        instrument_id,
        {sql_date(result.snapshot_date)},
        quantity,
        cost_basis,
        market_price,
        market_value,
        weight,
        unrealized_pnl,
        linked_thesis_id,
        {run_literal}
    from resolved_rows
    on conflict (portfolio_id, instrument_id, snapshot_date) do update
    set
        quantity = excluded.quantity,
        cost_basis = excluded.cost_basis,
        market_price = excluded.market_price,
        market_value = excluded.market_value,
        weight = excluded.weight,
        unrealized_pnl = excluded.unrealized_pnl,
        linked_thesis_id = excluded.linked_thesis_id,
        source_run_id = excluded.source_run_id
    returning linked_thesis_id
)
select json_build_object(
    'portfolio_id', (select portfolio_id from upsert_portfolio),
    'source_position_count', (select count(*) from source_rows),
    'position_count', (select count(*) from upsert_positions),
    'linked_thesis_count', (select count(*) from upsert_positions where linked_thesis_id is not null)
)::text;

commit;
"""


def run_position_snapshot_upsert(
    *,
    config: RuntimeConfig,
    positions_csv_path: str,
    portfolio_name: str,
    strategy_name: str,
    snapshot_date: date,
    base_currency: str = _DEFAULT_BASE_CURRENCY,
    market_code: str = _DEFAULT_MARKET_CODE,
    is_paper: bool = True,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    result = load_position_snapshot_sync_result(
        positions_csv_path=positions_csv_path,
        portfolio_name=portfolio_name,
        strategy_name=strategy_name,
        snapshot_date=snapshot_date,
        base_currency=base_currency,
        market_code=market_code,
        is_paper=is_paper,
    )
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="portfolio_position_snapshot_upsert",
        config_json={
            "positions_csv_path": positions_csv_path,
            "portfolio_name": portfolio_name,
            "base_currency": base_currency,
            "market_code": market_code,
            "strategy_name": strategy_name,
            "snapshot_date": snapshot_date.isoformat(),
            "is_paper": is_paper,
            "position_count": len(result.positions),
        },
    )
    try:
        upsert_result = json.loads(
            sql_executor.execute_scalar(render_position_snapshot_upsert_sql(result, source_run_id=run_id))
        )
        if int(upsert_result["position_count"]) != len(result.positions):
            raise ValueError(
                "Not all position snapshot rows matched canonical instruments: "
                f"{upsert_result['position_count']} of {len(result.positions)} inserted."
            )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    summary = result.summary()
    summary["run_id"] = run_id
    summary["portfolio_id"] = int(upsert_result["portfolio_id"])
    summary["linked_thesis_count"] = int(upsert_result["linked_thesis_count"])
    return summary


def _validate_required_columns(fieldnames: list[str]) -> None:
    normalized = {field.strip().lower() for field in fieldnames}
    required = {"symbol", "quantity", "market_price", "market_value"}
    missing = sorted(required - normalized)
    if missing:
        raise ValueError(f"Position snapshot CSV missing required columns: {', '.join(missing)}")


def _parse_position_row(raw_row: dict[str, str], *, row_number: int) -> PositionSnapshotRecord:
    row = {key.strip().lower(): (value.strip() if value is not None else "") for key, value in raw_row.items()}
    try:
        symbol = _required_text(row, "symbol").upper()
        return PositionSnapshotRecord(
            symbol=symbol,
            quantity=_required_decimal(row, "quantity"),
            market_price=_required_decimal(row, "market_price"),
            market_value=_required_decimal(row, "market_value"),
            cost_basis=_optional_decimal(row.get("cost_basis")),
            weight=_optional_decimal(row.get("weight")),
            unrealized_pnl=_optional_decimal(row.get("unrealized_pnl")),
            linked_thesis_id=_optional_int(row.get("linked_thesis_id")),
        )
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid position snapshot CSV row {row_number}.") from exc


def _required_text(row: dict[str, str], key: str) -> str:
    value = row.get(key, "")
    if not value:
        raise ValueError(f"`{key}` is required.")
    return value


def _required_decimal(row: dict[str, str], key: str) -> Decimal:
    value = row.get(key, "")
    if not value:
        raise ValueError(f"`{key}` is required.")
    return Decimal(value)


def _optional_decimal(value: str | None) -> Decimal | None:
    if value is None or value == "":
        return None
    return Decimal(value)


def _optional_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _render_position_value_tuple(record: PositionSnapshotRecord) -> str:
    return "(" + ", ".join(
        (
            sql_literal(record.symbol),
            sql_numeric(record.quantity),
            _sql_numeric_or_null(record.cost_basis),
            sql_numeric(record.market_price),
            sql_numeric(record.market_value),
            _sql_numeric_or_null(record.weight),
            _sql_numeric_or_null(record.unrealized_pnl),
            _sql_bigint_or_null(record.linked_thesis_id),
        )
    ) + ")"


def _sql_numeric_or_null(value: Decimal | None) -> str:
    if value is None:
        return "null::numeric"
    return sql_numeric(value)


def _sql_bigint_or_null(value: int | None) -> str:
    if value is None:
        return "null::bigint"
    return f"{value}::bigint"


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
    'ingest',
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
    truncated = error_summary.strip()[:2000] or "position snapshot upsert failed"
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
