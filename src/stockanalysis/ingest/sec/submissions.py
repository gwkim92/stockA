from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.http import execute_request
from stockanalysis.ingest.registry import get_source
from stockanalysis.ingest.sec.models import SecFilingRecord, SecFilingsSyncResult


def load_sec_filings_sync_result(
    cik: str,
    *,
    config: RuntimeConfig,
    submissions_json_path: str | None = None,
    max_filings: int | None = None,
) -> SecFilingsSyncResult:
    normalized_cik = cik.zfill(10)
    payload = _load_submissions_payload(
        normalized_cik,
        config=config,
        json_path=submissions_json_path,
    )
    result = normalize_submissions_payload(payload)
    if normalized_cik != result.cik:
        raise ValueError(f"Requested CIK `{normalized_cik}` does not match payload CIK `{result.cik}`")
    if max_filings is not None:
        if max_filings <= 0:
            raise ValueError("max_filings must be greater than 0")
        return SecFilingsSyncResult(
            cik=result.cik,
            company_name=result.company_name,
            filings=result.filings[:max_filings],
        )
    return result


def normalize_submissions_payload(payload: dict[str, Any]) -> SecFilingsSyncResult:
    cik = str(payload["cik"]).zfill(10)
    company_name = str(payload["name"])
    recent = payload.get("filings", {}).get("recent")
    if not isinstance(recent, dict):
        raise ValueError(f"SEC submissions payload for `{cik}` does not contain `filings.recent`")

    accessions = _coerce_list(recent, "accessionNumber")
    if not accessions:
        return SecFilingsSyncResult(cik=cik, company_name=company_name, filings=tuple())

    filings: list[SecFilingRecord] = []
    for index, accession in enumerate(accessions):
        if not accession:
            continue
        filing_date = date.fromisoformat(_list_value(recent, "filingDate", index) or "")
        primary_document = _list_value(recent, "primaryDocument", index)
        filings.append(
            SecFilingRecord(
                cik=cik,
                company_name=company_name,
                accession_number=accession,
                form_type=_list_value(recent, "form", index) or "unknown",
                filing_date=filing_date,
                primary_document=primary_document,
                primary_doc_description=_list_value(recent, "primaryDocDescription", index),
                filing_url=_build_primary_document_url(cik, accession, primary_document),
                filing_index_url=_build_index_url(cik, accession),
                items=_list_value(recent, "items", index),
                file_number=_list_value(recent, "fileNumber", index),
                film_number=_list_value(recent, "filmNumber", index),
                is_xbrl=_parse_optional_bool(_list_value(recent, "isXBRL", index)),
                is_inline_xbrl=_parse_optional_bool(_list_value(recent, "isInlineXBRL", index)),
            )
        )

    filings.sort(key=lambda record: (record.filing_date, record.accession_number), reverse=True)
    return SecFilingsSyncResult(cik=cik, company_name=company_name, filings=tuple(filings))


def _load_submissions_payload(
    cik: str,
    *,
    config: RuntimeConfig,
    json_path: str | None,
) -> dict[str, Any]:
    if json_path:
        return json.loads(Path(json_path).read_text(encoding="utf-8"))
    sec = get_source("sec")
    request = sec.build_request(
        "submissions",
        {"cik": cik},
        config=config,
        require_credentials=True,
    )
    return execute_request(request).as_json()


def _coerce_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"SEC submissions recent payload does not contain list `{key}`")
    return [str(item) if item is not None else "" for item in value]


def _list_value(payload: dict[str, Any], key: str, index: int) -> str | None:
    values = payload.get(key)
    if not isinstance(values, list):
        return None
    if index >= len(values):
        return None
    value = values[index]
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_optional_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    if value in {"1", "true", "True"}:
        return True
    if value in {"0", "false", "False"}:
        return False
    return None


def _build_index_url(cik: str, accession_number: str) -> str:
    cik_path = cik.lstrip("0") or "0"
    return f"https://www.sec.gov/Archives/edgar/data/{cik_path}/{accession_number}-index.html"


def _build_primary_document_url(cik: str, accession_number: str, primary_document: str | None) -> str:
    if not primary_document:
        return _build_index_url(cik, accession_number)
    cik_path = cik.lstrip("0") or "0"
    accession_path = accession_number.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{cik_path}/{accession_path}/{primary_document}"
