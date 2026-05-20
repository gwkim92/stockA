from __future__ import annotations

import csv
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.artifact_runner import (
    redact_command_argv,
    run_data_operation_artifact_command,
)
from stockanalysis.operations.cadence import DATA_OPERATIONS_ARTIFACT_ROOT_ENV
from stockanalysis.operations.env_file import merged_env_with_file
from stockanalysis.operations.env_readiness import PORTFOLIO_POSITIONS_CSV_ENV
from stockanalysis.operations.local_runtime_status import DEFAULT_LOCAL_RUNTIME_ROOT
from stockanalysis.operations.market_price_free_backfill import (
    MARKET_PRICE_BUDGET_LEDGER_PATH_ENV,
    MARKET_PRICE_PROVIDER_ENV,
)
from stockanalysis.operations.path_policy import (
    ensure_repo_outside,
    resolve_existing_file,
    resolve_output_path,
)


DEFAULT_PORTFOLIO_NAME = "Long Term Paper"
DEFAULT_STRATEGY_NAME = "long_term_core"
DEFAULT_HORIZON_TYPE = "long_term"
DEFAULT_MARKET_CODE = "US"
DEFAULT_SCORE_VERSION = "bootstrap-v1"
DEFAULT_THESIS_VERSION = "bootstrap-v1"
DEFAULT_REVIEW_VERSION = "bootstrap-v1"
DEFAULT_REVIEW_SOURCE = "deterministic_bootstrap"
DEFAULT_MACRO_SERIES = ("CPIAUCSL", "FEDFUNDS")
DEFAULT_MACRO_OBSERVATION_START = "2025-01-01"
OPERATING_DATA_REPORT_ENV = "STOCKANALYSIS_OPERATING_DATA_RUN_REPORT"

ArtifactRunner = Callable[..., dict[str, object]]


@dataclass(frozen=True)
class SourcePosition:
    symbol: str
    quantity: Decimal
    cost_basis: Decimal | None


def build_operating_data_run_report(
    *,
    repo_root: str | Path | None = None,
    runtime_root: str | Path = DEFAULT_LOCAL_RUNTIME_ROOT,
    data_operations_env_file: str | Path,
    artifact_root: str | Path | None = None,
    execute: bool = False,
    timeout_seconds: int = 3600,
    python_executable: str | Path | None = None,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
    strategy_name: str = DEFAULT_STRATEGY_NAME,
    horizon_type: str = DEFAULT_HORIZON_TYPE,
    market_code: str = DEFAULT_MARKET_CODE,
    universe_version: str | None = None,
    as_of_date: date | None = None,
    provider: str | None = None,
    daily_budget: int = 24,
    max_requests_per_run: int = 4,
    throttle_seconds: float = 1.0,
    outputsize: str = "100",
    portfolio_notional: Decimal = Decimal("100000"),
    runner: ArtifactRunner = run_data_operation_artifact_command,
    executor: Any | None = None,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if daily_budget <= 0:
        raise ValueError("daily_budget must be positive")
    if max_requests_per_run <= 0:
        raise ValueError("max_requests_per_run must be positive")
    if throttle_seconds < 0:
        raise ValueError("throttle_seconds must not be negative")

    generated_at_value = generated_at or datetime.now(timezone.utc)
    data_env_path = resolve_existing_file(
        data_operations_env_file,
        label="data operations env file",
        repo_root=repo_root,
        require_repo_outside=True,
    )
    env_mapping = merged_env_with_file(data_env_path)
    runtime_path = _resolve_runtime_root(runtime_root, repo_root=repo_root)
    artifact_root_path = _resolve_artifact_root(artifact_root, env=env_mapping, repo_root=repo_root)
    source_positions_path = _resolve_source_positions_path(env_mapping, repo_root=repo_root)
    source_positions = _load_source_positions(source_positions_path)
    resolved_python = str(python_executable or sys.executable)
    resolved_provider = provider or str(env_mapping.get(MARKET_PRICE_PROVIDER_ENV, "alpha_vantage")).strip() or "alpha_vantage"
    ledger_path = _resolve_market_price_ledger(env_mapping, runtime_path=runtime_path, repo_root=repo_root)

    sql_executor = executor if executor is not None else _build_executor_if_configured(env_mapping)
    if execute and sql_executor is None:
        raise ValueError("operating-data-run --execute requires STOCKANALYSIS_PSQL_COMMAND in the env file.")

    context = _load_operating_data_context(sql_executor) if sql_executor is not None else {}
    target_date = _resolve_target_date(explicit_date=as_of_date, context=context, generated_at=generated_at_value)
    resolved_universe_version = universe_version or f"live-{target_date.strftime('%Y%m%d')}"
    initial_prices = _load_latest_price_rows(sql_executor, [position.symbol for position in source_positions])
    event_missing_symbols = _symbol_list(context.get("missing_event_price_symbols"))
    portfolio_missing_symbols = [
        position.symbol
        for position in source_positions
        if position.symbol not in initial_prices or initial_prices[position.symbol].get("adjusted_close") in {None, ""}
    ]
    missing_price_symbols = sorted(set(event_missing_symbols).union(portfolio_missing_symbols))

    generated_dir = _generated_input_dir(runtime_path)
    watchlist_path = generated_dir / f"missing-price-watchlist-{target_date.isoformat()}.csv"
    positions_snapshot_path = generated_dir / f"position-snapshot-{target_date.isoformat()}.csv"

    planned_steps = _build_planned_steps(
        python_executable=resolved_python,
        env_file=data_env_path,
        watchlist_path=watchlist_path,
        positions_snapshot_path=positions_snapshot_path,
        ledger_path=ledger_path,
        missing_price_symbols=missing_price_symbols,
        target_date=target_date,
        portfolio_name=portfolio_name,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        market_code=market_code,
        universe_version=resolved_universe_version,
        provider=resolved_provider,
        daily_budget=daily_budget,
        max_requests_per_run=max_requests_per_run,
        throttle_seconds=throttle_seconds,
        outputsize=outputsize,
        portfolio_notional=portfolio_notional,
    )

    report: dict[str, object] = {
        "report_name": "operating_data_run",
        "generated_at": _format_timestamp(generated_at_value),
        "execute": execute,
        "run_status": "running" if execute else "preview_not_executed",
        "runtime_mode": "local_or_server_runtime",
        "data_operations_env_file": str(data_env_path),
        "artifact_root": str(artifact_root_path),
        "runtime_root": str(runtime_path),
        "generated_input_dir": str(generated_dir),
        "secrets_policy": "values_redacted_env_names_only",
        "broker_submission_allowed": False,
        "kill_switch_mutation_allowed": False,
        "scheduler_mutation_allowed": False,
        "derived_inputs": {
            "as_of_date": target_date.isoformat(),
            "latest_price_date": str(context.get("latest_price_date") or ""),
            "latest_event_date": str(context.get("latest_event_date") or ""),
            "portfolio_name": portfolio_name,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "market_code": market_code,
            "universe_version": resolved_universe_version,
            "source_position_count": len(source_positions),
            "source_symbols": [position.symbol for position in source_positions],
            "event_impacted_symbols": _symbol_list(context.get("event_impacted_symbols")),
            "missing_price_symbols": missing_price_symbols,
        },
        "generated_files": {
            "missing_price_watchlist": str(watchlist_path) if missing_price_symbols else "",
            "position_snapshot_csv": str(positions_snapshot_path),
        },
        "planned_steps": [_public_step(step) for step in planned_steps],
        "artifact_runs": [],
        "failed_step_count": 0,
        "next_actions": ["review planned_steps, then rerun with --execute if DB/provider writes are intended"],
    }
    if not execute:
        _assert_secret_free_payload(report)
        return report

    _write_missing_price_watchlist(watchlist_path, missing_price_symbols)
    artifact_runs: list[dict[str, object]] = []
    failed_step_count = 0

    for step in planned_steps:
        step_id = str(step["step_id"])
        if step_id == "portfolio-position-snapshot":
            refreshed_prices = _load_latest_price_rows(sql_executor, [position.symbol for position in source_positions])
            _write_position_snapshot_csv(
                positions_snapshot_path,
                source_positions=source_positions,
                price_rows=refreshed_prices,
            )
        if step.get("skip_reason"):
            continue
        artifact_run = runner(
            job_id=str(step["artifact_job_id"]),
            artifact_root=artifact_root_path,
            command_argv=step["command_argv"],
            env=env_mapping,
            timeout_seconds=timeout_seconds,
        )
        artifact_runs.append(_artifact_summary(step=step, artifact_run=artifact_run))
        if artifact_run.get("status") != "succeeded" or int(artifact_run.get("exit_code", 1)) != 0:
            failed_step_count += 1
            break

    report["artifact_runs"] = artifact_runs
    report["failed_step_count"] = failed_step_count
    report["run_status"] = "failed" if failed_step_count else "completed"
    report["next_actions"] = (
        ["inspect failed artifact stderr/metadata before re-running operating-data-run"]
        if failed_step_count
        else ["open /data-health and verify operating data freshness"]
    )
    _assert_secret_free_payload(report)
    return report


def load_operating_data_run_visibility_report(
    *,
    report_path: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    repo_root: str | Path | None = None,
) -> dict[str, object]:
    selected_path = str(report_path if report_path is not None else (env or os.environ).get(OPERATING_DATA_REPORT_ENV, "")).strip()
    base = {
        "status": "not_configured",
        "execute": False,
        "generated_at": "",
        "as_of_date": "",
        "failed_step_count": 0,
        "artifact_run_count": 0,
        "missing_price_symbols": [],
        "next_actions": ["run operating-data-run --output outside the repository"],
        "source": "not_configured",
    }
    if not selected_path:
        return base
    try:
        resolved_path = resolve_existing_file(
            selected_path,
            label="operating data run report",
            repo_root=repo_root,
            require_repo_outside=True,
        )
        payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {
            **base,
            "status": "invalid_report",
            "source": "invalid_report",
            "next_actions": ["regenerate operating-data-run summary report"],
        }
    if not isinstance(payload, dict) or payload.get("report_name") != "operating_data_run":
        return {
            **base,
            "status": "invalid_report",
            "source": "invalid_report",
            "next_actions": ["regenerate operating-data-run summary report"],
        }
    derived = payload.get("derived_inputs") if isinstance(payload.get("derived_inputs"), dict) else {}
    visibility = {
        "status": str(payload.get("run_status") or "unknown"),
        "execute": payload.get("execute") is True,
        "generated_at": str(payload.get("generated_at") or ""),
        "as_of_date": str(derived.get("as_of_date") or ""),
        "failed_step_count": int(payload.get("failed_step_count") or 0),
        "artifact_run_count": len(payload.get("artifact_runs")) if isinstance(payload.get("artifact_runs"), list) else 0,
        "missing_price_symbols": _symbol_list(derived.get("missing_price_symbols")),
        "next_actions": [str(item) for item in _list_or_empty(payload.get("next_actions"))],
        "source": "operating_data_run_report",
    }
    _assert_secret_free_payload(visibility)
    return visibility


def _build_planned_steps(
    *,
    python_executable: str,
    env_file: Path,
    watchlist_path: Path,
    positions_snapshot_path: Path,
    ledger_path: Path,
    missing_price_symbols: Sequence[str],
    target_date: date,
    portfolio_name: str,
    strategy_name: str,
    horizon_type: str,
    market_code: str,
    universe_version: str,
    provider: str,
    daily_budget: int,
    max_requests_per_run: int,
    throttle_seconds: float,
    outputsize: str,
    portfolio_notional: Decimal,
) -> list[dict[str, object]]:
    target = target_date.isoformat()
    signal_args = [
        "--as-of-date",
        target,
        "--strategy-name",
        strategy_name,
        "--horizon-type",
        horizon_type,
        "--universe-version",
        universe_version,
        "--market-code",
        market_code,
    ]
    steps: list[dict[str, object]] = [
        {
            "step_id": "missing-symbol-price-backfill",
            "artifact_job_id": "market-price-daily",
            "label": "Backfill event/portfolio symbols missing latest prices",
            "skip_reason": "" if missing_price_symbols else "no_missing_price_symbols",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "market-price-free-backfill-run",
                "--watchlist",
                str(watchlist_path),
                "--ledger",
                str(ledger_path),
                "--provider",
                provider,
                "--env-file",
                str(env_file),
                "--daily-budget",
                str(daily_budget),
                "--max-requests-per-run",
                str(max_requests_per_run),
                "--throttle-seconds",
                str(throttle_seconds),
                "--outputsize",
                outputsize,
                "--skip-if-fresh",
                "--freshness-date",
                target,
            ),
        },
        {
            "step_id": "macro-weekly",
            "artifact_job_id": "macro-weekly",
            "label": "Refresh free macro context",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.ingest.cli",
                "macro-batch-upsert",
                *sum((("--series-id", series_id) for series_id in DEFAULT_MACRO_SERIES), ()),
                "--observation-start",
                DEFAULT_MACRO_OBSERVATION_START,
            ),
        },
    ]
    steps.extend(
        [
            _ingest_step(
                "strategy-universe-slice",
                "cycle-recommendation-weekly",
                "Build strategy universe",
                python_executable,
                "strategy-universe-slice",
                (*signal_args, "--exchange", "Nasdaq", "--exchange", "NYSE", "--min-observation-count", "1"),
            ),
            _ingest_step(
                "market-feature-snapshot",
                "cycle-recommendation-weekly",
                "Build market feature snapshot",
                python_executable,
                "market-feature-snapshot",
                signal_args,
            ),
            _ingest_step(
                "instrument-theme-enrichment",
                "cycle-recommendation-weekly",
                "Link instruments to themes",
                python_executable,
                "instrument-theme-enrichment",
                signal_args,
            ),
            _ingest_step(
                "cycle-state-snapshot",
                "cycle-recommendation-weekly",
                "Refresh theme cycle state",
                python_executable,
                "cycle-state-snapshot",
                (*signal_args, "--score-version", DEFAULT_SCORE_VERSION),
            ),
            _ingest_step(
                "recommendation-bootstrap",
                "cycle-recommendation-weekly",
                "Refresh deterministic recommendations",
                python_executable,
                "recommendation-bootstrap",
                (*signal_args, "--score-version", DEFAULT_SCORE_VERSION),
            ),
            _ingest_step(
                "thesis-bootstrap",
                "cycle-recommendation-weekly",
                "Refresh investment thesis rows",
                python_executable,
                "thesis-bootstrap",
                (*signal_args, "--thesis-version", DEFAULT_THESIS_VERSION),
            ),
            _ingest_step(
                "thesis-review-bootstrap",
                "cycle-recommendation-weekly",
                "Refresh thesis review rows",
                python_executable,
                "thesis-review-bootstrap",
                (*signal_args, "--review-version", DEFAULT_REVIEW_VERSION, "--review-source", DEFAULT_REVIEW_SOURCE),
            ),
            {
                "step_id": "portfolio-position-snapshot",
                "artifact_job_id": "portfolio-position-daily",
                "label": "Upsert latest portfolio position snapshot",
                "skip_reason": "",
                "command_argv": (
                    python_executable,
                    "-m",
                    "stockanalysis.ingest.cli",
                    "portfolio-position-snapshot-upsert",
                    "--positions-csv",
                    str(positions_snapshot_path),
                    "--portfolio-name",
                    portfolio_name,
                    "--snapshot-date",
                    target,
                    "--strategy-name",
                    strategy_name,
                    "--market-code",
                    market_code,
                ),
            },
            _ingest_step(
                "portfolio-remediation-daily",
                "portfolio-remediation-daily",
                "Run portfolio review and remediation tickets",
                python_executable,
                "portfolio-remediation-daily-run",
                (
                    "--portfolio-name",
                    portfolio_name,
                    *signal_args,
                    "--review-version",
                    DEFAULT_REVIEW_VERSION,
                    "--review-source",
                    DEFAULT_REVIEW_SOURCE,
                    "--ticket-status",
                    "open",
                ),
            ),
            _ingest_step(
                "performance-outcome-monthly",
                "performance-outcome-monthly",
                "Run due performance outcome schedule",
                python_executable,
                "performance-outcome-schedule-bootstrap",
                (
                    "--due-on-date",
                    target,
                    "--strategy-name",
                    strategy_name,
                    "--horizon-type",
                    horizon_type,
                    "--universe-version",
                    universe_version,
                    "--market-code",
                    market_code,
                ),
            ),
            {
                "step_id": "paper-safety-bootstrap",
                "artifact_job_id": "portfolio-remediation-daily",
                "label": "Ensure simulated paper safety config exists",
                "skip_reason": "",
                "command_argv": (
                    python_executable,
                    "-m",
                    "stockanalysis.operations.cli",
                    "paper-safety-bootstrap-config",
                    "--env-file",
                    str(env_file),
                    "--portfolio-name",
                    portfolio_name,
                ),
            },
            {
                "step_id": "paper-validation-audit",
                "artifact_job_id": "portfolio-remediation-daily",
                "label": "Write broker-free paper validation audit",
                "skip_reason": "",
                "command_argv": (
                    python_executable,
                    "-m",
                    "stockanalysis.operations.cli",
                    "paper-validation-audit-run",
                    "--env-file",
                    str(env_file),
                    "--as-of-date",
                    target,
                    "--portfolio-notional",
                    str(portfolio_notional),
                    "--created-by",
                    "operating-data-run",
                ),
            },
        ]
    )
    return steps


def _ingest_step(
    step_id: str,
    artifact_job_id: str,
    label: str,
    python_executable: str,
    command: str,
    args: Sequence[str],
) -> dict[str, object]:
    return {
        "step_id": step_id,
        "artifact_job_id": artifact_job_id,
        "label": label,
        "skip_reason": "",
        "command_argv": (python_executable, "-m", "stockanalysis.ingest.cli", command, *args),
    }


def _load_operating_data_context(executor: Any) -> dict[str, Any]:
    payload = executor.execute_scalar(_render_operating_data_context_sql())
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("operating data context query did not return JSON") from exc
    return parsed if isinstance(parsed, dict) else {}


def _render_operating_data_context_sql() -> str:
    return """-- operating data context lookup
with latest_price as (
    select max(trade_date) as latest_price_date
    from market.daily_price_bar
),
latest_event as (
    select max((event_at at time zone 'UTC')::date) as latest_event_date
    from event.event
),
impacted_symbols as (
    select distinct upper(instrument.primary_symbol) as symbol
    from event.event event_row
    join event.event_instrument_impact impact on impact.event_id = event_row.event_id
    join ref.instrument instrument on instrument.instrument_id = impact.instrument_id
    where (event_row.event_at at time zone 'UTC')::date >= coalesce((select latest_event_date from latest_event), current_date) - interval '30 days'
),
missing_price_symbols as (
    select impacted.symbol
    from impacted_symbols impacted
    left join ref.instrument instrument on upper(instrument.primary_symbol) = impacted.symbol
    left join market.daily_price_bar bar
      on bar.instrument_id = instrument.instrument_id
     and bar.trade_date = (select latest_price_date from latest_price)
    where bar.instrument_id is null
)
select json_build_object(
    'latest_price_date', (select latest_price_date from latest_price),
    'latest_event_date', (select latest_event_date from latest_event),
    'event_impacted_symbols', coalesce((select json_agg(symbol order by symbol) from impacted_symbols), '[]'::json),
    'missing_event_price_symbols', coalesce((select json_agg(symbol order by symbol) from missing_price_symbols), '[]'::json)
)::text;"""


def _load_latest_price_rows(executor: Any | None, symbols: Sequence[str]) -> dict[str, dict[str, str]]:
    if executor is None or not symbols:
        return {}
    payload = executor.execute_scalar(_render_latest_price_lookup_sql(symbols))
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("latest price lookup did not return JSON") from exc
    rows = parsed if isinstance(parsed, list) else []
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        symbol = str(row.get("symbol") or "").upper()
        if symbol:
            result[symbol] = {str(key): str(value) if value is not None else "" for key, value in row.items()}
    return result


def _render_latest_price_lookup_sql(symbols: Sequence[str]) -> str:
    value_rows = ", ".join(f"({sql_literal(symbol.upper())})" for symbol in symbols)
    return f"""-- operating data latest price lookup
with requested(symbol) as (
    values {value_rows}
),
latest_prices as (
    select distinct on (requested.symbol)
        requested.symbol,
        bar.trade_date,
        bar.adjusted_close,
        bar.close
    from requested
    left join ref.instrument instrument on upper(instrument.primary_symbol) = requested.symbol
    left join market.daily_price_bar bar on bar.instrument_id = instrument.instrument_id
    order by requested.symbol, bar.trade_date desc nulls last
)
select coalesce(
    json_agg(
        json_build_object(
            'symbol', symbol,
            'trade_date', trade_date,
            'adjusted_close', adjusted_close,
            'close', close
        )
        order by symbol
    ),
    '[]'::json
)::text
from latest_prices;"""


def _load_source_positions(path: Path) -> list[SourcePosition]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise ValueError("portfolio source CSV must include a header row")
        if "symbol" not in reader.fieldnames or "quantity" not in reader.fieldnames:
            raise ValueError("portfolio source CSV must include symbol and quantity columns")
        positions: list[SourcePosition] = []
        for row_number, row in enumerate(reader, start=2):
            symbol = str(row.get("symbol") or "").strip().upper()
            if not symbol:
                raise ValueError(f"portfolio source CSV row {row_number} has an empty symbol")
            positions.append(
                SourcePosition(
                    symbol=symbol,
                    quantity=_decimal(row.get("quantity"), label=f"quantity at row {row_number}"),
                    cost_basis=_optional_decimal(row.get("cost_basis"), label=f"cost_basis at row {row_number}"),
                )
            )
    if not positions:
        raise ValueError("portfolio source CSV must include at least one position")
    return positions


def _write_missing_price_watchlist(path: Path, symbols: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=("symbol",))
        writer.writeheader()
        for symbol in symbols:
            writer.writerow({"symbol": symbol})


def _write_position_snapshot_csv(
    path: Path,
    *,
    source_positions: Sequence[SourcePosition],
    price_rows: Mapping[str, Mapping[str, str]],
) -> None:
    rows: list[dict[str, str]] = []
    total_market_value = Decimal("0")
    for position in source_positions:
        price_row = price_rows.get(position.symbol)
        if not price_row:
            raise ValueError(f"Missing latest market price for portfolio symbol: {position.symbol}")
        market_price = _decimal(
            price_row.get("adjusted_close") or price_row.get("close"),
            label=f"latest market price for {position.symbol}",
        )
        market_value = position.quantity * market_price
        total_market_value += market_value
        cost_basis = position.cost_basis
        unrealized_pnl = (market_price - cost_basis) * position.quantity if cost_basis is not None else None
        rows.append(
            {
                "symbol": position.symbol,
                "quantity": _format_decimal(position.quantity, places="0.00000000"),
                "cost_basis": _format_decimal(cost_basis, places="0.000000") if cost_basis is not None else "",
                "market_price": _format_decimal(market_price, places="0.000000"),
                "market_value": _format_decimal(market_value, places="0.01"),
                "weight": "",
                "unrealized_pnl": _format_decimal(unrealized_pnl, places="0.01") if unrealized_pnl is not None else "",
                "linked_thesis_id": "",
            }
        )
    if total_market_value <= 0:
        raise ValueError("portfolio source positions produce non-positive market value")
    for row in rows:
        market_value = _decimal(row["market_value"], label=f"market value for {row['symbol']}")
        row["weight"] = _format_decimal(market_value / total_market_value, places="0.0000")

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        fieldnames = (
            "symbol",
            "quantity",
            "cost_basis",
            "market_price",
            "market_value",
            "weight",
            "unrealized_pnl",
            "linked_thesis_id",
        )
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _public_step(step: Mapping[str, object]) -> dict[str, object]:
    return {
        "step_id": str(step.get("step_id") or ""),
        "artifact_job_id": str(step.get("artifact_job_id") or ""),
        "label": str(step.get("label") or ""),
        "skip_reason": str(step.get("skip_reason") or ""),
        "command_argv": redact_command_argv(tuple(str(item) for item in _list_or_empty(step.get("command_argv")))),
    }


def _artifact_summary(*, step: Mapping[str, object], artifact_run: Mapping[str, object]) -> dict[str, object]:
    return {
        "step_id": str(step.get("step_id") or ""),
        "artifact_job_id": str(step.get("artifact_job_id") or ""),
        "status": str(artifact_run.get("status") or "unknown"),
        "exit_code": int(artifact_run.get("exit_code") or 0),
        "artifact_dir": str(artifact_run.get("artifact_dir") or ""),
        "metadata_path": str(artifact_run.get("metadata_path") or ""),
        "stdout_path": str(artifact_run.get("stdout_path") or ""),
        "stderr_path": str(artifact_run.get("stderr_path") or ""),
    }


def _resolve_runtime_root(runtime_root: str | Path, *, repo_root: str | Path | None) -> Path:
    runtime_path = Path(runtime_root).expanduser().resolve()
    ensure_repo_outside(runtime_path, repo_root=repo_root, label="operating data runtime root")
    runtime_path.mkdir(parents=True, exist_ok=True)
    return runtime_path


def _resolve_artifact_root(
    explicit_artifact_root: str | Path | None,
    *,
    env: Mapping[str, str],
    repo_root: str | Path | None,
) -> Path:
    selected = explicit_artifact_root or str(env.get(DATA_OPERATIONS_ARTIFACT_ROOT_ENV, "")).strip()
    if not selected:
        raise ValueError(f"Provide --artifact-root or configure {DATA_OPERATIONS_ARTIFACT_ROOT_ENV}.")
    return resolve_output_path(
        selected,
        label="operating data artifact root",
        repo_root=repo_root,
        require_repo_outside=True,
    )


def _resolve_source_positions_path(env: Mapping[str, str], *, repo_root: str | Path | None) -> Path:
    selected = str(env.get(PORTFOLIO_POSITIONS_CSV_ENV, "")).strip()
    if not selected:
        raise ValueError(f"Missing required environment variable: {PORTFOLIO_POSITIONS_CSV_ENV}.")
    return resolve_existing_file(
        selected,
        label="portfolio source positions CSV",
        repo_root=repo_root,
        require_repo_outside=True,
    )


def _resolve_market_price_ledger(env: Mapping[str, str], *, runtime_path: Path, repo_root: str | Path | None) -> Path:
    selected = str(env.get(MARKET_PRICE_BUDGET_LEDGER_PATH_ENV, "")).strip()
    ledger_path = Path(selected).expanduser() if selected else runtime_path / "market-price-budget-ledger.json"
    return resolve_output_path(
        ledger_path,
        label="market price provider budget ledger",
        repo_root=repo_root,
        require_repo_outside=True,
    )


def _generated_input_dir(runtime_path: Path) -> Path:
    generated_dir = runtime_path / "operating-data"
    generated_dir.mkdir(parents=True, exist_ok=True)
    return generated_dir


def _build_executor_if_configured(env: Mapping[str, str]) -> PsqlCommandExecutor | None:
    if not str(env.get("STOCKANALYSIS_PSQL_COMMAND", "")).strip():
        return None
    config = RuntimeConfig(
        sec_user_agent=env.get("STOCKANALYSIS_SEC_USER_AGENT"),
        fred_api_key=env.get("STOCKANALYSIS_FRED_API_KEY"),
        alpha_vantage_api_key=env.get("STOCKANALYSIS_ALPHA_VANTAGE_API_KEY"),
        twelve_data_api_key=env.get("STOCKANALYSIS_TWELVE_DATA_API_KEY"),
        database_url=env.get("STOCKANALYSIS_DATABASE_URL"),
        psql_command=env.get("STOCKANALYSIS_PSQL_COMMAND"),
    )
    return PsqlCommandExecutor.from_config(config)


def _resolve_target_date(*, explicit_date: date | None, context: Mapping[str, Any], generated_at: datetime) -> date:
    if explicit_date is not None:
        return explicit_date
    latest_price_date = str(context.get("latest_price_date") or "").strip()
    if latest_price_date:
        return date.fromisoformat(latest_price_date)
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=timezone.utc)
    return generated_at.astimezone(timezone.utc).date()


def _symbol_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted({str(item).strip().upper() for item in value if str(item).strip()})


def _list_or_empty(value: object) -> list[object]:
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, list):
        return value
    return []


def _decimal(value: object, *, label: str) -> Decimal:
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"Invalid decimal for {label}: {value!r}") from exc


def _optional_decimal(value: object, *, label: str) -> Decimal | None:
    if value is None or str(value).strip() == "":
        return None
    return _decimal(value, label=label)


def _format_decimal(value: Decimal, *, places: str) -> str:
    return str(value.quantize(Decimal(places)))


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _assert_secret_free_payload(payload: Mapping[str, object]) -> None:
    text = json.dumps(payload, sort_keys=True)
    forbidden_markers = (
        "postgresql://",
        "postgres://",
        "hidden-",
        "token-",
        "api-key-",
        "runtime_pass",
        "bearer ",
    )
    for marker in forbidden_markers:
        if marker in text.lower():
            raise ValueError("Operating data run report contains a secret-like value.")
