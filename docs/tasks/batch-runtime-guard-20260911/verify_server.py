"""Small transient-unit failures, then two real research cycles with DB fingerprints."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

APP = Path('/opt/stockanalysis/app')
BASE = Path('/opt/stockanalysis/runtime/batch-guard-20260911')
STATUS = 'stockanalysis-operating-data-scheduler-status.service'


def capture(args):
    return subprocess.check_output(args, text=True, timeout=30).strip()


def probes():
    result = {}
    for port, path in ((8787, '/__ready'), (3000, '/data-health'), (13000, '/data-health')):
        with urllib.request.urlopen(f'http://127.0.0.1:{port}{path}', timeout=30) as response:
            assert response.status == 200
            result[str(port)] = response.status
    return result


def main():
    assert (BASE / 'activation.json').exists()
    assert not (BASE / 'canary-started.json').exists(), 'Inspect canary checkpoint before retry'
    timers = [row.split()[0] for row in capture(['systemctl', 'list-units', '--type=timer', '--state=active',
                 '--plain', '--no-legend', 'stockanalysis-*']).splitlines()]
    assert len(timers) == 14
    (BASE / 'canary-started.json').write_text(json.dumps({'timers': timers}) + '\n')
    result = {'before_probes': probes(), 'smokes': []}
    try:
        subprocess.run(['sudo', '-n', 'systemctl', 'stop', *timers], check=True, timeout=60)
        assert not capture(['systemctl', 'list-units', '--type=service', '--state=running,activating',
                            '--plain', '--no-legend', 'stockanalysis-operating-data-*'])
        for label, code, deadline, expected in (
            ('timeout', 'import time; time.sleep(60)', '2', 'timeout'),
            ('memory', 'import time; x=bytearray(160*1024*1024); time.sleep(2)', '15', 'oom-kill'),
        ):
            unit = 'stockanalysis-batch-guard-' + label + '-check'
            command = ['sudo', '-n', 'systemd-run', '--unit=' + unit, '--wait', '--quiet',
                '-p', 'Type=oneshot', '-p', 'Slice=stockanalysis-batch.slice', '-p', 'MemoryMax=64M',
                '-p', 'MemorySwapMax=0', '-p', 'OOMPolicy=kill', '-p', 'TimeoutStartSec=' + deadline,
                '-p', 'TimeoutStopSec=2', '-p', 'KillMode=control-group', '/usr/bin/python3', '-c', code]
            run = subprocess.run(command, capture_output=True, text=True, timeout=45)
            observed = capture(['systemctl', 'show', unit, '--property=Result,ExecMainStatus,MemoryMax,ControlGroup'])
            properties = dict(row.split('=', 1) for row in observed.splitlines() if '=' in row)
            result['smokes'].append({'kind': label, 'returncode': run.returncode, 'properties': properties,
                                     'web_api_probes': probes()})
            (BASE / 'canary-smokes.json').write_text(json.dumps(result, indent=2) + '\n')
            assert run.returncode != 0 and properties['Result'] == expected, properties
            assert properties['MemoryMax'] == str(64 * 1024**2)
            subprocess.run(['sudo', '-n', 'systemctl', 'reset-failed', unit], check=True)
        cgroup = capture(['systemctl', 'show', 'stockanalysis-batch.slice', '--property=ControlGroup', '--value'])
        group = Path('/sys/fs/cgroup') / cgroup.lstrip('/')
        result['kernel_limits'] = {name: (group / name).read_text().strip() for name in ('memory.max', 'memory.high', 'memory.swap.max', 'cpu.max', 'pids.max')}
        assert result['kernel_limits']['memory.max'] == str(2 * 1024**3)
        assert result['kernel_limits']['memory.swap.max'] == '0'
        quota, period = map(int, result['kernel_limits']['cpu.max'].split())
        assert quota == period
        sys.path.insert(0, str(APP / 'src'))
        spec = importlib.util.spec_from_file_location('research_verify', APP / 'docs/tasks/research-automation-20260911/verify_runtime.py')
        verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier)
        verifier.BASE = BASE
        sys.argv = ['verify', 'before']
        verifier.main()
        for cycle in (1, 2):
            print('research cycle', cycle, flush=True)
            subprocess.run(['sudo', '-n', 'systemctl', 'start', 'stockanalysis-operating-data-research-maintenance.service'], check=True, timeout=900)
            result['after_cycle_' + str(cycle)] = probes()
        sys.argv = ['verify', 'after']
        verifier.main()
    finally:
        subprocess.run(['sudo', '-n', 'systemctl', 'start', *timers], check=True, timeout=60)
        result['timers_restored'] = all(capture(['systemctl', 'is-active', timer]) == 'active' for timer in timers)
        (BASE / 'canary-result.json').write_text(json.dumps(result, indent=2) + '\n')
    subprocess.run(['sudo', '-n', 'systemctl', 'start', STATUS], check=True, timeout=60)
    from stockanalysis.operations.env_file import load_env_file_values
    env = load_env_file_values(BASE.parent / 'frontend-api.env')
    request = urllib.request.Request('http://127.0.0.1:8787/api/data-health',
        headers={'Authorization': 'Bearer ' + env['STOCKANALYSIS_FRONTEND_API_READ_TOKEN']})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)['data']
    scheduler = data['scheduler']['profile_scheduler']
    guard = scheduler['batch_runtime']
    assert guard['status'] == 'protected', guard
    assert guard['monitored_profile_count'] == guard['protected_profile_count'] == 13, guard
    assert guard['attention_profile_count'] == 0, guard
    research = next(timer['runtime_guard'] for timer in scheduler['timers'] if timer['profile_id'] == 'research-maintenance')
    assert research['status'] == 'succeeded' and research['completed_steps'] == 1, research
    result['api_guard'] = guard
    result['research_progress'] = research
    result['overall_data_health'] = data['overall_status']
    result['verified'] = True
    (BASE / 'canary-result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
