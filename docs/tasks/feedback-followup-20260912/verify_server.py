"""Bounded deterministic production follow-ups, then no-op; retain all decisions."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

APP = Path('/opt/stockanalysis/app')
BASE = Path('/opt/stockanalysis/runtime/feedback-followup-20260912')

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
    v = runpy.run_path(str(APP/'docs/tasks/research-source-refresh-20260911/verify_server.py'))
    identity = runpy.run_path(str(APP/'docs/tasks/research-automation-20260911/activate.py'))['identity']()
    os.environ.update(v['load_env_file_values'](BASE.parent/'data-operations.env'))
    db = v['PsqlCommandExecutor'].from_config(v['RuntimeConfig'].from_env())
    assert not (BASE/'canary-started.json').exists(), 'Inspect saved result before replay'
    timers = [line.split()[0] for line in v['capture'](['systemctl','list-units','--type=timer','--state=active','--plain','--no-legend','stockanalysis-*']).splitlines()]
    assert len(timers)==14
    day = datetime.now(timezone.utc).date()
    save('canary-started.json',dict(timers=timers,identity=identity,day=str(day)))
    try:
        subprocess.run(['sudo','-n','systemctl','stop',*timers],check=True,timeout=60)
        assert not v['capture'](['systemctl','list-units','--type=service','--state=running,activating','--plain','--no-legend','stockanalysis-operating-data-*'])
        before = v['hashes'](db,None)
        model_before = hashlib.sha256((BASE.parent/'ai-model-settings.sqlite3').read_bytes()).hexdigest()
        ai_before = db.execute_scalar('select count(*) from ai.model_invocation;')
        command = [sys.executable,'-m','stockanalysis.operations.cli','portfolio-review-feedback-action-router-run',
            '--complete-follow-ups','--env-file',str(BASE.parent/'data-operations.env'),
            '--portfolio-name','Long Term Paper','--as-of-date',str(day),'--execute']
        reports = []
        for name in ('first','repeat'):
            output = BASE/(name+'.json')
            subprocess.run(command+['--output',str(output)],check=True,timeout=90)
            report = json.loads(output.read_text()); reports.append(report)
            assert report['status']=='completed', report
            assert report['rounds'][-1]['action']['action_status']=='no_op_calibration_current'
        assert all(r['action']['route_action']=='no_op' for r in reports[1]['rounds'])
        assert v['hashes'](db,None)==before
        assert db.execute_scalar('select count(*) from ai.model_invocation;')==ai_before
        assert hashlib.sha256((BASE.parent/'ai-model-settings.sqlite3').read_bytes()).hexdigest()==model_before
        live = v['api']('/api/data-health')
        details = {key:live[key] for key in ('portfolio_review_feedback_calibration','portfolio_review_feedback_cadence','portfolio_review_feedback_action_router')}
        assert details['portfolio_review_feedback_cadence']['cadence_status']=='calibration_current'
        save('verification.json',dict(verified_at=datetime.now(timezone.utc).isoformat(),identity=identity,
            commit=v['capture'](['git','-C',str(APP),'rev-parse','HEAD']),reports=reports,
            protected_table_hashes=before,protected_tables_unchanged=True,ai_invocations_unchanged=ai_before,
            model_settings_unchanged=True,live=details,open_gates=live.get('open_gate_details',[])))
        print(json.dumps({'first_actions':[r['action']['route_action'] for r in reports[0]['rounds']],
            'repeat_actions':[r['action']['route_action'] for r in reports[1]['rounds']],
            'protected_tables_unchanged':True,'ai_invocations_unchanged':ai_before},ensure_ascii=False))
    finally:
        subprocess.run(['sudo','-n','systemctl','start',*timers],check=True,timeout=60)

if __name__ == '__main__': main()
