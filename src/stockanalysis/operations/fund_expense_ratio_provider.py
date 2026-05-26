from __future__ import annotations

import html
import re
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.request import Request, urlopen

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal, sql_numeric
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_SSGA_SPDR_SPY_PRODUCT_URL = "https://www.ssga.com/us/en/intermediary/etfs/spdr-sp-500-etf-trust-spy"
DEFAULT_SSGA_FUND_METRIC_SOURCE_NAME = "ssga_spdr_product_page"
DEFAULT_PIPELINE_NAME = "fund_expense_ratio_ssga_spdr_import"


@dataclass(frozen=True)
class FundExpenseRatioSnapshot:
    symbol: str
    metric_code: str
    metric_value: Decimal
    metric_unit: str
    source_name: str
    source_url: str
    source_as_of_date: date
    confidence: Decimal
    rationale: str

    @property
    def percent_value(self) -> Decimal:
        return self.metric_value * Decimal("100")


def download_ssga_spdr_product_page(*, url: str = DEFAULT_SSGA_SPDR_SPY_PRODUCT_URL) -> str:
    request = Request(url, headers={"User-Agent": "stockanalysis-fund-expense-ratio/0.1"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_ssga_spdr_expense_ratio_page(
    content: str,
    *,
    symbol: str = "SPY",
    source_url: str = DEFAULT_SSGA_SPDR_SPY_PRODUCT_URL,
    source_name: str = DEFAULT_SSGA_FUND_METRIC_SOURCE_NAME,
) -> FundExpenseRatioSnapshot:
    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        raise ValueError("symbol is required")
    text = html.unescape(content)
    raw_percent = _extract_gross_expense_ratio_percent(text)
    source_as_of_date = _extract_source_as_of_date(text)
    metric_value = raw_percent / Decimal("100")
    return FundExpenseRatioSnapshot(
        symbol=normalized_symbol,
        metric_code="gross_expense_ratio",
        metric_value=metric_value,
        metric_unit="ratio",
        source_name=source_name,
        source_url=source_url,
        source_as_of_date=source_as_of_date,
        confidence=Decimal("0.9500"),
        rationale=(
            f"Official State Street SPDR product page reported Gross Expense Ratio "
            f"{raw_percent}% as of {source_as_of_date.isoformat()}."
        ),
    )


def render_fund_expense_ratio_upsert_sql(
    snapshot: FundExpenseRatioSnapshot,
    *,
    source_run_id: int | None = None,
) -> str:
    source_run_literal = "null::bigint" if source_run_id is None else f"{int(source_run_id)}::bigint"
    return f"""-- fund expense ratio metric upsert
with input_row as (
    select
        {sql_literal(snapshot.symbol)}::text as symbol,
        {sql_literal(snapshot.metric_code)}::text as metric_code,
        {sql_numeric(snapshot.metric_value)} as metric_value,
        {sql_literal(snapshot.metric_unit)}::text as metric_unit,
        {sql_literal(snapshot.source_name)}::text as source_name,
        {sql_literal(snapshot.source_url)}::text as source_url,
        {sql_date(snapshot.source_as_of_date)} as source_as_of_date,
        {sql_numeric(snapshot.confidence)} as confidence,
        {sql_literal(snapshot.rationale)}::text as rationale
),
resolved_instrument as (
    select instrument.instrument_id
    from ref.instrument instrument
    join input_row input on upper(instrument.primary_symbol) = input.symbol
    where instrument.is_active
    order by instrument.instrument_id
    limit 1
),
guard_missing as (
    select case
        when not exists(select 1 from resolved_instrument)
        then 1 / 0
        else 1
    end as ok
)
insert into market.fund_metric_snapshot (
    instrument_id,
    as_of_date,
    metric_code,
    metric_value,
    metric_unit,
    source_name,
    source_url,
    source_as_of_date,
    confidence,
    rationale,
    source_run_id,
    updated_at
)
select
    instrument.instrument_id,
    input.source_as_of_date,
    input.metric_code,
    input.metric_value,
    input.metric_unit,
    input.source_name,
    input.source_url,
    input.source_as_of_date,
    input.confidence,
    input.rationale,
    {source_run_literal},
    now()
from input_row input
join resolved_instrument instrument on true
cross join guard_missing
on conflict (instrument_id, metric_code, source_name, source_as_of_date) do update
set
    as_of_date = excluded.as_of_date,
    metric_value = excluded.metric_value,
    metric_unit = excluded.metric_unit,
    source_url = excluded.source_url,
    confidence = excluded.confidence,
    rationale = excluded.rationale,
    source_run_id = excluded.source_run_id,
    updated_at = now()
returning fund_metric_snapshot_id;"""


def run_ssga_spdr_fund_expense_ratio_import(
    *,
    config: RuntimeConfig,
    symbol: str = "SPY",
    source_html: str | Path | None = None,
    raw_html_output: str | Path | None = None,
    source_url: str = DEFAULT_SSGA_SPDR_SPY_PRODUCT_URL,
    source_name: str = DEFAULT_SSGA_FUND_METRIC_SOURCE_NAME,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmpdir:
        if source_html:
            content = Path(source_html).expanduser().resolve().read_text(encoding="utf-8")
        else:
            content = download_ssga_spdr_product_page(url=source_url)
            if execute and raw_html_output is not None:
                raw_output_path = Path(raw_html_output)
                raw_output_path.parent.mkdir(parents=True, exist_ok=True)
                raw_output_path.write_text(content, encoding="utf-8")
        snapshot = parse_ssga_spdr_expense_ratio_page(
            content,
            symbol=symbol,
            source_url=source_url,
            source_name=source_name,
        )

    fund_metric_snapshot_id: int | None = None
    run_id: int | None = None
    if execute:
        sql_executor = executor or PsqlCommandExecutor.from_config(config)
        run_id = _create_pipeline_run(
            sql_executor,
            pipeline_name=DEFAULT_PIPELINE_NAME,
            config_json={
                "symbol": snapshot.symbol,
                "metric_code": snapshot.metric_code,
                "source_url": source_url,
                "source_name": source_name,
                "source_as_of_date": snapshot.source_as_of_date.isoformat(),
            },
        )
        try:
            fund_metric_snapshot_id = int(
                sql_executor.execute_scalar(render_fund_expense_ratio_upsert_sql(snapshot, source_run_id=run_id))
            )
            _mark_pipeline_run_succeeded(sql_executor, run_id)
        except Exception as exc:
            _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
            raise

    return {
        "report_name": DEFAULT_PIPELINE_NAME,
        "status": "completed" if execute else "planned",
        "execute": execute,
        "run_id": run_id,
        "fund_metric_snapshot_id": fund_metric_snapshot_id,
        "symbol": snapshot.symbol,
        "metric_code": snapshot.metric_code,
        "metric_value": format(snapshot.metric_value, "f"),
        "percent_value": format(snapshot.percent_value, "f"),
        "metric_unit": snapshot.metric_unit,
        "source_name": snapshot.source_name,
        "source_url": snapshot.source_url,
        "source_as_of_date": snapshot.source_as_of_date.isoformat(),
        "confidence": format(snapshot.confidence, "f"),
        "raw_html_output": str(raw_html_output or source_html or ""),
        "recommendation_scoring_mutated": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": "read_only_no_order",
    }


def _extract_gross_expense_ratio_percent(text: str) -> Decimal:
    patterns = (
        r'"gross-expense-ratio"\s*:\s*\{.*?"originalValue"\s*:\s*"([0-9]+(?:\.[0-9]+)?)"',
        r'"gross-expense-ratio"\s*:\s*\{.*?"value"\s*:\s*"([0-9]+(?:\.[0-9]+)?)\s*%"',
        r"Gross Expense Ratio.*?([0-9]+(?:\.[0-9]+)?)\s*%",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        try:
            value = Decimal(match.group(1))
        except InvalidOperation:
            continue
        if value < 0:
            continue
        return value
    raise ValueError("SSGA product page did not expose Gross Expense Ratio.")


def _extract_source_as_of_date(text: str) -> date:
    match = re.search(r"Fund Information.*?as of ([A-Za-z]+ [0-9]{1,2} [0-9]{4})", text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        match = re.search(r'"asOfDateSimple"\s*:\s*"([A-Za-z]+ [0-9]{1,2} [0-9]{4})"', text)
    if not match:
        match = re.search(r"as of ([A-Za-z]+ [0-9]{1,2} [0-9]{4})", text, flags=re.IGNORECASE)
    if not match:
        raise ValueError("SSGA product page did not expose a fund information as-of date.")
    return datetime.strptime(match.group(1), "%B %d %Y").date()
