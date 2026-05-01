from __future__ import annotations

import json
from dataclasses import dataclass

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.ingest.sec.models import (
    EventClassificationImpactBootstrapResult,
    SecEventImpactCandidate,
)
from stockanalysis.ingest.sec.sql import (
    render_event_classification_impact_upsert_sql,
    render_pending_sec_event_impact_candidates_sql,
    render_reporting_classification_bootstrap_sql,
)


@dataclass(frozen=True)
class _ImpactTarget:
    node_code: str
    node_type: str
    impact_direction: str
    impact_strength: float
    confidence: float
    rationale: str


_DEFAULT_IMPACT_TARGET = _ImpactTarget(
    node_code="PUBLIC_COMPANY_REPORTING",
    node_type="theme",
    impact_direction="neutral",
    impact_strength=0.5,
    confidence=0.85,
    rationale="SEC filing activity contributes to the public company reporting theme.",
)

_EVENT_TYPE_TO_IMPACT_TARGET: dict[str, _ImpactTarget] = {
    "sec_annual_report_filed": _ImpactTarget(
        node_code="ANNUAL_REPORTING",
        node_type="subtheme",
        impact_direction="neutral",
        impact_strength=0.75,
        confidence=0.95,
        rationale="Annual report filings are direct evidence for the annual reporting cycle.",
    ),
    "sec_quarterly_report_filed": _ImpactTarget(
        node_code="QUARTERLY_REPORTING",
        node_type="subtheme",
        impact_direction="neutral",
        impact_strength=0.7,
        confidence=0.94,
        rationale="Quarterly report filings are direct evidence for the quarterly reporting cycle.",
    ),
    "sec_current_report_filed": _ImpactTarget(
        node_code="CURRENT_REPORTING",
        node_type="subtheme",
        impact_direction="neutral",
        impact_strength=0.8,
        confidence=0.93,
        rationale="Current report filings are direct evidence for current reporting activity.",
    ),
    "sec_proxy_statement_filed": _ImpactTarget(
        node_code="CORPORATE_GOVERNANCE",
        node_type="subtheme",
        impact_direction="neutral",
        impact_strength=0.6,
        confidence=0.92,
        rationale="Proxy statement filings are direct evidence for corporate governance activity.",
    ),
}


def run_event_classification_impact_bootstrap(
    *,
    config: RuntimeConfig,
    limit: int = 20,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    candidates = load_pending_sec_event_impact_candidates(limit=limit, executor=sql_executor)
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
        pipeline_name="event_classification_impact_bootstrap",
        config_json={
            "limit": limit,
            "requested_event_count": len(candidates),
        },
    )
    try:
        sql_executor.execute_non_query(render_reporting_classification_bootstrap_sql())
        results: list[dict[str, object]] = []
        succeeded = 0
        failed = 0

        for candidate in candidates:
            target = _EVENT_TYPE_TO_IMPACT_TARGET.get(candidate.event_type, _DEFAULT_IMPACT_TARGET)
            try:
                sql_executor.execute_non_query(
                    render_event_classification_impact_upsert_sql(
                        event_id=candidate.event_id,
                        node_code=target.node_code,
                        node_type=target.node_type,
                        impact_direction=target.impact_direction,
                        impact_strength=target.impact_strength,
                        confidence=target.confidence,
                        rationale=target.rationale,
                    )
                )
            except Exception as exc:
                failed += 1
                results.append(
                    EventClassificationImpactBootstrapResult(
                        event_id=candidate.event_id,
                        event_type=candidate.event_type,
                        node_code=target.node_code,
                        status="failed",
                        run_id=run_id,
                        error=str(exc),
                    ).summary()
                )
                continue

            succeeded += 1
            results.append(
                EventClassificationImpactBootstrapResult(
                    event_id=candidate.event_id,
                    event_type=candidate.event_type,
                    node_code=target.node_code,
                    status="succeeded",
                    run_id=run_id,
                ).summary()
            )

        if failed:
            _mark_pipeline_run_failed(
                sql_executor,
                run_id,
                f"{failed} event classification impact bootstrap operations failed",
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


def load_pending_sec_event_impact_candidates(
    *,
    limit: int,
    executor: PsqlCommandExecutor,
) -> tuple[SecEventImpactCandidate, ...]:
    payload_text = executor.execute_scalar(render_pending_sec_event_impact_candidates_sql(limit=limit))
    payload = json.loads(payload_text)
    return tuple(
        SecEventImpactCandidate(
            event_id=int(item["event_id"]),
            event_type=str(item["event_type"]),
            dedupe_key=item.get("dedupe_key"),
            title=str(item["title"]),
        )
        for item in payload
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
    truncated = error_summary.strip()[:2000] or "event classification impact bootstrap failed"
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
