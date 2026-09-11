"""Bounded, same-host financial repair. Raw DB backups never leave the host.

Preview emits aggregate differences only. Execute is single-use and requires an
exact merged develop commit; it invokes existing ingestion/normalization services.
An interrupted execution must be inspected using its local checkpoint, not rerun.
"""
import argparse
from collections import Counter
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.ingest.sec.companyfacts import normalize_companyfacts_payload, run_sec_companyfacts_upsert
from stockanalysis.operations.env_file import load_env_file_values
from stockanalysis.operations.professional_equity_analysis import run_financial_metric_normalization

BASE = Path('/opt/stockanalysis/runtime/financial-period-integrity-20260911')
APP = Path('/opt/stockanalysis/app')
SYMBOLS = ('ARM', 'AAPL', 'NVDA')
SERVICES = ['stockanalysis-frontend-api.service','stockanalysis-web.service','stockanalysis-web-public-13000.service']
DAY = date(2026,9,11)


def capture(args):
    return subprocess.check_output(args,text=True).strip()


def run(args):
    subprocess.run(args,check=True,stdout=subprocess.DEVNULL)


def persist(name, value):
    (BASE/name).write_text(json.dumps(value,ensure_ascii=False,default=str,indent=2)+'\n')


def identity():
    request=urllib.request.Request('http://169.254.169.254/latest/api/token',method='PUT',headers={'X-aws-ec2-metadata-token-ttl-seconds':'60'})
    with urllib.request.urlopen(request,timeout=3) as response:
        token=response.read().decode()
    request=urllib.request.Request('http://169.254.169.254/latest/dynamic/instance-identity/document',headers={'X-aws-ec2-metadata-token':token})
    with urllib.request.urlopen(request,timeout=3) as response:
        actual=json.load(response)
    assert (actual['accountId'],actual['instanceId'],actual['region'])==('115623963546','i-029d51b163fb07b61','us-east-1')
    return {key:actual[key] for key in ('accountId','instanceId','region')}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--commit')
    args=parser.parse_args()
    os.umask(0o077)
    ident=identity()
    os.environ.update(load_env_file_values('/opt/stockanalysis/runtime/data-operations.env'))
    os.environ['PGOPTIONS']='-c statement_timeout=60000' + ('' if args.execute else ' -c default_transaction_read_only=on')
    config=RuntimeConfig.from_env()
    db=PsqlCommandExecutor.from_config(config)
    raw=json.loads((BASE/'companyfacts.json').read_text())

    def rows(query):
        return json.loads(db.execute_scalar("select coalesce(jsonb_agg(t),'[]'::jsonb)::text from ("+query+") t;"))

    instruments=rows("select instrument_id,primary_symbol from ref.instrument where primary_symbol in ('ARM','AAPL','NVDA')")
    assert len(instruments)==3 and {i['primary_symbol'] for i in instruments}==set(SYMBOLS)
    ids={i['primary_symbol']:i['instrument_id'] for i in instruments}
    ids_sql=','.join(str(i) for i in ids.values())
    period_query=f"select * from market.financial_statement_period where instrument_id in ({ids_sql})"
    metric_query=f"select m.* from market.financial_metric_value m join market.financial_statement_period p using(period_id) where p.instrument_id in ({ids_sql})"
    old_periods=rows(period_query)
    old_metrics=rows(metric_query)
    preview={}
    selected={}
    for symbol in SYMBOLS:
        result=normalize_companyfacts_payload(raw['samples'][symbol])
        selected[symbol]=result
        existing={(p['statement_scope'],p['period_end']):p for p in old_periods if p['instrument_id']==ids[symbol]}
        proposed={}
        for value in result.values:
            proposed.setdefault((value.statement_scope,value.period_end.isoformat()),[]).append(value)
        changed_year=0
        removed=0
        changed_duration=0
        for key,values in proposed.items():
            old=existing.get(key)
            if old:
                changed_year+=old['fiscal_year']!=values[0].fiscal_year
                changed_duration+=old['period_start']!=values[0].period_start.isoformat()
                codes={v.metric_code for v in values}
                removed+=sum(m['period_id']==old['period_id'] and m['metric_code'] not in codes for m in old_metrics)
        preview[symbol]={'selected_periods':len(proposed),'selected_facts':len(result.values),
                         'new_periods':len(set(proposed)-set(existing)), 'corrected_fiscal_years':changed_year,
                         'corrected_duration_starts':changed_duration,'removed_incompatible_metrics':removed,
                         'latest_annual_end':max(v.period_end for v in result.values if v.statement_scope=='annual').isoformat(),
                         'exclusion_counts':dict(Counter(f['exclusion_reason'] for f in result.excluded_facts))}
    report={'observed_at':datetime.now(timezone.utc).isoformat(),'identity':ident,'preview':preview,
            'database_writes':False,'raw_database_exported':False,'manual_model_calls':0}
    if not args.execute:
        print(json.dumps(report,ensure_ascii=False))
        return

    assert DAY==datetime.now(timezone.utc).date(),'Review the intended observation date before execution'
    assert args.commit and len(args.commit)==40 and all(c in '0123456789abcdef' for c in args.commit)
    assert capture(['git','-C',str(APP),'rev-parse','HEAD'])==args.commit,'Deploy the reviewed develop commit first'
    assert capture(['git','-C',str(APP),'branch','--show-current'])=='develop'
    assert not (BASE/'started.json').exists(),'Single-use pilot: inspect existing checkpoint, never replay'
    assert not capture(['git','-C',str(APP),'status','--porcelain','--untracked-files=no'])
    timers=[line.split()[0] for line in capture(['systemctl','list-units','--type=timer','--state=active','--plain','--no-legend','stockanalysis-*']).splitlines()]
    env_files=[BASE.parent/name for name in ('frontend-api.env','web.env','data-operations.env','ai-model-settings.sqlite3')]
    def settings_hash():
        return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in env_files}
    settings_before=settings_hash()
    started=False
    stopped=False
    try:
        if timers:
            run(['sudo','-n','systemctl','stop',*timers])
        assert not capture(['systemctl','list-units','--type=service','--state=running,activating','--plain','--no-legend','stockanalysis-operating-data-*']),'Wait for active batch before beginning'
        run(['sudo','-n','systemctl','stop',*SERVICES]);stopped=True
        today=rows(f"select * from market.financial_metric_normalized where instrument_id in ({ids_sql}) and as_of_date='{DAY}'")
        assert not today,'Preserve existing day snapshots; review a new repair plan'
        # Re-read under quiescence. Backups stay on this same host with mode 0600.
        persist('raw-before.json',{'periods':rows(period_query),'metrics':rows(metric_query),'normalized_today':today})
        protected=['signal.recommendation','signal.recommendation_score_component','portfolio.position_snapshot',
                   'ref.benchmark_composition','performance.recommendation_outcome','research.equity_research_artifact']
        def fingerprints():
            result={}
            queries={table:'select * from '+table for table in protected}
            queries['earlier_or_other_normalized']=f"select * from market.financial_metric_normalized where as_of_date < '{DAY}' or instrument_id not in ({ids_sql})"
            queries['other_periods']=f"select * from market.financial_statement_period where instrument_id not in ({ids_sql})"
            queries['other_raw_metrics']=f"select m.* from market.financial_metric_value m join market.financial_statement_period p using(period_id) where p.instrument_id not in ({ids_sql})"
            for key,query in queries.items():
                result[key]=db.execute_scalar("select md5(coalesce(string_agg(h,',' order by h),'')) from (select md5(to_jsonb(r)::text) h from ("+query+") r) hashes;")
            return result
        before=fingerprints()
        persist('protected-before.json',before)
        persist('started.json',{'commit':args.commit,'as_of_date':DAY,'identity':ident,'active_timers':timers,
                               'source_sha256':hashlib.sha256((BASE/'companyfacts.json').read_bytes()).hexdigest()})
        started=True
        completed=[]
        for symbol in SYMBOLS:
            source=BASE/(symbol+'-companyfacts.json')
            source.write_text(json.dumps(raw['samples'][symbol]))
            summary=run_sec_companyfacts_upsert(selected[symbol].cik,config=config,companyfacts_json_path=str(source),fallback_symbol=symbol)
            completed.append({'symbol':symbol,'run_id':summary['run_id'],'fact_count':summary['fact_count']})
            persist('checkpoint.json',{'imports':completed,'normalization_completed':False})
        normalized=run_financial_metric_normalization(config=config,as_of_date=DAY,symbols=SYMBOLS,execute=True)
        persist('checkpoint.json',{'imports':completed,'normalization_completed':True,'normalization_run_id':normalized['run_id']})
        checks=rows(f"select i.primary_symbol,n.period_end,n.metric_value,n.metric_status from market.financial_metric_normalized n join ref.instrument i using(instrument_id) where n.as_of_date='{DAY}' and ((i.primary_symbol='ARM' and n.period_end='2026-03-31' and n.metric_code='revenue_growth_yoy') or (i.primary_symbol='AAPL' and n.period_end='2026-06-27' and n.metric_code='operating_cash_flow_margin') or (i.primary_symbol='NVDA' and n.period_end='2026-07-26' and n.metric_code='operating_cash_flow_margin'))")
        assert len(checks)==3
        for row in checks:
            if row['primary_symbol']=='ARM':
                assert row['metric_status']=='computed' and abs(row['metric_value']-(4920/4007-1))<1e-7
            else:
                assert row['metric_status']=='unavailable' and row['metric_value'] is None
        assert before==fingerprints(),'Protected data changed: inspect before any retry'
        assert settings_before==settings_hash(),'Settings changed: inspect'
        report.update(database_writes=True,commit=args.commit,imports=completed,normalization_run_id=normalized['run_id'],
                      protected_tables_unchanged=True,settings_unchanged=True,financial_assertions_passed=True,
                      backup_location=str(BASE/'raw-before.json'))
        persist('completed.json',report)
    except BaseException as exc:
        if started:
            persist('attention.json',{'error_type':type(exc).__name__,'inspect_checkpoint_before_retry':True})
        raise
    finally:
        if stopped:
            run(['sudo','-n','systemctl','start',*SERVICES])
        if timers:
            run(['sudo','-n','systemctl','start',*timers])
    assert all(capture(['systemctl','is-active',service])=='active' for service in SERVICES)
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':
    main()
