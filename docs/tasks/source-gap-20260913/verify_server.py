"""Collect at most the three proven gaps; never generate reports in this canary."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

APP = Path('/opt/stockanalysis/app')
BASE = Path('/opt/stockanalysis/runtime/source-gap-20260913')
TARGETS = {'AAPL', 'ARM', 'NVDA'}

def save(name, value):
    (BASE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str)+'\n')

def main():
    if '--restore-timers' in sys.argv:
        checkpoint = BASE/'canary-started.json'
        if checkpoint.exists():
            timers = json.loads(checkpoint.read_text())['timers']
            assert len(timers)==14 and all(t.startswith('stockanalysis-operating-data-') and t.endswith('.timer') for t in timers)
            subprocess.run(['sudo','-n','systemctl','start',*timers],check=True,timeout=60)
        return
    from stockanalysis.operations.research_maintenance import run_research_maintenance
    from stockanalysis.operations.operating_data_orchestrator import _resolve_market_price_ledger
    v = runpy.run_path(str(APP/'docs/tasks/research-source-refresh-20260911/verify_server.py'))
    identity = runpy.run_path(str(APP/'docs/tasks/research-automation-20260911/activate.py'))['identity']()
    env = v['load_env_file_values'](BASE.parent/'data-operations.env')
    os.environ.update(env)
    config = v['RuntimeConfig'].from_env()
    db = v['PsqlCommandExecutor'].from_config(config)
    root = _resolve_market_price_ledger(env,runtime_path=BASE.parent,repo_root=APP).parent/'research-automation-artifacts'
    assert (root/'research-maintenance/worker.lock').exists()
    day = datetime.now(timezone.utc).date()
    assert not (BASE/'canary-started.json').exists(), 'Inspect saved evidence before replay'
    plan = run_research_maintenance(config=config,as_of_date=day,artifact_root=root,executor=db)
    due = [row for row in plan['queue'] if row['state']=='due']
    assert {row['primary_symbol'] for row in due} == TARGETS
    ids = ','.join(str(int(row['instrument_id'])) for row in due)
    timers = [line.split()[0] for line in v['capture'](['systemctl','list-units','--type=timer','--state=active','--plain','--no-legend','stockanalysis-*']).splitlines()]
    assert len(timers)==14
    queries = {table:'select * from '+table for table in (
        'signal.recommendation','signal.recommendation_score_component','portfolio.position_snapshot',
        'ref.benchmark_composition','performance.recommendation_outcome','research.equity_research_artifact')}
    queries['other_periods']='select * from market.financial_statement_period where instrument_id not in ('+ids+')'
    queries['other_metrics']='select m.* from market.financial_metric_value m join market.financial_statement_period p using(period_id) where p.instrument_id not in ('+ids+')'
    queries['other_or_historical_normalized']="select * from market.financial_metric_normalized where instrument_id not in ("+ids+") or as_of_date <> date '"+str(day)+"'"
    def hashes():
        return {key:db.execute_scalar("select md5(coalesce(string_agg(h,',' order by h),'')) from (select md5(to_jsonb(r)::text) h from ("+query+") r) hashes;") for key,query in queries.items()}
    save('canary-started.json',dict(identity=identity,timers=timers,targets=sorted(TARGETS),day=str(day)))
    try:
        subprocess.run(['sudo','-n','systemctl','stop',*timers],check=True,timeout=60)
        assert not v['capture'](['systemctl','list-units','--type=service','--state=running,activating','--plain','--no-legend','stockanalysis-operating-data-*'])
        before = hashes()
        model_before = hashlib.sha256((BASE.parent/'ai-model-settings.sqlite3').read_bytes()).hexdigest()
        invocations_before = db.execute_scalar('select count(*) from ai.model_invocation;')
        first = run_research_maintenance(config=config,as_of_date=day,artifact_root=root,executor=db,execute=True)
        save('first.json',first)
        assert first['status']=='completed', first
        assert {row['symbol'] for row in first['results']}==TARGETS
        assert all(row['status']=='succeeded' for row in first['results'])
        repeat = run_research_maintenance(config=config,as_of_date=day,artifact_root=root,executor=db,execute=True)
        save('repeat.json',repeat)
        assert repeat['status']=='completed' and not repeat['results']
        assert hashes()==before
        assert db.execute_scalar('select count(*) from ai.model_invocation;')==invocations_before
        assert hashlib.sha256((BASE.parent/'ai-model-settings.sqlite3').read_bytes()).hexdigest()==model_before
        queue = v['api']('/api/data-health')['research_refresh']
        targets = [row for row in queue['rows'] if row['symbol'] in TARGETS]
        assert len(targets)==3 and all(row['source_run_id'] and row['state']=='due' for row in targets)
        save('verification.json',dict(identity=identity,verified_at=datetime.now(timezone.utc).isoformat(),
            commit=v['capture'](['git','-C',str(APP),'rev-parse','HEAD']),
            first=first,repeat=repeat,queue=queue,protected_table_hashes=before,protected_tables_unchanged=True,
            model_settings_unchanged=True,ai_invocations_unchanged=invocations_before))
        print(json.dumps({'status':'passed','collected':first['results'],'repeat_results':repeat['results'],
            'queue_counts':queue['counts'],'protected_tables_unchanged':True,'ai_invocations_unchanged':invocations_before}))
    finally:
        subprocess.run(['sudo','-n','systemctl','start',*timers],check=True,timeout=60)

if __name__ == '__main__': main()
