from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.http import execute_request
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor, PsqlExecutionError
from stockanalysis.ingest.registry import get_source
from stockanalysis.ingest.sec.models import SecCompanyFactsSyncResult, SecCompanyFactsValueRecord
from stockanalysis.ingest.sec.sql import (
    render_instrument_lookup_by_company_name_sql,
    render_instrument_lookup_by_symbol_sql,
    render_sec_companyfacts_upsert_sql,
)

_FORM_TO_SCOPE = {
    "10-K": ("annual", True),
    "10-Q": ("quarterly", False),
    "20-F": ("annual", True),
}

_CONCEPT_TO_METRIC_CODE = {
    "Revenues": "revenue",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "revenue",
    "GrossProfit": "gross_profit",
    "NetIncomeLoss": "net_income",
    "OperatingIncomeLoss": "operating_income",
    "NetCashProvidedByUsedInOperatingActivities": "operating_cash_flow",
    "PaymentsToAcquirePropertyPlantAndEquipment": "capital_expenditure",
    "Assets": "total_assets",
    "Liabilities": "total_liabilities",
    "StockholdersEquity": "shareholders_equity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": "shareholders_equity",
    "EntityCommonStockSharesOutstanding": "shares_outstanding",
}

_POINT_IN_TIME_METRIC_CODES = {
    "total_assets",
    "total_liabilities",
    "shareholders_equity",
    "shares_outstanding",
}

_UNIT_BY_METRIC_CODE = {
    "shares_outstanding": "shares",
}

_DEFAULT_CIK_SYMBOL_FALLBACKS = {
    "0000034088": "XOM",
    "0000320193": "AAPL",
    "0000789019": "MSFT",
    "0001045810": "NVDA",
    "0001318605": "TSLA",
}


@dataclass(frozen=True)
class _ResolvedInstrument:
    instrument_id: int
    primary_symbol: str
    instrument_name: str
    issuer_display_name: str
    issuer_legal_name: str


def load_sec_companyfacts_sync_result(
    cik: str,
    *,
    config: RuntimeConfig,
    companyfacts_json_path: str | None = None,
) -> SecCompanyFactsSyncResult:
    payload = _load_companyfacts_payload(
        cik,
        config=config,
        json_path=companyfacts_json_path,
    )
    result = normalize_companyfacts_payload(payload)
    if not result.values:
        raise ValueError(f"SEC companyfacts payload for `{result.cik}` does not contain supported facts")
    return result


def normalize_companyfacts_payload(payload: dict[str, Any]) -> SecCompanyFactsSyncResult:
    cik = str(payload["cik"]).zfill(10)
    company_name = str(payload["entityName"])
    facts = payload.get("facts", {})
    us_gaap = facts.get("us-gaap")
    if not isinstance(us_gaap, dict):
        raise ValueError(f"SEC companyfacts payload for `{cik}` does not contain `facts.us-gaap`")
    fact_namespaces = [us_gaap]
    dei = facts.get("dei")
    if isinstance(dei, dict):
        fact_namespaces.append(dei)

    selected: dict[tuple[str, int, int | None, date, str], SecCompanyFactsValueRecord] = {}
    skipped_count = 0

    for facts_payload in fact_namespaces:
        for concept_name, concept_payload in facts_payload.items():
            metric_code = _CONCEPT_TO_METRIC_CODE.get(str(concept_name))
            if metric_code is None:
                continue
            expected_unit = _UNIT_BY_METRIC_CODE.get(metric_code, "USD")
            units = concept_payload.get("units")
            if not isinstance(units, dict):
                skipped_count += 1
                continue
            for unit_name, raw_items in units.items():
                if unit_name != expected_unit:
                    skipped_count += len(raw_items) if isinstance(raw_items, list) else 1
                    continue
                if not isinstance(raw_items, list):
                    skipped_count += 1
                    continue
                for raw_item in raw_items:
                    record = _normalize_companyfacts_item(metric_code, raw_item, unit=expected_unit)
                    if record is None:
                        skipped_count += 1
                        continue
                    key = (
                        record.statement_scope,
                        record.fiscal_year,
                        record.fiscal_quarter,
                        record.period_end,
                        record.metric_code,
                    )
                    existing = selected.get(key)
                    if existing is None or _is_newer_record(record, existing):
                        selected[key] = record

    values = tuple(
        sorted(
            selected.values(),
            key=lambda record: (
                record.period_end,
                record.statement_scope,
                record.metric_code,
            ),
        )
    )
    return SecCompanyFactsSyncResult(
        cik=cik,
        company_name=company_name,
        values=values,
        skipped_count=skipped_count,
    )


def run_sec_companyfacts_upsert(
    cik: str,
    *,
    config: RuntimeConfig,
    companyfacts_json_path: str | None = None,
    fallback_symbol: str | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    result = load_sec_companyfacts_sync_result(
        cik,
        config=config,
        companyfacts_json_path=companyfacts_json_path,
    )
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    instrument = resolve_instrument_for_company(
        result.company_name,
        cik=result.cik,
        fallback_symbol=fallback_symbol,
        executor=sql_executor,
    )
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="sec_companyfacts_upsert",
        config_json={
            "cik": result.cik,
            "company_name": result.company_name,
            "companyfacts_fixture_path": companyfacts_json_path,
            "fallback_symbol": _normalize_symbol(fallback_symbol),
            "instrument_id": instrument.instrument_id,
            "instrument_symbol": instrument.primary_symbol,
        },
    )
    try:
        sql_executor.execute_non_query(
            render_sec_companyfacts_upsert_sql(
                result,
                instrument_id=instrument.instrument_id,
                source_run_id=run_id,
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    summary = result.summary()
    summary["run_id"] = run_id
    summary["instrument_id"] = instrument.instrument_id
    summary["instrument_symbol"] = instrument.primary_symbol
    return summary


def resolve_instrument_for_company(
    company_name: str,
    *,
    cik: str | None = None,
    fallback_symbol: str | None = None,
    executor: PsqlCommandExecutor,
) -> _ResolvedInstrument:
    explicit_fallback_symbol = _normalize_symbol(fallback_symbol)
    if explicit_fallback_symbol is not None:
        try:
            payload_text = executor.execute_scalar(render_instrument_lookup_by_symbol_sql(explicit_fallback_symbol))
            payload = json.loads(payload_text)
            return _ResolvedInstrument(
                instrument_id=int(payload["instrument_id"]),
                primary_symbol=str(payload["primary_symbol"]),
                instrument_name=str(payload["instrument_name"]),
                issuer_display_name=str(payload["issuer_display_name"]),
                issuer_legal_name=str(payload["issuer_legal_name"]),
            )
        except PsqlExecutionError:
            pass

    try:
        payload_text = executor.execute_scalar(render_instrument_lookup_by_company_name_sql(company_name))
    except PsqlExecutionError as exc:
        resolved_fallback_symbol = _DEFAULT_CIK_SYMBOL_FALLBACKS.get(str(cik or "").zfill(10))
        if resolved_fallback_symbol is None:
            raise ValueError(f"No canonical instrument found for company `{company_name}`.") from exc
        try:
            payload_text = executor.execute_scalar(render_instrument_lookup_by_symbol_sql(resolved_fallback_symbol))
        except PsqlExecutionError as symbol_exc:
            raise ValueError(
                f"No canonical instrument found for company `{company_name}` "
                f"or CIK fallback symbol `{resolved_fallback_symbol}`."
            ) from symbol_exc
    payload = json.loads(payload_text)
    return _ResolvedInstrument(
        instrument_id=int(payload["instrument_id"]),
        primary_symbol=str(payload["primary_symbol"]),
        instrument_name=str(payload["instrument_name"]),
        issuer_display_name=str(payload["issuer_display_name"]),
        issuer_legal_name=str(payload["issuer_legal_name"]),
    )


def _normalize_symbol(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().upper()
    return normalized or None


def _normalize_companyfacts_item(
    metric_code: str,
    payload: dict[str, Any],
    *,
    unit: str,
) -> SecCompanyFactsValueRecord | None:
    form = str(payload.get("form", "")).upper()
    if form.endswith("/A"):
        form = form[:-2]
    scope = _FORM_TO_SCOPE.get(form)
    if scope is None:
        return None
    statement_scope, is_audited = scope
    start_text = payload.get("start")
    end_text = payload.get("end")
    if not end_text:
        return None
    if not start_text and metric_code in _POINT_IN_TIME_METRIC_CODES:
        start_text = end_text
    if not start_text:
        return None
    fy = payload.get("fy")
    if fy is None:
        return None
    try:
        value = Decimal(str(payload["val"]))
    except (KeyError, InvalidOperation):
        return None
    return SecCompanyFactsValueRecord(
        accession_number=_normalize_accession_number(payload.get("accn")),
        statement_scope=statement_scope,
        fiscal_year=int(fy),
        fiscal_quarter=_parse_fiscal_quarter(payload.get("fp"), statement_scope=statement_scope),
        period_start=date.fromisoformat(str(start_text)),
        period_end=date.fromisoformat(str(end_text)),
        report_date=_parse_optional_date(payload.get("filed")),
        currency_code="USD",
        is_audited=is_audited,
        metric_code=metric_code,
        metric_value=value,
        unit=unit,
    )


def _parse_fiscal_quarter(raw_fp: object, *, statement_scope: str) -> int | None:
    if statement_scope == "annual":
        return None
    if raw_fp is None:
        return None
    value = str(raw_fp).upper()
    if value.startswith("Q") and len(value) == 2 and value[1].isdigit():
        return int(value[1])
    return None


def _normalize_accession_number(raw_value: object) -> str | None:
    if raw_value is None:
        return None
    value = str(raw_value).strip()
    return value or None


def _parse_optional_date(raw_value: object) -> date | None:
    if raw_value in {None, ""}:
        return None
    return date.fromisoformat(str(raw_value))


def _is_newer_record(candidate: SecCompanyFactsValueRecord, existing: SecCompanyFactsValueRecord) -> bool:
    candidate_date = candidate.report_date or candidate.period_end
    existing_date = existing.report_date or existing.period_end
    if candidate_date != existing_date:
        return candidate_date > existing_date
    return (candidate.accession_number or "") >= (existing.accession_number or "")


def _load_companyfacts_payload(
    cik: str,
    *,
    config: RuntimeConfig,
    json_path: str | None,
) -> dict[str, Any]:
    if json_path:
        return json.loads(Path(json_path).read_text(encoding="utf-8"))
    sec = get_source("sec")
    request = sec.build_request(
        "companyfacts",
        {"cik": cik},
        config=config,
        require_credentials=True,
    )
    return execute_request(request).as_json()


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
    truncated = error_summary.strip()[:2000] or "sec companyfacts upsert failed"
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
