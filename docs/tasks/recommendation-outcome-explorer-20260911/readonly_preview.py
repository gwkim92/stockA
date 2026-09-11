"""Local GET-only preview. Evaluate the new read module in memory on the existing host."""
import json
import pathlib
import shlex
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parents[3]
SOURCE = (ROOT / 'src/stockanalysis/frontend/recommendation_outcomes.py').read_text()
REMOTE = '''import json,os,sys,types,urllib.request
sys.path.insert(0,"/opt/stockanalysis/app/src")
from stockanalysis.operations.env_file import load_env_file_values
payload=json.load(sys.stdin)
path=payload['path']
if path.split('?')[0]=='/api/recommendation-outcomes':
    os.environ.update(load_env_file_values('/opt/stockanalysis/runtime/data-operations.env'))
    os.environ['PGOPTIONS']='-c default_transaction_read_only=on -c statement_timeout=6000'
    module=types.ModuleType('stocka_outcome_preview');sys.modules[module.__name__]=module
    exec(payload['source'],module.__dict__)
    print(json.dumps(module.resolve_recommendation_outcomes(path,source='live'),ensure_ascii=False))
else:
    values=load_env_file_values('/opt/stockanalysis/runtime/frontend-api.env')
    request=urllib.request.Request('http://127.0.0.1:8787'+path,headers={'Authorization':'Bearer '+values['STOCKANALYSIS_FRONTEND_API_READ_TOKEN']})
    with urllib.request.urlopen(request,timeout=25) as response: print(response.read().decode())
'''
cache = {}
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not self.path.startswith('/api/'):
            self.send_error(404); return
        try:
            if self.path not in cache:
                result = subprocess.run(['ssh','-S','none','-i','/Users/woody/Downloads/settle.pem','-o','ControlMaster=no','-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=8','ec2-user@3.211.40.142','/opt/stockanalysis/venv/bin/python -c '+shlex.quote(REMOTE)],input=json.dumps({'path':self.path,'source':SOURCE}),text=True,capture_output=True,timeout=32)
                if result.returncode: raise RuntimeError('Read failed')
                cache[self.path] = json.dumps(json.loads(result.stdout),ensure_ascii=False).encode()
            body = cache[self.path]
        except Exception:
            self.send_error(503,'Read unavailable'); return
        self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(body)
    def log_message(self,fmt,*args): print(fmt % args,flush=True)
if __name__=='__main__': ThreadingHTTPServer(('127.0.0.1',18789),Handler).serve_forever()
