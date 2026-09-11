"""Bounded, restart-safe SEC statement maintenance using existing tables.

The statement replacement, current-day normalization and completion receipt are
one PostgreSQL transaction. Backups stay on the executing host. A lost response
is reconciled by locking that receipt; it never triggers an immediate replay.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import date
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time
from uuid import uuid4

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.market.universe import load_market_universe_records
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.ingest.sec.companyfacts import _load_companyfacts_payload, normalize_companyfacts_payload
from stockanalysis.ingest.sec.financial_periods import PERIOD_POLICY
from stockanalysis.ingest.sec.sql import render_sec_companyfacts_upsert_sql, render_sec_filings_upsert_sql
from stockanalysis.ingest.sec.submissions import load_sec_filings_sync_result
from stockanalysis.operations.professional_equity_analysis import render_financial_metric_normalization_upsert_sql
from stockanalysis.signal.universe import _create_pipeline_run, _mark_pipeline_run_failed

PIPELINE = "research_statement_refresh"
JOB_PIPELINE = "research_maintenance"
POLICY = "research-maintenance-v1"


def render_queue_sql(*, as_of_date: date) -> str:
    return f"""-- research maintenance queue (tracked US companies only)
with tracked as (
    select distinct i.instrument_id, i.primary_symbol
    from ref.instrument i
    where i.is_active and i.market_code = 'US'
      and lower(i.instrument_type) not in ('etf', 'fund', 'index', 'mutual_fund')
      and i.name !~* '(ETF|ETN|Index Fund|Invesco QQQ|SPDR.*Trust)'
      and (exists (select 1 from signal.recommendation r
           join signal.recommendation_batch b using(batch_id)
           where r.instrument_id=i.instrument_id and r.status='active' and b.as_of_date <= {sql_date(as_of_date)})
           or exists (select 1 from portfolio.position_snapshot p
                      where p.instrument_id=i.instrument_id and p.snapshot_date <= {sql_date(as_of_date)}))
), queue as (
    select t.*, last_run.status as last_status, last_run.started_at as last_attempt,
           last_good.ended_at as last_success,
           case when last_run.status='running' then 'reconcile'
                when last_run.status='failed' and last_run.started_at > now()-interval '24 hours' then 'retry_wait'
                when last_good.ended_at > now()-interval '7 days' then 'fresh'
                else 'due' end as state
    from tracked t
    left join lateral (select status,started_at from ops.pipeline_run r
        where r.pipeline_name={sql_literal(PIPELINE)}
          and r.config_json->>'instrument_id'=t.instrument_id::text
        order by run_id desc limit 1) last_run on true
    left join lateral (select ended_at from ops.pipeline_run r
        where r.pipeline_name in ({sql_literal(PIPELINE)},'sec_companyfacts_upsert') and r.status='succeeded'
          and r.config_json->>'instrument_id'=t.instrument_id::text
          and r.config_json->>'period_policy'={sql_literal(PERIOD_POLICY)}
          and (r.pipeline_name={sql_literal(PIPELINE)} or exists (
              select 1 from market.financial_metric_normalized n
              join ops.pipeline_run nr on nr.run_id=n.source_run_id
              where n.instrument_id=t.instrument_id and nr.status='succeeded'
                and nr.ended_at >= r.ended_at
          ))
        order by ended_at desc nulls last limit 1) last_good on true
)
select coalesce(jsonb_agg(to_jsonb(q) order by last_success nulls first, last_attempt nulls first, primary_symbol),'[]'::jsonb)::text
from queue q;"""


def render_reconcile_sql(run_id: int) -> str:
    # If the applying connection is still alive this fails NOWAIT, preserving
    # the unresolved state. Once its row lock is gone, succeeded proves commit;
    # running proves that the entire mutation transaction rolled back.
    return f"""begin;
select run_id from ops.pipeline_run where run_id={int(run_id)} for update nowait;
update ops.pipeline_run set status='failed', ended_at=now(), error_summary='interrupted_before_atomic_commit'
where run_id={int(run_id)} and pipeline_name={sql_literal(PIPELINE)} and status='running';
select status from ops.pipeline_run where run_id={int(run_id)};
commit;"""


def render_apply_sql(*, result, filings, instrument_id: int, symbol: str,
                     as_of_date: date, run_id: int) -> str:
    iid, rid = int(instrument_id), int(run_id)
    # Locks also serialize with legacy weekly writers that do not know about
    # this worker's file lock. The before-image stays in the same database;
    # this also works when psql runs inside the existing PostgreSQL container.
    backup_query = f"""select jsonb_build_object(
        'periods',(select coalesce(jsonb_agg(p),'[]') from market.financial_statement_period p where instrument_id={iid}),
        'metrics',(select coalesce(jsonb_agg(m),'[]') from market.financial_metric_value m join market.financial_statement_period p using(period_id) where p.instrument_id={iid}),
        'normalized_today',(select coalesce(jsonb_agg(n),'[]') from market.financial_metric_normalized n where instrument_id={iid} and as_of_date={sql_date(as_of_date)}))"""
    return f"""begin;
set local lock_timeout='10s';
set local statement_timeout='120s';
select run_id from ops.pipeline_run where run_id={rid} for update;
do $$ begin
 if not exists(select 1 from ops.pipeline_run where run_id={rid} and status='running') then
  raise exception 'maintenance_receipt_not_running';
 end if;
end $$;
lock table market.financial_statement_period, market.financial_metric_value,
    market.financial_metric_normalized in share row exclusive mode;
update ops.pipeline_run set config_json=jsonb_set(config_json,'{{backup_before}}',({backup_query})) where run_id={rid};
{render_sec_filings_upsert_sql(filings, ingested_by_run_id=rid, include_transaction=False)}
{render_sec_companyfacts_upsert_sql(result, instrument_id=iid, source_run_id=rid, include_transaction=False)}
{render_financial_metric_normalization_upsert_sql(as_of_date=as_of_date,source_run_id=rid,symbols=(symbol,))}
do $$ begin
 if not exists(select 1 from market.financial_metric_normalized where source_run_id={rid} and instrument_id={iid}) then
  raise exception 'maintenance_normalization_empty';
 end if;
end $$;
update ops.pipeline_run set status='succeeded', ended_at=now(), error_summary=null where run_id={rid};
commit;
"""


@contextmanager
def maintenance_lock(root: Path):
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (root / "worker.lock").open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def run_research_maintenance(*, config: RuntimeConfig, as_of_date: date,
                             artifact_root: Path, limit: int = 3, execute: bool = False,
                             executor=None) -> dict:
    if type(limit) is not int or not 1 <= limit <= 3:
        raise ValueError("Maintenance limit must be between 1 and 3")
    db = executor or PsqlCommandExecutor.from_config(config)
    report = {"pipeline_name": JOB_PIPELINE, "policy": POLICY, "period_policy": PERIOD_POLICY,
              "as_of_date": as_of_date.isoformat(), "execute": execute, "results": [],
              "order_boundary": "read_only_no_order", "automatic_weight_change_allowed": False,
              "refresh_days": 7, "retry_hours": 24, "limit": limit}
    if not execute:
        report.update(status="planned", queue=json.loads(db.execute_scalar(render_queue_sql(as_of_date=as_of_date))))
        return report
    # Scheduled maintenance always observes today; historical snapshots are not
    # overwritten by a backdated scheduler invocation.
    today = db.execute_scalar("select (now() at time zone 'UTC')::date;")
    if as_of_date.isoformat() != today:
        raise ValueError("Maintenance execute requires the current UTC date")
    root = Path(artifact_root).resolve() / "research-maintenance"
    try:
        with maintenance_lock(root):
            batch_id = _create_pipeline_run(db, pipeline_name=JOB_PIPELINE,
                config_json={"policy": POLICY, "as_of_date": as_of_date.isoformat()})
            report["run_id"] = batch_id
            try:
                result = _run_locked(db, config, as_of_date, root, limit, report)
                status = "failed" if result["status"] == "attention" else "succeeded"
                db.execute_non_query(f"update ops.pipeline_run set status={sql_literal(status)}, ended_at=now(), config_json=config_json || {sql_literal(json.dumps(result))}::jsonb where run_id={batch_id};")
                return result
            except BaseException:
                _mark_pipeline_run_failed(db, batch_id, "maintenance_batch_interrupted_or_failed")
                raise
    except BlockingIOError:
        report.update(status="already_running")
        return report


def _run_locked(db, config, as_of_date, root, limit, report):
    pending = json.loads(db.execute_scalar(f"select coalesce(jsonb_agg(run_id),'[]')::text from ops.pipeline_run where pipeline_name={sql_literal(PIPELINE)} and status='running';"))
    for run_id in pending:
        try:
            status = db.execute_scalar(render_reconcile_sql(run_id))
        except Exception:
            status = "reconcile_pending"
        report["results"].append({"run_id": run_id, "status": status, "reconciled": True})
    queue = json.loads(db.execute_scalar(render_queue_sql(as_of_date=as_of_date)))
    candidates = [row for row in queue if row["state"] == "due"][:limit]
    report["queue_counts"] = {state: sum(row["state"] == state for row in queue)
                              for state in ("due", "fresh", "retry_wait", "reconcile")}
    # Fetch the free identity mapping only when there is work.
    mapping = {r.symbol: r for r in load_market_universe_records(config=config)} if candidates else {}
    for target in candidates:
        symbol, iid = target["primary_symbol"], target["instrument_id"]
        run_id = _create_pipeline_run(db, pipeline_name=PIPELINE, config_json={
            "instrument_id": iid, "instrument_symbol": symbol, "as_of_date": as_of_date.isoformat(),
            "policy": POLICY, "period_policy": PERIOD_POLICY})
        row = {"symbol": symbol, "run_id": run_id}
        report["results"].append(row)
        try:
            record = mapping.get(symbol)
            if record is None:
                raise ValueError("sec_identity_unavailable")
            attempt = root / f"{run_id}-{uuid4().hex}"
            attempt.mkdir(mode=0o700)
            raw = _load_companyfacts_payload(record.cik, config=config, json_path=None)
            raw_bytes = json.dumps(raw, ensure_ascii=False, allow_nan=False).encode()
            source = attempt / "companyfacts.json"
            source.write_bytes(raw_bytes)
            result = normalize_companyfacts_payload(raw)
            if result.cik != record.cik or not result.values or result.period_policy != PERIOD_POLICY:
                raise ValueError("sec_statement_identity_or_facts_invalid")
            time.sleep(0.25)
            filings = load_sec_filings_sync_result(record.cik, config=config, max_filings=200)
            evidence = {"cik": record.cik, "source_sha256": hashlib.sha256(raw_bytes).hexdigest(),
                        "source_path": str(source), "backup_reference": f"ops.pipeline_run:{run_id}:backup_before",
                        "fact_count": len(result.values),
                        "selected_facts": [{"metric_code": v.metric_code, **(v.source_evidence or {})} for v in result.values],
                        "excluded_facts": list(result.excluded_facts)}
            db.execute_non_query(f"update ops.pipeline_run set config_json=config_json || {sql_literal(json.dumps(evidence,default=str))}::jsonb where run_id={run_id};")
            db.execute_non_query(render_apply_sql(result=result, filings=filings, instrument_id=iid,
                symbol=symbol, as_of_date=as_of_date, run_id=run_id))
            row.update(status="succeeded", fact_count=len(result.values))
        except Exception as exc:
            # Includes confirmed source errors and lost commit acknowledgements.
            # Reconcile the row before declaring failure or allowing a later retry.
            try:
                status = db.execute_scalar(render_reconcile_sql(run_id))
            except Exception:
                status = "reconcile_pending"
            code = "source_or_validation_failed" if isinstance(exc, ValueError) else "collection_or_storage_failed"
            row.update(status=status, error_code=code)
            if status == "failed":
                _mark_pipeline_run_failed(db, run_id, code)
            if status == "succeeded":
                row.update(reconciled=True)
                row.pop("error_code", None)
        time.sleep(0.25)
    report["failed_count"] = sum(r["status"] in ("failed", "reconcile_pending") and not r.get("reconciled") for r in report["results"])
    report["reconcile_pending_count"] = sum(r["status"] == "reconcile_pending" for r in report["results"])
    report["status"] = "attention" if report["failed_count"] or report["reconcile_pending_count"] else "completed"
    report["queue_counts_after"] = {state: 0 for state in ("due", "fresh", "retry_wait", "reconcile")}
    for row in json.loads(db.execute_scalar(render_queue_sql(as_of_date=as_of_date))):
        report["queue_counts_after"][row["state"]] += 1
    # Safe summary only; source records and backup files remain below root.
    temp = root / "status.tmp"
    temp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    os.replace(temp, root / "status.json")
    return report
