"""Deploy an exact reviewed develop commit with no web/dependency/schema diff."""
import json
import subprocess
import sys
import time
import urllib.request

from runtime_pilot import APP, BASE, capture, identity, persist, run


def main():
    expected=sys.argv[1]
    assert len(expected)==40 and all(c in '0123456789abcdef' for c in expected)
    ident=identity()
    assert not (BASE/'backend-activation.json').exists(),'Already activated; inspect instead of replaying'
    assert capture(['git','-C',str(APP),'branch','--show-current'])=='develop'
    assert not capture(['git','-C',str(APP),'status','--porcelain','--untracked-files=no'])
    previous=capture(['git','-C',str(APP),'rev-parse','HEAD'])
    run(['git','-C',str(APP),'fetch','origin','develop'])
    assert capture(['git','-C',str(APP),'rev-parse','FETCH_HEAD'])==expected
    run(['git','-C',str(APP),'merge-base','--is-ancestor',previous,expected])
    run(['git','-C',str(APP),'diff','--exit-code',previous,expected,'--','apps/web','pyproject.toml','db/migrations'])
    run(['git','-C',str(APP),'archive','--format=tar.gz','--output='+str(BASE/'previous-source.tar.gz'),previous])
    timers=[line.split()[0] for line in capture(['systemctl','list-units','--type=timer','--state=active','--plain','--no-legend','stockanalysis-*']).splitlines()]
    stopped=False
    try:
        if timers:
            run(['sudo','-n','systemctl','stop',*timers])
        assert not capture(['systemctl','list-units','--type=service','--state=running,activating','--plain','--no-legend','stockanalysis-operating-data-*']),'Active batch; no source change made'
        run(['sudo','-n','systemctl','stop','stockanalysis-frontend-api.service']);stopped=True
        run(['git','-C',str(APP),'pull','--ff-only','origin','develop'])
        assert capture(['git','-C',str(APP),'rev-parse','HEAD'])==expected
        run(['sudo','-n','systemctl','start','stockanalysis-frontend-api.service']);stopped=False
        ready=False
        for _ in range(30):
            try:
                with urllib.request.urlopen('http://127.0.0.1:8787/__ready',timeout=2) as response:
                    ready=response.status==200 and json.load(response).get('status')=='ok'
                if ready:
                    break
            except (OSError,ValueError):
                pass
            time.sleep(.5)
        assert ready,'API readiness failed; previous source backup is available'
        result={'identity':ident,'previous_commit':previous,'commit':expected,'api_ready':True,
                'web_build_unchanged':True,'schema_changed':False,'env_changed':False,'manual_model_calls':0}
        persist('backend-activation.json',result)
    finally:
        if stopped:
            run(['sudo','-n','systemctl','start','stockanalysis-frontend-api.service'])
        if timers:
            run(['sudo','-n','systemctl','start',*timers])
    print(json.dumps(result))


if __name__=='__main__':
    main()
