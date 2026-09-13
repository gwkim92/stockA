"""Activate verified Linux output; preserve all scheduler/runtime configuration."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request

APP = Path('/opt/stockanalysis/app')
BASE = Path('/opt/stockanalysis/runtime/operations-state-clarity-20260913')
SERVICES = ['stockanalysis-frontend-api.service', 'stockanalysis-web.service', 'stockanalysis-web-public-13000.service']


def capture(*args):
    return subprocess.check_output(args, text=True, timeout=60).strip()


def run(*args):
    subprocess.run(args, check=True, timeout=120)


def save(name, value):
    (BASE/name).write_text(json.dumps(value, indent=2)+'\n')


def settings():
    return {name: hashlib.sha256((BASE.parent/name).read_bytes()).hexdigest() for name in
            ('frontend-api.env', 'web.env', 'data-operations.env', 'ai-model-settings.sqlite3')}


def main():
    expected = sys.argv[1]
    assert len(expected)==40 and all(c in '0123456789abcdef' for c in expected)
    spec = importlib.util.spec_from_file_location('previous_activation', APP/'docs/tasks/research-automation-20260911/activate.py')
    helpers = importlib.util.module_from_spec(spec); spec.loader.exec_module(helpers)
    identity = helpers.identity()
    BASE.mkdir(exist_ok=True, mode=0o700)
    assert not (BASE/'started.json').exists(), 'Inspect previous checkpoint before replay'
    assert capture('git','-C',str(APP),'branch','--show-current')=='develop'
    assert not capture('git','-C',str(APP),'status','--porcelain','--untracked-files=no')
    previous = capture('git','-C',str(APP),'rev-parse','HEAD')
    run('git','-C',str(APP),'fetch','origin','develop')
    assert capture('git','-C',str(APP),'rev-parse','FETCH_HEAD')==expected
    run('git','-C',str(APP),'merge-base','--is-ancestor',previous,expected)
    run('git','-C',str(APP),'diff','--exit-code',previous,expected,'--','db','pyproject.toml','apps/web/package.json','apps/web/package-lock.json')
    assert shutil.disk_usage(BASE).free > 2_500_000_000
    manifest = json.loads((BASE/'linux-build-manifest.json').read_text())
    assert manifest['platform']=='linux/amd64'
    assert manifest['web_tree']==capture('git','-C',str(APP),'rev-parse',expected+':apps/web')
    archive = BASE/'web-runtime.tar.gz'
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['sha256']
    lock = subprocess.check_output(['git','-C',str(APP),'show',expected+':apps/web/package-lock.json'])
    assert hashlib.sha256(lock).hexdigest()==manifest['package_lock_sha256']
    build = BASE/'offhost-build'; build.mkdir()
    with tarfile.open(archive) as tar:
        tar.extractall(build, filter='data')
    assert (build/'.next/BUILD_ID').read_text().strip()==manifest['build_id']
    run('git','-C',str(APP),'archive','--format=tar.gz','--output='+str(BASE/'previous-source.tar.gz'),previous)
    timers = [line.split()[0] for line in capture('systemctl','list-units','--type=timer','--state=active','--plain','--no-legend','stockanalysis-*').splitlines()]
    assert len(timers)==14
    before = settings()
    save('started.json', {'identity':identity,'previous':previous,'expected':expected,'timers':timers,'settings':before})
    stopped = False
    try:
        run('sudo','-n','systemctl','stop',*timers)
        for attempt in range(31):
            active = capture('systemctl','list-units','--type=service','--state=running,activating','--plain','--no-legend','stockanalysis-operating-data-*')
            if not active: break
            if attempt==30: raise RuntimeError('Operating batch still active; inspect before activating')
            time.sleep(1)
        run('sudo','-n','systemctl','stop',*SERVICES); stopped=True
        run('git','-C',str(APP),'pull','--ff-only','origin','develop')
        assert capture('git','-C',str(APP),'rev-parse','HEAD')==expected
        (APP/'apps/web/.next').rename(BASE/'previous-next')
        (build/'.next').rename(APP/'apps/web/.next')
        run('sudo','-n','systemctl','start',*SERVICES); stopped=False
    except BaseException:
        save('attention.json', {'inspect_before_retry':True,'previous':previous,'expected':expected})
        raise
    finally:
        if stopped: run('sudo','-n','systemctl','start',*SERVICES)
        run('sudo','-n','systemctl','start',*timers)
    for port,path in [(8787,'/__ready'),(3000,'/data-health'),(13000,'/data-health')]:
        for attempt in range(20):
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}{path}',timeout=20) as response: assert response.status==200
                break
            except Exception:
                if attempt==19: raise
                time.sleep(1)
    assert settings()==before
    for timer in timers: assert capture('systemctl','is-active',timer)=='active'
    save('activation.json', {'identity':identity,'commit':expected,'previous':previous,'build_id':manifest['build_id'],
        'settings_unchanged':True,'timers_restored':len(timers),'services_active':all(capture('systemctl','is-active',s)=='active' for s in SERVICES),
        'routes_200':True,'activated_at':datetime.now(timezone.utc).isoformat()})
    print((BASE/'activation.json').read_text())


if __name__=='__main__': main()
