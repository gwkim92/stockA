"""Local review preview: fresh read-only API via SSH, with actual local review adapter."""
import json
from pathlib import Path
import shlex
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'src'))
from stockanalysis.frontend.research_content_review import content_review_for

REMOTE='''import sys,json,urllib.request
sys.path.insert(0,"/opt/stockanalysis/app/src")
from stockanalysis.operations.env_file import load_env_file_values
path=json.load(sys.stdin)['path']
values=load_env_file_values('/opt/stockanalysis/runtime/frontend-api.env')
request=urllib.request.Request('http://127.0.0.1:8787'+path,headers={'Authorization':'Bearer '+values['STOCKANALYSIS_FRONTEND_API_READ_TOKEN']})
with urllib.request.urlopen(request,timeout=35) as r: print(r.read().decode())
'''

def decorate(value):
    if isinstance(value,dict):
        if str(value.get('artifact_id','')).startswith('equity-research-artifact-') and 'generation' in value:
            value['content_review']=content_review_for(value)
            value['generation']['content_review_status']=value['content_review']['status']
        else:
            for item in value.values():decorate(item)
    elif isinstance(value,list):
        for item in value:decorate(item)

cache={}
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not self.path.startswith('/api/'):
            self.send_error(404);return
        try:
            if self.path not in cache:
                cmd=['ssh','-S','none','-i','/Users/woody/Downloads/settle.pem','-o','ControlMaster=no','-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=8','ec2-user@3.211.40.142','/opt/stockanalysis/venv/bin/python -c '+shlex.quote(REMOTE)]
                r=subprocess.run(cmd,input=json.dumps({'path':self.path}),text=True,capture_output=True,timeout=45,check=True)
                payload=json.loads(r.stdout);decorate(payload)
                cache[self.path]=json.dumps(payload,ensure_ascii=False).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(cache[self.path])
        except Exception:
            self.send_error(503,'Read unavailable')
    def log_message(self,fmt,*args):print(fmt % args,flush=True)

if __name__=='__main__':ThreadingHTTPServer(('127.0.0.1',18790),Handler).serve_forever()
