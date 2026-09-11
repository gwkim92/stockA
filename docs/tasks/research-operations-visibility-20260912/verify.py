"""Read back the live queue, duplicate-free GETs, services and recovery evidence."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import urllib.request

APP = Path('/opt/stockanalysis/app')
BASE = Path('/opt/stockanalysis/runtime/research-operations-visibility-20260912')


def main():
    v = runpy.run_path(str(APP/'docs/tasks/research-source-refresh-20260911/verify_server.py'))
    v['os'].environ.update(v['load_env_file_values'](BASE.parent/'data-operations.env'))
    db = v['PsqlCommandExecutor'].from_config(v['RuntimeConfig'].from_env())
    sql = "select jsonb_build_object('claims',(select count(*) from ops.pipeline_run where pipeline_name='equity_source_refresh'),'invocations',(select count(*) from ai.model_invocation))::text;"
    before = json.loads(db.execute_scalar(sql))
    model_path = BASE.parent/'ai-model-settings.sqlite3'
    model_before = hashlib.sha256(model_path.read_bytes()).hexdigest()
    first = v['api']('/api/data-health')
    status = first['research_refresh']
    second = v['api']('/api/data-health')['research_refresh']
    assert status['status'] in ('loaded','attention_required'), status
    assert status['read_only'] and status['scope']=='financial_source_only'
    assert status['daily_limit']==5 and status['total_count']==len(status['rows'])
    assert sum(status['counts'].values())==status['total_count']
    assert status['rows']==second['rows'] and status['daily_used']==second['daily_used']
    assert before==json.loads(db.execute_scalar(sql)), 'Concurrent producer or unexpected mutation; inspect'
    assert hashlib.sha256(model_path.read_bytes()).hexdigest()==model_before
    planned = v['run_research_report_refresh'](config=v['RuntimeConfig'].from_env(),executor=db,
        as_of_date=datetime.now(timezone.utc).date())
    assert [(r['symbol'],r['state']) for r in status['rows']]==[(r['primary_symbol'],r['state']) for r in planned['queue']]
    guard = first['scheduler']['profile_scheduler']['batch_runtime']
    assert guard['status']=='protected' and guard['protected_profile_count']==13 and guard['attention_profile_count']==0
    timers = subprocess.check_output(['systemctl','list-units','--type=timer','--state=active','--plain','--no-legend','stockanalysis-*'],text=True).splitlines()
    assert len(timers)==14
    html = {}
    for port in (3000,13000):
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/data-health',timeout=30) as response:
            body=response.read().decode(); assert response.status==200 and '보고서 갱신 현황' in body
            html[str(port)]={'status':response.status,'research_refresh_rendered':True}
    recovery=json.loads((BASE.parent/'operating-data-profile-scheduler-reports/decision-daily-operating-data-run.json').read_text())
    summary={key:recovery.get(key) for key in ('generated_at','run_status','failed_step_count','broker_submission_allowed')}
    summary['steps']=[{key:r.get(key) for key in ('step_id','status','exit_code')} for r in recovery.get('artifact_runs',[])]
    result={'verified_at':datetime.now(timezone.utc).isoformat(),
        'commit':subprocess.check_output(['git','-C',str(APP),'rev-parse','HEAD'],text=True).strip(),
        'research_refresh':status,'matches_worker_queue':True,'repeated_get_no_claim_or_invocation':True,
        'model_settings_unchanged':True,'read_counts':before,'timer_count':len(timers),'batch_guard':guard,
        'html':html,'recovery':summary,'overall_status':first['overall_status'],
        'open_gates':first.get('open_gate_details',[]),
        'stale_or_failed_jobs':[r for r in first['pipeline_runs'] if r.get('health_status') in ('stale','missing','failed','stale_running')]}
    (BASE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:val for k,val in result.items() if k not in ('research_refresh','open_gates')},ensure_ascii=False))
    print(json.dumps({'counts':status['counts'],'daily_used':status['daily_used'],'remaining_gates':[g['gate_id'] for g in result['open_gates']]},ensure_ascii=False))


if __name__=='__main__': main()
