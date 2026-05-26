from __future__ import annotations

import html
import re
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
DEFAULT_NAV_PREMIUM_DISCOUNT_PIPELINE_NAME = "fund_nav_premium_discount_ssga_spdr_import"


@dataclass(frozen=True)
class FundMetricSnapshot:
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


FundExpenseRatioSnapshot = FundMetricSnapshot


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
) -> FundMetricSnapshot:
    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        raise ValueError("symbol is required")
    text = html.unescape(content)
    raw_percent = _extract_gross_expense_ratio_percent(text)
    source_as_of_date = _extract_source_as_of_date(text)
    metric_value = raw_percent / Decimal("100")
    return FundMetricSnapshot(
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


def parse_ssga_spdr_nav_premium_discount_page(
    content: str,
    *,
    symbol: str = "SPY",
    source_url: str = DEFAULT_SSGA_SPDR_SPY_PRODUCT_URL,
    source_name: str = DEFAULT_SSGA_FUND_METRIC_SOURCE_NAME,
) -> tuple[FundMetricSnapshot, ...]:
    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        raise ValueError("symbol is required")
    text = html.unescape(content)
    nav_value, nav_as_of_date = _extract_nav_value_and_date(text)
    market_as_of_date = _extract_section_as_of_date(text, "Fund Market Price")
    bid_ask_midpoint = _extract_table_money_value(text, "Bid/Ask Midpoint")
    closing_price = _extract_table_money_value(text, "Closing Price")
    premium_discount = _extract_table_percent_ratio(text, "Premium/Discount")
    return (
        FundMetricSnapshot(
            symbol=normalized_symbol,
            metric_code="nav_per_share",
            metric_value=nav_value,
            metric_unit="USD",
            source_name=source_name,
            source_url=source_url,
            source_as_of_date=nav_as_of_date,
            confidence=Decimal("0.9500"),
            rationale=(
                f"Official State Street SPDR product page reported NAV per share "
                f"${nav_value} as of {nav_as_of_date.isoformat()}."
            ),
        ),
        FundMetricSnapshot(
            symbol=normalized_symbol,
            metric_code="bid_ask_midpoint",
            metric_value=bid_ask_midpoint,
            metric_unit="USD",
            source_name=source_name,
            source_url=source_url,
            source_as_of_date=market_as_of_date,
            confidence=Decimal("0.9000"),
            rationale=(
                f"Official State Street SPDR product page reported Bid/Ask Midpoint "
                f"${bid_ask_midpoint} as of {market_as_of_date.isoformat()}."
            ),
        ),
        FundMetricSnapshot(
            symbol=normalized_symbol,
            metric_code="closing_price",
            metric_value=closing_price,
            metric_unit="USD",
            source_name=source_name,
            source_url=source_url,
            source_as_of_date=market_as_of_date,
            confidence=Decimal("0.9000"),
            rationale=(
                f"Official State Street SPDR product page reported Closing Price "
                f"${closing_price} as of {market_as_of_date.isoformat()}."
            ),
        ),
        FundMetricSnapshot(
            symbol=normalized_symbol,
            metric_code="premium_discount_to_nav",
            metric_value=premium_discount,
            metric_unit="ratio",
            source_name=source_name,
            source_url=source_url,
            source_as_of_date=market_as_of_date,
            confidence=Decimal("0.9000"),
            rationale=(
                f"Official State Street SPDR product page reported Premium/Discount to NAV "
                f"{premium_discount * Decimal('100')}% as of {market_as_of_date.isoformat()}."
            ),
        ),
    )


def render_fund_expense_ratio_upsert_sql(
    snapshot: FundMetricSnapshot,
    *,
    source_run_id: int | None = None,
) -> str:
    source_run_literal = "null::bigint" if source_run_id is None else f"{int(source_run_id)}::bigint"
    return f"""-- source-backed fund metric upsert
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


def run_ssga_spdr_fund_nav_premium_discount_import(
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
    if source_html:
        content = Path(source_html).expanduser().resolve().read_text(encoding="utf-8")
    else:
        content = download_ssga_spdr_product_page(url=source_url)
        if execute and raw_html_output is not None:
            raw_output_path = Path(raw_html_output)
            raw_output_path.parent.mkdir(parents=True, exist_ok=True)
            raw_output_path.write_text(content, encoding="utf-8")
    snapshots = parse_ssga_spdr_nav_premium_discount_page(
        content,
        symbol=symbol,
        source_url=source_url,
        source_name=source_name,
    )

    fund_metric_snapshot_ids: list[int] = []
    run_id: int | None = None
    if execute:
        sql_executor = executor or PsqlCommandExecutor.from_config(config)
        run_id = _create_pipeline_run(
            sql_executor,
            pipeline_name=DEFAULT_NAV_PREMIUM_DISCOUNT_PIPELINE_NAME,
            config_json={
                "symbol": symbol.strip().upper(),
                "metric_codes": [snapshot.metric_code for snapshot in snapshots],
                "source_url": source_url,
                "source_name": source_name,
                "source_as_of_dates": sorted({snapshot.source_as_of_date.isoformat() for snapshot in snapshots}),
            },
        )
        try:
            for snapshot in snapshots:
                fund_metric_snapshot_ids.append(
                    int(sql_executor.execute_scalar(render_fund_expense_ratio_upsert_sql(snapshot, source_run_id=run_id)))
                )
            _mark_pipeline_run_succeeded(sql_executor, run_id)
        except Exception as exc:
            _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
            raise

    metrics_payload = [
        {
            "metric_code": snapshot.metric_code,
            "metric_value": format(snapshot.metric_value, "f"),
            "metric_unit": snapshot.metric_unit,
            "source_as_of_date": snapshot.source_as_of_date.isoformat(),
            "confidence": format(snapshot.confidence, "f"),
        }
        for snapshot in snapshots
    ]
    return {
        "report_name": DEFAULT_NAV_PREMIUM_DISCOUNT_PIPELINE_NAME,
        "status": "completed" if execute else "planned",
        "execute": execute,
        "run_id": run_id,
        "fund_metric_snapshot_ids": fund_metric_snapshot_ids,
        "symbol": symbol.strip().upper(),
        "source_name": source_name,
        "source_url": source_url,
        "metric_count": len(metrics_payload),
        "metrics": metrics_payload,
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


def _extract_nav_value_and_date(text: str) -> tuple[Decimal, date]:
    nav_match = re.search(
        r'"nav"\s*:\s*\{.*?"asOfDateSimple"\s*:\s*"([A-Za-z]+ [0-9]{1,2} [0-9]{4})".*?"originalValue"\s*:\s*"([0-9]+(?:\.[0-9]+)?)"',
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not nav_match:
        nav_match = re.search(
            r'"nav"\s*:\s*\{.*?"originalValue"\s*:\s*"([0-9]+(?:\.[0-9]+)?)".*?"asOfDateSimple"\s*:\s*"([A-Za-z]+ [0-9]{1,2} [0-9]{4})"',
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if nav_match:
            raw_value, raw_date = nav_match.group(1), nav_match.group(2)
        else:
            raise ValueError("SSGA product page did not expose NAV and NAV date.")
    else:
        raw_date, raw_value = nav_match.group(1), nav_match.group(2)
    try:
        nav_value = Decimal(raw_value)
    except InvalidOperation as exc:
        raise ValueError("SSGA product page exposed an invalid NAV value.") from exc
    return nav_value, datetime.strptime(raw_date, "%B %d %Y").date()


def _extract_section_as_of_date(text: str, section_title: str) -> date:
    pattern = rf"{re.escape(section_title)}.*?as of ([A-Za-z]+ [0-9]{{1,2}} [0-9]{{4}})"
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        raise ValueError(f"SSGA product page did not expose {section_title} as-of date.")
    return datetime.strptime(match.group(1), "%B %d %Y").date()


def _extract_table_money_value(text: str, label: str) -> Decimal:
    raw_value = _extract_table_value(text, label)
    try:
        return Decimal(raw_value.replace("$", "").replace(",", "").strip())
    except InvalidOperation as exc:
        raise ValueError(f"SSGA product page exposed an invalid {label} value.") from exc


def _extract_table_percent_ratio(text: str, label: str) -> Decimal:
    raw_value = _extract_table_value(text, label)
    try:
        return Decimal(raw_value.replace("%", "").replace(",", "").strip()) / Decimal("100")
    except InvalidOperation as exc:
        raise ValueError(f"SSGA product page exposed an invalid {label} value.") from exc


def _extract_table_value(text: str, label: str) -> str:
    pattern = rf"<th[^>]*>\s*{re.escape(label)}\b.*?</th>\s*<td[^>]*class=['\"][^'\"]*\bdata\b[^'\"]*['\"][^>]*>\s*([^<]+?)\s*</td>"
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        raise ValueError(f"SSGA product page did not expose {label}.")
    return match.group(1).strip()


def _extract_source_as_of_date(text: str) -> date:
    match = re.search(r"Fund Information.*?as of ([A-Za-z]+ [0-9]{1,2} [0-9]{4})", text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        match = re.search(r'"asOfDateSimple"\s*:\s*"([A-Za-z]+ [0-9]{1,2} [0-9]{4})"', text)
    if not match:
        match = re.search(r"as of ([A-Za-z]+ [0-9]{1,2} [0-9]{4})", text, flags=re.IGNORECASE)
    if not match:
        raise ValueError("SSGA product page did not expose a fund information as-of date.")
    return datetime.strptime(match.group(1), "%B %d %Y").date()
