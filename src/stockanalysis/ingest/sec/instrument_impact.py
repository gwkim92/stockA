from __future__ import annotations

import json
import re
from dataclasses import dataclass

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor, PsqlExecutionError
from stockanalysis.ingest.sec.models import (
    EventInstrumentImpactBootstrapResult,
    SecEventInstrumentImpactCandidate,
)
from stockanalysis.ingest.sec.sql import (
    render_event_instrument_impact_upsert_sql,
    render_instrument_lookup_by_company_name_sql,
    render_pending_sec_event_instrument_candidates_sql,
)

_TITLE_COMPANY_RE = re.compile(r":\s*(?P<company>.+?)\s*$")
_SUMMARY_COMPANY_RE = re.compile(r"^(?P<company>.+?) filed SEC Form ", re.IGNORECASE)


@dataclass(frozen=True)
class _ResolvedInstrument:
    instrument_id: int
    primary_symbol: str
    instrument_name: str
    issuer_display_name: str
    issuer_legal_name: str


_DEFAULT_IMPACT = {
    "impact_direction": "neutral",
    "impact_strength": 0.6,
    "confidence": 0.85,
}

_EVENT_TYPE_TO_IMPACT = {
    "sec_annual_report_filed": {
        "impact_direction": "neutral",
        "impact_strength": 0.75,
        "confidence": 0.95,
    },
    "sec_quarterly_report_filed": {
        "impact_direction": "neutral",
        "impact_strength": 0.7,
        "confidence": 0.94,
    },
    "sec_current_report_filed": {
        "impact_direction": "neutral",
        "impact_strength": 0.8,
        "confidence": 0.93,
    },
    "sec_proxy_statement_filed": {
        "impact_direction": "neutral",
        "impact_strength": 0.6,
        "confidence": 0.92,
    },
}


def run_event_instrument_impact_bootstrap(
    *,
    config: RuntimeConfig,
    limit: int = 20,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    candidates = load_pending_sec_event_instrument_candidates(limit=limit, executor=sql_executor)
    if not candidates:
        return {
            "run_id": None,
            "requested_event_count": 0,
            "succeeded_event_count": 0,
            "failed_event_count": 0,
            "results": [],
        }

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="event_instrument_impact_bootstrap",
        config_json={
            "limit": limit,
            "requested_event_count": len(candidates),
        },
    )
    succeeded = 0
    failed = 0
    results: list[dict[str, object]] = []
    try:
        for candidate in candidates:
            try:
                company_name = extract_company_name_from_event(candidate)
                instrument = resolve_instrument_for_company(company_name, executor=sql_executor)
                impact = _EVENT_TYPE_TO_IMPACT.get(candidate.event_type, _DEFAULT_IMPACT)
                sql_executor.execute_non_query(
                    render_event_instrument_impact_upsert_sql(
                        event_id=candidate.event_id,
                        instrument_id=instrument.instrument_id,
                        impact_direction=str(impact["impact_direction"]),
                        impact_strength=float(impact["impact_strength"]),
                        confidence=float(impact["confidence"]),
                        rationale=(
                            f"SEC event `{candidate.event_type}` for {company_name} maps to canonical "
                            f"instrument {instrument.primary_symbol}."
                        ),
                    )
                )
            except Exception as exc:
                failed += 1
                results.append(
                    EventInstrumentImpactBootstrapResult(
                        event_id=candidate.event_id,
                        event_type=candidate.event_type,
                        instrument_id=None,
                        instrument_symbol=None,
                        status="failed",
                        run_id=run_id,
                        error=str(exc),
                    ).summary()
                )
                continue

            succeeded += 1
            results.append(
                EventInstrumentImpactBootstrapResult(
                    event_id=candidate.event_id,
                    event_type=candidate.event_type,
                    instrument_id=instrument.instrument_id,
                    instrument_symbol=instrument.primary_symbol,
                    status="succeeded",
                    run_id=run_id,
                ).summary()
            )

        if failed:
            _mark_pipeline_run_failed(
                sql_executor,
                run_id,
                f"{failed} event instrument impact bootstrap operations failed",
            )
        else:
            _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return {
        "run_id": run_id,
        "requested_event_count": len(candidates),
        "succeeded_event_count": succeeded,
        "failed_event_count": failed,
        "results": results,
    }


def load_pending_sec_event_instrument_candidates(
    *,
    limit: int,
    executor: PsqlCommandExecutor,
) -> tuple[SecEventInstrumentImpactCandidate, ...]:
    payload_text = executor.execute_scalar(render_pending_sec_event_instrument_candidates_sql(limit=limit))
    payload = json.loads(payload_text)
    return tuple(
        SecEventInstrumentImpactCandidate(
            event_id=int(item["event_id"]),
            event_type=str(item["event_type"]),
            dedupe_key=item.get("dedupe_key"),
            title=str(item["title"]),
            summary=str(item["summary"]),
        )
        for item in payload
    )


def extract_company_name_from_event(candidate: SecEventInstrumentImpactCandidate) -> str:
    title_match = _TITLE_COMPANY_RE.search(candidate.title)
    if title_match:
        company = title_match.group("company").strip()
        if company:
            return company
    summary_match = _SUMMARY_COMPANY_RE.search(candidate.summary)
    if summary_match:
        company = summary_match.group("company").strip()
        if company:
            return company
    raise ValueError(f"Could not extract company name from event `{candidate.event_id}`.")


def resolve_instrument_for_company(
    company_name: str,
    *,
    executor: PsqlCommandExecutor,
) -> _ResolvedInstrument:
    try:
        payload_text = executor.execute_scalar(render_instrument_lookup_by_company_name_sql(company_name))
    except PsqlExecutionError as exc:
        raise ValueError(f"No canonical instrument found for company `{company_name}`.") from exc
    payload = json.loads(payload_text)
    return _ResolvedInstrument(
        instrument_id=int(payload["instrument_id"]),
        primary_symbol=str(payload["primary_symbol"]),
        instrument_name=str(payload["instrument_name"]),
        issuer_display_name=str(payload["issuer_display_name"]),
        issuer_legal_name=str(payload["issuer_legal_name"]),
    )


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
    truncated = error_summary.strip()[:2000] or "event instrument impact bootstrap failed"
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
