from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Mapping
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
DEFAULT_TRACKING_DIFFERENCE_PIPELINE_NAME = "fund_tracking_difference_ssga_spdr_import"
DEFAULT_INVESCO_QQQ_DETAILS_URL = (
    "https://dng-api.invesco.com/cache/v1/accounts/en_US/shareclasses/QQQ"
    "?idType=ticker&variationType=fundDetails&productType=ETF"
)
DEFAULT_INVESCO_QQQ_PERFORMANCE_URL = (
    "https://dng-api.invesco.com/cache/v1/accounts/en_US/shareclasses/QQQ/performance/rolling"
    "?idType=ticker&productType=ETF"
)
DEFAULT_INVESCO_QQQ_FUND_METRIC_SOURCE_NAME = "invesco_qqq_product_api"
DEFAULT_INVESCO_QQQ_EXPENSE_PIPELINE_NAME = "fund_expense_ratio_invesco_qqq_import"
DEFAULT_INVESCO_QQQ_NAV_PIPELINE_NAME = "fund_nav_premium_discount_invesco_qqq_import"
DEFAULT_INVESCO_QQQ_TRACKING_PIPELINE_NAME = "fund_tracking_difference_invesco_qqq_import"

TRACKING_DIFFERENCE_WINDOWS: tuple[tuple[str, str], ...] = (
    ("1_month", "1 Month"),
    ("qtd", "QTD"),
    ("ytd", "YTD"),
    ("1_year", "1 Year"),
    ("3_year", "3 Year"),
    ("5_year", "5 Year"),
    ("10_year", "10 Year"),
    ("since_inception", "Since Inception Jan 22 1993"),
)


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
    measurement_window: str = ""
    measurement_basis: str = ""
    benchmark_name: str = ""
    fund_return: Decimal | None = None
    benchmark_return: Decimal | None = None

    @property
    def percent_value(self) -> Decimal:
        return self.metric_value * Decimal("100")


FundExpenseRatioSnapshot = FundMetricSnapshot


def download_ssga_spdr_product_page(*, url: str = DEFAULT_SSGA_SPDR_SPY_PRODUCT_URL) -> str:
    request = Request(url, headers={"User-Agent": "stockanalysis-fund-expense-ratio/0.1"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def download_invesco_qqq_json(*, url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "stockanalysis-fund-metric/0.1",
            "Referer": "https://www.invesco.com/qqq-etf/en/about.html",
        },
    )
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


def parse_ssga_spdr_tracking_difference_page(
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
    headers = _extract_fund_performance_headers(text)
    nav_row = _extract_fund_performance_row(text, "NAV")
    benchmark_row = _extract_fund_performance_row(text, "Benchmark")
    benchmark_name = _extract_benchmark_name(benchmark_row["raw_row"])
    if nav_row["source_as_of_date"] != benchmark_row["source_as_of_date"]:
        raise ValueError("SSGA product page exposed mismatched NAV and benchmark performance dates.")

    snapshots: list[FundMetricSnapshot] = []
    for raw_window, fund_return, benchmark_return in zip(
        headers,
        nav_row["returns"],
        benchmark_row["returns"],
        strict=True,
    ):
        if fund_return is None or benchmark_return is None:
            continue
        window_code = _tracking_window_code(raw_window)
        metric_value = fund_return - benchmark_return
        snapshots.append(
            FundMetricSnapshot(
                symbol=normalized_symbol,
                metric_code=f"tracking_difference_nav_{window_code}",
                metric_value=metric_value,
                metric_unit="ratio",
                source_name=source_name,
                source_url=source_url,
                source_as_of_date=nav_row["source_as_of_date"],
                confidence=Decimal("0.9000"),
                rationale=(
                    f"Official State Street SPDR product page reported NAV return "
                    f"{fund_return * Decimal('100')}% and {benchmark_name} return "
                    f"{benchmark_return * Decimal('100')}% for {raw_window} as of "
                    f"{nav_row['source_as_of_date'].isoformat()}. Stored as tracking difference, "
                    f"not tracking error."
                ),
                measurement_window=raw_window,
                measurement_basis="nav_total_return_before_tax",
                benchmark_name=benchmark_name,
                fund_return=fund_return,
                benchmark_return=benchmark_return,
            )
        )
    if not snapshots:
        raise ValueError("SSGA product page did not expose comparable NAV and benchmark return windows.")
    return tuple(snapshots)


def parse_invesco_qqq_expense_ratio_json(
    content: str,
    *,
    symbol: str = "QQQ",
    source_url: str = DEFAULT_INVESCO_QQQ_DETAILS_URL,
    source_name: str = DEFAULT_INVESCO_QQQ_FUND_METRIC_SOURCE_NAME,
) -> FundMetricSnapshot:
    payload = json.loads(content)
    normalized_symbol = symbol.strip().upper()
    if normalized_symbol != "QQQ":
        raise ValueError("Invesco QQQ provider only supports symbol QQQ.")
    fee_percent = Decimal(str(payload["feeValue"]))
    source_as_of_date = _json_date(payload["effectiveDate"])
    return FundMetricSnapshot(
        symbol=normalized_symbol,
        metric_code="net_expense_ratio",
        metric_value=fee_percent / Decimal("100"),
        metric_unit="ratio",
        source_name=source_name,
        source_url=source_url,
        source_as_of_date=source_as_of_date,
        confidence=Decimal("0.9500"),
        rationale=(
            f"Official Invesco QQQ product API reported total expense ratio {fee_percent}% "
            f"as of {source_as_of_date.isoformat()}."
        ),
    )


def parse_invesco_qqq_nav_premium_discount_json(
    content: str,
    *,
    symbol: str = "QQQ",
    source_url: str = DEFAULT_INVESCO_QQQ_DETAILS_URL,
    source_name: str = DEFAULT_INVESCO_QQQ_FUND_METRIC_SOURCE_NAME,
) -> tuple[FundMetricSnapshot, ...]:
    payload = json.loads(content)
    normalized_symbol = symbol.strip().upper()
    if normalized_symbol != "QQQ":
        raise ValueError("Invesco QQQ provider only supports symbol QQQ.")
    source_as_of_date = _json_date(payload["effectiveBusinessDate"])
    nav = Decimal(str(payload["nav"]))
    return (
        FundMetricSnapshot(
            symbol=normalized_symbol,
            metric_code="nav_per_share",
            metric_value=nav,
            metric_unit="USD",
            source_name=source_name,
            source_url=source_url,
            source_as_of_date=source_as_of_date,
            confidence=Decimal("0.9500"),
            rationale=(
                f"Official Invesco QQQ product API reported NAV per share ${nav} "
                f"as of {source_as_of_date.isoformat()}."
            ),
        ),
    )


def parse_invesco_qqq_tracking_difference_json(
    content: str,
    *,
    symbol: str = "QQQ",
    source_url: str = DEFAULT_INVESCO_QQQ_PERFORMANCE_URL,
    source_name: str = DEFAULT_INVESCO_QQQ_FUND_METRIC_SOURCE_NAME,
) -> tuple[FundMetricSnapshot, ...]:
    payload = json.loads(content)
    normalized_symbol = symbol.strip().upper()
    if normalized_symbol != "QQQ":
        raise ValueError("Invesco QQQ provider only supports symbol QQQ.")
    source_as_of_date = _json_date(payload["effectiveDate"])
    snapshots: list[FundMetricSnapshot] = []
    for chart_key, window_code, window_label in (
        ("lineChart1YData", "1_year", "1 Year"),
        ("lineChart3YData", "3_year", "3 Year"),
        ("lineChart5YData", "5_year", "5 Year"),
        ("lineChart10YData", "10_year", "10 Year"),
    ):
        series = payload.get(chart_key) or []
        fund_series = _find_invesco_performance_series(series, "Shareclass")
        benchmark_series = _find_invesco_performance_series(series, "NASDAQ-100 Index")
        fund_return = _last_return_ratio(fund_series)
        benchmark_return = _last_return_ratio(benchmark_series)
        metric_value = fund_return - benchmark_return
        snapshots.append(
            FundMetricSnapshot(
                symbol=normalized_symbol,
                metric_code=f"tracking_difference_nav_{window_code}",
                metric_value=metric_value,
                metric_unit="ratio",
                source_name=source_name,
                source_url=source_url,
                source_as_of_date=source_as_of_date,
                confidence=Decimal("0.9000"),
                rationale=(
                    f"Official Invesco QQQ performance API reported NAV return "
                    f"{fund_return * Decimal('100')}% and NASDAQ-100 Index return "
                    f"{benchmark_return * Decimal('100')}% for {window_label} as of "
                    f"{source_as_of_date.isoformat()}. Stored as tracking difference, not tracking error."
                ),
                measurement_window=window_label,
                measurement_basis="nav_total_return_growth_of_10k",
                benchmark_name="NASDAQ-100 Index",
                fund_return=fund_return,
                benchmark_return=benchmark_return,
            )
        )
    return tuple(snapshots)


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
        {sql_literal(snapshot.rationale)}::text as rationale,
        {sql_literal(snapshot.measurement_window)}::text as measurement_window,
        {sql_literal(snapshot.measurement_basis)}::text as measurement_basis,
        {sql_literal(snapshot.benchmark_name)}::text as benchmark_name,
        {sql_numeric(snapshot.fund_return) if snapshot.fund_return is not None else "null::numeric"} as fund_return,
        {sql_numeric(snapshot.benchmark_return) if snapshot.benchmark_return is not None else "null::numeric"} as benchmark_return
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
    measurement_window,
    measurement_basis,
    benchmark_name,
    fund_return,
    benchmark_return,
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
    input.measurement_window,
    input.measurement_basis,
    input.benchmark_name,
    input.fund_return,
    input.benchmark_return,
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
    measurement_window = excluded.measurement_window,
    measurement_basis = excluded.measurement_basis,
    benchmark_name = excluded.benchmark_name,
    fund_return = excluded.fund_return,
    benchmark_return = excluded.benchmark_return,
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


def run_ssga_spdr_fund_tracking_difference_import(
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
    snapshots = parse_ssga_spdr_tracking_difference_page(
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
            pipeline_name=DEFAULT_TRACKING_DIFFERENCE_PIPELINE_NAME,
            config_json={
                "symbol": symbol.strip().upper(),
                "metric_codes": [snapshot.metric_code for snapshot in snapshots],
                "source_url": source_url,
                "source_name": source_name,
                "source_as_of_dates": sorted({snapshot.source_as_of_date.isoformat() for snapshot in snapshots}),
                "benchmark_name": snapshots[0].benchmark_name,
                "measurement_basis": snapshots[0].measurement_basis,
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
            "measurement_window": snapshot.measurement_window,
            "measurement_basis": snapshot.measurement_basis,
            "benchmark_name": snapshot.benchmark_name,
            "fund_return": format(snapshot.fund_return, "f") if snapshot.fund_return is not None else None,
            "benchmark_return": format(snapshot.benchmark_return, "f") if snapshot.benchmark_return is not None else None,
            "confidence": format(snapshot.confidence, "f"),
        }
        for snapshot in snapshots
    ]
    return {
        "report_name": DEFAULT_TRACKING_DIFFERENCE_PIPELINE_NAME,
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
        "metric_interpretation": "tracking_difference_not_tracking_error",
        "recommendation_scoring_mutated": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": "read_only_no_order",
    }


def run_invesco_qqq_fund_expense_ratio_import(
    *,
    config: RuntimeConfig,
    symbol: str = "QQQ",
    source_json: str | Path | None = None,
    raw_json_output: str | Path | None = None,
    source_url: str = DEFAULT_INVESCO_QQQ_DETAILS_URL,
    source_name: str = DEFAULT_INVESCO_QQQ_FUND_METRIC_SOURCE_NAME,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    content = _load_or_download_invesco_json(source_json=source_json, raw_json_output=raw_json_output, source_url=source_url, execute=execute)
    snapshot = parse_invesco_qqq_expense_ratio_json(
        content,
        symbol=symbol,
        source_url=source_url,
        source_name=source_name,
    )
    run_id, fund_metric_snapshot_ids = _execute_fund_metric_snapshots(
        config=config,
        pipeline_name=DEFAULT_INVESCO_QQQ_EXPENSE_PIPELINE_NAME,
        snapshots=(snapshot,),
        execute=execute,
        executor=executor,
    )
    return {
        "report_name": DEFAULT_INVESCO_QQQ_EXPENSE_PIPELINE_NAME,
        "status": "completed" if execute else "planned",
        "execute": execute,
        "run_id": run_id,
        "fund_metric_snapshot_id": fund_metric_snapshot_ids[0] if fund_metric_snapshot_ids else None,
        "symbol": snapshot.symbol,
        "metric_code": snapshot.metric_code,
        "metric_value": format(snapshot.metric_value, "f"),
        "percent_value": format(snapshot.percent_value, "f"),
        "metric_unit": snapshot.metric_unit,
        "source_name": snapshot.source_name,
        "source_url": snapshot.source_url,
        "source_as_of_date": snapshot.source_as_of_date.isoformat(),
        "confidence": format(snapshot.confidence, "f"),
        "raw_json_output": str(raw_json_output or source_json or ""),
        "recommendation_scoring_mutated": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": "read_only_no_order",
    }


def run_invesco_qqq_fund_nav_premium_discount_import(
    *,
    config: RuntimeConfig,
    symbol: str = "QQQ",
    source_json: str | Path | None = None,
    raw_json_output: str | Path | None = None,
    source_url: str = DEFAULT_INVESCO_QQQ_DETAILS_URL,
    source_name: str = DEFAULT_INVESCO_QQQ_FUND_METRIC_SOURCE_NAME,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    content = _load_or_download_invesco_json(source_json=source_json, raw_json_output=raw_json_output, source_url=source_url, execute=execute)
    snapshots = parse_invesco_qqq_nav_premium_discount_json(
        content,
        symbol=symbol,
        source_url=source_url,
        source_name=source_name,
    )
    run_id, fund_metric_snapshot_ids = _execute_fund_metric_snapshots(
        config=config,
        pipeline_name=DEFAULT_INVESCO_QQQ_NAV_PIPELINE_NAME,
        snapshots=snapshots,
        execute=execute,
        executor=executor,
    )
    return {
        "report_name": DEFAULT_INVESCO_QQQ_NAV_PIPELINE_NAME,
        "status": "completed" if execute else "planned",
        "execute": execute,
        "run_id": run_id,
        "fund_metric_snapshot_ids": fund_metric_snapshot_ids,
        "symbol": symbol.strip().upper(),
        "source_name": source_name,
        "source_url": source_url,
        "metric_count": len(snapshots),
        "metrics": _fund_metric_payload(snapshots),
        "raw_json_output": str(raw_json_output or source_json or ""),
        "recommendation_scoring_mutated": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": "read_only_no_order",
    }


def run_invesco_qqq_fund_tracking_difference_import(
    *,
    config: RuntimeConfig,
    symbol: str = "QQQ",
    source_json: str | Path | None = None,
    raw_json_output: str | Path | None = None,
    source_url: str = DEFAULT_INVESCO_QQQ_PERFORMANCE_URL,
    source_name: str = DEFAULT_INVESCO_QQQ_FUND_METRIC_SOURCE_NAME,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    content = _load_or_download_invesco_json(source_json=source_json, raw_json_output=raw_json_output, source_url=source_url, execute=execute)
    snapshots = parse_invesco_qqq_tracking_difference_json(
        content,
        symbol=symbol,
        source_url=source_url,
        source_name=source_name,
    )
    run_id, fund_metric_snapshot_ids = _execute_fund_metric_snapshots(
        config=config,
        pipeline_name=DEFAULT_INVESCO_QQQ_TRACKING_PIPELINE_NAME,
        snapshots=snapshots,
        execute=execute,
        executor=executor,
    )
    return {
        "report_name": DEFAULT_INVESCO_QQQ_TRACKING_PIPELINE_NAME,
        "status": "completed" if execute else "planned",
        "execute": execute,
        "run_id": run_id,
        "fund_metric_snapshot_ids": fund_metric_snapshot_ids,
        "symbol": symbol.strip().upper(),
        "source_name": source_name,
        "source_url": source_url,
        "metric_count": len(snapshots),
        "metrics": _fund_metric_payload(snapshots),
        "raw_json_output": str(raw_json_output or source_json or ""),
        "metric_interpretation": "tracking_difference_not_tracking_error",
        "recommendation_scoring_mutated": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": "read_only_no_order",
    }


def _load_or_download_invesco_json(
    *,
    source_json: str | Path | None,
    raw_json_output: str | Path | None,
    source_url: str,
    execute: bool,
) -> str:
    if source_json:
        return Path(source_json).expanduser().resolve().read_text(encoding="utf-8")
    content = download_invesco_qqq_json(url=source_url)
    if execute and raw_json_output is not None:
        raw_output_path = Path(raw_json_output)
        raw_output_path.parent.mkdir(parents=True, exist_ok=True)
        raw_output_path.write_text(content, encoding="utf-8")
    return content


def _execute_fund_metric_snapshots(
    *,
    config: RuntimeConfig,
    pipeline_name: str,
    snapshots: tuple[FundMetricSnapshot, ...],
    execute: bool,
    executor: PsqlCommandExecutor | None,
) -> tuple[int | None, list[int]]:
    fund_metric_snapshot_ids: list[int] = []
    run_id: int | None = None
    if not execute:
        return run_id, fund_metric_snapshot_ids
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    first = snapshots[0]
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=pipeline_name,
        config_json={
            "symbol": first.symbol,
            "metric_codes": [snapshot.metric_code for snapshot in snapshots],
            "source_name": first.source_name,
            "source_urls": sorted({snapshot.source_url for snapshot in snapshots}),
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
    return run_id, fund_metric_snapshot_ids


def _fund_metric_payload(snapshots: tuple[FundMetricSnapshot, ...]) -> list[dict[str, object]]:
    return [
        {
            "metric_code": snapshot.metric_code,
            "metric_value": format(snapshot.metric_value, "f"),
            "metric_unit": snapshot.metric_unit,
            "source_as_of_date": snapshot.source_as_of_date.isoformat(),
            "measurement_window": snapshot.measurement_window,
            "measurement_basis": snapshot.measurement_basis,
            "benchmark_name": snapshot.benchmark_name,
            "fund_return": format(snapshot.fund_return, "f") if snapshot.fund_return is not None else None,
            "benchmark_return": format(snapshot.benchmark_return, "f") if snapshot.benchmark_return is not None else None,
            "confidence": format(snapshot.confidence, "f"),
        }
        for snapshot in snapshots
    ]


def _json_date(value: object) -> date:
    return datetime.fromisoformat(str(value)).date()


def _find_invesco_performance_series(series: object, label_or_type: str) -> dict[str, object]:
    wanted = label_or_type.lower()
    for item in series if isinstance(series, list) else []:
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("type") or "").lower()
        item_label = str(item.get("label") or "").lower()
        if wanted in item_type or wanted in item_label:
            return item
    raise ValueError(f"Invesco QQQ performance JSON did not expose {label_or_type} series.")


def _last_return_ratio(series: Mapping[str, object]) -> Decimal:
    data = series.get("data")
    if not isinstance(data, list) or not data:
        raise ValueError("Invesco QQQ performance series did not expose return data.")
    last = data[-1]
    if not isinstance(last, dict):
        raise ValueError("Invesco QQQ performance series contained an invalid return point.")
    return Decimal(str(last["returnPercent"])) / Decimal("100")


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


def _extract_fund_performance_headers(text: str) -> tuple[str, ...]:
    before_tax_index = text.lower().find("fund before tax")
    if before_tax_index < 0:
        raise ValueError("SSGA product page did not expose Fund Before Tax performance rows.")
    table_head = text[:before_tax_index].rfind("<thead")
    if table_head < 0:
        raise ValueError("SSGA product page did not expose performance table headers.")
    table_head_end = text.find("</thead>", table_head)
    if table_head_end < 0 or table_head_end > before_tax_index:
        raise ValueError("SSGA product page exposed malformed performance table headers.")
    header_html = text[table_head:table_head_end]
    headers = tuple(
        _clean_html_text(raw_header)
        for raw_header in re.findall(
            r"<th[^>]*class=['\"][^'\"]*\bdata\b[^'\"]*['\"][^>]*>(.*?)</th>",
            header_html,
            flags=re.IGNORECASE | re.DOTALL,
        )
    )
    if not headers:
        raise ValueError("SSGA product page did not expose performance table window headers.")
    return headers


def _extract_fund_performance_row(text: str, label: str) -> dict[str, object]:
    pattern = rf"<tr>\s*<td>{re.escape(label)}\b.*?</tr>"
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        raise ValueError(f"SSGA product page did not expose {label} performance row.")
    row_html = match.group(0)
    date_match = re.search(
        r"<td[^>]*class=['\"][^'\"]*\bdate-col\b[^'\"]*['\"][^>]*>\s*([^<]+?)\s*</td>",
        row_html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not date_match:
        raise ValueError(f"SSGA product page did not expose {label} performance date.")
    raw_values = re.findall(
        r"<td[^>]*class=['\"][^'\"]*\bdata\b[^'\"]*['\"][^>]*>\s*([^<]*?)\s*</td>",
        row_html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return {
        "raw_row": row_html,
        "source_as_of_date": _parse_ssga_date(_clean_html_text(date_match.group(1))),
        "returns": tuple(_parse_optional_percent_ratio(raw_value) for raw_value in raw_values),
    }


def _extract_benchmark_name(row_html: object) -> str:
    row_text = str(row_html)
    match = re.search(
        r"<div[^>]*class=['\"][^'\"]*\binfo-data\b[^'\"]*['\"][^>]*>(.*?)</div>",
        row_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return "Benchmark"
    benchmark_name = _clean_html_text(match.group(1))
    return benchmark_name or "Benchmark"


def _tracking_window_code(window_label: str) -> str:
    normalized = re.sub(r"\s+", " ", window_label.strip()).lower()
    mapping = {
        "1 month": "1_month",
        "qtd": "qtd",
        "ytd": "ytd",
        "1 year": "1_year",
        "3 year": "3_year",
        "5 year": "5_year",
        "10 year": "10_year",
    }
    if normalized.startswith("since inception"):
        return "since_inception"
    if normalized not in mapping:
        raise ValueError(f"Unsupported SSGA performance window: {window_label}")
    return mapping[normalized]


def _parse_optional_percent_ratio(raw_value: str) -> Decimal | None:
    cleaned = _clean_html_text(raw_value)
    if not cleaned or cleaned in {"-", "--", "N/A"}:
        return None
    try:
        return Decimal(cleaned.replace("%", "").replace(",", "").strip()) / Decimal("100")
    except InvalidOperation as exc:
        raise ValueError(f"SSGA product page exposed an invalid performance return: {cleaned}") from exc


def _clean_html_text(value: str) -> str:
    without_breaks = re.sub(r"<br\s*/?>", " ", value, flags=re.IGNORECASE)
    without_tags = re.sub(r"<[^>]+>", " ", without_breaks)
    return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()


def _parse_ssga_date(raw_date: str) -> date:
    for fmt in ("%B %d %Y", "%b %d %Y"):
        try:
            return datetime.strptime(raw_date, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"SSGA product page exposed an invalid date: {raw_date}")


def _extract_source_as_of_date(text: str) -> date:
    match = re.search(r"Fund Information.*?as of ([A-Za-z]+ [0-9]{1,2} [0-9]{4})", text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        match = re.search(r'"asOfDateSimple"\s*:\s*"([A-Za-z]+ [0-9]{1,2} [0-9]{4})"', text)
    if not match:
        match = re.search(r"as of ([A-Za-z]+ [0-9]{1,2} [0-9]{4})", text, flags=re.IGNORECASE)
    if not match:
        raise ValueError("SSGA product page did not expose a fund information as-of date.")
    return _parse_ssga_date(match.group(1))
