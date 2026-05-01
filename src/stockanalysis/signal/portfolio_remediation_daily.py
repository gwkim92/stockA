from __future__ import annotations

from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.portfolio_remediation_ticket import (
    load_portfolio_remediation_ticket_report,
    run_portfolio_remediation_ticket_bootstrap,
)
from stockanalysis.signal.portfolio_review import run_portfolio_review_bootstrap
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)

_DEFAULT_MARKET_CODE = "US"
_DEFAULT_REVIEW_VERSION = "bootstrap-v1"
_DEFAULT_REVIEW_SOURCE = "deterministic_bootstrap"
_DEFAULT_TICKET_STATUS = "open"


def run_portfolio_remediation_daily_automation(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    as_of_date: date,
    strategy_name: str,
    horizon_type: str,
    universe_version: str,
    market_code: str = _DEFAULT_MARKET_CODE,
    review_version: str = _DEFAULT_REVIEW_VERSION,
    review_source: str = _DEFAULT_REVIEW_SOURCE,
    coverage_measurement_end_date: date | None = None,
    ticket_limit: int = 20,
    ticket_status: str | None = _DEFAULT_TICKET_STATUS,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    if ticket_limit <= 0:
        raise ValueError("ticket_limit must be greater than 0")

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="portfolio_remediation_daily_automation",
        config_json={
            "portfolio_name": portfolio_name,
            "as_of_date": as_of_date.isoformat(),
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "universe_version": universe_version,
            "market_code": market_code,
            "review_version": review_version,
            "review_source": review_source,
            "coverage_measurement_end_date": coverage_measurement_end_date.isoformat()
            if coverage_measurement_end_date
            else None,
            "ticket_limit": ticket_limit,
            "ticket_status": ticket_status,
        },
    )

    try:
        review_summary = run_portfolio_review_bootstrap(
            config=config,
            portfolio_name=portfolio_name,
            as_of_date=as_of_date,
            strategy_name=strategy_name,
            horizon_type=horizon_type,
            universe_version=universe_version,
            market_code=market_code,
            review_version=review_version,
            review_source=review_source,
            coverage_measurement_end_date=coverage_measurement_end_date,
            executor=sql_executor,
        )
        ticket_bootstrap_summary = run_portfolio_remediation_ticket_bootstrap(
            config=config,
            portfolio_name=portfolio_name,
            limit=ticket_limit,
            review_source=review_source,
            executor=sql_executor,
        )
        ticket_report = load_portfolio_remediation_ticket_report(
            config=config,
            portfolio_name=portfolio_name,
            limit=ticket_limit,
            status=ticket_status,
            executor=sql_executor,
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return {
        "report_name": "portfolio_remediation_daily_automation",
        "run_id": run_id,
        "portfolio_name": portfolio_name,
        "as_of_date": as_of_date.isoformat(),
        "strategy_name": strategy_name,
        "horizon_type": horizon_type,
        "universe_version": universe_version,
        "market_code": market_code,
        "review_version": review_version,
        "review_source": review_source,
        "coverage_measurement_end_date": coverage_measurement_end_date.isoformat()
        if coverage_measurement_end_date
        else None,
        "ticket_limit": ticket_limit,
        "ticket_status_filter": ticket_status,
        "steps": [
            _step_summary("portfolio_review_bootstrap", review_summary),
            _step_summary("portfolio_remediation_ticket_bootstrap", ticket_bootstrap_summary),
            _step_summary("portfolio_remediation_ticket_report", ticket_report),
        ],
        "review": review_summary,
        "ticket_bootstrap": ticket_bootstrap_summary,
        "ticket_report": ticket_report,
    }


def _step_summary(step_name: str, payload: dict[str, object]) -> dict[str, object]:
    return {
        "name": step_name,
        "report_name": payload.get("report_name"),
        "run_id": payload.get("run_id"),
        "status": "succeeded",
    }
