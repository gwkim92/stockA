"""Backend-only activation; the verified web artifact and runtime config stay intact."""
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
import time

APP = Path('/opt/stockanalysis/app')
BASE = Path('/opt/stockanalysis/runtime/operations-query-cost-20260913')

def capture(*args):
    return subprocess.check_output(args, text=True, timeout=60).strip()

def run(*args):
    subprocess.run(args, check=True, timeout=120)

def save(name, value):
    (BASE/name).write_text(json.dumps(value, indent=2)+'\n')

def main():
    expected = sys.argv[1]
    assert len(expected) == 40 and all(c in '0123456789abcdef' for c in expected)
    identity = runpy.run_path(str(APP/'docs/tasks/research-automation-20260911/activate.py'))['identity']()
    BASE.mkdir(mode=0o700, exist_ok=True)
    assert not (BASE/'activation-started.json').exists(), 'Inspect checkpoint before retry'
    assert capture('git','-C',str(APP),'branch','--show-current') == 'develop'
    assert not capture('git','-C',str(APP),'status','--porcelain','--untracked-files=no')
    previous = capture('git','-C',str(APP),'rev-parse','HEAD')
    run('git','-C',str(APP),'fetch','origin','develop')
    assert capture('git','-C',str(APP),'rev-parse','FETCH_HEAD') == expected
    run('git','-C',str(APP),'merge-base','--is-ancestor',previous,expected)
    run('git','-C',str(APP),'diff','--exit-code',previous,expected,'--','db','apps/web','pyproject.toml')
    run('git','-C',str(APP),'archive','--format=tar.gz','--output='+str(BASE/'previous-source.tar.gz'),previous)
    settings = {name:hashlib.sha256((BASE.parent/name).read_bytes()).hexdigest()
                for name in ('frontend-api.env','web.env','data-operations.env','ai-model-settings.sqlite3')}
    build = (APP/'apps/web/.next/BUILD_ID').read_text().strip()
    timers = [line.split()[0] for line in capture('systemctl','list-units','--type=timer','--state=active','--plain','--no-legend','stockanalysis-*').splitlines()]
    assert len(timers) == 14
    save('activation-started.json',dict(previous=previous,expected=expected,timers=timers,settings=settings,identity=identity))
    try:
        run('sudo','-n','systemctl','stop',*timers)
        for attempt in range(31):
            if not capture('systemctl','list-units','--type=service','--state=running,activating','--plain','--no-legend','stockanalysis-operating-data-*'): break
            if attempt == 30: raise RuntimeError('Active batch; inspect before retry')
            time.sleep(1)
        run('git','-C',str(APP),'pull','--ff-only','origin','develop')
        assert capture('git','-C',str(APP),'rev-parse','HEAD') == expected
        run('sudo','-n','systemctl','restart','stockanalysis-frontend-api.service')
    finally:
        run('sudo','-n','systemctl','start',*timers)
    assert (APP/'apps/web/.next/BUILD_ID').read_text().strip() == build
    assert all(hashlib.sha256((BASE.parent/name).read_bytes()).hexdigest()==digest for name,digest in settings.items())
    assert all(capture('systemctl','is-active',timer)=='active' for timer in timers)
    save('activation.json',dict(identity=identity,previous=previous,commit=expected,web_build_unchanged=build,settings_unchanged=True,timers_restored=14))
    print((BASE/'activation.json').read_text())

if __name__ == '__main__': main()
