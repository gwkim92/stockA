"""Collect safe final evidence after the guarded canary; no model calls."""
import json
import os
from pathlib import Path
import runpy
import subprocess
import urllib.request

from stockanalysis.operations.operating_data_orchestrator import build_operating_data_run_report

APP = Path('/opt/stockanalysis/app')
BASE = Path('/opt/stockanalysis/runtime/research-source-refresh-20260911')


if __name__=='__main__':
    helpers = runpy.run_path(str(BASE/'verify_server.py'))
    os.environ.update(helpers['load_env_file_values'](BASE.parent/'data-operations.env'))
    health = helpers['api']('/api/data-health')
    guard = health['scheduler']['profile_scheduler']['batch_runtime']
    assert guard['status']=='protected' and guard['protected_profile_count']==13
    assert guard['monitored_profile_count']==13 and guard['attention_profile_count']==0
    model = next(row for row in helpers['inventory']()['workloads'] if row['task']=='ai-equity-research-reporting')
    latest = model.get('latest') or {}
    canary = json.loads((BASE/'canary-verification.json').read_text())
    html_checks = {}
    for port in (3000, 13000):
        with urllib.request.urlopen('http://127.0.0.1:'+str(port)+'/stocks/'+canary['symbol'], timeout=60) as response:
            html = response.read().decode()
            html_checks[str(port)] = {'status': response.status,
                'financial_version_current_rendered': '보고서의 재무 입력 버전이 현재 수집 자료와 일치합니다.' in html}
            assert response.status==200
            if canary['actual_generation_verified']:
                assert html_checks[str(port)]['financial_version_current_rendered']
    plan = build_operating_data_run_report(repo_root=APP, runtime_root=BASE.parent,
        data_operations_env_file=BASE.parent/'data-operations.env', profile='research-maintenance', execute=False)
    steps = [row['step_id'] for row in plan['planned_steps']]
    assert steps==['research-maintenance', 'equity-research-reporting']
    result = {'activation': json.loads((BASE/'activation.json').read_text()), 'canary': canary,
        'batch_guard': guard, 'overall_data_health': health['overall_status'],
        'current_model': {key: latest.get(key) for key in ('status', 'requested_model', 'selected_model', 'actual_model', 'reasoning_effort')},
        'effective_model': model['effective_model'], 'server_rendered_html': html_checks, 'maintenance_steps': steps,
        'memory': subprocess.check_output(['free','-m'],text=True).strip()}
    (BASE/'final-verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))
