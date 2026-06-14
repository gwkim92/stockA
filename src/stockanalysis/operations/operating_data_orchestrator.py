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
from stockanalysis.operations.financial_period_source_linkage import DEFAULT_SOURCE_LINKAGE_MAX_FILINGS
from stockanalysis.operations.local_runtime_status import DEFAULT_LOCAL_RUNTIME_ROOT
from stockanalysis.operations.cross_asset_market import cross_asset_instrument_price_symbols
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
DEFAULT_HOLDING_THESIS_VERSION = "holding-bootstrap-v1"
DEFAULT_REVIEW_VERSION = "bootstrap-v1"
DEFAULT_REVIEW_SOURCE = "deterministic_bootstrap"
DEFAULT_MACRO_SERIES = (
    "CPIAUCSL",
    "FEDFUNDS",
    "DGS2",
    "DGS10",
    "DFII10",
    "T10YIE",
    "T10Y2Y",
    "T10Y3M",
    "DTWEXBGS",
    "DCOILWTICO",
    "DCOILBRENTEU",
    "DHHNGSP",
    "NASDAQQSLVO",
    "VIXCLS",
    "BAMLH0A0HYM2",
    "BAMLC0A0CM",
)
DEFAULT_MACRO_OBSERVATION_START = "2025-01-01"
DEFAULT_SEC_FILINGS_CIK = "320193"
DEFAULT_SEC_FILINGS_MAX_FILINGS = 3
DEFAULT_PERIOD_SOURCE_LINKAGE_MAX_FILINGS = DEFAULT_SOURCE_LINKAGE_MAX_FILINGS
DEFAULT_REPORTED_SEGMENT_HISTORY_PERIODS = 4
SEC_FILINGS_CIK_ENV = "STOCKANALYSIS_SEC_FILINGS_CIK"
SEC_FILINGS_MAX_FILINGS_ENV = "STOCKANALYSIS_SEC_FILINGS_MAX_FILINGS"
REPORTED_SEGMENT_HISTORY_PERIODS_ENV = "STOCKANALYSIS_REPORTED_SEGMENT_HISTORY_PERIODS"
OPERATING_DATA_REPORT_ENV = "STOCKANALYSIS_OPERATING_DATA_RUN_REPORT"

ArtifactRunner = Callable[..., dict[str, object]]


@dataclass(frozen=True)
class SourcePosition:
    symbol: str
    quantity: Decimal
    cost_basis: Decimal | None


@dataclass(frozen=True)
class OperatingDataRunProfile:
    profile_id: str
    label: str
    cadence: str
    recommended_schedule: str
    description: str
    step_ids: tuple[str, ...]

    def as_payload(self) -> dict[str, object]:
        return {
            "profile": self.profile_id,
            "label": self.label,
            "cadence": self.cadence,
            "recommended_schedule": self.recommended_schedule,
            "description": self.description,
            "step_ids": list(self.step_ids),
        }


MARKET_UNIVERSE_WEEKLY_STEP_IDS = (
    "market-universe-weekly",
)
SEC_FILINGS_WEEKLY_STEP_IDS = (
    "sec-filings-weekly",
    "sec-companyfacts-weekly",
    "financial-period-source-linkage",
    "professional-coverage-expansion",
    "financial-metric-normalization",
    "peer-relative-analysis",
    "financial-forecast-inputs",
    "reported-segment-footnote-parser",
    "segment-footnote-evidence",
    "sum-of-parts-valuation",
    "valuation-snapshot",
    "industry-competitive-positioning",
)
NEWS_INTRADAY_STEP_IDS = (
    "news-rss-ingest",
    "news-missing-instrument-bootstrap",
    "news-rss-enrichment",
    "news-korean-translation",
    "news-cluster-evidence",
    "news-ai-evidence",
    "cycle-ai-duplicate-title-cleanup",
    "news-ai-eval",
    "macro-event-propagation",
    "hierarchical-impact-propagation",
)
MARKET_DAILY_STEP_IDS = (
    "market-price-daily",
)
CROSS_ASSET_DAILY_STEP_IDS = (
    "free-provider-capacity-registry",
    "cross-asset-market-price-refresh",
    "cross-asset-indicator-provider-fetch",
    "cross-asset-indicator-ingest",
    "cross-asset-regime-snapshot",
    "indicator-news-linkage",
    "asset-correlation-analysis",
    "recommendation-cross-asset-components",
)
DECISION_DAILY_STEP_IDS = (
    "missing-symbol-price-backfill",
    "strategy-universe-slice",
    "market-feature-snapshot",
    "instrument-theme-enrichment",
    "cycle-state-snapshot",
    "cycle-hierarchy-snapshot-v2",
    "cycle-graph-context-summary",
    "cycle-community-ai-summary-v2",
    "recommendation-bootstrap",
    "recommendation-fundamental-components",
    "thesis-bootstrap",
    "thesis-review-bootstrap",
    "equity-research-reporting",
    "portfolio-position-snapshot",
    "portfolio-holding-thesis-bootstrap",
    "portfolio-remediation-daily",
    "paper-safety-bootstrap",
    "paper-validation-audit",
    "recommendation-outcome-backfill",
    "recommendation-outcome-due-action-router",
    "recommendation-quality-eval",
    "portfolio-review-feedback-cadence",
    "portfolio-review-feedback-action-router",
)
MACRO_WEEKLY_STEP_IDS = (
    "macro-weekly",
)
PERFORMANCE_MONTHLY_STEP_IDS = (
    "performance-outcome-monthly",
    "portfolio-attribution-monthly",
)
FULL_RECOVERY_STEP_IDS = (
    *MARKET_UNIVERSE_WEEKLY_STEP_IDS,
    *SEC_FILINGS_WEEKLY_STEP_IDS,
    *NEWS_INTRADAY_STEP_IDS,
    *MARKET_DAILY_STEP_IDS,
    *CROSS_ASSET_DAILY_STEP_IDS,
    *DECISION_DAILY_STEP_IDS,
    *MACRO_WEEKLY_STEP_IDS,
    *PERFORMANCE_MONTHLY_STEP_IDS,
)
SOURCE_POSITION_STEP_IDS = {
    "missing-symbol-price-backfill",
    "portfolio-position-snapshot",
}
OPERATING_DATA_RUN_PROFILES: tuple[OperatingDataRunProfile, ...] = (
    OperatingDataRunProfile(
        profile_id="market-universe-weekly",
        label="Weekly listed stock universe refresh",
        cadence="weekly",
        recommended_schedule="07:00 America/New_York every Monday",
        description="Refresh the active Nasdaq/NYSE instrument universe used by candles, signals, and stock pages.",
        step_ids=MARKET_UNIVERSE_WEEKLY_STEP_IDS,
    ),
    OperatingDataRunProfile(
        profile_id="sec-filings-weekly",
        label="Weekly SEC filing metadata refresh",
        cadence="weekly",
        recommended_schedule="08:00 America/New_York every Monday",
        description="Refresh SEC filing metadata for the configured core filer without touching news, candles, or portfolio rows.",
        step_ids=SEC_FILINGS_WEEKLY_STEP_IDS,
    ),
    OperatingDataRunProfile(
        profile_id="news-intraday",
        label="News and AI event intelligence",
        cadence="intraday",
        recommended_schedule="every 30-60 minutes during US market/news hours",
        description="Collect free RSS news, enrich pending events, refresh local news cluster evidence, and run validator-gated Codex OAuth news AI evidence without touching market candles or portfolio rows.",
        step_ids=NEWS_INTRADAY_STEP_IDS,
    ),
    OperatingDataRunProfile(
        profile_id="market-daily",
        label="Daily market candle refresh",
        cadence="daily",
        recommended_schedule="18:35 America/New_York on US trading days",
        description="Refresh configured market price watchlist with free-provider budget controls.",
        step_ids=MARKET_DAILY_STEP_IDS,
    ),
    OperatingDataRunProfile(
        profile_id="cross-asset-daily",
        label="Daily cross-asset regime refresh",
        cadence="daily",
        recommended_schedule="18:50 America/New_York after market-daily succeeds",
        description="Sync free macro and price indicators, classify cross-asset regimes, link news to indicator shocks, and attach zero-weight recommendation evidence components.",
        step_ids=CROSS_ASSET_DAILY_STEP_IDS,
    ),
    OperatingDataRunProfile(
        profile_id="decision-daily",
        label="Daily signal, recommendation, and holding review",
        cadence="daily",
        recommended_schedule="19:00 America/New_York after market-daily succeeds",
        description="Backfill missing decision inputs, refresh cycle/recommendation/thesis rows, update portfolio snapshot, and write paper validation audit.",
        step_ids=DECISION_DAILY_STEP_IDS,
    ),
    OperatingDataRunProfile(
        profile_id="macro-weekly",
        label="Weekly macro context",
        cadence="weekly",
        recommended_schedule="07:30 America/New_York every Monday",
        description="Refresh free macro context that changes slower than news and candles.",
        step_ids=MACRO_WEEKLY_STEP_IDS,
    ),
    OperatingDataRunProfile(
        profile_id="performance-monthly",
        label="Monthly performance outcome readiness",
        cadence="monthly",
        recommended_schedule="09:15 America/New_York on the first business day",
        description="Create due thesis outcome rows when recommendation horizons have matured.",
        step_ids=PERFORMANCE_MONTHLY_STEP_IDS,
    ),
    OperatingDataRunProfile(
        profile_id="full-recovery",
        label="Full recovery and deployment smoke",
        cadence="ad_hoc",
        recommended_schedule="manual only after deployment, incident recovery, or explicit backfill",
        description="Run every operating-data step in dependency order to prove or restore end-to-end data health.",
        step_ids=FULL_RECOVERY_STEP_IDS,
    ),
)
OPERATING_DATA_RUN_PROFILE_IDS = tuple(profile.profile_id for profile in OPERATING_DATA_RUN_PROFILES)


def build_operating_data_run_report(
    *,
    repo_root: str | Path | None = None,
    runtime_root: str | Path = DEFAULT_LOCAL_RUNTIME_ROOT,
    data_operations_env_file: str | Path,
    artifact_root: str | Path | None = None,
    profile: str = "full-recovery",
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
    selected_profile = _resolve_profile(profile)
    data_env_path = resolve_existing_file(
        data_operations_env_file,
        label="data operations env file",
        repo_root=repo_root,
        require_repo_outside=True,
    )
    env_mapping = merged_env_with_file(data_env_path)
    runtime_path = _resolve_runtime_root(runtime_root, repo_root=repo_root)
    artifact_root_path = _resolve_artifact_root(artifact_root, env=env_mapping, repo_root=repo_root)
    source_positions_required = _profile_requires_source_positions(selected_profile)
    source_positions_path = (
        _resolve_source_positions_path(env_mapping, repo_root=repo_root)
        if source_positions_required
        else None
    )
    source_positions = _load_source_positions(source_positions_path) if source_positions_path is not None else []
    resolved_python = str(python_executable or sys.executable)
    resolved_provider = provider or str(env_mapping.get(MARKET_PRICE_PROVIDER_ENV, "alpha_vantage")).strip() or "alpha_vantage"
    ledger_path = _resolve_market_price_ledger(env_mapping, runtime_path=runtime_path, repo_root=repo_root)
    sec_filings_cik = _resolve_sec_filings_cik(env_mapping)
    sec_filings_max_filings = _resolve_sec_filings_max_filings(env_mapping)
    reported_segment_history_periods = _resolve_reported_segment_history_periods(env_mapping)

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
    cross_asset_watchlist_path = generated_dir / f"cross-asset-price-watchlist-{target_date.isoformat()}.csv"
    positions_snapshot_path = generated_dir / f"position-snapshot-{target_date.isoformat()}.csv"
    missing_watchlist_required = "missing-symbol-price-backfill" in selected_profile.step_ids
    cross_asset_watchlist_required = "cross-asset-market-price-refresh" in selected_profile.step_ids
    cross_asset_symbols = cross_asset_instrument_price_symbols()
    position_snapshot_required = "portfolio-position-snapshot" in selected_profile.step_ids

    planned_steps = _build_planned_steps(
        python_executable=resolved_python,
        env_file=data_env_path,
        watchlist_path=watchlist_path,
        cross_asset_watchlist_path=cross_asset_watchlist_path,
        positions_snapshot_path=positions_snapshot_path,
        ledger_path=ledger_path,
        missing_price_symbols=missing_price_symbols,
        cross_asset_symbols=cross_asset_symbols,
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
        sec_filings_cik=sec_filings_cik,
        sec_filings_max_filings=sec_filings_max_filings,
        reported_segment_history_periods=reported_segment_history_periods,
        profile=selected_profile,
    )

    report: dict[str, object] = {
        "report_name": "operating_data_run",
        "profile": selected_profile.profile_id,
        "profile_label": selected_profile.label,
        "profile_cadence": selected_profile.cadence,
        "profile_recommended_schedule": selected_profile.recommended_schedule,
        "profile_description": selected_profile.description,
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
            "source_positions_required": source_positions_required,
            "source_position_count": len(source_positions),
            "source_symbols": [position.symbol for position in source_positions],
            "event_impacted_symbols": _symbol_list(context.get("event_impacted_symbols")),
            "missing_price_symbols": missing_price_symbols,
            "cross_asset_price_symbols": list(cross_asset_symbols),
            "sec_filings_cik": sec_filings_cik,
            "sec_filings_max_filings": sec_filings_max_filings,
            "reported_segment_history_periods": reported_segment_history_periods,
        },
        "generated_files": {
            "missing_price_watchlist": str(watchlist_path) if missing_watchlist_required and missing_price_symbols else "",
            "cross_asset_price_watchlist": str(cross_asset_watchlist_path) if cross_asset_watchlist_required else "",
            "position_snapshot_csv": str(positions_snapshot_path) if position_snapshot_required else "",
        },
        "planned_steps": [_public_step(step) for step in planned_steps],
        "profile_catalog": [profile_item.as_payload() for profile_item in _profile_payloads()],
        "artifact_runs": [],
        "failed_step_count": 0,
        "next_actions": ["review planned_steps, then rerun with --execute if DB/provider writes are intended"],
    }
    if not execute:
        _assert_secret_free_payload(report)
        return report

    if missing_watchlist_required:
        _write_missing_price_watchlist(watchlist_path, missing_price_symbols)
    if cross_asset_watchlist_required:
        _write_missing_price_watchlist(cross_asset_watchlist_path, cross_asset_symbols)
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
        "profile": "",
        "profile_cadence": "",
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
        "profile": str(payload.get("profile") or ""),
        "profile_cadence": str(payload.get("profile_cadence") or ""),
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
    cross_asset_watchlist_path: Path,
    positions_snapshot_path: Path,
    ledger_path: Path,
    missing_price_symbols: Sequence[str],
    cross_asset_symbols: Sequence[str],
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
    sec_filings_cik: str,
    sec_filings_max_filings: int,
    reported_segment_history_periods: int,
    profile: OperatingDataRunProfile,
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
            "step_id": "market-universe-weekly",
            "artifact_job_id": "market-universe-weekly",
            "label": "Refresh active Nasdaq/NYSE instrument universe",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.ingest.cli",
                "market-universe-bootstrap",
                "--exchange",
                "Nasdaq",
                "--exchange",
                "NYSE",
            ),
        },
        {
            "step_id": "sec-filings-weekly",
            "artifact_job_id": "sec-filings-weekly",
            "label": "Refresh configured SEC filing metadata",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.ingest.cli",
                "sec-filings-upsert",
                "--cik",
                sec_filings_cik,
                "--max-filings",
                str(sec_filings_max_filings),
            ),
        },
        {
            "step_id": "sec-companyfacts-weekly",
            "artifact_job_id": "sec-companyfacts-weekly",
            "label": "Refresh SEC companyfacts for the configured core filer",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.ingest.cli",
                "sec-companyfacts-upsert",
                "--cik",
                sec_filings_cik,
            ),
        },
        {
            "step_id": "financial-period-source-linkage",
            "artifact_job_id": "financial-period-source-linkage-weekly",
            "label": "Link SEC source documents and raw filings to financial statement periods",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "financial-period-source-linkage-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--statement-scope",
                "annual",
                "--cik",
                sec_filings_cik,
                "--max-filings",
                str(max(sec_filings_max_filings, DEFAULT_PERIOD_SOURCE_LINKAGE_MAX_FILINGS)),
                "--raw-fetch-limit",
                str(reported_segment_history_periods),
                "--execute",
            ),
        },
        {
            "step_id": "professional-coverage-expansion",
            "artifact_job_id": "professional-coverage-expansion-weekly",
            "label": "Expand SEC-backed professional analysis coverage for active recommendations",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "professional-coverage-expansion-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--limit",
                "25",
                "--companyfacts-limit",
                "5",
                "--research-limit",
                "5",
                "--research-provider",
                "fixture",
                "--execute",
            ),
        },
        {
            "step_id": "financial-metric-normalization",
            "artifact_job_id": "financial-metric-normalization-weekly",
            "label": "Normalize SEC companyfacts into professional financial metrics",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "financial-metric-normalization-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--execute",
            ),
        },
        {
            "step_id": "peer-relative-analysis",
            "artifact_job_id": "peer-relative-analysis-weekly",
            "label": "Build peer groups and relative financial metric snapshots",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "peer-relative-analysis-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--statement-scope",
                "annual",
                "--execute",
            ),
        },
        {
            "step_id": "valuation-snapshot",
            "artifact_job_id": "valuation-snapshot-weekly",
            "label": "Create conservative valuation snapshots without changing recommendation weights",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "valuation-snapshot-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--statement-scope",
                "annual",
                "--execute",
            ),
        },
        {
            "step_id": "financial-forecast-inputs",
            "artifact_job_id": "financial-forecast-inputs-weekly",
            "label": "Create explicit financial forecast inputs for valuation evidence",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "financial-forecast-inputs-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--statement-scope",
                "annual",
                "--execute",
            ),
        },
        {
            "step_id": "reported-segment-footnote-parser",
            "artifact_job_id": "reported-segment-footnote-parser-weekly",
            "label": "Parse reported segment metrics from SEC filing artifacts",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "reported-segment-footnote-parser-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--statement-scope",
                "annual",
                "--periods-per-instrument",
                str(reported_segment_history_periods),
                "--execute",
            ),
        },
        {
            "step_id": "sum-of-parts-valuation",
            "artifact_job_id": "sum-of-parts-valuation-weekly",
            "label": "Create conservative SOTP valuation components without changing recommendation weights",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "sum-of-parts-valuation-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--statement-scope",
                "annual",
                "--execute",
            ),
        },
        {
            "step_id": "segment-footnote-evidence",
            "artifact_job_id": "segment-footnote-evidence-weekly",
            "label": "Create SEC segment and footnote evidence for SOTP without changing recommendation weights",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "segment-footnote-evidence-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--statement-scope",
                "annual",
                "--execute",
            ),
        },
        {
            "step_id": "industry-competitive-positioning",
            "artifact_job_id": "industry-competitive-positioning-weekly",
            "label": "Create deterministic industry competitive positioning snapshots",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "industry-competitive-positioning-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--execute",
            ),
        },
        {
            "step_id": "news-rss-ingest",
            "artifact_job_id": "news-rss-daily",
            "label": "Collect configured free RSS/Atom news feeds",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "news-rss-daily-run",
                "--env-file",
                str(env_file),
            ),
        },
        {
            "step_id": "news-missing-instrument-bootstrap",
            "artifact_job_id": "news-missing-instrument-bootstrap-intraday",
            "label": "Bootstrap SEC-verified instruments for explicit missing news tickers",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "news-missing-instrument-bootstrap-run",
                "--env-file",
                str(env_file),
            ),
        },
        {
            "step_id": "news-rss-enrichment",
            "artifact_job_id": "news-rss-enrichment-intraday",
            "label": "Enrich pending RSS news into structured events",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "news-rss-enrich-run",
                "--env-file",
                str(env_file),
            ),
        },
        {
            "step_id": "news-korean-translation",
            "artifact_job_id": "news-korean-translation-intraday",
            "label": "Translate RSS news titles and summaries into Korean AI review text",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "news-rss-translation-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--provider",
                "codex_oauth",
                "--limit",
                "20",
                "--execute",
            ),
        },
        {
            "step_id": "news-cluster-evidence",
            "artifact_job_id": "event-intelligence-weekly",
            "label": "Refresh local news cluster evidence for AI analysis visibility",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "news-rss-cluster-evidence-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
            ),
        },
        {
            "step_id": "news-ai-evidence",
            "artifact_job_id": "event-intelligence-weekly",
            "label": "Extract Codex OAuth news AI evidence through validator-gated canonical impacts",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "news-rss-ai-extract-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--provider",
                "codex_oauth",
                "--limit",
                "10",
                "--execute",
            ),
        },
        {
            "step_id": "cycle-ai-duplicate-title-cleanup",
            "artifact_job_id": "event-intelligence-weekly",
            "label": "Merge safe syndicated duplicate news events before impact propagation",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "cycle-ai-duplicate-title-cleanup-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--lookback-days",
                "3",
                "--execute",
            ),
        },
        {
            "step_id": "news-ai-eval",
            "artifact_job_id": "news-ai-eval-intraday",
            "label": "Score fixture/gold news AI extraction quality before impact propagation",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "news-ai-eval-run",
                "--env-file",
                str(env_file),
                "--provider",
                "fixture",
                "--execute",
            ),
        },
        {
            "step_id": "macro-event-propagation",
            "artifact_job_id": "event-intelligence-weekly",
            "label": "Propagate market/theme news flows to exposed instruments",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "macro-event-propagation-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--limit",
                "200",
                "--execute",
            ),
        },
        {
            "step_id": "hierarchical-impact-propagation",
            "artifact_job_id": "event-intelligence-weekly",
            "label": "Propagate market/theme news flows through hierarchy paths to exposed instruments",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "hierarchical-impact-propagation-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--limit",
                "200",
                "--max-depth",
                "3",
                "--execute",
            ),
        },
        {
            "step_id": "market-price-daily",
            "artifact_job_id": "market-price-daily",
            "label": "Refresh configured market candle watchlist with provider budget limits",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "market-price-daily-run",
                "--env-file",
                str(env_file),
                "--provider",
                provider,
                "--daily-budget",
                str(daily_budget),
                "--max-requests-per-run",
                str(max_requests_per_run),
                "--throttle-seconds",
                str(throttle_seconds),
                "--outputsize",
                outputsize,
                "--skip-if-fresh",
            ),
        },
        {
            "step_id": "free-provider-capacity-registry",
            "artifact_job_id": "cross-asset-indicator-ingest-daily",
            "label": "Register free provider capacity and cross-asset indicator metadata",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "free-provider-capacity-registry-run",
                "--env-file",
                str(env_file),
                "--execute",
            ),
        },
        {
            "step_id": "cross-asset-market-price-refresh",
            "artifact_job_id": "cross-asset-market-price-refresh-daily",
            "label": "Refresh cross-asset ETF and rates/credit ETF price bars before indicator sync",
            "skip_reason": "" if cross_asset_symbols else "no_cross_asset_instrument_symbols",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "market-price-free-backfill-run",
                "--watchlist",
                str(cross_asset_watchlist_path),
                "--ledger",
                str(ledger_path),
                "--provider",
                provider,
                "--env-file",
                str(env_file),
                "--daily-budget",
                str(max(daily_budget, 80)),
                "--max-requests-per-run",
                str(max(max_requests_per_run, 24)),
                "--throttle-seconds",
                str(max(throttle_seconds, 8.0)),
                "--outputsize",
                "120",
                "--skip-if-fresh",
                "--allow-symbol-failures",
            ),
        },
        {
            "step_id": "cross-asset-indicator-ingest",
            "artifact_job_id": "cross-asset-indicator-ingest-daily",
            "label": "Sync FRED macro and price bars into cross-asset indicator observations",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "cross-asset-indicator-ingest-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--execute",
            ),
        },
        {
            "step_id": "cross-asset-indicator-provider-fetch",
            "artifact_job_id": "cross-asset-provider-fetch-daily",
            "label": "Fetch direct CBOE CSV and Twelve Data indicators that are not instrument price bars",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "cross-asset-indicator-provider-fetch-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--outputsize",
                "120",
                "--max-requests-per-run",
                "8",
                "--throttle-seconds",
                "8",
                "--allow-indicator-failures",
                "--execute",
            ),
        },
        {
            "step_id": "cross-asset-regime-snapshot",
            "artifact_job_id": "cross-asset-regime-daily",
            "label": "Compute cross-asset indicator snapshots and regime states",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "cross-asset-regime-snapshot-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--execute",
            ),
        },
        {
            "step_id": "indicator-news-linkage",
            "artifact_job_id": "indicator-news-linkage-daily",
            "label": "Link classified news to indicator shocks as non-causal evidence candidates",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "indicator-news-linkage-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--lookback-days",
                "2",
                "--execute",
            ),
        },
        {
            "step_id": "asset-correlation-analysis",
            "artifact_job_id": "asset-correlation-daily",
            "label": "Compute rolling co-movement correlations without causal claims",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "correlation-analysis-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--execute",
            ),
        },
        {
            "step_id": "recommendation-cross-asset-components",
            "artifact_job_id": "recommendation-cross-asset-components-daily",
            "label": "Attach zero-weight cross-asset components to current recommendations",
            "skip_reason": "",
            "command_argv": (
                python_executable,
                "-m",
                "stockanalysis.operations.cli",
                "recommendation-cross-asset-components-run",
                "--env-file",
                str(env_file),
                "--as-of-date",
                target,
                "--execute",
            ),
        },
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
                "--allow-symbol-failures",
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
            {
                "step_id": "cycle-hierarchy-snapshot-v2",
                "artifact_job_id": "cycle-recommendation-weekly",
                "label": "Refresh hierarchical macro/domain/theme cycle state",
                "skip_reason": "",
                "command_argv": (
                    python_executable,
                    "-m",
                    "stockanalysis.operations.cli",
                    "cycle-hierarchy-snapshot-v2-run",
                    "--env-file",
                    str(env_file),
                    "--as-of-date",
                    target,
                    "--execute",
                ),
            },
            {
                "step_id": "cycle-graph-context-summary",
                "artifact_job_id": "cycle-recommendation-weekly",
                "label": "Refresh reusable cycle graph context summaries",
                "skip_reason": "",
                "command_argv": (
                    python_executable,
                    "-m",
                    "stockanalysis.operations.cli",
                    "cycle-graph-context-summary-run",
                    "--env-file",
                    str(env_file),
                    "--as-of-date",
                    target,
                    "--execute",
                ),
            },
            {
                "step_id": "cycle-community-ai-summary-v2",
                "artifact_job_id": "cycle-community-ai-summary-daily",
                "label": "Refresh Korean AI summaries for cycle graph communities",
                "skip_reason": "",
                "command_argv": (
                    python_executable,
                    "-m",
                    "stockanalysis.operations.cli",
                    "cycle-community-ai-summary-v2-run",
                    "--env-file",
                    str(env_file),
                    "--as-of-date",
                    target,
                    "--provider",
                    "codex_oauth",
                    "--max-nodes",
                    "12",
                    "--execute",
                ),
            },
            _ingest_step(
                "recommendation-bootstrap",
                "cycle-recommendation-weekly",
                "Refresh deterministic recommendations",
                python_executable,
                "recommendation-bootstrap",
                (*signal_args, "--score-version", DEFAULT_SCORE_VERSION),
            ),
            {
                "step_id": "recommendation-fundamental-components",
                "artifact_job_id": "recommendation-fundamental-components-daily",
                "label": "Attach zero-weight fundamental components to active recommendations",
                "skip_reason": "",
                "command_argv": (
                    python_executable,
                    "-m",
                    "stockanalysis.operations.cli",
                    "recommendation-fundamental-components-run",
                    "--env-file",
                    str(env_file),
                    "--as-of-date",
                    target,
                    "--market-code",
                    market_code,
                    "--strategy-name",
                    strategy_name,
                    "--horizon-type",
                    horizon_type,
                    "--execute",
                ),
            },
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
                "step_id": "equity-research-reporting",
                "artifact_job_id": "equity-research-reporting-daily",
                "label": "Generate Korean equity research artifacts from financial, valuation, cycle, and thesis context",
                "skip_reason": "",
                "command_argv": (
                    python_executable,
                    "-m",
                    "stockanalysis.operations.cli",
                    "equity-research-reporting-run",
                    "--env-file",
                    str(env_file),
                    "--as-of-date",
                    target,
                    "--provider",
                    "codex_oauth",
                    "--limit",
                    "5",
                    "--execute",
                ),
            },
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
                "portfolio-holding-thesis-bootstrap",
                "portfolio-remediation-daily",
                "Create conservative thesis coverage for held positions",
                python_executable,
                "portfolio-holding-thesis-bootstrap",
                (
                    "--portfolio-name",
                    portfolio_name,
                    "--as-of-date",
                    target,
                    "--strategy-name",
                    strategy_name,
                    "--horizon-type",
                    horizon_type,
                    "--market-code",
                    market_code,
                    "--thesis-version",
                    DEFAULT_HOLDING_THESIS_VERSION,
                ),
            ),
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
            {
                "step_id": "performance-outcome-monthly",
                "artifact_job_id": "performance-outcome-monthly",
                "label": "Run due performance outcome schedule",
                "skip_reason": "",
                "command_argv": (
                    python_executable,
                    "-m",
                    "stockanalysis.operations.cli",
                    "recommendation-outcome-backfill-run",
                    "--env-file",
                    str(env_file),
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
                    "--execute",
                ),
            },
            {
                "step_id": "portfolio-attribution-monthly",
                "artifact_job_id": "portfolio-attribution-monthly",
                "label": "Run portfolio attribution for the latest eligible outcome window",
                "skip_reason": "",
                "command_argv": (
                    python_executable,
                    "-m",
                    "stockanalysis.operations.cli",
                    "portfolio-attribution-run",
                    "--env-file",
                    str(env_file),
                    "--portfolio-name",
                    portfolio_name,
                    "--as-of-date",
                    target,
                    "--execute",
                ),
            },
            {
                "step_id": "recommendation-outcome-backfill",
                "artifact_job_id": "recommendation-outcome-backfill-daily",
                "label": "Backfill due recommendation outcomes before quality evaluation",
                "skip_reason": "",
                "command_argv": (
                    python_executable,
                    "-m",
                    "stockanalysis.operations.cli",
                    "recommendation-outcome-backfill-run",
                    "--env-file",
                    str(env_file),
                    "--due-on-date",
                    target,
                    "--horizon-day",
                    "30",
                    "--strategy-name",
                    strategy_name,
                    "--horizon-type",
                    horizon_type,
                    "--universe-version",
                    universe_version,
                    "--market-code",
                    market_code,
                    "--execute",
                ),
            },
            {
                "step_id": "recommendation-outcome-due-action-router",
                "artifact_job_id": "recommendation-outcome-due-action-router-daily",
                "label": "Route due recommendation outcomes to safe calibration without changing weights",
                "skip_reason": "",
                "command_argv": (
                    python_executable,
                    "-m",
                    "stockanalysis.operations.cli",
                    "recommendation-outcome-due-action-router-run",
                    "--env-file",
                    str(env_file),
                    "--as-of-date",
                    target,
                    "--horizon-day",
                    "30",
                    "--strategy-name",
                    strategy_name,
                    "--horizon-type",
                    horizon_type,
                    "--universe-version",
                    universe_version,
                    "--market-code",
                    market_code,
                    "--execute",
                ),
            },
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
            {
                "step_id": "recommendation-quality-eval",
                "artifact_job_id": "recommendation-quality-eval-daily",
                "label": "Evaluate recommendation component quality without changing score weights",
                "skip_reason": "",
                "command_argv": (
                    python_executable,
                    "-m",
                    "stockanalysis.operations.cli",
                    "recommendation-quality-eval-run",
                    "--env-file",
                    str(env_file),
                    "--as-of-date",
                    target,
                    "--horizon",
                    "30d",
                    "--execute",
                ),
            },
            {
                "step_id": "portfolio-review-feedback-cadence",
                "artifact_job_id": "portfolio-review-feedback-cadence-daily",
                "label": "Decide whether portfolio review feedback or calibration should rerun",
                "skip_reason": "",
                "command_argv": (
                    python_executable,
                    "-m",
                    "stockanalysis.operations.cli",
                    "portfolio-review-feedback-cadence-run",
                    "--env-file",
                    str(env_file),
                    "--portfolio-name",
                    portfolio_name,
                    "--as-of-date",
                    target,
                    "--execute",
                ),
            },
            {
                "step_id": "portfolio-review-feedback-action-router",
                "artifact_job_id": "portfolio-review-feedback-action-router-daily",
                "label": "Run the safe portfolio review feedback or calibration action selected by cadence",
                "skip_reason": "",
                "command_argv": (
                    python_executable,
                    "-m",
                    "stockanalysis.operations.cli",
                    "portfolio-review-feedback-action-router-run",
                    "--env-file",
                    str(env_file),
                    "--portfolio-name",
                    portfolio_name,
                    "--as-of-date",
                    target,
                    "--execute",
                ),
            },
        ]
    )
    return _select_profile_steps(steps, profile=profile)


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


def _resolve_profile(profile_id: str) -> OperatingDataRunProfile:
    normalized = str(profile_id or "").strip()
    for profile in OPERATING_DATA_RUN_PROFILES:
        if profile.profile_id == normalized:
            return profile
    raise ValueError(f"Unsupported operating data run profile: {profile_id!r}.")


def _profile_payloads() -> tuple[OperatingDataRunProfile, ...]:
    return OPERATING_DATA_RUN_PROFILES


def _profile_requires_source_positions(profile: OperatingDataRunProfile) -> bool:
    return bool(SOURCE_POSITION_STEP_IDS.intersection(profile.step_ids))


def _resolve_sec_filings_cik(env: Mapping[str, str]) -> str:
    value = str(env.get(SEC_FILINGS_CIK_ENV, DEFAULT_SEC_FILINGS_CIK)).strip()
    if not value:
        raise ValueError(f"{SEC_FILINGS_CIK_ENV} must not be empty.")
    digits = "".join(char for char in value if char.isdigit())
    if not digits:
        raise ValueError(f"{SEC_FILINGS_CIK_ENV} must contain a numeric CIK.")
    return digits


def _resolve_sec_filings_max_filings(env: Mapping[str, str]) -> int:
    value = str(env.get(SEC_FILINGS_MAX_FILINGS_ENV, str(DEFAULT_SEC_FILINGS_MAX_FILINGS))).strip()
    try:
        parsed = int(value)
    except ValueError:
        raise ValueError(f"{SEC_FILINGS_MAX_FILINGS_ENV} must be an integer.")
    if parsed <= 0:
        raise ValueError(f"{SEC_FILINGS_MAX_FILINGS_ENV} must be positive.")
    return parsed


def _resolve_reported_segment_history_periods(env: Mapping[str, str]) -> int:
    value = str(env.get(REPORTED_SEGMENT_HISTORY_PERIODS_ENV, str(DEFAULT_REPORTED_SEGMENT_HISTORY_PERIODS))).strip()
    try:
        parsed = int(value)
    except ValueError:
        raise ValueError(f"{REPORTED_SEGMENT_HISTORY_PERIODS_ENV} must be an integer.")
    if parsed <= 0:
        raise ValueError(f"{REPORTED_SEGMENT_HISTORY_PERIODS_ENV} must be positive.")
    return parsed


def _select_profile_steps(
    steps: Sequence[dict[str, object]],
    *,
    profile: OperatingDataRunProfile,
) -> list[dict[str, object]]:
    steps_by_id = {str(step["step_id"]): step for step in steps}
    missing_step_ids = [step_id for step_id in profile.step_ids if step_id not in steps_by_id]
    if missing_step_ids:
        raise ValueError(f"Profile {profile.profile_id!r} references unknown steps: {', '.join(missing_step_ids)}")
    return [steps_by_id[step_id] for step_id in profile.step_ids]


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
    candidate_dates: list[date] = []
    latest_event_date = str(context.get("latest_event_date") or "").strip()
    if latest_event_date:
        candidate_dates.append(date.fromisoformat(latest_event_date))
    latest_price_date = str(context.get("latest_price_date") or "").strip()
    if latest_price_date:
        candidate_dates.append(date.fromisoformat(latest_price_date))
    if candidate_dates:
        return max(candidate_dates)
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
