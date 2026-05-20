from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.market.price import resolve_market_price_provider, run_market_price_batch_upsert
from stockanalysis.ingest.psql import PsqlCommandExecutor


LEDGER_VERSION = "market-price-provider-budget-v1"
DEFAULT_PROVIDER = "alpha_vantage"
MARKET_PRICE_PROVIDER_ENV = "STOCKANALYSIS_MARKET_PRICE_PROVIDER"
MARKET_PRICE_BUDGET_LEDGER_PATH_ENV = "STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH"
MARKET_PRICE_WATCHLIST_CSV_ENV = "STOCKANALYSIS_MARKET_PRICE_WATCHLIST_CSV"
MARKET_PRICE_DAILY_BUDGET_ENV = "STOCKANALYSIS_MARKET_PRICE_DAILY_BUDGET"
MARKET_PRICE_MAX_REQUESTS_PER_RUN_ENV = "STOCKANALYSIS_MARKET_PRICE_MAX_REQUESTS_PER_RUN"
MARKET_PRICE_THROTTLE_SECONDS_ENV = "STOCKANALYSIS_MARKET_PRICE_THROTTLE_SECONDS"
MARKET_PRICE_OUTPUTSIZE_ENV = "STOCKANALYSIS_MARKET_PRICE_OUTPUTSIZE"
MARKET_PRICE_FRESHNESS_DATE_ENV = "DATA_OPERATIONS_SCHEDULER_MARKET_PRICE_FRESHNESS_DATE"
MARKET_PRICE_FRESHNESS_POLICY_ENV = "DATA_OPERATIONS_SCHEDULER_MARKET_PRICE_FRESHNESS_POLICY"
MARKET_PRICE_NON_TRADING_DATES_ENV = "DATA_OPERATIONS_SCHEDULER_MARKET_PRICE_NON_TRADING_DATES"
MARKET_PRICE_DATA_READY_LOCAL_TIME_ENV = "DATA_OPERATIONS_SCHEDULER_MARKET_PRICE_DATA_READY_LOCAL_TIME"
DATA_OPERATIONS_SCHEDULER_RUN_DATE_ENV = "DATA_OPERATIONS_SCHEDULER_RUN_DATE"
DATA_OPERATIONS_SCHEDULER_SKIP_DATES_ENV = "DATA_OPERATIONS_SCHEDULER_SKIP_DATES"
MARKET_PRICE_DEFAULT_FRESHNESS_POLICY = "latest_completed_us_market_day"
MARKET_PRICE_TIMEZONE = "America/New_York"
MARKET_PRICE_DEFAULT_DATA_READY_LOCAL_TIME = "18:30"

_DEFAULT_DAILY_BUDGET_BY_PROVIDER = {
    "alpha_vantage": 25,
    "twelve_data": 800,
}
_DEFAULT_MAX_REQUESTS_PER_RUN_BY_PROVIDER = {
    "alpha_vantage": 25,
    "twelve_data": 50,
}
_DEFAULT_THROTTLE_SECONDS_BY_PROVIDER = {
    "alpha_vantage": 12.0,
    "twelve_data": 8.0,
}
_DEFAULT_OUTPUTSIZE_BY_PROVIDER = {
    "alpha_vantage": "compact",
    "twelve_data": "100",
}


@dataclass(frozen=True)
class WatchlistSymbol:
    symbol: str
    row_number: int
    metadata: dict[str, str]


@dataclass(frozen=True)
class MarketPriceFreshnessResolution:
    freshness_date: date | None
    policy: str
    source: str
    market_timezone: str
    data_ready_local_time: str
    non_trading_dates: tuple[date, ...]


def load_market_price_watchlist(path: str | Path) -> tuple[WatchlistSymbol, ...]:
    watchlist_path = Path(path)
    with watchlist_path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        symbol_field = _resolve_symbol_field(reader.fieldnames)
        symbols: list[WatchlistSymbol] = []
        seen: set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            raw_symbol = str(row.get(symbol_field, "")).strip()
            if not raw_symbol:
                raise ValueError(f"watchlist row {row_number} has an empty symbol.")
            symbol = raw_symbol.upper()
            if symbol in seen:
                continue
            seen.add(symbol)
            metadata = {
                key: str(value).strip()
                for key, value in row.items()
                if key is not None and key != symbol_field and value is not None
            }
            symbols.append(WatchlistSymbol(symbol=symbol, row_number=row_number, metadata=metadata))
    if not symbols:
        raise ValueError("watchlist must contain at least one symbol.")
    return tuple(symbols)


def run_market_price_free_backfill(
    *,
    config: RuntimeConfig,
    watchlist_path: str | Path,
    ledger_path: str | Path,
    provider: str = DEFAULT_PROVIDER,
    budget_date: date | None = None,
    daily_budget: int = 25,
    max_requests_per_run: int = 25,
    throttle_seconds: float = 1.0,
    fixtures_dir: str | None = None,
    outputsize: str | None = None,
    skip_if_fresh: bool = False,
    freshness_date: date | None = None,
    executor: PsqlCommandExecutor | None = None,
    run_started_at: datetime | None = None,
) -> dict[str, object]:
    resolved_provider = resolve_market_price_provider(provider)
    _validate_budget_inputs(
        daily_budget=daily_budget,
        max_requests_per_run=max_requests_per_run,
        throttle_seconds=throttle_seconds,
    )
    budget_day = budget_date or _utc_now().date()
    budget_day_key = budget_day.isoformat()
    started_at = _format_utc(run_started_at or _utc_now())
    watchlist_symbols = load_market_price_watchlist(watchlist_path)
    requested_symbols = [item.symbol for item in watchlist_symbols]

    ledger = load_budget_ledger(ledger_path, provider=resolved_provider)
    day_state = _resolve_day_state(ledger, budget_day_key=budget_day_key, daily_budget=daily_budget)
    used_before = int(day_state.get("used_request_count", 0))
    budget_remaining_before = max(0, daily_budget - used_before)
    request_budget_for_run = min(max_requests_per_run, budget_remaining_before)

    if request_budget_for_run <= 0:
        budget_block_reason = (
            "daily_provider_budget_exhausted"
            if budget_remaining_before <= 0
            else "run_request_budget_exhausted"
        )
        skipped_results = [
            {
                "symbol": symbol,
                "status": "skipped",
                "reason": budget_block_reason,
                "request_budget": 0,
            }
            for symbol in requested_symbols
        ]
        summary: dict[str, object] = {
            "report_name": "market_price_free_backfill_run",
            "status": "no_provider_request_budget",
            "budget_block_reason": budget_block_reason,
            "provider": resolved_provider,
            "budget_date": budget_day_key,
            "daily_budget": daily_budget,
            "used_request_count_before": used_before,
            "used_request_count_after": used_before,
            "budget_remaining_before": budget_remaining_before,
            "budget_remaining_after": budget_remaining_before,
            "request_budget_for_run": 0,
            "watchlist_path": str(Path(watchlist_path).resolve()),
            "ledger_path": str(Path(ledger_path).resolve()),
            "requested_symbol_count": len(requested_symbols),
            "succeeded_symbol_count": 0,
            "failed_symbol_count": 0,
            "skipped_symbol_count": len(requested_symbols),
            "provider_request_count": 0,
            "results": skipped_results,
        }
        _append_run_record(day_state, summary=summary, started_at=started_at, requested_symbols=requested_symbols)
        write_budget_ledger(ledger_path, ledger)
        return summary

    batch_kwargs: dict[str, Any] = {
        "config": config,
        "fixtures_dir": fixtures_dir,
        "outputsize": outputsize,
        "provider": resolved_provider,
        "throttle_seconds": throttle_seconds,
        "max_requests_per_run": request_budget_for_run,
        "skip_if_fresh": skip_if_fresh,
        "freshness_date": freshness_date,
    }
    if executor is not None:
        batch_kwargs["executor"] = executor
    batch_summary = run_market_price_batch_upsert(requested_symbols, **batch_kwargs)

    provider_request_count = int(batch_summary.get("provider_request_count", 0))
    used_after = used_before + provider_request_count
    budget_remaining_after = max(0, daily_budget - used_after)
    day_state["used_request_count"] = used_after
    day_state["daily_budget"] = daily_budget

    summary = {
        "report_name": "market_price_free_backfill_run",
        "status": "completed",
        "provider": resolved_provider,
        "budget_date": budget_day_key,
        "daily_budget": daily_budget,
        "used_request_count_before": used_before,
        "used_request_count_after": used_after,
        "budget_remaining_before": budget_remaining_before,
        "budget_remaining_after": budget_remaining_after,
        "request_budget_for_run": request_budget_for_run,
        "watchlist_path": str(Path(watchlist_path).resolve()),
        "ledger_path": str(Path(ledger_path).resolve()),
        **batch_summary,
    }
    _append_run_record(day_state, summary=summary, started_at=started_at, requested_symbols=requested_symbols)
    write_budget_ledger(ledger_path, ledger)
    return summary


def run_market_price_daily_from_env(
    *,
    config: RuntimeConfig,
    env: Mapping[str, str] | None = None,
    provider: str | None = None,
    budget_date: date | None = None,
    daily_budget: int | None = None,
    max_requests_per_run: int | None = None,
    throttle_seconds: float | None = None,
    outputsize: str | None = None,
    skip_if_fresh: bool = True,
    freshness_date: date | None = None,
    executor: PsqlCommandExecutor | None = None,
    reference_datetime: datetime | None = None,
) -> dict[str, object]:
    env_mapping = env or os.environ
    resolved_provider = resolve_market_price_provider(
        provider or str(env_mapping.get(MARKET_PRICE_PROVIDER_ENV, DEFAULT_PROVIDER))
    )
    watchlist_path = _required_env_value(env_mapping, MARKET_PRICE_WATCHLIST_CSV_ENV)
    ledger_path = _required_env_value(env_mapping, MARKET_PRICE_BUDGET_LEDGER_PATH_ENV)
    resolved_budget_date = budget_date or _optional_env_date(env_mapping, DATA_OPERATIONS_SCHEDULER_RUN_DATE_ENV)
    freshness_resolution = resolve_market_price_freshness_date(
        env=env_mapping,
        explicit_freshness_date=freshness_date,
        reference_datetime=reference_datetime,
    )

    summary = run_market_price_free_backfill(
        config=config,
        watchlist_path=watchlist_path,
        ledger_path=ledger_path,
        provider=resolved_provider,
        budget_date=resolved_budget_date,
        daily_budget=_resolve_env_int(
            env_mapping,
            MARKET_PRICE_DAILY_BUDGET_ENV,
            explicit_value=daily_budget,
            default_value=_DEFAULT_DAILY_BUDGET_BY_PROVIDER[resolved_provider],
        ),
        max_requests_per_run=_resolve_env_int(
            env_mapping,
            MARKET_PRICE_MAX_REQUESTS_PER_RUN_ENV,
            explicit_value=max_requests_per_run,
            default_value=_DEFAULT_MAX_REQUESTS_PER_RUN_BY_PROVIDER[resolved_provider],
        ),
        throttle_seconds=_resolve_env_float(
            env_mapping,
            MARKET_PRICE_THROTTLE_SECONDS_ENV,
            explicit_value=throttle_seconds,
            default_value=_DEFAULT_THROTTLE_SECONDS_BY_PROVIDER[resolved_provider],
        ),
        outputsize=outputsize or str(env_mapping.get(MARKET_PRICE_OUTPUTSIZE_ENV, "")).strip()
        or _DEFAULT_OUTPUTSIZE_BY_PROVIDER[resolved_provider],
        skip_if_fresh=skip_if_fresh,
        freshness_date=freshness_resolution.freshness_date,
        executor=executor,
    )
    summary["freshness_policy"] = freshness_resolution.policy
    summary["freshness_date_source"] = freshness_resolution.source
    summary["freshness_date"] = (
        freshness_resolution.freshness_date.isoformat()
        if freshness_resolution.freshness_date is not None
        else None
    )
    summary["market_timezone"] = freshness_resolution.market_timezone
    summary["market_price_data_ready_local_time"] = freshness_resolution.data_ready_local_time
    summary["market_price_non_trading_dates"] = [
        value.isoformat() for value in freshness_resolution.non_trading_dates
    ]
    return summary


def resolve_market_price_freshness_date(
    *,
    env: Mapping[str, str],
    explicit_freshness_date: date | None = None,
    reference_datetime: datetime | None = None,
) -> MarketPriceFreshnessResolution:
    non_trading_dates = _parse_non_trading_dates(
        str(env.get(MARKET_PRICE_NON_TRADING_DATES_ENV, "")).strip(),
        str(env.get(DATA_OPERATIONS_SCHEDULER_SKIP_DATES_ENV, "")).strip(),
    )
    data_ready_local_time = _env_value_or_default(
        env,
        MARKET_PRICE_DATA_READY_LOCAL_TIME_ENV,
        MARKET_PRICE_DEFAULT_DATA_READY_LOCAL_TIME,
    )
    if explicit_freshness_date is not None:
        return MarketPriceFreshnessResolution(
            freshness_date=explicit_freshness_date,
            policy="explicit",
            source="explicit_argument",
            market_timezone=MARKET_PRICE_TIMEZONE,
            data_ready_local_time=data_ready_local_time,
            non_trading_dates=non_trading_dates,
        )

    env_freshness_date = _optional_env_date(env, MARKET_PRICE_FRESHNESS_DATE_ENV)
    if env_freshness_date is not None:
        return MarketPriceFreshnessResolution(
            freshness_date=env_freshness_date,
            policy="explicit",
            source=MARKET_PRICE_FRESHNESS_DATE_ENV,
            market_timezone=MARKET_PRICE_TIMEZONE,
            data_ready_local_time=data_ready_local_time,
            non_trading_dates=non_trading_dates,
        )

    policy = _env_value_or_default(
        env,
        MARKET_PRICE_FRESHNESS_POLICY_ENV,
        MARKET_PRICE_DEFAULT_FRESHNESS_POLICY,
    )
    scheduler_run_date = _optional_env_date(env, DATA_OPERATIONS_SCHEDULER_RUN_DATE_ENV)
    if policy in {"scheduler_run_date", "run_date"}:
        return MarketPriceFreshnessResolution(
            freshness_date=scheduler_run_date,
            policy=policy,
            source=DATA_OPERATIONS_SCHEDULER_RUN_DATE_ENV if scheduler_run_date else "not_configured",
            market_timezone=MARKET_PRICE_TIMEZONE,
            data_ready_local_time=data_ready_local_time,
            non_trading_dates=non_trading_dates,
        )
    if policy != MARKET_PRICE_DEFAULT_FRESHNESS_POLICY:
        raise ValueError(
            f"Unsupported {MARKET_PRICE_FRESHNESS_POLICY_ENV}: {policy}. "
            f"Expected `{MARKET_PRICE_DEFAULT_FRESHNESS_POLICY}` or `scheduler_run_date`."
        )

    if scheduler_run_date is not None:
        target_date = _latest_trading_day_on_or_before(
            scheduler_run_date,
            non_trading_dates=non_trading_dates,
        )
        return MarketPriceFreshnessResolution(
            freshness_date=target_date,
            policy=policy,
            source=DATA_OPERATIONS_SCHEDULER_RUN_DATE_ENV,
            market_timezone=MARKET_PRICE_TIMEZONE,
            data_ready_local_time=data_ready_local_time,
            non_trading_dates=non_trading_dates,
        )

    target_date = resolve_latest_completed_us_market_day(
        reference_datetime=reference_datetime,
        data_ready_local_time=data_ready_local_time,
        non_trading_dates=non_trading_dates,
    )
    return MarketPriceFreshnessResolution(
        freshness_date=target_date,
        policy=policy,
        source="market_timezone_now",
        market_timezone=MARKET_PRICE_TIMEZONE,
        data_ready_local_time=data_ready_local_time,
        non_trading_dates=non_trading_dates,
    )


def resolve_latest_completed_us_market_day(
    *,
    reference_datetime: datetime | None = None,
    data_ready_local_time: str = MARKET_PRICE_DEFAULT_DATA_READY_LOCAL_TIME,
    non_trading_dates: tuple[date, ...] = (),
) -> date:
    local_now = _market_local_datetime(reference_datetime or _utc_now())
    ready_time = _parse_local_time(data_ready_local_time)
    candidate = local_now.date()
    if local_now.time() < ready_time:
        candidate -= timedelta(days=1)
    return _latest_trading_day_on_or_before(candidate, non_trading_dates=non_trading_dates)


def load_market_price_provider_budget_status(
    *,
    ledger_path: str | Path | None,
    budget_date: date,
    provider: str = DEFAULT_PROVIDER,
) -> dict[str, object]:
    try:
        resolved_provider = resolve_market_price_provider(provider)
    except ValueError:
        return _empty_budget_status(provider=provider, budget_day_key=budget_date.isoformat(), status="invalid_provider")
    budget_day_key = budget_date.isoformat()
    if ledger_path is None or not str(ledger_path).strip():
        return _empty_budget_status(provider=resolved_provider, budget_day_key=budget_day_key, status="not_configured")

    resolved_path = Path(ledger_path).expanduser()
    if not resolved_path.exists():
        return _empty_budget_status(provider=resolved_provider, budget_day_key=budget_day_key, status="ledger_missing")

    try:
        ledger = load_budget_ledger(resolved_path, provider=resolved_provider)
        days = ledger.get("days")
        if not isinstance(days, dict):
            raise ValueError("invalid ledger days")
        day_state = days.get(budget_day_key)
        if not isinstance(day_state, dict):
            return _empty_budget_status(provider=resolved_provider, budget_day_key=budget_day_key, status="day_missing")
        daily_budget = int(day_state.get("daily_budget", 0) or 0)
        used_request_count = int(day_state.get("used_request_count", 0) or 0)
        remaining_request_count = max(0, daily_budget - used_request_count)
        latest_run = _latest_budget_run_summary(day_state.get("runs"))
        return {
            "provider": resolved_provider,
            "status": "configured",
            "budget_date": budget_day_key,
            "daily_budget": daily_budget,
            "used_request_count": used_request_count,
            "remaining_request_count": remaining_request_count,
            "latest_run": latest_run,
            "source": "local_provider_budget_ledger",
        }
    except Exception:
        return _empty_budget_status(provider=resolved_provider, budget_day_key=budget_day_key, status="invalid_ledger")


def load_budget_ledger(path: str | Path, *, provider: str = DEFAULT_PROVIDER) -> dict[str, object]:
    resolved_provider = resolve_market_price_provider(provider)
    ledger_path = Path(path)
    if not ledger_path.exists():
        return {
            "version": LEDGER_VERSION,
            "provider": resolved_provider,
            "days": {},
        }
    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("budget ledger must contain a JSON object.")
    if payload.get("version") != LEDGER_VERSION:
        raise ValueError(f"budget ledger version must be `{LEDGER_VERSION}`.")
    if payload.get("provider") != resolved_provider:
        raise ValueError(f"budget ledger provider must be `{resolved_provider}`.")
    days = payload.get("days")
    if not isinstance(days, dict):
        raise ValueError("budget ledger days must be a JSON object.")
    return payload


def _empty_budget_status(*, provider: str, budget_day_key: str, status: str) -> dict[str, object]:
    return {
        "provider": provider,
        "status": status,
        "budget_date": budget_day_key,
        "daily_budget": 0,
        "used_request_count": 0,
        "remaining_request_count": 0,
        "latest_run": None,
        "source": "local_provider_budget_ledger",
    }


def _required_env_value(env: Mapping[str, str], name: str) -> str:
    value = str(env.get(name, "")).strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}.")
    return value


def _optional_env_date(env: Mapping[str, str], name: str) -> date | None:
    value = str(env.get(name, "")).strip()
    if not value:
        return None
    return date.fromisoformat(value)


def _env_value_or_default(env: Mapping[str, str], name: str, default_value: str) -> str:
    value = str(env.get(name, "")).strip()
    return value if value else default_value


def _parse_non_trading_dates(*values: str) -> tuple[date, ...]:
    parsed: set[date] = set()
    for value in values:
        normalized = value.replace(",", " ")
        for token in normalized.split():
            parsed.add(date.fromisoformat(token))
    return tuple(sorted(parsed))


def _market_local_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(ZoneInfo(MARKET_PRICE_TIMEZONE))


def _parse_local_time(value: str) -> time:
    try:
        hour_value, minute_value = value.split(":", 1)
        return time(hour=int(hour_value), minute=int(minute_value))
    except ValueError as exc:
        raise ValueError(
            f"{MARKET_PRICE_DATA_READY_LOCAL_TIME_ENV} must use HH:MM format."
        ) from exc


def _latest_trading_day_on_or_before(
    candidate: date,
    *,
    non_trading_dates: tuple[date, ...],
) -> date:
    current = candidate
    non_trading = set(non_trading_dates)
    while not _is_trading_day(current, non_trading_dates=non_trading):
        current -= timedelta(days=1)
    return current


def _is_trading_day(candidate: date, *, non_trading_dates: set[date]) -> bool:
    return candidate.weekday() < 5 and candidate not in non_trading_dates


def _resolve_env_int(
    env: Mapping[str, str],
    name: str,
    *,
    explicit_value: int | None,
    default_value: int,
) -> int:
    if explicit_value is not None:
        return explicit_value
    value = str(env.get(name, "")).strip()
    return int(value) if value else default_value


def _resolve_env_float(
    env: Mapping[str, str],
    name: str,
    *,
    explicit_value: float | None,
    default_value: float,
) -> float:
    if explicit_value is not None:
        return explicit_value
    value = str(env.get(name, "")).strip()
    return float(value) if value else default_value


def _latest_budget_run_summary(runs: object) -> dict[str, object] | None:
    if not isinstance(runs, list) or not runs:
        return None
    latest = runs[-1]
    if not isinstance(latest, dict):
        return None
    return {
        "started_at": str(latest.get("started_at") or ""),
        "status": str(latest.get("status") or "unknown"),
        "requested_symbol_count": int(latest.get("requested_symbol_count", 0) or 0),
        "provider_request_count": int(latest.get("provider_request_count", 0) or 0),
        "budget_remaining_after": int(latest.get("budget_remaining_after", 0) or 0),
    }


def write_budget_ledger(path: str | Path, ledger: dict[str, object]) -> None:
    ledger_path = Path(path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = ledger_path.with_name(f".{ledger_path.name}.tmp")
    temp_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp_path, ledger_path)


def _resolve_symbol_field(fieldnames: list[str] | None) -> str:
    if not fieldnames:
        raise ValueError("watchlist must include a symbol column.")
    for fieldname in fieldnames:
        if fieldname and fieldname.strip().lower() == "symbol":
            return fieldname
    raise ValueError("watchlist must include a symbol column.")


def _resolve_day_state(
    ledger: dict[str, object],
    *,
    budget_day_key: str,
    daily_budget: int,
) -> dict[str, object]:
    days = ledger.setdefault("days", {})
    if not isinstance(days, dict):
        raise ValueError("budget ledger days must be a JSON object.")
    raw_day_state = days.setdefault(
        budget_day_key,
        {
            "daily_budget": daily_budget,
            "used_request_count": 0,
            "runs": [],
        },
    )
    if not isinstance(raw_day_state, dict):
        raise ValueError(f"budget ledger day `{budget_day_key}` must be a JSON object.")
    raw_day_state["daily_budget"] = daily_budget
    raw_day_state.setdefault("used_request_count", 0)
    raw_day_state.setdefault("runs", [])
    return raw_day_state


def _append_run_record(
    day_state: dict[str, object],
    *,
    summary: dict[str, object],
    started_at: str,
    requested_symbols: list[str],
) -> None:
    runs = day_state.setdefault("runs", [])
    if not isinstance(runs, list):
        raise ValueError("budget ledger day runs must be a JSON array.")
    runs.append(
        {
            "started_at": started_at,
            "status": summary["status"],
            "requested_symbol_count": summary["requested_symbol_count"],
            "provider_request_count": summary["provider_request_count"],
            "budget_remaining_before": summary["budget_remaining_before"],
            "budget_remaining_after": summary["budget_remaining_after"],
            "requested_symbols": requested_symbols,
        }
    )


def _validate_budget_inputs(
    *,
    daily_budget: int,
    max_requests_per_run: int,
    throttle_seconds: float,
) -> None:
    if daily_budget < 0:
        raise ValueError("daily_budget must be greater than or equal to 0.")
    if max_requests_per_run < 0:
        raise ValueError("max_requests_per_run must be greater than or equal to 0.")
    if throttle_seconds < 0:
        raise ValueError("throttle_seconds must be greater than or equal to 0.")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _format_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
