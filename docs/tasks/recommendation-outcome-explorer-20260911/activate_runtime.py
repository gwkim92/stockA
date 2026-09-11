"""Activate a prebuilt Linux artifact on the existing personal host; never edit env/model settings."""
import hashlib, json, os, pathlib, socket, sqlite3, subprocess, sys, tarfile, time, urllib.request
os.umask(0o077)
app=pathlib.Path('/opt/stockanalysis/app')
base=pathlib.Path('/opt/stockanalysis/runtime/recommendation-outcome-explorer-20260911')
artifact=base/'artifact'
services=['stockanalysis-frontend-api.service','stockanalysis-web.service','stockanalysis-web-public-13000.service']
def run(args, **kw): return subprocess.run(args,check=True,text=True,**kw)
def capture(args): return subprocess.check_output(args,text=True).strip()
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def persist(name,value): (base/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def model_settings():
    path=base.parent/'ai-model-settings.sqlite3'
    with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as db:
        revision,model,overrides=db.execute('select revision, default_model, overrides from settings where id=1').fetchone()
    return {'revision':revision,'default_model':model,'overrides':json.loads(overrides),'mode':oct(path.stat().st_mode & 0o777)}
def fingerprints():
    return {name:{'sha256':digest(base.parent/name),'mode':oct((base.parent/name).stat().st_mode & 0o777)} for name in ('frontend-api.env','web.env','data-operations.env')}
def identity():
    request=urllib.request.Request('http://169.254.169.254/latest/api/token',method='PUT',headers={'X-aws-ec2-metadata-token-ttl-seconds':'60'})
    with urllib.request.urlopen(request,timeout=3) as response: token=response.read().decode()
    request=urllib.request.Request('http://169.254.169.254/latest/dynamic/instance-identity/document',headers={'X-aws-ec2-metadata-token':token})
    with urllib.request.urlopen(request,timeout=3) as response: result=json.load(response)
    assert (result['accountId'],result['instanceId'],result['region'])==('115623963546','i-029d51b163fb07b61','us-east-1'),'wrong AWS identity'
    return {key:result[key] for key in ('accountId','instanceId','region')}
def get(url):
    with urllib.request.urlopen(url,timeout=20) as response: return response.status,response.read().decode()

def main():
    ident=identity()
    assert not (base/'activation.json').exists(),'already activated; do not replay'
    expected=(artifact/'COMMIT').read_text().strip()
    assert len(expected)==40 and all(c in '0123456789abcdef' for c in expected)
    archive_hash=digest(artifact/'web-runtime.tar.gz')
    assert archive_hash==(artifact/'SHA256SUMS').read_text().split()[0]
    assert capture(['git','-C',str(app),'branch','--show-current'])=='develop'
    assert not capture(['git','-C',str(app),'status','--porcelain','--untracked-files=no']),'tracked runtime edits exist'
    previous=capture(['git','-C',str(app),'rev-parse','HEAD'])
    run(['git','-C',str(app),'fetch','origin','develop'])
    target=capture(['git','-C',str(app),'rev-parse','FETCH_HEAD'])
    run(['git','-C',str(app),'merge-base','--is-ancestor',previous,target])
    run(['git','-C',str(app),'merge-base','--is-ancestor',expected,target])
    run(['git','-C',str(app),'diff','--exit-code',expected,target,'--','apps/web','src','pyproject.toml','db'])
    lock=capture(['git','-C',str(app),'show',target+':apps/web/package-lock.json'])+'\n'
    assert hashlib.sha256(lock.encode()).hexdigest()==(artifact/'PACKAGE_LOCK_SHA256').read_text().split()[0]
    assert not capture(['git','-C',str(app),'diff','--name-only',previous,target,'--','pyproject.toml','apps/web/package-lock.json','db/migrations']), 'dependency/schema changes require another deployment plan'
    stage=base/'artifact-stage';stage.mkdir(exist_ok=False)
    with tarfile.open(artifact/'web-runtime.tar.gz') as bundle:
        for member in bundle.getmembers():
            path=pathlib.PurePosixPath(member.name)
            assert not path.is_absolute() and '..' not in path.parts and path.parts[0]=='.next'
            assert member.isdir() or member.isfile(),'unsupported artifact entry'
        bundle.extractall(stage)
    assert (stage/'.next/BUILD_ID').read_text().strip()==(artifact/'BUILD_ID').read_text().strip()
    before_env=fingerprints();before_model=model_settings()
    timers=[line.split()[0] for line in capture(['systemctl','list-units','--type=timer','--state=active','--plain','--no-legend','stockanalysis-*']).splitlines()]
    assert all(capture(['systemctl','is-active',unit])=='active' for unit in services)
    backup=base/'previous-next'
    assert not backup.exists()
    run(['git','-C',str(app),'archive','--format=tar.gz','--output='+str(base/'previous-source.tar.gz'),previous])
    persist('preflight.json',{'identity':ident,'previous_commit':previous,'target_commit':target,'artifact_commit':expected,'artifact_sha256':archive_hash,'active_timers':timers,'settings':before_model,'env_fingerprints':before_env})
    (base/'previous-commit').write_text(previous+'\n')
    stopped=False;source_changed=False;swapped=False
    try:
        if timers: run(['sudo','-n','systemctl','stop',*timers])
        assert not capture(['systemctl','list-units','--type=service','--state=running,activating','--plain','--no-legend','stockanalysis-operating-data-*']),'batch still active; retry only after it finishes'
        run(['sudo','-n','systemctl','stop',*services]);stopped=True
        source_changed=True
        run(['git','-C',str(app),'pull','--ff-only','origin','develop'])
        assert capture(['git','-C',str(app),'rev-parse','HEAD'])==target,'develop changed during activation'
        (app/'apps/web/.next').rename(backup)
        (stage/'.next').rename(app/'apps/web/.next');swapped=True
        run(['sudo','-n','systemctl','start',*services]);stopped=False
        for port in (8787,3000,13000):
            deadline=time.monotonic()+40
            while time.monotonic()<deadline:
                try:
                    with socket.create_connection(('127.0.0.1',port),timeout=1): pass
                    break
                except OSError: time.sleep(0.5)
            else: raise RuntimeError('service did not listen on port '+str(port))
        ready=None
        for attempt in range(20):
            try:
                status,body=get('http://127.0.0.1:8787/__ready');ready=json.loads(body)
                if status==200 and ready.get('status')=='ok': break
            except Exception: pass
            time.sleep(1)
        assert ready and ready.get('status')=='ok','API readiness failed'
        statuses={}
        for port,path,phrase in [(3000,'/performance/recommendations','전체 추천 성과'),(3000,'/performance/recommendations?symbol=AAPL&horizon=30','추천별 측정 결과'),(3000,'/performance','판단 성과'),(13000,'/admin/ai-agents','AI 모델 설정')]:
            status,body=get('http://127.0.0.1:'+str(port)+path)
            assert status==200 and phrase in body, f'web smoke failed: {port}{path}'
            statuses[str(port)+path]=status
        assert before_env==fingerprints(),'runtime env changed during deploy'
        after_model=model_settings()
        assert before_model==after_model,'model settings changed during deploy'
        assert all(capture(['systemctl','is-active',unit])=='active' for unit in services)
        result={'identity':ident,'previous_commit':previous,'commit':target,'artifact_commit':expected,'build_id':(artifact/'BUILD_ID').read_text().strip(),'artifact_sha256':archive_hash,'api_ready':ready['status'],'web_statuses':statuses,'model_settings':after_model,'env_unchanged':True,'services_active':services,'rollback_backup':str(backup),'database_migrations':False,'manual_model_calls':0}
        persist('activation.json',result)
    except BaseException:
        if source_changed or swapped:
            run(['sudo','-n','systemctl','stop',*services]);stopped=True
            if backup.exists():
                if (app/'apps/web/.next').exists(): (app/'apps/web/.next').rename(base/'failed-next')
                backup.rename(app/'apps/web/.next')
            if source_changed:
                # Only undo this activation's clean fast-forward, never unrelated edits.
                assert not capture(['git','-C',str(app),'status','--porcelain','--untracked-files=no'])
                run(['git','-C',str(app),'reset','--hard',previous])
        if stopped: run(['sudo','-n','systemctl','start',*services])
        persist('rollback.json',{'restored_commit':capture(['git','-C',str(app),'rev-parse','HEAD']),'at':time.time()})
        raise
    finally:
        if timers: run(['sudo','-n','systemctl','start',*timers])
    restored=[unit for unit in timers if capture(['systemctl','is-active',unit])=='active']
    assert len(restored)==len(timers)
    result['restored_timers']=restored;persist('activation.json',result)
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__': main()
