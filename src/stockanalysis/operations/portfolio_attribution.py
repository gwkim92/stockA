from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Mapping

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.performance.attribution import run_portfolio_attribution_bootstrap
from stockanalysis.signal.universe import _create_pipeline_run, _mark_pipeline_run_succeeded


DEFAULT_PORTFOLIO_NAME = "Long Term Paper"
DEFAULT_ATTRIBUTION_METHODOLOGY = "position_weighted_alpha_v1"
PIPELINE_NAME = "portfolio_attribution_bootstrap"


@dataclass(frozen=True)
class PortfolioAttributionWindow:
    portfolio_name: str
    snapshot_date: date
    measurement_end_date: date
    covered_position_count: int
    covered_weight: Decimal

    def as_payload(self) -> dict[str, object]:
        return {
            "portfolio_name": self.portfolio_name,
            "snapshot_date": self.snapshot_date.isoformat(),
            "measurement_end_date": self.measurement_end_date.isoformat(),
            "covered_position_count": self.covered_position_count,
            "covered_weight": str(self.covered_weight),
        }


def render_portfolio_attribution_window_lookup_sql(*, portfolio_name: str, as_of_date: date) -> str:
    return f"""-- portfolio attribution candidate window lookup
with selected_portfolio as (
    select portfolio_id, portfolio_name
    from portfolio.portfolio
    where portfolio_name = {sql_literal(portfolio_name)}
    limit 1
),
eligible_windows as (
    select
        portfolio.portfolio_name,
        position.snapshot_date,
        outcome.measurement_end_date,
        count(*) as covered_position_count,
        sum(position.weight) as covered_weight
    from selected_portfolio portfolio
    join portfolio.position_snapshot position on position.portfolio_id = portfolio.portfolio_id
    join performance.thesis_outcome outcome
      on outcome.thesis_id = position.linked_thesis_id
     and outcome.measurement_start_date = position.snapshot_date
    where position.snapshot_date <= {sql_date(as_of_date)}
      and outcome.measurement_end_date <= {sql_date(as_of_date)}
      and position.quantity <> 0
      and position.weight is not null
      and position.linked_thesis_id is not null
    group by portfolio.portfolio_name, position.snapshot_date, outcome.measurement_end_date
)
select coalesce(
    (
        select json_build_object(
            'portfolio_name', portfolio_name,
            'snapshot_date', snapshot_date,
            'measurement_end_date', measurement_end_date,
            'covered_position_count', covered_position_count,
            'covered_weight', covered_weight
        )
        from eligible_windows
        order by measurement_end_date desc, snapshot_date desc, covered_position_count desc
        limit 1
    ),
    '{{}}'::json
)::text;"""


def resolve_portfolio_attribution_window(
    *,
    config: RuntimeConfig,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
    as_of_date: date,
    executor: PsqlCommandExecutor | None = None,
) -> PortfolioAttributionWindow | None:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = sql_executor.execute_scalar(
        render_portfolio_attribution_window_lookup_sql(portfolio_name=portfolio_name, as_of_date=as_of_date)
    )
    try:
        row = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("portfolio attribution window lookup did not return JSON") from exc
    if not isinstance(row, Mapping) or not row:
        return None
    return PortfolioAttributionWindow(
        portfolio_name=str(row.get("portfolio_name") or portfolio_name),
        snapshot_date=date.fromisoformat(str(row["snapshot_date"])),
        measurement_end_date=date.fromisoformat(str(row["measurement_end_date"])),
        covered_position_count=int(row.get("covered_position_count") or 0),
        covered_weight=Decimal(str(row.get("covered_weight") or "0")),
    )


def run_portfolio_attribution_monthly(
    *,
    config: RuntimeConfig,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
    as_of_date: date,
    methodology: str = DEFAULT_ATTRIBUTION_METHODOLOGY,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    window = resolve_portfolio_attribution_window(
        config=config,
        portfolio_name=portfolio_name,
        as_of_date=as_of_date,
        executor=sql_executor,
    )
    report: dict[str, object] = {
        "report_name": "portfolio_attribution_monthly",
        "generated_at": _format_timestamp(generated_at or datetime.now(timezone.utc)),
        "status": "planned" if not execute else "running",
        "execute": execute,
        "portfolio_name": portfolio_name,
        "as_of_date": as_of_date.isoformat(),
        "methodology": methodology,
        "broker_submit_allowed": False,
        "automatic_order_allowed": False,
        "order_boundary": "read_only_no_order",
        "selected_window": window.as_payload() if window else None,
    }
    if window is None:
        report["status"] = "no_eligible_attribution_window" if not execute else "completed_no_eligible_window"
        report["next_action"] = "wait for thesis outcomes that match a portfolio snapshot date"
        if execute:
            run_id = _create_pipeline_run(
                sql_executor,
                pipeline_name=PIPELINE_NAME,
                config_json={
                    "portfolio_name": portfolio_name,
                    "as_of_date": as_of_date.isoformat(),
                    "methodology": methodology,
                    "action": "no_eligible_attribution_window",
                },
            )
            _mark_pipeline_run_succeeded(sql_executor, run_id)
            report["run_id"] = run_id
        return report

    report["next_action"] = "execute attribution for the selected covered portfolio/outcome window"
    if not execute:
        return report

    result = run_portfolio_attribution_bootstrap(
        config=config,
        portfolio_name=portfolio_name,
        snapshot_date=window.snapshot_date,
        measurement_end_date=window.measurement_end_date,
        methodology=methodology,
        executor=sql_executor,
    )
    report.update(result)
    report["status"] = "completed"
    return report


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

