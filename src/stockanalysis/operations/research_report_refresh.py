"""Reserve one changed financial source before invoking the existing report path.

Reservations survive process/DB acknowledgement loss. Unknown outcomes never replay;
confirmed failed calls with stored fallback results can retry after 24 hours.
The advisory transaction lock coordinates this runner across hosts; the original
reporting pipeline records the claim ID so the existing daily budget is counted once.
"""
from __future__ import annotations

from datetime import date
import json
import re
from typing import Any

from stockanalysis.ai import equity_research_reporting as equity
from stockanalysis.ai.equity_research_batch import EquityResearchBatchError
from stockanalysis.ai.equity_research_persistence import reconcile_result, _fingerprint
from stockanalysis.ai.model_settings import inventory
from stockanalysis.ai.research_source_version import latest_source_sql, validated_version, generation_policy as source_policy
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor

PIPELINE = 'equity_source_refresh'
POLICY = 'financial-source-report-refresh-v1'
DAILY_LIMIT = 5


def generation_policy(model: str, reasoning: str = 'low') -> str:
    return source_policy(model=model, template=equity.DEFAULT_TEMPLATE_VERSION, reasoning=reasoning,
                         context_limit=equity.DEFAULT_MAX_CONTEXT_CHARS)


def _queue_ctes(as_of_date: date, policy: str, symbol: str | None = None) -> str:
    return f"""tracked as (
    select i.instrument_id, i.primary_symbol from ref.instrument i
    where i.is_active and i.market_code='US'
      {('and i.primary_symbol=' + sql_literal(symbol)) if symbol else ''}
      and lower(i.instrument_type) not in ('etf','fund','index','mutual_fund')
      and i.name !~* '(ETF|ETN|Index Fund|Invesco QQQ|SPDR.*Trust)'
      and (exists(select 1 from signal.recommendation r join signal.recommendation_batch b using(batch_id)
          where r.instrument_id=i.instrument_id and r.status='active' and b.as_of_date <= {sql_date(as_of_date)})
        or exists(select 1 from portfolio.position_snapshot p where p.instrument_id=i.instrument_id
          and p.snapshot_date <= {sql_date(as_of_date)}))
), sources as (
    select i.*, s.*, encode(sha256(convert_to(i.instrument_id::text || '|' || s.source_sha256 || '|'
        || s.period_policy || '|' || {sql_literal(policy)}, 'UTF8')), 'hex') as generation_key
    from tracked i left join lateral ({latest_source_sql('i.instrument_id')}) s on true
), queue as (
    select s.*, coalesce(pending.run_id, previous.run_id) as previous_claim_id,
        coalesce(pending.status, previous.status) as previous_status,
        previous.ended_at as previous_claim_ended_at,
        case when previous.status='failed' and previous.config_json->'result_receipt'->>'outcome'='fallback'
            then previous.ended_at + interval '24 hours' end as retry_after,
        coalesce(pending.config_json,previous.config_json)->>'failure_code' as failure_code,
        case when s.source_run_id is null then 'waiting_for_source'
             when exists(select 1 from ops.pipeline_run pending where pending.pipeline_name='{PIPELINE}'
                and pending.config_json->>'instrument_id'=s.instrument_id::text and pending.status='running') then 'reconcile'
             when exists(select 1 from research.equity_research_artifact a
                join ops.pipeline_run g on g.run_id=a.source_run_id
                cross join lateral jsonb_each(case when jsonb_typeof(g.config_json->'equity_result_receipts_v1')='object'
                    then g.config_json->'equity_result_receipts_v1' else '{{}}'::jsonb end) receipt
                join ai.model_invocation inv on inv.run_id=g.run_id and inv.request_hash=receipt.key
                where a.instrument_id=s.instrument_id and a.artifact_type='full_equity_research'
                  and a.provider='codex_oauth' and inv.status='succeeded'
                  and receipt.value->>'outcome'='primary'
                  and receipt.value->>'result_fingerprint'={_fingerprint('a')}
                  and receipt.value->>'invocation_fingerprint'={_fingerprint('inv')}
                  and g.config_json->>'source_generation_policy'={sql_literal(policy)}
                  and g.config_json->'financial_source_versions'->s.primary_symbol->>'source_sha256'=s.source_sha256
                  and g.config_json->'financial_source_versions'->s.primary_symbol->>'period_policy'=s.period_policy
             ) then 'current'
             when previous.status='succeeded' then 'result_changed'
             when previous.status='failed' and previous.config_json->'result_receipt'->>'outcome'='fallback'
                  and previous.ended_at <= now()-interval '24 hours' then 'due'
             when previous.status='failed' and previous.config_json->'result_receipt'->>'outcome'='fallback' then 'retry_wait'
             when previous.run_id is not null then 'attempt_recorded'
             else 'due' end as state
    from sources s left join lateral (
        select r.run_id,r.status,r.config_json from ops.pipeline_run r where r.pipeline_name='{PIPELINE}'
          and r.config_json->>'instrument_id'=s.instrument_id::text and r.status='running'
        order by r.run_id desc limit 1
    ) pending on true left join lateral (
        select r.run_id,r.status,r.ended_at,r.config_json from ops.pipeline_run r where r.pipeline_name='{PIPELINE}'
          and r.config_json->>'generation_key'=s.generation_key order by r.run_id desc limit 1
    ) previous on true
), budget as (
    select (select count(*) from ops.pipeline_run r where r.pipeline_name='{PIPELINE}'
              and r.config_json->>'as_of_date'={sql_literal(as_of_date.isoformat())})
      + (select coalesce(sum(case when jsonb_typeof(r.config_json->'symbols')='array'
                then jsonb_array_length(r.config_json->'symbols') else {DAILY_LIMIT} end),0)
         from ops.pipeline_run r where r.pipeline_name='equity_research_reporting'
           and r.config_json->>'provider'='codex_oauth'
           and r.config_json->>'as_of_date'={sql_literal(as_of_date.isoformat())}
           and not (coalesce(r.config_json,'{{}}'::jsonb) ? 'source_refresh_claim_id')) as used
)"""


def render_queue_sql(*, as_of_date: date, policy: str, symbol: str | None = None) -> str:
    return f"""-- research source refresh queue
with {_queue_ctes(as_of_date, policy, symbol)}
select jsonb_build_object('daily_used',(select used from budget),'daily_limit',{DAILY_LIMIT},
    'queue',coalesce((select jsonb_agg(to_jsonb(q) order by ended_at,primary_symbol) from queue q),'[]'))::text;"""


def render_reservation_sql(*, as_of_date: date, policy: str, model: str, symbol: str | None = None) -> str:
    # Lock in a separate statement so READ COMMITTED takes a *new* snapshot after
    # waiting. A lock and queue selection in one statement would see old claims.
    return f"""-- reserve research source refresh
begin;
set local lock_timeout='5s';
set local statement_timeout='15s';
select pg_advisory_xact_lock(728431962);
with {_queue_ctes(as_of_date, policy, symbol)}, selected as (
    select q.* from queue q where state='due' and (select used from budget)<{DAILY_LIMIT}
      and (now() at time zone 'UTC')::date={sql_date(as_of_date)}
    order by ended_at,primary_symbol limit 1
), reserved as (
    insert into ops.pipeline_run(run_kind,pipeline_name,status,config_json)
    select 'ai','{PIPELINE}','running', jsonb_build_object(
        'policy','{POLICY}','as_of_date',{sql_literal(as_of_date.isoformat())},
        'instrument_id',instrument_id,'symbol',primary_symbol,'generation_key',generation_key,
        'generation_policy',{sql_literal(policy)},'model_name',{sql_literal(model)},
        'source_version',jsonb_build_object('source_run_id',source_run_id,
            'source_sha256',source_sha256,'period_policy',period_policy))
    from selected returning run_id,config_json
)
select jsonb_build_object('claim',(select jsonb_build_object('run_id',run_id,'request',config_json) from reserved),
    'daily_used',(select used from budget),'daily_limit',{DAILY_LIMIT})::text;
commit;"""


def _finish(db: Any, claim_id: int, *, status: str, details: dict[str, Any]) -> None:
    if status not in ('succeeded', 'failed'):
        raise ValueError('invalid_refresh_terminal_status')
    db.execute_non_query(f"""update ops.pipeline_run set status={sql_literal(status)},ended_at=now(),
        config_json=config_json || {sql_literal(json.dumps(details))}::jsonb
        where run_id={int(claim_id)} and pipeline_name='{PIPELINE}' and status='running';""")


def _reconcile_pending(db: Any) -> list[dict[str, Any]]:
    # A confirmed committed receipt can close a lost coordinator response.
    # No receipt (including a still-active call) never authorizes another call.
    raw = db.execute_scalar(f"""-- pending research source refresh receipts
select coalesce(jsonb_agg(to_jsonb(t)),'[]')::text from (
    select p.run_id as claim_id,c.run_id as child_run_id,c.config_json->'equity_result_receipts_v1' as receipts
    from ops.pipeline_run p left join ops.pipeline_run c
      on c.pipeline_name='equity_research_reporting'
      and c.config_json->>'source_refresh_claim_id'=p.run_id::text
    where p.pipeline_name='{PIPELINE}' and p.status='running'
    order by (c.config_json->'equity_result_receipts_v1' is null),p.run_id limit 50) t;""")
    observations = []
    for row in json.loads(raw):
        receipts = row.get('receipts')
        if not isinstance(receipts, dict) or len(receipts) != 1:
            observations.append({'claim_id': row['claim_id'], 'status': 'reconcile'})
            continue
        request_hash = next(iter(receipts))
        observed = reconcile_result(db, run_id=row['child_run_id'], request_hash=request_hash)
        if observed['status'] != 'matching':
            observations.append({'claim_id': row['claim_id'], 'status': 'reconcile'})
            continue
        receipt = observed['receipt']
        status = 'succeeded' if receipt['outcome'] == 'primary' else 'failed'
        _finish(db, row['claim_id'], status=status, details={'result_receipt': receipt,
            'child_run_id': row['child_run_id'], 'reconciled': True})
        observations.append({'claim_id': row['claim_id'], 'status': status})
    return observations


def run_research_report_refresh(*, config: Any, as_of_date: date, execute: bool = False,
                               executor: Any = None, report_runner: Any = None,
                               model_name: str | None = None, symbol: str | None = None) -> dict[str, Any]:
    if type(as_of_date) is not date:
        raise ValueError('invalid_refresh_date')
    if symbol is not None and (not isinstance(symbol, str) or not re.fullmatch(r'[A-Z0-9][A-Z0-9.-]{0,19}', symbol)):
        raise ValueError('invalid_refresh_symbol')
    db = executor or PsqlCommandExecutor.from_config(config)
    if model_name is None:
        settings = inventory()
        workload = next((item for item in settings['workloads'] if item['task'] == equity.DEFAULT_TASK_NAME), {})
        model_name = workload.get('effective_model') or equity.DEFAULT_MODEL_NAME
    policy = generation_policy(model_name)
    report = {'pipeline_name': PIPELINE, 'policy': POLICY, 'as_of_date': as_of_date.isoformat(),
        'execute': execute, 'model_name': model_name, 'generation_policy': policy, 'daily_limit': DAILY_LIMIT, 'maximum_calls_per_run': 1,
        'recommendation_scoring_mutated': False, 'broker_submit_allowed': False,
        'order_boundary': 'read_only_no_order'}
    if not execute:
        return {**report, 'status': 'planned', **json.loads(db.execute_scalar(render_queue_sql(as_of_date=as_of_date, policy=policy, symbol=symbol)))}
    if db.execute_scalar("select (now() at time zone 'UTC')::date;") != as_of_date.isoformat():
        raise ValueError('Refresh execute requires the current UTC date')
    report['reconciliation'] = _reconcile_pending(db)
    report['attention_required'] = any(row['status'] == 'reconcile' for row in report['reconciliation'])
    reserved = json.loads(db.execute_scalar(render_reservation_sql(as_of_date=as_of_date, policy=policy, model=model_name, symbol=symbol)))
    report['daily_used_before'] = reserved['daily_used']
    claim = reserved['claim']
    if claim is None:
        return {**report, 'status': 'reconcile' if report['attention_required'] else
                'daily_limit' if reserved['daily_used'] >= DAILY_LIMIT else 'no_op', 'provider_attempted': False}
    claim_id, request = claim['run_id'], claim['request']
    report.update(claim_id=claim_id, symbol=request['symbol'], generation_key=request['generation_key'])
    source_version = validated_version(request['source_version'])
    runner = report_runner or equity.run_equity_research_reporting
    try:
        child = runner(config=config, as_of_date=as_of_date, symbols=(request['symbol'],), limit=1,
            provider=equity.CODEX_OAUTH_PROVIDER, model_name=model_name, reasoning_effort='low', execute=True,
            executor=db, source_refresh_claim={'claim_id': claim_id, 'source_version': source_version})
        result = child['results'][0]
        receipt = result.get('result_receipt')
        if not receipt:
            raise ValueError('Refresh child did not return a stored result receipt')
        observed = reconcile_result(db, run_id=child['run_id'], request_hash=receipt['request_hash'])
        if observed['status'] != 'matching' or observed['receipt'] != receipt:
            raise ValueError('Refresh stored result could not be reconciled')
        status = 'succeeded' if receipt['outcome'] == 'primary' else 'failed'
        _finish(db, claim_id, status=status, details={'child_run_id': child['run_id'], 'result_receipt': receipt})
        return {**report, 'status': status, 'child_run_id': child['run_id'],
                'result_receipt': receipt, 'provider_attempted': result['provider_attempted']}
    except EquityResearchBatchError as exc:
        outcome_unknown = exc.report.get('fatal_error', {}).get('persistence_outcome_unknown', False)
        # Without a validated fallback receipt, this generation is not retried.
        if not outcome_unknown:
            _finish(db, claim_id, status='failed', details={'failure_code': 'report_not_completed',
                'child_run_id': exc.report.get('run_id')})
        return {**report, 'status': 'reconcile' if outcome_unknown else 'failed',
                'automatic_retry_allowed': False, 'error_code': 'report_not_completed'}
    except Exception:
        # Leave the durable reservation running. Do not guess whether the child
        # committed or whether a model response was received before disconnection.
        return {**report, 'status': 'reconcile', 'automatic_retry_allowed': False,
                'error_code': 'refresh_outcome_unknown'}
