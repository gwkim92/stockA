from __future__ import annotations

import json
from collections import Counter
from datetime import date
from typing import Any

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.ingest.sec.companyfacts import _load_companyfacts_payload
from stockanalysis.ingest.sec.models import SecFilingRecord, SecFilingsSyncResult
from stockanalysis.ingest.sec.submissions import load_sec_filings_sync_result
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_EVAL_NAME = "professional_source_blocker_raw_filing_remediation"
DEFAULT_DATASET_VERSION = "professional-source-blocker-raw-filing-remediation-v1"
DEFAULT_PIPELINE_NAME = "professional_source_blocker_raw_filing_remediation"
DEFAULT_PROVIDER = "deterministic_sec_source_policy"
DEFAULT_MODEL_NAME = "raw-filing-feasibility-v1"
SUPPORTED_PERIODIC_FORMS = frozenset({"10-K", "10-Q", "20-F", "40-F"})
PROSPECTUS_FORMS = frozenset({"424B4", "S-1", "S-1/A", "F-1", "F-1/A", "S-11", "S-11/A"})
REGISTRATION_ONLY_FORMS = frozenset({"S-8", "S-3", "S-3/A"})


def build_professional_source_blocker_raw_filing_decision(
    *,
    symbol: str,
    cik: str,
    as_of_date: date,
    filings: SecFilingsSyncResult,
    companyfacts_payload: dict[str, Any] | None,
    companyfacts_error: str | None = None,
) -> dict[str, object]:
    normalized_symbol = symbol.upper().strip()
    normalized_cik = str(cik).zfill(10)
    companyfacts_profile = _companyfacts_profile(companyfacts_payload, error=companyfacts_error)
    filing_profile = _filing_profile(filings)
    periodic_candidate = _latest_filing(
        filings.filings,
        allowed_forms=SUPPORTED_PERIODIC_FORMS,
        require_xbrl=True,
    )
    prospectus_candidate = _latest_filing(
        filings.filings,
        allowed_forms=PROSPECTUS_FORMS,
        require_xbrl=False,
    )
    registration_only_candidate = _latest_filing(
        filings.filings,
        allowed_forms=REGISTRATION_ONLY_FORMS,
        require_xbrl=False,
    )

    if companyfacts_profile["has_us_gaap"]:
        decision_status = "standard_companyfacts_available"
        blocker_code = ""
        durable_exclusion = False
        remediation_allowed = True
        next_action = "standard SEC companyfacts 경로를 다시 실행해 canonical financial facts를 적재한다."
        rationale = "SEC companyfacts에 us-gaap namespace가 있으므로 표준 financial-period-source-linkage 경로를 사용할 수 있다."
        remediation_command = (
            "stockanalysis-operations financial-period-source-linkage-run "
            f"--env-file <ENV> --as-of-date {as_of_date.isoformat()} "
            f"--fallback-symbol {normalized_symbol} --cik {normalized_cik} --execute"
        )
    elif periodic_candidate is not None:
        decision_status = "periodic_raw_xbrl_candidate"
        blocker_code = "raw_periodic_xbrl_parser_required"
        durable_exclusion = False
        remediation_allowed = False
        next_action = "10-K/10-Q/20-F/40-F raw XBRL parser task를 별도로 구현한 뒤 canonical source evidence로 적재한다."
        rationale = (
            "표준 companyfacts us-gaap는 없지만 XBRL/inline XBRL periodic filing이 있어 "
            "전용 raw filing parser로 지원할 수 있는 후보이다."
        )
        remediation_command = ""
    elif prospectus_candidate is not None:
        decision_status = "durable_exclusion_until_periodic_filing"
        blocker_code = "ipo_prospectus_without_standard_periodic_financials"
        durable_exclusion = True
        remediation_allowed = False
        next_action = "첫 10-Q/10-K 또는 안전한 prospectus/pro-forma parser가 생기기 전까지 장기 기업 재무 커버리지에서 제외한다."
        rationale = (
            "무료 SEC companyfacts에 us-gaap financial facts가 없고, 확인 가능한 주요 원천은 prospectus/registration filing이다. "
            "prospectus의 pro-forma, predecessor, carve-out 표는 표준 operating-company financial model로 자동 전환하면 오염 위험이 크다."
        )
        remediation_command = ""
    elif registration_only_candidate is not None:
        decision_status = "durable_exclusion_until_periodic_filing"
        blocker_code = "registration_only_without_standard_periodic_financials"
        durable_exclusion = True
        remediation_allowed = False
        next_action = "S-8 등 registration-only 문서는 기업 재무 모델 원천으로 쓰지 말고 첫 10-Q/10-K를 기다린다."
        rationale = (
            "표준 companyfacts와 periodic filing이 없고 registration-only filing만 확인된다. "
            "이 문서는 장기 기업 재무 모델의 매출, 현금흐름, 재무상태 원천으로 부족하다."
        )
        remediation_command = ""
    else:
        decision_status = "durable_exclusion_no_supported_public_financial_filing"
        blocker_code = "no_supported_free_public_financial_filing"
        durable_exclusion = True
        remediation_allowed = False
        next_action = "무료 공개 periodic financial filing이 확인될 때까지 장기 기업 재무 커버리지에서 제외한다."
        rationale = "표준 companyfacts, periodic XBRL filing, prospectus 후보가 모두 확인되지 않았다."
        remediation_command = ""

    return {
        "eval_name": DEFAULT_EVAL_NAME,
        "dataset_version": DEFAULT_DATASET_VERSION,
        "as_of_date": as_of_date.isoformat(),
        "symbol": normalized_symbol,
        "cik": normalized_cik,
        "company_name": filings.company_name,
        "decision_status": decision_status,
        "blocker_code": blocker_code,
        "durable_exclusion": durable_exclusion,
        "remediation_allowed": remediation_allowed,
        "remediation_command": remediation_command,
        "rationale": rationale,
        "next_action": next_action,
        "recheck_trigger": "new_10_q_or_10_k_or_20_f_filing" if durable_exclusion else "backend_source_task",
        "companyfacts": companyfacts_profile,
        "filings": filing_profile,
        "latest_supported_periodic_filing": _filing_to_json(periodic_candidate),
        "latest_prospectus_filing": _filing_to_json(prospectus_candidate),
        "latest_registration_only_filing": _filing_to_json(registration_only_candidate),
        "guardrails": {
            "synthetic_financial_facts_allowed": False,
            "paid_provider_required": False,
            "recommendation_scoring_mutated": False,
            "automatic_weight_change_allowed": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "order_boundary": "read_only_no_order",
        },
    }


def render_professional_source_blocker_raw_filing_decision_insert_sql(
    *,
    score_json: dict[str, object],
    eval_name: str = DEFAULT_EVAL_NAME,
    dataset_version: str = DEFAULT_DATASET_VERSION,
    provider: str = DEFAULT_PROVIDER,
    model_name: str = DEFAULT_MODEL_NAME,
) -> str:
    score_text = json.dumps(score_json, ensure_ascii=False, sort_keys=True)
    return f"""insert into ai.eval_run (
    eval_name,
    dataset_version,
    provider,
    model_name,
    score_json
)
values (
    {sql_literal(eval_name)},
    {sql_literal(dataset_version)},
    {sql_literal(provider)},
    {sql_literal(model_name)},
    {sql_literal(score_text)}::jsonb
)
returning eval_run_id;"""


def run_professional_source_blocker_raw_filing_remediation(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    cik: str,
    fallback_symbol: str,
    max_filings: int = 50,
    execute: bool = False,
    submissions_json_path: str | None = None,
    companyfacts_json_path: str | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    normalized_cik = str(cik).zfill(10)
    filings = load_sec_filings_sync_result(
        normalized_cik,
        config=config,
        submissions_json_path=submissions_json_path,
        max_filings=max_filings,
    )
    companyfacts_payload: dict[str, Any] | None = None
    companyfacts_error: str | None = None
    try:
        companyfacts_payload = _load_companyfacts_payload(
            normalized_cik,
            config=config,
            json_path=companyfacts_json_path,
        )
    except Exception as exc:  # noqa: BLE001 - persisted as source feasibility evidence.
        companyfacts_error = str(exc)

    decision = build_professional_source_blocker_raw_filing_decision(
        symbol=fallback_symbol,
        cik=normalized_cik,
        as_of_date=as_of_date,
        filings=filings,
        companyfacts_payload=companyfacts_payload,
        companyfacts_error=companyfacts_error,
    )
    report: dict[str, object] = {
        "report_name": DEFAULT_EVAL_NAME,
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "provider": DEFAULT_PROVIDER,
        "model_name": DEFAULT_MODEL_NAME,
        "decision": decision,
    }
    if not execute:
        return report
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "cik": normalized_cik,
            "fallback_symbol": fallback_symbol.upper().strip(),
            "max_filings": max_filings,
            "synthetic_financial_facts_allowed": False,
            "recommendation_scoring_mutated": False,
            "automatic_order_allowed": False,
        },
    )
    try:
        eval_run_id = int(
            sql_executor.execute_scalar(
                render_professional_source_blocker_raw_filing_decision_insert_sql(score_json=decision)
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise
    return {
        **report,
        "status": "completed",
        "run_id": run_id,
        "eval_run_id": eval_run_id,
    }


def _companyfacts_profile(payload: dict[str, Any] | None, *, error: str | None) -> dict[str, object]:
    if payload is None:
        return {
            "status": "failed" if error else "missing",
            "error": error or "",
            "namespaces": [],
            "has_us_gaap": False,
            "concept_count_by_namespace": {},
        }
    facts = payload.get("facts")
    if not isinstance(facts, dict):
        return {
            "status": "missing_facts",
            "error": "",
            "namespaces": [],
            "has_us_gaap": False,
            "concept_count_by_namespace": {},
        }
    namespaces = sorted(str(key) for key in facts.keys())
    concept_counts = {
        str(namespace): len(value) if isinstance(value, dict) else 0 for namespace, value in facts.items()
    }
    return {
        "status": "loaded",
        "error": "",
        "namespaces": namespaces,
        "has_us_gaap": isinstance(facts.get("us-gaap"), dict),
        "concept_count_by_namespace": concept_counts,
    }


def _filing_profile(filings: SecFilingsSyncResult) -> dict[str, object]:
    form_counts = Counter(record.form_type for record in filings.filings)
    return {
        "filing_count": len(filings.filings),
        "form_counts": dict(sorted(form_counts.items())),
        "latest_filing": _filing_to_json(filings.filings[0] if filings.filings else None),
        "supported_periodic_form_count": sum(1 for record in filings.filings if record.form_type in SUPPORTED_PERIODIC_FORMS),
        "xbrl_periodic_form_count": sum(
            1
            for record in filings.filings
            if record.form_type in SUPPORTED_PERIODIC_FORMS and (record.is_xbrl or record.is_inline_xbrl)
        ),
        "prospectus_form_count": sum(1 for record in filings.filings if record.form_type in PROSPECTUS_FORMS),
        "registration_only_form_count": sum(1 for record in filings.filings if record.form_type in REGISTRATION_ONLY_FORMS),
    }


def _latest_filing(
    filings: tuple[SecFilingRecord, ...],
    *,
    allowed_forms: frozenset[str],
    require_xbrl: bool,
) -> SecFilingRecord | None:
    for record in filings:
        if record.form_type not in allowed_forms:
            continue
        if require_xbrl and not (record.is_xbrl or record.is_inline_xbrl):
            continue
        return record
    return None


def _filing_to_json(record: SecFilingRecord | None) -> dict[str, object] | None:
    if record is None:
        return None
    return {
        "form_type": record.form_type,
        "filing_date": record.filing_date.isoformat(),
        "accession_number": record.accession_number,
        "primary_document": record.primary_document,
        "primary_doc_description": record.primary_doc_description,
        "filing_url": record.filing_url,
        "filing_index_url": record.filing_index_url,
        "is_xbrl": record.is_xbrl,
        "is_inline_xbrl": record.is_inline_xbrl,
    }
