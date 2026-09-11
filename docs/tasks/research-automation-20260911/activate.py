"""Exact develop activation; build off-line, preserve runtime settings and backups."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

APP=Path('/opt/stockanalysis/app')
BASE=Path('/opt/stockanalysis/runtime/research-automation-20260911')
SERVICES=['stockanalysis-frontend-api.service','stockanalysis-web.service','stockanalysis-web-public-13000.service']


def capture(argv): return subprocess.check_output(argv,text=True).strip()
def run(argv,**kwargs): subprocess.run(argv,check=True,**kwargs)
def save(name,value): (BASE/name).write_text(json.dumps(value,default=str,indent=2)+'\n')


def identity():
    req=urllib.request.Request('http://169.254.169.254/latest/api/token',method='PUT',headers={'X-aws-ec2-metadata-token-ttl-seconds':'60'})
    with urllib.request.urlopen(req,timeout=3) as r: token=r.read().decode()
    req=urllib.request.Request('http://169.254.169.254/latest/dynamic/instance-identity/document',headers={'X-aws-ec2-metadata-token':token})
    with urllib.request.urlopen(req,timeout=3) as r: data=json.load(r)
    assert (data['accountId'],data['instanceId'],data['region'])==('115623963546','i-029d51b163fb07b61','us-east-1')
    return {k:data[k] for k in ('accountId','instanceId','region')}


def main():
    expected=sys.argv[1]
    assert len(expected)==40 and all(c in '0123456789abcdef' for c in expected)
    ident=identity()
    os.umask(0o077); BASE.mkdir(exist_ok=True,mode=0o700)
    assert not (BASE/'activation.json').exists(),'Already activated; inspect saved evidence'
    assert not (BASE/'started.json').exists(),'Interrupted activation: inspect checkpoint before any replay'
    assert capture(['git','-C',str(APP),'branch','--show-current'])=='develop'
    assert not capture(['git','-C',str(APP),'status','--porcelain','--untracked-files=no'])
    previous=capture(['git','-C',str(APP),'rev-parse','HEAD'])
    run(['git','-C',str(APP),'fetch','origin','develop'])
    assert capture(['git','-C',str(APP),'rev-parse','FETCH_HEAD'])==expected
    run(['git','-C',str(APP),'merge-base','--is-ancestor',previous,expected])
    run(['git','-C',str(APP),'diff','--exit-code',previous,expected,'--','db/migrations','pyproject.toml','apps/web/package.json','apps/web/package-lock.json'])
    assert shutil.disk_usage(BASE).free>2_500_000_000
    env_paths=[BASE.parent/name for name in ('frontend-api.env','web.env','data-operations.env','ai-model-settings.sqlite3')]
    def hashes(): return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in env_paths}
    settings_before=hashes()
    stage=BASE/'build';stage.mkdir()
    archive=BASE/'web-source.tar'
    run(['git','-C',str(APP),'archive','--output='+str(archive),expected,'apps/web'])
    run(['tar','-xf',str(archive),'-C',str(stage)])
    web=stage/'apps/web'
    shutil.copytree(APP/'apps/web/node_modules',web/'node_modules',symlinks=True)
    sys.path.insert(0,str(APP/'src'))
    from stockanalysis.operations.env_file import load_env_file_values
    build_env=dict(os.environ);build_env.update(load_env_file_values(BASE.parent/'web.env'))
    with (BASE/'build.log').open('w') as log:
        run(['npm','run','build'],cwd=web,env=build_env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
    build_id=(web/'.next/BUILD_ID').read_text().strip()
    run(['git','-C',str(APP),'archive','--format=tar.gz','--output='+str(BASE/'previous-source.tar.gz'),previous])
    timers=[line.split()[0] for line in capture(['systemctl','list-units','--type=timer','--state=active','--plain','--no-legend','stockanalysis-*']).splitlines()]
    save('started.json',{'previous':previous,'expected':expected,'timers':timers,'identity':ident,'settings_hashes':settings_before})
    stopped=False
    try:
        if timers: run(['sudo','-n','systemctl','stop',*timers])
        assert not capture(['systemctl','list-units','--type=service','--state=running,activating','--plain','--no-legend','stockanalysis-operating-data-*']),'Wait for active operating-data batch'
        run(['sudo','-n','systemctl','stop',*SERVICES]);stopped=True
        run(['git','-C',str(APP),'pull','--ff-only','origin','develop'])
        assert capture(['git','-C',str(APP),'rev-parse','HEAD'])==expected
        (APP/'apps/web/.next').rename(BASE/'previous-next')
        (web/'.next').rename(APP/'apps/web/.next')
        from stockanalysis.operations.operating_data_profile_scheduler import build_operating_data_profile_scheduler_invocation_plan
        manifest=build_operating_data_profile_scheduler_invocation_plan(
            scheduler_target='systemd',repo_root=APP,runtime_root=BASE.parent,
            data_operations_env_file=BASE.parent/'data-operations.env',profile_ids=['research-maintenance'],
            manifest_output_root=BASE/'manifests',python_executable='/opt/stockanalysis/venv/bin/python',
            execute=True,systemd_user='ec2-user',systemd_group='ec2-user',systemd_home='/home/ec2-user')
        save('manifest-plan.json',manifest)
        for file in manifest['profiles'][0]['manifest_file_previews']:
            source=Path(file['path'])
            assert source.suffix in ('.service','.timer') and source.name.startswith('stockanalysis-operating-data-research-maintenance.')
            run(['sudo','-n','install','-m','644',str(source),'/etc/systemd/system/'+source.name])
        run(['sudo','-n','systemctl','daemon-reload'])
        run(['sudo','-n','systemctl','start',*SERVICES]);stopped=False
        run(['sudo','-n','systemctl','enable','--now','stockanalysis-operating-data-research-maintenance.timer'])
    except BaseException:
        save('attention.json',{'stage':'activation','expected':expected,'previous':previous,'inspect_before_retry':True})
        raise
    finally:
        if stopped: run(['sudo','-n','systemctl','start',*SERVICES])
        if timers: run(['sudo','-n','systemctl','start',*timers])
    for service in SERVICES: assert capture(['systemctl','is-active',service])=='active'
    for url in ('http://127.0.0.1:8787/__ready','http://127.0.0.1:3000/data-health','http://127.0.0.1:13000/data-health'):
        for attempt in range(30):
            try:
                with urllib.request.urlopen(url,timeout=15) as r: assert r.status==200
                break
            except Exception:
                if attempt==29: raise
                time.sleep(.5)
    assert settings_before==hashes(),'Runtime settings changed'
    result={'identity':ident,'previous_commit':previous,'commit':expected,'build_id':build_id,
            'services_active':True,'routes_200':True,'settings_unchanged':True,'schema_changed':False,
            'new_timer_active':capture(['systemctl','is-active','stockanalysis-operating-data-research-maintenance.timer'])=='active',
            'activated_at':datetime.now(timezone.utc).isoformat()}
    save('activation.json',result);print(json.dumps(result))


if __name__=='__main__': main()
