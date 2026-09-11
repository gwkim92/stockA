"""Two sequential installed-service runs with saved timer state and DB fingerprints."""
import json
import os
from pathlib import Path
import subprocess
import time

APP = Path('/opt/stockanalysis/app')
BASE = Path('/opt/stockanalysis/runtime/research-automation-20260911')
PYTHON = '/opt/stockanalysis/venv/bin/python'
UNIT = 'stockanalysis-operating-data-research-maintenance.service'


def capture(args):
    return subprocess.check_output(args, text=True, timeout=30).strip()


def main():
    assert (BASE / 'activation.json').is_file()
    assert not (BASE / 'canary-started.json').exists(), 'Inspect prior run before retry'
    timers = [row.split()[0] for row in capture(['systemctl', 'list-units', '--type=timer',
              '--state=active', '--plain', '--no-legend', 'stockanalysis-*']).splitlines()]
    assert len(timers) == 14 and 'stockanalysis-operating-data-research-maintenance.timer' in timers
    (BASE / 'canary-started.json').write_text(json.dumps({'timers': timers}) + '\n')
    env = {**os.environ, 'PYTHONPATH': str(APP / 'src')}
    verify = [PYTHON, str(APP / 'docs/tasks/research-automation-20260911/verify_runtime.py')]
    try:
        subprocess.run(['sudo', '-n', 'systemctl', 'stop', *timers], check=True, timeout=60)
        for attempt in range(60):
            active = capture(['systemctl', 'list-units', '--type=service', '--state=running,activating',
                              '--plain', '--no-legend', 'stockanalysis-operating-data-*'])
            if not active:
                break
            if attempt == 59:
                raise RuntimeError('Existing operating-data job is still active; no replay')
            time.sleep(10)
        subprocess.run([*verify, 'before'], env=env, check=True, timeout=180)
        for cycle in (1, 2):
            print(f'cycle {cycle} starting', flush=True)
            subprocess.run(['sudo', '-n', 'systemctl', 'start', UNIT], check=True, timeout=900)
            print(capture(['systemctl', 'show', UNIT, '--property=Result,ExecMainStatus,MemoryPeak,CPUUsageNSec']), flush=True)
        subprocess.run([*verify, 'after'], env=env, check=True, timeout=180)
    finally:
        subprocess.run(['sudo', '-n', 'systemctl', 'start', *timers], check=True, timeout=60)
        restored = all(capture(['systemctl', 'is-active', timer]) == 'active' for timer in timers)
        (BASE / 'canary-timers-restored.json').write_text(json.dumps({'timers_restored': restored, 'count': len(timers)}) + '\n')
        print(json.dumps({'timers_restored': restored, 'count': len(timers)}), flush=True)


if __name__ == '__main__':
    main()
